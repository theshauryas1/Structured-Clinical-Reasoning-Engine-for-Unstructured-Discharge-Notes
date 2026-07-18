# Developer Onboarding Guide

Welcome to the **Clinical Reasoning Engine** project! This guide walks you through setting up your local environment, running tests, benchmarking performance, and retraining the ML calibration models.

---

## 1. Local Development Setup

### 1.1. System Requirements
- **Python**: Version 3.10 or 3.11 recommended.
- **Node.js**: Version 18+ and npm installed.
- **Tesseract OCR**:
  - *Windows*: Download the installer from the UB Mannheim repository. Add `C:\Program Files\Tesseract-OCR` to your system `PATH` env.
  - *macOS*: Install via Homebrew: `brew install tesseract`.
  - *Linux*: Run `sudo apt-get install -y tesseract-ocr`.
- **API Keys**: Access keys for Groq (`GROQ_API_KEY`) or NVIDIA NIM (`NVIDIA_NIM_API_KEY`) to enable LLM-based reasoning and transcription fallbacks.

### 1.2. Backend Installation
1. Navigate to the project directory:
   ```bash
   cd clinical-reasoning-engine
   ```
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   # Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install base dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. *(Optional)* Install optional NLP tools if you want scispaCy support:
   ```bash
   pip install -r backend/requirements-optional-nlp.txt
   ```
5. Create and configure your environment variables by renaming or editing `.env`:
   ```env
   # Database path
   CLINICAL_REASONING_DB_PATH=backend/db/reports.sqlite3
   # Groq key
   GROQ_API_KEY=your-api-key
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The backend API will be available at `http://localhost:8000`.

### 1.3. Frontend Installation
1. Open a new terminal window and navigate to the frontend folder:
   ```bash
   cd clinical-reasoning-engine/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The dashboard will be active at `http://localhost:5173`.

---

## 2. Validation & Testing

### 2.1. Running the Test Suite
Ensure your virtual environment is active, then run:
```bash
cd clinical-reasoning-engine
.\venv\Scripts\python.exe -m pytest -v
```
This tests timeline construction, translation modules, database connections, and multi-agent operations.

### 2.2. Running Evaluations & Benchmarks
Execute the evaluation suite to measure top-k accuracy, MRR, and Brier scores:
```bash
python scripts/evaluate.py
```

---

## 3. Retraining Calibration Models

If you update the clinical guidelines database or add new note templates, you must retrain the scoring weights:

### 3.1. Reranker
Trains linear weights comparing timeline features to correct diagnoses:
```bash
python scripts/train_reranker.py
```
Output: [reranker_weights.json](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/ml/artifacts/reranker_weights.json).

### 3.2. Confidence Calibrator
Fits logistic regression weights to map RAG scoring outputs to calibrated percentages:
```bash
python scripts/train_confidence_calibrator.py
```
Output: [confidence_calibrator.json](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/ml/artifacts/confidence_calibrator.json).

### 3.3. Orchestration Policy
Tunes retrieval thresholds and logging triggers:
```bash
python scripts/train_orchestration_policy.py
```
Output: [orchestration_policy.json](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/ml/artifacts/orchestration_policy.json).
