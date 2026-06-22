import { useEffect, useRef } from "react";
import * as THREE from "three";
import gsap from "gsap";

/**
 * HolographicCard - A 3D holographic panel that reacts to mouse hover
 * with rainbow iridescence, depth parallax, and a scanning beam.
 */
export default function HolographicCard({ children, style = {}, className = "" }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const innerRef = useRef(null);
  const sceneRef = useRef({});

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const w = container.clientWidth;
    const h = container.clientHeight;

    // ─── Three.js Setup ────────────────────────────────────────────────────
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // ─── Holographic Background Plane ──────────────────────────────────────
    const planeGeo = new THREE.PlaneGeometry(2 * (w / h), 2, 32, 32);
    const planeMat = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        mouse: { value: new THREE.Vector2(0.5, 0.5) },
        resolution: { value: new THREE.Vector2(w, h) },
      },
      transparent: true,
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vNormal;
        uniform float time;
        uniform vec2 mouse;
        void main() {
          vUv = uv;
          vNormal = normal;
          vec3 pos = position;
          // Subtle wave distortion
          pos.z += sin(uv.x * 8.0 + time * 1.5) * 0.008;
          pos.z += cos(uv.y * 6.0 + time * 1.2) * 0.008;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform vec2 mouse;
        varying vec2 vUv;
        
        vec3 hsl2rgb(vec3 c) {
          vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
          return c.z + c.y * (rgb - 0.5) * (1.0 - abs(2.0 * c.z - 1.0));
        }
        
        void main() {
          vec2 uv = vUv;
          
          // Iridescent rainbow sweep
          float angle = atan(uv.y - 0.5, uv.x - 0.5);
          float dist = length(uv - 0.5);
          float hue = mod(angle / (3.14159 * 2.0) + time * 0.08 + dist * 0.5, 1.0);
          vec3 rainbow = hsl2rgb(vec3(hue, 0.8, 0.55));
          
          // Grid pattern
          vec2 grid = fract(uv * 18.0);
          float gridLine = step(0.95, grid.x) + step(0.95, grid.y);
          
          // Scanline
          float scanY = fract(time * 0.22);
          float scanBeam = smoothstep(0.0, 0.03, abs(uv.y - scanY)) < 1.0 
            ? (1.0 - smoothstep(0.0, 0.025, abs(uv.y - scanY))) 
            : 0.0;
          
          // Mouse proximity glow
          float mouseDist = length(uv - mouse);
          float mouseGlow = 1.0 - smoothstep(0.0, 0.5, mouseDist);
          
          // Combine
          vec3 base = vec3(0.03, 0.07, 0.05);
          vec3 color = base + rainbow * 0.12 + gridLine * vec3(0.0, 0.25, 0.15);
          color += vec3(0.2, 1.0, 0.6) * scanBeam * 0.35;
          color += rainbow * mouseGlow * 0.25;
          
          float alpha = 0.08 + gridLine * 0.05 + scanBeam * 0.15 + mouseGlow * 0.06;
          gl_FragColor = vec4(color, alpha);
        }
      `,
    });

    const plane = new THREE.Mesh(planeGeo, planeMat);
    scene.add(plane);

    sceneRef.current = { scene, camera, renderer, planeMat };

    // ─── Animation Loop ────────────────────────────────────────────────────
    let animId;
    const clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      planeMat.uniforms.time.value = clock.getElapsedTime();
      renderer.render(scene, camera);
    };
    animate();

    // ─── Mouse parallax on card ───────────────────────────────────────────
    let bounds = container.getBoundingClientRect();

    const handleMouseMove = (e) => {
      bounds = container.getBoundingClientRect();
      const mx = (e.clientX - bounds.left) / bounds.width;
      const my = (e.clientY - bounds.top) / bounds.height;

      planeMat.uniforms.mouse.value.set(mx, 1 - my);

      // 3D tilt via CSS
      const rx = (my - 0.5) * 12;
      const ry = (mx - 0.5) * -12;
      gsap.to(innerRef.current, {
        rotateX: rx,
        rotateY: ry,
        duration: 0.6,
        ease: "power2.out",
        transformPerspective: 1200,
      });
    };

    const handleMouseEnter = () => {
      gsap.to(container, { "--holo-opacity": 1, duration: 0.4 });
    };

    const handleMouseLeave = () => {
      planeMat.uniforms.mouse.value.set(0.5, 0.5);
      gsap.to(innerRef.current, {
        rotateX: 0,
        rotateY: 0,
        duration: 0.8,
        ease: "elastic.out(1, 0.6)",
      });
    };

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseenter", handleMouseEnter);
    container.addEventListener("mouseleave", handleMouseLeave);

    const handleResize = () => {
      const nw = container.clientWidth;
      const nh = container.clientHeight;
      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
      planeMat.uniforms.resolution.value.set(nw, nh);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseenter", handleMouseEnter);
      container.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        position: "relative",
        borderRadius: "20px",
        overflow: "hidden",
        border: "1px solid rgba(206, 247, 158, 0.15)",
        background: "rgba(6, 14, 18, 0.85)",
        backdropFilter: "blur(20px)",
        boxShadow: "0 0 0 1px rgba(206,247,158,0.08), 0 20px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(206,247,158,0.1)",
        ...style,
      }}
    >
      {/* Three.js holographic layer */}
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* Corner decorations */}
      {["tl", "tr", "bl", "br"].map((pos) => (
        <div
          key={pos}
          style={{
            position: "absolute",
            zIndex: 2,
            width: 12,
            height: 12,
            borderColor: "rgba(206,247,158,0.5)",
            borderStyle: "solid",
            borderWidth: 0,
            ...(pos === "tl" ? { top: 8, left: 8, borderTopWidth: 2, borderLeftWidth: 2, borderTopLeftRadius: 4 } : {}),
            ...(pos === "tr" ? { top: 8, right: 8, borderTopWidth: 2, borderRightWidth: 2, borderTopRightRadius: 4 } : {}),
            ...(pos === "bl" ? { bottom: 8, left: 8, borderBottomWidth: 2, borderLeftWidth: 2, borderBottomLeftRadius: 4 } : {}),
            ...(pos === "br" ? { bottom: 8, right: 8, borderBottomWidth: 2, borderRightWidth: 2, borderBottomRightRadius: 4 } : {}),
          }}
        />
      ))}

      {/* Content */}
      <div
        ref={innerRef}
        style={{
          position: "relative",
          zIndex: 1,
          transformStyle: "preserve-3d",
          willChange: "transform",
        }}
      >
        {children}
      </div>
    </div>
  );
}
