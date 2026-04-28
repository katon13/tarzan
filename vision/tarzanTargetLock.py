# -*- coding: utf-8 -*-
"""
TARZAN - Target Lock

Globalna warstwa stabilizacji celu dla wszystkich pluginów vision:
- KameraHSV,
- KameraHAAR,
- KameraMEDIAPIPE,
- KameraHEAD.

Plugin wykrywa cel. TargetLock robi operatorowe "przyspawanie":
DETECT -> LOCK -> HOLD -> LOST.

Nie czyta kamery i nie zmienia algorytmów detekcji. Pracuje wyłącznie na
CameraTrackingResult, czyli na wspólnym kontrakcie dla KHR.
"""

from __future__ import annotations

from dataclasses import dataclass
import time

from vision.tarzanCameraTracker import CameraTrackingResult


@dataclass
class TargetLockConfig:
    enabled: bool = True
    hold_ms: int = 550
    lock_confirm_frames: int = 2
    lost_confirm_frames: int = 6
    error_smoothing: float = 0.35
    center_smoothing: float = 0.30
    area_smoothing: float = 0.20
    lost_decay: float = 0.96
    max_jump_px: float = 300.0
    draw_overlay: bool = True
    approximate_box_scale: float = 1.35


class TarzanTargetLock:
    """Stabilizuje wynik detekcji bez mieszania się w pluginy.

    Stany operatorowe:
    - DETECT: świeży wynik pluginu, jeszcze potwierdzany,
    - LOCK: cel przyspawany i aktualizowany,
    - HOLD: plugin chwilowo zgubił cel, ale KHR nadal dostaje ostatni stabilny error_x,
    - LOST: cel naprawdę zgubiony.
    """

    def __init__(self, settings: dict | None = None) -> None:
        self.settings = settings or {}
        self.config = self._config_from_settings(self.settings)
        self.reset()

    def reload_settings(self, settings: dict | None) -> None:
        self.settings = settings or {}
        self.config = self._config_from_settings(self.settings)

    def reset(self) -> None:
        self.state = "LOST"
        self.visible = False
        self.x = 0.0
        self.y = 0.0
        self.area = 0.0
        self.error_x = 0.0
        self.frame_center_x = 0.0
        self.frame_width = 0
        self.frame_height = 0
        self._lock_count = 0
        self._lost_count = 0
        self._last_seen_ms = 0
        self._last_state_change_ms = int(time.time() * 1000)

    def _config_from_settings(self, settings: dict) -> TargetLockConfig:
        cfg = (settings.get("tracking", {}) or {}).get("target_lock", {}) or {}
        return TargetLockConfig(
            enabled=bool(cfg.get("enabled", True)),
            hold_ms=int(cfg.get("hold_ms", 550)),
            lock_confirm_frames=max(1, int(cfg.get("lock_confirm_frames", 2))),
            lost_confirm_frames=max(1, int(cfg.get("lost_confirm_frames", 6))),
            error_smoothing=max(0.0, min(1.0, float(cfg.get("error_smoothing", 0.35)))),
            center_smoothing=max(0.0, min(1.0, float(cfg.get("center_smoothing", 0.30)))),
            area_smoothing=max(0.0, min(1.0, float(cfg.get("area_smoothing", 0.20)))),
            lost_decay=max(0.0, min(1.0, float(cfg.get("lost_decay", 0.96)))),
            max_jump_px=max(0.0, float(cfg.get("max_jump_px", 300.0))),
            draw_overlay=bool(cfg.get("draw_overlay", True)),
            approximate_box_scale=max(0.5, float(cfg.get("approximate_box_scale", 1.35))),
        )

    def process(self, result: CameraTrackingResult, now_ms: int | None = None) -> CameraTrackingResult:
        cfg = self.config
        if not cfg.enabled:
            self._stamp_result(result, "DETECT" if result.visible else "LOST", 0)
            return result

        now_ms = int(time.time() * 1000) if now_ms is None else int(now_ms)
        detected = bool(result.visible)
        self.frame_center_x = float(result.frame_center_x or self.frame_center_x or 0.0)
        self.frame_width = int(result.frame_width or self.frame_width or 0)
        self.frame_height = int(result.frame_height or self.frame_height or 0)

        if detected:
            rx = float(result.object_x)
            ry = float(result.object_y)
            ra = float(result.area)
            re = float(result.error_x)

            if self.visible and cfg.max_jump_px > 0:
                dx = rx - self.x
                dy = ry - self.y
                if (dx * dx + dy * dy) ** 0.5 > cfg.max_jump_px:
                    # Podejrzany przeskok na inny obiekt. Nie zrywamy od razu — HOLD.
                    detected = False
                else:
                    self._accept_detection(rx, ry, ra, re, now_ms)
            else:
                self._accept_detection(rx, ry, ra, re, now_ms)

        if not detected:
            self._lost_count += 1
            self._lock_count = 0
            hold_alive = self.visible and (now_ms - self._last_seen_ms) <= cfg.hold_ms and self._lost_count < cfg.lost_confirm_frames
            if hold_alive:
                self.state = "HOLD"
                self.error_x *= cfg.lost_decay
            else:
                self.state = "LOST"
                self.visible = False
                self.error_x = 0.0

        out = CameraTrackingResult(
            visible=bool(self.visible),
            error_x=float(self.error_x if self.visible else 0.0),
            object_x=float(self.x if self.visible else 0.0),
            object_y=float(self.y if self.visible else 0.0),
            frame_center_x=float(result.frame_center_x or self.frame_center_x),
            frame_width=int(result.frame_width or self.frame_width),
            frame_height=int(result.frame_height or self.frame_height),
            area=float(self.area if self.visible else 0.0),
            frame_rgb=result.frame_rgb,
        )
        hold_left = max(0, cfg.hold_ms - (now_ms - self._last_seen_ms)) if self.visible else 0
        self._stamp_result(out, self.state, hold_left)
        if cfg.draw_overlay and out.frame_rgb is not None:
            self._draw_overlay(out)
        return out

    def _accept_detection(self, rx: float, ry: float, ra: float, re: float, now_ms: int) -> None:
        cfg = self.config
        self._lost_count = 0
        self._lock_count += 1
        self._last_seen_ms = now_ms

        if not self.visible:
            self.x = rx
            self.y = ry
            self.area = ra
            self.error_x = re
            self.visible = self._lock_count >= cfg.lock_confirm_frames
            self.state = "LOCK" if self.visible else "DETECT"
            return

        cs = cfg.center_smoothing
        as_ = cfg.area_smoothing
        es = cfg.error_smoothing
        self.x = self.x + (rx - self.x) * cs
        self.y = self.y + (ry - self.y) * cs
        self.area = self.area + (ra - self.area) * as_
        self.error_x = self.error_x + (re - self.error_x) * es
        self.visible = True
        self.state = "LOCK"

    def _stamp_result(self, result: CameraTrackingResult, state: str, hold_left_ms: int) -> None:
        try:
            result.lock_state = state
            result.lock_hold_left_ms = int(hold_left_ms)
            result.lock_age_ms = int(max(0, int(time.time() * 1000) - self._last_state_change_ms))
            result.lock_enabled = bool(self.config.enabled)
        except Exception:
            pass

    def _draw_overlay(self, result: CameraTrackingResult) -> None:
        try:
            import cv2
        except Exception:
            return
        frame = result.frame_rgb
        try:
            h, w = frame.shape[:2]
        except Exception:
            return

        state = getattr(result, "lock_state", "LOST")
        if state == "LOCK":
            color = (255, 210, 0)      # RGB żółty
            thickness = 2
        elif state == "HOLD":
            color = (255, 150, 0)      # RGB pomarańczowy
            thickness = 2
        elif state == "DETECT":
            color = (0, 230, 80)       # RGB zielony
            thickness = 2
        else:
            color = (150, 150, 150)
            thickness = 1

        if result.visible and result.object_x and result.object_y:
            side = int((max(float(result.area), 900.0) ** 0.5) * self.config.approximate_box_scale)
            side = max(32, min(side, min(w, h)))
            x1 = max(0, int(result.object_x - side / 2))
            y1 = max(0, int(result.object_y - side / 2))
            x2 = min(w - 1, int(result.object_x + side / 2))
            y2 = min(h - 1, int(result.object_y + side / 2))
            if state == "HOLD":
                # Prosty przerywany box.
                step = 12
                for x in range(x1, x2, step * 2):
                    cv2.line(frame, (x, y1), (min(x + step, x2), y1), color, thickness)
                    cv2.line(frame, (x, y2), (min(x + step, x2), y2), color, thickness)
                for y in range(y1, y2, step * 2):
                    cv2.line(frame, (x1, y), (x1, min(y + step, y2)), color, thickness)
                    cv2.line(frame, (x2, y), (x2, min(y + step, y2)), color, thickness)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            cv2.circle(frame, (int(result.object_x), int(result.object_y)), 5, color, -1)

        hold_left = int(getattr(result, "lock_hold_left_ms", 0) or 0)
        cv2.putText(
            frame,
            f"TARGET LOCK: {state} hold={hold_left}ms err={result.error_x:+.0f}px",
            (10, max(52, min(h - 12, 56))),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
