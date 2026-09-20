"""
Phase 9 Unit Tests: Edge Gateway Interface & MAVLink / CAN Emulation.
Verifies CAN 2.0B encoding/decoding, MAVLink v2 frame handling,
Edge Gateway demultiplexing, and telemetry ring-buffering during link dropouts.
Reference: overview.md Sections 47, 48, 67, 81.
"""

import pytest
from protocols.can_bus import EngineCANCodec, CANFrame, CAN_ID_RPM_THROTTLE, CAN_ID_CHT, CAN_ID_OIL
from protocols.mavlink_handler import (
    MAVLinkEngineHandler, MAVLinkPacket, mavlink_crc_accumulate,
    MSG_ID_NAMED_VALUE_FLOAT, MSG_ID_ENGINE_STATUS_CUSTOM
)
from gateway.edge_gateway import EdgeGateway


def test_can_frame_pack_unpack():
    """Verifies standard 16-byte Linux SocketCAN frame pack/unpack."""
    frame = CANFrame(can_id=0x200, data=b'\x92\x09\x40\x1f\x00\x00\x00\x00')
    packed = frame.pack()
    assert len(packed) == 16

    unpacked = CANFrame.unpack(packed)
    assert unpacked.can_id == 0x200
    assert unpacked.dlc == 8
    assert unpacked.data[:4] == b'\x92\x09\x40\x1f'


def test_can_telemetry_encoding_decoding():
    """Verifies CAN bus encoding and decoding for engine channels (§47)."""
    # 1. RPM & Throttle
    frame_rpm = EngineCANCodec.encode_rpm_throttle(rpm=2450.0, throttle_pct=65.0)
    decoded_rpm = EngineCANCodec.decode_frame(frame_rpm)
    assert decoded_rpm["rpm"] == 2450.0
    assert decoded_rpm["throttle"] == 65.0

    # 2. CHT & EGT
    frame_cht, frame_egt = EngineCANCodec.encode_temperatures(cht_c=168.4, egt_c=712.2)
    decoded_cht = EngineCANCodec.decode_frame(frame_cht)
    decoded_egt = EngineCANCodec.decode_frame(frame_egt)
    assert decoded_cht["cht"] == 168.4
    assert decoded_egt["egt"] == 712.2

    # 3. Oil Pressure and Temperature
    frame_oil = EngineCANCodec.encode_oil(oil_pressure_bar=4.825, oil_temp_c=92.3)
    decoded_oil = EngineCANCodec.decode_frame(frame_oil)
    assert decoded_oil["oil_pressure"] == 4.825
    assert decoded_oil["oil_temperature"] == 92.3

    # 4. Fuel & Vibration
    frame_fuel = EngineCANCodec.encode_fuel(fuel_flow_lh=18.45)
    assert EngineCANCodec.decode_frame(frame_fuel)["fuel_flow"] == 18.45

    frame_vib = EngineCANCodec.encode_vibration(vibration_g=0.285)
    assert EngineCANCodec.decode_frame(frame_vib)["vibration"] == 0.285


def test_mavlink_crc_and_packet_serialization():
    """Verifies MAVLink v2 frame serialization and CRC accumulation."""
    payload = b'TESTPAYLOAD'
    pkt = MAVLinkPacket(msg_id=123, payload=payload, sys_id=1, comp_id=1, seq=5)
    raw = pkt.serialize(crc_extra=50)
    assert raw[0] == 0xFD
    assert raw[1] == len(payload)
    assert len(raw) == 10 + len(payload) + 2

    parsed_pkt, consumed = MAVLinkPacket.parse(raw)
    assert parsed_pkt is not None
    assert parsed_pkt.msg_id == 123
    assert parsed_pkt.payload == payload
    assert consumed == len(raw)


def test_mavlink_named_value_float():
    """Verifies MAVLink NAMED_VALUE_FLOAT (ID 251) encode/decode."""
    raw = MAVLinkEngineHandler.encode_named_value_float(
        name="RPM",
        value=2450.0,
        time_boot_ms=10500,
        seq=1
    )
    parsed_pkt, _ = MAVLinkPacket.parse(raw)
    assert parsed_pkt is not None
    assert parsed_pkt.msg_id == MSG_ID_NAMED_VALUE_FLOAT

    name, val, t_ms = MAVLinkEngineHandler.decode_named_value_float(parsed_pkt.payload)
    assert name == "RPM"
    assert round(val, 1) == 2450.0
    assert t_ms == 10500


def test_mavlink_engine_status_pack():
    """Verifies multi-sensor MAVLink engine pack (ID 185)."""
    raw = MAVLinkEngineHandler.encode_engine_pack(
        rpm=2450.0,
        cht=168.4,
        egt=712.2,
        oil_pressure=4.8,
        oil_temp=92.3,
        fuel_flow=18.4,
        vibration=0.28,
        time_boot_ms=25000,
        seq=2
    )
    parsed_pkt, _ = MAVLinkPacket.parse(raw)
    assert parsed_pkt is not None
    assert parsed_pkt.msg_id == MSG_ID_ENGINE_STATUS_CUSTOM

    decoded = MAVLinkEngineHandler.decode_engine_pack(parsed_pkt.payload)
    assert decoded["rpm"] == 2450.0
    assert decoded["cht"] == 168.4
    assert decoded["egt"] == 712.2
    assert decoded["oil_pressure"] == 4.8


def test_edge_gateway_demux_and_buffering():
    """Verifies edge gateway demultiplexing, ring buffering, and drain recovery (§81)."""
    gw = EdgeGateway(buffer_capacity=10)
    assert gw.get_status()["status"] == "STOPPED"
    gw.start_listening()
    assert gw.get_status()["status"] == "LISTENING"

    # Feed a SocketCAN frame
    can_frame = EngineCANCodec.encode_rpm_throttle(rpm=2600.0, throttle_pct=70.0)
    records = gw.process_raw_bytes(can_frame.pack())
    assert len(records) == 1
    assert records[0]["rpm"] == 2600.0
    assert records[0]["source_protocol"] == "SOCKETCAN_2.0B"

    # Feed a MAVLink packed frame
    mav_raw = MAVLinkEngineHandler.encode_engine_pack(
        rpm=2500.0, cht=165.0, egt=705.0, oil_pressure=4.9,
        oil_temp=90.0, fuel_flow=18.0, vibration=0.25
    )
    mav_records = gw.process_raw_bytes(mav_raw)
    assert len(mav_records) == 1
    assert mav_records[0]["egt"] == 705.0
    assert mav_records[0]["source_protocol"] == "MAVLINK_ENGINE_PACK"

    # Check buffering
    status = gw.get_status()
    assert status["packets_received"] == 2
    assert status["packets_decoded"] == 2
    assert status["buffered_samples"] == 2

    # Drain buffer (link reconnection)
    drained = gw.drain_buffer()
    assert len(drained) == 2
    assert gw.get_status()["buffered_samples"] == 0
