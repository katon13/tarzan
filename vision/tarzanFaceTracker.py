# -*- coding: utf-8 -*-
"""
TARZAN - Face Tracker

Plugin twarzy dla KHR/VISION SETUP.
- nie otwiera kamery,
- nie robi cap.read() w torze CameraSession,
- analizuje klatkę dostarczoną przez CameraSession,
- czyta pełne ustawienia z tracking.face_tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vision.tarzanCameraTracker import CameraTrackingResult
from vision.tarzanTrackingState import TrackingStateFilter
from vision.tarzanVisionConfig import load_vision_settings


@dataclass
class FaceTrackerConfig:
    backend: str = "MEDIAPIPE"
    processing_max_width: int = 480
    preview_max_width: int = 640
    draw_debug: bool = True
    min_face_area: float = 1200.0
    max_face_area: float = 250000.0
    target_point: str = "FACE_CENTER"
    model_selection: int = 0
    min_detection_confidence: float = 0.55
    require_mediapipe: bool = True
    cascade_name: str = "haarcascade_frontalface_default.xml"
    haar_scale_factor: float = 1.1
    haar_min_neighbors: int = 5
    haar_flags: int = 0
    haar_min_size_w: int = 40
    haar_min_size_h: int = 40
    haar_max_size_w: int = 0
    haar_max_size_h: int = 0
    haar_equalize_hist: bool = True


class TarzanFaceTracker:
    def __init__(
        self,
        device_index: int = 0,
        frame_width: int = 640,
        frame_height: int = 360,
        project_root: Path | None = None,
        settings: dict | None = None,
        backend: str | None = None,
    ) -> None:
        self.project_root = project_root
        self.settings = settings
        if self.settings is None and project_root is not None:
            self.settings = load_vision_settings(project_root)

        self.device_index = int(device_index)
        self.frame_width = int(frame_width)
        self.frame_height = int(frame_height)
        self.cap = None
        self.cv2 = None
        self.np = None
        self.last_result = CameraTrackingResult()
        self.backend_override = backend.upper() if backend else None
        self.config = self._config_from_settings()
        self.filter = self._make_filter()
        self._mp_face_detection = None
        self._mp_detector = None
        self._haar_cascade = None
        self._backend_ready = False
        self._active_backend = self.config.backend.upper()
        self._backend_error = ""

    def _face_cfg(self) -> dict:
        return (self.settings or {}).get("tracking", {}).get("face_tracking", {}) or {}

    def _config_from_settings(self) -> FaceTrackerConfig:
        face = self._face_cfg()
        common = face.get("common", {})
        mp = face.get("mediapipe", {})
        haar = face.get("haar", {})
        # zgodność ze starym płaskim JSON
        backend = self.backend_override or face.get("active_backend", face.get("backend", "MEDIAPIPE"))
        return FaceTrackerConfig(
            backend=str(backend).upper(),
            processing_max_width=int(common.get("processing_max_width", face.get("processing_max_width", 480)) or 480),
            preview_max_width=int(common.get("preview_max_width", face.get("max_width", 640)) or 640),
            draw_debug=bool(common.get("draw_debug", face.get("draw_debug", True))),
            min_face_area=float(common.get("min_face_area", face.get("min_face_area", 1200.0))),
            max_face_area=float(common.get("max_face_area", face.get("max_face_area", 250000.0))),
            target_point=str(common.get("target_point", "FACE_CENTER")).upper(),
            model_selection=int(mp.get("model_selection", face.get("model_selection", 0))),
            min_detection_confidence=float(mp.get("min_detection_confidence", face.get("min_detection_confidence", 0.55))),
            require_mediapipe=bool(mp.get("require_installed", True)),
            cascade_name=str(haar.get("cascade_name", "haarcascade_frontalface_default.xml")),
            haar_scale_factor=float(haar.get("scale_factor", 1.1)),
            haar_min_neighbors=int(haar.get("min_neighbors", 5)),
            haar_flags=int(haar.get("flags", 0)),
            haar_min_size_w=int(haar.get("min_size_w", 40)),
            haar_min_size_h=int(haar.get("min_size_h", 40)),
            haar_max_size_w=int(haar.get("max_size_w", 0)),
            haar_max_size_h=int(haar.get("max_size_h", 0)),
            haar_equalize_hist=bool(haar.get("equalize_hist", True)),
        )

    def _make_filter(self) -> TrackingStateFilter:
        common = self._face_cfg().get("common", {})
        return TrackingStateFilter(
            center_smoothing=float(common.get("center_smoothing", 0.35)),
            area_smoothing=float(common.get("area_smoothing", 0.25)),
            visible_hysteresis_on=int(common.get("visible_hysteresis_on", 2)),
            visible_hysteresis_off=int(common.get("visible_hysteresis_off", 5)),
            hold_last_target_ms=int(common.get("hold_last_target_ms", 250)),
            max_jump_px=float(common.get("max_jump_px", 260)),
        )

    def set_target_profile(self, name: str) -> None:
        return

    def prepare_backend(self) -> None:
        """Przygotowuje bibliotekę FACE poza workerem kamery.

        MediaPipe może ładować model i zależności wolniej niż zwykły HSV.
        Wywołanie z UI/setup/start pozwala uniknąć inicjalizacji w środku cap.read().
        Błąd MediaPipe nie zamyka kamery — zostanie użyty HAAR fallback.
        """
        self._ensure_backend()

    def _ensure_backend(self) -> None:
        if self._backend_ready:
            return
        requested = self.config.backend.upper()
        self._backend_error = ""
        if requested == "MEDIAPIPE":
            try:
                import mediapipe as mp  # type: ignore
                self._mp_face_detection = mp.solutions.face_detection
                self._mp_detector = self._mp_face_detection.FaceDetection(
                    model_selection=self.config.model_selection,
                    min_detection_confidence=self.config.min_detection_confidence,
                )
                self._active_backend = "MEDIAPIPE"
                self._backend_ready = True
                return
            except Exception as exc:
                # FACE nie może zabić kamery. Brak MediaPipe albo błąd modelu
                # przełącza plugin na HAAR fallback, ale HAAR wymaga cv2, które
                # jest przypinane dopiero przez CameraSession po otwarciu kamery.
                self._backend_error = f"MEDIAPIPE ERROR -> HAAR FALLBACK: {exc}"
                if self.cv2 is None:
                    self._active_backend = "PENDING_HAAR"
                    self._backend_ready = False
                    return

        self._ensure_haar()
        if self._haar_cascade is not None and not self._haar_cascade.empty():
            self._active_backend = "HAAR"
        else:
            self._active_backend = "MEDIAPIPE_ERROR"
            if not self._backend_error:
                self._backend_error = "FACE ERROR: brak aktywnego backendu MediaPipe/Haar"
        self._backend_ready = True

    def _ensure_haar(self) -> None:
        if self._haar_cascade is not None or self.cv2 is None:
            return
        cascade_name = self.config.cascade_name
        try:
            cascade_path = str(Path(self.cv2.data.haarcascades) / cascade_name)
        except Exception:
            cascade_path = cascade_name
        self._haar_cascade = self.cv2.CascadeClassifier(cascade_path)

    def read(self) -> CameraTrackingResult:
        if self.cap is None or self.cv2 is None:
            self.last_result = CameraTrackingResult()
            return self.last_result
        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.last_result = CameraTrackingResult()
            return self.last_result
        return self.process_frame(frame)

    def process_frame(self, frame, include_frame_rgb: bool = True) -> CameraTrackingResult:
        if frame is None or self.cv2 is None:
            self.last_result = CameraTrackingResult()
            return self.last_result
        self._ensure_backend()
        try:
            if self._active_backend == "MEDIAPIPE" and self._mp_detector is not None:
                result = self._detect_mediapipe(frame)
            elif self._active_backend == "MEDIAPIPE_ERROR":
                result = self._error_result(frame)
            else:
                result = self._detect_haar(frame)
        except Exception as exc:
            self._backend_error = f"FACE PROCESS ERROR: {exc}"
            self._active_backend = "MEDIAPIPE_ERROR"
            result = self._error_result(frame)
        if not include_frame_rgb:
            result.frame_rgb = None
        self.last_result = result
        return result

    def _resize_for_processing(self, frame):
        h, w = frame.shape[:2]
        max_w = int(self.config.processing_max_width or 0)
        if max_w > 0 and w > max_w:
            process_w = max_w
            process_h = max(1, int(h * (process_w / float(w))))
            process_frame = self.cv2.resize(frame, (process_w, process_h), interpolation=self.cv2.INTER_AREA)
            return process_frame, w / float(process_w), h / float(process_h)
        return frame, 1.0, 1.0

    def _detect_mediapipe(self, frame) -> CameraTrackingResult:
        cv2 = self.cv2
        h, w = frame.shape[:2]
        frame_center_x = w / 2.0
        process_frame, sx, sy = self._resize_for_processing(frame)
        ph, pw = process_frame.shape[:2]
        rgb = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
        detections = self._mp_detector.process(rgb).detections if self._mp_detector is not None else None
        best = None
        best_area = 0.0
        if detections:
            for det in detections:
                box = det.location_data.relative_bounding_box
                x = max(0, int(box.xmin * pw))
                y = max(0, int(box.ymin * ph))
                bw = max(1, int(box.width * pw))
                bh = max(1, int(box.height * ph))
                area_full = float(bw * bh) * sx * sy
                if area_full < self.config.min_face_area or area_full > self.config.max_face_area:
                    continue
                if area_full > best_area:
                    best_area = area_full
                    best = (x, y, bw, bh)
        return self._result_from_box(frame, best, best_area, frame_center_x, sx, sy, backend="FACE_MEDIAPIPE")

    def _detect_haar(self, frame) -> CameraTrackingResult:
        cv2 = self.cv2
        h, w = frame.shape[:2]
        frame_center_x = w / 2.0
        process_frame, sx, sy = self._resize_for_processing(frame)
        gray = cv2.cvtColor(process_frame, cv2.COLOR_BGR2GRAY)
        if self.config.haar_equalize_hist:
            gray = cv2.equalizeHist(gray)
        min_size = (max(1, self.config.haar_min_size_w), max(1, self.config.haar_min_size_h))
        max_size = ()
        if self.config.haar_max_size_w > 0 and self.config.haar_max_size_h > 0:
            max_size = (self.config.haar_max_size_w, self.config.haar_max_size_h)
        faces = []
        if self._haar_cascade is not None and not self._haar_cascade.empty():
            kwargs = dict(
                scaleFactor=max(1.01, self.config.haar_scale_factor),
                minNeighbors=max(1, self.config.haar_min_neighbors),
                flags=int(self.config.haar_flags),
                minSize=min_size,
            )
            if max_size:
                kwargs["maxSize"] = max_size
            faces = self._haar_cascade.detectMultiScale(gray, **kwargs)
        best = None
        best_area = 0.0
        for x, y, bw, bh in faces:
            area_full = float(bw * bh) * sx * sy
            if area_full < self.config.min_face_area or area_full > self.config.max_face_area:
                continue
            if area_full > best_area:
                best_area = area_full
                best = (int(x), int(y), int(bw), int(bh))
        return self._result_from_box(frame, best, best_area, frame_center_x, sx, sy, backend="FACE_HAAR")

    def _error_result(self, frame) -> CameraTrackingResult:
        cv2 = self.cv2
        h, w = frame.shape[:2]
        if self.config.draw_debug:
            cv2.putText(frame, self._backend_error[:80], (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return CameraTrackingResult(False, 0.0, 0.0, 0.0, w / 2.0, w, h, 0.0, frame_rgb)

    def _result_from_box(self, frame, box, area: float, frame_center_x: float, sx: float, sy: float, backend: str) -> CameraTrackingResult:
        cv2 = self.cv2
        h, w = frame.shape[:2]
        visible_raw = box is not None
        object_x = 0.0
        object_y = 0.0
        draw_box = None
        if box is not None:
            x, y, bw, bh = box
            x1 = int(x * sx)
            y1 = int(y * sy)
            x2 = int((x + bw) * sx)
            y2 = int((y + bh) * sy)
            object_x = (x1 + x2) / 2.0
            object_y = (y1 + y2) / 2.0
            draw_box = (x1, y1, x2, y2)
        filtered = self.filter.update(visible_raw, object_x, object_y, area)
        visible = filtered.visible
        if visible:
            object_x = filtered.x
            object_y = filtered.y
            area = filtered.area
        if self.config.draw_debug:
            if draw_box is not None and visible:
                x1, y1, x2, y2 = draw_box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 255), 2)
                cv2.circle(frame, (int(object_x), int(object_y)), 5, (0, 255, 255), -1)
            cv2.line(frame, (int(frame_center_x), 0), (int(frame_center_x), h), (255, 255, 255), 1)
            error_x_dbg = object_x - frame_center_x if visible else 0.0
            cv2.putText(frame, f"{backend} visible={int(visible)} error_x={error_x_dbg:+.1f} area={area:.0f}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        error_x = object_x - frame_center_x if visible else 0.0
        display_frame = frame
        max_w = int(self.config.preview_max_width or 0)
        if max_w > 0 and w > max_w:
            display_w = max_w
            display_h = max(1, int(h * (display_w / float(w))))
            display_frame = cv2.resize(frame, (display_w, display_h), interpolation=cv2.INTER_AREA)
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        return CameraTrackingResult(visible, error_x, object_x, object_y, frame_center_x, w, h, area, frame_rgb)

    def close(self) -> None:
        if self._mp_detector is not None:
            try:
                self._mp_detector.close()
            except Exception:
                pass
        self._mp_detector = None
        self._backend_ready = False
