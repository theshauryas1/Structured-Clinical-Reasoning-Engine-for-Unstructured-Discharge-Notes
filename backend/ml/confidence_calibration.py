import json
import math
from pathlib import Path
from typing import Dict

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
CALIBRATOR_PATH = ARTIFACTS_DIR / "confidence_calibrator.json"

DEFAULT_CALIBRATOR = {
    "bias": -0.35,
    "weights": {
        "base_score": 2.1,
        "retrieval_score": 1.1,
        "support_count": 0.7,
        "section_coverage": 0.45,
        "rank_bonus": 0.4,
        "contradiction_penalty": -0.9,
        "ranking_score": 0.3,
    },
}


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def load_calibrator() -> dict:
    if CALIBRATOR_PATH.exists():
        return json.loads(CALIBRATOR_PATH.read_text(encoding="utf-8"))
    return DEFAULT_CALIBRATOR


def save_calibrator(weights: dict) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    CALIBRATOR_PATH.write_text(json.dumps(weights, indent=2), encoding="utf-8")


def predict_probability(features: Dict[str, float], model: dict | None = None) -> float:
    model = model or load_calibrator()
    linear = float(model.get("bias", 0.0))
    for name, value in features.items():
        linear += float(model.get("weights", {}).get(name, 0.0)) * float(value)
    return round(_sigmoid(linear), 3)
