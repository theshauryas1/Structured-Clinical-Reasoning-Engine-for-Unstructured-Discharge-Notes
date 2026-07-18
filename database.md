# Database Schema & Models Layout

This document details the database storage engine, Entity-Relationship mappings, SQLAlchemy schemas, and structured JSON payloads used by the **Clinical Reasoning Engine**.

---

## 1. Storage & Engines Setup

The application supports database-engine parity:
- **Local Development**: Configured to run against a self-contained SQLite database file located at `backend/db/reports.sqlite3`. Columns representing complex structures store plain JSON text.
- **Production Layer**: Configured to run against Neon PostgreSQL. Utilizes the native `JSONB` column formats for fast parsing, indexing, and querying. Clinical guidelines RAG similarity queries utilize the PostgreSQL `pgvector` extension for cosine distance lookups.
- **ORM Interface**: Initialized via SQLAlchemy in [models.py](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/db/models.py) and schema scripts in [schema.sql](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/db/schema.sql).

---

## 2. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS {
        string id PK
        string username UNIQUE
        string password_hash
        datetime created_at
    }
    USER_SESSIONS {
        string token PK
        string user_id FK
        datetime created_at
        datetime expires_at
    }
    CLINICAL_NOTES {
        string id PK
        string user_id FK
        string raw_text
        string extractor_backend
        jsonb warnings_json
        datetime created_at
    }
    REASONING_OUTPUTS {
        string id PK
        string note_id FK "Unique"
        jsonb timeline_json
        jsonb differentials_json
        jsonb contradictions_json
        jsonb confidence_json
        jsonb reasoning_trace_json
        jsonb orchestration_trace_json
        jsonb report_json
        datetime generated_at
    }
    CLINICAL_GUIDELINES {
        int id PK
        string condition UNIQUE
        string summary
        string follow_up
        vector embedding "1024-dim"
        datetime created_at
    }
    CHATS {
        string id PK
        string user_id FK
        string title
        string note_id FK
        datetime created_at
    }
    CHAT_MESSAGES {
        string id PK
        string chat_id FK
        string role
        string content
        string media_name
        string media_content
        datetime created_at
    }

    USERS ||--o{ USER_SESSIONS : "authenticates"
    USERS ||--o{ CLINICAL_NOTES : "owns"
    USERS ||--o{ CHATS : "initiates"
    CLINICAL_NOTES ||--|| REASONING_OUTPUTS : "produces"
    CLINICAL_NOTES ||--o{ CHATS : "references"
    CHATS ||--o{ CHAT_MESSAGES : "contains"
```

---

## 3. Core Database Tables

For SQLAlchemy model definitions, see [models.py](file:///c:/Structured%20Clinical%20Reasoning%20Engine%20for%20Unstructured%20Discharge%20Notes/clinical-reasoning-engine/backend/db/models.py).

### 3.1. `users`
Tracks auditor/clinician user accounts.
- Columns: `id` (VARCHAR(64), PK), `username` (VARCHAR(64), UNIQUE), `password_hash` (TEXT), `created_at` (TIMESTAMPTZ).

### 3.2. `user_sessions`
Tracks authentication tokens.
- Columns: `token` (VARCHAR(64), PK), `user_id` (FK to `users.id`, ON DELETE CASCADE), `created_at` (TIMESTAMPTZ), `expires_at` (TIMESTAMPTZ).

### 3.3. `clinical_notes`
Tracks the original ingested clinician reports.
- Columns: `id` (VARCHAR(64), PK), `user_id` (FK to `users.id`, NULLABLE), `raw_text` (TEXT), `extractor_backend` (VARCHAR(64)), `warnings_json` (JSONB/JSON), `created_at` (TIMESTAMPTZ).

### 3.4. `reasoning_outputs`
Stores the outputs and intermediate traces of the reasoning graph.
- Columns: `id` (VARCHAR(64), PK), `note_id` (FK to `clinical_notes.id`, UNIQUE, ON DELETE CASCADE), `timeline_json` (JSONB/JSON), `differentials_json` (JSONB/JSON), `contradictions_json` (JSONB/JSON), `confidence_json` (JSONB/JSON), `reasoning_trace_json` (JSONB/JSON), `orchestration_trace_json` (JSONB/JSON), `report_json` (JSONB/JSON), `generated_at` (TIMESTAMPTZ).

### 3.5. `chats` & `chat_messages`
Stores multi-turn conversational records over patient files.
- `chats`: `id` (PK), `user_id` (FK to `users.id`), `title` (VARCHAR(255)), `note_id` (FK to `clinical_notes.id`, NULLABLE), `created_at` (TIMESTAMPTZ).
- `chat_messages`: `id` (PK), `chat_id` (FK to `chats.id`, ON DELETE CASCADE), `role` (VARCHAR(64) - e.g., 'user', 'assistant'), `content` (TEXT), `media_name` (VARCHAR(255)), `media_content` (TEXT), `created_at` (TIMESTAMPTZ).

### 3.6. `clinical_guidelines`
Contains embedded medical guidelines utilized by the RAG retrieval layer.
- Columns: `id` (INTEGER, PK, SERIAL), `condition` (TEXT, UNIQUE), `summary` (TEXT), `follow_up` (TEXT), `embedding` (vector(1024), ONLY ON POSTGRES), `created_at` (TIMESTAMPTZ).

---

## 4. Key JSON Layout Specs

### 4.1. `timeline_json`
```json
{
  "sections": [
    {
      "name": "admission",
      "text": "...",
      "events": [
        {
          "text": "dyspnea",
          "label": "SYMPTOM",
          "normalized_text": "dyspnea",
          "domain": "cardiovascular",
          "section": "admission",
          "sentence_text": "Patient admitted with severe dyspnea.",
          "status": "active",
          "start": 22,
          "end": 29
        }
      ]
    }
  ]
}
```

### 4.2. `contradictions_json`
```json
[
  {
    "type": "status_reversal",
    "entity": "respiratory distress",
    "description": "Marked resolved in course, but active at discharge.",
    "admission_evidence": {
      "text_span": "respiratory distress resolved",
      "section": "hospital_course",
      "sentence_text": "Patient's respiratory distress resolved on Day 2."
    },
    "discharge_evidence": {
      "text_span": "discharged home on continuous O2",
      "section": "discharge",
      "sentence_text": "Patient discharged home on continuous O2."
    },
    "confidence": 0.88
  }
]
```

### 4.3. `confidence_json`
```json
[
  {
    "hypothesis": "Heart failure exacerbation",
    "confidence": 0.812,
    "uncertainty": 0.045,
    "mean_score": 0.825,
    "features": {
      "base_score": 0.72,
      "retrieval_score": 0.65,
      "support_count": 0.5,
      "section_coverage": 1.0,
      "contradiction_penalty": 0.1
    }
  }
]
```
