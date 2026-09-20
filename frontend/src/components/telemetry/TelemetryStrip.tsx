"use client";
import React from 'react';
import { Activity, Flame, Thermometer, Droplet, Gauge, Fuel, Waves, BatteryCharging } from 'lucide-react';
import { TelemetryPacket } from '../../types/telemetry';
import { EngineComponentId } from '../../types/engine';
import TelemetryCard from './TelemetryCard';
import { StatusType } from '../common/StatusBadge';

interface TelemetryStripProps {
  telemetry: TelemetryPacket;
  history?: TelemetryPacket[];
  onSelectComponent?: (id: EngineComponentId) => void;
}

export default function TelemetryStrip({
  telemetry,
  history = [],
  onSelectComponent,
}: TelemetryStripProps) {
  // Extract histories for sparklines
  const getHistoryArray = (key: keyof TelemetryPacket, fallback: number) => {
    if (!history || history.length === 0) {
      return [fallback * 0.98, fallback, fallback * 1.01, fallback * 0.99, fallback];
    }
    return history.map((h) => Number(h[key]) || fallback);
  };

  // Semantic Status Evaluator
  const rpmStatus: StatusType = telemetry.rpm > 3000 ? "WARNING" : "NOMINAL";
  const egtStatus: StatusType = telemetry.egt > 780 ? "CRITICAL" : telemetry.egt > 740 ? "WARNING" : "NOMINAL";
  const chtStatus: StatusType = telemetry.cht > 200 ? "CRITICAL" : telemetry.cht > 185 ? "WARNING" : "NOMINAL";
  const oilPressStatus: StatusType = telemetry.oil_pressure < 2.8 ? "CRITICAL" : telemetry.oil_pressure < 3.5 ? "WARNING" : "NOMINAL";
  const oilTempStatus: StatusType = telemetry.oil_temperature > 112 ? "CRITICAL" : telemetry.oil_temperature > 105 ? "WARNING" : "NOMINAL";
  const fuelStatus: StatusType = telemetry.fuel_flow > 24 ? "ADVISORY" : "NOMINAL";
  const vibStatus: StatusType = telemetry.vibration > 0.6 ? "CRITICAL" : telemetry.vibration > 0.4 ? "WARNING" : "NOMINAL";
  const battStatus: StatusType = telemetry.battery_voltage < 25 ? "WARNING" : "NOMINAL";

  return (
    <div className="w-full select-none">
      <div className="flex items-center justify-between mb-2 font-mono">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#22AFFF]" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8]">
            Live Telemetry (8-Channel Bus)
          </h3>
        </div>
        <span className="text-[10px] text-[#60758A]">
          Click any card to inspect corresponding 3D engine component &bull; Synchronized 2 Hz Stream
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <TelemetryCard
          icon={Gauge}
          label="RPM"
          value={telemetry.rpm}
          unit="rpm"
          status={rpmStatus}
          history={getHistoryArray("rpm", telemetry.rpm)}
          onClick={() => onSelectComponent && onSelectComponent("propeller")}
        />
        <TelemetryCard
          icon={Flame}
          label="EGT"
          value={telemetry.egt}
          unit="°C"
          status={egtStatus}
          history={getHistoryArray("egt", telemetry.egt)}
          onClick={() => onSelectComponent && onSelectComponent("exhaust")}
        />
        <TelemetryCard
          icon={Thermometer}
          label="CHT"
          value={telemetry.cht}
          unit="°C"
          status={chtStatus}
          history={getHistoryArray("cht", telemetry.cht)}
          onClick={() => onSelectComponent && onSelectComponent("cylinder_3")}
        />
        <TelemetryCard
          icon={Droplet}
          label="Oil Pressure"
          value={telemetry.oil_pressure}
          unit="bar"
          status={oilPressStatus}
          history={getHistoryArray("oil_pressure", telemetry.oil_pressure)}
          onClick={() => onSelectComponent && onSelectComponent("lubrication")}
        />
        <TelemetryCard
          icon={Thermometer}
          label="Oil Temp"
          value={telemetry.oil_temperature}
          unit="°C"
          status={oilTempStatus}
          history={getHistoryArray("oil_temperature", telemetry.oil_temperature)}
          onClick={() => onSelectComponent && onSelectComponent("lubrication")}
        />
        <TelemetryCard
          icon={Fuel}
          label="Fuel Flow"
          value={telemetry.fuel_flow}
          unit="L/h"
          status={fuelStatus}
          history={getHistoryArray("fuel_flow", telemetry.fuel_flow)}
          onClick={() => onSelectComponent && onSelectComponent("intake")}
        />
        <TelemetryCard
          icon={Waves}
          label="Vibration"
          value={telemetry.vibration}
          unit="g"
          status={vibStatus}
          history={getHistoryArray("vibration", telemetry.vibration)}
          onClick={() => onSelectComponent && onSelectComponent("cylinder_bank")}
        />
        <TelemetryCard
          icon={BatteryCharging}
          label="Battery"
          value={telemetry.battery_voltage}
          unit="V"
          status={battStatus}
          history={getHistoryArray("battery_voltage", telemetry.battery_voltage)}
          onClick={() => onSelectComponent && onSelectComponent("gearbox")}
        />
      </div>
    </div>
  );
}
