import { startTransition, useDeferredValue, useState } from "react";

import ConfidenceBars from "./components/ConfidenceBars";
import ContradictionCards from "./components/ContradictionCards";
import TimelineView from "./components/TimelineView";

const SAMPLE_NOTE = `ADMISSION SUMMARY:
65 yo female presenting with acute worsening shortness of breath, productive cough with yellow sputum, and fever of 101.2F. Chest X-ray showed right lower lobe infiltrate consistent with community-acquired pneumonia.

HOSPITAL COURSE:
Admitted to medicine and started on IV Ceftriaxone and Azithromycin. Oxygen requirement was 2L nasal cannula, weaned to room air by day 4.

DISCHARGE DIAGNOSES AND PLAN:
1. Right lower lobe community-acquired pneumonia - resolved clinically.
2. New onset atrial fibrillation - rate controlled on Metoprolol.
3. Developed mild acute kidney injury during hospitalization.`;

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const LANGUAGE_OPTIONS = [
  { value: "auto", label: "Auto-detect" },
  { value: "en", label: "English" },
  { value: "de", label: "Deutsch" },
  { value: "fr", label: "Français" },
  { value: "nl", label: "Nederlands" },
  { value: "es", label: "Español" },
];

export default function App() {
  const [noteText, setNoteText] = useState(SAMPLE_NOTE);
  const [language, setLanguage] = useState("auto");
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const deferredReport = useDeferredValue(report);
  const presentationReport = deferredReport?.display_report || deferredReport;
  const contradictionCount = presentationReport?.contradiction_flags?.length || 0;

  const summary = presentationReport
    ? {
        noteId: presentationReport.note_id,
        differentials: presentationReport.differentials?.length || 0,
        contradictions: contradictionCount,
        confidenceScores: presentationReport.confidence_scores?.length || 0,
      }
    : null;

  async function handleAnalyze(event) {
    event.preventDefault();
    setStatus("loading");
    setError("");

    try {
      const response = await fetch(`${API_BASE}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_text: noteText, lang: language }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Unable to process note.");
      }

      const payload = await response.json();
      startTransition(() => {
        setReport(payload);
      });
      setStatus("ready");
    } catch (submissionError) {
      setStatus("error");
      setError(submissionError.message);
    }
  }

  return (
    <div className="page-shell">
      <div className="page-backdrop" />
      <main className="dashboard">
        <section className="hero">
          <p className="eyebrow">Audit-ready clinical NLP</p>
          <h1>Clinical reasoning engine for discharge-note contradictions</h1>
          <p className="lede">
            Paste a discharge summary, run the reasoning graph, and inspect the
            structured timeline, contradiction evidence, confidence trace, and
            translated presentation layer.
          </p>
        </section>

        <section className="workspace">
          <form className="composer" onSubmit={handleAnalyze}>
            <div className="panel-header">
              <h2>Input note</h2>
              <span className={`status-pill status-${status}`}>{status}</span>
            </div>
            <label className="field-label" htmlFor="language-select">
              Input language
            </label>
            <select
              id="language-select"
              className="language-select"
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
            >
              {LANGUAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <textarea
              className="note-input"
              value={noteText}
              onChange={(event) => setNoteText(event.target.value)}
              placeholder="Paste a raw discharge note here..."
            />
            <div className="composer-actions">
              <button className="primary-button" type="submit">
                Run reasoning pipeline
              </button>
              <button
                className="ghost-button"
                type="button"
                onClick={() => setNoteText(SAMPLE_NOTE)}
              >
                Load sample
              </button>
            </div>
            {error ? <p className="error-text">{error}</p> : null}
          </form>

          <div className="overview-grid">
            <div className="metric-card">
              <span className="metric-label">Extractor</span>
              <strong>{presentationReport?.timeline?.extractor_backend || "not run"}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Contradictions</span>
              <strong>{summary?.contradictions ?? 0}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Differentials</span>
              <strong>{summary?.differentials ?? 0}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Confidence sets</span>
              <strong>{summary?.confidenceScores ?? 0}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Display language</span>
              <strong>{deferredReport?.display_language || "en"}</strong>
            </div>
          </div>
        </section>

        {presentationReport ? (
          <>
            <section className="report-panel">
              <div className="panel-header">
                <h2>Timeline</h2>
                <span className="subtle-copy">
                  Note ID: {summary?.noteId} • Source: {deferredReport?.source_language || "en"} • Pipeline:{" "}
                  {deferredReport?.pipeline_language || "en"}
                </span>
              </div>
              <TimelineView timeline={presentationReport.timeline} />
            </section>

            <section className="report-grid">
              <div className="report-panel">
                <div className="panel-header">
                  <h2>Contradiction flags</h2>
                </div>
                <ContradictionCards contradictions={presentationReport.contradiction_flags} />
              </div>

              <div className="report-panel">
                <div className="panel-header">
                  <h2>Confidence scores</h2>
                </div>
                <ConfidenceBars
                  confidenceScores={presentationReport.confidence_scores}
                  differentials={presentationReport.differentials}
                />
              </div>
            </section>

            <section className="report-panel">
              <div className="panel-header">
                <h2>Reasoning trace</h2>
              </div>
              <div className="trace-list">
                {presentationReport.reasoning_trace.map((step) => (
                  <article className="trace-card" key={step.agent}>
                    <span className="trace-agent">{step.agent}</span>
                    <h3>{step.summary}</h3>
                    <p>{step.details.join(" • ")}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="report-panel">
              <div className="panel-header">
                <h2>Orchestration policy</h2>
              </div>
              <div className="trace-list">
                {presentationReport.orchestration_trace?.map((step, index) => (
                  <article className="trace-card" key={`${step.step}-${step.action}-${index}`}>
                    <span className="trace-agent">{step.step}</span>
                    <h3>{step.action}</h3>
                    <p>{step.reason}</p>
                  </article>
                )) || <p className="empty-state">No orchestration actions recorded.</p>}
              </div>
            </section>
          </>
        ) : null}
      </main>
    </div>
  );
}
