import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.agents.graph import run_reasoning_pipeline
from backend.orchestration.policy import save_policy

NOTES_DIR = ROOT / "tests" / "synthetic_notes"
EVAL_CASES = ROOT / "tests" / "eval" / "eval_cases.json"


def train_orchestration_policy() -> dict:
    cases = json.loads(EVAL_CASES.read_text(encoding="utf-8"))
    weak_scores = []
    strong_scores = []

    for case in cases:
        note_text = (NOTES_DIR / case["note_file"]).read_text(encoding="utf-8")
        report = run_reasoning_pipeline(note_text, note_id=f"pol-{case['note_file']}")
        if not report.differentials:
            continue
        top = report.differentials[0]
        if top.name == case["expected_top_differential"]:
            strong_scores.append(top.ranking_score)
        else:
            weak_scores.append(top.ranking_score)

    threshold = 0.35
    if weak_scores and strong_scores:
        threshold = round((sum(weak_scores) / len(weak_scores) + sum(strong_scores) / len(strong_scores)) / 2, 3)

    policy = {
        "retrieve_again_threshold": threshold,
        "rerank_min_candidates": 2,
        "run_contradiction": True,
        "run_confidence": True,
    }
    save_policy(policy)
    return policy


if __name__ == "__main__":
    print(json.dumps(train_orchestration_policy(), indent=2))
