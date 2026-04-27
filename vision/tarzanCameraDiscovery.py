# -*- coding: utf-8 -*-
"""
TARZAN - Camera Discovery

Ciche wykrywanie kamer USB.
Nie steruje KHR. Tylko sprawdza dostępne źródła obrazu.
"""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass


@dataclass
class CameraInfo:
    index: int
    backend: str
    opened: bool
    width: int = 0
    height: int = 0
    fps: float = 0.0
    message: str = ""


_BACKENDS = {
    "ANY": None,
    "DSHOW": "CAP_DSHOW",
    "MSMF": "CAP_MSMF",
}


@contextlib.contextmanager
def _suppress_stderr():
    """
    OpenCV na Windows potrafi wypisywać warningi z C++ bez rzucania wyjątku.
    Tu wyciszamy je tylko na czas skanowania kamer.
    """
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


def _backend_value(cv2, backend_name: str):
    attr = _BACKENDS.get(backend_name, None)
    if attr is None:
        return None
    return getattr(cv2, attr, None)


def scan_cameras(indexes: list[int] | None = None, backend: str = "DSHOW") -> list[CameraInfo]:
    indexes = indexes or [0, 1, 2, 3, 4]
    backend = backend or "DSHOW"

    if backend == "ANY":
        backends = ["ANY"]
    else:
        backends = [backend]

    try:
        import cv2
    except Exception as exc:
        return [CameraInfo(index=-1, backend="NONE", opened=False, message=f"Brak OpenCV: {exc}")]

    try:
        cv2.setLogLevel(0)
    except Exception:
        pass

    found: list[CameraInfo] = []

    for index in indexes:
        for backend_name in backends:
            backend_value = _backend_value(cv2, backend_name)

            with _suppress_stderr():
                try:
                    if backend_value is None:
                        cap = cv2.VideoCapture(index)
                    else:
                        cap = cv2.VideoCapture(index, backend_value)

                    opened = bool(cap is not None and cap.isOpened())

                    if opened:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = float(cap.get(cv2.CAP_PROP_FPS))
                        found.append(
                            CameraInfo(
                                index=index,
                                backend=backend_name,
                                opened=True,
                                width=width,
                                height=height,
                                fps=fps,
                                message="OK",
                            )
                        )

                    if cap is not None:
                        cap.release()

                except Exception:
                    pass

    return found
