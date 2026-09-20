"""
CAN Bus and SocketCAN Protocol Handler for Aero-Piston Engine Telemetry.
Implements CAN 2.0B frame encoding and decoding for ECU/FADEC engine channels.
Reference: overview.md Sections 5, 47, 81.
"""

from dataclasses import dataclass
import struct
from typing import Any, Dict, List, Optional, Tuple
from schemas.telemetry import TelemetryPacket, SensorQuality


# Standard CAN Arbitration IDs for Engine Telemetry (§47)
CAN_ID_RPM_THROTTLE = 0x200
CAN_ID_CHT = 0x201
CAN_ID_EGT = 0x202
CAN_ID_OIL = 0x203
CAN_ID_FUEL = 0x204
CAN_ID_VIBRATION = 0x205
CAN_ID_ELECTRICAL = 0x206


@dataclass
class CANFrame:
    """Standard 8-byte CAN 2.0B Frame."""
    can_id: int
    data: bytes
    is_extended: bool = False
    dlc: int = 8

    def pack(self) -> bytes:
        """Packs standard Linux SocketCAN struct can_frame (can_id: uint32, can_dlc: uint8, data: 8 bytes)."""
        can_id_flag = self.can_id | (0x80000000 if self.is_extended else 0)
        padded_data = self.data.ljust(8, b'\x00')[:8]
        return struct.pack("=IB3x8s", can_id_flag, len(self.data), padded_data)

    @classmethod
    def unpack(cls, raw_bytes: bytes) -> "CANFrame":
        """Unpacks Linux SocketCAN 16-byte raw frame."""
        if len(raw_bytes) < 16:
            raise ValueError(f"SocketCAN frame must be at least 16 bytes, got {len(raw_bytes)}")
        can_id_raw, dlc, data = struct.unpack("=IB3x8s", raw_bytes[:16])
        is_extended = bool(can_id_raw & 0x80000000)
        can_id = can_id_raw & 0x1FFFFFFF
        return cls(can_id=can_id, data=data[:dlc], is_extended=is_extended, dlc=dlc)


class EngineCANCodec:
    """Encodes engine telemetry into CAN frames and decodes CAN frames into telemetry fields."""

    @staticmethod
    def encode_rpm_throttle(rpm: float, throttle_pct: float) -> CANFrame:
        """
        0x200:
        Bytes 0-1: RPM (uint16, 1 RPM/bit)
        Bytes 2-3: Throttle (uint16, 0.01 %/bit -> 0 to 10000)
        """
        rpm_val = int(max(0, min(65535, round(rpm))))
        thr_val = int(max(0, min(10000, round(throttle_pct * 100))))
        data = struct.pack("<HH4x", rpm_val, thr_val)
        return CANFrame(can_id=CAN_ID_RPM_THROTTLE, data=data)

    @staticmethod
    def encode_temperatures(cht_c: float, egt_c: float) -> Tuple[CANFrame, CANFrame]:
        """
        0x201: CHT (uint16, 0.1 °C/bit)
        0x202: EGT (uint16, 0.1 °C/bit)
        """
        cht_raw = int(max(0, min(65535, round(cht_c * 10))))
        egt_raw = int(max(0, min(65535, round(egt_c * 10))))
        frame_cht = CANFrame(can_id=CAN_ID_CHT, data=struct.pack("<H6x", cht_raw))
        frame_egt = CANFrame(can_id=CAN_ID_EGT, data=struct.pack("<H6x", egt_raw))
        return frame_cht, frame_egt

    @staticmethod
    def encode_oil(oil_pressure_bar: float, oil_temp_c: float) -> CANFrame:
        """
        0x203:
        Bytes 0-1: Oil Pressure (uint16, 0.001 bar/bit -> e.g. 4800 = 4.8 bar)
        Bytes 2-3: Oil Temperature (int16, 0.1 °C/bit)
        """
        press_raw = int(max(0, min(65535, round(oil_pressure_bar * 1000))))
        temp_raw = int(round(oil_temp_c * 10))
        data = struct.pack("<Hh4x", press_raw, temp_raw)
        return CANFrame(can_id=CAN_ID_OIL, data=data)

    @staticmethod
    def encode_fuel(fuel_flow_lh: float) -> CANFrame:
        """0x204: Fuel Flow (uint16, 0.01 L/h/bit)."""
        ff_raw = int(max(0, min(65535, round(fuel_flow_lh * 100))))
        return CANFrame(can_id=CAN_ID_FUEL, data=struct.pack("<H6x", ff_raw))

    @staticmethod
    def encode_vibration(vibration_g: float) -> CANFrame:
        """0x205: Vibration RMS (uint16, 0.001 g/bit)."""
        vib_raw = int(max(0, min(65535, round(vibration_g * 1000))))
        return CANFrame(can_id=CAN_ID_VIBRATION, data=struct.pack("<H6x", vib_raw))

    @staticmethod
    def encode_electrical(voltage_v: float, current_a: float) -> CANFrame:
        """
        0x206:
        Bytes 0-1: Bus Voltage (uint16, 0.01 V/bit)
        Bytes 2-3: Alternator Current (int16, 0.01 A/bit)
        """
        v_raw = int(max(0, min(65535, round(voltage_v * 100))))
        a_raw = int(round(current_a * 100))
        return CANFrame(can_id=CAN_ID_ELECTRICAL, data=struct.pack("<Hh4x", v_raw, a_raw))

    @staticmethod
    def decode_frame(frame: CANFrame) -> Dict[str, Any]:
        """Decodes standard engine CAN frame into telemetry fields."""
        fields: Dict[str, Any] = {}
        data = frame.data

        if frame.can_id == CAN_ID_RPM_THROTTLE and len(data) >= 4:
            rpm, thr = struct.unpack("<HH", data[:4])
            fields["rpm"] = float(rpm)
            fields["throttle"] = float(thr) / 100.0

        elif frame.can_id == CAN_ID_CHT and len(data) >= 2:
            cht_raw = struct.unpack("<H", data[:2])[0]
            fields["cht"] = round(float(cht_raw) / 10.0, 1)

        elif frame.can_id == CAN_ID_EGT and len(data) >= 2:
            egt_raw = struct.unpack("<H", data[:2])[0]
            fields["egt"] = round(float(egt_raw) / 10.0, 1)

        elif frame.can_id == CAN_ID_OIL and len(data) >= 4:
            press_raw, temp_raw = struct.unpack("<Hh", data[:4])
            fields["oil_pressure"] = round(float(press_raw) / 1000.0, 3)
            fields["oil_temperature"] = round(float(temp_raw) / 10.0, 1)

        elif frame.can_id == CAN_ID_FUEL and len(data) >= 2:
            ff_raw = struct.unpack("<H", data[:2])[0]
            fields["fuel_flow"] = round(float(ff_raw) / 100.0, 2)

        elif frame.can_id == CAN_ID_VIBRATION and len(data) >= 2:
            vib_raw = struct.unpack("<H", data[:2])[0]
            fields["vibration"] = round(float(vib_raw) / 1000.0, 3)

        elif frame.can_id == CAN_ID_ELECTRICAL and len(data) >= 4:
            v_raw, a_raw = struct.unpack("<Hh", data[:4])
            fields["battery_voltage"] = round(float(v_raw) / 100.0, 2)
            fields["alternator_current"] = round(float(a_raw) / 100.0, 2)

        return fields
