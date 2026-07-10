import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export default function LoginPage({ onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // "login" or "register"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (mode === "register" && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (mode === "register" && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed.");
      }
      if (onAuthSuccess) onAuthSuccess(data.username);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Background grid */}
      <div style={styles.gridOverlay} />

      <div style={styles.card}>
        {/* Logo / Brand */}
        <div style={styles.brand}>
          <div style={styles.brandDot} />
          <span style={styles.brandText}>NEXUS CRE</span>
        </div>

        <h1 style={styles.title}>
          {mode === "login" ? "Sign In" : "Create Account"}
        </h1>
        <p style={styles.subtitle}>
          {mode === "login"
            ? "Access your clinical audit history and AI assistant."
            : "Create an account to save your audits and chat history."}
        </p>

        {/* Mode Toggle */}
        <div style={styles.toggleBar}>
          <button
            style={{ ...styles.toggleBtn, ...(mode === "login" ? styles.toggleBtnActive : {}) }}
            onClick={() => { setMode("login"); setError(""); }}
          >
            SIGN IN
          </button>
          <button
            style={{ ...styles.toggleBtn, ...(mode === "register" ? styles.toggleBtnActive : {}) }}
            onClick={() => { setMode("register"); setError(""); }}
          >
            REGISTER
          </button>
        </div>

        <form onSubmit={handleSubmit} style={styles.form} autoComplete="off">
          <div style={styles.fieldGroup}>
            <label style={styles.label}>USERNAME</label>
            <input
              id="auth-username"
              type="text"
              style={styles.input}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="your_username"
              required
              autoFocus
            />
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>PASSWORD</label>
            <input
              id="auth-password"
              type="password"
              style={styles.input}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••"
              required
            />
          </div>

          {mode === "register" && (
            <div style={styles.fieldGroup}>
              <label style={styles.label}>CONFIRM PASSWORD</label>
              <input
                id="auth-confirm-password"
                type="password"
                style={styles.input}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••"
                required
              />
            </div>
          )}

          {error && (
            <div style={styles.errorBox}>
              <span style={styles.errorIcon}>⚠</span> {error}
            </div>
          )}

          <button
            id="auth-submit"
            type="submit"
            style={{ ...styles.submitBtn, ...(loading ? styles.submitBtnDisabled : {}) }}
            disabled={loading}
          >
            {loading ? "Processing..." : mode === "login" ? "SIGN IN →" : "CREATE ACCOUNT →"}
          </button>
        </form>

        <p style={styles.disclaimer}>
          🔒 Credentials are hashed with PBKDF2-SHA256. Sessions expire after 30 days.
        </p>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#030a0c",
    position: "relative",
    overflow: "hidden",
    padding: "20px",
  },
  gridOverlay: {
    position: "absolute",
    inset: 0,
    backgroundImage:
      "linear-gradient(rgba(206,247,158,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(206,247,158,0.03) 1px, transparent 1px)",
    backgroundSize: "40px 40px",
    pointerEvents: "none",
  },
  card: {
    position: "relative",
    zIndex: 1,
    width: "100%",
    maxWidth: "440px",
    background: "rgba(8, 18, 22, 0.9)",
    border: "1px solid rgba(206,247,158,0.12)",
    borderRadius: "20px",
    padding: "48px 40px",
    backdropFilter: "blur(30px)",
    boxShadow: "0 0 80px rgba(206,247,158,0.04), 0 32px 64px rgba(0,0,0,0.5)",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "32px",
  },
  brandDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#cef79e",
    boxShadow: "0 0 12px #cef79e",
    animation: "pulse-dot 2s infinite",
  },
  brandText: {
    fontFamily: "'Roboto Mono', monospace",
    fontSize: "11px",
    letterSpacing: "3px",
    color: "rgba(206,247,158,0.5)",
    textTransform: "uppercase",
  },
  title: {
    fontFamily: "'Inter Tight', sans-serif",
    fontSize: "32px",
    fontWeight: 700,
    color: "#f0f4f0",
    margin: "0 0 8px 0",
    letterSpacing: "-0.5px",
  },
  subtitle: {
    fontFamily: "'Inter Tight', sans-serif",
    fontSize: "14px",
    color: "rgba(201,203,190,0.5)",
    margin: "0 0 28px 0",
    lineHeight: 1.5,
  },
  toggleBar: {
    display: "flex",
    background: "rgba(0,0,0,0.3)",
    border: "1px solid rgba(206,247,158,0.08)",
    borderRadius: "10px",
    padding: "4px",
    marginBottom: "28px",
  },
  toggleBtn: {
    flex: 1,
    padding: "10px",
    background: "transparent",
    border: "none",
    borderRadius: "8px",
    color: "rgba(206,247,158,0.4)",
    fontFamily: "'Roboto Mono', monospace",
    fontSize: "11px",
    letterSpacing: "1px",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
  toggleBtnActive: {
    background: "#cef79e",
    color: "#030a0c",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "18px",
  },
  fieldGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  label: {
    fontFamily: "'Roboto Mono', monospace",
    fontSize: "10px",
    letterSpacing: "1.5px",
    color: "rgba(206,247,158,0.4)",
  },
  input: {
    padding: "12px 16px",
    background: "rgba(0,0,0,0.3)",
    border: "1px solid rgba(206,247,158,0.12)",
    borderRadius: "10px",
    color: "#f0f4f0",
    fontFamily: "'Inter Tight', sans-serif",
    fontSize: "15px",
    outline: "none",
    transition: "border-color 0.2s ease",
  },
  errorBox: {
    background: "rgba(239, 68, 68, 0.08)",
    border: "1px solid rgba(239, 68, 68, 0.3)",
    borderRadius: "10px",
    padding: "12px 16px",
    color: "#fca5a5",
    fontFamily: "'Inter Tight', sans-serif",
    fontSize: "13px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  errorIcon: {
    fontSize: "14px",
  },
  submitBtn: {
    marginTop: "4px",
    padding: "14px",
    background: "#cef79e",
    color: "#030a0c",
    border: "none",
    borderRadius: "10px",
    fontFamily: "'Roboto Mono', monospace",
    fontSize: "13px",
    letterSpacing: "1px",
    cursor: "pointer",
    fontWeight: 700,
    transition: "all 0.2s ease",
  },
  submitBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
  disclaimer: {
    marginTop: "24px",
    fontFamily: "'Roboto Mono', monospace",
    fontSize: "10px",
    color: "rgba(201,203,190,0.2)",
    textAlign: "center",
    lineHeight: 1.6,
  },
};
