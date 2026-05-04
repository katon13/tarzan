from __future__ import annotations

import json
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
        self._cache: Dict[str, Any] = {}

    def _load_json(self, path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def snapshot(self) -> Dict[str, Any]:
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
        signal_names = self.bus.names() if hasattr(self.bus, "names") else []
        all_state = self.bus.snapshot() if hasattr(self.bus, "snapshot") else {}
        active_outputs = sum(1 for value in all_state.values() if value not in (0, False, None, ""))
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
            "ehr.show_protocol_preview": bool(ehr.get("show_protocol_preview", True)),
            "ehr.show_axis_metrics": bool(ehr.get("show_axis_metrics", True)),
            "ehr.show_ghost_line": bool(ehr.get("show_ghost_line", True)),
            "ehr.take_duration_minutes": float(ehr.get("take_duration_minutes", 3.0)),
            "vision.source": source,
            "vision.active_profile": active_profile,
            "vision.tracking_mode": tracking.get("tracking_mode", "HSV_COLOR"),
            "vision.active_target": active_target,
            "vision.coordinate_mode": tracking.get("coordinate_mode", "CENTER_ERROR_X"),
            "vision.roi_enabled": bool(tracking.get("roi_enabled", False)),
            "vision.preview_fps": int((tracking.get("preview") or {}).get("live_fps", 15)),
            "vision.camera_width": int(camera.get("frame_width", 1920)),
            "vision.camera_height": int(camera.get("frame_height", 1080)),
            "vision.camera_fps": int(camera.get("fps", 15)),
            "vision.auto_exposure": bool(camera.get("auto_exposure", True)),
            "vision.auto_focus": bool(camera.get("auto_focus", False)),
            "vision.focus": float(camera.get("focus", 0.0)),
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
            "io.play_action_led": all_state.get("play_p16_action_led", 0),
            "io.rec_auto_enable": all_state.get("rec_p38_auto_enable", 0),
            "io.shock_sensor": all_state.get("rec_p39_shock_sensor", 0),
            "io.mass_reg_enable": all_state.get("play_p41_mass_reg_enable", 0),
            "io.arm_h_enable": all_state.get("play_p50_step_en_arm_h", 0),
            "io.arm_v_enable": all_state.get("play_p51_step_en_arm_v", 0),
        }
        self._cache = out
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
