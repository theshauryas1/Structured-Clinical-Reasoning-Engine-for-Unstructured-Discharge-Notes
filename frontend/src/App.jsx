import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./styles.css";
import Navbar3D from "./components/Navbar3D";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import DiagnosticsPage from "./pages/DiagnosticsPage";
import DetailPage from "./pages/DetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        minHeight: "100vh",
        backgroundColor: "#030a0c",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        position: "relative",
      }}>
        <Navbar3D />

        <div style={{ flex: 1 }}>
          <Routes>
            <Route path="/"           element={<DashboardPage />} />
            <Route path="/history"    element={<HistoryPage />} />
            <Route path="/diagnostics" element={<DiagnosticsPage />} />
            <Route path="/report/:id" element={<DetailPage />} />
          </Routes>
        </div>

        {/* Footer */}
        <footer style={{
          borderTop: "1px solid rgba(206,247,158,0.06)",
          padding: "20px 32px",
          background: "rgba(0,0,0,0.5)",
          backdropFilter: "blur(20px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}>
          <div style={{
            fontFamily: "'Roboto Mono', monospace",
            fontSize: 10,
            color: "rgba(201,203,190,0.2)",
            letterSpacing: "1px",
          }}>
            © 2026 NEXUS CRE · AI Clinical Reasoning Engine · Not for Clinical Use
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {[
              ["NVIDIA NIM", "https://build.nvidia.com"],
              ["Helsinki NLP", "https://huggingface.co/Helsinki-NLP"],
            ].map(([label, href]) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: 9,
                  color: "rgba(206,247,158,0.3)",
                  textDecoration: "none",
                  letterSpacing: "0.5px",
                  transition: "color 0.2s",
                }}
              >
                {label} ↗
              </a>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 5, height: 5, borderRadius: "50%",
              background: "#4ade80",
              boxShadow: "0 0 6px #4ade80",
              animation: "pulse-dot 2s infinite",
              display: "inline-block",
            }} />
            <span style={{
              fontFamily: "'Roboto Mono', monospace",
              fontSize: 9,
              color: "rgba(74,222,128,0.4)",
              letterSpacing: "1px",
            }}>
              ALL SYSTEMS NOMINAL
            </span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
