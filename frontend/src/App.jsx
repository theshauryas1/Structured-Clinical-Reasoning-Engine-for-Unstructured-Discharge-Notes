import { useState } from "react";

const SAMPLE_NOTE = `ADMISSION SUMMARY:
Patient admitted with fever, cough, and shortness of breath.

HOSPITAL COURSE:
Fever resolved after 3 days on ceftriaxone and azithromycin. Oxygen requirement improved.

DISCHARGE DIAGNOSES AND PLAN:
Community-acquired pneumonia improved clinically. New onset atrial fibrillation noted during admission.`;

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

const styles = {
  page: {
    fontFamily: "Arial, sans-serif",
    background: "#f8f9fa",
    minHeight: "100vh",
    padding: "24px 16px 48px",
  },
  shell: {
    maxWidth: "860px",
    margin: "0 auto",
  },
  title: {
    marginBottom: "8px",
  },
  disclaimer: {
    color: "#b42318",
    fontWeight: 700,
    marginBottom: "20px",
  },
  textarea: {
    width: "100%",
    minHeight: "220px",
    padding: "14px",
    border: "1px solid #d0d5dd",
    borderRadius: "8px",
    resize: "vertical",
    background: "#ffffff",
    marginBottom: "14px",
  },
  buttonRow: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
    marginBottom: "18px",
  },
  primaryButton: {
    padding: "10px 15px",
    background: "#007bff",
    color: "white",
    border: "none",
    borderRadius: "5px",
    cursor: "pointer",
  },
  secondaryButton: {
    padding: "10px 15px",
    background: "#e9ecef",
    color: "#111827",
    border: "none",
    borderRadius: "5px",
    cursor: "pointer",
  },
  section: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: "10px",
    padding: "18px",
    marginTop: "18px",
  },
  timelineWrap: {
    borderLeft: "3px solid #007bff",
    paddingLeft: "12px",
  },
  timelineItem: {
    padding: "12px 0",
    borderBottom: "1px solid #e5e7eb",
  },
  timelineEvent: {
    marginTop: "8px",
    padding: "10px",
    background: "#f8fafc",
    borderRadius: "8px",
  },
  contradictionCard: {
    background: "#ffe6e6",
    padding: "12px",
    marginBottom: "10px",
    borderLeft: "5px solid red",
    borderRadius: "6px",
  },
  diagnosisCard: {
    padding: "12px",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    marginBottom: "10px",
    background: "#ffffff",
  },
  confidenceTrack: {
    background: "#ddd",
    borderRadius: "5px",
    overflow: "hidden",
    marginTop: "6px",
  },
  confidenceFill: {
    background: "#28a745",
    color: "white",
    padding: "5px",
    minWidth: "52px",
    whiteSpace: "nowrap",
  },
  meta: {
    color: "#475467",
    marginTop: "6px",
  },
  error: {
    color: "#b42318",
    marginTop: "8px",
  },
};

function formatSectionName(value) {
  if (!value) {
    return "Unknown";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function App() {
  const [input, setInput] = useState("");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const report = output?.display_report || output;
  const timeline = report?.timeline?.sections || [];
  const contradictions = report?.contradiction_flags || [];
  const differentials = report?.differentials || [];
  const confidenceScores = report?.confidence_scores || [];

  const confidenceByName = new Map();
  for (const item of confidenceScores) {
    confidenceByName.set(item.hypothesis, item.confidence);
  }

  const analyze = async () => {
    if (!input.trim()) {
      setError("Please paste a clinical note before analyzing.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ note_text: input }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Error processing request");
      }

      setOutput(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Error processing request");
    } finally {
      setLoading(false);
    }
  };

  const loadSample = () => {
    setInput(SAMPLE_NOTE);
    setError("");
  };

  return (
    <div style={styles.page}>
      <div style={styles.shell}>
        <h1 style={styles.title}>Clinical Reasoning Engine</h1>
        <p style={styles.disclaimer}>
          This is a research/demo system and not for clinical use.
        </p>

        <textarea
          rows={10}
          style={styles.textarea}
          placeholder="Paste clinical discharge note..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />

        <div style={styles.buttonRow}>
          <button onClick={analyze} disabled={!input.trim() || loading} style={styles.primaryButton}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
          <button onClick={loadSample} type="button" style={styles.secondaryButton}>
            Try Sample
          </button>
        </div>

        {loading && <p>Processing clinical note...</p>}
        {error ? <p style={styles.error}>{error}</p> : null}

        {report ? (
          <div style={{ marginTop: "30px" }}>
            <div style={styles.section}>
              <h2>Timeline</h2>
              {timeline.length ? (
                <div style={styles.timelineWrap}>
                  {timeline.map((section) => (
                    <div key={section.name} style={styles.timelineItem}>
                      <strong>{formatSectionName(section.name)}</strong>
                      <div style={styles.meta}>{section.text}</div>
                      {section.events?.map((event, index) => (
                        <div key={`${event.start}-${event.end}-${index}`} style={styles.timelineEvent}>
                          <strong>{event.text}</strong>
                          <div>
                            {event.label} | {event.status}
                          </div>
                          <div style={styles.meta}>{event.sentence_text}</div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ) : (
                <p>No timeline returned.</p>
              )}
            </div>

            <div style={styles.section}>
              <h2>Contradictions</h2>
              {contradictions.length === 0 && <p>No contradictions found.</p>}
              {contradictions.map((item, index) => (
                <div key={`${item.type}-${item.entity}-${index}`} style={styles.contradictionCard}>
                  <strong>{item.type}</strong>
                  <p style={{ marginBottom: 0 }}>{item.description}</p>
                </div>
              ))}
            </div>

            <div style={styles.section}>
              <h2>Differential Diagnosis</h2>
              {differentials.length ? (
                differentials.map((item, index) => {
                  const confidence = confidenceByName.get(item.name) ?? item.score ?? 0;
                  const percentage = `${Math.max(0, Math.min(100, confidence * 100))}%`;
                  return (
                    <div key={`${item.name}-${index}`} style={styles.diagnosisCard}>
                      <strong>{item.name}</strong>
                      {item.rationale ? <div style={styles.meta}>{item.rationale}</div> : null}
                      <div style={styles.confidenceTrack}>
                        <div style={{ ...styles.confidenceFill, width: percentage }}>
                          {(confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p>No differential diagnosis returned.</p>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default App;
