from typing import Dict, List

from backend.agents.models import ClinicalEvent, ClinicalTimeline, SectionBlock, SectionName
from backend.ingestion.ner_extractor import (
    EXTRACTOR_BACKEND,
    EXTRACTOR_WARNINGS,
    extract_entities,
    extract_sentences,
    infer_domain,
    normalize_entity_text,
)


def _classify_section_heading(line: str) -> SectionName | None:
    upper_line = line.upper().strip()
    if any(token in upper_line for token in ["ADMISSION", "HPI", "PRESENTING", "INITIAL ASSESSMENT"]):
        return SectionName.ADMISSION
    if (
        ("HOSPITAL COURSE" in upper_line and "SUMMARY" not in upper_line)
        or "ICU COURSE" in upper_line
        or "CLINICAL COURSE" in upper_line
        or upper_line == "COURSE:"
    ):
        return SectionName.HOSPITAL_COURSE
    if any(token in upper_line for token in ["DISCHARGE", "FINAL DIAGNOS", "FINAL STATUS", "PLAN", "CONDITION"]):
        return SectionName.DISCHARGE
    return None


def _infer_status(sentence: str) -> str:
    lowered = sentence.lower()
    worsening_cues = ["worsening", "deteriorat", "declin", "required", "requiring", "at rest"]
    new_cues = ["new onset", "developed", "new ", "newly", "bumped to"]
    improving_cues = ["improved", "improving", "better", "weaned", "decreasing"]
    resolved_cues = ["resolved", "no acute distress", "denies", "cleared", "completed"]
    stable_cues = ["stable", "well controlled", "controlled", "unchanged"]

    if any(cue in lowered for cue in worsening_cues):
        return "worsening"
    if any(cue in lowered for cue in new_cues):
        return "new"
    if any(cue in lowered for cue in resolved_cues):
        return "resolved"
    if any(cue in lowered for cue in improving_cues):
        return "improving"
    if any(cue in lowered for cue in stable_cues):
        return "stable"
    return "active"


def split_note_sections(text: str) -> Dict[str, str]:
    """
    Splits a note into admission, hospital-course, and discharge sections
    using common heading patterns from discharge summaries.
    """
    current_section = SectionName.ADMISSION
    section_lines: Dict[SectionName, List[str]] = {
        SectionName.ADMISSION: [],
        SectionName.HOSPITAL_COURSE: [],
        SectionName.DISCHARGE: [],
    }

    for line in text.splitlines():
        heading_section = _classify_section_heading(line)
        if heading_section is not None:
            current_section = heading_section
        section_lines[current_section].append(line)

    return {section.value: "\n".join(lines).strip() for section, lines in section_lines.items()}


def build_timeline(text: str) -> ClinicalTimeline:
    sections_text = split_note_sections(text)
    section_models: List[SectionBlock] = []
    running_search_start = 0

    for section_name in [SectionName.ADMISSION, SectionName.HOSPITAL_COURSE, SectionName.DISCHARGE]:
        section_text = sections_text.get(section_name.value, "").strip()
        if not section_text:
            continue

        section_start = text.find(section_text, running_search_start)
        if section_start < 0:
            section_start = text.find(section_text)
        section_end = section_start + len(section_text)
        running_search_start = max(section_end, running_search_start)

        events: List[ClinicalEvent] = []
        for sentence in extract_sentences(section_text):
            sentence_text = str(sentence["text"])
            sentence_start = section_start + int(sentence["start"])
            sentence_end = section_start + int(sentence["end"])
            status = _infer_status(sentence_text)

            for entity in extract_entities(sentence_text):
                entity_text = str(entity["text"])
                entity_start = sentence_start + int(entity["start"])
                entity_end = sentence_start + int(entity["end"])
                normalized = normalize_entity_text(entity_text)

                events.append(
                    ClinicalEvent(
                        text=entity_text,
                        label=str(entity["label"]),
                        normalized_text=normalized,
                        domain=infer_domain(f"{entity_text} {sentence_text}"),
                        section=section_name,
                        start=entity_start,
                        end=entity_end,
                        sentence_text=sentence_text,
                        sentence_start=sentence_start,
                        sentence_end=sentence_end,
                        status=status,
                    )
                )

        section_models.append(
            SectionBlock(
                name=section_name,
                text=section_text,
                start=section_start,
                end=section_end,
                events=events,
            )
        )

    return ClinicalTimeline(
        raw_text=text,
        extractor_backend=EXTRACTOR_BACKEND,
        warnings=EXTRACTOR_WARNINGS,
        sections=section_models,
    )
