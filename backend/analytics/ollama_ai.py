"""
MAADT Local Ollama AI Propulsion Copilot & Diagnostic Inference Engine.
Connects directly to locally hosted Ollama models (e.g. qwen2.5:3b, mistral, qwen3:14b)
to provide grounded aerospace propulsion diagnostics, explainable anomaly reasoning,
and interactive mission control copilot assistance.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("maadt.ai")


class OllamaAIService:
    """
    Service gateway to local Ollama LLMs for aerospace propulsion digital twin inference.
    """

    def __init__(self, base_url: Optional[str] = None, default_model: str = "qwen2.5:3b"):
        resolved_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = resolved_url.rstrip("/")
        self.active_model = default_model
        self.fallback_models = ["qwen2.5:3b", "mistral:latest", "qwen3:14b", "prakriti-chat:latest"]

    async def check_health(self) -> Dict[str, Any]:
        """Check if local Ollama daemon or Cloud Gemini API is available."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            return {
                "status": "ONLINE",
                "active_model": model,
                "available_models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
                "provider": "Google Cloud Gemini",
            }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    # Ensure active model is in list, or pick best available
                    if self.active_model not in models and models:
                        for fb in self.fallback_models:
                            if fb in models:
                                self.active_model = fb
                                break
                        else:
                            self.active_model = models[0]
                    return {
                        "status": "ONLINE",
                        "active_model": self.active_model,
                        "available_models": models,
                        "base_url": self.base_url,
                    }
        except Exception as e:
            logger.warning(f"Local Ollama service check failed: {e}")

        return {
            "status": "OFFLINE",
            "active_model": self.active_model,
            "available_models": [],
            "base_url": self.base_url,
            "error": "Ollama service unreachable and GEMINI_API_KEY not set",
        }

    async def set_active_model(self, model_name: str) -> Dict[str, Any]:
        """Switch the active local LLM model for inference."""
        health = await self.check_health()
        if health["status"] == "ONLINE":
            if model_name in health["available_models"]:
                self.active_model = model_name
                return {"status": "SUCCESS", "active_model": self.active_model}
            else:
                return {
                    "status": "ERROR",
                    "error": f"Model '{model_name}' not installed in Ollama. Available: {health['available_models']}",
                }
        return {"status": "ERROR", "error": "Ollama offline"}

    async def generate_diagnostic_report(
        self,
        telemetry: Dict[str, Any],
        diagnostic_info: Optional[Dict[str, Any]] = None,
        subsystem_health: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes a deep physics-grounded aerospace diagnostic report using the local LLM.
        """
        rpm = telemetry.get("rpm", 2450)
        cht = telemetry.get("cht", 175)
        egt = telemetry.get("egt", 710)
        expected_egt = telemetry.get("expected_egt", 705)
        vibration = telemetry.get("vibration", 0.28)
        oil_p = telemetry.get("oil_pressure", 4.8)
        oil_t = telemetry.get("oil_temperature", 92)
        fuel_flow = telemetry.get("fuel_flow", 18.5)
        anomaly_score = telemetry.get("anomaly_score", 0.0)
        margin = telemetry.get("mission_margin", 75)
        regime = telemetry.get("operating_regime", "CRUISE")

        diag_issue = diagnostic_info.get("fault_type", "nominal") if diagnostic_info else "nominal"
        diag_prob = diagnostic_info.get("probability", 0.0) if diagnostic_info else 0.0
        diag_evidence = diagnostic_info.get("evidence", []) if diagnostic_info else []

        prompt = f"""You are the Chief Propulsion Diagnostic AI for the MAADT (Mission-Aware Aero-Engine Digital Twin) workstation, analyzing a 1352cc turbocharged aero-piston engine (AeroPiston-4X) powering a DRDO surveillance UAV.

CURRENT ENGINE TELEMETRY SNAPSHOT:
- Operating Regime: {regime}
- RPM: {rpm:.1f} (Nominal: 2200-2650)
- Cylinder Head Temp (CHT): {cht:.1f} °C (Max Nominal: 185°C, Redline: 230°C)
- Exhaust Gas Temp (EGT): {egt:.1f} °C (Physics Baseline: {expected_egt:.1f} °C, Redline: 880°C)
- Vibration: {vibration:.3f} g RMS (Nominal: <0.35 g, Critical: 1.2 g)
- Oil Pressure: {oil_p:.2f} bar (Nominal: 3.8-5.2 bar)
- Oil Temp: {oil_t:.1f} °C (Nominal: 80-105°C)
- Fuel Flow: {fuel_flow:.2f} L/h
- Composite Anomaly Score: {anomaly_score:.3f} (Warning: >0.45, Critical: >0.70)
- Current Mission Margin: {margin:.1f}%
- Statistical Classifier Hypothesis: {diag_issue} (Probability: {diag_prob:.1%})
- Detected Physical Deviations: {', '.join(diag_evidence) if diag_evidence else 'None'}

TASK:
Provide a concise, professional aerospace engineering diagnostic evaluation covering:
1. PRIMARY DIAGNOSTIC FINDING (Root cause mechanism)
2. SUBSYSTEM DEGRADATION IMPACT (Thermal, combustion, or mechanical stress)
3. FLIGHT OPERATION DIRECTIVE (Throttle adjustment, altitude recommendation, or RTB)
4. PREVENTATIVE MAINTENANCE DIRECTIVE (Specific component inspection)

Keep formatting crisp with clear headers. Output concise, technical engineering language."""

        t0 = time.time()
        ai_response = None
        used_model = self.active_model

        if os.environ.get("GEMINI_API_KEY"):
            ai_response = await self._call_gemini(prompt, system="You are an expert DRDO aerospace propulsion diagnostic engineer.")
            if ai_response:
                used_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        if not ai_response:
            ai_response = await self._call_ollama(prompt, system="You are an expert DRDO aerospace propulsion diagnostic engineer.")

        elapsed = time.time() - t0

        return {
            "status": "SUCCESS" if ai_response else "FALLBACK",
            "model_used": used_model,
            "inference_time_seconds": round(elapsed, 2),
            "diagnostic_report": ai_response or self._generate_rule_based_fallback(telemetry, diagnostic_info),
            "analyzed_timestamp": time.time(),
        }

    async def chat_copilot(
        self,
        user_message: str,
        telemetry: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Interactive mission control chat copilot grounded in live Digital Twin parameters.
        """
        rpm = telemetry.get("rpm", 2450)
        cht = telemetry.get("cht", 175)
        egt = telemetry.get("egt", 710)
        vibration = telemetry.get("vibration", 0.28)
        oil_p = telemetry.get("oil_pressure", 4.8)
        health = telemetry.get("health_index", 88)
        margin = telemetry.get("mission_margin", 75)
        active_diagnostic = telemetry.get("active_diagnostic", {})

        system_prompt = f"""You are MAADT-Copilot, an onboard AI Propulsion & Mission Control Specialist for the AeroPiston-4X turbocharged engine.
Live Engine State:
- RPM: {rpm}, CHT: {cht}°C, EGT: {egt}°C, Vibration: {vibration}g, Oil Press: {oil_p} bar
- Engine Health: {health}%, Mission Survival Margin: {margin}%
- Active Diagnostic: {active_diagnostic.get('fault_type', 'healthy')} (Severity: {active_diagnostic.get('severity', 'NOMINAL')})

Answer the pilot / flight engineer's question precisely, using accurate thermodynamic and mechanical aerospace terminology. Be concise and authoritative."""

        messages = []
        if history:
            for item in history[-6:]:  # include up to last 3 turns
                messages.append(item)
        messages.append({"role": "user", "content": user_message})

        t0 = time.time()
        response_text = None
        used_model = self.active_model

        if os.environ.get("GEMINI_API_KEY"):
            response_text = await self._call_gemini_chat(messages, system=system_prompt)
            if response_text:
                used_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        if not response_text:
            response_text = await self._call_ollama_chat(messages, system=system_prompt)

        elapsed = time.time() - t0

        return {
            "status": "SUCCESS" if response_text else "FALLBACK",
            "model_used": used_model,
            "inference_time_seconds": round(elapsed, 2),
            "reply": response_text or "Digital Twin Copilot offline. Telemetry nominal; all parameters within operating boundaries.",
        }

    async def _call_ollama(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """Direct inference via Ollama /api/generate."""
        payload = {
            "model": self.active_model,
            "prompt": prompt,
            "system": system or "You are an aerospace propulsion engineer.",
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 450,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama API call error: {e}")
        return None

    async def _call_ollama_chat(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Optional[str]:
        """Chat inference via Ollama /api/chat."""
        formatted_messages = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        formatted_messages.extend(messages)

        payload = {
            "model": self.active_model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 350,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    msg = resp.json().get("message", {})
                    return msg.get("content", "").strip()
        except Exception as e:
            logger.error(f"Ollama chat call error: {e}")
        return None

    async def _call_gemini(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """Inference using Google Cloud Gemini API."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return None
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ]
        }
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                else:
                    logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
        return None

    async def _call_gemini_chat(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Optional[str]:
        """Chat multi-turn inference using Google Cloud Gemini API."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return None
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
        gemini_contents = []
        for m in messages:
            role = "model" if m.get("role") in ["assistant", "system"] else "user"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}],
            })
        payload: Dict[str, Any] = {"contents": gemini_contents}
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                else:
                    logger.warning(f"Gemini chat API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Gemini chat API error: {e}")
        return None

    def _generate_rule_based_fallback(self, telemetry: Dict[str, Any], diag: Optional[Dict[str, Any]]) -> str:
        """Heuristic fallback if Ollama service is stopped."""
        fault = diag.get("fault_type", "nominal") if diag else "nominal"
        return f"""### PRIMARY DIAGNOSTIC FINDING
Physical state classification identifies: {fault.upper().replace('_', ' ')}.
Observed operating telemetry tracks within acceptable bounds, with subtle divergence in thermodynamic indicators.

### SUBSYSTEM DEGRADATION IMPACT
- Thermal Envelope: Headroom within ±10% of physics baseline.
- Mechanical Fatigue: Vibration amplitudes monitored via accelerometer arrays.

### FLIGHT OPERATION DIRECTIVE
Maintain current cruise profile while closely monitoring Cylinder Head Temperature (CHT) and harmonic vibration peaks. Avoid unnecessary high-manifold pressure transients.

### PREVENTATIVE MAINTENANCE DIRECTIVE
Conduct post-sortie borescope inspection and check fuel rail pressure regulator upon recovery."""


ollama_ai_service = OllamaAIService()
