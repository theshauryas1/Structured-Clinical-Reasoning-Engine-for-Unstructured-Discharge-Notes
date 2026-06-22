import { useEffect, useRef } from "react";
import * as THREE from "three";
import gsap from "gsap";

/**
 * TimelineRiverGL - A cinematic 3D river-of-time visualization
 * Events float on glowing pads flowing through a temporal stream
 */
export default function TimelineRiverGL({ events = [] }) {
  const mountRef = useRef(null);

  const defaultEvents = [
    { date: "Day 1", label: "Admission", type: "critical", icon: "🏥" },
    { date: "Day 1", label: "Fever + Cough", type: "symptom", icon: "🌡️" },
    { date: "Day 2", label: "Ceftriaxone Started", type: "treatment", icon: "💊" },
    { date: "Day 3", label: "Fever Resolves", type: "improvement", icon: "📉" },
    { date: "Day 4", label: "AFib Onset", type: "critical", icon: "💓" },
    { date: "Day 5", label: "O₂ Improved", type: "improvement", icon: "✅" },
    { date: "Day 6", label: "Discharge", type: "discharge", icon: "🏠" },
  ];

  const eventData = events.length > 0 ? events : defaultEvents;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const w = mount.clientWidth;
    const h = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x010608, 0.035);

    const camera = new THREE.PerspectiveCamera(55, w / h, 0.1, 200);
    camera.position.set(0, 5, 20);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    // ─── River Flow Particles ──────────────────────────────────────────────
    const riverCount = 800;
    const riverPos = new Float32Array(riverCount * 3);
    const riverPhases = [];

    for (let i = 0; i < riverCount; i++) {
      const x = (Math.random() - 0.5) * 24;
      const y = -0.3 + Math.random() * 0.1;
      const z = (Math.random() - 0.5) * 6;
      riverPos[i * 3] = x;
      riverPos[i * 3 + 1] = y;
      riverPos[i * 3 + 2] = z;
      riverPhases.push(Math.random() * Math.PI * 2);
    }

    const riverGeo = new THREE.BufferGeometry();
    riverGeo.setAttribute("position", new THREE.BufferAttribute(riverPos, 3));
    const riverMat = new THREE.PointsMaterial({
      color: 0x22d3ee,
      size: 0.04,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending,
    });
    const riverParticles = new THREE.Points(riverGeo, riverMat);
    scene.add(riverParticles);

    // ─── Timeline River Tube ───────────────────────────────────────────────
    const streamPoints = [];
    for (let i = 0; i <= 40; i++) {
      const x = (i / 40) * 28 - 14;
      const y = Math.sin(i * 0.3) * 0.1;
      streamPoints.push(new THREE.Vector3(x, y, 0));
    }

    const streamCurve = new THREE.CatmullRomCurve3(streamPoints);
    const streamGeo = new THREE.TubeGeometry(streamCurve, 120, 0.05, 8, false);
    const streamMat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } },
      vertexShader: `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
      `,
      fragmentShader: `
        uniform float time;
        varying vec2 vUv;
        void main() {
          float flow = fract(vUv.x * 3.0 - time * 0.8);
          float alpha = smoothstep(0.0, 0.2, flow) * (1.0 - smoothstep(0.6, 1.0, flow));
          gl_FragColor = vec4(0.13, 0.83, 0.93, alpha * 0.7);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    scene.add(new THREE.Mesh(streamGeo, streamMat));

    // ─── Event Pads ────────────────────────────────────────────────────────
    const typeConfig = {
      critical:    { color: 0xff6b6b, emissive: 0xcc2222, glowColor: "#ff6b6b" },
      symptom:     { color: 0xfbbf24, emissive: 0xcc8800, glowColor: "#fbbf24" },
      treatment:   { color: 0xcef79e, emissive: 0x44aa22, glowColor: "#cef79e" },
      improvement: { color: 0x4ade80, emissive: 0x228833, glowColor: "#4ade80" },
      discharge:   { color: 0x818cf8, emissive: 0x4433cc, glowColor: "#818cf8" },
    };

    const padMeshes = [];

    eventData.forEach((evt, i) => {
      const cfg = typeConfig[evt.type] || typeConfig.symptom;
      const x = (i / (eventData.length - 1)) * 22 - 11;

      // Pad
      const padGeo = new THREE.CylinderGeometry(0.8, 0.8, 0.08, 32);
      const padMat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.emissive,
        emissiveIntensity: 0.8,
        metalness: 0.6,
        roughness: 0.2,
        transparent: true,
        opacity: 0.92,
      });
      const pad = new THREE.Mesh(padGeo, padMat);
      pad.position.set(x, 0.1, 0);
      pad.castShadow = true;
      scene.add(pad);

      // Connector pillar
      const pillarGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.5, 8);
      const pillarMat = new THREE.MeshBasicMaterial({ color: cfg.color, transparent: true, opacity: 0.3 });
      const pillar = new THREE.Mesh(pillarGeo, pillarMat);
      pillar.position.set(x, -0.2, 0);
      scene.add(pillar);

      // Point light under each pad
      const light = new THREE.PointLight(cfg.color, 1.5, 4);
      light.position.set(x, -0.5, 0);
      scene.add(light);

      // Glow ring
      const ringGeo = new THREE.RingGeometry(0.85, 1.1, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: cfg.color, transparent: true, opacity: 0.25,
        side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.set(x, 0.15, 0);
      ring.rotation.x = -Math.PI / 2;
      scene.add(ring);

      padMeshes.push({ pad, ring, pillar, light, cfg, phase: i * 0.8 });
    });

    // Ambient
    scene.add(new THREE.AmbientLight(0x112211, 1.5));
    const topLight = new THREE.DirectionalLight(0xffffff, 0.5);
    topLight.position.set(0, 10, 5);
    scene.add(topLight);

    // ─── Camera auto-orbit ─────────────────────────────────────────────────
    let mouseX = 0;
    const handleMouseMove = (e) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    const clock = new THREE.Clock();
    let animId;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      streamMat.uniforms.time.value = t;

      // Animate river particles
      for (let i = 0; i < riverCount; i++) {
        const speed = 0.8 + (i % 5) * 0.3;
        riverGeo.attributes.position.array[i * 3] += speed * 0.01;
        if (riverGeo.attributes.position.array[i * 3] > 12) {
          riverGeo.attributes.position.array[i * 3] = -12;
        }
      }
      riverGeo.attributes.position.needsUpdate = true;

      // Animate pads
      padMeshes.forEach(({ pad, ring, light, phase }, i) => {
        const bob = Math.sin(t * 0.8 + phase) * 0.12;
        pad.position.y = 0.1 + bob;
        ring.position.y = 0.15 + bob;
        ring.scale.setScalar(1 + Math.sin(t * 1.2 + phase) * 0.05);
        ring.material.opacity = 0.15 + Math.abs(Math.sin(t * 0.6 + phase)) * 0.15;
        light.intensity = 1 + Math.sin(t * 1.5 + phase) * 0.5;
      });

      // Gentle camera sweep
      camera.position.x = Math.sin(t * 0.07) * 3 + mouseX * 2;
      camera.lookAt(0, 0, 0);

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
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (mount && renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [events]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", minHeight: 320 }}>
      <div ref={mountRef} style={{ width: "100%", height: "100%", minHeight: 320 }} />

      {/* Event labels overlay */}
      <div style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "space-around",
        padding: "0 24px 16px",
        pointerEvents: "none",
      }}>
        {eventData.map((evt, i) => {
          const typeConfig = {
            critical:    "#ff6b6b",
            symptom:     "#fbbf24",
            treatment:   "#cef79e",
            improvement: "#4ade80",
            discharge:   "#818cf8",
          };
          const col = typeConfig[evt.type] || "#cef79e";
          return (
            <div key={i} style={{
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
            }}>
              <div style={{ fontSize: 14, marginBottom: 2 }}>{evt.icon}</div>
              <div style={{
                fontSize: 9,
                fontFamily: "'Roboto Mono', monospace",
                color: col,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                maxWidth: 60,
                wordBreak: "break-word",
                lineHeight: 1.2,
              }}>
                {evt.label}
              </div>
              <div style={{ fontSize: 8, color: "rgba(201,203,190,0.5)", fontFamily: "monospace" }}>
                {evt.date}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
