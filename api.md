# API Specification

The **Clinical Reasoning Engine** exposes a REST API built with FastAPI. It handles unstructured clinical note ingestion, file parsing, multi-agent reasoning execution, contextual chatbot Q&A, and display localization.

For code definitions, see [main.py](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/main.py).

---

## 1. Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Inquiries application health status, cache availability, and LLM keys. | No |
| `POST` | `/ingest` | Ingests a raw text clinical note, translates to EN if needed, runs the reasoning graph, and returns results. | Yes (If configured) |
| `POST` | `/ingest-file` | Ingests PDF, image, or audio records, extracts text context, and forwards it to the reasoning graph. | Yes (If configured) |
| `POST` | `/chat` | Handles multi-turn conversational Q&A over the clinical report in Clinical or Layperson mode. | Yes (If configured) |
| `POST` | `/explain/{note_id}` | Generates a layperson-friendly clinical report summary using analogies. | Yes (If configured) |
| `GET` | `/report/{note_id}` | Retrieves the saved report and applies dynamic target display translations. | Yes (If configured) |

---

## 2. API Security & Rate-Limiting

API security is configured in [main.py](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/main.py#L86-L103) via:
- **API Key Header**: `X-API-Key`
- **Bearer Token**: `Authorization: Bearer <API_KEY>`

If the environment variable `CLINICAL_REASONING_API_KEY` is empty or set to `dev-mode-unsafe`, authentication is bypassed.

### Rate Limiter
The FastAPI backend enforces a rate limiter via `RateLimitMiddleware` (configured by default to **60 requests per minute** per client IP) on all API endpoints. Exceeding this limit returns a `429 Too Many Requests` JSON response:
```json
{
  "detail": "Too many requests. Please try again in a minute."
}
```

---

## 3. Endpoint Specifications

### 3.1. `GET /health`
Returns runtime details of models, database connectivity, and environment variables.

#### Response Example
```json
{
  "status": "healthy",
  "database": "connected",
  "translator": {
    "transformers_available": true,
    "langdetect_available": true,
    "cached_models": ["fr", "es", "de", "nl"]
  },
  "llm_configs": {
    "groq_configured": true,
    "nvidia_nim_configured": false
  },
  "confidence_calibrator": "loaded",
  "reranker": "loaded",
  "orchestration_policy": "loaded"
}
```

---

### 3.2. `POST /ingest`
Submits raw text for multi-agent reasoning analysis.

#### Request Body (JSON)
- `note_id` (string, required): A unique reference ID.
- `note_text` (string, required): Raw clinician note.
- `lang` (string, optional): Input language. Defaults to `"auto"`. Supported: `en`, `de`, `fr`, `nl`, `es`.
- `display_lang` (string, optional): Return translation language. Defaults to `"en"`.

```json
{
  "note_id": "demo-001",
  "note_text": "ADMISSION SUMMARY:\nPatient admitted with fever and cough...",
  "lang": "auto",
  "display_lang": "es"
}
```

#### Response (JSON)
Returns the stored English report payload, and a translated copy under `display_report` if `display_lang` is not English.
```json
{
  "note_id": "demo-001",
  "lang": "en",
  "display_lang": "es",
  "timeline": { ... },
  "differentials": [ ... ],
  "contradictions": [ ... ],
  "confidence_scores": [ ... ],
  "display_report": {
    "timeline": { ... },
    "differentials": [ ... ],
    "contradictions": [ ... ]
  }
}
```

---

### 3.3. `POST /ingest-file`
Uploads a document or audio file for analysis. Supported formats: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.wav`, `.mp3`, `.m4a`.
Maximum file size: **10 MB**.

#### Request (Multipart Form Data)
- `file` (file upload, required)
- `note_id` (string, optional): Generated if omitted.
- `lang` (string, optional): Input language (`"auto"`).
- `display_lang` (string, optional): Return translation language (`"en"`).

#### Text Extraction Fallbacks
1. **PDF**: Extracted via PyMuPDF. If scanned (no text), falls back to Tesseract OCR.
2. **Image**: Processed via Tesseract OCR.
3. **Audio**: Dispatched to Whisper STT via Groq or OpenAI APIs.

---

### 3.4. `POST /chat`
Submits a query to the chatbot. Conversational history is loaded from the database using the session's chat ID.

#### Request Body (JSON)
- `chat_id` (string, required): ID of the chat session.
- `message` (string, required): Clinician query.
- `mode` (string, optional): `"clinical"` (technical) or `"layperson"` (simplified analogies). Defaults to `"clinical"`.
- `note_id` (string, required): The clinical note report context to discuss.

```json
{
  "chat_id": "session-123",
  "message": "Why did you mark pneumonia as a status reversal?",
  "mode": "clinical",
  "note_id": "demo-001"
}
```

#### Response Example
```json
{
  "reply": "[Disclaimer: Research/demo model...] The contradiction was flagged because the patient's respiratory status was marked as resolved on Day 3, but the discharge summary documents an active prescription for Azithromycin due to ongoing productive cough.",
  "chat_id": "session-123"
}
```

---

### 3.5. `POST /explain/{note_id}`
Generates a simplified explanation of the reasoning report for a patient or layperson.

#### Response Example
```json
{
  "note_id": "demo-001",
  "plain_language_summary": "### Clinical Summary\nYou were admitted with a high temperature...\n\n### Diagnosis Analogies\nThink of the heart's rhythm like a drummer in a band...",
  "generated_at": "2026-07-18T12:00:00Z"
}
```

---

## 4. LLM API Pacing & Guardrails

To prevent rate limits (`429`) when running against external LLM providers (e.g., Groq, NVIDIA NIM), the backend uses thread-safe pacing queues defined in:
- [groq_guardrails.py](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/groq_guardrails.py)
- [nim_guardrails.py](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/nim_guardrails.py)

### Configurations
- `MIN_INTERVAL_SECONDS`: The minimum time window enforced between consecutive API queries (e.g., 4s for Groq).
- `MAX_RETRIES`: Number of retry attempts.
- `BACKOFF_SECONDS`: Multiplier for exponential backoff delays.
