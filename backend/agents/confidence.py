from statistics import mean, pvariance
from typing import Dict, List

from backend.agents.models import AuditStep, ConfidenceScore, Hypothesis
from backend.ml.confidence_calibration import predict_probability


def _section_coverage(hypothesis: Hypothesis) -> float:
    sections = {evidence.section.value for evidence in hypothesis.supporting_evidence}
    return min(1.0, len(sections) / 3)


def _feature_vector(hypothesis: Hypothesis, contradiction_count: int) -> Dict[str, float]:
    support_count = min(1.0, len(hypothesis.supporting_evidence) / 3)
    coverage = _section_coverage(hypothesis)
    contradiction_penalty = min(1.0, contradiction_count / 5)
    rank_bonus = max(0.0, 1 - ((hypothesis.rank - 1) * 0.2))
    return {
        "base_score": hypothesis.score,
        "retrieval_score": hypothesis.retrieval_score,
        "support_count": support_count,
        "section_coverage": coverage,
        "rank_bonus": rank_bonus,
        "contradiction_penalty": contradiction_penalty,
        "ranking_score": max(0.0, min(1.0, hypothesis.ranking_score / 3)),
    }


def _sample_predictions(features: Dict[str, float], passes: int = 8) -> List[float]:
    samples: List[float] = []
    for index in range(passes):
        adjustment = ((index % 4) - 1.5) * 0.04
        perturbed = dict(features)
        perturbed["retrieval_score"] = max(0.0, min(1.0, perturbed["retrieval_score"] + adjustment))
        perturbed["base_score"] = max(0.0, min(1.0, perturbed["base_score"] - (adjustment / 2)))
        samples.append(predict_probability(perturbed))
    return samples


def score_confidence(state: dict) -> dict:
    hypotheses: List[Hypothesis] = list(state.get("differentials", []))
    contradiction_count = len(state.get("contradictions", []))

    confidence_scores: List[ConfidenceScore] = []
    for hypothesis in hypotheses:
        features = _feature_vector(hypothesis, contradiction_count)
        sampled_scores = _sample_predictions(features)
        avg = round(mean(sampled_scores), 3)
        variance = round(pvariance(sampled_scores), 4) if len(sampled_scores) > 1 else 0.0
        uncertainty = round(min(1.0, (variance * 18) + (features["contradiction_penalty"] * 0.15)), 3)
        confidence = round(max(0.0, min(1.0, avg - (uncertainty * 0.18))), 3)
        confidence_scores.append(
            ConfidenceScore(
                hypothesis=hypothesis.name,
                mean_score=avg,
                variance=variance,
                uncertainty=uncertainty,
                confidence=confidence,
                model_type="feature_calibrated",
                features={key: round(value, 3) for key, value in features.items()},
                sampled_scores=sampled_scores,
            )
        )

    trace = list(state.get("reasoning_trace", []))
    trace.append(
        AuditStep(
            agent="confidence_agent",
            summary=f"Scored confidence for {len(confidence_scores)} hypotheses using a learned calibration model.",
            details=[f"{score.hypothesis}:{score.confidence}" for score in confidence_scores],
        )
    )

    return {
        "confidence_scores": confidence_scores,
        "reasoning_trace": trace,
    }
