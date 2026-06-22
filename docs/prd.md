# Product Requirements Document (PRD)
## Clinical Reasoning Engine

---

## 1. Executive Summary & Overview
The **Clinical Reasoning Engine** is an intelligent assistant designed to ingest unstructured clinical discharge notes, reconstruct them into structured timelines, detect clinical or temporal contradictions, rank likely differential diagnoses, and provide calibrated confidence scores. It is built to assist clinical auditors, hospital compliance officers, and healthcare professionals in verifying the semantic consistency of discharge summaries and improving audit efficiency.

---

## 2. Product Objectives
- **Semantic Reconstruction**: Translate narrative-heavy, unstructured discharge notes into a queryable, structured event timeline spanning Admission, Hospital Course, and Discharge.
- **Contradiction Auditing**: Identify critical temporal and clinical contradictions (e.g., resolving a symptom mid-stay that is noted as a severe active problem at discharge) to reduce clinical errors.
- **Calibrated Hypotheses**: Generate differential diagnosis rankings supported by both structured internal evidence and relevant external clinical knowledge retrieved dynamically (RAG).
- **Multilingual Support**: Allow clinicians to work in their native languages (`de`, `fr`, `nl`, `es`, `en`) while keeping the core reasoning pipeline semantics standardized in English.

---

## 3. User Personas
### 3.1. Clinical Auditor
- **Goal**: Audit patient charts and discharge records for diagnostic consistency and documentation compliance.
- **Pain Point**: Discharge summaries are often verbose, disorganized, and contain conflicting statements (e.g., "resolved pneumonia" in one section, and "active cough requiring azithromycin" in another). Reading them manually is slow and error-prone.

### 3.2. Healthcare Provider (Admitting/Discharging Physician)
- **Goal**: Quickly review a patient's trajectory during an audit or transition of care.
- **Pain Point**: Reviewing notes from other providers is tedious, and important new onset issues might be missed in long summaries.

---

## 4. Key Functional Requirements

| Ref # | Feature | Description | Priority |
| :--- | :--- | :--- | :--- |
| **FR-1** | **Timeline Extraction** | Segment notes into Admission, Hospital Course, and Discharge. Extract clinical entities (Symptoms, Diagnoses, Procedures, Medications, Vitals, Labs) and associate them with event status (e.g., active, new, stable, resolved). | **P0** |
| **FR-2** | **Contradiction Detection** | Scan timelines to identify three classes of temporal contradictions: `missing_symptom` (present at admission but not resolved or mentioned at discharge), `new_finding` (appears at discharge without preceding context), and `status_reversal` (worsened at discharge despite being resolved in the hospital course). | **P0** |
| **FR-3** | **Differential Diagnosis Generation** | Match timeline events against clinical guidelines and use a dual-mode Retrieval-Augmented Generation (RAG) knowledge base. Connected to PostgreSQL, utilizes `pgvector` semantic embedding similarity search (via `nvidia/nv-embedqa-e5-v5`). Under SQLite (local development), falls back to a lexical TF-IDF matching engine. | **P0** |
| **FR-4** | **Learned Reranking** | Use a trained model over structural features (base score, section coverage, discharge support) to score and sort candidates. | **P1** |
| **FR-5** | **Calibrated Confidence** | Provide Brier-calibrated confidence and uncertainty scores for each hypothesis using logistic regression over feature markers. | **P0** |
| **FR-6** | **Multilingual Edge Layer** | Support auto-detect and translation for German, French, Dutch, and Spanish. Process the core logic in English and translate outputs back to the requested display language. | **P1** |
| FR-7 | **Audit Dashboard** | A responsive web interface displaying the segmented timeline, flagged contradictions with evidence, and ranked diagnoses with interactive confidence visualizers. | **P0** |
| **FR-8** | **Document Ingestion** | Support direct ingestion of PDF reports (both native text and scanned via OCR), image photos (PNG/JPG via Tesseract OCR), and audio voice recordings (WAV/MP3 via Whisper transcribing) in addition to raw text. | **P1** |
| **FR-9** | **Conversational Chatbot** | Provide interactive Q&A over the patient report findings, with a select option for **Clinical Mode** (technical vocabulary) vs. **Layperson Mode** (simple wording, analogies). Enforce medical disclaimer prominence. | **P1** |
| **FR-10**| **Plain-Language Summary** | Generate a structured patient-friendly translation/summary of the entire clinical report (Timeline events, warnings, and diagnosis breakdowns using analogies). | **P1** |

---

## 5. Non-Functional Requirements

### 5.1. Accuracy & Reliability
- **Differential Ranking**: Reranker should maintain high Top-3 accuracy compared to baseline heuristics.
- **Contradiction Precision/Recall**: Target > 80% F1 score on synthetic validation notes.
- **Confidence Calibration**: Minimize Brier score (< 0.15) to ensure confidence percentages correspond closely to empirical correctness.

### 5.2. Performance & Latency
- **FastAPI Edge Response**: Response time under 2 seconds for English notes.
- **Translation Overhead**: Edge translation using Helsinki-NLP models may introduce up to 5 seconds latency depending on host memory and hardware configuration (CPU/GPU).
- **Caching**: Translation models must be cached in memory to prevent repeat disk loads.
- **API Rate-Limit Pacing**: Support automatic retry backoff and token pacing when connecting to downstream LLM inference providers (Groq, NVIDIA NIM) to prevent model provider rate limits.

### 5.3. Architecture & Deployability
- **Self-Contained Baseline**: The application must run locally without external API keys (using rule-based extractors and local SQLite) for testing.
- **Production Deployment**: Support deployment on Render (backend API), Vercel (frontend), and Neon (PostgreSQL database), with configurable API endpoints for Groq or NVIDIA NIM.

---

## 6. Future Product Roadmap

To transition the Clinical Reasoning Engine from a prototype to a production-grade system serving real clinicians, we have established the following engineering roadmap:

### 6.1. Enhanced OCR Accuracy via VLMs
- **Objective**: Replace the local Tesseract OCR engine with a visual language model (VLM) such as **Meta Llama-3.2-11b-Vision-Instruct**.
- **User Impact**: Drastically improves the layout parsing of complex multi-column medical charts, lab results tables, and printed text. 

### 6.2. Two-Phase Semantic RAG (`pgvector`) [IMPLEMENTED]
- **Status**: Completed. Connected PostgreSQL to utilize the `pgvector` extension powered by **NVIDIA Retrieval QA Embeddings** (`nvidia/nv-embedqa-e5-v5`), with a robust local SQLite TF-IDF keyword fallback. Seeding/indexing is managed automatically at server startup.

### 6.3. Dictation Verification safety Gate
- **Objective**: Introduce a mandatory dictation transcription verification card inside the UI before running the clinical reasoning agents over audio note transcripts.
- **User Impact**: Clinicians can review, edit, and approve transcribing results from Canary-1b STT, avoiding propagation of audio speech errors (e.g. transcribing "PO2" as "PO too") into down-stream clinical contradiction warnings.

### 6.4. Production Infrastructure scaling
- **Objective**: Transition downstream external NIM endpoints from shared free catalog infrastructure (which are rate-limited and subject to change) to dedicated, self-hosted NIM containers running on private GPU nodes.

---

## 7. Document Links
- Technical Details: [trd.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/trd.md)
- UI/UX Specifications: [ux_ui_design.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/ux_ui_design.md)
- Database Layout: [backend_schema.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/backend_schema.md)
- Implementation and Training Guide: [implementation_guide.md](file:///C:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/docs/implementation_guide.md)
