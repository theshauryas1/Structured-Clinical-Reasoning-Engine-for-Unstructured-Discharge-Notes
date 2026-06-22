# Implementation and Training Guide
## Clinical Reasoning Engine

---

## 1. Local Development Setup
To run the Clinical Reasoning Engine on your machine, follow these setup steps:

### 1.0. System-Level Dependencies
For document ingestion and OCR capabilities, the following system-level configurations are required:
- **Tesseract OCR**:
  - *Windows*: Install via the UB Mannheim installer. Add `C:\Program Files\Tesseract-OCR` (or your custom install directory) to your system `PATH`.
  - *macOS*: Run `brew install tesseract`.
  - *Linux / Debian*: Run `sudo apt-get install -y tesseract-ocr`. (This is handled automatically in the production Docker image).
- **Audio Transcription Keys**: Ensure either `GROQ_API_KEY` or `OPENAI_API_KEY` is present in your environment variables to enable the Whisper API transcription fallback.

### 1.1. Backend Setup
1. Open a terminal and navigate to the project directory:
   ```bash
   cd clinical-reasoning-engine
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the required base dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. *(Optional)* Install optional NLP tools if you want scispaCy support:
   ```bash
   pip install -r backend/requirements-optional-nlp.txt
   ```
5. Run the FastAPI development server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The backend API will be available at `http://localhost:8000`.

### 1.1.1. Environment Variables Configuration
Configure your backend environment by renaming or editing `.env` in the root folder:
```env
# Database configuration
CLINICAL_REASONING_DB_PATH=backend/db/reports.sqlite3

# Groq LLM configuration (Optional)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_MAX_RETRIES=1
GROQ_MIN_INTERVAL_SECONDS=4
GROQ_BACKOFF_SECONDS=8
GROQ_TIMEOUT_SECONDS=30

# NVIDIA NIM configuration (Optional)
NVIDIA_NIM_API_KEY=your_nvidia_nim_api_key
NVIDIA_NIM_MODEL=meta/llama-3.1-8b-instruct
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MAX_RETRIES=1
NVIDIA_NIM_MIN_INTERVAL_SECONDS=1.0
NVIDIA_NIM_BACKOFF_SECONDS=4.0
NVIDIA_NIM_TIMEOUT_SECONDS=30.0
```


### 1.2. Frontend Setup
1. Open a second terminal window and navigate to the frontend directory:
   ```bash
   cd clinical-reasoning-engine/frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the Vite developer server:
   ```bash
   npm run dev
   ```
   The interactive dashboard will be available at `http://localhost:5173`.
   - Configure custom API URLs by setting `VITE_API_URL` inside `frontend/.env`.

---

## 2. Step-by-Step Data Flow (e.g. Ingestion of Spanish Notes)
Below is a trace of what happens when a user inputs a note in Spanish:

```mermaid
sequenceDiagram
    autonumber
    actor Clinician
    participant Frontend
    participant API as FastAPI Gateway
    participant TL as Translation Layer
    participant LG as LangGraph Engine
    participant DB as SQLite/PostgreSQL Database

    Clinician->>Frontend: Clicks "Analyze" on a Spanish note
    Frontend->>API: POST /ingest {note_text: "...", lang: "auto", display_lang: "es"}
    API->>TL: detect_input_language("...")
    TL-->>API: Returns source_language = "es"
    API->>TL: translate("...", src_lang="es", to_english=True)
    TL-->>API: Returns English translated text
    API->>LG: run_reasoning_pipeline(english_note)
    Note over LG: Timeline, Reranking, Contradiction checks,<br/>and Confidence calibration execute in English.
    LG-->>API: Returns NoteReport (in English)
    API->>TL: build_display_report(report_payload, display_language="es")
    TL-->>API: Returns translated report payload (in Spanish)
    API->>DB: save_report() [Persists original EN report + metadata]
    API-->>Frontend: Sends JSON (English report + Spanish display_report)
    Frontend-->>Clinician: Renders interactive Spanish Timeline, Contradictions, and Fills
```

---

## 3. Testing and Benchmarking

### 3.1. Automated Test Suite
Run unit tests to verify the integrity of timeline builders, contradiction agents, translation modules, file extraction/OCR, chatbot interactions, and plain-language summaries:
```bash
cd clinical-reasoning-engine
# Run all tests (including core pipeline and new additions)
.\venv\Scripts\python.exe -m pytest -v
```
- Tests are defined in the `tests/` directory (e.g., [test_additions.py](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/tests/test_additions.py) validates the newly added ingestion, Q&A, and explanation features).

### 3.2. Evaluation Suite
Evaluate the system's baseline diagnostic accuracy and contradiction classification scores:
- Script: [evaluate.py](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/scripts/evaluate.py)
- Execution:
  ```bash
  python scripts/evaluate.py
  ```
- Metrics output:
  - Top-1 and Top-3 differential accuracy.
  - Mean Reciprocal Rank (MRR).
  - Contradiction Precision, Recall, and F1-score.
  - Brier score (confidence calibration calibration check).

---

## 4. Machine Learning Retraining Hooks
If you modify the RAG database, extractors, or have new medical labels, you can retrain the rerank weights and calibration metrics using the provided scripts:

### 4.1. Reranker Training
Fits linear weights comparing hypothesis support features to correct diagnoses:
- Script: [train_reranker.py](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/scripts/train_reranker.py)
- Execution:
  ```bash
  python scripts/train_reranker.py
  ```
- Artifact generated: `backend/ml/artifacts/reranker_weights.json`

### 4.2. Confidence Calibrator Training
Fits logistic calibration weights using observed hypothesis success rates:
- Script: [train_confidence_calibrator.py](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/scripts/train_confidence_calibrator.py)
- Execution:
  ```bash
  python scripts/train_confidence_calibrator.py
  ```
- Artifact generated: `backend/ml/artifacts/confidence_calibrator.json`

### 4.3. Orchestration Policy Training
Sets optimal retrieval thresholds and workflow heuristics:
- Script: [train_orchestration_policy.py](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/scripts/train_orchestration_policy.py)
- Execution:
  ```bash
  python scripts/train_orchestration_policy.py
  ```
- Artifact generated: `backend/ml/artifacts/orchestration_policy.json`

---

## 5. Deployment Profiles
To prepare the system for cloud hosting, follow the guidelines below:

### 5.1. Database Setup (Neon Postgres)
1. Create a PostgreSQL project on Neon.
2. In the database dashboard, copy the pooled connection string.
3. Configure the backend env variable:
   ```env
   DATABASE_URL=postgresql://your-username:your-password@your-neon-host/neondb?sslmode=require
   ```

### 5.2. Backend Deploy (Render)
1. Link your git repository to Render.
2. Create a new **Web Service**, pointing the root directory to the repo root.
3. Set the build Command to compile base requirements (do not include optional NLP scripts to keep memory footprint light).
4. Configure required variables (`DATABASE_URL`, `PORT`, and `CLINICAL_REASONING_CORS_ORIGINS`), alongside LLM provider keys if using external inference models (`GROQ_*` or `NVIDIA_NIM_*`).
5. Set start command:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

### 5.3. Frontend Deploy (Vercel)
1. Import the repository project to Vercel.
2. Set the root directory of the build to `frontend/`.
3. Add the environment variable:
   ```env
   VITE_API_URL=https://your-render-backend-url.onrender.com
   ```
4. Vercel will build and serve the application as a static site using the configurations in `frontend/vercel.json`.

---

## 6. Implementation Setup for Roadmap Upgrades

### 6.1. Setting up `pgvector` in PostgreSQL [ACTIVE]
The system automatically creates the `vector` extension, sets up the `clinical_guidelines` table, and seeds embeddings at application startup.
1. Configure your Postgres database connection in `.env`:
   ```env
   DATABASE_URL=postgresql://your-username:your-password@your-neon-host/neondb?sslmode=require
   ```
2. Enable NVIDIA NIM credentials and set the preferred embedding model:
   ```env
   NVIDIA_NIM_API_KEY=nvapi-your-key-here
   NVIDIA_NIM_EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
   ```
3. When the FastAPI gateway launches (via `uvicorn backend.main:app`), the lifespan handler triggers `index_guidelines_to_postgres` defined in [index_guidelines.py](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/rag/index_guidelines.py) to enable extensions and index guidelines.

### 6.2. Two-Phase RAG Ingestion Pipeline [ACTIVE]
- **Startup Indexing**: Guidelines are loaded from `knowledge_base.jsonl`, embedded once using NIM's passage input type (`input_type="passage"`), and saved into the database's `clinical_guidelines` table.
- **Online Query Phase**: When analyzing notes, queries are generated from the extracted medical findings, embedded via the NIM query input type (`input_type="query"`), and evaluated against the database using a fast cosine distance query:
  ```sql
  SELECT condition, summary, follow_up, 1 - (embedding <=> CAST(:emb AS vector)) AS similarity
  FROM clinical_guidelines
  ORDER BY embedding <=> CAST(:emb AS vector)
  LIMIT 3;
  ```

### 6.3. Upcoming Audio Dictation Transcription Verification Gate
- To prevent transcription mistakes from polluting the LangGraph contradiction checker, place a validation step in the frontend. 
- In [App.jsx](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/frontend/src/App.jsx):
  1. Call `/ingest-file` (which returns the Canary-1b transcription).
  2. Display the text in an editable text box.
  3. Require the clinician to click "Approve and Run Reasoning Engine" before calling the main `/ingest` reasoning pipeline.

---

## 7. Document Links
- Product Context: [prd.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/prd.md)
- Technical Details: [trd.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/trd.md)
- UI/UX Specifications: [ux_ui_design.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/ux_ui_design.md)
- Database Layout: [backend_schema.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/backend_schema.md)
