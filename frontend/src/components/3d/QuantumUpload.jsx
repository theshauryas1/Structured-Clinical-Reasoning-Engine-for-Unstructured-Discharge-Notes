import { useEffect, useRef } from "react";
import * as THREE from "three";
import gsap from "gsap";

/**
 * QuantumUpload - A stunning 3D animated upload zone with particle
 * field that reacts to drag-and-drop state
 */
export default function QuantumUpload({
  file,
  onFileSelect,
  onDrop,
  dragActive,
  onDragEnter,
  onDragLeave,
  onDragOver,
  uploadInfo,
  uploadLabel,
  ocrNotice,
}) {
  const mountRef = useRef(null);
  const stateRef = useRef({ dragActive: false, file: null });

  useEffect(() => {
    stateRef.current.dragActive = dragActive;
    stateRef.current.file = file;
  }, [dragActive, file]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const w = mount.clientWidth;
    const h = mount.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 100);
    camera.position.z = 14;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // ─── Particle field ────────────────────────────────────────────────────
    const count = 350;
    const positions = new Float32Array(count * 3);
    const velocities = [];
    const targets = [];

    for (let i = 0; i < count; i++) {
      // Random initial scatter
      positions[i * 3]     = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 5;

      velocities.push({
        x: (Math.random() - 0.5) * 0.02,
        y: (Math.random() - 0.5) * 0.02,
        z: (Math.random() - 0.5) * 0.01,
        phase: Math.random() * Math.PI * 2,
        speed: 0.3 + Math.random() * 0.7,
      });

      // Target: converge into a document/upload icon shape
      const col = Math.floor(i / (count / 10));
      const row = i % Math.floor(count / 10);
      targets.push({
        x: (col - 5) * 1.6,
        y: (row - Math.floor(count / 10) / 2) * 0.7,
        z: 0,
      });
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const mat = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        dragActive: { value: 0.0 },
        hasFile: { value: 0.0 },
      },
      vertexShader: `
        uniform float time;
        uniform float dragActive;
        uniform float hasFile;
        attribute vec3 position;
        varying float vStrength;
        void main() {
          vStrength = 0.5 + 0.5 * sin(time + position.x + position.y);
          float size = 4.0 + dragActive * 3.0 + hasFile * 2.0;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (150.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform float dragActive;
        uniform float hasFile;
        varying float vStrength;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float d = length(uv);
          if (d > 0.5) discard;
          float alpha = (1.0 - smoothstep(0.2, 0.5, d)) * 0.85;
          
          // Color transitions: idle → drag → file
          vec3 idleCol = vec3(0.25, 0.5, 0.35);
          vec3 dragCol = vec3(0.808, 0.969, 0.62);
          vec3 fileCol = vec3(0.133, 0.82, 0.93);
          
          vec3 col = mix(idleCol, dragCol, dragActive);
          col = mix(col, fileCol, hasFile);
          col *= (0.6 + vStrength * 0.5);
          
          gl_FragColor = vec4(col, alpha);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const points = new THREE.Points(geo, mat);
    scene.add(points);

    // ─── Upload icon geometry (arrow + line) ──────────────────────────────
    const arrowGeo = new THREE.ConeGeometry(0.5, 1.2, 8);
    const arrowMat = new THREE.MeshBasicMaterial({
      color: 0xcef79e,
      transparent: true,
      opacity: 0.0,
      wireframe: true,
    });
    const arrow = new THREE.Mesh(arrowGeo, arrowMat);
    arrow.position.y = 0.5;
    scene.add(arrow);

    const stemGeo = new THREE.BoxGeometry(0.15, 1.5, 0.15);
    const stemMat = new THREE.MeshBasicMaterial({ color: 0xcef79e, transparent: true, opacity: 0.0 });
    const stem = new THREE.Mesh(stemGeo, stemMat);
    stem.position.y = -0.8;
    scene.add(stem);

    // ─── Border ring animation ─────────────────────────────────────────────
    const borderRingGeo = new THREE.RingGeometry(5.5, 5.55, 64);
    const borderRingMat = new THREE.MeshBasicMaterial({
      color: 0xcef79e,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
    });
    const borderRing = new THREE.Mesh(borderRingGeo, borderRingMat);
    scene.add(borderRing);

    let mouseX = 0, mouseY = 0;
    const handleMouseMove = (e) => {
      const rect = mount.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      mouseY = -((e.clientY - rect.top) / rect.height - 0.5) * 2;
    };
    mount.addEventListener("mousemove", handleMouseMove);

    const clock = new THREE.Clock();
    let animId;
    let currentDrag = 0;
    let currentFile = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      // Lerp uniform values
      currentDrag += (stateRef.current.dragActive ? 1 : 0 - currentDrag) * 0.08;
      currentFile += (stateRef.current.file ? 1 : 0 - currentFile) * 0.06;
      mat.uniforms.time.value = t;
      mat.uniforms.dragActive.value = currentDrag;
      mat.uniforms.hasFile.value = currentFile;

      // Show arrow icon when file is loaded
      arrowMat.opacity = currentFile * 0.6;
      stemMat.opacity = currentFile * 0.6;

      // Animate particles
      for (let i = 0; i < count; i++) {
        const v = velocities[i];
        const tg = targets[i];
        const converge = currentDrag * 0.5 + currentFile * 0.8;

        // Wander
        positions[i * 3]     += Math.sin(t * v.speed + v.phase) * 0.006 + v.x * (1 - converge);
        positions[i * 3 + 1] += Math.cos(t * v.speed * 0.8 + v.phase) * 0.006 + v.y * (1 - converge);
        positions[i * 3 + 2] += v.z * (1 - converge);

        // Converge to target on drag
        if (converge > 0.01) {
          positions[i * 3]     += (tg.x - positions[i * 3]) * converge * 0.04;
          positions[i * 3 + 1] += (tg.y - positions[i * 3 + 1]) * converge * 0.04;
          positions[i * 3 + 2] += (tg.z - positions[i * 3 + 2]) * converge * 0.04;
        }

        // Boundary wrap
        if (Math.abs(positions[i * 3]) > 10) positions[i * 3] *= -0.9;
        if (Math.abs(positions[i * 3 + 1]) > 5) positions[i * 3 + 1] *= -0.9;
      }
      geo.attributes.position.needsUpdate = true;

      // Rotate slightly with mouse
      points.rotation.y = mouseX * 0.08;
      points.rotation.x = mouseY * 0.04;

      // Pulse border ring
      borderRing.scale.setScalar(1 + Math.sin(t * 1.5) * 0.015);
      borderRing.material.opacity = 0.08 + currentDrag * 0.15 + Math.abs(Math.sin(t)) * 0.04;
      borderRing.rotation.z = t * 0.05;

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      mount.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (mount && renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      style={{ position: "relative", borderRadius: 16, overflow: "hidden", cursor: "pointer" }}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onClick={() => document.getElementById("file-upload-quantum").click()}
    >
      {/* Three.js canvas layer */}
      <div
        ref={mountRef}
        style={{ height: 160, width: "100%", position: "relative" }}
      />

      {/* Glass overlay with text */}
      <div style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
        background: dragActive
          ? "rgba(206,247,158,0.04)"
          : "rgba(0,0,0,0.1)",
        border: dragActive
          ? "1px dashed rgba(206,247,158,0.6)"
          : "1px dashed rgba(206,247,158,0.18)",
        borderRadius: 16,
        transition: "all 0.25s ease",
        pointerEvents: "none",
      }}>
        {/* Icon */}
        <div style={{ fontSize: 28, marginBottom: 4, filter: dragActive ? "brightness(1.5)" : "none" }}>
          {file ? "📄" : dragActive ? "⬇️" : "⬆️"}
        </div>

        <div style={{
          fontFamily: "'Inter Tight', sans-serif",
          fontSize: 14,
          color: file ? "#22d3ee" : dragActive ? "#cef79e" : "rgba(255,255,255,0.7)",
          fontWeight: 500,
          transition: "color 0.25s",
        }}>
          {file ? `${file.name}` : uploadLabel}
        </div>

        <div style={{
          fontFamily: "'Roboto Mono', monospace",
          fontSize: 10,
          color: "rgba(201,203,190,0.4)",
          letterSpacing: "0.5px",
        }}>
          {uploadInfo}
        </div>

        {ocrNotice && (
          <div style={{
            fontFamily: "'Roboto Mono', monospace",
            fontSize: 9,
            color: "rgba(248,113,113,0.6)",
            letterSpacing: "0.3px",
          }}>
            {ocrNotice}
          </div>
        )}
      </div>

      <input
        type="file"
        id="file-upload-quantum"
        style={{ display: "none" }}
        accept=".pdf,.png,.jpg,.jpeg,.txt,.wav,.mp3,.m4a"
        onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
      />
    </div>
  );
}
