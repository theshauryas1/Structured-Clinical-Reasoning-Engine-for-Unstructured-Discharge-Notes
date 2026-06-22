import html
import logging
import os
import re
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, File, Form, UploadFile, Security, Depends
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.ingestion.file_extractor import extract_content
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from backend.agents.graph import run_reasoning_pipeline
from backend.agents.chat_agent import ChatRequest, generate_chat_response
from backend.agents.plain_lang_translator import generate_plain_language_explanation
from backend.db.models import Base, ClinicalNote, ReasoningOutput
from backend.groq_guardrails import load_groq_settings
from backend.nim_guardrails import load_nim_settings
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

logger = logging.getLogger("clinical_reasoning_security")
logging.basicConfig(level=logging.INFO)

# --- Security Constants ---
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".wav", ".mp3", ".m4a"}

FILE_SIGNATURES = {
    b"%PDF": ".pdf",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpeg",  # Covers JPEG and JPG
}

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
SECURITY_BEARER = HTTPBearer(auto_error=False)


# --- Security Verification Dependencies & Helpers ---

def verify_api_key(
    header_key: Optional[str] = Depends(API_KEY_HEADER),
    bearer_key: Optional[HTTPAuthorizationCredentials] = Depends(SECURITY_BEARER)
) -> None:
    expected_key = os.getenv("CLINICAL_REASONING_API_KEY", "").strip()
    if not expected_key or expected_key == "dev-mode-unsafe":
        return
        
    if header_key == expected_key:
        return
        
    if bearer_key and bearer_key.credentials == expected_key:
        return
        
    raise HTTPException(
        status_code=401,
        detail="Unauthorized. A valid X-API-Key or Bearer token is required."
    )


def sanitize_filename(filename: str) -> str:
    basename = os.path.basename(filename)
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', basename)
    if not sanitized or sanitized.startswith(".."):
        sanitized = f"upload_{int(time.time())}"
    return sanitized


async def validate_uploaded_file(file: UploadFile) -> tuple[bytes, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")
        
    filename = sanitize_filename(file.filename)
    ext = os.path.splitext(filename.lower())[1]
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not supported. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    file_bytes = b""
    chunk_size = 1024 * 1024  # 1MB
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_bytes += chunk
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File payload too large. Maximum allowed size is 10MB."
            )
            
    if ext in {".pdf", ".png", ".jpg", ".jpeg"}:
        matched_sig = False
        for sig, sig_ext in FILE_SIGNATURES.items():
            if file_bytes.startswith(sig):
                if sig_ext == ".jpeg" and ext in {".jpg", ".jpeg"}:
                    matched_sig = True
                    break
                elif sig_ext == ext:
                    matched_sig = True
                    break
        if not matched_sig:
            raise HTTPException(
                status_code=400,
                detail=f"File content does not match the declared extension '{ext}' (signature mismatch)."
            )
            
    elif ext == ".txt":
        try:
            file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid text file encoding. Must be UTF-8 formatted."
            )
            
    return file_bytes, filename


def sanitize_input_text(text: str) -> str:
    clean_text = re.sub(r'<[^>]*>', '', text)
    return clean_text[:50000]


# --- Security Middlewares ---

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = defaultdict(list)
        
    async def dispatch(self, request, call_next):
        path = request.url.path
        is_api_route = path in {
            "/health", "/ingest", "/ingest-file", "/chat", "/explain", "/reports"
        } or path.startswith("/report/") or path.startswith("/explain/")
        
        if is_api_route and self.calls_per_minute > 0:
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]
            
            if len(self.requests[client_ip]) >= self.calls_per_minute:
                logger.warning(f"Rate limit triggered for client IP: {client_ip}")
                return JSONResponse(
                    content={"detail": "Too many requests. Please try again in a minute."},
                    status_code=429
                )
            self.requests[client_ip].append(now)
            
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        csp_directives = (
            "default-src 'self'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws://localhost:* http://localhost:* https://api.groq.com https://integrate.api.nvidia.com https://api.openai.com; "
            "img-src 'self' data:;"
        )
        response.headers["Content-Security-Policy"] = csp_directives
        
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        return response


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
    display_lang: str = Field(
        default="auto",
        description="Display language for translated report: auto, en, de, fr, nl, or es.",
    )


def _resolve_display_language(requested_lang: str, source_language: str) -> str:
    normalized = (requested_lang or "auto").strip().lower()
    if normalized == "auto":
        return source_language
    if normalized not in {"en", *SUPPORTED.keys()}:
        raise TranslationLayerError(
            f"Unsupported display language '{requested_lang}'. Supported values: auto, en, de, fr, nl, es."
        )
    return normalized


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
    expected_key = os.getenv("CLINICAL_REASONING_API_KEY", "").strip()
    if not expected_key:
        logger.warning(
            "WARNING: CLINICAL_REASONING_API_KEY is not set in the environment. "
            "The reasoning engine's API endpoints are running in public/unsecured mode."
        )
    else:
        logger.info("Security check initialized: API key authentication is ACTIVE.")

    if DATABASE_URL.startswith("postgres") or DATABASE_URL.startswith("postgresql"):
        try:
            from backend.rag.index_guidelines import index_guidelines_to_postgres
            index_guidelines_to_postgres(DATABASE_ENGINE)
        except Exception as exc:
            pass
    yield


app = FastAPI(title="Clinical Reasoning Engine", version="1.0.0", lifespan=lifespan)

# Add Rate-Limiting & Security Headers Middlewares
try:
    rate_limit_val = int(os.getenv("CLINICAL_REASONING_RATE_LIMIT", "60"))
except ValueError:
    rate_limit_val = 60

app.add_middleware(RateLimitMiddleware, calls_per_minute=rate_limit_val)
app.add_middleware(SecurityHeadersMiddleware)

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

@app.get("/health", dependencies=[Depends(verify_api_key)])
def health() -> dict:
    try:
        groq_settings = load_groq_settings()
        nim_settings = load_nim_settings()
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
            "nvidia_nim": {
                "configured": bool(nim_settings.api_key),
                "model": nim_settings.model,
                "base_url": nim_settings.base_url,
                "max_retries": nim_settings.max_retries,
                "min_interval_seconds": nim_settings.min_interval_seconds,
                "backoff_seconds": nim_settings.backoff_seconds,
                "timeout_seconds": nim_settings.timeout_seconds,
            },
            "database": {
                "configured": True,
                "driver": make_url(DATABASE_URL).drivername,
            },
        }
    except Exception as exc:
        logger.error(f"Health check failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal status audit failed.")


@app.post("/ingest", dependencies=[Depends(verify_api_key)])
def ingest_note(payload: IngestRequest) -> dict:
    payload.note_text = sanitize_input_text(payload.note_text)
    note_id = payload.note_id or str(uuid.uuid4())
    try:
        source_language, language_warnings = detect_input_language(payload.note_text, payload.lang)
        english_note = translate(payload.note_text, src_lang=source_language, to_english=True)
        display_language = _resolve_display_language(payload.display_lang, source_language)
    except TranslationLayerError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected language pipeline error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to run translation layer.")

    try:
        report = run_reasoning_pipeline(english_note, note_id=note_id)
        report_payload = report.model_dump(mode="json")
        report_payload["warnings"] = [*report_payload.get("warnings", []), *language_warnings]
        display_report = build_display_report(report_payload, display_language)

        response_payload = {
            **report_payload,
            "source_language": source_language,
            "pipeline_language": "en",
            "display_language": display_language,
            "display_report": display_report,
            "translated_input_text": english_note,
        }
        save_report(note_id, payload.note_text, response_payload)
        return response_payload
    except Exception as exc:
        logger.error(f"Reasoning pipeline run failed for ID {note_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Clinical reasoning pipeline processing failed.")


@app.post("/ingest-file", dependencies=[Depends(verify_api_key)])
async def ingest_file(
    file: UploadFile = File(...),
    lang: str = Form("auto"),
    display_lang: str = Form("auto")
) -> dict:
    try:
        file_bytes, filename = await validate_uploaded_file(file)
        extracted_text, extraction_warnings = extract_content(
            file_bytes, filename, file.content_type
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"File upload content extraction failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not extract contents from uploaded file.")

    payload = IngestRequest(
        note_text=extracted_text,
        lang=lang,
        display_lang=display_lang
    )

    response_payload = ingest_note(payload)
    if extraction_warnings:
        response_payload["warnings"] = [
            *response_payload.get("warnings", []),
            extraction_warnings
        ]

    return response_payload


@app.get("/report/{note_id}", dependencies=[Depends(verify_api_key)])
def fetch_report(note_id: str, display_lang: str = "auto") -> dict:
    report = get_report(note_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    try:
        target_language = _resolve_display_language(display_lang, report.get("source_language", "en"))
    except TranslationLayerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Report translation fetch failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load display translations.")

    if target_language == report.get("display_language"):
        return report

    try:
        english_report = {
            key: value
            for key, value in report.items()
            if key not in {"source_language", "pipeline_language", "display_language", "display_report", "translated_input_text"}
        }
        report["display_language"] = target_language
        report["display_report"] = build_display_report(english_report, target_language)
        return report
    except Exception as exc:
        logger.error(f"Language report construction failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to format display language translation.")


@app.post("/chat", dependencies=[Depends(verify_api_key)])
def chat_with_report(payload: ChatRequest) -> dict:
    report = get_report(payload.note_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found. Ingest the note first.")

    try:
        response_text = generate_chat_response(payload, report)
        return {"response": response_text}
    except Exception as exc:
        logger.error(f"Chat generation failure: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while generating reasoning response.")


@app.post("/explain/{note_id}", dependencies=[Depends(verify_api_key)])
def explain_report(note_id: str) -> dict:
    report = get_report(note_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    try:
        explanation = generate_plain_language_explanation(report)
        return {"explanation": explanation}
    except Exception as exc:
        logger.error(f"Explain translation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while generating layperson translation.")


@app.get("/reports", dependencies=[Depends(verify_api_key)])
def list_reports() -> list:
    try:
        with SessionLocal() as session:
            records = session.query(ReasoningOutput).order_by(ReasoningOutput.generated_at.desc()).all()
            results = []
            for r in records:
                report_data = r.report_json or {}
                timeline_sections = r.timeline_json.get("sections", []) if r.timeline_json else []
                event_count = sum(len(s.get("events", [])) for s in timeline_sections)
                results.append({
                    "note_id": r.id,
                    "created_at": r.generated_at.isoformat() if r.generated_at else None,
                    "source_language": report_data.get("source_language", "en"),
                    "display_language": report_data.get("display_language", "en"),
                    "contradiction_count": len(r.contradictions_json or []),
                    "differential_count": len(r.differentials_json or []),
                    "event_count": event_count,
                })
            return results
    except Exception as exc:
        logger.error(f"Failed to list clinical audits: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to retrieve clinical logs.")


@app.delete("/report/{note_id}", dependencies=[Depends(verify_api_key)])
def delete_report(note_id: str) -> dict:
    try:
        with SessionLocal() as session:
            output_record = session.get(ReasoningOutput, note_id)
            note_record = session.get(ClinicalNote, note_id)
            if output_record:
                session.delete(output_record)
            if note_record:
                session.delete(note_record)
            session.commit()
            return {"status": "deleted", "note_id": note_id}
    except Exception as exc:
        logger.error(f"Failed to delete audit record {note_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to delete clinical log record.")


@app.get("/")
def serve_frontend() -> FileResponse:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=503,
            detail="Frontend assets are not built yet. Run `npm install && npm run build` in the frontend directory.",
        )
    return FileResponse(index_file)


@app.exception_handler(StarletteHTTPException)
async def spa_route_handler(request, exc):
    if exc.status_code == 404:
        path = request.url.path
        # Skip API routes and other known routes
        if path.startswith("/api") or path in {
            "/ingest", "/ingest-file", "/chat", "/explain", "/health", "/reports"
        } or path.startswith("/explain/") or path.startswith("/report/"):
            return await http_exception_handler(request, exc)
        
        index_file = FRONTEND_DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return await http_exception_handler(request, exc)


if FRONTEND_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
