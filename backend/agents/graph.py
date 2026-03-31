from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from backend.agents.confidence import score_confidence
from backend.agents.contradiction import detect_contradictions
from backend.agents.differential import generate_differentials
from backend.agents.meta import synthesize_report
from backend.agents.models import (
    AuditStep,
    ClinicalTimeline,
    ConfidenceScore,
    Contradiction,
    Hypothesis,
    NoteReport,
    PolicyDecision,
)
from backend.orchestration.nodes import plan_after_contradiction, plan_after_differential


class GraphState(TypedDict, total=False):
    note_id: str
    note_text: str
    timeline: ClinicalTimeline
    differentials: List[Hypothesis]
    contradictions: List[Contradiction]
    confidence_scores: List[ConfidenceScore]
    reasoning_trace: List[AuditStep]
    orchestration_trace: List[PolicyDecision]
    report: NoteReport


def create_agent_graph():
    """
    Builds the full multi-agent LangGraph flow:
    differential -> contradiction -> confidence -> meta.
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("differential_agent", generate_differentials)
    workflow.add_node("policy_after_differential", plan_after_differential)
    workflow.add_node("contradiction_agent", detect_contradictions)
    workflow.add_node("policy_after_contradiction", plan_after_contradiction)
    workflow.add_node("confidence_agent", score_confidence)
    workflow.add_node("meta_agent", synthesize_report)

    workflow.set_entry_point("differential_agent")
    workflow.add_edge("differential_agent", "policy_after_differential")
    workflow.add_edge("policy_after_differential", "contradiction_agent")
    workflow.add_edge("contradiction_agent", "policy_after_contradiction")
    workflow.add_edge("policy_after_contradiction", "confidence_agent")
    workflow.add_edge("confidence_agent", "meta_agent")
    workflow.add_edge("meta_agent", END)

    return workflow.compile()


def run_reasoning_pipeline(note_text: str, note_id: Optional[str] = None) -> NoteReport:
    app = create_agent_graph()
    result = app.invoke({"note_text": note_text, "note_id": note_id})
    return result["report"]
