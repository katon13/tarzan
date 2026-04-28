# -*- coding: utf-8 -*-
"""
TARZAN - Camera Tracker

Kamera USB → wykrycie obiektu → error_x.

Zasada:
kamera nie steruje osią.
kamera dostarcza tylko error_x + visible.
KHR robi korektę A(t).

Wymaga:
python -m pip install opencv-python numpy pillow
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import contextlib
import os

from vision.tarzanCameraControls import apply_camera_settings, read_camera_state, fourcc_to_int
from vision.tarzanTrackingState import TrackingStateFilter
from vision.tarzanVisionConfig import load_vision_settings, odd_kernel, target_profile_from_settings


@contextlib.contextmanager
def _suppress_stderr():
    try:
        fd = os.open(os.devnull, os.O_WRONLY)
        old = os.dup(2)
        os.dup2(fd, 2)
        os.close(fd)
        yield
    finally:
        try:
            os.dup2(old, 2)
            os.close(old)
        except Exception:
            pass


@dataclass
class CameraTrackingResult:
    visible: bool = False
    error_x: float = 0.0
    object_x: float = 0.0
    object_y: float = 0.0
    frame_center_x: float = 0.0
    frame_width: int = 0
    frame_height: int = 0
    area: float = 0.0
    frame_rgb: object | None = None
    # Global TargetLock / przyspawanie celu. Pola są opcjonalne dla starych pluginów.
    lock_state: str = "OFF"
    lock_hold_left_ms: int = 0
    lock_age_ms: int = 0
    lock_enabled: bool = False


class TarzanCameraTracker:
    def __init__(
        self,
        device_index: int = 0,
        frame_width: int = 640,
        frame_height: int = 360,
        min_area: float = 500.0,
        project_root: Path | None = None,
    ) -> None:
        self.project_root = project_root
        self.settings = None
        self.profile = None

        self.device_index = int(device_index)
        self.frame_width = int(frame_width)
        self.frame_height = int(frame_height)
        self.min_area = float(min_area)

        self.cap = None
        self.cv2 = None
        self.np = None

        self.camera_state = {}
        self.last_result = CameraTrackingResult()

        self.filter = TrackingStateFilter()

        if project_root is not None:
            self.load_settings(project_root)

    def load_settings(self, project_root: Path) -> None:
        self.settings = load_vision_settings(project_root)
        discovery = self.settings.get("camera_discovery", {})
        camera_cfg = self.settings.get("camera_device", {})
        tracking_cfg = self.settings.get("tracking", {})
        filter_cfg = tracking_cfg.get("target_filter", {})

        self.device_index = int(discovery.get("preferred_index", self.device_index))
        self.frame_width = int(camera_cfg.get("frame_width", self.frame_width))
        self.frame_height = int(camera_cfg.get("frame_height", self.frame_height))
        self.profile = target_profile_from_settings(self.settings)

        self.min_area = float(self.profile.min_area)

        self.filter = TrackingStateFilter(
            center_smoothing=float(filter_cfg.get("center_smoothing", 0.35)),
            area_smoothing=float(filter_cfg.get("area_smoothing", 0.25)),
            visible_hysteresis_on=int(filter_cfg.get("visible_hysteresis_on", 2)),
            visible_hysteresis_off=int(filter_cfg.get("visible_hysteresis_off", 5)),
            hold_last_target_ms=int(filter_cfg.get("hold_last_target_ms", 250)),
            max_jump_px=float(filter_cfg.get("max_jump_px", 220)),
        )

    def set_target_profile(self, name: str) -> None:
        if self.settings is None:
            return
        self.profile = target_profile_from_settings(self.settings, name)

    def open(self, allow_fallback: bool = False, fast_open: bool = False, read_state: bool = True) -> tuple[bool, str]:
        try:
            import cv2
            import numpy as np
        except Exception as exc:
            return False, f"Brak OpenCV/numpy: {exc}"

        self.cv2 = cv2
        self.np = np
        try:
            cv2.setLogLevel(0)
        except Exception:
            pass

        backend_name = "DSHOW"
        if self.settings:
            backend_name = self.settings.get("camera_discovery", {}).get("preferred_backend", "DSHOW")

        backend = getattr(cv2, f"CAP_{backend_name}", None)

        with _suppress_stderr():
            if backend is not None:
                self.cap = cv2.VideoCapture(self.device_index, backend)
            else:
                self.cap = cv2.VideoCapture(self.device_index)

            # Fallback tylko na żądanie. W trybie operatorskim ma być szybko.
            if allow_fallback and (not self.cap or not self.cap.isOpened()):
                self.cap = cv2.VideoCapture(self.device_index)

        if not self.cap or not self.cap.isOpened():
            return False, f"Nie można otworzyć kamery index={self.device_index} backend={backend_name}"

        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        camera_cfg = self.settings.get("camera_device", {}) if self.settings else {}

        if fast_open:
            # TRYB LIVE / KHR:
            # OpenCV działa szybko, ale bez ustawienia formatu kamera potrafi wrócić do 1920x1080.
            # Dlatego robimy tylko minimalny, roboczy format LIVE w wątku kamery, nigdy w UI:
            # FOURCC + WIDTH + HEIGHT + FPS. Bez UVC exposure/focus/WB i bez cap.get().
            try:
                fourcc = camera_cfg.get("fourcc")
                if fourcc:
                    self.cap.set(cv2.CAP_PROP_FOURCC, fourcc_to_int(cv2, fourcc))
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_cfg.get("frame_width", self.frame_width)))
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_cfg.get("frame_height", self.frame_height)))
                self.cap.set(cv2.CAP_PROP_FPS, float(camera_cfg.get("fps", 15)))
            except Exception:
                pass
        else:
            # TRYB SERWISOWY:
            # Pełne ustawienia kamery są świadomie wolniejsze i wykonywane tylko w oknie ustawień.
            if self.settings:
                apply_camera_settings(self.cap, cv2, camera_cfg)
            else:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        warmup = 0 if fast_open else 5
        if self.settings:
            warmup = 0 if fast_open else int(self.settings.get("camera_discovery", {}).get("warmup_frames", 5))
        for _ in range(max(0, warmup)):
            self.cap.read()

        if read_state and not fast_open:
            self.camera_state = read_camera_state(self.cap, cv2)
        else:
            self.camera_state = {}

        mode = "FAST" if fast_open else "FULL"
        return True, f"Kamera otwarta {mode} index={self.device_index}"

    def close(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = None

    def read(self) -> CameraTrackingResult:
        if self.cap is None or self.cv2 is None:
            self.last_result = CameraTrackingResult()
            return self.last_result

        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.last_result = CameraTrackingResult()
            return self.last_result

        return self.process_frame(frame, include_frame_rgb=True)

    def process_frame(self, frame, include_frame_rgb: bool = True) -> CameraTrackingResult:
        """Analizuje klatkę dostarczoną przez CameraSession.

        Dzięki temu tylko CameraSession wykonuje cap.read(); tracker pozostaje
        wyłącznie pluginem analizy obrazu.
        """
        result = self._detect_object(frame, include_frame_rgb=include_frame_rgb)
        self.last_result = result
        return result

    def _detect_object(self, frame, include_frame_rgb: bool = True) -> CameraTrackingResult:
        cv2 = self.cv2
        np = self.np

        h, w = frame.shape[:2]
        frame_center_x = w / 2.0

        profile = self.profile
        if profile is None:
            if self.settings:
                profile = target_profile_from_settings(self.settings)
            else:
                raise RuntimeError("Brak profilu trackingu")

        tracking_cfg = self.settings.get("tracking", {}) if self.settings else {}
        preview_cfg = tracking_cfg.get("preview", {})
        processing_max_width = int(preview_cfg.get("processing_max_width", 640) or 0)
        preview_max_width = int(preview_cfg.get("max_width", 640) or 0)

        raw_profile = {}
        try:
            raw_profile = tracking_cfg.get("target_profiles", {}).get(profile.name, {}) if profile is not None else {}
        except Exception:
            raw_profile = {}
        color_enabled = bool(raw_profile.get("color_enabled", True))
        shape_enabled = bool(raw_profile.get("shape_enabled", False))
        shape_cfg = raw_profile.get("shape", {}) or {}
        selection_cfg = raw_profile.get("selection", {}) or {}
        prefer_center = bool(selection_cfg.get("prefer_center", False))

        # Przetwarzanie działa na małej kopii, ale wynik/error_x wraca w skali pełnego kadru.
        process_frame = frame
        scale_to_full_x = 1.0
        scale_to_full_y = 1.0
        if processing_max_width > 0 and w > processing_max_width:
            process_w = processing_max_width
            process_h = max(1, int(h * (process_w / float(w))))
            process_frame = cv2.resize(frame, (process_w, process_h), interpolation=cv2.INTER_AREA)
            scale_to_full_x = w / float(process_w)
            scale_to_full_y = h / float(process_h)

        ph, pw = process_frame.shape[:2]

        roi_offset_x = 0
        roi_offset_y = 0
        working = process_frame

        roi_cfg = tracking_cfg.get("roi", {})
        if tracking_cfg.get("roi_enabled", False):
            rx = int(float(roi_cfg.get("x", 0.0)) * pw)
            ry = int(float(roi_cfg.get("y", 0.0)) * ph)
            rw = int(float(roi_cfg.get("w", 1.0)) * pw)
            rh = int(float(roi_cfg.get("h", 1.0)) * ph)
            rx = max(0, min(pw - 1, rx))
            ry = max(0, min(ph - 1, ry))
            rw = max(1, min(pw - rx, rw))
            rh = max(1, min(ph - ry, rh))
            working = process_frame[ry:ry+rh, rx:rx+rw]
            roi_offset_x = rx
            roi_offset_y = ry

        if profile.blur_kernel > 1:
            blur_k = odd_kernel(profile.blur_kernel)
            working = cv2.GaussianBlur(working, (blur_k, blur_k), 0)

        if color_enabled:
            hsv = cv2.cvtColor(working, cv2.COLOR_BGR2HSV)

            mask = None
            for item in profile.hsv_ranges:
                lower = np.array([item.h_min, item.s_min, item.v_min])
                upper = np.array([item.h_max, item.s_max, item.v_max])
                current = cv2.inRange(hsv, lower, upper)
                mask = current if mask is None else cv2.bitwise_or(mask, current)
        else:
            # Tryb kształtu bez koloru: cały obraz jako maska robocza po grayscale.
            gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
            _thr, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        open_k = odd_kernel(profile.morph_open_kernel)
        close_k = odd_kernel(profile.morph_close_kernel)

        if open_k > 1:
            kernel = np.ones((open_k, open_k), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        if close_k > 1:
            kernel = np.ones((close_k, close_k), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_score = -1.0

        area_scale = scale_to_full_x * scale_to_full_y

        for contour in contours:
            area_small = float(cv2.contourArea(contour))
            area_full = area_small * area_scale
            if area_full < profile.min_area or area_full > profile.max_area:
                continue

            x, y, bw, bh = cv2.boundingRect(contour)
            rect_area = float(max(1, bw * bh))
            extent = area_small / rect_area

            hull = cv2.convexHull(contour)
            hull_area = float(max(1.0, cv2.contourArea(hull)))
            solidity = area_small / hull_area

            if solidity < profile.min_solidity or extent < profile.min_extent:
                continue

            perimeter = float(cv2.arcLength(contour, True))
            epsilon_factor = float(shape_cfg.get("approx_epsilon_factor", 0.04))
            approx = cv2.approxPolyDP(contour, epsilon_factor * perimeter, True) if perimeter > 0 else contour
            vertices = int(len(approx))
            aspect = float(bw) / float(max(1, bh))
            circularity = float(4.0 * 3.141592653589793 * area_small / max(1.0, perimeter * perimeter)) if perimeter > 0 else 0.0

            if shape_enabled:
                shape_type = str(shape_cfg.get("type", "ANY")).upper()
                min_vertices = int(shape_cfg.get("min_vertices", 0))
                max_vertices = int(shape_cfg.get("max_vertices", 99))
                aspect_min = float(shape_cfg.get("aspect_ratio_min", 0.2))
                aspect_max = float(shape_cfg.get("aspect_ratio_max", 5.0))
                circ_min = float(shape_cfg.get("min_circularity", 0.0))
                circ_max = float(shape_cfg.get("max_circularity", 1.0))

                if vertices < min_vertices or vertices > max_vertices:
                    continue
                if aspect < aspect_min or aspect > aspect_max:
                    continue
                if circularity < circ_min or circularity > circ_max:
                    continue

                if shape_type == "TRIANGLE" and vertices != 3:
                    continue
                if shape_type == "SQUARE":
                    if vertices != 4 or not (0.75 <= aspect <= 1.33):
                        continue
                if shape_type == "RECTANGLE" and vertices != 4:
                    continue
                if shape_type == "CIRCLE" and circularity < max(0.65, circ_min):
                    continue
                if shape_type == "STAR" and not (8 <= vertices <= 14):
                    continue

            if prefer_center:
                cx_small = x + bw / 2.0 + roi_offset_x
                cy_small = y + bh / 2.0 + roi_offset_y
                frame_cx_small = pw / 2.0
                frame_cy_small = ph / 2.0
                dist = ((cx_small - frame_cx_small) ** 2 + (cy_small - frame_cy_small) ** 2) ** 0.5
                center_score = 1.0 / (1.0 + dist)
                score = area_full * 0.3 + center_score * 100000.0
            else:
                score = area_full if profile.prefer_largest_contour else solidity * extent * area_full
            if score > best_score:
                best_score = score
                best = (contour, area_full, x, y, bw, bh, solidity, extent)

        visible_raw = False
        object_x = 0.0
        object_y = 0.0
        area = 0.0
        draw_box = None

        if best is not None:
            contour, area, x, y, bw, bh, solidity, extent = best
            m = cv2.moments(contour)
            if m["m00"] != 0:
                object_x_small = float(m["m10"] / m["m00"]) + roi_offset_x
                object_y_small = float(m["m01"] / m["m00"]) + roi_offset_y
                object_x = object_x_small * scale_to_full_x
                object_y = object_y_small * scale_to_full_y
                visible_raw = True

                x1 = int((x + roi_offset_x) * scale_to_full_x)
                y1 = int((y + roi_offset_y) * scale_to_full_y)
                x2 = int((x + roi_offset_x + bw) * scale_to_full_x)
                y2 = int((y + roi_offset_y + bh) * scale_to_full_y)
                draw_box = (x1, y1, x2, y2)

        filtered = self.filter.update(visible_raw, object_x, object_y, area)
        visible = filtered.visible
        if visible:
            object_x = filtered.x
            object_y = filtered.y
            area = filtered.area

        # Rysunek robimy na pełnej klatce, ale zwracamy do UI zmniejszony podgląd.
        if draw_box is not None and visible:
            x1, y1, x2, y2 = draw_box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (int(object_x), int(object_y)), 6, (0, 255, 255), -1)

        cv2.line(frame, (int(frame_center_x), 0), (int(frame_center_x), h), (255, 255, 255), 1)

        error_x = object_x - frame_center_x if visible else 0.0

        cv2.putText(
            frame,
            f"profile={profile.name} visible={int(visible)} error_x={error_x:+.1f}",
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        display_frame = frame
        if preview_max_width > 0 and w > preview_max_width:
            display_w = preview_max_width
            display_h = max(1, int(h * (display_w / float(w))))
            display_frame = cv2.resize(frame, (display_w, display_h), interpolation=cv2.INTER_AREA)

        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB) if include_frame_rgb else None

        return CameraTrackingResult(
            visible=visible,
            error_x=error_x,
            object_x=object_x,
            object_y=object_y,
            frame_center_x=frame_center_x,
            frame_width=w,
            frame_height=h,
            area=area,
            frame_rgb=frame_rgb,
        )
