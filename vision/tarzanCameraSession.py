# -*- coding: utf-8 -*-
"""
TARZAN - Camera Session

Globalny pipeline live kamery dla KHR.

Zasada architektury po poprawce:
- jeden VideoCapture,
- osobny CAMERA READER worker: tylko cap.read() + lekki frame_rgb dla UI,
- osobny TRACKING worker: HSV / HAAR / MEDIAPIPE na kopii ostatniej klatki,
- brak UI,
- brak scan kamer,
- brak pełnych ustawień serwisowych UVC,
- KHR pobiera tylko latest_result / error_x.

Najważniejsze: tracking nie może zatrzymać czytania kamery.
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
try:
    from vision.tarzanFaceTracker import TarzanFaceTracker
except Exception:
    TarzanFaceTracker = None


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
    tracking_mode: str = "HSV_COLOR"
    min_area: float = 500.0
    live_fps: int = 15
    detect_every_n: int = 2
    tracking_start_after_frames: int = 3


class CameraSession:
    """
    Sesja live kamery dla KHR.

    Ten obiekt ma dwa niezależne tory:
    1. CAMERA READER: utrzymuje świeżą klatkę z kamery.
    2. TRACKING: analizuje ostatnią klatkę i aktualizuje error_x/visible.

    KHR i UI są konsumentami stanu. Nie czytają kamery i nie wykonują trackingu.
    """

    def __init__(self, project_root: Path, profile_name: str | None = None, tick_profile_callback=None, frame_output_enabled: bool = False, tracking_mode: str | None = None) -> None:
        self.project_root = project_root
        self.profile_name = profile_name
        self._tracking_mode_override = tracking_mode
        self.settings = load_vision_settings(project_root)
        self.config = self._config_from_settings(profile_name)

        self.cv2 = None
        self.np = None
        self.cap = None
        self.tracker = None

        self._lock = threading.RLock()
        self._frame_lock = threading.RLock()
        self._stop = threading.Event()
        self._reader_thread: threading.Thread | None = None
        self._tracking_thread: threading.Thread | None = None

        self._opening = False
        self._opened = False
        self._tracking_ready = False
        self._tracking_enabled = False
        self._pending_tracking_mode: str | None = None
        self._pending_tracker = None
        self._active_tracking_mode = str(self.config.tracking_mode or "HSV_COLOR").upper()
        self._message = "Kamera nieaktywna"

        self._latest_result = CameraTrackingResult()
        self._latest_frame = None
        self._latest_bgr_frame = None
        self._latest_frame_no = 0
        self._last_tracked_frame_no = 0

        self._worker_tick_ms = 0.0
        self._reader_tick_ms = 0.0
        self._tracking_tick_ms = 0.0
        self._tick_profile_callback = tick_profile_callback
        self._frame_output_enabled = bool(frame_output_enabled)

    # ------------------------------------------------------------------
    # CONFIG / PUBLIC API
    # ------------------------------------------------------------------
    def reload_config_from_json(self) -> None:
        self.settings = load_vision_settings(self.project_root)
        self.config = self._config_from_settings(self.profile_name)

    def set_frame_output_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._frame_output_enabled = bool(enabled)
            if not enabled:
                self._latest_frame = None
                if self._latest_result is not None:
                    self._latest_result.frame_rgb = None

    def set_tracking_mode(self, mode: str) -> None:
        mode = (mode or "HSV_COLOR").strip().upper()
        if mode not in ("HSV_COLOR", "FACE_HAAR", "FACE_MEDIAPIPE"):
            mode = "HSV_COLOR"

        prepared_tracker = None
        if mode == "FACE_MEDIAPIPE" and TarzanFaceTracker is not None:
            try:
                prepared_tracker = TarzanFaceTracker(
                    device_index=self.config.device_index,
                    frame_width=self.config.frame_width,
                    frame_height=self.config.frame_height,
                    project_root=None,
                    settings=self.settings,
                    backend="MEDIAPIPE",
                )
                prepare = getattr(prepared_tracker, "prepare_backend", None)
                if callable(prepare):
                    prepare()
            except Exception:
                prepared_tracker = None

        with self._lock:
            self._tracking_mode_override = mode
            self._pending_tracking_mode = mode
            self._pending_tracker = prepared_tracker
            if self._opened:
                self._message = f"CameraSession LIVE | pending plugin={mode} | camera unchanged"

    def request_tracking_mode(self, mode: str) -> None:
        self.set_tracking_mode(mode)

    @property
    def tracking_mode(self) -> str:
        with self._lock:
            return str(self._pending_tracking_mode or self.config.tracking_mode)

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
            tracking_mode=str(self._tracking_mode_override or tracking.get("tracking_mode", "HSV_COLOR")),
            min_area=float(active_profile.get("min_area", 500.0)),
            live_fps=max(1, int(preview.get("live_fps", camera.get("fps", 15)) or 15)),
            detect_every_n=max(1, int(preview.get("detect_every_n", 2) or 2)),
            tracking_start_after_frames=max(0, int(preview.get("tracking_start_after_frames", 3) or 3)),
        )

    @property
    def is_running(self) -> bool:
        thread = self._reader_thread
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
            return float(max(self._reader_tick_ms, self._tracking_tick_ms))

    @property
    def reader_tick_ms(self) -> float:
        with self._lock:
            return float(self._reader_tick_ms)

    @property
    def tracking_tick_ms_value(self) -> float:
        with self._lock:
            return float(self._tracking_tick_ms)

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------
    def open_once(self) -> None:
        """Startuje sesję tylko raz. Nie blokuje UI."""
        if self.is_running or self.is_opening or self.is_open:
            return

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
            self._latest_bgr_frame = None
            self._latest_frame_no = 0
            self._last_tracked_frame_no = 0
            self._reader_tick_ms = 0.0
            self._tracking_tick_ms = 0.0

        self._reader_thread = threading.Thread(
            target=self._camera_reader_loop,
            name="TARZAN_CAMERA_READER",
            daemon=True,
        )
        self._reader_thread.start()

    def close(self) -> None:
        self._stop.set()
        for thread in (self._tracking_thread, self._reader_thread):
            if thread is not None and thread.is_alive():
                thread.join(timeout=1.5)
        self._tracking_thread = None
        self._reader_thread = None
        self._release_cap()
        self._close_tracker()
        with self._lock:
            self._opening = False
            self._opened = False
            self._tracking_ready = False
            self._tracking_enabled = False
            self._message = "Kamera nieaktywna"
            self._latest_result = CameraTrackingResult()
            self._latest_frame = None
            self._latest_bgr_frame = None
            self._worker_tick_ms = 0.0
            self._reader_tick_ms = 0.0
            self._tracking_tick_ms = 0.0

    def start_tracking(self) -> None:
        with self._lock:
            self._tracking_enabled = True
            if self._opened:
                self._message = f"CameraSession LIVE | tracking ON index={self.config.device_index} backend={self.config.backend}"
        self._ensure_tracking_thread()

    def stop_tracking(self) -> None:
        with self._lock:
            self._tracking_enabled = False
            self._tracking_ready = False
            if self._opened:
                self._message = f"CameraSession LIVE PREVIEW_ONLY index={self.config.device_index} backend={self.config.backend}"

    # ------------------------------------------------------------------
    # CAMERA READER WORKER: ONLY CAP.READ
    # ------------------------------------------------------------------
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

        # Minimalne ustawienie formatu LIVE. Bez exposure/focus/WB/read_state.
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        try:
            fourcc = self.config.fourcc
            if fourcc and len(str(fourcc)) == 4:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*str(fourcc)))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.config.frame_width))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.config.frame_height))
            cap.set(cv2.CAP_PROP_FPS, float(self.config.fps))
        except Exception:
            pass

        self.cap = cap
        return True, f"CameraSession LIVE | reader only index={self.config.device_index} backend={self.config.backend}"

    def _camera_reader_loop(self) -> None:
        try:
            ok, msg = self._open_capture()
            with self._lock:
                self._opening = False
                self._opened = ok
                self._message = msg
            if not ok:
                return

            self._ensure_tracking_thread()
            frame_period = 1.0 / max(1, self.config.live_fps)
            next_t = time.perf_counter()

            while not self._stop.is_set():
                tick0 = time.perf_counter()
                frame = self._read_bgr_frame()
                if frame is not None:
                    plain = self._plain_result_from_frame(frame)
                    with self._frame_lock:
                        self._latest_bgr_frame = frame
                        self._latest_frame_no += 1
                        frame_no = self._latest_frame_no
                    with self._lock:
                        previous = self._latest_result
                        # Gdy tracking jest aktywny, zachowujemy ostatnie error_x/visible.
                        # Reader podmienia tylko bieżący obraz/frame info.
                        if self._tracking_enabled and previous is not None:
                            # Tracking worker rysuje ramki/kwadraty na frame_rgb.
                            # Reader nie może tego nadpisać czystą klatką, bo wtedy
                            # z podglądu znika zaznaczenie wykrytego obiektu.
                            preview_frame = previous.frame_rgb if previous.frame_rgb is not None else plain.frame_rgb
                            self._latest_result = CameraTrackingResult(
                                visible=previous.visible,
                                error_x=previous.error_x,
                                object_x=previous.object_x,
                                object_y=previous.object_y,
                                frame_center_x=plain.frame_center_x,
                                frame_width=plain.frame_width,
                                frame_height=plain.frame_height,
                                area=previous.area,
                                frame_rgb=preview_frame,
                            )
                        else:
                            self._latest_result = plain
                        self._latest_frame = plain.frame_rgb
                        self._reader_tick_ms = (time.perf_counter() - tick0) * 1000.0
                else:
                    with self._lock:
                        self._message = "CameraSession READ ERROR | brak klatki"
                        self._reader_tick_ms = (time.perf_counter() - tick0) * 1000.0

                if self._tick_profile_callback is not None:
                    try:
                        self._tick_profile_callback("KHR_CAMERA.reader_tick", self._reader_tick_ms / 1000.0)
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

    def _read_bgr_frame(self):
        if self.cap is None:
            return None
        try:
            ok, frame = self.cap.read()
        except Exception:
            return None
        if not ok or frame is None:
            return None
        return frame

    def _plain_result_from_frame(self, frame) -> CameraTrackingResult:
        if frame is None or self.cv2 is None:
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

    # ------------------------------------------------------------------
    # TRACKING WORKER: ONLY PROCESS_FRAME ON COPIES
    # ------------------------------------------------------------------
    def _ensure_tracking_thread(self) -> None:
        thread = self._tracking_thread
        if thread is not None and thread.is_alive():
            return
        self._tracking_thread = threading.Thread(
            target=self._tracking_loop,
            name="TARZAN_TRACKING_WORKER",
            daemon=True,
        )
        self._tracking_thread.start()

    def _tracking_loop(self) -> None:
        frame_period = 1.0 / max(1, self.config.live_fps)
        next_t = time.perf_counter()
        local_counter = 0
        while not self._stop.is_set():
            if not self.tracking_enabled:
                self._stop.wait(0.02)
                continue

            tick0 = time.perf_counter()
            local_counter += 1
            try:
                self._apply_pending_tracking_switch()
                with self._frame_lock:
                    frame_no = self._latest_frame_no
                    frame = self._latest_bgr_frame
                if frame is None or frame_no == self._last_tracked_frame_no:
                    self._stop.wait(0.002)
                    continue
                if frame_no <= self.config.tracking_start_after_frames:
                    self._last_tracked_frame_no = frame_no
                    continue
                if (local_counter % self.config.detect_every_n) != 0:
                    self._last_tracked_frame_no = frame_no
                    continue

                try:
                    frame_for_tracking = frame.copy()
                except Exception:
                    frame_for_tracking = frame

                with self._lock:
                    want_frame = bool(self._frame_output_enabled)

                # Tracking zwraca frame_rgb z naniesionym debugiem/ramkami.
                # To jest właściwy obraz dla UI w trybie śledzenia.
                result = self._detect_result_from_frame(frame_for_tracking, include_frame_rgb=want_frame)
                self._last_tracked_frame_no = frame_no

                with self._lock:
                    self._latest_result = result
                    self._latest_frame = result.frame_rgb
                    self._tracking_tick_ms = (time.perf_counter() - tick0) * 1000.0
                    self._message = f"CameraSession LIVE + {self.config.tracking_mode} | reader={self._reader_tick_ms:.1f}ms tracking={self._tracking_tick_ms:.1f}ms"
            except Exception as exc:
                with self._lock:
                    self._tracking_tick_ms = (time.perf_counter() - tick0) * 1000.0
                    self._message = f"TRACKING WORKER ERROR | camera unchanged | {exc}"

            if self._tick_profile_callback is not None:
                try:
                    self._tick_profile_callback("KHR_TRACKING.worker_tick", self._tracking_tick_ms / 1000.0)
                except Exception:
                    pass

            next_t += frame_period
            sleep_s = next_t - time.perf_counter()
            if sleep_s <= 0:
                next_t = time.perf_counter()
                sleep_s = 0.001
            self._stop.wait(min(sleep_s, frame_period))

    def _apply_pending_tracking_switch(self) -> None:
        with self._lock:
            mode = self._pending_tracking_mode
            prepared_tracker = self._pending_tracker
            self._pending_tracking_mode = None
            self._pending_tracker = None
        if not mode:
            return

        self._close_tracker()
        self.tracker = prepared_tracker
        if self.tracker is not None:
            self._attach_runtime_to_tracker(self.tracker)

        self.config.tracking_mode = mode
        self._active_tracking_mode = mode
        with self._lock:
            self._tracking_ready = self.tracker is not None
            self._message = f"CameraSession LIVE | plugin={mode} | camera unchanged"

    def _ensure_tracker(self) -> None:
        if self.tracker is not None:
            return
        mode = str(self.config.tracking_mode or "HSV_COLOR").upper()
        if mode in ("FACE_HAAR", "FACE_MEDIAPIPE") and TarzanFaceTracker is not None:
            backend = "HAAR" if mode == "FACE_HAAR" else "MEDIAPIPE"
            tracker = TarzanFaceTracker(
                device_index=self.config.device_index,
                frame_width=self.config.frame_width,
                frame_height=self.config.frame_height,
                project_root=None,
                settings=self.settings,
                backend=backend,
            )
        else:
            tracker = TarzanCameraTracker(
                device_index=self.config.device_index,
                frame_width=self.config.frame_width,
                frame_height=self.config.frame_height,
                min_area=self.config.min_area,
                project_root=None,
            )
            tracker.settings = self.settings
            tracker.set_target_profile(self.config.target_profile)
        self._attach_runtime_to_tracker(tracker)
        self.tracker = tracker
        with self._lock:
            self._tracking_ready = True

    def _attach_runtime_to_tracker(self, tracker) -> None:
        tracker.device_index = self.config.device_index
        tracker.frame_width = self.config.frame_width
        tracker.frame_height = self.config.frame_height
        tracker.cv2 = self.cv2
        tracker.np = self.np
        # Celowo NIE podpinamy cap. Plugin trackingu nie ma czytać kamery.
        try:
            tracker.cap = None
        except Exception:
            pass

    def _detect_result_from_frame(self, frame, include_frame_rgb: bool = False) -> CameraTrackingResult:
        if frame is None:
            return CameraTrackingResult()
        self._ensure_tracker()
        tracker = self.tracker
        if tracker is None:
            return CameraTrackingResult()
        return self._run_tracker_on_frame(tracker, frame, include_frame_rgb=include_frame_rgb)

    def _run_tracker_on_frame(self, tracker, frame, include_frame_rgb: bool) -> CameraTrackingResult:
        process_frame = getattr(tracker, "process_frame", None)
        if callable(process_frame):
            try:
                return process_frame(frame, include_frame_rgb=include_frame_rgb)
            except TypeError:
                result = process_frame(frame)
                if not include_frame_rgb:
                    result.frame_rgb = None
                return result
        detect = getattr(tracker, "_detect_object", None)
        if callable(detect):
            try:
                return detect(frame, include_frame_rgb=include_frame_rgb)
            except TypeError:
                result = detect(frame)
                if not include_frame_rgb:
                    result.frame_rgb = None
                return result
        return CameraTrackingResult()

    # ------------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------------
    def _release_cap(self) -> None:
        cap = self.cap
        self.cap = None
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass

    def _close_tracker(self) -> None:
        tracker = self.tracker
        self.tracker = None
        if tracker is not None:
            try:
                tracker.cap = None
            except Exception:
                pass
            close = getattr(tracker, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
