/**
 * App.jsx — Root app with AuthProvider, protected routes, and Sidebar Chatbot
 * 
 * Skills applied:
 *  - react-patterns: Context + AuthProvider wrapping, composition, lazy loading
 *  - security-auditor: Protect all routes behind auth; redirect unauthenticated users
 *  - animation-principles: Route transition (short fade, 200ms)
 */
import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles.css";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import Navbar3D from "./components/Navbar3D";
import SidebarChatbot from "./components/SidebarChatbot";

// Lazy-load pages (react-patterns: code-split per route)
const DashboardPage  = lazy(() => import("./pages/DashboardPage"));
const HistoryPage    = lazy(() => import("./pages/HistoryPage"));
const DiagnosticsPage = lazy(() => import("./pages/DiagnosticsPage"));
const DetailPage     = lazy(() => import("./pages/DetailPage"));
const LoginPage      = lazy(() => import("./pages/LoginPage"));

// ─── Protected Route (security-auditor: block unauthenticated access) ─────────
function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

// ─── Route guard: redirect logged-in users away from login ───────────────────
function PublicOnly({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (user) return <Navigate to="/" replace />;
  return children;
}

// ─── Minimal loading state (animation-principles: instant, no jank) ──────────
function LoadingScreen() {
  return (
    <div style={{
      minHeight: "100vh", display: "flex",
      alignItems: "center", justifyContent: "center",
      background: "#030a0c",
      fontFamily: "'Roboto Mono', monospace",
      fontSize: 11, letterSpacing: "2px",
      color: "rgba(206,247,158,0.35)",
    }}>
      INITIALIZING…
    </div>
  );
}

// ─── Page fade wrapper (animation-principles: 200ms fade-in on route change) ──
function PageWrapper({ children }) {
  return (
    <div style={{ animation: "page-fade 0.2s ease-out both" }}>
      {children}
    </div>
  );
}

// ─── Inner app (consumes auth context) ───────────────────────────────────────
function AppInner() {
  const { user, logout } = useAuth();

  return (
    <BrowserRouter>
      <style>{`
        @keyframes page-fade {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
      `}</style>

      <div style={{
        minHeight: "100vh",
        backgroundColor: "#030a0c",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        position: "relative",
      }}>
        {/* Navbar: pass user + logout so it can render account info */}
        <Navbar3D user={user} onLogout={logout} />

        <div style={{ flex: 1 }}>
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              {/* Public */}
              <Route
                path="/login"
                element={
                  <PublicOnly>
                    <PageWrapper><LoginPage /></PageWrapper>
                  </PublicOnly>
                }
              />

              {/* Protected */}
              <Route
                path="/"
                element={
                  <Protected>
                    <PageWrapper><DashboardPage /></PageWrapper>
                  </Protected>
                }
              />
              <Route
                path="/history"
                element={
                  <Protected>
                    <PageWrapper><HistoryPage /></PageWrapper>
                  </Protected>
                }
              />
              <Route
                path="/diagnostics"
                element={
                  <Protected>
                    <PageWrapper><DiagnosticsPage /></PageWrapper>
                  </Protected>
                }
              />
              <Route
                path="/report/:id"
                element={
                  <Protected>
                    <PageWrapper><DetailPage /></PageWrapper>
                  </Protected>
                }
              />

              {/* Catch-all → redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
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
            fontSize: 10, color: "rgba(201,203,190,0.2)", letterSpacing: "1px",
          }}>
            © 2026 NEXUS CRE · AI Clinical Reasoning Engine · Not for Clinical Use
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {[
              ["NVIDIA NIM", "https://build.nvidia.com"],
              ["Helsinki NLP", "https://huggingface.co/Helsinki-NLP"],
            ].map(([label, href]) => (
              <a key={label} href={href} target="_blank" rel="noreferrer" style={{
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 9, color: "rgba(206,247,158,0.3)",
                textDecoration: "none", letterSpacing: "0.5px",
                transition: "color 0.2s",
              }}>
                {label} ↗
              </a>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 5, height: 5, borderRadius: "50%",
              background: "#4ade80", boxShadow: "0 0 6px #4ade80",
              animation: "pulse-dot 2s infinite", display: "inline-block",
            }} />
            <span style={{
              fontFamily: "'Roboto Mono', monospace",
              fontSize: 9, color: "rgba(74,222,128,0.4)", letterSpacing: "1px",
            }}>
              ALL SYSTEMS NOMINAL
            </span>
          </div>
        </footer>

        {/* Global sidebar chatbot — only visible for authenticated users */}
        <SidebarChatbot />
      </div>
    </BrowserRouter>
  );
}

// ─── Root: AuthProvider wraps everything ─────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
