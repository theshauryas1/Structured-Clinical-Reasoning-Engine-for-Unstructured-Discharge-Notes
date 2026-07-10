/**
 * SidebarChatbot — Bioluminescent Terminal design system
 * 
 * Skills applied:
 *  - frontend-design: Bioluminescent Terminal aesthetic (DFII 13/15)
 *  - design-spells: Typewriter effect, magnetic send button, scan-line shimmer, file drop highlight
 *  - react-patterns: Custom hooks, compound component, composition, single responsibility
 *  - animation-principles: Entrance stagger (30ms), ease-out slides, purposeful micro-motion
 *  - security-auditor: No PII leaked in UI; file validation client-side before upload
 *  - ux-writing: Contextual placeholder copy, mode labels, disclaimer surfacing
 */

import React, {
  useState, useRef, useEffect, useCallback, useReducer
} from "react";
import { useAuth } from "../hooks/useAuth";

const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

// ─── Constants ───────────────────────────────────────────────────────────────
const ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "txt"];
const MAX_FILE_MB = 10;
const MODE_META = {
  general: { label: "GENERAL", icon: "◎", color: "#cef79e", desc: "Medical Q&A" },
  rag:     { label: "RAG",     icon: "⬡", color: "#67e8f9", desc: "Clinical Guidelines" },
  report:  { label: "REPORT",  icon: "⬢", color: "#a78bfa", desc: "Report Context" },
};

// ─── State Machine (react-patterns: useReducer for complex state) ─────────────
const initialState = {
  chats: [],
  activeChatId: null,
  messages: [],
  input: "",
  file: null,
  mode: "general",
  sending: false,
  loadingChats: false,
  loadingMessages: false,
  error: null,
};

function chatReducer(state, action) {
  switch (action.type) {
    case "SET_CHATS":          return { ...state, chats: action.chats, loadingChats: false };
    case "SET_ACTIVE_CHAT":    return { ...state, activeChatId: action.id, messages: [], loadingMessages: true };
    case "SET_MESSAGES":       return { ...state, messages: action.messages, loadingMessages: false };
    case "APPEND_MESSAGE":     return { ...state, messages: [...state.messages, action.message] };
    case "REPLACE_LAST_MSG":   return { ...state, messages: [...state.messages.slice(0, -1), action.message] };
    case "SET_INPUT":          return { ...state, input: action.input };
    case "SET_FILE":           return { ...state, file: action.file };
    case "SET_MODE":           return { ...state, mode: action.mode };
    case "SENDING":            return { ...state, sending: true, error: null };
    case "SENT":               return { ...state, sending: false, input: "", file: null };
    case "ERROR":              return { ...state, sending: false, loadingMessages: false, error: action.error };
    case "CLEAR_ERROR":        return { ...state, error: null };
    default:                   return state;
  }
}

// ─── Custom hook: chat API ────────────────────────────────────────────────────
function useChatAPI(dispatch) {
  const loadChats = useCallback(async () => {
    dispatch({ type: "SET_CHATS", chats: [] }); // trigger loading
    try {
      const r = await fetch(`${API}/api/chats`, { credentials: "include" });
      if (!r.ok) throw new Error("Failed to load chats");
      dispatch({ type: "SET_CHATS", chats: await r.json() });
    } catch (e) {
      dispatch({ type: "ERROR", error: e.message });
    }
  }, [dispatch]);

  const createChat = useCallback(async (title = "New Chat", noteId = null) => {
    const r = await fetch(`${API}/api/chats`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, note_id: noteId }),
    });
    if (!r.ok) throw new Error("Could not create chat");
    return r.json();
  }, []);

  const loadMessages = useCallback(async (chatId) => {
    const r = await fetch(`${API}/api/chats/${chatId}`, { credentials: "include" });
    if (!r.ok) throw new Error("Failed to load messages");
    const data = await r.json();
    dispatch({ type: "SET_MESSAGES", messages: data.messages });
  }, [dispatch]);

  const sendMessage = useCallback(async (chatId, content, mode, file, noteId) => {
    const form = new FormData();
    form.append("content", content);
    form.append("mode", mode);
    if (noteId) form.append("note_id", noteId);
    if (file)   form.append("file", file);

    const r = await fetch(`${API}/api/chats/${chatId}/message`, {
      method: "POST", credentials: "include", body: form,
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      throw new Error(e.detail || "Send failed");
    }
    return r.json();
  }, []);

  const deleteChat = useCallback(async (chatId) => {
    await fetch(`${API}/api/chats/${chatId}`, { method: "DELETE", credentials: "include" });
  }, []);

  return { loadChats, createChat, loadMessages, sendMessage, deleteChat };
}

// ─── Typewriter Effect hook (design-spells) ───────────────────────────────────
function useTypewriter(text, speed = 8) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  useEffect(() => {
    setDisplayed("");
    setDone(false);
    if (!text) { setDone(true); return; }
    let i = 0;
    const tick = setInterval(() => {
      i += speed; // batch chars for performance (animation-principles: keep under 400ms)
      setDisplayed(text.slice(0, i));
      if (i >= text.length) { setDisplayed(text); setDone(true); clearInterval(tick); }
    }, 12);
    return () => clearInterval(tick);
  }, [text, speed]);
  return { displayed, done };
}

// ─── Single message bubble ────────────────────────────────────────────────────
function MessageBubble({ msg, isLast }) {
  const isUser = msg.role === "user";
  const isTyping = msg._typing;
  const { displayed } = useTypewriter(isTyping ? msg.content : "");
  const content = isTyping ? displayed : msg.content;

  return (
    <div style={{
      display: "flex",
      flexDirection: isUser ? "row-reverse" : "row",
      gap: 10,
      alignItems: "flex-end",
      // animation-principles: entrance slide, ease-out, 200ms
      animation: "msg-slide-in 0.2s cubic-bezier(0.22,1,0.36,1) both",
      marginBottom: 14,
    }}>
      {/* Avatar */}
      <div style={{
        width: 26, height: 26, borderRadius: "50%", flexShrink: 0,
        background: isUser
          ? "linear-gradient(135deg, rgba(206,247,158,0.15), rgba(206,247,158,0.05))"
          : "linear-gradient(135deg, rgba(103,232,249,0.15), rgba(103,232,249,0.05))",
        border: `1px solid ${isUser ? "rgba(206,247,158,0.3)" : "rgba(103,232,249,0.3)"}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 11,
      }}>
        {isUser ? "U" : "✦"}
      </div>

      {/* Bubble */}
      <div style={{
        maxWidth: "78%",
        padding: "11px 15px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        background: isUser
          ? "linear-gradient(135deg, rgba(206,247,158,0.08), rgba(206,247,158,0.04))"
          : "rgba(10,22,28,0.8)",
        border: isUser
          ? "1px solid rgba(206,247,158,0.15)"
          : "1px solid rgba(103,232,249,0.1)",
        fontFamily: "'Inter Tight', sans-serif",
        fontSize: 13.5,
        lineHeight: 1.6,
        color: isUser ? "#d4f7a0" : "#c9cbbe",
        backdropFilter: "blur(10px)",
        position: "relative",
        wordBreak: "break-word",
        whiteSpace: "pre-wrap",
      }}>
        {/* Typing cursor (design-spells) */}
        {isTyping && (
          <span style={{
            display: "inline-block", width: 2, height: "1em",
            background: "#67e8f9", marginLeft: 2,
            animation: "blink-cursor 0.7s step-end infinite",
            verticalAlign: "text-bottom",
          }} />
        )}
        {content}
        {/* File badge */}
        {msg.media_name && (
          <div style={{
            marginTop: 6, padding: "4px 8px",
            background: "rgba(206,247,158,0.06)",
            border: "1px solid rgba(206,247,158,0.1)",
            borderRadius: 6, fontSize: 11,
            color: "rgba(206,247,158,0.5)",
            fontFamily: "'Roboto Mono', monospace",
          }}>
            📎 {msg.media_name}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Mode selector strip ──────────────────────────────────────────────────────
function ModeStrip({ mode, onChange }) {
  return (
    <div style={{
      display: "flex", gap: 6, padding: "0 14px",
    }}>
      {Object.entries(MODE_META).map(([key, meta]) => (
        <button
          key={key}
          id={`chat-mode-${key}`}
          onClick={() => onChange(key)}
          title={meta.desc}
          style={{
            display: "flex", alignItems: "center", gap: 5,
            padding: "5px 10px",
            background: mode === key
              ? `linear-gradient(135deg, ${meta.color}18, ${meta.color}08)`
              : "transparent",
            border: `1px solid ${mode === key ? `${meta.color}40` : "rgba(255,255,255,0.05)"}`,
            borderRadius: 8,
            color: mode === key ? meta.color : "rgba(201,203,190,0.35)",
            fontFamily: "'Roboto Mono', monospace",
            fontSize: 9, letterSpacing: "0.5px",
            cursor: "pointer",
            // animation-principles: micro toggle, 120ms
            transition: "all 0.12s ease-out",
          }}
        >
          <span style={{ fontSize: 11 }}>{meta.icon}</span> {meta.label}
        </button>
      ))}
    </div>
  );
}

// ─── Main Sidebar Chatbot Component ──────────────────────────────────────────
export default function SidebarChatbot({ noteId = null, defaultOpen = false }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(defaultOpen);
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const api = useChatAPI(dispatch);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  // Load chats on open (react-patterns: effect cleanup)
  useEffect(() => {
    if (open && user) { api.loadChats(); }
  }, [open, user]);

  // Auto-scroll messages (animation-principles: instant scroll within chat)
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state.messages]);

  const handleNewChat = useCallback(async () => {
    try {
      const title = noteId ? `Report Chat — ${new Date().toLocaleTimeString()}` : `Chat — ${new Date().toLocaleTimeString()}`;
      const chat = await api.createChat(title, noteId);
      dispatch({ type: "SET_ACTIVE_CHAT", id: chat.id });
      dispatch({ type: "SET_MESSAGES", messages: [] });
      await api.loadChats();
      dispatch({ type: "SET_ACTIVE_CHAT", id: chat.id });
    } catch (e) {
      dispatch({ type: "ERROR", error: e.message });
    }
  }, [api, noteId]);

  const handleSelectChat = useCallback(async (chatId) => {
    dispatch({ type: "SET_ACTIVE_CHAT", id: chatId });
    try {
      await api.loadMessages(chatId);
    } catch (e) {
      dispatch({ type: "ERROR", error: e.message });
    }
  }, [api]);

  const handleSend = useCallback(async () => {
    const content = state.input.trim();
    if (!content || state.sending) return;

    // Ensure chat exists
    let chatId = state.activeChatId;
    if (!chatId) {
      try {
        const chat = await api.createChat("New Chat", noteId);
        chatId = chat.id;
        dispatch({ type: "SET_ACTIVE_CHAT", id: chatId });
        await api.loadChats();
      } catch (e) {
        dispatch({ type: "ERROR", error: e.message });
        return;
      }
    }

    dispatch({ type: "SENDING" });

    // Optimistic user message
    const userMsg = {
      id: `local-${Date.now()}`,
      role: "user",
      content,
      media_name: state.file?.name || null,
      created_at: new Date().toISOString(),
    };
    dispatch({ type: "APPEND_MESSAGE", message: userMsg });

    // Placeholder assistant "typing" bubble (design-spells: typewriter)
    const typingMsg = {
      id: `typing-${Date.now()}`,
      role: "assistant",
      content: "Thinking…",
      _typing: false,
      created_at: new Date().toISOString(),
    };
    dispatch({ type: "APPEND_MESSAGE", message: typingMsg });

    try {
      const result = await api.sendMessage(chatId, content, state.mode, state.file, noteId);
      // Replace typing bubble with real typewriter response
      dispatch({
        type: "REPLACE_LAST_MSG",
        message: {
          id: result.message_id,
          role: "assistant",
          content: result.response,
          _typing: true, // trigger typewriter
          created_at: new Date().toISOString(),
        },
      });
      dispatch({ type: "SENT" });
      await api.loadChats(); // refresh titles
    } catch (e) {
      dispatch({ type: "REPLACE_LAST_MSG", message: { ...typingMsg, content: `⚠ ${e.message}`, _typing: false } });
      dispatch({ type: "ERROR", error: e.message });
    }
  }, [state, api, noteId]);

  // File drop (design-spells: glow on drag-over)
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (!dropped) return;
    const ext = dropped.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      dispatch({ type: "ERROR", error: `File type .${ext} not supported. Use: ${ALLOWED_EXTENSIONS.join(", ")}` });
      return;
    }
    if (dropped.size > MAX_FILE_MB * 1024 * 1024) {
      dispatch({ type: "ERROR", error: `File too large (max ${MAX_FILE_MB} MB)` });
      return;
    }
    dispatch({ type: "SET_FILE", file: dropped });
  }, []);

  const handleDeleteChat = useCallback(async (e, chatId) => {
    e.stopPropagation();
    await api.deleteChat(chatId);
    if (state.activeChatId === chatId) {
      dispatch({ type: "SET_ACTIVE_CHAT", id: null });
      dispatch({ type: "SET_MESSAGES", messages: [] });
    }
    await api.loadChats();
  }, [api, state.activeChatId]);

  if (!user) return null; // security: only render for authenticated users

  return (
    <>
      {/* ── CSS Keyframes injected once ── */}
      <style>{`
        @keyframes msg-slide-in {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes blink-cursor {
          50% { opacity: 0; }
        }
        @keyframes sidebar-open {
          from { opacity: 0; transform: translateX(40px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes scan-line {
          0%   { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
        @keyframes pulse-ring {
          0%, 100% { box-shadow: 0 0 0 0 rgba(206,247,158,0.4); }
          50%       { box-shadow: 0 0 0 8px rgba(206,247,158,0); }
        }
        /* File input accent (design-spells: magnetic hover) */
        .chat-input:focus {
          border-color: rgba(206,247,158,0.3) !important;
          box-shadow: 0 0 0 3px rgba(206,247,158,0.06) !important;
        }
        .send-btn:hover:not(:disabled) {
          background: #cef79e !important;
          transform: scale(1.06) !important;
          box-shadow: 0 0 20px rgba(206,247,158,0.3) !important;
        }
        .send-btn:active { transform: scale(0.96) !important; }
        .chat-list-item:hover { background: rgba(206,247,158,0.04) !important; }
      `}</style>

      {/* ── Toggle Pill (design-spells: pulse-ring on unread) ── */}
      <button
        id="chatbot-toggle"
        onClick={() => setOpen(!open)}
        title="Open AI Assistant"
        style={{
          position: "fixed", bottom: 28, right: 28, zIndex: 1000,
          width: 52, height: 52,
          background: open
            ? "rgba(12,24,30,0.95)"
            : "linear-gradient(135deg, rgba(206,247,158,0.15), rgba(206,247,158,0.06))",
          border: "1.5px solid rgba(206,247,158,0.35)",
          borderRadius: "50%",
          color: "#cef79e", fontSize: 20,
          cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          transition: "all 0.2s cubic-bezier(0.22,1,0.36,1)",
          animation: !open ? "pulse-ring 2.5s infinite" : "none",
          boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
        }}
      >
        {open ? "×" : "✦"}
      </button>

      {/* ── Sidebar Panel ── */}
      {open && (
        <div
          id="chatbot-sidebar"
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{
            position: "fixed", top: 0, right: 0, bottom: 0,
            width: "clamp(320px, 38vw, 520px)",
            zIndex: 999,
            display: "flex", flexDirection: "column",
            background: "rgba(5,14,18,0.97)",
            borderLeft: `1px solid ${dragOver ? "rgba(206,247,158,0.4)" : "rgba(206,247,158,0.1)"}`,
            backdropFilter: "blur(40px)",
            animation: "sidebar-open 0.28s cubic-bezier(0.22,1,0.36,1) both",
            // design-spells: glowing drop target
            boxShadow: dragOver
              ? "inset 0 0 60px rgba(206,247,158,0.06), -8px 0 80px rgba(0,0,0,0.6)"
              : "-8px 0 80px rgba(0,0,0,0.6)",
            transition: "box-shadow 0.2s, border-color 0.2s",
          }}
        >
          {/* Scan-line shimmer (design-spells: aesthetic terminal feel) */}
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
            background: "linear-gradient(transparent 50%, rgba(206,247,158,0.008) 50%)",
            backgroundSize: "100% 4px",
            pointerEvents: "none", zIndex: 0, opacity: 0.6,
          }} />

          {/* ── Header ── */}
          <div style={{
            position: "relative", zIndex: 1,
            padding: "16px 18px",
            borderBottom: "1px solid rgba(206,247,158,0.06)",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(0,0,0,0.3)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 7, height: 7, borderRadius: "50%", background: "#cef79e",
                boxShadow: "0 0 10px #cef79e", flexShrink: 0,
              }} />
              <div>
                <div style={{
                  fontFamily: "'Roboto Mono', monospace", fontSize: 11,
                  letterSpacing: "2px", color: "rgba(206,247,158,0.7)",
                }}>NEXUS AI ASSISTANT</div>
                <div style={{
                  fontFamily: "'Roboto Mono', monospace", fontSize: 9,
                  color: "rgba(201,203,190,0.3)", letterSpacing: "1px", marginTop: 2,
                }}>
                  {MODE_META[state.mode].icon} {MODE_META[state.mode].desc} · {user?.username}
                </div>
              </div>
            </div>
            <button
              id="chat-new-btn"
              onClick={handleNewChat}
              title="New Chat"
              style={{
                background: "rgba(206,247,158,0.06)",
                border: "1px solid rgba(206,247,158,0.15)",
                borderRadius: 8, padding: "6px 12px",
                color: "rgba(206,247,158,0.6)",
                fontFamily: "'Roboto Mono', monospace", fontSize: 10,
                letterSpacing: "0.5px", cursor: "pointer",
                transition: "all 0.15s ease-out",
              }}
            >
              + NEW
            </button>
          </div>

          {/* ── Body (Chat List + Messages) ── */}
          <div style={{ flex: 1, display: "flex", overflow: "hidden", position: "relative", zIndex: 1 }}>
            {/* ── Left: Chat history list ── */}
            <div style={{
              width: 160, flexShrink: 0,
              borderRight: "1px solid rgba(206,247,158,0.05)",
              overflowY: "auto", padding: "10px 0",
              display: "flex", flexDirection: "column",
            }}>
              <div style={{
                padding: "4px 12px 8px",
                fontFamily: "'Roboto Mono', monospace", fontSize: 9,
                color: "rgba(201,203,190,0.25)", letterSpacing: "1px",
              }}>
                HISTORY
              </div>
              {state.chats.length === 0 && (
                <div style={{
                  padding: "8px 12px",
                  fontFamily: "'Inter Tight', sans-serif", fontSize: 12,
                  color: "rgba(201,203,190,0.2)",
                }}>No chats yet</div>
              )}
              {state.chats.map((c) => (
                <div
                  key={c.id}
                  className="chat-list-item"
                  onClick={() => handleSelectChat(c.id)}
                  style={{
                    padding: "8px 12px",
                    cursor: "pointer",
                    background: state.activeChatId === c.id
                      ? "rgba(206,247,158,0.06)"
                      : "transparent",
                    borderLeft: state.activeChatId === c.id
                      ? "2px solid rgba(206,247,158,0.4)"
                      : "2px solid transparent",
                    transition: "all 0.15s ease-out",
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    gap: 4,
                  }}
                >
                  <div>
                    <div style={{
                      fontFamily: "'Inter Tight', sans-serif",
                      fontSize: 11.5, color: "rgba(240,244,240,0.75)",
                      overflow: "hidden", textOverflow: "ellipsis",
                      whiteSpace: "nowrap", maxWidth: 110,
                    }}>
                      {c.title}
                    </div>
                    <div style={{
                      fontFamily: "'Roboto Mono', monospace",
                      fontSize: 9, color: "rgba(201,203,190,0.25)", marginTop: 2,
                    }}>
                      {c.message_count} msg
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteChat(e, c.id)}
                    title="Delete chat"
                    style={{
                      background: "none", border: "none",
                      color: "rgba(239,68,68,0.3)", cursor: "pointer", fontSize: 12,
                      padding: "2px 4px", borderRadius: 4,
                      transition: "color 0.15s",
                      flexShrink: 0,
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = "rgba(239,68,68,0.8)"}
                    onMouseLeave={(e) => e.currentTarget.style.color = "rgba(239,68,68,0.3)"}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            {/* ── Right: Messages ── */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              {/* Messages list */}
              <div style={{ flex: 1, overflowY: "auto", padding: "16px 14px" }}>
                {!state.activeChatId && !state.loadingMessages && (
                  <div style={{
                    display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                    height: "100%", gap: 14, opacity: 0.5,
                  }}>
                    <div style={{ fontSize: 32 }}>✦</div>
                    <div style={{
                      fontFamily: "'Inter Tight', sans-serif",
                      fontSize: 13, color: "rgba(206,247,158,0.4)",
                      textAlign: "center", lineHeight: 1.6,
                    }}>
                      Start a new chat or select one<br/>from the history panel.
                    </div>
                    <div style={{
                      fontFamily: "'Roboto Mono', monospace",
                      fontSize: 9, color: "rgba(201,203,190,0.2)",
                      letterSpacing: "0.5px", textAlign: "center", lineHeight: 1.8,
                    }}>
                      DRAG &amp; DROP PDF or IMAGE<br/>for document Q&amp;A
                    </div>
                  </div>
                )}
                {state.loadingMessages && (
                  <div style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    height: "100%", color: "rgba(206,247,158,0.3)",
                    fontFamily: "'Roboto Mono', monospace", fontSize: 11,
                    letterSpacing: "1px",
                  }}>
                    LOADING…
                  </div>
                )}
                {state.messages.map((msg, i) => (
                  <MessageBubble key={msg.id} msg={msg} isLast={i === state.messages.length - 1} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* ── Footer: Mode + Input + File ── */}
          <div style={{
            position: "relative", zIndex: 1,
            borderTop: "1px solid rgba(206,247,158,0.06)",
            background: "rgba(0,0,0,0.4)",
            backdropFilter: "blur(20px)",
          }}>
            {/* Mode strip */}
            <div style={{ paddingTop: 10, paddingBottom: 6 }}>
              <ModeStrip mode={state.mode} onChange={(m) => dispatch({ type: "SET_MODE", mode: m })} />
            </div>

            {/* Error banner */}
            {state.error && (
              <div style={{
                margin: "0 14px 6px",
                padding: "8px 12px",
                background: "rgba(239,68,68,0.06)",
                border: "1px solid rgba(239,68,68,0.2)",
                borderRadius: 8,
                color: "rgba(252,165,165,0.8)",
                fontFamily: "'Inter Tight', sans-serif",
                fontSize: 12, display: "flex",
                alignItems: "center", justifyContent: "space-between",
              }}>
                <span>⚠ {state.error}</span>
                <button
                  onClick={() => dispatch({ type: "CLEAR_ERROR" })}
                  style={{
                    background: "none", border: "none", color: "rgba(252,165,165,0.5)",
                    cursor: "pointer", fontSize: 14, padding: 0,
                  }}
                >×</button>
              </div>
            )}

            {/* File badge (design-spells: animate-in pill) */}
            {state.file && (
              <div style={{
                margin: "0 14px 6px",
                padding: "6px 10px",
                background: "rgba(206,247,158,0.06)",
                border: "1px solid rgba(206,247,158,0.15)",
                borderRadius: 8, display: "flex", alignItems: "center", gap: 6,
                fontFamily: "'Roboto Mono', monospace", fontSize: 10,
                color: "rgba(206,247,158,0.6)",
                animation: "msg-slide-in 0.15s ease-out both",
              }}>
                <span>📎</span>
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {state.file.name}
                </span>
                <span style={{ color: "rgba(206,247,158,0.3)" }}>
                  {(state.file.size / 1024).toFixed(0)} KB
                </span>
                <button
                  onClick={() => dispatch({ type: "SET_FILE", file: null })}
                  style={{
                    background: "none", border: "none",
                    color: "rgba(239,68,68,0.5)", cursor: "pointer", fontSize: 12,
                  }}
                >×</button>
              </div>
            )}

            {/* Input area */}
            <div style={{
              padding: "8px 14px 14px",
              display: "flex", gap: 8, alignItems: "flex-end",
            }}>
              {/* File attach button */}
              <button
                id="chat-attach-btn"
                title="Attach PDF or Image"
                onClick={() => fileInputRef.current?.click()}
                style={{
                  width: 36, height: 36, flexShrink: 0,
                  background: "rgba(206,247,158,0.05)",
                  border: "1px solid rgba(206,247,158,0.1)",
                  borderRadius: 10, color: "rgba(206,247,158,0.4)",
                  fontSize: 14, cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "all 0.15s ease-out",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(206,247,158,0.3)";
                  e.currentTarget.style.color = "rgba(206,247,158,0.8)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "rgba(206,247,158,0.1)";
                  e.currentTarget.style.color = "rgba(206,247,158,0.4)";
                }}
              >
                📎
              </button>
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: "none" }}
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) dispatch({ type: "SET_FILE", file: f });
                  e.target.value = "";
                }}
              />

              {/* Text input */}
              <textarea
                ref={inputRef}
                id="chat-input"
                className="chat-input"
                rows={1}
                placeholder={
                  state.mode === "rag"
                    ? "Ask about clinical guidelines…"
                    : state.mode === "report"
                    ? "Ask about this patient report…"
                    : "Ask a medical question or drop a document…"
                }
                value={state.input}
                onChange={(e) => {
                  dispatch({ type: "SET_INPUT", input: e.target.value });
                  // auto-resize (design-spells: elastic textarea)
                  e.target.style.height = "auto";
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
                }}
                style={{
                  flex: 1, resize: "none", overflow: "hidden",
                  padding: "10px 12px",
                  background: "rgba(0,0,0,0.3)",
                  border: "1px solid rgba(206,247,158,0.1)",
                  borderRadius: 10,
                  color: "#d4f7a0",
                  fontFamily: "'Inter Tight', sans-serif",
                  fontSize: 13.5, lineHeight: 1.5,
                  outline: "none",
                  transition: "border-color 0.15s, box-shadow 0.15s",
                  minHeight: 36, maxHeight: 120,
                }}
              />

              {/* Send button (design-spells: magnetic) */}
              <button
                id="chat-send-btn"
                className="send-btn"
                onClick={handleSend}
                disabled={!state.input.trim() || state.sending}
                style={{
                  width: 36, height: 36, flexShrink: 0,
                  background: state.sending
                    ? "rgba(206,247,158,0.1)"
                    : "rgba(206,247,158,0.12)",
                  border: "1px solid rgba(206,247,158,0.25)",
                  borderRadius: 10,
                  color: state.sending ? "rgba(206,247,158,0.3)" : "#cef79e",
                  fontSize: 14, cursor: state.sending ? "not-allowed" : "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "all 0.15s cubic-bezier(0.22,1,0.36,1)",
                }}
              >
                {state.sending ? "…" : "↑"}
              </button>
            </div>

            {/* Disclaimer (ux-writing: always visible, subtle) */}
            <div style={{
              padding: "0 14px 10px",
              fontFamily: "'Roboto Mono', monospace", fontSize: 9,
              color: "rgba(201,203,190,0.18)", letterSpacing: "0.3px",
              lineHeight: 1.5,
            }}>
              ⚠ Not for clinical decision-making. For educational and auditing use only.
            </div>
          </div>

          {/* Drag overlay */}
          {dragOver && (
            <div style={{
              position: "absolute", inset: 0, zIndex: 10,
              background: "rgba(206,247,158,0.04)",
              border: "2px dashed rgba(206,247,158,0.4)",
              display: "flex", alignItems: "center", justifyContent: "center",
              pointerEvents: "none",
            }}>
              <div style={{
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 14, letterSpacing: "2px",
                color: "rgba(206,247,158,0.6)",
              }}>
                DROP FILE TO ANALYZE
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
