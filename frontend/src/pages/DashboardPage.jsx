import React, { useState, useRef, useEffect } from "react";
import gsap from "gsap";
import { getTranslations, buildLanguageOptions, SUPPORTED_LANGUAGES } from "../utils/translations";
import ReportWorkspace3D from "../components/ReportWorkspace3D";
import NeuralBrainCanvas from "../components/3d/NeuralBrainCanvas";
import HolographicCard from "../components/3d/HolographicCard";
import QuantumUpload from "../components/3d/QuantumUpload";
import ProcessingOrb from "../components/3d/ProcessingOrb";

const SAMPLE_NOTE = `ADMISSION SUMMARY:
Patient admitted with fever, cough, and shortness of breath.

HOSPITAL COURSE:
Fever resolved after 3 days on ceftriaxone and azithromycin. Oxygen requirement improved.

DISCHARGE DIAGNOSES AND PLAN:
Community-acquired pneumonia improved clinically. New onset atrial fibrillation noted during admission.`;

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

// ─── Animated stat counter ──────────────────────────────────────────────────
function StatCounter({ value, label, color = "#cef79e", prefix = "", suffix = "" }) {
  const numRef = useRef(null);
  const objRef = useRef({ val: 0 });

  useEffect(() => {
    gsap.to(objRef.current, {
      val: parseFloat(value) || 0,
      duration: 2,
      ease: "power2.out",
      onUpdate: () => {
        if (numRef.current) {
          const v = objRef.current.val;
          numRef.current.textContent = prefix + (Number.isInteger(parseFloat(value)) ? Math.round(v) : v.toFixed(2)) + suffix;
        }
      },
    });
  }, [value]);

  return (
    <div style={{ textAlign: "center" }}>
      <div
        ref={numRef}
        style={{
          fontFamily: "'Inter Tight', sans-serif",
          fontSize: 32,
          fontWeight: 700,
          color,
          letterSpacing: "-1px",
          textShadow: `0 0 20px ${color}44`,
        }}
      >
        {prefix}0{suffix}
      </div>
      <div style={{
        fontFamily: "'Roboto Mono', monospace",
        fontSize: 9,
        color: "rgba(201,203,190,0.45)",
        letterSpacing: "1.5px",
        textTransform: "uppercase",
        marginTop: 4,
      }}>
        {label}
      </div>
    </div>
  );
}

// ─── Glowing text area ──────────────────────────────────────────────────────
function GlowTextarea({ value, onChange, placeholder }) {
  const [focused, setFocused] = useState(false);

  return (
    <div style={{ position: "relative" }}>
      {focused && (
        <div style={{
          position: "absolute",
          inset: -1,
          borderRadius: 14,
          background: "transparent",
          border: "1px solid rgba(206,247,158,0.5)",
          boxShadow: "0 0 20px rgba(206,247,158,0.15), inset 0 0 20px rgba(206,247,158,0.04)",
          pointerEvents: "none",
          zIndex: 2,
          transition: "all 0.3s",
        }} />
      )}
      <textarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          width: "100%",
          minHeight: 160,
          padding: "16px 20px",
          background: "rgba(0,0,0,0.35)",
          border: "1px solid rgba(77,87,87,0.5)",
          borderRadius: 12,
          color: "#fff",
          fontFamily: "'Roboto Mono', monospace",
          fontSize: 13,
          lineHeight: 1.7,
          resize: "vertical",
          outline: "none",
          transition: "border-color 0.25s",
          position: "relative",
          zIndex: 1,
        }}
      />
      {value && (
        <div style={{
          position: "absolute",
          bottom: 10,
          right: 14,
          fontFamily: "'Roboto Mono', monospace",
          fontSize: 9,
          color: "rgba(206,247,158,0.35)",
          letterSpacing: "0.5px",
          zIndex: 3,
        }}>
          {value.length} chars · {value.split(/\s+/).filter(Boolean).length} words
        </div>
      )}
    </div>
  );
}

// ─── Hero stats bar ─────────────────────────────────────────────────────────
function HeroStats({ output }) {
  if (!output) return null;
  const report = output.display_report || output;
  const diagCount = report.differentials?.length || 0;
  const contCount = report.contradiction_flags?.length || 0;
  const confScore = report.confidence_scores?.[0]?.score || 0;
  const timelineCount = Object.values(report.timeline || {}).flat().length;

  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      gap: 48,
      padding: "28px 0",
      borderTop: "1px solid rgba(206,247,158,0.08)",
      borderBottom: "1px solid rgba(206,247,158,0.08)",
      marginBottom: 40,
      flexWrap: "wrap",
    }}>
      <StatCounter value={diagCount} label="Hypotheses" color="#cef79e" />
      <StatCounter value={contCount} label="Contradictions" color="#f87171" />
      <StatCounter value={Math.round(confScore * 100)} label="Top Confidence" suffix="%" color="#4ade80" />
      <StatCounter value={timelineCount} label="Timeline Events" color="#22d3ee" />
    </div>
  );
}

// ─── Main Dashboard ──────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("auto");
  const [displayLanguage, setDisplayLanguage] = useState("en");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [showOutput, setShowOutput] = useState(false);
  const heroRef = useRef(null);
  const formRef = useRef(null);

  const uiLanguage = output?.display_language || displayLanguage;
  const t = getTranslations(uiLanguage);
  const inputLanguageOptions = buildLanguageOptions(t);
  const displayLanguageOptions = SUPPORTED_LANGUAGES.map((v) => ({ value: v, label: t.languageLabels[v] }));

  // Entry animation
  useEffect(() => {
    if (heroRef.current) {
      gsap.fromTo(heroRef.current,
        { opacity: 0, y: 40 },
        { opacity: 1, y: 0, duration: 1.2, ease: "power3.out" }
      );
    }
  }, []);

  useEffect(() => {
    if (output && !loading) {
      setShowOutput(true);
      setTimeout(() => {
        document.getElementById("output-anchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 300);
    }
  }, [output, loading]);

  const analyze = async () => {
    if (!input.trim()) { setError(t.emptyInputError); return; }
    setLoading(true); setError(""); setOutput(null); setShowOutput(false);
    try {
      const res = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_text: input, lang: language, display_lang: displayLanguage }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || t.requestError);
      setOutput(data);
    } catch (err) {
      setError(err.message || t.requestError);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    setUploading(true); setLoading(true); setError(""); setOutput(null); setShowOutput(false);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lang", language);
    formData.append("display_lang", displayLanguage);
    try {
      const res = await fetch(`${API_URL}/ingest-file`, { method: "POST", body: formData });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || t.requestError);
      setOutput(data); setFile(null);
    } catch (err) {
      setError(err.message || t.requestError);
    } finally {
      setUploading(false); setLoading(false);
    }
  };

  return (
    <>
      {/* ── Fixed 3D background ── */}
      <NeuralBrainCanvas />

      <main style={{ position: "relative", zIndex: 1, maxWidth: 1240, margin: "0 auto", padding: "48px 24px 100px" }}>

        {/* ══ HERO SECTION ═══════════════════════════════════════════════════ */}
        <section ref={heroRef} style={{ textAlign: "center", marginBottom: 56 }}>
          {/* Status pill */}
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 16px",
            borderRadius: 9999,
            background: "rgba(74,222,128,0.06)",
            border: "1px solid rgba(74,222,128,0.18)",
            marginBottom: 28,
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: "50%",
              background: "#4ade80", boxShadow: "0 0 8px #4ade80",
              animation: "pulse-dot 2s infinite",
            }} />
            <span style={{
              fontFamily: "'Roboto Mono', monospace",
              fontSize: 10,
              color: "#4ade80",
              letterSpacing: "2px",
              textTransform: "uppercase",
            }}>
              Multi-Agent Reasoning Online
            </span>
          </div>

          {/* Main title */}
          <h1 style={{
            fontFamily: "'Inter Tight', sans-serif",
            fontSize: "clamp(36px, 6vw, 80px)",
            fontWeight: 800,
            lineHeight: 1.0,
            letterSpacing: "-2px",
            marginBottom: 20,
            background: "linear-gradient(135deg, #fff 0%, #cef79e 40%, #22d3ee 80%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}>
            Clinical<br />
            <span style={{ fontStyle: "italic", opacity: 0.85 }}>Reasoning</span>{" "}
            <span style={{
              background: "linear-gradient(90deg, #cef79e, #4ade80)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}>Engine</span>
          </h1>

          <p style={{
            fontFamily: "'Inter Tight', sans-serif",
            fontSize: 16,
            color: "rgba(201,203,190,0.55)",
            maxWidth: 520,
            margin: "0 auto 36px",
            lineHeight: 1.6,
            letterSpacing: "-0.2px",
          }}>
            {t.disclaimer || "AI-assisted structured analysis of unstructured clinical discharge notes. Not for diagnostic decisions."}
          </p>

          {/* Capability tags */}
          {[
            ["⏱", "Timeline Reconstruction"],
            ["⚡", "Contradiction Mining"],
            ["🧠", "Differential Calibration"],
            ["💬", "Multilingual Analysis"],
          ].map(([icon, label]) => (
            <span key={label} style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 12px",
              borderRadius: 9999,
              background: "rgba(206,247,158,0.04)",
              border: "1px solid rgba(206,247,158,0.1)",
              fontFamily: "'Roboto Mono', monospace",
              fontSize: 10,
              color: "rgba(206,247,158,0.6)",
              letterSpacing: "0.5px",
              margin: "0 4px 8px",
              textTransform: "uppercase",
            }}>
              {icon} {label}
            </span>
          ))}
        </section>

        {/* ══ INPUT FORM CARD ════════════════════════════════════════════════ */}
        <HolographicCard style={{ marginBottom: 28 }}>
          <div style={{ padding: "32px 36px" }}>
            {/* Card header */}
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 24,
              paddingBottom: 20,
              borderBottom: "1px solid rgba(206,247,158,0.08)",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 8, height: 8, borderRadius: "50%",
                  background: "#cef79e", boxShadow: "0 0 12px #cef79e",
                  animation: "pulse-dot 2s infinite",
                }} />
                <span style={{
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: 10,
                  color: "rgba(206,247,158,0.6)",
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                }}>
                  DISCHARGE NOTE INPUT
                </span>
              </div>

              {/* Terminal ID */}
              <span style={{
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 9,
                color: "rgba(201,203,190,0.2)",
                letterSpacing: "1px",
              }}>
                TRM-{Math.floor(Math.random() * 9000 + 1000)}
              </span>
            </div>

            {/* Upload zone */}
            <QuantumUpload
              file={file}
              dragActive={dragActive}
              onFileSelect={setFile}
              onDragEnter={() => setDragActive(true)}
              onDragLeave={() => setDragActive(false)}
              onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
              onDrop={(e) => {
                e.preventDefault();
                setDragActive(false);
                if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
              }}
              uploadLabel={t.uploadLabel || "DROP DISCHARGE NOTE HERE"}
              uploadInfo={t.uploadInfo || "PDF · PNG · JPG · TXT · WAV · MP3"}
              ocrNotice={t.ocrNotice || "OCR available for image files"}
            />

            {file && (
              <div style={{ display: "flex", gap: 10, margin: "16px 0" }}>
                <button onClick={uploadFile} disabled={loading} style={styles.primaryBtn}>
                  {uploading ? "⚙ ANALYZING FILE..." : "⬆ ANALYZE FILE"}
                </button>
                <button onClick={() => setFile(null)} style={styles.ghostBtn}>
                  CANCEL
                </button>
              </div>
            )}

            {/* Divider */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              margin: "20px 0",
            }}>
              <div style={{ flex: 1, height: 1, background: "rgba(206,247,158,0.08)" }} />
              <span style={{
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 9,
                color: "rgba(201,203,190,0.25)",
                letterSpacing: "2px",
              }}>
                OR PASTE TEXT
              </span>
              <div style={{ flex: 1, height: 1, background: "rgba(206,247,158,0.08)" }} />
            </div>

            {/* Text area */}
            <GlowTextarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t.notePlaceholder || "Paste clinical discharge note text here..."}
            />

            {/* Language controls */}
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", margin: "20px 0" }}>
              {[
                { id: "lang-in", label: t.inputLanguage || "Input Language", value: language, opts: inputLanguageOptions, onChange: setLanguage },
                { id: "lang-out", label: t.displayLanguage || "Display Language", value: displayLanguage, opts: displayLanguageOptions, onChange: setDisplayLanguage },
              ].map(({ id, label, value, opts, onChange }) => (
                <div key={id} style={{ flex: "1 1 200px", display: "flex", flexDirection: "column", gap: 6 }}>
                  <label htmlFor={id} style={{
                    fontFamily: "'Roboto Mono', monospace",
                    fontSize: 9,
                    color: "rgba(201,203,190,0.4)",
                    letterSpacing: "2px",
                    textTransform: "uppercase",
                  }}>
                    {label}
                  </label>
                  <select
                    id={id}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    style={{
                      padding: "10px 14px",
                      background: "rgba(0,0,0,0.3)",
                      border: "1px solid rgba(77,87,87,0.5)",
                      borderRadius: 10,
                      color: "#fff",
                      fontFamily: "'Roboto Mono', monospace",
                      fontSize: 12,
                      appearance: "none",
                      cursor: "pointer",
                    }}
                  >
                    {opts.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <button
                id="analyze-btn"
                onClick={analyze}
                disabled={loading}
                style={styles.primaryBtn}
              >
                {loading && !uploading ? "⚙ PROCESSING..." : "⚡ ANALYZE NOTE"}
              </button>
              <button
                onClick={() => { setInput(SAMPLE_NOTE); setError(""); setFile(null); }}
                style={styles.ghostBtn}
              >
                LOAD SAMPLE
              </button>
              {(input || output) && (
                <button
                  onClick={() => { setInput(""); setOutput(null); setShowOutput(false); setError(""); }}
                  style={{ ...styles.ghostBtn, color: "rgba(248,113,113,0.5)", borderColor: "rgba(248,113,113,0.15)" }}
                >
                  CLEAR
                </button>
              )}
            </div>
          </div>
        </HolographicCard>

        {/* ══ ERROR ════════════════════════════════════════════════════════ */}
        {error && (
          <div style={{
            padding: "16px 24px",
            borderRadius: 12,
            background: "rgba(220,38,38,0.06)",
            border: "1px solid rgba(220,38,38,0.25)",
            color: "#f87171",
            fontFamily: "'Roboto Mono', monospace",
            fontSize: 12,
            marginBottom: 24,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}>
            <span style={{ fontSize: 16 }}>⚠</span>
            {error}
          </div>
        )}

        {/* ══ PROCESSING STATE ════════════════════════════════════════════ */}
        {loading && (
          <HolographicCard style={{ marginBottom: 28 }}>
            <ProcessingOrb />
          </HolographicCard>
        )}

        {/* ══ OUTPUT ══════════════════════════════════════════════════════ */}
        {showOutput && output && !loading && (
          <div id="output-anchor">
            {/* Info bar */}
            <div style={{
              display: "flex",
              gap: 20,
              flexWrap: "wrap",
              padding: "16px 24px",
              background: "rgba(206,247,158,0.03)",
              border: "1px solid rgba(206,247,158,0.1)",
              borderRadius: 12,
              marginBottom: 24,
            }}>
              {[
                ["Source Lang", output.source_language?.toUpperCase() || "EN"],
                ["Pipeline", "EN (Helsinki Edge)"],
                ["Display", output.display_language?.toUpperCase() || "EN"],
                ["Note ID", output.note_id?.slice(0, 8) || "—"],
              ].map(([k, v]) => (
                <div key={k}>
                  <div style={{ fontFamily: "'Roboto Mono', monospace", fontSize: 9, color: "rgba(201,203,190,0.3)", letterSpacing: "1px", textTransform: "uppercase", marginBottom: 2 }}>
                    {k}
                  </div>
                  <div style={{ fontFamily: "'Inter Tight', sans-serif", fontSize: 14, color: "#cef79e", fontWeight: 600 }}>
                    {v}
                  </div>
                </div>
              ))}
            </div>

            <HeroStats output={output} />
            <ReportWorkspace3D output={output} translations={t} uiLanguage={uiLanguage} />
          </div>
        )}
      </main>
    </>
  );
}

const styles = {
  primaryBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "12px 28px",
    background: "linear-gradient(135deg, rgba(206,247,158,0.9) 0%, rgba(74,222,128,0.9) 100%)",
    color: "#0a1a0f",
    border: "none",
    borderRadius: 10,
    fontFamily: "'Roboto Mono', monospace",
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: "1.5px",
    textTransform: "uppercase",
    cursor: "pointer",
    boxShadow: "0 0 20px rgba(206,247,158,0.2), 0 4px 12px rgba(0,0,0,0.4)",
    transition: "all 0.2s ease",
  },
  ghostBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "12px 20px",
    background: "transparent",
    color: "rgba(201,203,190,0.5)",
    border: "1px solid rgba(77,87,87,0.4)",
    borderRadius: 10,
    fontFamily: "'Roboto Mono', monospace",
    fontSize: 11,
    letterSpacing: "1px",
    textTransform: "uppercase",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
};
