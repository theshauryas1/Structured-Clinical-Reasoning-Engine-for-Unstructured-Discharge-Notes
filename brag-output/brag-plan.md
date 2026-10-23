# Brag Plan: Clinical Reasoning Engine (Launch & Architecture Edition)

## What is this app?
The **Structured Clinical Reasoning Engine for Unstructured Discharge Notes** is a multi-agent AI system that parses raw, narrative hospital discharge summaries into chronological clinical timelines, flags latent temporal contradictions, generates guideline-backed differential diagnoses using RAG, and outputs feature-calibrated confidence scores.

## The angle
Discharge summaries are rushed, dense, and written by multiple rotating clinicians. They are filled with latent contradictions (symptoms marked resolved, but discharged on active treatment), unaddressed admission problems, and missed secondary diagnoses. The Clinical Reasoning Engine acts as an automated audit helper with:
- **Multimodal Ingestion**: Scanned PDF OCR (PyMuPDF + Tesseract), clinician audio dictation (Whisper STT with human approval), and edge language translation (MarianMT).
- **LangGraph State Graph**: 5 specialist reasoning nodes with intermediate policy checkpoints (`plan_after_differential`, `plan_after_contradiction`).
- **Hybrid Relational & Vector RAG**: SQLite/Neon PostgreSQL parity with `pgvector` 1024-dim cosine distance lookups for clinical guidelines.
- **Empirical 1,000-Case Benchmark**: 94.2% Top-1 Diagnostic Accuracy, 100.0% Top-3 Accuracy, 0.9705 MRR, and 54.9 cases/sec throughput.

---

## Storyboard (52.0 Seconds / 7 Scenes)

### Scene 1: The Hook & Core Value Proposition (0.0s – 7.4s)
- **Visual**: Medical cyber-slate ground with pulsing cyan indicator: `CLINICAL NLP & MULTI-AGENT DIAGNOSTICS`. Hero title: `Clinical Reasoning Engine`. Subtitle: `Automated Timeline Extraction, Contradiction Detection & Calibrated Differentials`.
- **Stat Cards**: 1,000 Cases (Evaluated Benchmark), 94.2% (Top-1 Accuracy), 100.0% (Top-3 Coverage), 54.9 / sec (Throughput Speed).
- **Sound**: Medical monitor heartbeat pulse (D2/F2) with warm atmospheric pads.

### Scene 2: Multimodal Ingestion & Edge Translation (7.4s – 14.8s)
- **Visual**: 4 Ingestion Channel Cards:
  - `Scanned & Native PDF`: PyMuPDF with automatic fallback to local Tesseract OCR.
  - `Clinician Audio Dictation`: Serverless Whisper STT with verification gate before reasoning.
  - `MarianMT Edge Translation`: Helsinki-NLP transformer models translating DE, FR, NL, ES to English for stable clinical semantics.
  - `Clinical NER Extractor`: ScispaCy `en_core_sci_sm` mapping medical entities with regex fallbacks.
- **Sound**: Crisp scanner shutter hit and rising synthesizer sweep.

### Scene 3: LangGraph Multi-Agent State Graph (14.8s – 22.2s)
- **Visual**: 5-node agent pipeline layout:
  - Node 1: `Timeline Segmenter` (Admission &rarr; Course &rarr; Discharge chronological mapping).
  - Node 2: `Differential Agent` (Clinical guideline vector RAG + linear reranker).
  - Node 3: `Contradiction Agent` (Flags status reversals, missing symptoms, new findings).
  - Node 4: `Confidence Agent` (8-pass perturbation variance + logistic regression calibrator).
  - Node 5: `Meta Agent` (Synthesis into final structured JSON & audit traces).
- **Sound**: Multi-node activation arpeggio cascade.

### Scene 4: Database Layout & Hybrid Vector RAG (22.2s – 29.6s)
- **Visual**: Split storage architecture:
  - Left: Relational Schemas (`clinical_notes`, `reasoning_outputs` native JSONB, `chats`, SQLite/Postgres parity).
  - Right: `pgvector` 1024-dimension embeddings for `clinical_guidelines` table with cosine distance (`<=>`), plus thread-safe LLM rate pacing guardrails.
- **Sound**: Low resonant bass drop and vector query glide.

### Scene 5: Contradiction Auditing & Clinical Safety (29.6s – 37.0s)
- **Visual**: Live clinical audit terminal frames:
  - Left: `Status Reversal Flagged`: Severe dyspnea marked resolved on Day 2, but discharged home on continuous O2 therapy.
  - Right: `Calibrated Confidence Scoring`: Heart Failure Exacerbation (Base Score 0.72 + Coverage 1.0 - Penalty 0.10 &rarr; Calibrated Probability 0.812 &plusmn;0.045).
  - Bottom: Mandatory Clinical Research Disclaimer.
- **Sound**: Two-tone medical monitor alert beep followed by a crystal D5 calibration chime.

### Scene 6: 1,000-Case Empirical Benchmark (37.0s – 44.4s)
- **Visual**: 4 empirical evidence counters:
  - `94.2%`: Top-1 Accuracy across all 1,000 cases.
  - `100.0%`: Top-3 Coverage (Zero false exclusions).
  - `0.9705`: Mean Reciprocal Rank (MRR).
  - `54.9 /s`: Throughput speed (1,000 cases in 18.2 seconds).
  - Breakdown: Stroke (100%), Pneumonia (100%), Knee Arthroplasty (95.8%), A-Fib (94.0%).
- **Sound**: Driving electronic percussion and 120Hz rhythmic impact.

### Scene 7: Production Deployment & Source-Available CTA (44.4s – 52.0s)
- **Visual**: Google Cloud Run showcase with live links:
  - React Audit Dashboard (Interactive Timeline & Contradiction Cards)
  - FastAPI Backend REST Gateway (`/ingest`, `/chat`, `/explain`)
  - Google Cloud Run (`clinical-cre` on `us-central1`)
  - Author: **Shaurya Sharma**
- **Punchline**: "Source-available for evaluation & review • Explore the clinical architecture."
- **Sound**: Resolving C5 crystal tone and smooth master fade.

---

## Technical Specifications
- **Resolution**: 1920x1080 (1080p Full HD)
- **Framerate**: 30.0 fps (1560 frames total)
- **Duration**: 52.0 seconds
- **Audio**: 48,000 Hz, 16-bit Stereo WAV synthesized via NumPy/SciPy
- **Video Codec**: H.264 (High Profile, YUV420p, CRF 18, faststart enabled)
- **Audio Codec**: AAC-LC @ 192 kbps
- **Poster**: 1920x1080 JPEG baked into frame 0 and saved as `brag.jpg`
