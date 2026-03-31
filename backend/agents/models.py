from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SectionName(str, Enum):
    ADMISSION = "admission"
    HOSPITAL_COURSE = "hospital_course"
    DISCHARGE = "discharge"


class ContradictionType(str, Enum):
    MISSING_SYMPTOM = "missing_symptom"
    NEW_FINDING = "new_finding"
    STATUS_REVERSAL = "status_reversal"


class Evidence(BaseModel):
    text_span: str = Field(description="Exact text span supporting the finding.")
    section: SectionName = Field(description="Section where the evidence was found.")
    start: int = Field(description="Character start offset in the raw note.")
    end: int = Field(description="Character end offset in the raw note.")
    sentence_text: str = Field(description="Full sentence containing the evidence.")


class ClinicalEvent(BaseModel):
    text: str
    label: str
    normalized_text: str
    domain: str
    section: SectionName
    start: int
    end: int
    sentence_text: str
    sentence_start: int
    sentence_end: int
    status: str


class SectionBlock(BaseModel):
    name: SectionName
    text: str
    start: int
    end: int
    events: List[ClinicalEvent] = Field(default_factory=list)


class ClinicalTimeline(BaseModel):
    raw_text: str
    extractor_backend: str
    warnings: List[str] = Field(default_factory=list)
    sections: List[SectionBlock] = Field(default_factory=list)

    @property
    def all_events(self) -> List[ClinicalEvent]:
        return [event for section in self.sections for event in section.events]


class Hypothesis(BaseModel):
    name: str
    rank: int
    score: float = Field(ge=0.0, le=1.0)
    retrieval_score: float = Field(default=0.0, ge=0.0, le=1.0)
    ranking_score: float = Field(default=0.0)
    rationale: str
    retrieved_contexts: List[str] = Field(default_factory=list)
    ranking_features: dict = Field(default_factory=dict)
    supporting_evidence: List[Evidence] = Field(default_factory=list)


class Contradiction(BaseModel):
    type: ContradictionType = Field(description="The category of the contradiction.")
    entity: str = Field(description="The biomedical entity involved.")
    description: str = Field(description="Why this contradicts the admission-to-discharge story.")
    admission_evidence: Optional[Evidence] = Field(None, description="Admission-side evidence.")
    discharge_evidence: Optional[Evidence] = Field(None, description="Discharge-side evidence.")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ContradictionList(BaseModel):
    contradictions: List[Contradiction] = Field(default_factory=list, description="List of detected contradictions.")


class ConfidenceScore(BaseModel):
    hypothesis: str
    mean_score: float = Field(ge=0.0, le=1.0)
    variance: float = Field(ge=0.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_type: str = Field(default="feature_calibrated")
    features: dict = Field(default_factory=dict)
    sampled_scores: List[float] = Field(default_factory=list)


class PolicyDecision(BaseModel):
    step: str
    action: str
    reason: str
    features: dict = Field(default_factory=dict)


class AuditStep(BaseModel):
    agent: str
    summary: str
    details: List[str] = Field(default_factory=list)


class NoteReport(BaseModel):
    note_id: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timeline: ClinicalTimeline
    differentials: List[Hypothesis] = Field(default_factory=list)
    contradiction_flags: List[Contradiction] = Field(default_factory=list)
    confidence_scores: List[ConfidenceScore] = Field(default_factory=list)
    reasoning_trace: List[AuditStep] = Field(default_factory=list)
    orchestration_trace: List[PolicyDecision] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
