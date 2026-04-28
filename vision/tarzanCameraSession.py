# -*- coding: utf-8 -*-
"""
TARZAN - Camera Session

Czysty rdzeń live kamery dla KHR.

Zasada architektury:
- jeden VideoCapture,
- jeden worker thread,
- open() i read() należą do tej samej sesji,
- brak UI,
- brak scan kamer,
- brak pełnych ustawień serwisowych UVC,
- KHR pobiera tylko latest_frame / latest_result / error_x.
"""

from __future__ import annotations

from pathlib import Path
import contextlib
import os
import threading
import time
from dataclasses import dataclass

from vision.tarzanCameraTracker import CameraTrackingResult, TarzanCameraTracker
from vision.tarzanVisionConfig import load_vision_settings


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
class CameraSessionConfig:
    device_index: int = 0
    backend: str = "DSHOW"
    frame_width: int = 640
    frame_height: int = 360
    fps: int = 15
    fourcc: str = "MJPG"
    target_profile: str = "RED_OBJECT"
    min_area: float = 500.0
    live_fps: int = 15
    detect_every_n: int = 2
    tracking_start_after_frames: int = 3


class CameraSession:
    """
    Minimalna sesja live kamery.

    Start jest rozdzielony:
    1) VideoCapture + pierwszy obraz,
    2) dopiero potem lazy-start trackera.

    Inicjacja kamery nie jest blokowana przez HSV / contours / error_x.
    """

    def __init__(self, project_root: Path, profile_name: str | None = None, tick_profile_callback=None, frame_output_enabled: bool = False) -> None:
        self.project_root = project_root
        self.profile_name = profile_name
        self.settings = load_vision_settings(project_root)
        self.config = self._config_from_settings(profile_name)

        self.cv2 = None
        self.np = None
        self.cap = None
        self.tracker: TarzanCameraTracker | None = None

        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._opening = False
        self._opened = False
        self._tracking_ready = False
        self._tracking_enabled = False
        self._message = "Kamera nieaktywna"
        self._latest_result = CameraTrackingResult()
        self._latest_frame = None
        self._worker_tick_ms = 0.0
        self._tick_profile_callback = tick_profile_callback
        self._frame_output_enabled = bool(frame_output_enabled)

    def reload_config_from_json(self) -> None:
        """Odświeża ustawienia startu kamery bez dotykania sterownika.

        Każdy OPEN CAMERA ma brać aktualny data/khr/vision_settings.json.
        To nie wykonuje scan, cap.set(), read_state ani apply.
        """
        self.settings = load_vision_settings(self.project_root)
        self.config = self._config_from_settings(self.profile_name)

    def set_frame_output_enabled(self, enabled: bool) -> None:
        """Włącza/wyłącza produkowanie frame_rgb dla UI.

        Przy wyłączonym podglądzie worker czyta kamerę, ale nie robi cvtColor
        tylko po to, żeby UI mogło narysować obraz.
        """
        with self._lock:
            self._frame_output_enabled = bool(enabled)
            if not enabled:
                self._latest_frame = None
                if self._latest_result is not None:
                    self._latest_result.frame_rgb = None

    def _config_from_settings(self, profile_name: str | None = None) -> CameraSessionConfig:
        discovery = self.settings.get("camera_discovery", {})
        camera = self.settings.get("camera_device", {})
        tracking = self.settings.get("tracking", {})
        active_target = profile_name or tracking.get("active_target", "RED_OBJECT")
        active_profile = tracking.get("target_profiles", {}).get(active_target, {})
        preview = tracking.get("preview", {})

        return CameraSessionConfig(
            device_index=int(discovery.get("preferred_index", 0)),
            backend=str(discovery.get("preferred_backend", "DSHOW")),
            frame_width=int(camera.get("frame_width", 640)),
            frame_height=int(camera.get("frame_height", 360)),
            fps=int(camera.get("fps", 15)),
            fourcc=str(camera.get("fourcc", "MJPG")),
            target_profile=str(active_target),
            min_area=float(active_profile.get("min_area", 500.0)),
            live_fps=max(1, int(preview.get("live_fps", camera.get("fps", 15)) or 15)),
            detect_every_n=max(1, int(preview.get("detect_every_n", 2) or 2)),
            tracking_start_after_frames=max(0, int(preview.get("tracking_start_after_frames", 3) or 3)),
        )

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return bool(thread is not None and thread.is_alive())

    @property
    def is_open(self) -> bool:
        with self._lock:
            return bool(self._opened)

    @property
    def is_opening(self) -> bool:
        with self._lock:
            return bool(self._opening)

    @property
    def tracking_ready(self) -> bool:
        with self._lock:
            return bool(self._tracking_ready)

    @property
    def tracking_enabled(self) -> bool:
        with self._lock:
            return bool(self._tracking_enabled)

    @property
    def message(self) -> str:
        with self._lock:
            return self._message

    @property
    def latest_result(self) -> CameraTrackingResult:
        with self._lock:
            return self._latest_result

    @property
    def latest_frame(self):
        with self._lock:
            return self._latest_frame

    @property
    def error_x(self) -> float:
        return float(self.latest_result.error_x)

    @property
    def worker_tick_ms(self) -> float:
        with self._lock:
            return float(self._worker_tick_ms)

    def open_once(self) -> None:
        """Startuje sesję tylko raz. Nie blokuje UI."""
        if self.is_running or self.is_opening or self.is_open:
            return

        # Twarda zasada TARZAN KHR:
        # każdy OPEN CAMERA bierze aktualny JSON, ale nie konsultuje go ze sterownikiem.
        self.reload_config_from_json()

        self._stop.clear()
        with self._lock:
            self._opening = True
            self._opened = False
            self._tracking_ready = False
            self._tracking_enabled = False
            self._message = "Kamera: otwieranie LIVE..."
            self._latest_result = CameraTrackingResult()
            self._latest_frame = None
            self._worker_tick_ms = 0.0

        self._thread = threading.Thread(
            target=self._read_loop,
            name="TARZAN_CAMERA_SESSION",
            daemon=True,
        )
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.8)
        self._thread = None
        self._release_cap()
        with self._lock:
            self._opening = False
            self._opened = False
            self._tracking_ready = False
            self._tracking_enabled = False
            self._message = "Kamera nieaktywna"
            self._latest_result = CameraTrackingResult()
            self._latest_frame = None
            self._worker_tick_ms = 0.0

    def _open_capture(self) -> tuple[bool, str]:
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

        backend_value = getattr(cv2, f"CAP_{self.config.backend}", None)
        with _suppress_stderr():
            if backend_value is not None:
                cap = cv2.VideoCapture(self.config.device_index, backend_value)
            else:
                cap = cv2.VideoCapture(self.config.device_index)

        if cap is None or not cap.isOpened():
            return False, f"Nie można otworzyć kamery index={self.config.device_index} backend={self.config.backend}"

        # NORMALNA PRACA KHR: zero cap.set(), zero read_state(), zero apply.
        # Kamera była ustawiona wcześniej w trybie serwisowym; tutaj tylko otwieramy i czytamy.
        self.cap = cap
        return True, f"CameraSession LIVE READ_ONLY index={self.config.device_index} backend={self.config.backend}"

    def start_tracking(self) -> None:
        """Włącza tracking dopiero po świadomym START KHR."""
        with self._lock:
            self._tracking_enabled = True
            if self._opened:
                self._message = f"CameraSession LIVE | tracking pending index={self.config.device_index} backend={self.config.backend}"

    def stop_tracking(self) -> None:
        """Wyłącza tracking i zostawia sam podgląd kamery."""
        with self._lock:
            self._tracking_enabled = False
            self._tracking_ready = False
            if self._opened:
                self._message = f"CameraSession LIVE PREVIEW_ONLY index={self.config.device_index} backend={self.config.backend}"

    def _ensure_tracker(self) -> None:
        if self.tracker is not None:
            return
        # Tracker nie może podczas START KHR ponownie ładować JSON ani otwierać kamery.
        # Dostaje gotowe ustawienia sesji i istniejący cap. Algorytm śledzenia zostaje bez zmian.
        tracker = TarzanCameraTracker(
            device_index=self.config.device_index,
            frame_width=self.config.frame_width,
            frame_height=self.config.frame_height,
            min_area=self.config.min_area,
            project_root=None,
        )
        tracker.settings = self.settings
        tracker.device_index = self.config.device_index
        tracker.frame_width = self.config.frame_width
        tracker.frame_height = self.config.frame_height
        tracker.min_area = self.config.min_area
        tracker.cv2 = self.cv2
        tracker.np = self.np
        tracker.cap = self.cap
        tracker.set_target_profile(self.config.target_profile)
        self.tracker = tracker
        with self._lock:
            self._tracking_ready = True
            self._message = f"CameraSession LIVE + TRACKING index={self.config.device_index} backend={self.config.backend}"

    def _plain_read_frame(self) -> CameraTrackingResult:
        if self.cap is None or self.cv2 is None:
            return CameraTrackingResult()
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return CameraTrackingResult()
        h, w = frame.shape[:2]
        with self._lock:
            want_frame = bool(self._frame_output_enabled)
        frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB) if want_frame else None
        return CameraTrackingResult(
            visible=False,
            error_x=0.0,
            object_x=0.0,
            object_y=0.0,
            frame_center_x=w / 2.0,
            frame_width=w,
            frame_height=h,
            area=0.0,
            frame_rgb=frame_rgb,
        )

    def _read_loop(self) -> None:
        try:
            ok, msg = self._open_capture()
            with self._lock:
                self._opening = False
                self._opened = ok
                self._message = msg

            if not ok:
                return

            frame_period = 1.0 / max(1, self.config.live_fps)
            next_t = time.perf_counter()
            frame_no = 0

            while not self._stop.is_set():
                frame_no += 1
                tick0 = time.perf_counter()
                try:
                    if not self.tracking_enabled:
                        # OPEN/PREVIEW: tylko obraz. Zero trackera, zero HSV, zero contours.
                        result = self._plain_read_frame()
                    elif frame_no <= self.config.tracking_start_after_frames:
                        # Po START KHR dajemy kamerze kilka czystych klatek przed pierwszą detekcją.
                        result = self._plain_read_frame()
                    elif (frame_no % self.config.detect_every_n) == 0:
                        self._ensure_tracker()
                        result = self.tracker.read() if self.tracker is not None else self._plain_read_frame()
                        with self._lock:
                            want_frame = bool(self._frame_output_enabled)
                        if not want_frame:
                            result.frame_rgb = None
                    else:
                        # Między detekcjami aktualizujemy obraz bez liczenia error_x.
                        plain = self._plain_read_frame()
                        previous = self.latest_result
                        result = CameraTrackingResult(
                            visible=previous.visible,
                            error_x=previous.error_x,
                            object_x=previous.object_x,
                            object_y=previous.object_y,
                            frame_center_x=plain.frame_center_x,
                            frame_width=plain.frame_width,
                            frame_height=plain.frame_height,
                            area=previous.area,
                            frame_rgb=plain.frame_rgb,
                        )
                except Exception as exc:
                    result = CameraTrackingResult()
                    with self._lock:
                        self._message = f"Błąd CameraSession.read: {exc}"

                tick_s = time.perf_counter() - tick0
                with self._lock:
                    self._latest_result = result
                    self._latest_frame = result.frame_rgb
                    self._worker_tick_ms = tick_s * 1000.0

                if self._tick_profile_callback is not None:
                    try:
                        self._tick_profile_callback("KHR_CAMERA.worker_tick", tick_s)
                    except Exception:
                        pass

                next_t += frame_period
                sleep_s = next_t - time.perf_counter()
                if sleep_s <= 0:
                    next_t = time.perf_counter()
                    sleep_s = 0.001
                self._stop.wait(min(sleep_s, frame_period))
        finally:
            self._release_cap()
            with self._lock:
                self._opening = False
                self._opened = False
                self._tracking_ready = False
                self._tracking_enabled = False

    def _release_cap(self) -> None:
        cap = self.cap
        self.cap = None
        if self.tracker is not None:
            self.tracker.cap = None
        self.tracker = None
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
