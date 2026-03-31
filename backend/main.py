import json
import sqlite3
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agents.graph import run_reasoning_pipeline
from backend.ingestion.ner_extractor import EXTRACTOR_BACKEND, EXTRACTOR_WARNINGS
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
DB_PATH = APP_DIR / "db" / "reports.sqlite3"


class IngestRequest(BaseModel):
    note_text: str = Field(min_length=1, description="Raw discharge note text.")
    note_id: Optional[str] = Field(default=None, description="Optional client-supplied note ID.")
    lang: str = Field(default="auto", description="Input language: auto, en, de, fr, nl, or es.")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                note_id TEXT PRIMARY KEY,
                raw_text TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_report(note_id: str, note_text: str, report: dict) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO reports (note_id, raw_text, report_json)
            VALUES (?, ?, ?)
            ON CONFLICT(note_id) DO UPDATE SET
                raw_text=excluded.raw_text,
                report_json=excluded.report_json
            """,
            (note_id, note_text, json.dumps(report)),
        )
        connection.commit()


def get_report(note_id: str) -> Optional[dict]:
    with _connect() as connection:
        row = connection.execute(
            "SELECT report_json FROM reports WHERE note_id = ?",
            (note_id,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["report_json"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Clinical Reasoning Engine", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "extractor_backend": EXTRACTOR_BACKEND,
        "warnings": EXTRACTOR_WARNINGS,
        "translation_models_available": TRANSFORMERS_AVAILABLE,
        "language_detection_available": LANGDETECT_AVAILABLE,
        "supported_languages": ["en", *SUPPORTED.keys()],
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
