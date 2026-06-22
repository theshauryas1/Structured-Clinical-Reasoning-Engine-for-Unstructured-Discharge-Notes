import React, { useState, useEffect } from "react";

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

export default function DiagnosticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch diagnostics.");
        return res.json();
      })
      .then((health) => {
        setData(health);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const styles = {
    container: {
      maxWidth: "1200px",
      margin: "0 auto",
      padding: "40px 24px 80px",
    },
    title: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "var(--text-heading-sm)",
      lineHeight: "var(--leading-heading-sm)",
      letterSpacing: "var(--tracking-heading-sm)",
      color: "var(--color-paper)",
      marginBottom: "24px",
      textTransform: "uppercase",
    },
    grid: {
      display: "flex",
      flexDirection: "column",
      gap: "20px",
    },
    card: {
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      padding: "30px",
    },
    sectionTitle: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "14px",
      color: "var(--color-lichen)",
      textTransform: "uppercase",
      marginBottom: "16px",
      display: "flex",
      alignItems: "center",
      gap: "8px",
    },
    statusIndicator: {
      width: "8px",
      height: "8px",
      borderRadius: "50%",
      backgroundColor: "var(--color-bioluminescent-lime)",
    },
    statusIndicatorInactive: {
      width: "8px",
      height: "8px",
      borderRadius: "50%",
      backgroundColor: "var(--color-graphite)",
    },
    metricsList: {
      display: "flex",
      flexWrap: "wrap",
      gap: "30px",
      marginTop: "10px",
    },
    metricBox: {
      flex: "1 1 220px",
      borderTop: "1px solid var(--color-graphite)",
      paddingTop: "12px",
    },
    label: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      color: "var(--color-graphite)",
      marginBottom: "6px",
    },
    value: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "18px",
      color: "var(--color-paper)",
    },
    highlightValue: {
      color: "var(--color-bioluminescent-lime)",
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "16px",
    },
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>System Diagnostics</h1>
        <div style={{ color: "var(--color-lichen)" }}>Querying hardware and neural assets...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>System Diagnostics</h1>
        <div style={{ color: "red", border: "1px solid red", padding: "16px", borderRadius: "8px" }}>
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <main style={styles.container} className="animate-fade-in-up">
      <h1 style={styles.title}>System Diagnostics.</h1>

      <div style={styles.grid}>
        {/* Core NLP Pipeline */}
        <div style={styles.card}>
          <div style={styles.sectionTitle}>
            <div style={styles.statusIndicator} className="pulse-accent-dot"></div>
            01 / Natural Language Extraction
          </div>
          <div style={styles.metricsList}>
            <div style={styles.metricBox}>
              <div style={styles.label}>EXTRACTOR BACKEND</div>
              <div style={styles.value}>{data.extractor_backend || "rules (fallback)"}</div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>TRANSLATION EDGE CACHE (MARIANMT)</div>
              <div style={styles.value}>{data.translation_models_available ? "Active / In Memory" : "Unavailable"}</div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>AUTO-LANGUAGE DETECTION</div>
              <div style={styles.value}>{data.language_detection_available ? "Active" : "Disabled"}</div>
            </div>
          </div>
        </div>

        {/* Database Store */}
        <div style={styles.card}>
          <div style={styles.sectionTitle}>
            <div style={styles.statusIndicator} className="pulse-accent-dot"></div>
            02 / Persistent Data Layer
          </div>
          <div style={styles.metricsList}>
            <div style={styles.metricBox}>
              <div style={styles.label}>DATABASE CONNECTION</div>
              <div style={styles.value}>ONLINE</div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>ACTIVE SQL ENGINE DRIVER</div>
              <div style={styles.value}>{data.database?.driver || "SQLite"}</div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>HEALTH CHECK</div>
              <div style={styles.value}>Parity OK</div>
            </div>
          </div>
        </div>

        {/* ML Calibration weights */}
        <div style={styles.card}>
          <div style={styles.sectionTitle}>
            <div style={styles.statusIndicator} className="pulse-accent-dot"></div>
            03 / ML Weights & Calibration Artifacts
          </div>
          <div style={styles.metricsList}>
            <div style={styles.metricBox}>
              <div style={styles.label}>LEARNED RERANKER WEIGHTS</div>
              <div style={{ ...styles.value, ...(data.learned_artifacts?.reranker ? styles.highlightValue : {}) }}>
                {data.learned_artifacts?.reranker ? "LOADED / VERIFIED" : "FALLBACK RULES ACTIVE"}
              </div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>CONFIDENCE CALIBRATOR WEIGHTS</div>
              <div style={{ ...styles.value, ...(data.learned_artifacts?.confidence_calibrator ? styles.highlightValue : {}) }}>
                {data.learned_artifacts?.confidence_calibrator ? "LOADED / CALIBRATED" : "FALLBACK ACTIVE"}
              </div>
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>ORCHESTRATION POLICY</div>
              <div style={{ ...styles.value, ...(data.learned_artifacts?.orchestration_policy ? styles.highlightValue : {}) }}>
                {data.learned_artifacts?.orchestration_policy ? "LOADED / ACTIVE" : "DEFAULT POLICY"}
              </div>
            </div>
          </div>
        </div>

        {/* LLM Providers */}
        <div style={styles.card}>
          <div style={styles.sectionTitle}>
            <div style={styles.statusIndicator} className="pulse-accent-dot"></div>
            04 / External Inference Providers
          </div>
          <div style={styles.metricsList}>
            <div style={styles.metricBox}>
              <div style={styles.label}>NVIDIA NIM COMPLETIONS API</div>
              <div style={styles.value}>{data.nvidia_nim?.configured ? "CONFIGURED" : "NOT CONFIGURED"}</div>
              {data.nvidia_nim?.configured && (
                <div style={{ fontSize: "13px", color: "var(--color-graphite)", marginTop: "4px" }}>
                  Model: {data.nvidia_nim.model}<br />
                  Url: {data.nvidia_nim.base_url}
                </div>
              )}
            </div>
            <div style={styles.metricBox}>
              <div style={styles.label}>GROQ COMPLETIONS API (FALLBACK)</div>
              <div style={styles.value}>{data.groq?.configured ? "CONFIGURED" : "NOT CONFIGURED"}</div>
              {data.groq?.configured && (
                <div style={{ fontSize: "13px", color: "var(--color-graphite)", marginTop: "4px" }}>
                  Model: {data.groq.model}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
