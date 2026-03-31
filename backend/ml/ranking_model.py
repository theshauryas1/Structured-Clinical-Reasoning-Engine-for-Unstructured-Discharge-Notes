import json
from pathlib import Path
from typing import Dict, List

from backend.agents.models import ClinicalTimeline, Hypothesis

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
RERANKER_PATH = ARTIFACTS_DIR / "reranker_weights.json"

DEFAULT_RERANKER = {
    "bias": -0.2,
    "weights": {
        "base_score": 1.35,
        "retrieval_score": 1.1,
        "support_count": 0.7,
        "section_coverage": 0.45,
        "discharge_support": 0.25,
        "context_count": 0.2,
    },
}


def load_reranker() -> dict:
    if RERANKER_PATH.exists():
        return json.loads(RERANKER_PATH.read_text(encoding="utf-8"))
    return DEFAULT_RERANKER


def save_reranker(weights: dict) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    RERANKER_PATH.write_text(json.dumps(weights, indent=2), encoding="utf-8")


def build_ranking_features(hypothesis: Hypothesis, timeline: ClinicalTimeline) -> Dict[str, float]:
    support_count = min(1.0, len(hypothesis.supporting_evidence) / 3)
    section_coverage = min(
        1.0,
        len({evidence.section.value for evidence in hypothesis.supporting_evidence}) / 3,
    )
    discharge_support = min(
        1.0,
        sum(1 for evidence in hypothesis.supporting_evidence if evidence.section.value == "discharge") / 2,
    )
    context_count = min(1.0, len(hypothesis.retrieved_contexts) / 3)
    return {
        "base_score": round(hypothesis.score, 3),
        "retrieval_score": round(hypothesis.retrieval_score, 3),
        "support_count": round(support_count, 3),
        "section_coverage": round(section_coverage, 3),
        "discharge_support": round(discharge_support, 3),
        "context_count": round(context_count, 3),
    }


def score_ranking_features(features: Dict[str, float], model: dict | None = None) -> float:
    model = model or load_reranker()
    score = float(model.get("bias", 0.0))
    for name, value in features.items():
        score += float(model.get("weights", {}).get(name, 0.0)) * float(value)
    return round(score, 4)


def rerank_hypotheses(hypotheses: List[Hypothesis], timeline: ClinicalTimeline) -> List[Hypothesis]:
    model = load_reranker()
    rescored: List[Hypothesis] = []
    for hypothesis in hypotheses:
        features = build_ranking_features(hypothesis, timeline)
        ranking_score = score_ranking_features(features, model)
        rescored.append(
            hypothesis.model_copy(
                update={
                    "ranking_features": features,
                    "ranking_score": ranking_score,
                }
            )
        )

    rescored.sort(key=lambda item: item.ranking_score, reverse=True)
    return [
        hypothesis.model_copy(update={"rank": index})
        for index, hypothesis in enumerate(rescored, start=1)
    ]
