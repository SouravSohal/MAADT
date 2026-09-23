"""
Configuration loader for engine definitions, mission profiles, and fault scenarios.
Handles resolution of YAML files, caching, and fallback defaults.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .engine_config import EngineConfig, MissionConfig

_env_config_dir = os.environ.get("MAADT_CONFIG_DIR")
if _env_config_dir:
    CONFIG_DIR = Path(_env_config_dir)
else:
    candidate = Path(__file__).resolve().parent.parent.parent / "configs"
    CONFIG_DIR = candidate if candidate.exists() else Path("/app/configs")


class ConfigManager:
    """Manages loaded engine, mission, and scenario configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is not None:
            self.config_dir = config_dir
        elif "MAADT_CONFIG_DIR" in os.environ:
            self.config_dir = Path(os.environ["MAADT_CONFIG_DIR"])
        else:
            self.config_dir = CONFIG_DIR
        self._engines: Dict[str, EngineConfig] = {}
        self._missions: Dict[str, MissionConfig] = {}
        self.reload_all()

    def reload_all(self):
        """Scans the config directory and loads all available configs."""
        self._load_engines()
        self._load_missions()

    def _load_engines(self):
        engine_dir = self.config_dir / "engines"
        if not engine_dir.exists():
            # Create default in-memory config if directory missing
            self._engines["default"] = EngineConfig()
            return

        for file_path in engine_dir.glob("*.yaml"):
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    if data and "engine" in data:
                        cfg = EngineConfig(**data["engine"])
                        key = file_path.stem
                        self._engines[key] = cfg
            except Exception as e:
                print(f"[ConfigManager] Error loading engine config {file_path}: {e}")

        if not self._engines:
            self._engines["default"] = EngineConfig()

    def _load_missions(self):
        mission_dir = self.config_dir / "missions"
        if not mission_dir.exists():
            return

        for file_path in mission_dir.glob("*.yaml"):
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    if data and "mission" in data:
                        cfg = MissionConfig(**data["mission"])
                        key = cfg.id or file_path.stem
                        self._missions[key] = cfg
            except Exception as e:
                print(f"[ConfigManager] Error loading mission config {file_path}: {e}")

    def get_engine_config(self, engine_name: str = "aero_piston_x") -> EngineConfig:
        """Returns the requested engine configuration or fallback default."""
        if engine_name in self._engines:
            return self._engines[engine_name]
        for cfg in self._engines.values():
            if cfg.name.lower() == engine_name.lower():
                return cfg
        return list(self._engines.values())[0]

    def get_mission_config(self, mission_id: str) -> Optional[MissionConfig]:
        """Returns a mission configuration by ID."""
        return self._missions.get(mission_id)

    def list_engines(self) -> List[str]:
        return list(self._engines.keys())

    def list_missions(self) -> List[Dict[str, str]]:
        return [{"id": m.id, "name": m.name, "description": m.description} for m in self._missions.values()]


# Global singleton instance
config_manager = ConfigManager()
