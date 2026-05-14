from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]


class TarzanNextionStateMapper:
    def __init__(self, bus) -> None:
        self.bus = bus
        self.khr_path = ROOT_DIR / "data" / "khr" / "khr_settings.json"
        self.vision_path = ROOT_DIR / "data" / "khr" / "vision_settings.json"
        self.ehr_path = ROOT_DIR / "data" / "ehr" / "main_take_settings.json"
        self.par_path = ROOT_DIR / "data" / "par" / "tarzan_par_layout.json"
        
        self._file_cache: Dict[str, tuple[float, Any]] = {}
        self._cache: Dict[str, Any] = {}
        self._last_snapshot = {}
        self._last_snapshot_time = 0.0

    def _load_json(self, path: Path, default: Any) -> Any:
        now = time.time()
        path_str = str(path)
        if path_str in self._file_cache:
            ts, data = self._file_cache[path_str]
            if now - ts < 1.0:  # 1 sekunda cache'u dla plików
                return data
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._file_cache[path_str] = (now, data)
            return data
        except Exception:
            return default

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        if (now - self._last_snapshot_time) < 0.02:
            return self._last_snapshot
        khr = self._load_json(self.khr_path, {})
        vision = self._load_json(self.vision_path, {})
        ehr = self._load_json(self.ehr_path, {})
        par = self._load_json(self.par_path, {})
        tracking = vision.get("tracking", {})
        camera = vision.get("camera_device", {})
        face = tracking.get("face_tracking", {})
        target_profiles = tracking.get("target_profiles", {})
        source = khr.get("active_source", "TEST")
        active_profile = khr.get("active_profile", "CINEMA")
        active_target = tracking.get("active_target", "RED_OBJECT")
        current_profile = (khr.get("profiles", {}) or {}).get(active_profile, {})
        
        # Optymalizacja: pobieramy tylko potrzebne wartości zamiast całego snapshotu magistrali
        def bget(n, d=0): return self.bus.get(n, d) if hasattr(self.bus, "get") else d
        
        signal_names = self.bus.names() if hasattr(self.bus, "names") else []
        active_outputs = 0 # Wartość przybliżona lub do pominięcia w szybkim cyklu
        
        out = {
            "system.mode": getattr(self.bus, "mode", "TEST"),
            "system.take_time_ms": getattr(self.bus, "take_time_ms", 0),
            "system.loaded_take": getattr(self.bus, "loaded_take_path", "") or "BRAK",
            "system.signal_count": len(signal_names),
            "system.active_outputs": active_outputs,
            "par.visible_panels": len([k for k, v in (par.get("panels") or {}).items() if v]),
            "par.timeline_visible": bool((par.get("panels") or {}).get("timeline", True)),
            "par.operator_visible": bool((par.get("panels") or {}).get("operator", True)),
            "par.axes_visible": bool((par.get("panels") or {}).get("axes", True)),
            "par.log_visible": bool((par.get("panels") or {}).get("log", True)),
            "par_level_x": bget("par_level_x"),
            "par_level_y": bget("par_level_y"),
            "par_level_z": bget("par_level_z"),
            "ehr.show_protocol_preview": bool(ehr.get("show_protocol_preview", True)),
            "ehr.show_axis_metrics": bool(ehr.get("show_axis_metrics", True)),
            "ehr.show_ghost_line": bool(ehr.get("show_ghost_line", True)),
            "khr.source": source,
            "khr.profile": active_profile,
            "tracking.active_target": active_target,
            "vision.source": camera.get("source_name", source),
            "vision.tracking_mode": face.get("active_backend", face.get("backend", "HAAR")),
            "vision.active_target": active_target,
            "vision.camera_fps": float(camera.get("fps", 0.0) or 0.0),
            "vision.exposure": float(camera.get("exposure", -6.0)),
            "vision.brightness": float(camera.get("brightness", 0.0)),
            "vision.gain": float(camera.get("gain", 0.0)),
            "tracking.target_profiles_count": len(target_profiles),
            "tracking.face_backend": face.get("active_backend", face.get("backend", "HAAR")),
            "tracking.target_lock": bool((tracking.get("target_lock") or {}).get("enabled", True)),
            "tracking.profile_gain": float(current_profile.get("gain", 0.0)),
            "tracking.profile_dead_zone_px": float(current_profile.get("dead_zone_px", 0.0)),
            "tracking.profile_prediction": float(current_profile.get("prediction", 0.0)),
            "tracking.profile_damping": float(current_profile.get("damping", 0.0)),
            "tracking.profile_max_correction": float(current_profile.get("max_correction", 0.0)),
            "io.play_action_led": bget("play_p16_action_led"),
            "io.rec_auto_enable": bget("rec_p38_auto_enable"),
            "io.shock_sensor": bget("rec_p39_shock_sensor"),
            "io.mass_reg_enable": bget("play_p41_mass_reg_enable"),
            "io.arm_h_enable": bget("play_p50_step_en_arm_h"),
            "io.arm_v_enable": bget("play_p51_step_en_arm_v"),
        }
        self._cache = out
        self._last_snapshot = out
        self._last_snapshot_time = now
        return out

    def set_value(self, path: str, value: Any) -> None:
        if path.startswith("vision.") or path.startswith("tracking."):
            data = self._load_json(self.vision_path, {})
            self._set_nested(data, path.split(".")[1:], value)
            self._write_json(self.vision_path, data)
            return
        if path.startswith("ehr."):
            data = self._load_json(self.ehr_path, {})
            self._set_nested(data, path.split(".")[1:], value)
            self._write_json(self.ehr_path, data)
            return
        if path.startswith("par."):
            data = self._load_json(self.par_path, {})
            self._set_nested(data, path.split(".")[1:], value)
            self._write_json(self.par_path, data)
            return

    def _set_nested(self, data: Dict[str, Any], keys: List[str], value: Any) -> None:
        target = data
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        target[keys[-1]] = value
