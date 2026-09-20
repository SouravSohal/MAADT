"use client";
import React, { useRef, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { EngineComponentId, EngineViewMode } from '../../types/engine';
import { TelemetryPacket } from '../../types/telemetry';
import TranslucentMaleUAVAirframe, { AirframeDisplayMode } from './TranslucentMaleUAVAirframe';

interface ProceduralAeroPistonEngineProps {
  telemetry: TelemetryPacket;
  viewMode: EngineViewMode;
  selectedComponent: EngineComponentId | null;
  onSelectComponent: (id: EngineComponentId) => void;
  airframeMode?: AirframeDisplayMode;
}

export default function ProceduralAeroPistonEngine({
  telemetry,
  viewMode,
  selectedComponent,
  onSelectComponent,
  airframeMode = "translucent",
}: ProceduralAeroPistonEngineProps) {
  const groupRef = useRef<THREE.Group>(null);
  const propRef = useRef<THREE.Group>(null);
  const crankRef = useRef<THREE.Group>(null);
  const faultLightRef = useRef<THREE.PointLight>(null);
  const [hoveredId, setHoveredId] = useState<EngineComponentId | null>(null);

  // Helper to determine if a specific component has an active anomaly/fault
  const isComponentFaulted = (id: EngineComponentId): boolean => {
    // 1. Direct active fault lookup from telemetry
    const hasActive = telemetry.active_faults?.some((f) => {
      const type = (f.fault_type || "").toLowerCase();
      if (type.includes("injector") || type.includes("misfire")) {
        return id === "cylinder_3";
      }
      if (type.includes("lubricat") || type.includes("oil")) {
        return id === "lubrication";
      }
      if (type.includes("turbo")) {
        return id === "turbocharger";
      }
      if (type.includes("overheat") || type.includes("thermal")) {
        return id === "cylinder_bank" || id.startsWith("cylinder_");
      }
      if (type.includes("sensor")) {
        return id === "exhaust" || id === "cylinder_3";
      }
      return false;
    });

    if (hasActive) return true;

    // 2. Anomaly score threshold (> 0.40 triggers Cylinder 3 injector alert in demo scenario)
    if (telemetry.anomaly_score > 0.4 && id === "cylinder_3") {
      return true;
    }

    return false;
  };

  // Determine if any engine component is in faulted state
  const hasAnyFault = useMemo(() => {
    const componentKeys: EngineComponentId[] = [
      "cylinder_1", "cylinder_2", "cylinder_3", "cylinder_4",
      "cylinder_bank", "turbocharger", "lubrication", "crankshaft", "intake", "exhaust", "propeller", "gearbox"
    ];
    return componentKeys.some((id) => isComponentFaulted(id));
  }, [telemetry]);

  // Spatial coordinates for the dynamic localized pulsing fault light
  const faultLightPos: [number, number, number] = useMemo(() => {
    if (isComponentFaulted("cylinder_3")) return [-0.42, 0.15, 0.72];
    if (isComponentFaulted("cylinder_1")) return [0.42, 0.15, 0.72];
    if (isComponentFaulted("cylinder_2")) return [0.42, 0.15, -0.72];
    if (isComponentFaulted("cylinder_4")) return [-0.42, 0.15, -0.72];
    if (isComponentFaulted("turbocharger")) return [-1.1, -0.10, 0.2];
    if (isComponentFaulted("lubrication")) return [0.1, -0.35, 0.42];
    if (isComponentFaulted("intake")) return [0, 0.55, 0];
    return [-0.42, 0.15, 0.72];
  }, [telemetry]);

  // Continuous animation frame (Rotation, Vibration, and Dynamic Breathing Glow)
  useFrame((state, delta) => {
    // 1. Rotational speed driven by RPM
    const rpm = telemetry.rpm || 2450;
    const rps = rpm / 60;

    if (propRef.current) {
      propRef.current.rotation.x += rps * Math.PI * 2 * delta;
    }
    if (crankRef.current) {
      crankRef.current.rotation.x += rps * Math.PI * 2 * delta;
    }

    // 2. Subtle mechanical vibration driven by telemetry vibration amplitude
    if (groupRef.current && telemetry.vibration) {
      const vibAmp = (telemetry.vibration / 1.0) * 0.003;
      groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 45) * vibAmp;
      groupRef.current.position.z = Math.cos(state.clock.elapsedTime * 35) * vibAmp;
    }

    // 3. CONTINUOUS HARMONIC BREATHING GLOW FOR FAULTED PARTS (DIM <-> LIGHT)
    // Sin wave oscillating between -1 and +1 with period ~1.5s (4.2 rad/s)
    const time = state.clock.elapsedTime;
    const pulseFactor = 0.5 + 0.5 * Math.sin(time * 4.2);
    // Smoothly breathe from dim (0.20) to bright light (2.40)
    const currentFaultIntensity = 0.20 + pulseFactor * 2.20;

    if (groupRef.current) {
      groupRef.current.traverse((child) => {
        if ((child as THREE.Mesh).isMesh && child.userData?.isFaulted) {
          const mesh = child as THREE.Mesh;
          // Only modulate if not currently selected by user (selected shows solid cyan CAD inspection)
          if (child.userData?.componentId !== selectedComponent) {
            const mat = mesh.material as THREE.MeshStandardMaterial;
            if (mat && mat.emissive) {
              mat.emissiveIntensity = currentFaultIntensity;
            }
          }
        }
      });
    }

    // Modulate localized fault warning light intensity in sync
    if (faultLightRef.current) {
      faultLightRef.current.intensity = hasAnyFault ? (0.4 + pulseFactor * 2.6) : 0;
    }
  });

  // Material builder helper respecting ViewMode, Selection, and Active Fault state
  const getComponentMaterial = (
    id: EngineComponentId,
    subsystem: "Combustion" | "Thermal" | "Lubrication" | "Mechanical" | "Induction" | "Exhaust",
    baseColor: number = 0x334155
  ) => {
    const isSelected = selectedComponent === id;
    const isHovered = hoveredId === id;
    const isFaulted = isComponentFaulted(id);

    // Base colors
    let color = baseColor;
    let emissive = 0x000000;
    let emissiveIntensity = 0.0;
    let opacity = 1.0;
    let transparent = false;

    // View Modes Handling
    if (viewMode === "X-Ray") {
      transparent = true;
      if (id === "cylinder_bank") {
        opacity = 0.22;
        color = 0x1e293b;
      } else if (id.startsWith("cylinder_")) {
        opacity = 0.45;
      } else {
        opacity = 0.65;
      }
    } else if (viewMode === "System") {
      // Color-coded subsystems
      if (subsystem === "Combustion") color = 0xd97706; // Amber
      else if (subsystem === "Thermal" || subsystem === "Exhaust") color = 0xef4444; // Red
      else if (subsystem === "Lubrication") color = 0x0284c7; // Blue
      else if (subsystem === "Induction") color = 0x06b6d4; // Cyan
      else color = 0x475569; // Slate
    } else if (viewMode === "Thermal") {
      // Thermal gradients based on CHT & EGT
      if (id === "exhaust" || id === "turbocharger") {
        const egt = telemetry.egt || 710;
        const factor = Math.min(1, Math.max(0, (egt - 650) / 170));
        color = 0x7f1d1d;
        emissive = 0xef4444;
        emissiveIntensity = 0.4 + factor * 1.6;
      } else if (id.startsWith("cylinder_")) {
        const cht = id === "cylinder_3" ? (telemetry.cht || 170) + 23 : telemetry.cht || 170;
        const factor = Math.min(1, Math.max(0, (cht - 150) / 70));
        color = 0x9a3412;
        emissive = 0xf97316;
        emissiveIntensity = 0.3 + factor * 1.5;
      }
    }

    // Active Fault Highlight (High-visibility warning glowing amber/orange-red)
    if (isFaulted) {
      color = 0x7f1d1d; // Deep warning crimson base
      emissive = 0xff4d15; // Vivid glowing hazard orange-red
      emissiveIntensity = 1.0; // Base intensity; dynamically modulated from dim to bright light by useFrame
    }

    // Hover & Selection Highlight
    if (isSelected) {
      emissive = 0x22afff;
      emissiveIntensity = 1.6;
    } else if (isHovered) {
      emissive = isFaulted ? 0xff7733 : 0x22afff;
      emissiveIntensity = 1.1;
    }

    return new THREE.MeshStandardMaterial({
      color,
      emissive: new THREE.Color(emissive),
      emissiveIntensity,
      metalness: 0.75,
      roughness: 0.3,
      transparent,
      opacity,
    });
  };

  const handleClick = (e: any, id: EngineComponentId) => {
    e.stopPropagation();
    onSelectComponent(id);
  };

  const handlePointerOver = (e: any, id: EngineComponentId) => {
    e.stopPropagation();
    setHoveredId(id);
  };

  const handlePointerOut = (e: any) => {
    e.stopPropagation();
    setHoveredId(null);
  };

  return (
    <group ref={groupRef} position={[0, 0, 0]} rotation={[0, -Math.PI / 4, 0]} scale={1.15}>
      {/* Dynamic localized pulsing warning light at the faulted component */}
      {hasAnyFault && (
        <pointLight
          ref={faultLightRef}
          position={faultLightPos}
          color="#FF4D15"
          distance={3.2}
          decay={2}
          intensity={1.5}
        />
      )}

      {/* 1. Central Crankcase Housing (Split-crankcase alloy block) */}
      <mesh
        userData={{ componentId: "cylinder_bank", isFaulted: isComponentFaulted("cylinder_bank") }}
        material={getComponentMaterial("cylinder_bank", "Mechanical", 0x1e293b)}
        position={[0, 0, 0]}
        onClick={(e) => handleClick(e, "cylinder_bank")}
        onPointerOver={(e) => handlePointerOver(e, "cylinder_bank")}
        onPointerOut={handlePointerOut}
      >
        <boxGeometry args={[1.5, 0.75, 0.8]} />
      </mesh>

      {/* 2. Rotating Crankshaft Assembly (Internal - visible in cutaway/x-ray) */}
      <group ref={crankRef} position={[0, 0, 0]}>
        <mesh
          userData={{ componentId: "crankshaft", isFaulted: isComponentFaulted("crankshaft") }}
          material={getComponentMaterial("crankshaft", "Mechanical", 0x64748b)}
          rotation={[0, 0, Math.PI / 2]}
          onClick={(e) => handleClick(e, "crankshaft")}
          onPointerOver={(e) => handlePointerOver(e, "crankshaft")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.07, 0.07, 1.8, 16]} />
        </mesh>
        {/* Crankshaft Counterweights & Rod Journals */}
        {[-0.45, -0.15, 0.15, 0.45].map((pos, i) => (
          <mesh
            key={i}
            userData={{ componentId: "crankshaft", isFaulted: isComponentFaulted("crankshaft") }}
            material={getComponentMaterial("crankshaft", "Mechanical", 0x94a3b8)}
            position={[pos, Math.sin(i * Math.PI) * 0.15, Math.cos(i * Math.PI) * 0.15]}
          >
            <boxGeometry args={[0.12, 0.28, 0.18]} />
          </mesh>
        ))}
      </group>

      {/* 3. Four Horizontally-Opposed Finned Cylinders (Boxer-4 Aero Config) */}
      {/* Cylinder 1: Front Right (+X, +Z) */}
      <group position={[0.42, 0, 0.72]}>
        <mesh
          userData={{ componentId: "cylinder_1", isFaulted: isComponentFaulted("cylinder_1") }}
          material={getComponentMaterial("cylinder_1", "Combustion", 0x334155)}
          rotation={[Math.PI / 2, 0, 0]}
          onClick={(e) => handleClick(e, "cylinder_1")}
          onPointerOver={(e) => handlePointerOver(e, "cylinder_1")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.26, 0.28, 0.75, 20]} />
        </mesh>
        {/* Cooling Fins */}
        {[-0.2, -0.08, 0.04, 0.16].map((offset, idx) => (
          <mesh
            key={idx}
            userData={{ componentId: "cylinder_1", isFaulted: isComponentFaulted("cylinder_1") }}
            material={getComponentMaterial("cylinder_1", "Thermal", 0x475569)}
            position={[0, 0, offset]}
          >
            <cylinderGeometry args={[0.31, 0.31, 0.02, 20]} />
          </mesh>
        ))}
        {/* Cylinder Head */}
        <mesh
          userData={{ componentId: "cylinder_1", isFaulted: isComponentFaulted("cylinder_1") }}
          material={getComponentMaterial("cylinder_1", "Combustion", 0x1e293b)}
          position={[0, 0, 0.42]}
        >
          <boxGeometry args={[0.48, 0.48, 0.16]} />
        </mesh>
      </group>

      {/* Cylinder 2: Front Left (+X, -Z) */}
      <group position={[0.42, 0, -0.72]}>
        <mesh
          userData={{ componentId: "cylinder_2", isFaulted: isComponentFaulted("cylinder_2") }}
          material={getComponentMaterial("cylinder_2", "Combustion", 0x334155)}
          rotation={[-Math.PI / 2, 0, 0]}
          onClick={(e) => handleClick(e, "cylinder_2")}
          onPointerOver={(e) => handlePointerOver(e, "cylinder_2")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.26, 0.28, 0.75, 20]} />
        </mesh>
        {/* Cooling Fins */}
        {[-0.2, -0.08, 0.04, 0.16].map((offset, idx) => (
          <mesh
            key={idx}
            userData={{ componentId: "cylinder_2", isFaulted: isComponentFaulted("cylinder_2") }}
            material={getComponentMaterial("cylinder_2", "Thermal", 0x475569)}
            position={[0, 0, -offset]}
          >
            <cylinderGeometry args={[0.31, 0.31, 0.02, 20]} />
          </mesh>
        ))}
        {/* Cylinder Head */}
        <mesh
          userData={{ componentId: "cylinder_2", isFaulted: isComponentFaulted("cylinder_2") }}
          material={getComponentMaterial("cylinder_2", "Combustion", 0x1e293b)}
          position={[0, 0, -0.42]}
        >
          <boxGeometry args={[0.48, 0.48, 0.16]} />
        </mesh>
      </group>

      {/* Cylinder 3: Rear Right (-X, +Z) — PRIMARY TARGET FOR FAULT HIGHLIGHT */}
      <group position={[-0.42, 0, 0.72]}>
        <mesh
          userData={{ componentId: "cylinder_3", isFaulted: isComponentFaulted("cylinder_3") }}
          material={getComponentMaterial("cylinder_3", "Combustion", 0x334155)}
          rotation={[Math.PI / 2, 0, 0]}
          onClick={(e) => handleClick(e, "cylinder_3")}
          onPointerOver={(e) => handlePointerOver(e, "cylinder_3")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.26, 0.28, 0.75, 20]} />
        </mesh>
        {/* Cooling Fins */}
        {[-0.2, -0.08, 0.04, 0.16].map((offset, idx) => (
          <mesh
            key={idx}
            userData={{ componentId: "cylinder_3", isFaulted: isComponentFaulted("cylinder_3") }}
            material={getComponentMaterial("cylinder_3", "Thermal", 0x475569)}
            position={[0, 0, offset]}
          >
            <cylinderGeometry args={[0.31, 0.31, 0.02, 20]} />
          </mesh>
        ))}
        {/* Cylinder Head */}
        <mesh
          userData={{ componentId: "cylinder_3", isFaulted: isComponentFaulted("cylinder_3") }}
          material={getComponentMaterial("cylinder_3", "Combustion", 0x1e293b)}
          position={[0, 0, 0.42]}
        >
          <boxGeometry args={[0.48, 0.48, 0.16]} />
        </mesh>
      </group>

      {/* Cylinder 4: Rear Left (-X, -Z) */}
      <group position={[-0.42, 0, -0.72]}>
        <mesh
          userData={{ componentId: "cylinder_4", isFaulted: isComponentFaulted("cylinder_4") }}
          material={getComponentMaterial("cylinder_4", "Combustion", 0x334155)}
          rotation={[-Math.PI / 2, 0, 0]}
          onClick={(e) => handleClick(e, "cylinder_4")}
          onPointerOver={(e) => handlePointerOver(e, "cylinder_4")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.26, 0.28, 0.75, 20]} />
        </mesh>
        {/* Cooling Fins */}
        {[-0.2, -0.08, 0.04, 0.16].map((offset, idx) => (
          <mesh
            key={idx}
            userData={{ componentId: "cylinder_4", isFaulted: isComponentFaulted("cylinder_4") }}
            material={getComponentMaterial("cylinder_4", "Thermal", 0x475569)}
            position={[0, 0, -offset]}
          >
            <cylinderGeometry args={[0.31, 0.31, 0.02, 20]} />
          </mesh>
        ))}
        {/* Cylinder Head */}
        <mesh
          userData={{ componentId: "cylinder_4", isFaulted: isComponentFaulted("cylinder_4") }}
          material={getComponentMaterial("cylinder_4", "Combustion", 0x1e293b)}
          position={[0, 0, -0.42]}
        >
          <boxGeometry args={[0.48, 0.48, 0.16]} />
        </mesh>
      </group>

      {/* 4. Intake Plenum & Injection Rail (Top Induction) */}
      <group position={[0, 0.48, 0]}>
        {/* Central Plenum Chamber */}
        <mesh
          userData={{ componentId: "intake", isFaulted: isComponentFaulted("intake") }}
          material={getComponentMaterial("intake", "Induction", 0x0f172a)}
          position={[0, 0, 0]}
          onClick={(e) => handleClick(e, "intake")}
          onPointerOver={(e) => handlePointerOver(e, "intake")}
          onPointerOut={handlePointerOut}
        >
          <boxGeometry args={[1.2, 0.18, 0.35]} />
        </mesh>
        {/* Runners branching to cylinders */}
        {[-0.35, 0.35].map((xPos, idx) => (
          <React.Fragment key={idx}>
            <mesh
              userData={{ componentId: "intake", isFaulted: isComponentFaulted("intake") }}
              material={getComponentMaterial("intake", "Induction", 0x475569)}
              position={[xPos, -0.15, 0.45]}
            >
              <cylinderGeometry args={[0.04, 0.04, 0.4, 8]} />
            </mesh>
            <mesh
              userData={{ componentId: "intake", isFaulted: isComponentFaulted("intake") }}
              material={getComponentMaterial("intake", "Induction", 0x475569)}
              position={[xPos, -0.15, -0.45]}
            >
              <cylinderGeometry args={[0.04, 0.04, 0.4, 8]} />
            </mesh>
          </React.Fragment>
        ))}
      </group>

      {/* 5. Exhaust Manifold & Tuned Runners (Bottom/Rear) */}
      <group position={[-0.2, -0.44, 0]}>
        <mesh
          userData={{ componentId: "exhaust", isFaulted: isComponentFaulted("exhaust") }}
          material={getComponentMaterial("exhaust", "Exhaust", 0x475569)}
          position={[0, 0, 0]}
          onClick={(e) => handleClick(e, "exhaust")}
          onPointerOver={(e) => handlePointerOver(e, "exhaust")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.07, 0.07, 1.1, 12]} />
        </mesh>
        {/* Exhaust collector pipe leading to Turbocharger */}
        <mesh
          userData={{ componentId: "exhaust", isFaulted: isComponentFaulted("exhaust") }}
          material={getComponentMaterial("exhaust", "Exhaust", 0x475569)}
          position={[-0.5, 0.1, 0]}
          rotation={[0, 0, Math.PI / 4]}
        >
          <cylinderGeometry args={[0.08, 0.08, 0.6, 12]} />
        </mesh>
      </group>

      {/* 6. High-Altitude Turbocharger & Wastegate (Rear Mount) */}
      <group position={[-1.1, -0.2, 0]}>
        {/* Turbine Snail Housing */}
        <mesh
          userData={{ componentId: "turbocharger", isFaulted: isComponentFaulted("turbocharger") }}
          material={getComponentMaterial("turbocharger", "Thermal", 0x1e293b)}
          rotation={[0, Math.PI / 2, 0]}
          onClick={(e) => handleClick(e, "turbocharger")}
          onPointerOver={(e) => handlePointerOver(e, "turbocharger")}
          onPointerOut={handlePointerOut}
        >
          <torusGeometry args={[0.22, 0.09, 16, 24]} />
        </mesh>
        {/* Compressor Housing */}
        <mesh
          userData={{ componentId: "turbocharger", isFaulted: isComponentFaulted("turbocharger") }}
          material={getComponentMaterial("turbocharger", "Induction", 0x64748b)}
          position={[-0.15, 0, 0]}
        >
          <cylinderGeometry args={[0.16, 0.24, 0.22, 16]} />
        </mesh>
        {/* Wastegate Actuator Canister */}
        <mesh
          userData={{ componentId: "turbocharger", isFaulted: isComponentFaulted("turbocharger") }}
          material={getComponentMaterial("turbocharger", "Induction", 0x94a3b8)}
          position={[0, 0.28, 0.12]}
        >
          <cylinderGeometry args={[0.06, 0.06, 0.22, 12]} />
        </mesh>
      </group>

      {/* 7. Front Gearbox / Propeller Reduction Unit (PRSU) */}
      <group position={[0.92, 0.05, 0]}>
        <mesh
          userData={{ componentId: "gearbox", isFaulted: isComponentFaulted("gearbox") }}
          material={getComponentMaterial("gearbox", "Mechanical", 0x0f172a)}
          rotation={[0, 0, Math.PI / 2]}
          onClick={(e) => handleClick(e, "gearbox")}
          onPointerOver={(e) => handlePointerOver(e, "gearbox")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.28, 0.38, 0.45, 20]} />
        </mesh>
      </group>

      {/* 8. Propeller Assembly (Spinner Hub & 2 Aero Blades) */}
      <group ref={propRef} position={[1.25, 0.05, 0]}>
        {/* Spinner Cone */}
        <mesh
          userData={{ componentId: "propeller", isFaulted: isComponentFaulted("propeller") }}
          material={getComponentMaterial("propeller", "Mechanical", 0x0f172a)}
          rotation={[0, 0, -Math.PI / 2]}
          onClick={(e) => handleClick(e, "propeller")}
          onPointerOver={(e) => handlePointerOver(e, "propeller")}
          onPointerOut={handlePointerOut}
        >
          <coneGeometry args={[0.22, 0.42, 20]} />
        </mesh>
        {/* Carbon Composite Propeller Blade 1 */}
        <mesh
          userData={{ componentId: "propeller", isFaulted: isComponentFaulted("propeller") }}
          material={getComponentMaterial("propeller", "Mechanical", 0x1e293b)}
          position={[0, 0.82, 0]}
        >
          <boxGeometry args={[0.05, 1.45, 0.16]} />
        </mesh>
        {/* Carbon Composite Propeller Blade 2 */}
        <mesh
          userData={{ componentId: "propeller", isFaulted: isComponentFaulted("propeller") }}
          material={getComponentMaterial("propeller", "Mechanical", 0x1e293b)}
          position={[0, -0.82, 0]}
        >
          <boxGeometry args={[0.05, 1.45, 0.16]} />
        </mesh>
      </group>

      {/* 9. Lubrication Circuit (Oil Filter Canister & Stainless Lines) */}
      <group position={[0.1, -0.42, 0.42]}>
        <mesh
          userData={{ componentId: "lubrication", isFaulted: isComponentFaulted("lubrication") }}
          material={getComponentMaterial("lubrication", "Lubrication", 0x0284c7)}
          onClick={(e) => handleClick(e, "lubrication")}
          onPointerOver={(e) => handlePointerOver(e, "lubrication")}
          onPointerOut={handlePointerOut}
        >
          <cylinderGeometry args={[0.11, 0.11, 0.32, 16]} />
        </mesh>
        {/* Oil Line */}
        <mesh
          userData={{ componentId: "lubrication", isFaulted: isComponentFaulted("lubrication") }}
          material={getComponentMaterial("lubrication", "Lubrication", 0x38bdf8)}
          position={[-0.2, 0.15, 0]}
        >
          <cylinderGeometry args={[0.025, 0.025, 0.4, 8]} />
        </mesh>
      </group>

      {/* 10. DRDO TAPAS-BH-201 MALE UAV Translucent Airframe Enclosure */}
      <TranslucentMaleUAVAirframe mode={airframeMode} />
    </group>
  );
}
