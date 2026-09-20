"use client";
import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { TelemetryPacket } from '../../types/telemetry';

interface EGTTrendChartProps {
  history: TelemetryPacket[];
  currentEgt: number;
  expectedEgt: number;
}

export default function EGTTrendChart({
  history,
  currentEgt,
  expectedEgt,
}: EGTTrendChartProps) {
  // Transform history into chart points with last 10 minutes simulated timestamps
  const chartData = (history.length > 0
    ? history
    : Array.from({ length: 20 }, (_, i) => ({
        egt: 710 + (i > 12 ? (i - 12) * 5.8 : 0),
        expected_egt: 710,
        timestamp: Date.now() / 1000 - (20 - i) * 30,
      }))
  ).map((item, idx) => ({
    time: item.timestamp
      ? new Date(item.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : `T-${(20 - idx) * 30}s`,
    actual: item.egt,
    expected: item.expected_egt || 710.0,
    residual: Number((item.egt - (item.expected_egt || 710.0)).toFixed(1)),
  }));

  const divergence = Number((currentEgt - expectedEgt).toFixed(1));

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 font-mono select-none flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            THERMODYNAMIC RESIDUAL
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">EGT Trend (Last 10 Minutes)</h3>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-[#8FA4B8]">Divergence (Δ): </span>
          <span
            className={`text-xs font-bold ${
              divergence > 35 ? 'text-[#FF4D4D]' : divergence > 15 ? 'text-[#FF8A3D]' : 'text-[#22D88A]'
            }`}
          >
            {divergence > 0 ? `+${divergence}` : divergence} °C
          </span>
        </div>
      </div>

      {/* Recharts Line Chart */}
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1B344B" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#60758A"
              tick={{ fontSize: 9, fill: "#8FA4B8" }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[600, 880]}
              stroke="#60758A"
              tick={{ fontSize: 9, fill: "#8FA4B8" }}
              tickLine={false}
              unit="°"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#07111D",
                borderColor: "#1B344B",
                borderRadius: "8px",
                fontSize: "11px",
                fontFamily: "monospace",
              }}
              labelStyle={{ color: "#8FA4B8" }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="plainline"
              wrapperStyle={{ fontSize: "10px", paddingBottom: "6px" }}
            />
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual EGT"
              stroke="#FF4D4D"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="expected"
              name="Expected EGT"
              stroke="#22AFFF"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#60758A] mt-1 pt-1.5 border-t border-[#1B344B]/60">
        <span>Model: Reduced-Order Thermodynamic Physics v1.0.4</span>
        <span className="text-[#22AFFF]">MAE &lt; 3.5%</span>
      </div>
    </div>
  );
}
