import html
import logging
import os

# Load .env before any backend module reads env vars
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)   # .env always wins; safe since we set intentionally
except ImportError:
    pass  # python-dotenv optional; env vars set externally still work

import re
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, File, Form, UploadFile, Security, Depends, Cookie, Header, Response
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
from backend.db.models import Base, ClinicalNote, ReasoningOutput, User, UserSession, Chat, ChatMessage
from backend.db.auth import hash_password, verify_password, create_session, verify_session
from backend.llm_gateway import call_llm_gateway
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

    # SQLite migration for user_id column in clinical_notes
    if DATABASE_URL.startswith("sqlite"):
        try:
            with DATABASE_ENGINE.begin() as conn:
                # Check if user_id column exists
                cursor = conn.exec_driver_sql("PRAGMA table_info(clinical_notes)")
                columns = [row[1] for row in cursor.fetchall()]
                if "user_id" not in columns:
                    conn.exec_driver_sql("ALTER TABLE clinical_notes ADD COLUMN user_id TEXT")
                    logger.info("Migrated SQLite: Added user_id column to clinical_notes")
        except Exception as exc:
            logger.warning(f"Failed to run SQLite database migration: {exc}")


def save_report(note_id: str, note_text: str, report: dict, user_id: str) -> None:
    timeline_payload = report.get("timeline", {})
    note = ClinicalNote(
        id=note_id,
        user_id=user_id,
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
            "gemini": {
                "configured": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
                "model": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
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
        save_report(note_id, payload.note_text, response_payload, user_id=getattr(payload, '_user_id', None) or "anonymous")
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
    return FileResponse(
        index_file,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


# --- Auth Pydantic Models ---

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=256)


class LoginRequest(BaseModel):
    username: str
    password: str


# --- Auth Endpoints ---

def _get_current_user_id(session_token: Optional[str] = Cookie(default=None)) -> Optional[str]:
    """Dependency: returns user_id from session cookie, or None if not logged in."""
    if not session_token:
        return None
    with SessionLocal() as db:
        return verify_session(db, session_token)


def _require_auth(user_id: Optional[str] = Depends(_get_current_user_id)) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user_id


@app.post("/api/auth/register")
def register_user(payload: RegisterRequest, response: Response) -> dict:
    username = payload.username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
    with SessionLocal() as db:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken.")
        user_id = str(uuid.uuid4())
        pw_hash = hash_password(payload.password)
        new_user = User(id=user_id, username=username, password_hash=pw_hash)
        db.add(new_user)
        db.commit()
        token = create_session(db, user_id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return {"status": "registered", "username": username}


@app.post("/api/auth/login")
def login_user(payload: LoginRequest, response: Response) -> dict:
    username = payload.username.strip().lower()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        token = create_session(db, user.id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return {"status": "ok", "username": user.username}


@app.post("/api/auth/logout")
def logout_user(response: Response, session_token: Optional[str] = Cookie(default=None)) -> dict:
    if session_token:
        with SessionLocal() as db:
            record = db.query(UserSession).filter(UserSession.token == session_token).first()
            if record:
                db.delete(record)
                db.commit()
    response.delete_cookie("session_token")
    return {"status": "logged_out"}


@app.get("/api/auth/me")
def get_me(user_id: str = Depends(_require_auth)) -> dict:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        return {"user_id": user.id, "username": user.username}


# --- Chat API Endpoints ---

class NewChatRequest(BaseModel):
    title: str = Field(default="New Chat", max_length=255)
    note_id: Optional[str] = Field(default=None)


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    mode: str = Field(default="general")  # 'general', 'rag', 'report'
    note_id: Optional[str] = Field(default=None)


@app.get("/api/chats")
def list_chats(user_id: str = Depends(_require_auth)) -> list:
    with SessionLocal() as db:
        chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "note_id": c.note_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "message_count": len(c.messages),
            }
            for c in chats
        ]


@app.post("/api/chats")
def create_chat(payload: NewChatRequest, user_id: str = Depends(_require_auth)) -> dict:
    chat_id = str(uuid.uuid4())
    with SessionLocal() as db:
        new_chat = Chat(id=chat_id, user_id=user_id, title=payload.title, note_id=payload.note_id)
        db.add(new_chat)
        db.commit()
    return {"id": chat_id, "title": payload.title, "note_id": payload.note_id}


@app.get("/api/chats/{chat_id}")
def get_chat_messages(chat_id: str, user_id: str = Depends(_require_auth)) -> dict:
    with SessionLocal() as db:
        chat = db.get(Chat, chat_id)
        if not chat or chat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Chat not found.")
        messages = [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "media_name": m.media_name,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in sorted(chat.messages, key=lambda x: x.created_at or "")
        ]
        return {"chat_id": chat_id, "title": chat.title, "note_id": chat.note_id, "messages": messages}


@app.post("/api/chats/{chat_id}/message")
async def send_chat_message(
    chat_id: str,
    content: str = Form(...),
    mode: str = Form(default="general"),
    note_id: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
    user_id: str = Depends(_require_auth),
) -> dict:
    with SessionLocal() as db:
        chat = db.get(Chat, chat_id)
        if not chat or chat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Chat not found.")

    # Extract text from uploaded file if present
    media_name = None
    media_context = ""
    if file and file.filename:
        try:
            file_bytes, filename = await validate_uploaded_file(file)
            extracted_text, _ = extract_content(file_bytes, filename, file.content_type or "application/octet-stream")
            media_name = filename
            media_context = f"\n\n[DOCUMENT CONTEXT from '{filename}']:\n{extracted_text[:8000]}"
        except Exception as exc:
            logger.warning(f"Chat file extraction failed: {exc}")
            media_context = f"\n\n[File upload '{file.filename}' could not be processed: {exc}]"
            media_name = file.filename

    # Build system prompt based on mode
    if mode == "rag":
        from backend.rag.retriever import retrieve_context
        rag_results = retrieve_context(content, top_k=3)
        rag_context = "\n".join(
            f"- {r['condition']}: {r['summary']} (Follow-up: {r.get('follow_up', '')})"
            for r in rag_results
        )
        system_prompt = (
            "You are an expert clinical reasoning assistant backed by a medical guidelines knowledge base. "
            "Answer the user's question using the following retrieved clinical guidelines as context.\n\n"
            f"RETRIEVED GUIDELINES:\n{rag_context}\n\n"
            "[Disclaimer: This assistant is for educational and auditing purposes only. Not for clinical decision-making.]"
        )
    elif mode == "report" and note_id:
        report = get_report(note_id)
        if report:
            from backend.agents.chat_agent import formulate_report_context
            report_ctx = formulate_report_context(report)
            system_prompt = (
                "You are an expert clinical reasoning assistant. Answer questions about the patient report.\n\n"
                f"{report_ctx}\n\n"
                "[Disclaimer: This assistant is for educational and auditing purposes only. Not for clinical decision-making.]"
            )
        else:
            system_prompt = "You are an expert clinical reasoning assistant. [Disclaimer: Educational use only.]"
    else:
        system_prompt = (
            "You are a knowledgeable medical information assistant. Answer the user's medical or clinical question clearly and accurately. "
            "Always remind users to consult a qualified healthcare professional for personal medical advice. "
            "[Disclaimer: This assistant is for educational purposes only. Not a substitute for professional medical advice.]"
        )

    # Save user message
    user_msg_id = str(uuid.uuid4())
    user_content = content + media_context
    with SessionLocal() as db:
        user_msg = ChatMessage(
            id=user_msg_id,
            chat_id=chat_id,
            role="user",
            content=content,  # store clean content; context sent to LLM only
            media_name=media_name,
            media_content=media_context if media_context else None,
        )
        db.add(user_msg)
        db.commit()

    # Get conversation history
    with SessionLocal() as db:
        chat = db.get(Chat, chat_id)
        history = sorted(chat.messages, key=lambda x: x.created_at or "")
        llm_messages = [{"role": "system", "content": system_prompt}]
        for m in history[:-1]:  # exclude newly added user msg
            msg_content = m.content
            if m.media_content:
                msg_content += m.media_content
            llm_messages.append({"role": m.role, "content": msg_content})
        # Add current user message with file context
        llm_messages.append({"role": "user", "content": user_content})

    # Call LLM Gateway
    try:
        assistant_reply = call_llm_gateway(llm_messages)
    except Exception as exc:
        logger.error(f"LLM Gateway call failed in chat: {exc}", exc_info=True)
        assistant_reply = "I'm sorry, the AI service is temporarily unavailable. Please try again shortly."

    # Save assistant message
    assistant_msg_id = str(uuid.uuid4())
    with SessionLocal() as db:
        assistant_msg = ChatMessage(
            id=assistant_msg_id,
            chat_id=chat_id,
            role="assistant",
            content=assistant_reply,
        )
        db.add(assistant_msg)
        db.commit()

    return {"response": assistant_reply, "message_id": assistant_msg_id}


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str, user_id: str = Depends(_require_auth)) -> dict:
    with SessionLocal() as db:
        chat = db.get(Chat, chat_id)
        if not chat or chat.user_id != user_id:
            raise HTTPException(status_code=404, detail="Chat not found.")
        db.delete(chat)
        db.commit()
    return {"status": "deleted", "chat_id": chat_id}


@app.exception_handler(StarletteHTTPException)
async def spa_route_handler(request, exc):
    if exc.status_code == 404:
        path = request.url.path
        if path.startswith("/api") or path in {
            "/ingest", "/ingest-file", "/chat", "/explain", "/health", "/reports"
        } or path.startswith("/explain/") or path.startswith("/report/"):
            return await http_exception_handler(request, exc)
        index_file = FRONTEND_DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(
                index_file,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )
    return await http_exception_handler(request, exc)


if FRONTEND_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
