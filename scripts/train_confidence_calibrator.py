import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.agents.graph import run_reasoning_pipeline
from backend.ml.confidence_calibration import save_calibrator

NOTES_DIR = ROOT / "tests" / "synthetic_notes"
EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases.json"


def train_confidence_calibrator() -> dict:
    cases = json.loads(EVAL_CASES.read_text(encoding="utf-8"))
    positive_totals = {}
    negative_totals = {}
    positive_count = 0
    negative_count = 0

    for case in cases:
        note_text = (NOTES_DIR / case["note_file"]).read_text(encoding="utf-8")
        report = run_reasoning_pipeline(note_text, note_id=f"cal-{case['note_file']}")
        expected = case["expected_top_differential"]

        for score in report.confidence_scores:
            target = positive_totals if score.hypothesis == expected else negative_totals
            for key, value in score.features.items():
                target[key] = target.get(key, 0.0) + float(value)
            if score.hypothesis == expected:
                positive_count += 1
            else:
                negative_count += 1

    weights = {}
    for key in set(positive_totals) | set(negative_totals):
        pos_avg = positive_totals.get(key, 0.0) / max(1, positive_count)
        neg_avg = negative_totals.get(key, 0.0) / max(1, negative_count)
        weights[key] = round(pos_avg - neg_avg, 4)

    model = {"bias": 0.0, "weights": weights}
    save_calibrator(model)
    return model


if __name__ == "__main__":
    print(json.dumps(train_confidence_calibrator(), indent=2))
