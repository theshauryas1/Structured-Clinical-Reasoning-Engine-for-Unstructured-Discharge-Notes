import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const location = useLocation();

  const styles = {
    header: {
      background: "var(--color-abyssal-ink)",
      borderBottom: "1px solid var(--color-graphite)",
      padding: "20px 24px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      maxWidth: "1200px",
      margin: "0 auto",
      width: "100%",
    },
    logoGroup: {
      display: "flex",
      alignItems: "center",
      gap: "10px",
    },
    logoDot: {
      width: "8px",
      height: "8px",
      borderRadius: "50%",
      backgroundColor: "var(--color-bioluminescent-lime)",
    },
    logoText: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "19px",
      color: "var(--color-paper)",
      letterSpacing: "-0.5px",
      textDecoration: "none",
      textTransform: "uppercase",
    },
    navLinks: {
      display: "flex",
      gap: "12px",
      listStyle: "none",
    },
    link: {
      display: "inline-block",
      padding: "6px 14px",
      borderRadius: "var(--radius-nav)",
      border: "1px solid var(--color-graphite)",
      fontFamily: "var(--font-roboto-mono)",
      fontSize: "13px",
      letterSpacing: "-0.26px",
      textDecoration: "none",
      color: "var(--color-lichen)",
      transition: "all 0.15s ease",
    },
    activeLink: {
      background: "var(--color-bioluminescent-lime)",
      borderColor: "var(--color-bioluminescent-lime)",
      color: "var(--color-abyssal-ink)",
    },
  };

  return (
    <header style={styles.header}>
      <Link to="/" style={styles.logoGroup}>
        <div style={styles.logoDot} className="pulse-accent-dot"></div>
        <span style={styles.logoText}>INTEGRATED BIOSCIENCES</span>
      </Link>
      <nav>
        <ul style={styles.navLinks}>
          <li>
            <Link
              to="/"
              style={{
                ...styles.link,
                ...(location.pathname === "/" ? styles.activeLink : {}),
              }}
            >
              DASHBOARD
            </Link>
          </li>
          <li>
            <Link
              to="/history"
              style={{
                ...styles.link,
                ...(location.pathname === "/history" ? styles.activeLink : {}),
              }}
            >
              AUDIT HISTORY
            </Link>
          </li>
          <li>
            <Link
              to="/diagnostics"
              style={{
                ...styles.link,
                ...(location.pathname === "/diagnostics" ? styles.activeLink : {}),
              }}
            >
              DIAGNOSTICS
            </Link>
          </li>
        </ul>
      </nav>
    </header>
  );
}
