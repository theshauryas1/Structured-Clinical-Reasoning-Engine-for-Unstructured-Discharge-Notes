import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.agents.graph import run_reasoning_pipeline

DEFAULT_NOTES_DIR = ROOT / "tests" / "synthetic_notes"
DEFAULT_EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases_1000.json"
if not DEFAULT_EVAL_CASES.exists():
    DEFAULT_EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases_50.json"
if not DEFAULT_EVAL_CASES.exists():
    DEFAULT_EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases.json"


def evaluate(cases_path: Path = DEFAULT_EVAL_CASES, notes_dir: Path = DEFAULT_NOTES_DIR, verbose: bool = False) -> dict:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    total_cases = len(cases)
    results = []
    top1_hits = 0
    top3_hits = 0
    contradiction_tp = 0
    contradiction_fp = 0
    contradiction_fn = 0
    reciprocal_rank_sum = 0.0
    brier_components = []

    condition_stats = {}
    start_time = time.time()

    print(f"Evaluating {total_cases} clinical cases from {cases_path.name}...", file=sys.stderr)

    for idx, case in enumerate(cases, start=1):
        note_file = case["note_file"]
        note_text = (notes_dir / note_file).read_text(encoding="utf-8")
        report = run_reasoning_pipeline(note_text, note_id=note_file)

        predicted_names = [hypothesis.name for hypothesis in report.differentials]
        predicted_types = {item.type.value for item in report.contradiction_flags}
        expected_types = set(case["expected_contradiction_types"])
        expected_top = case["expected_top_differential"]

        top1_hit = bool(predicted_names and predicted_names[0] == expected_top)
        top3_hit = expected_top in predicted_names[:3]
        top1_hits += int(top1_hit)
        top3_hits += int(top3_hit)
        if expected_top in predicted_names:
            reciprocal_rank_sum += 1 / (predicted_names.index(expected_top) + 1)

        tp = len(predicted_types & expected_types)
        fp = len(predicted_types - expected_types)
        fn = len(expected_types - predicted_types)

        contradiction_tp += tp
        contradiction_fp += fp
        contradiction_fn += fn

        for score in report.confidence_scores:
            target = 1.0 if score.hypothesis == expected_top else 0.0
            brier_components.append((score.confidence - target) ** 2)

        # Per condition breakdown
        if expected_top not in condition_stats:
            condition_stats[expected_top] = {"total": 0, "top1": 0, "top3": 0}
        condition_stats[expected_top]["total"] += 1
        condition_stats[expected_top]["top1"] += int(top1_hit)
        condition_stats[expected_top]["top3"] += int(top3_hit)

        if idx % 100 == 0 or idx == total_cases:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            print(f"Progress: {idx}/{total_cases} cases processed ({rate:.1f} cases/s)...", file=sys.stderr)

        if verbose or total_cases <= 50:
            results.append(
                {
                    "note_file": note_file,
                    "expected_top_differential": expected_top,
                    "top_differential": predicted_names[0] if predicted_names else None,
                    "top1_hit": top1_hit,
                    "top3_hit": top3_hit,
                    "predicted_contradiction_types": sorted(predicted_types),
                    "expected_contradiction_types": sorted(expected_types),
                }
            )

    elapsed_total = round(time.time() - start_time, 2)
    precision = (
        contradiction_tp / (contradiction_tp + contradiction_fp)
        if (contradiction_tp + contradiction_fp)
        else 0.0
    )
    recall = (
        contradiction_tp / (contradiction_tp + contradiction_fn)
        if (contradiction_tp + contradiction_fn)
        else 0.0
    )
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall)
        else 0.0
    )

    per_condition_summary = {
        cond: {
            "total_cases": data["total"],
            "top1_accuracy": round(data["top1"] / data["total"], 4),
            "top3_accuracy": round(data["top3"] / data["total"], 4),
        }
        for cond, data in condition_stats.items()
    }

    return {
        "summary": {
            "num_cases": total_cases,
            "evaluation_time_seconds": elapsed_total,
            "throughput_cases_per_sec": round(total_cases / max(0.001, elapsed_total), 1),
            "top1_accuracy": round(top1_hits / total_cases, 4),
            "top3_accuracy": round(top3_hits / total_cases, 4),
            "mrr": round(reciprocal_rank_sum / total_cases, 4),
            "contradiction_precision": round(precision, 4),
            "contradiction_recall": round(recall, 4),
            "contradiction_f1": round(f1, 4),
            "brier_score": round(
                sum(brier_components) / max(1, len(brier_components)), 4
            ),
            "by_condition": per_condition_summary,
        },
        "cases_sample": results[:20] if not verbose else results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate clinical reasoning engine on test cases.")
    parser.add_argument(
        "--cases",
        type=str,
        default=str(DEFAULT_EVAL_CASES),
        help="Path to JSON evaluation cases file",
    )
    parser.add_argument(
        "--notes-dir",
        type=str,
        default=str(DEFAULT_NOTES_DIR),
        help="Path to synthetic notes directory",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include full details for all individual cases in the output JSON",
    )
    args = parser.parse_args()

    eval_result = evaluate(
        cases_path=Path(args.cases),
        notes_dir=Path(args.notes_dir),
        verbose=args.verbose,
    )
    print(json.dumps(eval_result, indent=2))
