export type SensorQuality =
  | "VALID"
  | "STALE"
  | "MISSING"
  | "OUT_OF_RANGE"
  | "NOISY"
  | "SUSPECT";

export type OperatingRegime =
  | "START"
  | "WARM_UP"
  | "IDLE"
  | "TAXI"
  | "TAKEOFF"
  | "CLIMB"
  | "CRUISE"
  | "LOITER"
  | "THROTTLE_TRANSIENT"
  | "DESCENT"
  | "LANDING"
  | "SHUTDOWN";

export type AlertSeverity =
  | "INFO"
  | "ADVISORY"
  | "WARNING"
  | "HIGH"
  | "CRITICAL";

export type FaultType =
  | "misfire"
  | "injector_abnormality"
  | "ignition_degradation"
  | "lubrication_issue"
  | "sensor_drift"
  | "sensor_failure"
  | "combustion_instability"
  | "overheating"
  | "abnormal_vibration"
  | "electrical_abnormality"
  | "healthy";

export interface AnomalyScoreDetails {
  composite_score: number;
  physics_score: number;
  statistical_score: number;
  ml_score: number;
  trend_score: number;
  is_out_of_distribution: boolean;
}

export interface PhysicsResiduals {
  egt_residual: number;
  cht_residual: number;
  rpm_residual: number;
  fuel_flow_residual: number;
  oil_temp_residual: number;
  oil_pressure_residual: number;
}

export interface SubsystemHealth {
  overall: number;
  thermal: number;
  combustion: number;
  lubrication: number;
  vibration: number;
  electrical: number;
  confidence: number;
}

export interface RULPrediction {
  hours_remaining: number;
  hours_lower_bound: number;
  hours_upper_bound: number;
  confidence: number;
  trend: "STABLE" | "LINEAR" | "ACCELERATING" | "SUDDEN";
  limiting_subsystem: string;
  degradation_rate_pct_hr: number;
}

export interface StressIndex {
  thermal: number;
  mechanical: number;
  combustion: number;
  lubrication: number;
  transient: number;
  overall: number;
  cumulative_stress: number;
}

export interface MissionMarginBreakdown {
  thermal_margin: number;
  load_margin: number;
  fuel_margin: number;
  degradation_margin: number;
  rul_margin: number;
  composite_margin: number;
  confidence: number;
  is_critical: boolean;
  recommendation: string;
}

export interface DiagnosticHypothesis {
  fault_type: string;
  probability: number;
  severity: AlertSeverity;
  subsystem: string;
  evidence: string[];
}

export interface TelemetryPacket {
  timestamp: number;
  engine_id: string;
  altitude: number;
  throttle: number;
  rpm: number;
  egt: number;
  expected_egt: number;
  cht: number;
  expected_cht: number;
  oil_pressure: number;
  oil_temperature: number;
  fuel_flow: number;
  vibration: number;
  battery_voltage: number;
  health_index: number;
  anomaly_score: number;
  anomaly_breakdown: AnomalyScoreDetails;
  mission_margin: number;
  mission_margin_breakdown: MissionMarginBreakdown;
  operating_regime: OperatingRegime;
  active_faults: Array<{
    fault_type: string;
    severity: number;
    target_sensor?: string;
  }>;
  active_diagnostic: DiagnosticHypothesis;
  estimated_mechanical_state: {
    estimated_rpm: number;
    estimated_load: number;
    estimated_thermal_stress: number;
  };
  residuals: PhysicsResiduals;
  subsystem_health: SubsystemHealth;
  sensor_trust: Record<string, number>;
  sensor_quality: Record<string, SensorQuality>;
  twin_confidence: number;
  stress_index: StressIndex;
  rul: RULPrediction;
}
