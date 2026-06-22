import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

export default function HistoryPage() {
  const [reports, setReports] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchReports = () => {
    fetch(`${API_URL}/reports`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load audit history.");
        return res.json();
      })
      .then((data) => {
        setReports(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDelete = async (id, e) => {
    e.preventDefault();
    if (!window.confirm("Are you sure you want to delete this clinical audit report?")) return;
    try {
      const res = await fetch(`${API_URL}/report/${id}`, { method: "DELETE" });
      if (res.ok) {
        setReports(reports.filter((r) => r.note_id !== id));
      } else {
        alert("Failed to delete report.");
      }
    } catch (err) {
      console.error(err);
      alert("Error deleting report.");
    }
  };

  const filteredReports = reports.filter((r) =>
    r.note_id.toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (isoString) => {
    if (!isoString) return "-";
    const date = new Date(isoString);
    return date.toLocaleString();
  };

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
    searchContainer: {
      marginBottom: "24px",
      display: "flex",
    },
    searchInput: {
      width: "100%",
      maxWidth: "400px",
      padding: "10px 14px",
      fontSize: "15px",
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-buttons)",
      color: "var(--color-paper)",
    },
    tableCard: {
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      overflow: "hidden",
    },
    table: {
      width: "100%",
      borderCollapse: "collapse",
      textAlign: "left",
    },
    th: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      letterSpacing: "-0.26px",
      color: "var(--color-lichen)",
      padding: "16px 20px",
      borderBottom: "1px solid var(--color-graphite)",
      textTransform: "uppercase",
    },
    td: {
      padding: "18px 20px",
      borderBottom: "1px solid var(--color-graphite)",
      fontSize: "15px",
      color: "var(--color-paper)",
    },
    tr: {
      transition: "background 0.15s ease",
    },
    trHover: {
      background: "rgba(255, 255, 255, 0.02)",
    },
    monoText: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      color: "var(--color-lichen)",
    },
    alertBadge: {
      color: "#ff8080",
      fontFamily: "var(--font-roboto-mono)",
    },
    successBadge: {
      color: "var(--color-bioluminescent-lime)",
      fontFamily: "var(--font-roboto-mono)",
    },
    actions: {
      display: "flex",
      gap: "10px",
    },
    viewBtn: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      padding: "6px 12px",
      color: "var(--color-abyssal-ink)",
      background: "var(--color-bioluminescent-lime)",
      border: "none",
      borderRadius: "6px",
      textDecoration: "none",
      display: "inline-block",
    },
    deleteBtn: {
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      padding: "6px 12px",
      color: "#ff8080",
      background: "transparent",
      border: "1px solid #ff8080",
      borderRadius: "6px",
    },
  };

  return (
    <main style={styles.container} className="animate-fade-in-up">
      <h1 style={styles.title}>Audit History.</h1>

      <div style={styles.searchContainer}>
        <input
          type="text"
          placeholder="Filter audits by Note ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.searchInput}
        />
      </div>

      {loading ? (
        <div style={{ color: "var(--color-lichen)" }}>Fetching clinical registry logs...</div>
      ) : error ? (
        <div style={{ color: "red" }}>Error loading history: {error}</div>
      ) : filteredReports.length === 0 ? (
        <div style={{ color: "var(--color-lichen)" }}>No clinical audits recorded yet.</div>
      ) : (
        <div style={styles.tableCard}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Note ID</th>
                <th style={styles.th}>Ingested At</th>
                <th style={styles.th}>Language Flow</th>
                <th style={styles.th}>Events</th>
                <th style={styles.th}>Contradictions</th>
                <th style={styles.th}>Diagnoses</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredReports.map((report) => (
                <tr key={report.note_id} style={styles.tr}>
                  <td style={{ ...styles.td, ...styles.monoText }}>
                    {report.note_id.slice(0, 18)}...
                  </td>
                  <td style={{ ...styles.td, ...styles.monoText }}>
                    {formatDate(report.created_at)}
                  </td>
                  <td style={{ ...styles.td, ...styles.monoText }}>
                    {report.source_language.toUpperCase()} &rarr; {report.display_language.toUpperCase()}
                  </td>
                  <td style={styles.td}>{report.event_count}</td>
                  <td style={styles.td}>
                    {report.contradiction_count > 0 ? (
                      <span style={styles.alertBadge}>
                        {report.contradiction_count} FLAGGED
                      </span>
                    ) : (
                      <span style={styles.successBadge}>0</span>
                    )}
                  </td>
                  <td style={styles.td}>{report.differential_count}</td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <Link to={`/report/${report.note_id}`} className="btn-hover-scale" style={styles.viewBtn}>
                        VIEW
                      </Link>
                      <button
                        onClick={(e) => handleDelete(report.note_id, e)}
                        className="btn-hover-scale"
                        style={styles.deleteBtn}
                      >
                        DELETE
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
