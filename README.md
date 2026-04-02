# Clinical Reasoning Engine

An end-to-end MVP for extracting structured clinical timelines from discharge notes, detecting temporal contradictions, generating differential hypotheses, scoring confidence, and exposing the results through a FastAPI backend plus React audit UI.

## What is implemented

- `backend/ingestion/ner_extractor.py`
  Uses `en_core_sci_sm` when available and falls back to a deterministic clinical phrase matcher so the project remains runnable in local/test environments.
- `backend/ingestion/timeline_builder.py`
  Builds an admission -> hospital course -> discharge timeline with typed events, sentence spans, offsets, domains, and status tags.
- `backend/agents/differential.py`
  Ranks likely diagnoses from structured note evidence plus local RAG retrieval.
- `backend/agents/contradiction.py`
  Detects `missing_symptom`, `new_finding`, and `status_reversal` contradictions with evidence pointers.
- `backend/agents/confidence.py`
  Produces feature-calibrated confidence and uncertainty scores from structured evidence, retrieval strength, and contradiction burden.
- `backend/agents/meta.py`
  Assembles the final structured JSON report and reasoning trace.
- `backend/agents/graph.py`
  Wires the full multi-agent pipeline in LangGraph, including policy checkpoints around ranking and contradiction analysis.
- `backend/main.py`
  FastAPI app with `POST /ingest`, `GET /report/{note_id}`, and `GET /health`.
- `backend/translation_layer.py`
  Edge translation layer for `de`, `fr`, `nl`, and `es` input/output while keeping the internal pipeline in English.
- `backend/db/schema.sql`
  Neon/Postgres-style schema for note + reasoning storage.
- `frontend/`
  React/Vite audit interface for timeline view, contradiction cards, and confidence bars.
- `tests/`
  Ten realistic synthetic notes plus API/pipeline tests.
- `scripts/evaluate.py`
  Runs a small benchmark suite and reports top-k differential accuracy plus contradiction precision/recall/F1.
- `scripts/train_reranker.py`
  Learns simple reranker weights from labeled evaluation cases.
- `scripts/train_confidence_calibrator.py`
  Learns calibration weights from observed hypothesis correctness.
- `scripts/train_orchestration_policy.py`
  Learns a retrieval threshold for post-contradiction orchestration decisions.

## Local development

```bash
cd clinical-reasoning-engine
.\venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\venv\Scripts\uvicorn.exe backend.main:app --reload
```

Optional local NLP extras if you want the scispaCy extractor instead of the built-in fallback:

```bash
.\venv\Scripts\python.exe -m pip install -r backend/requirements-optional-nlp.txt
```

API endpoints:

- `GET /health`
- `POST /ingest`
- `GET /report/{note_id}`

Example request:

```json
{
  "note_id": "demo-note",
  "note_text": "ADMISSION SUMMARY:\nPatient admitted with fever and cough...",
  "lang": "auto"
}
```

Multilingual flow:

- Input note in `de`, `fr`, `nl`, or `es`
- Translate to English at the API edge
- Run the full reasoning pipeline in English
- Build a translated `display_report` for the UI
- Keep the original structured report in English for stable internal semantics

Frontend in a second terminal:

```bash
cd clinical-reasoning-engine/frontend
npm install
npm run dev
```

Optional env var:

- `VITE_API_URL=http://localhost:8000`

## Deployment

Recommended stack for this repo:

- Backend: Railway
- Frontend: Vercel
- Database: Neon Postgres

### Railway backend

Set Railway root directory to the repo root and deploy the included `Dockerfile` or `railway.json`.

Required Railway env vars:

- `DATABASE_URL`: Neon connection string
- `CLINICAL_REASONING_CORS_ORIGINS`: your Vercel frontend URL, for example `https://your-app.vercel.app`
- `PORT`: provided by Railway automatically

Optional Groq env vars for free-tier protection:

- `GROQ_API_KEY`: your Groq API key
- `GROQ_MODEL`: defaults to `llama-3.1-8b-instant`
- `GROQ_MAX_RETRIES`: defaults to `1`
- `GROQ_MIN_INTERVAL_SECONDS`: defaults to `4`
- `GROQ_BACKOFF_SECONDS`: defaults to `8`
- `GROQ_TIMEOUT_SECONDS`: defaults to `30`

Start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Deployment note:

- Railway should install `backend/requirements.txt`
- Do not install `backend/requirements-optional-nlp.txt` on Railway unless you intentionally want to compile heavy NLP dependencies
- The app already falls back to a deterministic extractor when scispaCy is unavailable

### Vercel frontend

Set the Vercel project root to `frontend/`.

Required Vercel env var:

- `VITE_API_URL=https://your-railway-backend.up.railway.app`

The included `frontend/vercel.json` is ready for a Vite static deploy.

### Neon database

Create a Neon Postgres database and paste its pooled connection string into Railway as `DATABASE_URL`.

Schema notes:

- The app now persists reports through SQLAlchemy.
- If `DATABASE_URL` is missing locally, it falls back to SQLite at `backend/db/reports.sqlite3`.

### Local fallback

```powershell
.\start.ps1
```

### Groq rate-limit guidance

If you use the free Groq tier, start with:

```env
GROQ_MODEL=llama-3.1-8b-instant
GROQ_MAX_RETRIES=1
GROQ_MIN_INTERVAL_SECONDS=4
GROQ_BACKOFF_SECONDS=8
GROQ_TIMEOUT_SECONDS=30
```

This repo now includes a reusable guardrail helper in `backend/groq_guardrails.py` so future Groq-powered calls can share the same pacing and retry rules.

## Test suite

```bash
cd clinical-reasoning-engine
.\venv\Scripts\python.exe -m pytest -q
```

## Evaluation

```bash
cd clinical-reasoning-engine
.\venv\Scripts\python.exe scripts/evaluate.py
```

This prints:

- top-1 differential accuracy
- top-3 differential accuracy
- contradiction precision
- contradiction recall
- contradiction F1
- mean reciprocal rank
- Brier score

## Training hooks

```bash
cd clinical-reasoning-engine
.\venv\Scripts\python.exe scripts/train_reranker.py
.\venv\Scripts\python.exe scripts/train_confidence_calibrator.py
.\venv\Scripts\python.exe scripts/train_orchestration_policy.py
```

Saved artifacts:

- `backend/ml/artifacts/reranker_weights.json`
- `backend/ml/artifacts/confidence_calibrator.json`
- `backend/ml/artifacts/orchestration_policy.json`

## Notes

- The project prefers scispaCy `en_core_sci_sm`; in this workspace that model is not installed, so tests run against the deterministic fallback extractor.
- The confidence agent is implemented as a deterministic feature-calibrated scorer so the system remains locally testable while exposing interpretable confidence features.
- The differential agent now uses a local retrieval layer over a small curated clinical knowledge base, which is intentionally lightweight and demo-oriented rather than exhaustive.
- The differential stack now includes a learned reranker over structured and retrieval-backed features.
- The confidence agent uses a learned feature-calibrated scoring model over differential score, retrieval strength, support count, section coverage, rank, and contradiction burden.
- The orchestration layer is policy-driven and currently logs decisions around reranking, contradiction analysis, and additional retrieval opportunities.
- The multilingual layer uses Helsinki-NLP MarianMT models via HuggingFace and supports auto-detection through `langdetect`.
- Translation is best-effort and general-domain. Clinical terminology may be imperfect for some European-language notes, so this should be called a demo-safe capability rather than production-grade medical translation.
- Translation models are lazy-loaded and cached per language, but they are still large and may increase memory pressure on low-tier deployments.
