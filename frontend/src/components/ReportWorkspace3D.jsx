import React, { useState, useEffect, useRef } from "react";
import gsap from "gsap";
import TimelineView from "./TimelineView";
import ContradictionCards from "./ContradictionCards";
import ConfidenceBars from "./ConfidenceBars";
import HolographicCard from "./3d/HolographicCard";
import MoleculeOrbit from "./3d/MoleculeOrbit";
import DataVortex from "./3d/DataVortex";
import TimelineRiverGL from "./3d/TimelineRiverGL";

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

// ─── Tab button ──────────────────────────────────────────────────────────────
function TabBtn({ active, onClick, children, icon }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        padding: "12px 20px",
        border: "none",
        borderRadius: 10,
        background: active
          ? "rgba(206,247,158,0.1)"
          : "transparent",
        color: active ? "#cef79e" : "rgba(201,203,190,0.4)",
        fontFamily: "'Roboto Mono', monospace",
        fontSize: 10,
        letterSpacing: "1.5px",
        textTransform: "uppercase",
        cursor: "pointer",
        transition: "all 0.2s ease",
        boxShadow: active ? "inset 0 0 0 1px rgba(206,247,158,0.2)" : "none",
      }}
    >
      {icon && <span style={{ fontSize: 14 }}>{icon}</span>}
      {children}
      {active && (
        <span style={{
          width: 5, height: 5, borderRadius: "50%",
          background: "#cef79e", boxShadow: "0 0 6px #cef79e",
        }} />
      )}
    </button>
  );
}

// ─── Chat bubble ─────────────────────────────────────────────────────────────
function ChatBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
    }}>
      <div style={{
        maxWidth: "88%",
        padding: "10px 16px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser
          ? "rgba(206,247,158,0.08)"
          : "rgba(0,0,0,0.3)",
        border: isUser
          ? "1px solid rgba(206,247,158,0.2)"
          : "1px solid rgba(77,87,87,0.3)",
        color: isUser ? "#cef79e" : "rgba(255,255,255,0.85)",
        fontFamily: "'Inter Tight', sans-serif",
        fontSize: 13,
        lineHeight: 1.6,
        whiteSpace: "pre-wrap",
      }}>
        {!isUser && (
          <div style={{
            fontFamily: "'Roboto Mono', monospace",
            fontSize: 8,
            color: "rgba(34,211,238,0.5)",
            letterSpacing: "1px",
            marginBottom: 4,
          }}>
            NEXUS AI ·
          </div>
        )}
        {msg.content}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function ReportWorkspace3D({ output, translations, uiLanguage }) {
  const [viewMode, setViewMode] = useState("clinical");
  const [explanationText, setExplanationText] = useState("");
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatMode, setChatMode] = useState("clinical");
  const [sendingChat, setSendingChat] = useState(false);
  const [vizMode, setVizMode] = useState("molecule"); // molecule | river | vortex
  const chatEndRef = useRef(null);
  const workspaceRef = useRef(null);

  const t = translations;
  const report = output?.display_report || output;
  const timeline = report?.timeline || {};
  const contradictions = report?.contradiction_flags || [];
  const differentials = report?.differentials || [];
  const confidenceScores = report?.confidence_scores || [];

  // Prepare timeline events for 3D river
  const timelineEvents = Object.entries(timeline).flatMap(([phase, events]) =>
    (Array.isArray(events) ? events : [events]).map((ev) => ({
      date: phase,
      label: typeof ev === "string" ? ev.slice(0, 22) : (ev.event || "Event"),
      type: phase.toLowerCase().includes("discharge") ? "discharge"
        : phase.toLowerCase().includes("admit") ? "critical"
        : phase.toLowerCase().includes("treat") ? "treatment"
        : "symptom",
      icon: phase.toLowerCase().includes("discharge") ? "🏠"
        : phase.toLowerCase().includes("admit") ? "🏥"
        : phase.toLowerCase().includes("treat") ? "💊"
        : "📋",
    }))
  );

  // Molecule data
  const diagData = differentials.slice(0, 7).map((d, i) => ({
    label: d.diagnosis || d.name || `Dx${i}`,
    confidence: confidenceScores.find((c) => c.diagnosis === d.diagnosis)?.score || (0.9 - i * 0.12),
  }));

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => {
    setChatMode(viewMode === "clinical" ? "clinical" : "layperson");
  }, [viewMode]);

  // Entry animation
  useEffect(() => {
    if (workspaceRef.current) {
      gsap.fromTo(workspaceRef.current, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" });
    }
  }, []);

  const loadExplanation = async () => {
    if (explanationText || !output?.note_id) return;
    setLoadingExplanation(true);
    try {
      const res = await fetch(`${API_URL}/explain/${output.note_id}`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Error generating explanation");
      setExplanationText(data.explanation);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoadingExplanation(false);
    }
  };

  useEffect(() => {
    if (viewMode === "plain") loadExplanation();
  }, [viewMode]);

  const sendChatMessage = async (e) => {
    if (e) e.preventDefault();
    if (!chatInput.trim() || !output?.note_id) return;
    const userMsg = { role: "user", content: chatInput };
    const newMessages = [...chatMessages, userMsg];
    setChatMessages(newMessages);
    setChatInput("");
    setSendingChat(true);
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_id: output.note_id, messages: newMessages, mode: chatMode }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Error");
      setChatMessages([...newMessages, { role: "assistant", content: data.response }]);
    } catch (err) {
      setChatMessages([...newMessages, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setSendingChat(false);
    }
  };

  return (
    <section ref={workspaceRef}>

      {/* ── View mode switcher ──────────────────────────────────────────── */}
      <div style={{
        display: "flex",
        gap: 4,
        padding: 4,
        background: "rgba(0,0,0,0.3)",
        border: "1px solid rgba(77,87,87,0.3)",
        borderRadius: 14,
        marginBottom: 28,
        maxWidth: 520,
      }}>
        <TabBtn active={viewMode === "clinical"} onClick={() => setViewMode("clinical")} icon="🔬">
          Clinical Report
        </TabBtn>
        <TabBtn active={viewMode === "plain"} onClick={() => setViewMode("plain")} icon="📖">
          Patient Summary
        </TabBtn>
      </div>

      {/* ── 3D Visualization panel ─────────────────────────────────────── */}
      <HolographicCard style={{ marginBottom: 28, overflow: "hidden" }}>
        {/* Viz switcher */}
        <div style={{
          display: "flex",
          gap: 2,
          padding: "12px 20px 0",
          borderBottom: "1px solid rgba(206,247,158,0.06)",
        }}>
          {[
            ["molecule", "⚛", "Differential Orbits"],
            ["river", "⏱", "Timeline River"],
            ["vortex", "🌀", "Contradiction Vortex"],
          ].map(([id, icon, label]) => (
            <button
              key={id}
              onClick={() => setVizMode(id)}
              style={{
                padding: "8px 16px 12px",
                background: "transparent",
                border: "none",
                borderBottom: vizMode === id ? "2px solid #cef79e" : "2px solid transparent",
                color: vizMode === id ? "#cef79e" : "rgba(201,203,190,0.35)",
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 9,
                letterSpacing: "1px",
                textTransform: "uppercase",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                transition: "all 0.2s",
              }}
            >
              <span>{icon}</span> {label}
            </button>
          ))}
        </div>

        {/* 3D viewport */}
        <div style={{ height: 360, position: "relative" }}>
          {vizMode === "molecule" && <MoleculeOrbit diagnoses={diagData} active />}
          {vizMode === "river" && <TimelineRiverGL events={timelineEvents} />}
          {vizMode === "vortex" && <DataVortex contradictions={contradictions} />}

          {/* Overlay badge */}
          <div style={{
            position: "absolute",
            top: 16,
            right: 16,
            padding: "4px 10px",
            background: "rgba(0,0,0,0.5)",
            border: "1px solid rgba(206,247,158,0.1)",
            borderRadius: 6,
            fontFamily: "'Roboto Mono', monospace",
            fontSize: 8,
            color: "rgba(206,247,158,0.4)",
            letterSpacing: "1px",
            pointerEvents: "none",
          }}>
            WEBGL · LIVE
          </div>
        </div>
      </HolographicCard>

      {/* ── Main layout: report + chat ─────────────────────────────────── */}
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", alignItems: "flex-start" }}>

        {/* ── Left: Report content ──────────────────────────────────────── */}
        <div style={{ flex: "3 1 560px", minWidth: 320 }}>
          {viewMode === "clinical" ? (
            <div>
              {/* Timeline */}
              <HolographicCard style={{ marginBottom: 20 }}>
                <div style={{ padding: "24px 28px" }}>
                  <SectionHeader icon="⏱" label="Timeline Reconstruction" color="#22d3ee" />
                  <TimelineView timeline={timeline} />
                </div>
              </HolographicCard>

              {/* Contradictions */}
              <HolographicCard style={{ marginBottom: 20 }}>
                <div style={{ padding: "24px 28px" }}>
                  <SectionHeader icon="⚡" label="Contradiction Audits" color="#f87171" badge={contradictions.length} />
                  <ContradictionCards contradictions={contradictions} />
                </div>
              </HolographicCard>

              {/* Differentials */}
              <HolographicCard style={{ marginBottom: 20 }}>
                <div style={{ padding: "24px 28px" }}>
                  <SectionHeader icon="🧠" label="Calibrated Hypotheses" color="#cef79e" badge={differentials.length} />
                  <ConfidenceBars confidenceScores={confidenceScores} differentials={differentials} />
                </div>
              </HolographicCard>
            </div>
          ) : (
            <HolographicCard>
              <div style={{ padding: "24px 28px" }}>
                <SectionHeader icon="📖" label="Patient Translation" color="#818cf8" />
                {loadingExplanation ? (
                  <div style={{
                    padding: "40px 0",
                    textAlign: "center",
                    fontFamily: "'Roboto Mono', monospace",
                    fontSize: 11,
                    color: "rgba(206,247,158,0.5)",
                    letterSpacing: "1px",
                    animation: "pulse-dot 2s infinite",
                  }}>
                    TRANSLATING TO PLAIN LANGUAGE...
                  </div>
                ) : (
                  <div style={{
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.8,
                    fontSize: 15,
                    fontFamily: "'Inter Tight', sans-serif",
                    color: "rgba(255,255,255,0.85)",
                  }}>
                    {explanationText}
                  </div>
                )}
              </div>
            </HolographicCard>
          )}
        </div>

        {/* ── Right: Chat interface ─────────────────────────────────────── */}
        <div style={{ flex: "2 1 340px", minWidth: 300 }}>
          <HolographicCard style={{ position: "sticky", top: 88 }}>
            <div style={{ display: "flex", flexDirection: "column", height: 620, padding: "20px 22px" }}>
              {/* Chat header */}
              <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingBottom: 14,
                marginBottom: 14,
                borderBottom: "1px solid rgba(206,247,158,0.08)",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 16 }}>🤖</span>
                  <div>
                    <div style={{
                      fontFamily: "'Inter Tight', sans-serif",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "#cef79e",
                    }}>
                      Report Q&A
                    </div>
                    <div style={{
                      fontFamily: "'Roboto Mono', monospace",
                      fontSize: 8,
                      color: "rgba(34,211,238,0.5)",
                      letterSpacing: "1px",
                    }}>
                      NEXUS AI · POWERED
                    </div>
                  </div>
                </div>
                <select
                  value={chatMode}
                  onChange={(e) => setChatMode(e.target.value)}
                  style={{
                    padding: "4px 10px",
                    background: "rgba(0,0,0,0.4)",
                    border: "1px solid rgba(206,247,158,0.15)",
                    borderRadius: 8,
                    color: "#cef79e",
                    fontFamily: "'Roboto Mono', monospace",
                    fontSize: 9,
                    letterSpacing: "0.5px",
                    cursor: "pointer",
                  }}
                >
                  <option value="clinical">Clinical Mode</option>
                  <option value="layperson">Patient Mode</option>
                </select>
              </div>

              {/* Disclaimer */}
              <div style={{
                padding: "8px 12px",
                background: "rgba(220,38,38,0.06)",
                border: "1px solid rgba(220,38,38,0.15)",
                borderLeft: "3px solid rgba(220,38,38,0.5)",
                borderRadius: 8,
                marginBottom: 14,
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 9,
                color: "rgba(248,113,113,0.7)",
                letterSpacing: "0.3px",
                lineHeight: 1.5,
              }}>
                {chatMode === "clinical"
                  ? "⚠ Auditor mode. Not for raw diagnostic decisions."
                  : "⚠ Empathetic mode. Consult physician for diagnosis."}
              </div>

              {/* Messages */}
              <div style={{
                flex: 1,
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: 10,
                padding: "4px 0",
                marginBottom: 14,
              }}>
                {chatMessages.length === 0 ? (
                  <div style={{
                    padding: "40px 20px",
                    textAlign: "center",
                    fontFamily: "'Roboto Mono', monospace",
                    fontSize: 10,
                    color: "rgba(201,203,190,0.2)",
                    lineHeight: 1.8,
                    letterSpacing: "0.5px",
                  }}>
                    ASK ABOUT<br />
                    TIMELINE EVENTS<br />
                    CONTRADICTION FLAGS<br />
                    RANKED DIFFERENTIALS
                  </div>
                ) : (
                  chatMessages.map((msg, i) => <ChatBubble key={i} msg={msg} />)
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={sendChatMessage} style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={t.chatPlaceholder || "Ask about this report..."}
                  disabled={sendingChat}
                  style={{
                    flex: 1,
                    padding: "10px 14px",
                    background: "rgba(0,0,0,0.4)",
                    border: "1px solid rgba(77,87,87,0.4)",
                    borderRadius: 10,
                    color: "#fff",
                    fontFamily: "'Inter Tight', sans-serif",
                    fontSize: 13,
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  disabled={sendingChat || !chatInput.trim()}
                  style={{
                    padding: "10px 16px",
                    background: sendingChat
                      ? "rgba(206,247,158,0.1)"
                      : "rgba(206,247,158,0.85)",
                    color: sendingChat ? "#cef79e" : "#0a1a0f",
                    border: "none",
                    borderRadius: 10,
                    fontFamily: "'Roboto Mono', monospace",
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: "1px",
                    cursor: sendingChat ? "not-allowed" : "pointer",
                    transition: "all 0.2s",
                    minWidth: 60,
                  }}
                >
                  {sendingChat ? "···" : "SEND"}
                </button>
              </form>
            </div>
          </HolographicCard>
        </div>
      </div>
    </section>
  );
}

function SectionHeader({ icon, label, color, badge }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      marginBottom: 20,
      paddingBottom: 14,
      borderBottom: "1px solid rgba(206,247,158,0.06)",
    }}>
      <span style={{ fontSize: 16 }}>{icon}</span>
      <span style={{
        fontFamily: "'Inter Tight', sans-serif",
        fontSize: 16,
        fontWeight: 700,
        color: color || "#cef79e",
        letterSpacing: "-0.3px",
        textTransform: "uppercase",
      }}>
        {label}
      </span>
      {badge !== undefined && badge > 0 && (
        <span style={{
          padding: "2px 8px",
          borderRadius: 9999,
          background: `${color}18`,
          border: `1px solid ${color}33`,
          fontFamily: "'Roboto Mono', monospace",
          fontSize: 9,
          color,
          letterSpacing: "0.5px",
        }}>
          {badge}
        </span>
      )}
    </div>
  );
}
