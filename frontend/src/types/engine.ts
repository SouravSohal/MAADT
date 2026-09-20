export type EngineComponentId =
  | "propeller"
  | "gearbox"
  | "cylinder_bank"
  | "cylinder_1"
  | "cylinder_2"
  | "cylinder_3"
  | "cylinder_4"
  | "turbocharger"
  | "intake"
  | "exhaust"
  | "lubrication"
  | "crankshaft";

export type EngineViewMode = "3D" | "System" | "Thermal" | "X-Ray";

export interface ComponentDetails {
  id: EngineComponentId;
  name: string;
  subsystem: "Combustion" | "Thermal" | "Lubrication" | "Mechanical" | "Induction" | "Exhaust";
  health: number; // 0-100%
  cht?: number; // °C
  egt?: number; // °C
  vibration?: number; // g
  status: "Normal" | "Advisory" | "Abnormal" | "Critical";
  diagnostic?: {
    issue: string;
    probability: number;
    severity: "INFO" | "ADVISORY" | "WARNING" | "CRITICAL";
    evidence: string[];
    trend: string;
  };
}
