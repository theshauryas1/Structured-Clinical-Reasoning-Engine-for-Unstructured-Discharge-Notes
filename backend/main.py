import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from backend.agents.graph import run_reasoning_pipeline
from backend.db.models import Base, ClinicalNote, ReasoningOutput
from backend.groq_guardrails import load_groq_settings
from backend.ingestion.ner_extractor import EXTRACTOR_BACKEND, EXTRACTOR_WARNINGS
from backend.ml.confidence_calibration import CALIBRATOR_PATH
from backend.ml.ranking_model import RERANKER_PATH
from backend.orchestration.policy import POLICY_PATH
from backend.translation_layer import (
    LANGDETECT_AVAILABLE,
    SUPPORTED,
    TRANSFORMERS_AVAILABLE,
    TranslationLayerError,
    build_display_report,
    detect_input_language,
    translate,
)

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
FRONTEND_DIST_DIR = PROJECT_DIR / "frontend" / "dist"
DEFAULT_SQLITE_PATH = Path(os.getenv("CLINICAL_REASONING_DB_PATH", APP_DIR / "db" / "reports.sqlite3"))


def _database_url() -> str:
    raw_url = os.getenv("DATABASE_URL")
    if raw_url:
        if raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
        if raw_url.startswith("postgresql://"):
            return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return raw_url
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


DATABASE_URL = _database_url()
DATABASE_ENGINE = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=DATABASE_ENGINE, autoflush=False, autocommit=False, future=True)


class IngestRequest(BaseModel):
    note_text: str = Field(min_length=1, description="Raw discharge note text.")
    note_id: Optional[str] = Field(default=None, description="Optional client-supplied note ID.")
    lang: str = Field(default="auto", description="Input language: auto, en, de, fr, nl, or es.")


def initialize_database() -> None:
    if DATABASE_URL.startswith("sqlite"):
        DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(DATABASE_ENGINE)


def save_report(note_id: str, note_text: str, report: dict) -> None:
    timeline_payload = report.get("timeline", {})
    note = ClinicalNote(
        id=note_id,
        raw_text=note_text,
        extractor_backend=timeline_payload.get("extractor_backend", EXTRACTOR_BACKEND),
        warnings_json=report.get("warnings", []),
    )
    reasoning_output = ReasoningOutput(
        id=note_id,
        note_id=note_id,
        timeline_json=timeline_payload,
        differentials_json=report.get("differentials", []),
        contradictions_json=report.get("contradiction_flags", []),
        confidence_json=report.get("confidence_scores", []),
        reasoning_trace_json=report.get("reasoning_trace", []),
        orchestration_trace_json=report.get("orchestration_trace", []),
        report_json=report,
    )

    with SessionLocal() as session:
        session.merge(note)
        session.merge(reasoning_output)
        session.commit()


def get_report(note_id: str) -> Optional[dict]:
    with SessionLocal() as session:
        record = session.get(ReasoningOutput, note_id)
        if record is None:
            return None
        return record.report_json


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Clinical Reasoning Engine", version="1.0.0", lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CLINICAL_REASONING_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict:
    groq_settings = load_groq_settings()
    return {
        "status": "ok",
        "extractor_backend": EXTRACTOR_BACKEND,
        "warnings": EXTRACTOR_WARNINGS,
        "translation_models_available": TRANSFORMERS_AVAILABLE,
        "language_detection_available": LANGDETECT_AVAILABLE,
        "supported_languages": ["en", *SUPPORTED.keys()],
        "learned_artifacts": {
            "reranker": RERANKER_PATH.exists(),
            "confidence_calibrator": CALIBRATOR_PATH.exists(),
            "orchestration_policy": POLICY_PATH.exists(),
        },
        "groq": {
            "configured": bool(groq_settings.api_key),
            "model": groq_settings.model,
            "max_retries": groq_settings.max_retries,
            "min_interval_seconds": groq_settings.min_interval_seconds,
            "backoff_seconds": groq_settings.backoff_seconds,
            "timeout_seconds": groq_settings.timeout_seconds,
        },
        "database": {
            "configured": True,
            "driver": make_url(DATABASE_URL).drivername,
        },
    }


@app.post("/ingest")
def ingest_note(payload: IngestRequest) -> dict:
    note_id = payload.note_id or str(uuid.uuid4())
    try:
        source_language, language_warnings = detect_input_language(payload.note_text, payload.lang)
        english_note = translate(payload.note_text, src_lang=source_language, to_english=True)
    except TranslationLayerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    report = run_reasoning_pipeline(english_note, note_id=note_id)
    report_payload = report.model_dump(mode="json")
    report_payload["warnings"] = [*report_payload.get("warnings", []), *language_warnings]
    display_report = build_display_report(report_payload, source_language)

    response_payload = {
        **report_payload,
        "source_language": source_language,
        "pipeline_language": "en",
        "display_language": source_language,
        "display_report": display_report,
        "translated_input_text": english_note,
    }
    save_report(note_id, payload.note_text, response_payload)
    return response_payload


@app.get("/report/{note_id}")
def fetch_report(note_id: str) -> dict:
    report = get_report(note_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@app.get("/")
def serve_frontend() -> FileResponse:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=503,
            detail="Frontend assets are not built yet. Run `npm install && npm run build` in the frontend directory.",
        )
    return FileResponse(index_file)


if FRONTEND_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
