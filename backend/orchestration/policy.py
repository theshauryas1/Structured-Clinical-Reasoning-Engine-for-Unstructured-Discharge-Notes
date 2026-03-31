import json
from pathlib import Path
from typing import Dict, List

from backend.agents.models import AuditStep, ClinicalTimeline, PolicyDecision

POLICY_PATH = Path(__file__).resolve().parents[1] / "ml" / "artifacts" / "orchestration_policy.json"

DEFAULT_POLICY = {
    "retrieve_again_threshold": 0.35,
    "rerank_min_candidates": 2,
    "run_contradiction": True,
    "run_confidence": True,
}


def load_policy() -> dict:
    if POLICY_PATH.exists():
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return DEFAULT_POLICY


def save_policy(policy: dict) -> None:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICY_PATH.write_text(json.dumps(policy, indent=2), encoding="utf-8")


def build_policy_features(timeline: ClinicalTimeline, differentials_count: int = 0) -> Dict[str, float]:
    events = timeline.all_events
    discharge_events = sum(1 for event in events if event.section.value == "discharge")
    contradiction_risk = sum(
        1
        for event in events
        if event.status in {"new", "worsening"} and event.section.value == "discharge"
    )
    return {
        "event_count": len(events),
        "discharge_event_ratio": round(discharge_events / max(1, len(events)), 3),
        "contradiction_risk": contradiction_risk,
        "differentials_count": differentials_count,
    }


def decide_post_differential(timeline: ClinicalTimeline, differentials_count: int) -> List[PolicyDecision]:
    policy = load_policy()
    features = build_policy_features(timeline, differentials_count)
    decisions: List[PolicyDecision] = []

    if differentials_count >= int(policy.get("rerank_min_candidates", 2)):
        decisions.append(
            PolicyDecision(
                step="post_differential",
                action="rerank_differentials",
                reason="Enough candidate hypotheses exist to justify learned reranking.",
                features=features,
            )
        )

    if features["contradiction_risk"] > 0 or bool(policy.get("run_contradiction", True)):
        decisions.append(
            PolicyDecision(
                step="post_differential",
                action="run_contradiction_agent",
                reason="Discharge risk signals warrant contradiction analysis.",
                features=features,
            )
        )

    return decisions


def decide_post_contradiction(contradictions_count: int, top_ranking_score: float) -> List[PolicyDecision]:
    policy = load_policy()
    features = {
        "contradictions_count": contradictions_count,
        "top_ranking_score": round(top_ranking_score, 3),
    }
    decisions: List[PolicyDecision] = []

    if contradictions_count > 0 and top_ranking_score < float(policy.get("retrieve_again_threshold", 0.35)):
        decisions.append(
            PolicyDecision(
                step="post_contradiction",
                action="consider_additional_retrieval",
                reason="Conflicting findings with weak ranking support suggest more context may help.",
                features=features,
            )
        )

    if bool(policy.get("run_confidence", True)):
        decisions.append(
            PolicyDecision(
                step="post_contradiction",
                action="run_confidence_agent",
                reason="Confidence scoring is enabled for final report synthesis.",
                features=features,
            )
        )

    return decisions


def trace_policy_decisions(trace: List[AuditStep], decisions: List[PolicyDecision], agent: str) -> List[AuditStep]:
    trace.append(
        AuditStep(
            agent=agent,
            summary=f"Policy produced {len(decisions)} orchestration decisions.",
            details=[f"{decision.step}:{decision.action}" for decision in decisions],
        )
    )
    return trace
