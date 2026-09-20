"""
MAVLink Protocol Handler for UAV Telemetry Streams.
Implements MAVLink v2 packet decoding and encoding for engine parameters
using standard NAMED_VALUE_FLOAT (ID 251) and custom engine status frames.
Reference: overview.md Sections 5, 47, 81.
"""

from dataclasses import dataclass
import struct
from typing import Any, Dict, List, Optional, Tuple


MAVLINK_V2_MAGIC = 0xFD
MSG_ID_NAMED_VALUE_FLOAT = 251
MSG_ID_ENGINE_STATUS_CUSTOM = 185  # Custom MAVLink message for multi-sensor pack


def mavlink_crc_accumulate(buf: bytes, crc: int = 0xFFFF) -> int:
    """Computes X.25 / MAVLink standard 16-bit CRC."""
    for b in buf:
        tmp = b ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc &= 0xFFFF
    return crc


@dataclass
class MAVLinkPacket:
    """MAVLink v2 Packet representation."""
    msg_id: int
    payload: bytes
    sys_id: int = 1
    comp_id: int = 1
    seq: int = 0
    incompat_flags: int = 0
    compat_flags: int = 0

    def serialize(self, crc_extra: int = 170) -> bytes:
        """Serializes frame into MAVLink v2 wire format."""
        header = struct.pack(
            "<BBBBBBBHB",
            MAVLINK_V2_MAGIC,
            len(self.payload),
            self.incompat_flags,
            self.compat_flags,
            self.seq,
            self.sys_id,
            self.comp_id,
            self.msg_id & 0xFFFF,
            (self.msg_id >> 16) & 0xFF,
        )
        packet_bytes = header + self.payload
        crc = mavlink_crc_accumulate(packet_bytes[1:])  # Skip magic
        crc = mavlink_crc_accumulate(bytes([crc_extra]), crc)
        return packet_bytes + struct.pack("<H", crc)

    @classmethod
    def parse(cls, data: bytes) -> Tuple[Optional["MAVLinkPacket"], int]:
        """
        Parses the first complete MAVLink v2 packet from data bytes.
        Returns (packet, bytes_consumed).
        """
        if len(data) < 12:  # Min header (10) + CRC (2)
            return None, 0

        magic_idx = data.find(bytes([MAVLINK_V2_MAGIC]))
        if magic_idx == -1:
            return None, len(data)

        if magic_idx > 0:
            data = data[magic_idx:]

        if len(data) < 12:
            return None, magic_idx

        payload_len = data[1]
        total_len = 10 + payload_len + 2
        if len(data) < total_len:
            return None, magic_idx  # Need more bytes

        incompat_flags, compat_flags, seq, sys_id, comp_id = struct.unpack("<BBBBB", data[2:7])
        msg_id_low, msg_id_high = struct.unpack("<HB", data[7:10])
        msg_id = (msg_id_high << 16) | msg_id_low

        payload = data[10 : 10 + payload_len]
        crc_received = struct.unpack("<H", data[10 + payload_len : total_len])[0]

        packet = cls(
            msg_id=msg_id,
            payload=payload,
            sys_id=sys_id,
            comp_id=comp_id,
            seq=seq,
            incompat_flags=incompat_flags,
            compat_flags=compat_flags,
        )
        return packet, magic_idx + total_len


class MAVLinkEngineHandler:
    """Encodes and decodes MAVLink engine telemetry packets."""

    @staticmethod
    def encode_named_value_float(
        name: str,
        value: float,
        time_boot_ms: int = 0,
        seq: int = 0,
        sys_id: int = 1,
        comp_id: int = 1
    ) -> bytes:
        """Encodes standard MAVLink NAMED_VALUE_FLOAT (ID 251)."""
        name_bytes = name.encode("ascii")[:10].ljust(10, b'\x00')
        payload = struct.pack("<If10s", time_boot_ms, float(value), name_bytes)
        pkt = MAVLinkPacket(
            msg_id=MSG_ID_NAMED_VALUE_FLOAT,
            payload=payload,
            sys_id=sys_id,
            comp_id=comp_id,
            seq=seq,
        )
        return pkt.serialize(crc_extra=170)

    @staticmethod
    def decode_named_value_float(payload: bytes) -> Tuple[str, float, int]:
        """Decodes NAMED_VALUE_FLOAT payload -> (name, value, time_boot_ms)."""
        if len(payload) < 18:
            raise ValueError(f"NAMED_VALUE_FLOAT payload requires 18 bytes, got {len(payload)}")
        time_boot_ms, val, name_raw = struct.unpack("<If10s", payload[:18])
        name = name_raw.decode("ascii", errors="ignore").rstrip("\x00")
        return name, val, time_boot_ms

    @staticmethod
    def encode_engine_pack(
        rpm: float,
        cht: float,
        egt: float,
        oil_pressure: float,
        oil_temp: float,
        fuel_flow: float,
        vibration: float,
        time_boot_ms: int = 0,
        seq: int = 0
    ) -> bytes:
        """
        Custom MAVLink packed message ID 185:
        Pack all primary aero-piston parameters into a single 28-byte UDP packet.
        """
        payload = struct.pack(
            "<Ifffffff",
            time_boot_ms,
            float(rpm),
            float(cht),
            float(egt),
            float(oil_pressure),
            float(oil_temp),
            float(fuel_flow),
            float(vibration),
        )
        pkt = MAVLinkPacket(
            msg_id=MSG_ID_ENGINE_STATUS_CUSTOM,
            payload=payload,
            seq=seq,
        )
        return pkt.serialize(crc_extra=185)

    @staticmethod
    def decode_engine_pack(payload: bytes) -> Dict[str, Any]:
        """Decodes custom engine status packet ID 185."""
        if len(payload) < 32:
            raise ValueError(f"Engine status pack requires 32 bytes, got {len(payload)}")
        time_boot_ms, rpm, cht, egt, oil_p, oil_t, ff, vib = struct.unpack("<Ifffffff", payload[:32])
        return {
            "time_boot_ms": time_boot_ms,
            "rpm": round(rpm, 1),
            "cht": round(cht, 1),
            "egt": round(egt, 1),
            "oil_pressure": round(oil_p, 3),
            "oil_temperature": round(oil_t, 1),
            "fuel_flow": round(ff, 2),
            "vibration": round(vib, 3),
        }
