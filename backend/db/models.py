from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extractor_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    warnings_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reasoning_output: Mapped["ReasoningOutput"] = relationship(back_populates="note", uselist=False)


class ReasoningOutput(Base):
    __tablename__ = "reasoning_outputs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    note_id: Mapped[str] = mapped_column(ForeignKey("clinical_notes.id"), unique=True, nullable=False)
    timeline_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    differentials_json: Mapped[list] = mapped_column(JSON, default=list)
    contradictions_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence_json: Mapped[list] = mapped_column(JSON, default=list)
    reasoning_trace_json: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    note: Mapped[ClinicalNote] = relationship(back_populates="reasoning_output")
