import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.agents.graph import run_reasoning_pipeline

NOTES_DIR = ROOT / "tests" / "synthetic_notes"
EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases.json"


def evaluate() -> dict:
    cases = json.loads(EVAL_CASES.read_text(encoding="utf-8"))
    results = []
    top1_hits = 0
    top3_hits = 0
    contradiction_tp = 0
    contradiction_fp = 0
    contradiction_fn = 0

    for case in cases:
        note_text = (NOTES_DIR / case["note_file"]).read_text(encoding="utf-8")
        report = run_reasoning_pipeline(note_text, note_id=case["note_file"])

        predicted_names = [hypothesis.name for hypothesis in report.differentials]
        predicted_types = {item.type.value for item in report.contradiction_flags}
        expected_types = set(case["expected_contradiction_types"])
        expected_top = case["expected_top_differential"]

        top1_hit = bool(predicted_names and predicted_names[0] == expected_top)
        top3_hit = expected_top in predicted_names[:3]
        top1_hits += int(top1_hit)
        top3_hits += int(top3_hit)

        contradiction_tp += len(predicted_types & expected_types)
        contradiction_fp += len(predicted_types - expected_types)
        contradiction_fn += len(expected_types - predicted_types)

        results.append(
            {
                "note_file": case["note_file"],
                "top_differential": predicted_names[0] if predicted_names else None,
                "top1_hit": top1_hit,
                "top3_hit": top3_hit,
                "predicted_contradiction_types": sorted(predicted_types),
                "expected_contradiction_types": sorted(expected_types),
            }
        )

    total_cases = len(cases)
    precision = contradiction_tp / (contradiction_tp + contradiction_fp) if (contradiction_tp + contradiction_fp) else 0.0
    recall = contradiction_tp / (contradiction_tp + contradiction_fn) if (contradiction_tp + contradiction_fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "cases": results,
        "summary": {
            "num_cases": total_cases,
            "top1_accuracy": round(top1_hits / total_cases, 3),
            "top3_accuracy": round(top3_hits / total_cases, 3),
            "contradiction_precision": round(precision, 3),
            "contradiction_recall": round(recall, 3),
            "contradiction_f1": round(f1, 3),
        },
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
