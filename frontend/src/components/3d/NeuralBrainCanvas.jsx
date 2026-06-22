import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function NeuralBrainCanvas() {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, mount.clientWidth / mount.clientHeight, 0.1, 1000);
    camera.position.set(0, 0, 28);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    mount.appendChild(renderer.domElement);

    // ─── Neural Node Particles ───────────────────────────────────────────────
    const nodeCount = 280;
    const nodePositions = new Float32Array(nodeCount * 3);
    const nodeSizes = new Float32Array(nodeCount);
    const nodeColors = new Float32Array(nodeCount * 3);

    const palette = [
      new THREE.Color(0xcef79e), // bioluminescent lime
      new THREE.Color(0x4ade80), // green
      new THREE.Color(0x22d3ee), // cyan
      new THREE.Color(0x818cf8), // indigo
      new THREE.Color(0xfbbf24), // amber (rare)
    ];

    const nodeData = [];
    for (let i = 0; i < nodeCount; i++) {
      // Spherical distribution biased toward a brain shape
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 6 + Math.random() * 6;

      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta) * 0.75; // Flatten slightly
      const z = r * Math.cos(phi);

      nodePositions[i * 3] = x;
      nodePositions[i * 3 + 1] = y;
      nodePositions[i * 3 + 2] = z;

      nodeSizes[i] = 0.08 + Math.random() * 0.18;

      const c = palette[Math.floor(Math.random() * palette.length)];
      nodeColors[i * 3] = c.r;
      nodeColors[i * 3 + 1] = c.g;
      nodeColors[i * 3 + 2] = c.b;

      nodeData.push({
        ox: x, oy: y, oz: z,
        speed: 0.2 + Math.random() * 0.4,
        phase: Math.random() * Math.PI * 2,
        amplitude: 0.15 + Math.random() * 0.3,
      });
    }

    const nodesGeo = new THREE.BufferGeometry();
    nodesGeo.setAttribute("position", new THREE.BufferAttribute(nodePositions, 3));
    nodesGeo.setAttribute("color", new THREE.BufferAttribute(nodeColors, 3));
    nodesGeo.setAttribute("size", new THREE.BufferAttribute(nodeSizes, 1));

    const nodesMat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float time;
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (280.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        void main() {
          vec2 uv = gl_PointCoord - vec2(0.5);
          float dist = length(uv);
          if (dist > 0.5) discard;
          float alpha = 1.0 - smoothstep(0.2, 0.5, dist);
          // Glow core
          float glow = 1.0 - smoothstep(0.0, 0.25, dist);
          vec3 finalColor = mix(vColor, vec3(1.0), glow * 0.5);
          gl_FragColor = vec4(finalColor, alpha * 0.9);
        }
      `,
      transparent: true,
      vertexColors: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    const nodesMesh = new THREE.Points(nodesGeo, nodesMat);
    scene.add(nodesMesh);

    // ─── Synapse Connection Lines ─────────────────────────────────────────────
    const linePositions = [];
    const lineColors = [];
    const connections = [];
    const connectionCount = 180;

    for (let i = 0; i < connectionCount; i++) {
      const a = Math.floor(Math.random() * nodeCount);
      const b = Math.floor(Math.random() * nodeCount);
      const ax = nodePositions[a * 3], ay = nodePositions[a * 3 + 1], az = nodePositions[a * 3 + 2];
      const bx = nodePositions[b * 3], by = nodePositions[b * 3 + 1], bz = nodePositions[b * 3 + 2];
      const dist = Math.sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2);

      if (dist < 9) {
        linePositions.push(ax, ay, az, bx, by, bz);
        const alpha = (1 - dist / 9) * 0.35;
        lineColors.push(0.808, 0.969, 0.62, alpha, 0.808, 0.969, 0.62, alpha);
        connections.push({ a, b, alpha });
      }
    }

    const linesGeo = new THREE.BufferGeometry();
    const linesPosArray = new Float32Array(linePositions);
    linesGeo.setAttribute("position", new THREE.BufferAttribute(linesPosArray, 3));
    const linesMat = new THREE.LineBasicMaterial({ color: 0xcef79e, transparent: true, opacity: 0.12, blending: THREE.AdditiveBlending });
    const linesMesh = new THREE.LineSegments(linesGeo, linesMat);
    scene.add(linesMesh);

    // ─── Pulse Rings ──────────────────────────────────────────────────────────
    const rings = [];
    for (let i = 0; i < 3; i++) {
      const rGeo = new THREE.RingGeometry(7 + i * 2.5, 7.05 + i * 2.5, 64);
      const rMat = new THREE.MeshBasicMaterial({
        color: 0xcef79e, side: THREE.DoubleSide, transparent: true, opacity: 0.06,
        blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(rGeo, rMat);
      ring.rotation.x = Math.PI / 2;
      ring.userData = { phase: (i / 3) * Math.PI * 2 };
      scene.add(ring);
      rings.push(ring);
    }

    // ─── Floating DNA Helix ───────────────────────────────────────────────────
    const helixPoints1 = [], helixPoints2 = [];
    for (let i = 0; i < 60; i++) {
      const t = (i / 60) * Math.PI * 6;
      const x = Math.cos(t) * 2.5;
      const y = i * 0.3 - 9;
      const z = Math.sin(t) * 2.5;
      helixPoints1.push(new THREE.Vector3(x - 15, y, z));
      helixPoints2.push(new THREE.Vector3(-x - 15, y, z));
    }

    const helixCurve1 = new THREE.CatmullRomCurve3(helixPoints1);
    const helixCurve2 = new THREE.CatmullRomCurve3(helixPoints2);

    const helixGeo1 = new THREE.TubeGeometry(helixCurve1, 100, 0.04, 8, false);
    const helixGeo2 = new THREE.TubeGeometry(helixCurve2, 100, 0.04, 8, false);
    const helixMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.4, blending: THREE.AdditiveBlending });

    scene.add(new THREE.Mesh(helixGeo1, helixMat));
    scene.add(new THREE.Mesh(helixGeo2, helixMat));

    // Helix rungs
    for (let i = 0; i < 60; i += 4) {
      const t = (i / 60) * Math.PI * 6;
      const p1 = helixPoints1[i];
      const p2 = helixPoints2[i];
      if (!p1 || !p2) continue;
      const rungGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
      const rungMat = new THREE.LineBasicMaterial({ color: 0x818cf8, transparent: true, opacity: 0.25, blending: THREE.AdditiveBlending });
      scene.add(new THREE.Line(rungGeo, rungMat));
    }

    // ─── Mouse interaction ────────────────────────────────────────────────────
    let mouseX = 0, mouseY = 0;
    const handleMouseMove = (e) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    // ─── Animation ────────────────────────────────────────────────────────────
    const clock = new THREE.Clock();
    let animId;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      nodesMat.uniforms.time.value = elapsed;

      // Animate node positions (pulsing breathe)
      for (let i = 0; i < nodeCount; i++) {
        const nd = nodeData[i];
        const wave = Math.sin(elapsed * nd.speed + nd.phase) * nd.amplitude;
        nodesGeo.attributes.position.array[i * 3] = nd.ox + wave;
        nodesGeo.attributes.position.array[i * 3 + 1] = nd.oy + Math.cos(elapsed * nd.speed * 0.7 + nd.phase) * nd.amplitude;
        nodesGeo.attributes.position.array[i * 3 + 2] = nd.oz + wave * 0.5;
      }
      nodesGeo.attributes.position.needsUpdate = true;

      // Pulse rings
      rings.forEach((ring, i) => {
        const phase = elapsed * 0.4 + ring.userData.phase;
        ring.scale.setScalar(1 + Math.sin(phase) * 0.06);
        ring.material.opacity = 0.04 + Math.abs(Math.sin(phase)) * 0.05;
      });

      // Gentle rotation
      nodesMesh.rotation.y = elapsed * 0.04 + mouseX * 0.15;
      nodesMesh.rotation.x = Math.sin(elapsed * 0.025) * 0.12 + mouseY * 0.08;
      linesMesh.rotation.y = nodesMesh.rotation.y;
      linesMesh.rotation.x = nodesMesh.rotation.x;

      renderer.render(scene, camera);
    };
    animate();

    // ─── Resize ───────────────────────────────────────────────────────────────
    const handleResize = () => {
      if (!mount) return;
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
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        background: "radial-gradient(ellipse at 30% 40%, #0a1a0f 0%, #060e12 50%, #000000 100%)",
      }}
    />
  );
}
