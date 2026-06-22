import { useEffect, useRef } from "react";

/**
 * ProcessingOrb - A stunning animated 3D processing indicator
 * shown while the AI engine is running
 */
export default function ProcessingOrb({ label = "NEURAL ENGINE ACTIVE" }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    const cx = W / 2;
    const cy = H / 2;
    let animId;
    let t = 0;

    function drawRing(radius, width, speed, colorStart, colorEnd, alpha, t) {
      const grad = ctx.createConicalGradient
        ? null
        : ctx.createLinearGradient(cx - radius, cy, cx + radius, cy);

      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.strokeStyle = colorStart;
      ctx.lineWidth = width;
      ctx.globalAlpha = alpha;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    function draw() {
      animId = requestAnimationFrame(draw);
      t += 0.016;
      ctx.clearRect(0, 0, W, H);

      // Outer glow
      const outerGlow = ctx.createRadialGradient(cx, cy, 30, cx, cy, 90);
      outerGlow.addColorStop(0, "rgba(206,247,158,0.08)");
      outerGlow.addColorStop(1, "rgba(206,247,158,0)");
      ctx.fillStyle = outerGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, 90, 0, Math.PI * 2);
      ctx.fill();

      // Multiple spinning arcs
      const arcs = [
        { r: 65, start: t * 1.2, sweep: 1.8, color: "#cef79e", width: 2.5, alpha: 0.9 },
        { r: 65, start: t * 1.2 + Math.PI, sweep: 0.8, color: "#4ade80", width: 1.5, alpha: 0.5 },
        { r: 52, start: -t * 0.9, sweep: 2.2, color: "#22d3ee", width: 2.0, alpha: 0.7 },
        { r: 52, start: -t * 0.9 + Math.PI, sweep: 0.6, color: "#818cf8", width: 1.0, alpha: 0.4 },
        { r: 40, start: t * 1.8, sweep: 1.2, color: "#fbbf24", width: 1.5, alpha: 0.5 },
        { r: 40, start: t * 1.8 + Math.PI, sweep: 2.8, color: "#cef79e", width: 0.8, alpha: 0.25 },
      ];

      arcs.forEach(({ r, start, sweep, color, width, alpha }) => {
        ctx.beginPath();
        ctx.arc(cx, cy, r, start, start + sweep);
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.lineCap = "round";
        ctx.globalAlpha = alpha;
        ctx.shadowColor = color;
        ctx.shadowBlur = 12;
        ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
      });

      // Dot markers on rings
      [65, 52, 40].forEach((r, ri) => {
        const speed = [1.2, -0.9, 1.8][ri];
        const angle = t * speed;
        const dx = Math.cos(angle) * r;
        const dy = Math.sin(angle) * r;
        const col = ["#cef79e", "#22d3ee", "#fbbf24"][ri];

        ctx.beginPath();
        ctx.arc(cx + dx, cy + dy, 3.5, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.shadowColor = col;
        ctx.shadowBlur = 18;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Core pulse
      const pulse = 0.7 + 0.3 * Math.sin(t * 4);
      const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20 * pulse);
      coreGrad.addColorStop(0, "rgba(206,247,158,0.9)");
      coreGrad.addColorStop(0.4, "rgba(206,247,158,0.4)");
      coreGrad.addColorStop(1, "rgba(206,247,158,0)");
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, 20 * pulse, 0, Math.PI * 2);
      ctx.fill();

      // Inner bright core
      ctx.beginPath();
      ctx.arc(cx, cy, 6 * pulse, 0, Math.PI * 2);
      ctx.fillStyle = "#fff";
      ctx.shadowColor = "#cef79e";
      ctx.shadowBlur = 20;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Radiating lines (like radar)
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2 + t * 0.3;
        const len = 30 + Math.sin(t * 3 + i) * 8;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle) * 8, cy + Math.sin(angle) * 8);
        ctx.lineTo(cx + Math.cos(angle) * len, cy + Math.sin(angle) * len);
        ctx.strokeStyle = "#cef79e";
        ctx.lineWidth = 0.5;
        ctx.globalAlpha = 0.15 + Math.sin(t * 2 + i * 0.8) * 0.1;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    }
    draw();

    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "48px 0",
      gap: 24,
    }}>
      <canvas
        ref={canvasRef}
        style={{ width: 200, height: 200 }}
        width={200}
        height={200}
      />
      <div style={{
        fontFamily: "'Roboto Mono', monospace",
        fontSize: 11,
        color: "#cef79e",
        letterSpacing: "3px",
        textTransform: "uppercase",
        animation: "pulse-dot 2s infinite",
      }}>
        {label}
      </div>
      <div style={{
        fontFamily: "'Roboto Mono', monospace",
        fontSize: 10,
        color: "rgba(201,203,190,0.4)",
        letterSpacing: "1px",
        maxWidth: 280,
        textAlign: "center",
        lineHeight: 1.6,
      }}>
        Multi-Agent Timeline Reconstruction · Contradiction Mining · Differential Calibration
      </div>
    </div>
  );
}
