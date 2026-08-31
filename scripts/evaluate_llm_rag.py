import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
import dotenv
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

dotenv.load_dotenv(ROOT / ".env")

from backend.rag.retriever import retrieve_context

NOTES_DIR = ROOT / "tests" / "synthetic_notes"
DEFAULT_EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases_1000.json"
if not DEFAULT_EVAL_CASES.exists():
    DEFAULT_EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases_50.json"


def call_llm_for_case(note_text: str, rag_docs: list, api_key: str, model: str = "meta/llama-3.1-8b-instruct") -> dict:
    rag_context = "\n".join(
        [
            f"- Guideline Condition: {doc.get('condition', '')}\n"
            f"  Summary: {doc.get('summary', '')}\n"
            f"  Recommended Follow-up: {doc.get('follow_up', '')}"
            for doc in rag_docs
        ]
    )

    system_prompt = (
        "You are an expert Clinical Reasoning AI evaluating an unstructured discharge note with RAG guideline context.\n"
        "Analyze the discharge note and retrieved clinical guidelines. Output a valid JSON object with the following keys:\n"
        "1. 'primary_differential': The exact most likely primary clinical diagnosis (e.g. 'Acute ischemic stroke', 'Community-acquired pneumonia', 'Acute kidney injury', 'Atrial fibrillation', 'Acute hypoxemic respiratory failure', 'Post-operative recovery after total knee arthroplasty').\n"
        "2. 'top3_differentials': Array of the top 3 differential diagnoses.\n"
        "3. 'contradiction_types': Array of detected discrepancy flags. Allowed values: 'missing_symptom', 'new_finding', 'status_reversal'. If none, use [].\n"
        "4. 'rag_faithfulness_score': Float between 0.0 and 1.0 evaluating how well the note is grounded in the retrieved guideline.\n"
        "5. 'clinical_reasoning': Concise 1-2 sentence clinical rationale.\n"
        "Output ONLY raw JSON."
    )

    user_content = (
        f"--- UNSTRUCTURED DISCHARGE NOTE ---\n{note_text}\n\n"
        f"--- RETRIEVED RAG CLINICAL GUIDELINES ---\n{rag_context}\n"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
    }

    resp = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"NIM HTTP {resp.status_code}: {resp.text[:200]}")

    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def run_llm_evaluation(num_cases: int = 12, cases_path: Path = DEFAULT_EVAL_CASES, shuffle: bool = True):
    api_key = os.getenv("NVIDIA_NIM_API_KEY", "").strip()
    if not api_key:
        print("Error: NVIDIA_NIM_API_KEY is not set.", file=sys.stderr)
        return

    raw_cases = json.loads(cases_path.read_text(encoding="utf-8"))
    
    if shuffle:
        # Group by condition to ensure balanced representation across all conditions
        by_cond = {}
        for c in raw_cases:
            by_cond.setdefault(c["expected_top_differential"], []).append(c)
        
        sampled = []
        cond_keys = list(by_cond.keys())
        idx = 0
        while len(sampled) < num_cases and any(by_cond.values()):
            cond = cond_keys[idx % len(cond_keys)]
            if by_cond[cond]:
                sampled.append(by_cond[cond].pop(0))
            idx += 1
        cases = sampled
    else:
        cases = raw_cases[:num_cases]

    total = len(cases)

    print(f"\n=======================================================", file=sys.stderr)
    print(f" Starting LIVE LLM Evaluation (NVIDIA NIM LLaMA 3.1 8B)", file=sys.stderr)
    print(f" Dataset: {cases_path.name} | Total Diverse Cases: {total}", file=sys.stderr)
    print(f"=======================================================\n", file=sys.stderr)

    results = []
    top1_hits = 0
    top3_hits = 0
    faithfulness_scores = []
    latencies = []

    contradiction_tp = 0
    contradiction_fp = 0
    contradiction_fn = 0

    for i, case in enumerate(cases, start=1):
        note_file = case["note_file"]
        note_text = (NOTES_DIR / note_file).read_text(encoding="utf-8")
        expected_top = case["expected_top_differential"]
        expected_contradictions = set(case["expected_contradiction_types"])

        # 1. RAG Retrieval
        rag_docs = retrieve_context(note_text, top_k=2)

        # 2. Live LLM Call
        t0 = time.time()
        try:
            llm_out = call_llm_for_case(note_text, rag_docs, api_key=api_key)
            latency = round(time.time() - t0, 2)
            latencies.append(latency)
        except Exception as exc:
            print(f"Error on case {i}: {exc}", file=sys.stderr)
            continue

        predicted_primary = llm_out.get("primary_differential", "")
        predicted_top3 = llm_out.get("top3_differentials", [])
        predicted_contradictions = set(llm_out.get("contradiction_types", []))
        rag_faithfulness = float(llm_out.get("rag_faithfulness_score", 0.8))
        faithfulness_scores.append(rag_faithfulness)

        # Match primary diagnosis
        top1_hit = expected_top.lower() in predicted_primary.lower() or predicted_primary.lower() in expected_top.lower()
        top3_hit = any(expected_top.lower() in p.lower() or p.lower() in expected_top.lower() for p in predicted_top3) or top1_hit

        top1_hits += int(top1_hit)
        top3_hits += int(top3_hit)

        tp = len(predicted_contradictions & expected_contradictions)
        fp = len(predicted_contradictions - expected_contradictions)
        fn = len(expected_contradictions - predicted_contradictions)
        contradiction_tp += tp
        contradiction_fp += fp
        contradiction_fn += fn

        status_symbol = "✓" if top1_hit else "✗"
        print(
            f"[{i:02d}/{total:02d}] {status_symbol} Target: {expected_top:<35} | LLM: {predicted_primary:<35} ({latency}s)",
            file=sys.stderr,
        )

        results.append(
            {
                "case": note_file,
                "expected_top": expected_top,
                "llm_primary": predicted_primary,
                "llm_top3": predicted_top3,
                "top1_hit": top1_hit,
                "expected_contradictions": sorted(expected_contradictions),
                "llm_contradictions": sorted(predicted_contradictions),
                "rag_faithfulness": rag_faithfulness,
                "latency_sec": latency,
                "reasoning": llm_out.get("clinical_reasoning", ""),
            }
        )
        time.sleep(0.3)

    prec = contradiction_tp / (contradiction_tp + contradiction_fp) if (contradiction_tp + contradiction_fp) else 0.0
    rec = contradiction_tp / (contradiction_tp + contradiction_fn) if (contradiction_tp + contradiction_fn) else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0

    summary = {
        "llm_model": "meta/llama-3.1-8b-instruct",
        "total_cases_evaluated": len(results),
        "top1_diagnostic_accuracy": round(top1_hits / max(1, len(results)), 4),
        "top3_diagnostic_accuracy": round(top3_hits / max(1, len(results)), 4),
        "avg_rag_faithfulness": round(sum(faithfulness_scores) / max(1, len(faithfulness_scores)), 3),
        "avg_latency_per_case_sec": round(sum(latencies) / max(1, len(latencies)), 2),
        "contradiction_precision": round(prec, 4),
        "contradiction_recall": round(rec, 4),
        "contradiction_f1": round(f1, 4),
    }

    print(json.dumps({"summary": summary, "cases": results}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-cases", type=int, default=12, help="Number of cases to run live through LLM")
    parser.add_argument("--cases", type=str, default=str(DEFAULT_EVAL_CASES), help="Path to evaluation cases JSON")
    parser.add_argument("--no-shuffle", action="store_true", help="Do not balance/shuffle condition types")
    args = parser.parse_args()
    run_llm_evaluation(num_cases=args.num_cases, cases_path=Path(args.cases), shuffle=not args.no_shuffle)
