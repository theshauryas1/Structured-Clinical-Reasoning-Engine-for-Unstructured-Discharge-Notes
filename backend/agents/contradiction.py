from typing import Dict, List, Optional, Tuple

from backend.agents.models import (
    AuditStep,
    ClinicalEvent,
    Contradiction,
    ContradictionType,
    Evidence,
    SectionName,
)
from backend.ingestion.timeline_builder import build_timeline

RELEVANT_LABELS = {"SYMPTOM", "DIAGNOSIS"}
ACTIVE_STATUSES = {"active", "new", "worsening", "stable", "improving"}
RESOLUTION_STATUSES = {"resolved", "improving", "stable"}


def _evidence_from_event(event: ClinicalEvent) -> Evidence:
    return Evidence(
        text_span=event.text,
        section=event.section,
        start=event.start,
        end=event.end,
        sentence_text=event.sentence_text,
    )


def _group_by_normalized(events: List[ClinicalEvent]) -> Dict[str, List[ClinicalEvent]]:
    grouped: Dict[str, List[ClinicalEvent]] = {}
    for event in events:
        grouped.setdefault(event.normalized_text, []).append(event)
    return grouped


def _missing_symptom_candidates(
    admission_events: List[ClinicalEvent],
    later_events: List[ClinicalEvent],
    discharge_events: List[ClinicalEvent],
) -> List[Contradiction]:
    contradictions: List[Contradiction] = []
    discharge_names = {event.normalized_text for event in discharge_events}
    resolved_names = {
        event.normalized_text for event in later_events if event.status in RESOLUTION_STATUSES
    }

    grouped_admission = _group_by_normalized(
        [event for event in admission_events if event.label in RELEVANT_LABELS and event.status in ACTIVE_STATUSES]
    )
    for normalized, events in grouped_admission.items():
        anchor = events[0]
        if normalized in discharge_names:
            continue
        if normalized in resolved_names:
            continue
        contradictions.append(
            Contradiction(
                type=ContradictionType.MISSING_SYMPTOM,
                entity=normalized,
                description=(
                    f"{normalized} is documented at admission but never revisited in discharge documentation "
                    "and there is no explicit resolution statement."
                ),
                admission_evidence=_evidence_from_event(anchor),
                discharge_evidence=None,
                confidence=0.82,
            )
        )
    return contradictions


def _new_finding_candidates(
    prior_events: List[ClinicalEvent],
    discharge_events: List[ClinicalEvent],
) -> List[Contradiction]:
    contradictions: List[Contradiction] = []
    prior_names = {event.normalized_text for event in prior_events}

    grouped_discharge = _group_by_normalized(
        [event for event in discharge_events if event.label in RELEVANT_LABELS]
    )
    for normalized, events in grouped_discharge.items():
        anchor = events[0]
        sentence = anchor.sentence_text.lower()
        if normalized in prior_names:
            continue
        if anchor.status not in {"new", "worsening"} and not any(
            cue in sentence for cue in ["new onset", "developed", "acute", "requiring"]
        ):
            continue
        contradictions.append(
            Contradiction(
                type=ContradictionType.NEW_FINDING,
                entity=normalized,
                description=(
                    f"{normalized} appears in discharge planning without a matching admission or hospital-course mention."
                ),
                admission_evidence=None,
                discharge_evidence=_evidence_from_event(anchor),
                confidence=0.86,
            )
        )
    return contradictions


def _status_reversal_candidates(
    earlier_events: List[ClinicalEvent],
    discharge_events: List[ClinicalEvent],
) -> List[Contradiction]:
    contradictions: List[Contradiction] = []
    improved_by_domain: Dict[str, ClinicalEvent] = {}

    for event in earlier_events:
        if event.status in RESOLUTION_STATUSES and event.domain != "general":
            improved_by_domain.setdefault(event.domain, event)

    for event in discharge_events:
        sentence = event.sentence_text.lower()
        worsening_language = any(
            cue in sentence
            for cue in ["worsening", "deteriorat", "requiring", "at rest", "continuously"]
        )
        if event.domain not in improved_by_domain:
            continue
        if event.status not in {"worsening", "new", "active"} and not worsening_language:
            continue
        earlier = improved_by_domain[event.domain]
        contradictions.append(
            Contradiction(
                type=ContradictionType.STATUS_REVERSAL,
                entity=f"{event.domain} status",
                description=(
                    f"{event.domain.title()} status looked improved or resolved earlier in the stay, "
                    f"but discharge documentation describes a worse active problem around {event.normalized_text}."
                ),
                admission_evidence=_evidence_from_event(earlier),
                discharge_evidence=_evidence_from_event(event),
                confidence=0.84,
            )
        )
    return contradictions


def detect_contradictions(state: dict) -> dict:
    """
    Detects typed admission-vs-discharge contradictions from a structured timeline.
    This node is deterministic so the core Week 2 behavior is testable without API keys.
    """
    if "note_text" not in state:
        return {"contradictions": []}

    timeline = state.get("timeline") or build_timeline(state["note_text"])
    admission_events = [event for event in timeline.all_events if event.section == SectionName.ADMISSION]
    hospital_events = [event for event in timeline.all_events if event.section == SectionName.HOSPITAL_COURSE]
    discharge_events = [event for event in timeline.all_events if event.section == SectionName.DISCHARGE]

    contradictions: List[Contradiction] = []
    contradictions.extend(_missing_symptom_candidates(admission_events, hospital_events + discharge_events, discharge_events))
    contradictions.extend(_new_finding_candidates(admission_events + hospital_events, discharge_events))
    contradictions.extend(_status_reversal_candidates(admission_events + hospital_events, discharge_events))

    deduped: Dict[Tuple[str, str], Contradiction] = {}
    for contradiction in contradictions:
        key = (contradiction.type.value, contradiction.entity)
        deduped[key] = contradiction

    final_contradictions = list(deduped.values())
    trace = list(state.get("reasoning_trace", []))
    trace.append(
        AuditStep(
            agent="contradiction_agent",
            summary=f"Flagged {len(final_contradictions)} typed contradictions.",
            details=[f"{item.type.value}:{item.entity}" for item in final_contradictions],
        )
    )

    return {
        "timeline": timeline,
        "contradictions": final_contradictions,
        "reasoning_trace": trace,
    }
