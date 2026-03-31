CREATE TABLE IF NOT EXISTS clinical_notes (
    id TEXT PRIMARY KEY,
    raw_text TEXT NOT NULL,
    extractor_backend TEXT NOT NULL,
    warnings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reasoning_outputs (
    id TEXT PRIMARY KEY,
    note_id TEXT NOT NULL UNIQUE REFERENCES clinical_notes(id) ON DELETE CASCADE,
    timeline_json JSONB NOT NULL,
    differentials_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    contradictions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    reasoning_trace_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reasoning_outputs_note_id ON reasoning_outputs(note_id);
