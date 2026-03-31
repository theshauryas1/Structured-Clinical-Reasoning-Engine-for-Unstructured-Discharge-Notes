import uuid

from backend.agents.models import AuditStep, NoteReport


def synthesize_report(state: dict) -> dict:
    note_id = state.get("note_id") or str(uuid.uuid4())
    trace = list(state.get("reasoning_trace", []))
    trace.append(
        AuditStep(
            agent="meta_agent",
            summary="Assembled final structured JSON report with audit trail.",
            details=[
                f"differentials={len(state.get('differentials', []))}",
                f"contradictions={len(state.get('contradictions', []))}",
                f"confidence_scores={len(state.get('confidence_scores', []))}",
            ],
        )
    )

    timeline = state["timeline"]
    report = NoteReport(
        note_id=note_id,
        timeline=timeline,
        differentials=state.get("differentials", []),
        contradiction_flags=state.get("contradictions", []),
        confidence_scores=state.get("confidence_scores", []),
        reasoning_trace=trace,
        warnings=timeline.warnings,
    )

    return {
        "note_id": note_id,
        "report": report,
        "reasoning_trace": trace,
    }
