import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import gsap from "gsap";

/**
 * MoleculeOrbit - An orbiting molecular structure of diagnostics data
 * nodes orbiting a central glowing core
 */
export default function MoleculeOrbit({ diagnoses = [], active = false }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const w = mount.clientWidth;
    const h = mount.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 200);
    camera.position.set(0, 0, 22);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    mount.appendChild(renderer.domElement);

    // ─── Central Core ──────────────────────────────────────────────────────
    const coreGeo = new THREE.IcosahedronGeometry(1.8, 4);
    const coreMat = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color1: { value: new THREE.Color(0xcef79e) },
        color2: { value: new THREE.Color(0x22d3ee) },
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vPos;
        uniform float time;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vPos = position;
          vec3 pos = position;
          // Plasma surface deformation
          float deform = sin(pos.x * 3.0 + time * 2.0) * 0.08
                       + cos(pos.y * 4.0 + time * 1.5) * 0.06
                       + sin(pos.z * 2.5 + time * 2.5) * 0.07;
          pos += normal * deform;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform vec3 color1;
        uniform vec3 color2;
        varying vec3 vNormal;
        varying vec3 vPos;
        void main() {
          float fresnel = pow(1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0))), 2.5);
          float pulse = 0.5 + 0.5 * sin(time * 2.0);
          vec3 col = mix(color1, color2, fresnel);
          col = mix(col, vec3(1.0), fresnel * 0.4 * pulse);
          float alpha = 0.4 + fresnel * 0.6;
          gl_FragColor = vec4(col, alpha);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);

    // Core glow sphere
    const glowGeo = new THREE.SphereGeometry(2.4, 32, 32);
    const glowMat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 }, color: { value: new THREE.Color(0xcef79e) } },
      vertexShader: `varying vec3 vNormal; void main() { vNormal = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `
        uniform vec3 color;
        uniform float time;
        varying vec3 vNormal;
        void main() {
          float f = pow(1.0 - abs(dot(vNormal, vec3(0.0,0.0,1.0))), 3.0);
          float pulse = 0.7 + 0.3 * sin(time * 1.8);
          gl_FragColor = vec4(color, f * 0.35 * pulse);
        }
      `,
      transparent: true,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const glow = new THREE.Mesh(glowGeo, glowMat);
    scene.add(glow);

    // ─── Orbital Rings ─────────────────────────────────────────────────────
    const orbitalSpeeds = [0.35, -0.22, 0.18];
    const orbitalTilts = [0, Math.PI / 4, Math.PI / 2.5];
    const orbitalRadii = [5, 6.5, 8];
    const orbitalGroups = [];

    orbitalTilts.forEach((tilt, i) => {
      const ringGeo = new THREE.RingGeometry(orbitalRadii[i] - 0.015, orbitalRadii[i] + 0.015, 80);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xcef79e, transparent: true, opacity: 0.08, side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = tilt;
      scene.add(ring);

      const group = new THREE.Group();
      group.rotation.x = tilt;
      scene.add(group);
      orbitalGroups.push({ group, speed: orbitalSpeeds[i], orbitRadius: orbitalRadii[i] });
    });

    // ─── Diagnostic Spheres ────────────────────────────────────────────────
    const diagnoseData = diagnoses.length > 0 ? diagnoses : [
      { label: "CAP", confidence: 0.88 },
      { label: "AFib", confidence: 0.72 },
      { label: "PE", confidence: 0.45 },
      { label: "CHF", confidence: 0.38 },
      { label: "SIRS", confidence: 0.31 },
    ];

    const nodeObjects = [];
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    diagnoseData.forEach((diag, i) => {
      const orbGroup = orbitalGroups[i % orbitalGroups.length];
      const radius = orbGroup.orbitRadius;
      const angle = (i / diagnoseData.length) * Math.PI * 2;

      const size = 0.25 + diag.confidence * 0.55;
      const geo = new THREE.IcosahedronGeometry(size, 1);

      const conf = diag.confidence;
      let nodeColor = new THREE.Color();
      if (conf > 0.7) nodeColor.set(0xcef79e);
      else if (conf > 0.5) nodeColor.set(0xfbbf24);
      else nodeColor.set(0xf87171);

      const mat = new THREE.MeshStandardMaterial({
        color: nodeColor,
        emissive: nodeColor,
        emissiveIntensity: 0.6,
        metalness: 0.8,
        roughness: 0.2,
        transparent: true,
        opacity: 0.9,
      });

      const sphere = new THREE.Mesh(geo, mat);
      sphere.userData = { diag, originalColor: nodeColor.clone(), orbGroup, angle };
      sphere.position.x = Math.cos(angle) * radius;
      sphere.position.z = Math.sin(angle) * radius;

      orbGroup.group.add(sphere);
      nodeObjects.push(sphere);

      // Connection line to core
      const linePoints = [new THREE.Vector3(0, 0, 0), sphere.position.clone()];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(linePoints);
      const lineMat = new THREE.LineBasicMaterial({ color: nodeColor, transparent: true, opacity: 0.12, blending: THREE.AdditiveBlending });
      // Don't add line connections since they don't update easily
    });

    // Lights
    const ambientLight = new THREE.AmbientLight(0x112211, 2);
    scene.add(ambientLight);
    const pointLight = new THREE.PointLight(0xcef79e, 3, 30);
    scene.add(pointLight);
    const pointLight2 = new THREE.PointLight(0x22d3ee, 2, 20);
    pointLight2.position.set(5, 5, 5);
    scene.add(pointLight2);

    sceneRef.current = { scene, camera, renderer, core, glow, coreMat, glowMat, orbitalGroups, nodeObjects, raycaster, mouse };

    // Mouse interaction
    const handleMouseMove = (e) => {
      const rect = mount.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    };
    mount.addEventListener("mousemove", handleMouseMove);

    // Animation
    const clock = new THREE.Clock();
    let animId;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      coreMat.uniforms.time.value = t;
      glowMat.uniforms.time.value = t;

      core.rotation.y = t * 0.3;
      core.rotation.x = t * 0.15;

      orbitalGroups.forEach(({ group, speed }) => {
        group.rotation.y += speed * 0.008;
      });

      // Raycasting for hover
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(nodeObjects);

      nodeObjects.forEach((node) => {
        const isHit = hits.length > 0 && hits[0].object === node;
        const targetScale = isHit ? 1.5 : 1.0;
        node.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
        node.material.emissiveIntensity = isHit ? 1.5 : 0.6;
        node.rotation.y += 0.02;
      });

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      const nw = mount.clientWidth;
      const nh = mount.clientHeight;
      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
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
  }, [diagnoses]);

  return (
    <div
      ref={mountRef}
      style={{
        width: "100%",
        height: "100%",
        minHeight: 340,
        cursor: "crosshair",
      }}
    />
  );
}
