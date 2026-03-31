from typing import Dict, List

from backend.agents.models import AuditStep, ClinicalEvent, Evidence, Hypothesis
from backend.ingestion.timeline_builder import build_timeline
from backend.rag.retriever import retrieve_context

DIFFERENTIAL_RULES = [
    {
        "name": "Acute ischemic stroke",
        "keywords": ["weakness", "aphasia", "facial droop", "ischemic stroke", "mca", "infarct"],
    },
    {
        "name": "Community-acquired pneumonia",
        "keywords": ["pneumonia", "productive cough", "fever", "infiltrate", "shortness of breath"],
    },
    {
        "name": "Atrial fibrillation",
        "keywords": ["atrial fibrillation", "afib", "palpitations"],
    },
    {
        "name": "Acute kidney injury",
        "keywords": ["acute kidney injury", "aki", "creatinine"],
    },
    {
        "name": "Acute hypoxemic respiratory failure",
        "keywords": ["acute respiratory failure", "oxygen", "desaturation", "shortness of breath", "hypoxia"],
    },
    {
        "name": "Post-operative recovery after total knee arthroplasty",
        "keywords": ["total knee arthroplasty", "tka", "incision", "post-op", "knee"],
    },
]


def _evidence_from_event(event: ClinicalEvent) -> Evidence:
    return Evidence(
        text_span=event.text,
        section=event.section,
        start=event.start,
        end=event.end,
        sentence_text=event.sentence_text,
    )


def _collect_matching_events(events: List[ClinicalEvent], keywords: List[str]) -> List[ClinicalEvent]:
    matching_events: List[ClinicalEvent] = []
    seen_keys = set()
    for event in events:
        haystack = f"{event.normalized_text} {event.sentence_text.lower()}"
        if any(keyword in haystack for keyword in keywords):
            key = (event.normalized_text, event.start, event.end)
            if key not in seen_keys:
                seen_keys.add(key)
                matching_events.append(event)
    return matching_events


def _build_query(events: List[ClinicalEvent]) -> str:
    normalized_terms = sorted({event.normalized_text for event in events})
    domains = sorted({event.domain for event in events if event.domain != "general"})
    sentences = " ".join(event.sentence_text for event in events[:3])
    return " ".join(normalized_terms + domains + [sentences])


def _retrieval_score(retrieved_contexts: List[Dict[str, object]]) -> float:
    if not retrieved_contexts:
        return 0.0
    top_score = float(retrieved_contexts[0]["score"])
    return round(min(1.0, top_score / 6), 3)


def generate_differentials(state: dict) -> dict:
    timeline = state.get("timeline") or build_timeline(state["note_text"])
    events = timeline.all_events
    candidates: List[Hypothesis] = []
    retrieval_trace: List[str] = []

    for rule in DIFFERENTIAL_RULES:
        matching_events = _collect_matching_events(events, rule["keywords"])
        query_text = _build_query(matching_events) if matching_events else " ".join(rule["keywords"])
        retrieved_contexts = retrieve_context(query_text, top_k=3)

        if not matching_events and not any(
            context["condition"].lower() == rule["name"].lower() for context in retrieved_contexts
        ):
            continue

        discharge_bonus = 0.1 if any(event.section.value == "discharge" for event in matching_events) else 0.0
        unique_hits = len({event.normalized_text for event in matching_events})
        retrieval_alignment = next(
            (context for context in retrieved_contexts if context["condition"].lower() == rule["name"].lower()),
            None,
        )
        retrieval_score = _retrieval_score([retrieval_alignment] if retrieval_alignment else retrieved_contexts[:1])
        score = min(0.98, 0.22 + (unique_hits * 0.11) + discharge_bonus + (retrieval_score * 0.35))

        rationale_parts = []
        if matching_events:
            rationale_parts.append(
                "Structured evidence matched "
                + ", ".join(sorted({event.normalized_text for event in matching_events})[:4])
            )
        if retrieval_alignment:
            rationale_parts.append(
                f"RAG support: {retrieval_alignment['summary']}"
            )
        elif retrieved_contexts:
            rationale_parts.append(
                f"Nearest retrieved context: {retrieved_contexts[0]['condition']}."
            )
        rationale = " ".join(rationale_parts) or "Fallback differential generated from retrieval-only context."

        candidates.append(
            Hypothesis(
                name=rule["name"],
                rank=0,
                score=round(score, 3),
                retrieval_score=retrieval_score,
                rationale=rationale,
                retrieved_contexts=[
                    f"{context['condition']}: {context['summary']}" for context in retrieved_contexts
                ],
                supporting_evidence=[_evidence_from_event(event) for event in matching_events[:3]],
            )
        )

        if retrieved_contexts:
            retrieval_trace.append(
                f"{rule['name']} <= {retrieved_contexts[0]['condition']} ({retrieved_contexts[0]['score']})"
            )

    if not candidates and events:
        most_salient = events[0]
        fallback_contexts = retrieve_context(_build_query([most_salient]), top_k=2)
        candidates.append(
            Hypothesis(
                name=(fallback_contexts[0]["condition"] if fallback_contexts else most_salient.normalized_text.title()),
                rank=1,
                score=0.35,
                retrieval_score=_retrieval_score(fallback_contexts[:1]),
                rationale="Fallback hypothesis derived from the earliest structured clinical event with retrieval support.",
                retrieved_contexts=[
                    f"{context['condition']}: {context['summary']}" for context in fallback_contexts
                ],
                supporting_evidence=[_evidence_from_event(most_salient)],
            )
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    ranked: List[Hypothesis] = []
    for index, candidate in enumerate(candidates[:5], start=1):
        ranked.append(candidate.model_copy(update={"rank": index}))

    trace = list(state.get("reasoning_trace", []))
    trace.append(
        AuditStep(
            agent="differential_agent",
            summary=f"Generated {len(ranked)} ranked differentials from structured evidence plus local retrieval.",
            details=retrieval_trace[:5] or [hypothesis.name for hypothesis in ranked],
        )
    )

    return {
        "timeline": timeline,
        "differentials": ranked,
        "reasoning_trace": trace,
    }
