"use client";
import React, { useMemo } from 'react';
import * as THREE from 'three';

export type AirframeDisplayMode = "translucent" | "ghost" | "wireframe" | "hidden";

interface TranslucentMaleUAVAirframeProps {
  mode?: AirframeDisplayMode;
  opacity?: number;
}

/**
 * Procedural Lofting Functions to generate a continuous, sleek 3D aerodynamic aircraft hull.
 * Replaces disconnected boxy shapes and wireframe meshes with a complete, smooth 3D model
 * of India's DRDO TAPAS-BH-201 (Rustom-II) MALE UAV.
 */

// 1. Continuous Fuselage Geometry with SATCOM Radome & Engine Bay Lofting
function createFuselageGeometry(): THREE.BufferGeometry {
  const STATIONS = [
    // Nose spinner interface (meets engine propeller at x = 1.25)
    { x: 1.25, cy: 0.05, ryTop: 0.22, ryBot: 0.22, rz: 0.22 },
    // Forward Cowling
    { x: 1.05, cy: 0.06, ryTop: 0.35, ryBot: 0.30, rz: 0.35 },
    // Nose section & Forward gear bay
    { x: 0.85, cy: 0.08, ryTop: 0.50, ryBot: 0.38, rz: 0.50 },
    // Forward SATCOM Radome rise
    { x: 0.65, cy: 0.12, ryTop: 0.66, ryBot: 0.44, rz: 0.64 },
    // DRDO TAPAS SATCOM Radome Peak
    { x: 0.40, cy: 0.15, ryTop: 0.74, ryBot: 0.48, rz: 0.82 },
    // Radome-to-Engine Bay transition
    { x: 0.15, cy: 0.10, ryTop: 0.68, ryBot: 0.52, rz: 1.18 },
    // Engine Bay Center (Encapsulating Boxer-4 Cylinders 1-4)
    { x: -0.15, cy: 0.06, ryTop: 0.64, ryBot: 0.54, rz: 1.28 },
    // Engine Bay Aft (Encapsulating Turbocharger, Exhaust, and Induction)
    { x: -0.55, cy: 0.05, ryTop: 0.60, ryBot: 0.52, rz: 1.24 },
    // Engine Bay Exit & Wing Root Junction
    { x: -0.95, cy: 0.06, ryTop: 0.54, ryBot: 0.48, rz: 1.08 },
    // Mid Fuselage Transition
    { x: -1.40, cy: 0.08, ryTop: 0.46, ryBot: 0.40, rz: 0.75 },
    // Avionics & Mission Systems Bay
    { x: -1.95, cy: 0.10, ryTop: 0.40, ryBot: 0.34, rz: 0.52 },
    // Tail Boom Root
    { x: -2.55, cy: 0.12, ryTop: 0.32, ryBot: 0.28, rz: 0.36 },
    // Tail Boom Mid-Section
    { x: -3.25, cy: 0.15, ryTop: 0.25, ryBot: 0.22, rz: 0.26 },
    // Tail Boom Aft (Approaching Vertical Fin)
    { x: -3.95, cy: 0.18, ryTop: 0.20, ryBot: 0.18, rz: 0.20 },
    // Aft Empennage Tail Cone
    { x: -4.60, cy: 0.22, ryTop: 0.14, ryBot: 0.13, rz: 0.14 },
    // Tail Stinger Tip
    { x: -4.75, cy: 0.23, ryTop: 0.04, ryBot: 0.04, rz: 0.04 },
  ];

  const M = 28; // Radial segments around each cross section
  const positions: number[] = [];
  const indices: number[] = [];

  STATIONS.forEach((st) => {
    for (let j = 0; j < M; j++) {
      const theta = (j * 2 * Math.PI) / M;
      const sinT = Math.sin(theta);
      const cosT = Math.cos(theta);
      const ry = sinT >= 0 ? st.ryTop : st.ryBot;
      const x = st.x;
      const y = st.cy + ry * sinT;
      const z = st.rz * cosT;
      positions.push(x, y, z);
    }
  });

  for (let i = 0; i < STATIONS.length - 1; i++) {
    for (let j = 0; j < M; j++) {
      const jNext = (j + 1) % M;
      const v00 = i * M + j;
      const v10 = (i + 1) * M + j;
      const v11 = (i + 1) * M + jNext;
      const v01 = i * M + jNext;
      // Outward-facing triangles
      indices.push(v00, v01, v11);
      indices.push(v00, v11, v10);
    }
  }

  // Front Cap (Spinner Collar)
  const frontCenterIdx = positions.length / 3;
  positions.push(1.26, 0.05, 0.0);
  for (let j = 0; j < M; j++) {
    const jNext = (j + 1) % M;
    indices.push(frontCenterIdx, j, jNext);
  }

  // Aft Cap (Tail Stinger)
  const aftCenterIdx = positions.length / 3;
  positions.push(-4.78, 0.23, 0.0);
  const lastStationOffset = (STATIONS.length - 1) * M;
  for (let j = 0; j < M; j++) {
    const jNext = (j + 1) % M;
    indices.push(aftCenterIdx, lastStationOffset + jNext, lastStationOffset + j);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

// 2. Continuous Aerodynamic Wing Geometry with Airfoil Section & Upturned Winglets
function createWingGeometry(isRight: boolean): THREE.BufferGeometry {
  const WING_STATIONS = [
    { spanZ: 0.55, chord: 1.15, xOffset: -0.28, thick: 0.16, yOffset: 0.58 },
    { spanZ: 1.20, chord: 1.00, xOffset: -0.25, thick: 0.14, yOffset: 0.59 },
    { spanZ: 2.50, chord: 0.82, xOffset: -0.21, thick: 0.11, yOffset: 0.61 },
    { spanZ: 3.80, chord: 0.65, xOffset: -0.17, thick: 0.08, yOffset: 0.63 },
    { spanZ: 4.65, chord: 0.48, xOffset: -0.14, thick: 0.05, yOffset: 0.66 },
    // Winglet curvature upward
    { spanZ: 4.78, chord: 0.44, xOffset: -0.14, thick: 0.04, yOffset: 0.74 },
    { spanZ: 4.85, chord: 0.38, xOffset: -0.13, thick: 0.035, yOffset: 0.94 },
    { spanZ: 4.88, chord: 0.30, xOffset: -0.12, thick: 0.03, yOffset: 1.16 },
  ];

  const numAirfoilSteps = 12;
  const profile: { u: number; yNorm: number }[] = [];
  // Upper surface: trailing edge -> leading edge
  for (let i = 0; i <= numAirfoilSteps; i++) {
    const t = i / numAirfoilSteps;
    const u = 1 - Math.cos((t * Math.PI) / 2);
    const yNorm = 5 * (0.2969 * Math.sqrt(Math.max(0, u)) - 0.1260 * u - 0.3516 * u * u + 0.2843 * Math.pow(u, 3) - 0.1015 * Math.pow(u, 4));
    profile.push({ u, yNorm });
  }
  // Lower surface: leading edge -> trailing edge
  for (let i = 1; i <= numAirfoilSteps; i++) {
    const t = 1 - i / numAirfoilSteps;
    const u = 1 - Math.cos((t * Math.PI) / 2);
    const yNorm = -5 * (0.2969 * Math.sqrt(Math.max(0, u)) - 0.1260 * u - 0.3516 * u * u + 0.2843 * Math.pow(u, 3) - 0.1015 * Math.pow(u, 4));
    profile.push({ u, yNorm });
  }

  const P = profile.length;
  const positions: number[] = [];
  const indices: number[] = [];

  WING_STATIONS.forEach((st) => {
    for (let j = 0; j < P; j++) {
      const p = profile[j];
      const x = st.xOffset + p.u * st.chord;
      const y = st.yOffset + p.yNorm * st.thick;
      const z = isRight ? st.spanZ : -st.spanZ;
      positions.push(x, y, z);
    }
  });

  for (let i = 0; i < WING_STATIONS.length - 1; i++) {
    for (let j = 0; j < P; j++) {
      const jNext = (j + 1) % P;
      const v00 = i * P + j;
      const v10 = (i + 1) * P + j;
      const v11 = (i + 1) * P + jNext;
      const v01 = i * P + jNext;
      if (isRight) {
        indices.push(v00, v01, v11);
        indices.push(v00, v11, v10);
      } else {
        indices.push(v00, v11, v01);
        indices.push(v00, v10, v11);
      }
    }
  }

  // Wingtip / Winglet cap
  const lastOffset = (WING_STATIONS.length - 1) * P;
  const tipCenterIdx = positions.length / 3;
  const lastSt = WING_STATIONS[WING_STATIONS.length - 1];
  positions.push(lastSt.xOffset + 0.5 * lastSt.chord, lastSt.yOffset, isRight ? lastSt.spanZ : -lastSt.spanZ);
  for (let j = 0; j < P; j++) {
    const jNext = (j + 1) % P;
    if (isRight) {
      indices.push(tipCenterIdx, lastOffset + jNext, lastOffset + j);
    } else {
      indices.push(tipCenterIdx, lastOffset + j, lastOffset + jNext);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

// 3. Swept Vertical Stabilizer Geometry
function createVerticalFinGeometry(): THREE.BufferGeometry {
  const FIN_STATIONS = [
    { y: 0.30, chord: 1.15, xLE: -3.70, thick: 0.12 },
    { y: 0.70, chord: 0.98, xLE: -3.85, thick: 0.10 },
    { y: 1.15, chord: 0.82, xLE: -4.00, thick: 0.08 },
    { y: 1.55, chord: 0.68, xLE: -4.15, thick: 0.065 }
  ];

  const numSteps = 10;
  const profile: { u: number; zNorm: number }[] = [];
  for (let i = 0; i <= numSteps; i++) {
    const t = i / numSteps;
    const u = 1 - Math.cos((t * Math.PI) / 2);
    const zNorm = 5 * (0.2969 * Math.sqrt(Math.max(0, u)) - 0.1260 * u - 0.3516 * u * u + 0.2843 * Math.pow(u, 3) - 0.1015 * Math.pow(u, 4));
    profile.push({ u, zNorm });
  }
  for (let i = 1; i <= numSteps; i++) {
    const t = 1 - i / numSteps;
    const u = 1 - Math.cos((t * Math.PI) / 2);
    const zNorm = -5 * (0.2969 * Math.sqrt(Math.max(0, u)) - 0.1260 * u - 0.3516 * u * u + 0.2843 * Math.pow(u, 3) - 0.1015 * Math.pow(u, 4));
    profile.push({ u, zNorm });
  }

  const P = profile.length;
  const positions: number[] = [];
  const indices: number[] = [];

  FIN_STATIONS.forEach((st) => {
    for (let j = 0; j < P; j++) {
      const p = profile[j];
      const x = st.xLE - p.u * st.chord;
      const y = st.y;
      const z = p.zNorm * st.thick;
      positions.push(x, y, z);
    }
  });

  for (let i = 0; i < FIN_STATIONS.length - 1; i++) {
    for (let j = 0; j < P; j++) {
      const jNext = (j + 1) % P;
      const v00 = i * P + j;
      const v10 = (i + 1) * P + j;
      const v11 = (i + 1) * P + jNext;
      const v01 = i * P + jNext;
      indices.push(v00, v01, v11);
      indices.push(v00, v11, v10);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

// 4. High-Mounted T-Tail Horizontal Stabilizer Geometry
function createHorizontalStabilizerGeometry(): THREE.BufferGeometry {
  const STABILIZER_STATIONS = [
    { z: -1.35, chord: 0.35, xLE: -4.38, thick: 0.035 },
    { z: -0.70, chord: 0.46, xLE: -4.34, thick: 0.045 },
    { z: 0.0, chord: 0.58, xLE: -4.30, thick: 0.055 },
    { z: 0.70, chord: 0.46, xLE: -4.34, thick: 0.045 },
    { z: 1.35, chord: 0.35, xLE: -4.38, thick: 0.035 }
  ];

  const numSteps = 10;
  const profile: { u: number; yNorm: number }[] = [];
  for (let i = 0; i <= numSteps; i++) {
    const t = i / numSteps;
    const u = 1 - Math.cos((t * Math.PI) / 2);
    const yNorm = 5 * (0.2969 * Math.sqrt(Math.max(0, u)) - 0.1260 * u - 0.3516 * u * u + 0.2843 * Math.pow(u, 3) - 0.1015 * Math.pow(u, 4));
    profile.push({ u, yNorm });
  }
  for (let i = 1; i <= numSteps; i++) {
    const t = 1 - i / numSteps;
    const u = 1 - Math.cos((t * Math.PI) / 2);
    const yNorm = -5 * (0.2969 * Math.sqrt(Math.max(0, u)) - 0.1260 * u - 0.3516 * u * u + 0.2843 * Math.pow(u, 3) - 0.1015 * Math.pow(u, 4));
    profile.push({ u, yNorm });
  }

  const P = profile.length;
  const positions: number[] = [];
  const indices: number[] = [];

  STABILIZER_STATIONS.forEach((st) => {
    for (let j = 0; j < P; j++) {
      const p = profile[j];
      const x = st.xLE - p.u * st.chord;
      const y = 1.56 + p.yNorm * st.thick;
      const z = st.z;
      positions.push(x, y, z);
    }
  });

  for (let i = 0; i < STABILIZER_STATIONS.length - 1; i++) {
    for (let j = 0; j < P; j++) {
      const jNext = (j + 1) % P;
      const v00 = i * P + j;
      const v10 = (i + 1) * P + j;
      const v11 = (i + 1) * P + jNext;
      const v01 = i * P + jNext;
      indices.push(v00, v01, v11);
      indices.push(v00, v11, v10);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Complete, True 3D Model of India's DRDO TAPAS-BH-201 (Rustom-II) MALE UAV.
 * Rendered with a solid, sleek, translucent aerospace composite material
 * (without distracting wireframe cage lines) so the internal AeroPiston-4X
 * engine is 100% visible operating within the airframe.
 */
export default function TranslucentMaleUAVAirframe({
  mode = "translucent",
  opacity = 0.28,
}: TranslucentMaleUAVAirframeProps) {
  if (mode === "hidden") return null;

  const isWireframe = mode === "wireframe";
  const effectiveOpacity = mode === "ghost" ? 0.09 : opacity;

  // Memoize all procedural geometries
  const fuselageGeo = useMemo(() => createFuselageGeometry(), []);
  const rightWingGeo = useMemo(() => createWingGeometry(true), []);
  const leftWingGeo = useMemo(() => createWingGeometry(false), []);
  const verticalFinGeo = useMemo(() => createVerticalFinGeometry(), []);
  const hStabGeo = useMemo(() => createHorizontalStabilizerGeometry(), []);

  // Primary Translucent Aerospace Composite Material
  // Glass/stealth composite PBR shader: highlights show the 3D curves while keeping the engine fully visible inside.
  const compositeMaterial = useMemo(() => {
    return new THREE.MeshPhysicalMaterial({
      color: 0x16365c, // Technical deep cyan/navy composite hue
      emissive: 0x091829, // Subtle inner ambient luminescence
      emissiveIntensity: 0.15,
      roughness: 0.14, // Specular gloss catching 3D aerodynamic highlights
      metalness: 0.15,
      transmission: 0.68, // Optical transmission through the composite shell
      ior: 1.34,
      transparent: true,
      opacity: isWireframe ? 0.9 : effectiveOpacity,
      depthWrite: false, // Critical: inner engine components are never culled or occluded!
      side: THREE.DoubleSide,
      wireframe: isWireframe,
    });
  }, [effectiveOpacity, isWireframe]);

  // High-Contrast Hardware Trim Material (EO/IR turret, landing gear, antennas)
  const hardwareMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: 0x0a1622,
      roughness: 0.35,
      metalness: 0.7,
      transparent: true,
      opacity: Math.min(1.0, effectiveOpacity * 3.0),
      depthWrite: false,
    });
  }, [effectiveOpacity]);



  return (
    <group name="TAPAS_MALE_UAV_AIRFRAME" position={[0, 0, 0]} raycast={() => {}}>
      {/* ================= 1. COMPLETE 3D TRANSLUCENT FUSELAGE ================= */}
      {/* Seamless procedural aerodynamic hull enclosing engine bay, radome, and tail boom */}
      <mesh geometry={fuselageGeo} material={compositeMaterial} />

      {/* ================= 2. COMPLETE 3D TRANSLUCENT WINGS ================= */}
      {/* High-aspect ratio wings with tapered airfoil and upturned wingtip winglets */}
      <mesh geometry={rightWingGeo} material={compositeMaterial} />
      <mesh geometry={leftWingGeo} material={compositeMaterial} />

      {/* Center Wing Fairing Blend */}
      <mesh material={compositeMaterial} position={[-0.2, 0.60, 0]}>
        <boxGeometry args={[1.18, 0.14, 1.2]} />
      </mesh>

      {/* ================= 3. COMPLETE 3D TRANSLUCENT EMPENNAGE ================= */}
      {/* Swept Vertical Stabilizer */}
      <mesh geometry={verticalFinGeo} material={compositeMaterial} />

      {/* High-Mounted T-Tail Horizontal Stabilizer */}
      <mesh geometry={hStabGeo} material={compositeMaterial} />

      {/* Twin Ventral Strakes (Directional stability under aft fuselage) */}
      {[-0.24, 0.24].map((zOffset, i) => (
        <mesh
          key={i}
          material={compositeMaterial}
          position={[-3.6, -0.05, zOffset]}
          rotation={[i === 0 ? 0.3 : -0.3, 0, 0.2]}
        >
          <boxGeometry args={[0.75, 0.28, 0.03]} />
        </mesh>
      ))}

      {/* ================= 4. ENGINE BAY NACA COOLING AIR DUCTS ================= */}
      {/* Side air scoops providing ram-air cooling around cylinder heads */}
      {[-1.32, 1.32].map((zPos, idx) => (
        <group key={idx} position={[0.2, 0.05, zPos]} rotation={[0, idx === 0 ? -0.2 : 0.2, 0]}>
          <mesh material={compositeMaterial}>
            <boxGeometry args={[0.65, 0.42, 0.18]} />
          </mesh>
          <mesh material={hardwareMaterial} position={[0.33, 0, 0]}>
            <planeGeometry args={[0.12, 0.32]} />
          </mesh>
        </group>
      ))}

      {/* ================= 5. SURVEILLANCE PAYLOAD & SENSORS ================= */}
      {/* Under-Nose EO/IR Optical Gimbal Turret */}
      <group position={[0.75, -0.52, 0]}>
        {/* Turret Mounting Collar */}
        <mesh material={hardwareMaterial} position={[0, 0.08, 0]}>
          <cylinderGeometry args={[0.15, 0.18, 0.10, 16]} />
        </mesh>
        {/* Optical Sensor Sphere */}
        <mesh material={hardwareMaterial} position={[0, -0.08, 0]}>
          <sphereGeometry args={[0.20, 20, 20]} />
        </mesh>
        {/* Daylight EO Camera Aperture */}
        <mesh position={[0.13, -0.08, 0.06]} rotation={[0, Math.PI / 2, 0]}>
          <cylinderGeometry args={[0.055, 0.055, 0.08, 16]} />
          <meshBasicMaterial color={0x22afff} />
        </mesh>
        {/* Thermal FLIR Sensor Aperture */}
        <mesh position={[0.13, -0.08, -0.06]} rotation={[0, Math.PI / 2, 0]}>
          <cylinderGeometry args={[0.045, 0.045, 0.08, 16]} />
          <meshBasicMaterial color={0xf59e0b} />
        </mesh>
      </group>

      {/* Nose Air Data Pitot Boom Probe */}
      <mesh material={hardwareMaterial} position={[1.48, 0.05, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.008, 0.012, 0.45, 12]} />
      </mesh>



      {/* ================= 7. WING HARDPOINT PYLONS & TRICYCLE LANDING GEAR ================= */}
      {/* Underslung Wing Payload Pylons */}
      {[-2.2, -1.3, 1.3, 2.2].map((pylonZ, i) => (
        <mesh key={i} material={hardwareMaterial} position={[-0.15, 0.48, pylonZ]}>
          <boxGeometry args={[0.42, 0.12, 0.05]} />
        </mesh>
      ))}

      {/* Nose Landing Gear (Strut & Dual Wheels) */}
      <group position={[1.05, -0.72, 0]}>
        <mesh material={hardwareMaterial} position={[0, 0.20, 0]}>
          <cylinderGeometry args={[0.028, 0.028, 0.44, 12]} />
        </mesh>
        {[-0.07, 0.07].map((wZ, i) => (
          <mesh key={i} material={hardwareMaterial} position={[0, -0.04, wZ]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.10, 0.10, 0.05, 16]} />
          </mesh>
        ))}
      </group>

      {/* Main Landing Gear (Port & Starboard Struts & Wheels) */}
      {[-1.05, 1.05].map((gZ, i) => (
        <group key={i} position={[-0.25, -0.75, gZ]}>
          <mesh material={hardwareMaterial} position={[0, 0.22, 0]}>
            <cylinderGeometry args={[0.035, 0.035, 0.46, 12]} />
          </mesh>
          <mesh material={hardwareMaterial} position={[0, -0.04, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.14, 0.14, 0.08, 16]} />
          </mesh>
        </group>
      ))}

      {/* Internal Firewall Bulkhead (Separating Engine Bay and Avionics) */}
      <mesh position={[-1.0, 0.05, 0]}>
        <boxGeometry args={[0.03, 0.88, 1.35]} />
        <meshStandardMaterial color={0x475569} transparent opacity={0.25} metalness={0.8} />
      </mesh>
    </group>
  );
}
