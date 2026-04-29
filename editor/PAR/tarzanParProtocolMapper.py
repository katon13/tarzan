"""
Mapowanie protokołu TAKE/EHR na sygnały magistrali TARZAN.

TAKE używa czytelnych kolumn typu CAM_H_STEP, CAM_H_DIR.
SignalBus używa realnych nazw z core.tarzanZmienneSygnalowe.
Mapper zapisuje jednocześnie:
- sygnały wirtualne TAKE_* do diagnostyki,
- realne sygnały CNC/PLAY/REC, jeśli istnieją w mapie systemowej.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class AxisProtocolMap:
    prefix: str
    axis_key: str
    label: str
    step_signals: List[str] = field(default_factory=list)
    dir_signals: List[str] = field(default_factory=list)
    enable_signals: List[str] = field(default_factory=list)
    event_signals: List[str] = field(default_factory=list)


class TarzanParProtocolMapper:
    """Tłumaczy wiersz TAKE na paczkę sygnałów SignalBus."""

    def __init__(self, known_signal_names: Iterable[str]) -> None:
        self.known = set(known_signal_names)
        self.axis_maps: Dict[str, AxisProtocolMap] = self._build_maps()

    def _pick(self, *names: str) -> List[str]:
        return [name for name in names if name in self.known]

    def _build_maps(self) -> Dict[str, AxisProtocolMap]:
        # Uwaga: CAM_H_STEP zostaje czytelny w protokole, ale w busie trafia też
        # do realnych nazw sygnałów. Dla osi kamery preferuję CNC, bo to wyjścia automatyki.
        maps = [
            AxisProtocolMap(
                prefix="CAM_H", axis_key="cam_h", label="oś pozioma kamery",
                step_signals=self._pick("cnc_x_cam_h_ctr", "rec_p01_copy_ctr_cam_h"),
                dir_signals=self._pick("cnc_x_cam_h_dir", "rec_p03_copy_dir_cam_h"),
            ),
            AxisProtocolMap(
                prefix="CAM_V", axis_key="cam_v", label="oś pionowa kamery",
                step_signals=self._pick("cnc_y_cam_v_ctr", "rec_p02_copy_ctr_cam_v"),
                dir_signals=self._pick("cnc_y_cam_v_dir", "rec_p04_copy_dir_cam_v"),
            ),
            AxisProtocolMap(
                prefix="CAM_T", axis_key="cam_t", label="oś pochyłu kamery",
                step_signals=self._pick("cnc_a_arm_tilt_ctr", "rec_p08_copy_ctr_cam_tilt"),
                dir_signals=self._pick("cnc_a_arm_tilt_dir", "rec_p08_copy_dir_cam_tilt"),
            ),
            AxisProtocolMap(
                prefix="CAM_F", axis_key="cam_f", label="oś ostrości kamery",
                step_signals=self._pick("cnc_z_cam_f_ctr", "rec_p07_copy_ctr_cam_f"),
                dir_signals=self._pick("cnc_z_cam_f_dir", "rec_p07_copy_dir_cam_f"),
            ),
            AxisProtocolMap(
                prefix="ARM_H", axis_key="arm_h", label="oś pozioma ramienia",
                step_signals=self._pick("play_p46_step_ctr_arm_h", "cnc_b_arm_h_ctr"),
                dir_signals=self._pick("play_p38_step_dir_arm_h", "cnc_b_arm_h_dir"),
                enable_signals=self._pick("play_p50_step_en_arm_h"),
            ),
            AxisProtocolMap(
                prefix="ARM_V", axis_key="arm_v", label="oś pionowa ramienia",
                step_signals=self._pick("play_p48_step_ctr_arm_v", "cnc_c_arm_v_ctr"),
                dir_signals=self._pick("play_p39_step_dir_arm_v", "cnc_c_arm_v_dir"),
                enable_signals=self._pick("play_p51_step_en_arm_v"),
            ),
            AxisProtocolMap(
                prefix="DRON", axis_key="dron", label="DRON",
                step_signals=[], dir_signals=[], event_signals=["TAKE_DRON_RELEASE"],
            ),
        ]
        return {m.prefix: m for m in maps}

    def map_row(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        time_ms = self._int(row.get("TIME_MS", 0))
        out["TAKE_TIME_MS"] = time_ms

        for prefix, axis in self.axis_maps.items():
            step_col = f"{prefix}_STEP"
            dir_col = f"{prefix}_DIR"
            event_col = f"{prefix}_EVENT"

            if step_col in row:
                step_value = self._bit(row.get(step_col))
                out[f"TAKE_{step_col}"] = step_value
                for name in axis.step_signals:
                    out[name] = step_value

            if dir_col in row:
                dir_value = self._bit(row.get(dir_col))
                out[f"TAKE_{dir_col}"] = dir_value
                for name in axis.dir_signals:
                    out[name] = dir_value

            if event_col in row:
                event_raw = row.get(event_col, "")
                event_value = 1 if str(event_raw).strip() else 0
                out[f"TAKE_{event_col}"] = event_value
                for name in axis.event_signals:
                    out[name] = event_value

            # Jeżeli oś wykonuje protokół, enable osi ramienia trzymamy w stanie 1.
            if (step_col in row or dir_col in row) and axis.enable_signals:
                for name in axis.enable_signals:
                    out[name] = 1

        return out

    def map_take_columns(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for prefix, axis in self.axis_maps.items():
            result[f"{prefix}_STEP"] = [f"TAKE_{prefix}_STEP"] + axis.step_signals
            result[f"{prefix}_DIR"] = [f"TAKE_{prefix}_DIR"] + axis.dir_signals
            result[f"{prefix}_EVENT"] = [f"TAKE_{prefix}_EVENT"] + axis.event_signals
        return result

    def _bit(self, value: Any) -> int:
        if value in {1, True, "1", "true", "TRUE", "on", "ON"}:
            return 1
        return 0

    def _int(self, value: Any) -> int:
        try:
            return int(float(value))
        except Exception:
            return 0
