import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getTranslations } from "../utils/translations";
import ReportWorkspace from "../components/ReportWorkspace";

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

export default function DetailPage() {
  const { id } = useParams();
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/report/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Report not found or failed to load.");
        return res.json();
      })
      .then((data) => {
        setOutput(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  const uiLanguage = output?.display_language || "en";
  const t = getTranslations(uiLanguage);

  const styles = {
    container: {
      maxWidth: "1200px",
      margin: "0 auto",
      padding: "40px 24px 80px",
    },
    backRow: {
      marginBottom: "24px",
    },
    backLink: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      color: "var(--color-lichen)",
      textDecoration: "none",
      border: "1px solid var(--color-graphite)",
      padding: "6px 12px",
      borderRadius: "6px",
      display: "inline-block",
      transition: "all 0.15s ease",
    },
    title: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "var(--text-heading-sm)",
      lineHeight: "var(--leading-heading-sm)",
      letterSpacing: "var(--tracking-heading-sm)",
      color: "var(--color-paper)",
      marginBottom: "8px",
      textTransform: "uppercase",
    },
    disclaimer: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      color: "var(--color-graphite)",
      marginBottom: "36px",
      textTransform: "uppercase",
      display: "flex",
      alignItems: "center",
      gap: "8px",
    },
    accentDot: {
      width: "6px",
      height: "6px",
      borderRadius: "50%",
      backgroundColor: "var(--color-bioluminescent-lime)",
    },
    infoPanel: {
      background: "rgba(206, 247, 158, 0.02)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      padding: "20px",
      marginBottom: "30px",
    },
    infoGrid: {
      display: "flex",
      gap: "30px",
      flexWrap: "wrap",
    },
    infoItem: {
      flex: "1 1 180px",
    },
    infoLabel: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "12px",
      color: "var(--color-graphite)",
      textTransform: "uppercase",
      marginBottom: "4px",
    },
    infoVal: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "16px",
      color: "var(--color-paper)",
    },
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.backRow}>
          <Link to="/history" className="btn-hover-scale" style={styles.backLink}>&larr; BACK TO HISTORY</Link>
        </div>
        <h1 style={styles.title}>Audit Report</h1>
        <div style={{ color: "var(--color-lichen)" }}>Retrieving report data and traces...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.backRow}>
          <Link to="/history" className="btn-hover-scale" style={styles.backLink}>&larr; BACK TO HISTORY</Link>
        </div>
        <h1 style={styles.title}>Error</h1>
        <div style={{ color: "red", border: "1px solid red", padding: "16px", borderRadius: "8px" }}>
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <main style={styles.container} className="animate-fade-in-up">
      <div style={styles.backRow}>
        <Link to="/history" className="btn-hover-scale" style={styles.backLink}>&larr; BACK TO HISTORY</Link>
      </div>

      <h1 style={styles.title}>Audit Report: {id.slice(0, 18)}...</h1>
      <div style={styles.disclaimer}>
        <div style={styles.accentDot} className="pulse-accent-dot"></div>
        {t.disclaimer}
      </div>

      <div style={styles.infoPanel}>
        <div style={styles.infoGrid}>
          <div style={styles.infoItem}>
            <div style={styles.infoLabel}>Source Language</div>
            <div style={styles.infoVal}>{output.source_language?.toUpperCase() || "EN"}</div>
          </div>
          <div style={styles.infoItem}>
            <div style={styles.infoLabel}>Pipeline Channel</div>
            <div style={styles.infoVal}>EN (Helsinki Edge Standard)</div>
          </div>
          <div style={styles.infoItem}>
            <div style={styles.infoLabel}>Display Channel</div>
            <div style={styles.infoVal}>{output.display_language?.toUpperCase() || "EN"}</div>
          </div>
        </div>
      </div>

      <ReportWorkspace output={output} translations={t} uiLanguage={uiLanguage} />
    </main>
  );
}
