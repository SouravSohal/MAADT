import { MissionMarginBreakdown } from "./telemetry";

export interface CounterfactualBranch {
  scenario_id: string;
  scenario_name: string;
  description: string;
  target_throttle: number;
  target_altitude: number;
  horizon_minutes: number;
  peak_cht: number;
  peak_egt: number;
  final_health: number;
  final_survival_margin: number;
  safety_verdict: "SAFE" | "MARGINAL" | "UNSAFE" | "CRITICAL";
  recommendation: string;
  margin_breakdown?: MissionMarginBreakdown;
}

export interface ReplayMilestone {
  timestamp: number;
  time_formatted: string;
  event_type: "START" | "TAKEOFF" | "CLIMB" | "CRUISE" | "ANOMALY" | "DESCENT" | "LANDING";
  description: string;
  severity: "INFO" | "ADVISORY" | "WARNING" | "CRITICAL";
  health_at_event: number;
  margin_at_event: number;
}

export interface FleetAircraft {
  uav_id: string;
  engine_id: string;
  status: "AIRBORNE" | "STANDBY" | "MAINTENANCE";
  health_index: number;
  flight_hours: number;
  active_faults: number;
  mission: string;
  regime: string;
  composite_margin: number;
  rul_hours: number;
}
