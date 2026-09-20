"""
Tests for local Ollama AI Diagnostic and Copilot Gateway (§MAADT AI).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_ai_status_endpoint():
    """Verify the AI status endpoint returns Ollama daemon connectivity and models."""
    resp = client.get("/api/v1/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "active_model" in data
    assert "available_models" in data
    assert data["status"] in ["ONLINE", "OFFLINE"]


def test_ai_model_select_endpoint():
    """Verify switching active Ollama model."""
    resp = client.post("/api/v1/ai/model/select", json={"model_name": "qwen2.5:3b"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["SUCCESS", "ERROR"]


def test_ai_diagnostics_analyze_endpoint():
    """Verify AI-powered diagnostics analysis generation."""
    payload = {
        "telemetry": {
            "rpm": 2480,
            "cht": 178,
            "egt": 715,
            "expected_egt": 710,
            "vibration": 0.29,
            "oil_pressure": 4.7,
            "oil_temperature": 94,
            "fuel_flow": 18.2,
            "anomaly_score": 0.12,
            "mission_margin": 82.0,
            "operating_regime": "CRUISE",
        },
        "diagnostic_info": {
            "fault_type": "healthy",
            "probability": 0.94,
            "evidence": ["Thermodynamics tracking physics baseline"],
        },
    }
    resp = client.post("/api/v1/ai/diagnostics/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "diagnostic_report" in data
    assert "model_used" in data
    assert len(data["diagnostic_report"]) > 50


def test_ai_copilot_chat_endpoint():
    """Verify interactive AI copilot chat response with live telemetry context."""
    payload = {
        "message": "What is the current thermal state of the engine?",
        "telemetry": {
            "rpm": 2450,
            "cht": 175,
            "egt": 710,
            "vibration": 0.28,
            "health_index": 92.0,
            "mission_margin": 78.0,
        },
    }
    resp = client.post("/api/v1/ai/copilot/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "model_used" in data
    assert len(data["reply"]) > 10
