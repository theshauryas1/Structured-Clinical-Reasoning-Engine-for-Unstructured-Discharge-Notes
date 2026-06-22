import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * DataVortex - A spinning torus/vortex visualization for contradiction/data flow
 * showing conflict data as distorted rings with color-coded severity
 */
export default function DataVortex({ contradictions = [] }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const w = mount.clientWidth;
    const h = mount.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 100);
    camera.position.set(0, 4, 16);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    // ─── Outer Torus ───────────────────────────────────────────────────────
    const torusMat = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        hasConflict: { value: contradictions.length > 0 ? 1.0 : 0.0 },
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vPos;
        uniform float time;
        void main() {
          vUv = uv;
          vPos = position;
          vec3 pos = position;
          // Wobble
          pos += normal * (sin(uv.x * 12.0 + time * 3.0) * 0.05 + cos(uv.y * 8.0 + time * 2.0) * 0.04);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform float hasConflict;
        varying vec2 vUv;
        varying vec3 vPos;
        
        void main() {
          // Racing stripe pattern around torus
          float stripe = fract(vUv.x * 8.0 - time * 0.5);
          float isStripe = step(0.8, stripe);
          
          // Conflict fire colors
          vec3 normalCol = vec3(0.0, 0.6, 0.4);
          vec3 conflictCol = vec3(1.0, 0.2, 0.05);
          vec3 baseCol = mix(normalCol, conflictCol, hasConflict * 0.7);
          
          vec3 stripeCol = mix(baseCol, vec3(1.0), 0.5);
          vec3 col = mix(baseCol, stripeCol, isStripe * 0.6);
          
          float alpha = 0.3 + isStripe * 0.3;
          gl_FragColor = vec4(col, alpha);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const torusGeo = new THREE.TorusGeometry(4, 0.4, 32, 120);
    const torus = new THREE.Mesh(torusGeo, torusMat);
    scene.add(torus);

    // Inner torus
    const innerTorusMat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 } },
      vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `
        uniform float time;
        varying vec2 vUv;
        void main() {
          float flow = fract(vUv.x * 5.0 + time * 1.2);
          float a = smoothstep(0.0, 0.3, flow) * (1.0 - smoothstep(0.5, 1.0, flow));
          gl_FragColor = vec4(0.13, 0.83, 0.93, a * 0.5);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const innerTorus = new THREE.Mesh(new THREE.TorusGeometry(2.5, 0.12, 16, 80), innerTorusMat);
    innerTorus.rotation.x = Math.PI / 4;
    scene.add(innerTorus);

    // ─── Conflict Arcs ─────────────────────────────────────────────────────
    const conflictCount = Math.max(contradictions.length, 0);
    const conflictArcs = [];

    for (let i = 0; i < Math.min(conflictCount, 6); i++) {
      const arcGeo = new THREE.TorusGeometry(4 + i * 0.3, 0.06, 8, 60, Math.PI * 0.6);
      const arcMat = new THREE.MeshBasicMaterial({
        color: 0xff4444, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending,
      });
      const arc = new THREE.Mesh(arcGeo, arcMat);
      arc.rotation.z = (i / conflictCount) * Math.PI * 2;
      arc.userData = { speed: 0.5 + Math.random() * 1.0, dir: i % 2 === 0 ? 1 : -1 };
      scene.add(arc);
      conflictArcs.push(arc);
    }

    // ─── Central Sphere ────────────────────────────────────────────────────
    const coreGeo = new THREE.SphereGeometry(1.2, 32, 32);
    const coreMat = new THREE.ShaderMaterial({
      uniforms: { time: { value: 0 }, hasConflict: { value: conflictCount > 0 ? 1.0 : 0.0 } },
      vertexShader: `
        uniform float time;
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform float hasConflict;
        varying vec3 vNormal;
        void main() {
          float f = pow(1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0))), 2.5);
          float pulse = 0.5 + 0.5 * sin(time * 3.0);
          vec3 calmCol = vec3(0.2, 1.0, 0.7);
          vec3 alertCol = vec3(1.0, 0.2, 0.1);
          vec3 col = mix(calmCol, alertCol, hasConflict);
          col = mix(col, vec3(1.0), f * 0.5 * pulse);
          gl_FragColor = vec4(col, 0.5 + f * 0.5);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);

    // ─── Particle Spray ────────────────────────────────────────────────────
    const sprayCount = 200;
    const sprayPos = new Float32Array(sprayCount * 3);
    const sprayPhases = [];

    for (let i = 0; i < sprayCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const r = 3 + Math.random() * 3;
      sprayPos[i * 3] = Math.cos(angle) * r;
      sprayPos[i * 3 + 1] = (Math.random() - 0.5) * 2;
      sprayPos[i * 3 + 2] = Math.sin(angle) * r;
      sprayPhases.push(Math.random() * Math.PI * 2);
    }

    const sprayGeo = new THREE.BufferGeometry();
    sprayGeo.setAttribute("position", new THREE.BufferAttribute(sprayPos, 3));
    const sprayMat = new THREE.PointsMaterial({
      color: conflictCount > 0 ? 0xff6666 : 0x4ade80,
      size: 0.08,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
    });
    const spray = new THREE.Points(sprayGeo, sprayMat);
    scene.add(spray);

    scene.add(new THREE.AmbientLight(0x111111, 3));

    let mouseX = 0, mouseY = 0;
    const handleMouseMove = (e) => {
      const rect = mount.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    };
    mount.addEventListener("mousemove", handleMouseMove);

    const clock = new THREE.Clock();
    let animId;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      torusMat.uniforms.time.value = t;
      innerTorusMat.uniforms.time.value = t;
      coreMat.uniforms.time.value = t;

      torus.rotation.y = t * 0.2;
      torus.rotation.x = Math.sin(t * 0.15) * 0.4;

      innerTorus.rotation.z = t * 0.35;
      innerTorus.rotation.y = t * 0.15;

      conflictArcs.forEach((arc) => {
        arc.rotation.z += arc.userData.speed * 0.012 * arc.userData.dir;
        arc.rotation.x = Math.sin(t * 0.4) * 0.3;
      });

      // Particle orbit
      for (let i = 0; i < sprayCount; i++) {
        const phase = sprayPhases[i] + t * 0.3;
        const r = 3.5 + Math.sin(phase * 2) * 0.5;
        sprayGeo.attributes.position.array[i * 3] = Math.cos(phase) * r;
        sprayGeo.attributes.position.array[i * 3 + 2] = Math.sin(phase) * r;
        sprayGeo.attributes.position.array[i * 3 + 1] = Math.sin(t + sprayPhases[i]) * 1.5;
      }
      sprayGeo.attributes.position.needsUpdate = true;

      // Mouse tilt
      torus.rotation.x += (mouseY * 0.3 - torus.rotation.x) * 0.05;

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
  }, [contradictions]);

  return <div ref={mountRef} style={{ width: "100%", height: "100%", minHeight: 260 }} />;
}
