import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import * as THREE from "three";

function HexLogo() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.z = 4;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(52, 52);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Hex geometry
    const hexShape = new THREE.Shape();
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2 - Math.PI / 6;
      const x = Math.cos(angle) * 1.1;
      const y = Math.sin(angle) * 1.1;
      if (i === 0) hexShape.moveTo(x, y);
      else hexShape.lineTo(x, y);
    }
    hexShape.closePath();

    const extSettings = { depth: 0.3, bevelEnabled: true, bevelSize: 0.06, bevelThickness: 0.06, bevelSegments: 3 };
    const { ExtrudeGeometry } = THREE;
    const hexGeo = new ExtrudeGeometry(hexShape, extSettings);
    hexGeo.center();

    const hexMat = new THREE.MeshStandardMaterial({
      color: 0xcef79e,
      emissive: 0x44aa22,
      emissiveIntensity: 0.7,
      metalness: 0.9,
      roughness: 0.1,
    });
    const hex = new THREE.Mesh(hexGeo, hexMat);
    scene.add(hex);

    // Inner cross
    const barGeo = new THREE.BoxGeometry(0.12, 1.0, 0.5);
    const barMat = new THREE.MeshStandardMaterial({ color: 0x0a1a0f, emissive: 0x000000 });
    const bar1 = new THREE.Mesh(barGeo, barMat);
    const bar2 = new THREE.Mesh(barGeo, barMat);
    bar2.rotation.z = Math.PI / 2;
    hex.add(bar1);
    hex.add(bar2);

    scene.add(new THREE.AmbientLight(0xffffff, 1));
    const pLight = new THREE.PointLight(0xcef79e, 3, 10);
    pLight.position.set(2, 2, 2);
    scene.add(pLight);

    const clock = new THREE.Clock();
    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      hex.rotation.y = t * 0.6;
      hex.rotation.x = Math.sin(t * 0.4) * 0.2;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} width={52} height={52} style={{ display: "block" }} />;
}

// Animated biosignal line (ECG-style)
function BiosignalStrip() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    let offset = 0;
    let animId;

    function ecgSegment(x) {
      // Mimic an ECG waveform
      const t = (x % 120) / 120;
      if (t < 0.1) return Math.sin(t / 0.1 * Math.PI) * 3;
      if (t < 0.15) return -2 + Math.sin((t - 0.1) / 0.05 * Math.PI) * 2;
      if (t < 0.2) return -2 + (t - 0.15) / 0.05 * 18;
      if (t < 0.22) return 16 - (t - 0.2) / 0.02 * 20;
      if (t < 0.25) return -4 + (t - 0.22) / 0.03 * 6;
      if (t < 0.35) return 2 + Math.sin((t - 0.25) / 0.1 * Math.PI) * 4;
      return 0;
    }

    const draw = () => {
      animId = requestAnimationFrame(draw);
      ctx.clearRect(0, 0, w, h);
      offset += 0.8;

      ctx.beginPath();
      ctx.strokeStyle = "#cef79e";
      ctx.lineWidth = 1.5;
      ctx.shadowColor = "#cef79e";
      ctx.shadowBlur = 6;

      for (let x = 0; x < w; x++) {
        const y = h / 2 - ecgSegment(x + offset);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Trailing fade
      const grad = ctx.createLinearGradient(0, 0, w, 0);
      grad.addColorStop(0, "rgba(10,26,15,0.9)");
      grad.addColorStop(0.6, "rgba(10,26,15,0)");
      grad.addColorStop(1, "rgba(10,26,15,0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    };
    draw();

    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      width={180}
      height={36}
      style={{ display: "block", opacity: 0.7 }}
    />
  );
}

const NAV_LINKS = [
  { to: "/", label: "Dashboard", badge: null },
  { to: "/history", label: "History", badge: null },
  { to: "/diagnostics", label: "Diagnostics", badge: "AI" },
];

export default function Navbar3D() {
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState(() => localStorage.getItem("nexus_cre_api_key") || "");
  const [isSaved, setIsSaved] = useState(false);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 1000,
        transition: "all 0.4s ease",
        background: scrolled
          ? "rgba(6,14,18,0.92)"
          : "rgba(6,14,18,0.6)",
        backdropFilter: "blur(24px)",
        borderBottom: "1px solid rgba(206,247,158,0.08)",
        boxShadow: scrolled
          ? "0 4px 40px rgba(0,0,0,0.7), 0 1px 0 rgba(206,247,158,0.06)"
          : "none",
      }}
    >
      <nav
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 24px",
          height: 68,
          display: "flex",
          alignItems: "center",
          gap: 0,
        }}
      >
        {/* Logo */}
        <Link to="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 12, marginRight: 36 }}>
          <HexLogo />
          <div>
            <div style={{
              fontFamily: "'Inter Tight', sans-serif",
              fontWeight: 700,
              fontSize: 15,
              color: "#cef79e",
              letterSpacing: "-0.3px",
              lineHeight: 1.1,
            }}>
              NEXUS<span style={{ color: "rgba(206,247,158,0.4)" }}>://</span>CRE
            </div>
            <div style={{
              fontFamily: "'Roboto Mono', monospace",
              fontSize: 9,
              color: "rgba(201,203,190,0.45)",
              letterSpacing: "1.5px",
              textTransform: "uppercase",
            }}>
              Clinical Reasoning Engine
            </div>
          </div>
        </Link>

        {/* Biosignal strip */}
        <div style={{ marginRight: "auto", display: "flex", alignItems: "center" }}>
          <BiosignalStrip />
        </div>

        {/* Nav links */}
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          {NAV_LINKS.map(({ to, label, badge }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                style={{
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "8px 16px",
                  borderRadius: 10,
                  textDecoration: "none",
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: 12,
                  letterSpacing: "0.5px",
                  textTransform: "uppercase",
                  color: active ? "#cef79e" : "rgba(201,203,190,0.6)",
                  background: active
                    ? "rgba(206,247,158,0.06)"
                    : "transparent",
                  border: active
                    ? "1px solid rgba(206,247,158,0.15)"
                    : "1px solid transparent",
                  transition: "all 0.2s ease",
                }}
              >
                {active && (
                  <span style={{
                    width: 5,
                    height: 5,
                    borderRadius: "50%",
                    background: "#cef79e",
                    boxShadow: "0 0 8px #cef79e",
                    animation: "pulse-dot 2s infinite",
                    flexShrink: 0,
                  }} />
                )}
                {label}
                {badge && (
                  <span style={{
                    padding: "1px 5px",
                    borderRadius: 4,
                    background: "rgba(34,211,238,0.15)",
                    border: "1px solid rgba(34,211,238,0.3)",
                    color: "#22d3ee",
                    fontSize: 8,
                    fontFamily: "'Roboto Mono', monospace",
                    letterSpacing: "1px",
                  }}>
                    {badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Status indicator */}
        <div style={{
          marginLeft: 20,
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "6px 12px",
          background: "rgba(74,222,128,0.05)",
          border: "1px solid rgba(74,222,128,0.15)",
          borderRadius: 8,
          fontFamily: "'Roboto Mono', monospace",
          fontSize: 9,
          color: "#4ade80",
          letterSpacing: "1px",
        }}>
          <span style={{
            width: 5,
            height: 5,
            borderRadius: "50%",
            background: "#4ade80",
            boxShadow: "0 0 6px #4ade80",
            animation: "pulse-dot 1.5s infinite",
          }} />
          ONLINE
        </div>

        {/* API Security Config Key */}
        <button
          onClick={() => {
            setApiKeyInput(localStorage.getItem("nexus_cre_api_key") || "");
            setShowSecurityModal(true);
          }}
          className="btn-hover-scale"
          style={{
            marginLeft: 12,
            background: "rgba(206,247,158,0.06)",
            border: "1px solid rgba(206,247,158,0.15)",
            borderRadius: 8,
            padding: "6px 10px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
          }}
          title="API Key Configuration"
        >
          <span style={{ fontSize: 12 }}>🔑</span>
        </button>
      </nav>

      {/* Security Modal Overlay */}
      {showSecurityModal && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(3,10,12,0.85)",
          backdropFilter: "blur(20px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 99999,
          padding: 20,
        }}>
          <div style={{
            background: "rgba(6,18,20,0.95)",
            border: "1px solid rgba(206,247,158,0.2)",
            borderRadius: 16,
            padding: "32px 36px",
            width: "100%",
            maxWidth: 480,
            boxShadow: "0 24px 80px rgba(0,0,0,0.9), 0 0 40px rgba(206,247,158,0.08)",
            position: "relative",
          }}>
            {/* Close Button */}
            <button
              onClick={() => {
                setShowSecurityModal(false);
                setIsSaved(false);
              }}
              style={{
                position: "absolute",
                top: 20,
                right: 20,
                background: "transparent",
                border: "none",
                color: "rgba(201,203,190,0.4)",
                fontSize: 18,
                cursor: "pointer",
              }}
            >
              ✕
            </button>

            {/* Modal Title */}
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <span style={{ fontSize: 24 }}>🔒</span>
              <div style={{ textAlign: "left" }}>
                <h2 style={{
                  margin: 0,
                  fontFamily: "'Inter Tight', sans-serif",
                  fontSize: 18,
                  fontWeight: 700,
                  color: "#cef79e",
                }}>
                  Security Controls
                </h2>
                <p style={{
                  margin: 0,
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: 8,
                  color: "rgba(34,211,238,0.5)",
                  letterSpacing: "1px",
                  textTransform: "uppercase",
                }}>
                  Access Key Configuration
                </p>
              </div>
            </div>

            <p style={{
              fontFamily: "'Inter Tight', sans-serif",
              fontSize: 12,
              color: "rgba(255,255,255,0.7)",
              lineHeight: 1.6,
              marginBottom: 20,
              textAlign: "left",
            }}>
              If the clinical backend requires API key validation (via <code style={{ color: "#cef79e", background: "rgba(206,247,158,0.08)", padding: "2px 4px", borderRadius: 4, fontSize: 10 }}>CLINICAL_REASONING_API_KEY</code>), enter your key below to authenticate report generation, chat, and retrieval requests.
            </p>

            {/* Input fields */}
            <div style={{ marginBottom: 24, textAlign: "left" }}>
              <label style={{
                display: "block",
                fontFamily: "'Roboto Mono', monospace",
                fontSize: 9,
                color: "rgba(201,203,190,0.5)",
                marginBottom: 8,
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}>
                Nexus CRE API Key
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="Enter API validation key..."
                  style={{
                    width: "100%",
                    padding: "12px 40px 12px 14px",
                    background: "rgba(0,0,0,0.4)",
                    border: "1px solid rgba(206,247,158,0.15)",
                    borderRadius: 10,
                    color: "#fff",
                    fontFamily: "'Roboto Mono', monospace",
                    fontSize: 12,
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
                {/* Show/Hide eye */}
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  style={{
                    position: "absolute",
                    right: 12,
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "transparent",
                    border: "none",
                    color: "rgba(201,203,190,0.4)",
                    cursor: "pointer",
                    fontSize: 14,
                  }}
                >
                  {showKey ? "👁️" : "🙈"}
                </button>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={() => {
                  localStorage.removeItem("nexus_cre_api_key");
                  setApiKeyInput("");
                  setIsSaved(true);
                  setTimeout(() => {
                    setIsSaved(false);
                    setShowSecurityModal(false);
                  }, 800);
                }}
                style={{
                  padding: "10px 16px",
                  background: "transparent",
                  border: "1px solid rgba(248,113,113,0.3)",
                  borderRadius: 10,
                  color: "#f87171",
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: 10,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                CLEAR KEY
              </button>
              <button
                onClick={() => {
                  localStorage.setItem("nexus_cre_api_key", apiKeyInput.trim());
                  setIsSaved(true);
                  setTimeout(() => {
                    setIsSaved(false);
                    setShowSecurityModal(false);
                  }, 800);
                }}
                style={{
                  padding: "10px 20px",
                  background: "#cef79e",
                  border: "none",
                  borderRadius: 10,
                  color: "#0a1a0f",
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: 10,
                  fontWeight: 700,
                  cursor: "pointer",
                  transition: "all 0.2s",
                  boxShadow: "0 0 12px rgba(206,247,158,0.2)",
                }}
              >
                {isSaved ? "SAVED ✓" : "SAVE CONFIG"}
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
