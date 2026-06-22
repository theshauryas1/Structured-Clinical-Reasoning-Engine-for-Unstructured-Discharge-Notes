import React, { useState, useEffect, useRef } from "react";
import TimelineView from "./TimelineView";
import ContradictionCards from "./ContradictionCards";
import ConfidenceBars from "./ConfidenceBars";

const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

export default function ReportWorkspace({ output, translations, uiLanguage }) {
  const [viewMode, setViewMode] = useState("clinical"); // 'clinical' or 'plain'
  
  // Explanation state
  const [explanationText, setExplanationText] = useState("");
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatMode, setChatMode] = useState("clinical"); // 'clinical' or 'layperson'
  const [sendingChat, setSendingChat] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  // Sync chatMode with viewMode automatically for better UX
  useEffect(() => {
    setChatMode(viewMode === "clinical" ? "clinical" : "layperson");
  }, [viewMode]);

  const t = translations;
  const report = output?.display_report || output;
  const timeline = report?.timeline || {};
  const contradictions = report?.contradiction_flags || [];
  const differentials = report?.differentials || [];
  const confidenceScores = report?.confidence_scores || [];

  const loadExplanation = async () => {
    if (explanationText || !output?.note_id) return;
    setLoadingExplanation(true);
    try {
      const res = await fetch(`${API_URL}/explain/${output.note_id}`, {
        method: "POST",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Error generating plain-language translation");
      }
      setExplanationText(data.explanation);
    } catch (err) {
      console.error(err);
      alert(err.message || "Error generating explanation");
    } finally {
      setLoadingExplanation(false);
    }
  };

  useEffect(() => {
    if (viewMode === "plain") {
      loadExplanation();
    }
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
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          note_id: output.note_id,
          messages: newMessages,
          mode: chatMode,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Error calling chatbot");
      }

      setChatMessages([...newMessages, { role: "assistant", content: data.response }]);
    } catch (err) {
      console.error(err);
      setChatMessages([...newMessages, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setSendingChat(false);
    }
  };

  const styles = {
    workspace: {
      marginTop: "40px",
    },
    toggleBar: {
      display: "flex",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-nav)",
      padding: "4px",
      background: "rgba(0, 0, 0, 0.2)",
      marginBottom: "30px",
      maxWidth: "500px",
    },
    toggleBtn: {
      flex: 1,
      padding: "10px 16px",
      border: "none",
      borderRadius: "10px",
      cursor: "pointer",
      background: "transparent",
      color: "var(--color-lichen)",
      fontSize: "13px",
      letterSpacing: "-0.26px",
      transition: "all 0.15s ease",
    },
    toggleBtnActive: {
      background: "var(--color-bioluminescent-lime)",
      color: "var(--color-abyssal-ink)",
    },
    layoutGrid: {
      display: "flex",
      gap: "30px",
      flexWrap: "wrap",
    },
    mainCol: {
      flex: "3 1 600px",
      minWidth: "320px",
    },
    sidebarCol: {
      flex: "2 1 360px",
      minWidth: "320px",
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      padding: "24px",
      display: "flex",
      flexDirection: "column",
      maxHeight: "800px",
    },
    sectionTitle: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "24px",
      lineHeight: "1.2",
      letterSpacing: "-0.14px",
      color: "var(--color-paper)",
      marginBottom: "20px",
      borderBottom: "1px solid var(--color-graphite)",
      paddingBottom: "10px",
      textTransform: "uppercase",
    },
    chatHeader: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      borderBottom: "1px solid var(--color-graphite)",
      paddingBottom: "12px",
      marginBottom: "12px",
    },
    chatTitle: {
      fontFamily: "var(--font-aspekta)",
      fontSize: "19px",
      color: "var(--color-paper)",
      textTransform: "uppercase",
    },
    chatSelect: {
      padding: "4px 8px",
      fontSize: "12px",
      fontFamily: "var(--font-roboto-mono)",
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      color: "var(--color-bioluminescent-lime)",
    },
    chatDisclaimer: {
      background: "rgba(180, 35, 24, 0.05)",
      color: "#ff8080",
      fontFamily: "var(--font-aspekta)",
      fontSize: "13px",
      padding: "10px 14px",
      borderRadius: "8px",
      marginBottom: "14px",
      borderLeft: "4px solid #b42318",
      lineHeight: "1.3",
    },
    chatHistory: {
      flex: 1,
      overflowY: "auto",
      minHeight: "350px",
      maxHeight: "550px",
      padding: "12px",
      background: "rgba(0, 0, 0, 0.15)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "8px",
      marginBottom: "14px",
      display: "flex",
      flexDirection: "column",
      gap: "10px",
    },
    bubble: {
      padding: "10px 14px",
      borderRadius: "12px",
      maxWidth: "90%",
      fontSize: "14px",
      lineHeight: "1.4",
      fontFamily: "var(--font-aspekta)",
    },
    userBubble: {
      border: "1px solid var(--color-bioluminescent-lime)",
      color: "var(--color-bioluminescent-lime)",
      alignSelf: "flex-end",
      borderRadius: "12px 12px 0 12px",
    },
    assistantBubble: {
      border: "1px solid var(--color-graphite)",
      color: "var(--color-paper)",
      alignSelf: "flex-start",
      borderRadius: "12px 12px 12px 0",
      background: "rgba(255, 255, 255, 0.02)",
      whiteSpace: "pre-wrap",
    },
    chatInputRow: {
      display: "flex",
      gap: "8px",
    },
    chatInput: {
      flex: 1,
      padding: "10px 14px",
      fontSize: "14px",
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "8px",
      color: "var(--color-paper)",
    },
    chatBtn: {
      padding: "10px 16px",
      background: "var(--color-bioluminescent-lime)",
      color: "var(--color-abyssal-ink)",
      border: "none",
      borderRadius: "8px",
    },
    explainCard: {
      background: "var(--color-abyssal-ink)",
      border: "1px solid var(--color-graphite)",
      borderRadius: "var(--radius-cards)",
      padding: "30px",
      color: "var(--color-paper)",
      fontFamily: "var(--font-aspekta)",
    },
    explainText: {
      whiteSpace: "pre-wrap",
      lineHeight: "1.6",
      fontSize: "16px",
      color: "var(--color-paper)",
    },
  };

  return (
    <section style={styles.workspace}>
      {/* Switcher */}
      <div style={styles.toggleBar}>
        <button
          className="btn-hover-scale"
          style={{
            ...styles.toggleBtn,
            ...(viewMode === "clinical" ? styles.toggleBtnActive : {}),
          }}
          onClick={() => setViewMode("clinical")}
        >
          CLINICAL AUDIT REPORT
        </button>
        <button
          className="btn-hover-scale"
          style={{
            ...styles.toggleBtn,
            ...(viewMode === "plain" ? styles.toggleBtnActive : {}),
          }}
          onClick={() => setViewMode("plain")}
        >
          PLAIN-LANGUAGE SUMMARY
        </button>
      </div>

      <div style={styles.layoutGrid}>
        {/* Main Panel */}
        <div style={styles.mainCol}>
          {viewMode === "clinical" ? (
            <div className="animate-fade-in-up">
              <h2 style={styles.sectionTitle}>Timeline Reconstruction.</h2>
              <TimelineView timeline={timeline} />

              <h2 style={{ ...styles.sectionTitle, marginTop: "40px" }}>Contradiction Audits.</h2>
              <ContradictionCards contradictions={contradictions} />

              <h2 style={{ ...styles.sectionTitle, marginTop: "40px" }}>Calibrated Hypotheses.</h2>
              <ConfidenceBars
                confidenceScores={confidenceScores}
                differentials={differentials}
              />
            </div>
          ) : (
            <div className="animate-fade-in-up">
              <h2 style={styles.sectionTitle}>Patient Translation.</h2>
              <div style={styles.explainCard}>
                {loadingExplanation ? (
                  <p style={{ color: "var(--color-lichen)", fontFamily: "var(--font-roboto-mono)", fontSize: "14px" }}>
                    Translating and generating analogies...
                  </p>
                ) : (
                  <div style={styles.explainText}>{explanationText}</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Chatbot Sidebar */}
        <div style={styles.sidebarCol}>
          <div style={styles.chatHeader}>
            <span style={styles.chatTitle}>Report Q&A.</span>
            <select
              style={styles.chatSelect}
              value={chatMode}
              onChange={(e) => setChatMode(e.target.value)}
            >
              <option value="clinical">Clinical Mode</option>
              <option value="layperson">Patient Mode</option>
            </select>
          </div>
          
          <div style={styles.chatDisclaimer}>
            {chatMode === "clinical"
              ? "Disclaimer: Auditor mode. Not for raw diagnostic decision making."
              : "Disclaimer: Empathetic advocate mode. Consult a physician for diagnosis."}
          </div>

          <div style={styles.chatHistory}>
            {chatMessages.length === 0 ? (
              <div style={{ color: "var(--color-graphite)", fontSize: "13px", padding: "10px", textAlign: "center" }}>
                Ask a question about timeline events, contradiction evidence, or ranked diagnoses.
              </div>
            ) : (
              chatMessages.map((msg, index) => (
                <div
                  key={index}
                  className={msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}
                  style={{
                    ...styles.bubble,
                    ...(msg.role === "user" ? styles.userBubble : styles.assistantBubble),
                  }}
                >
                  {msg.content}
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={sendChatMessage} style={styles.chatInputRow}>
            <input
              type="text"
              placeholder={t.chatPlaceholder || "Ask a question..."}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              style={styles.chatInput}
              disabled={sendingChat}
            />
            <button
              type="submit"
              className="btn-hover-scale"
              style={styles.chatBtn}
              disabled={sendingChat || !chatInput.trim()}
            >
              {sendingChat ? "..." : "SEND"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
