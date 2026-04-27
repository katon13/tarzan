# -*- coding: utf-8 -*-
"""
TARZAN - Camera Controls

Mapowanie kontrolowanych parametrów VideoCapture.
Nie każda kamera wspiera wszystkie parametry.
Jeżeli kamera nie wspiera parametru, OpenCV może go zignorować.
"""

from __future__ import annotations


def fourcc_to_int(cv2, fourcc: str) -> int:
    fourcc = (fourcc or "").strip()
    if len(fourcc) != 4:
        return 0
    return cv2.VideoWriter_fourcc(*fourcc)


def apply_camera_settings(cap, cv2, camera_cfg: dict) -> None:
    # Format i rozmiar.
    fourcc = camera_cfg.get("fourcc")
    if fourcc:
        cap.set(cv2.CAP_PROP_FOURCC, fourcc_to_int(cv2, fourcc))

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_cfg.get("frame_width", 640)))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_cfg.get("frame_height", 360)))
    cap.set(cv2.CAP_PROP_FPS, float(camera_cfg.get("fps", 30)))

    # Typowe parametry kamer UVC. Część kamer je ignoruje.
    optional_map = {
        "brightness": getattr(cv2, "CAP_PROP_BRIGHTNESS", None),
        "contrast": getattr(cv2, "CAP_PROP_CONTRAST", None),
        "saturation": getattr(cv2, "CAP_PROP_SATURATION", None),
        "gain": getattr(cv2, "CAP_PROP_GAIN", None),
        "exposure": getattr(cv2, "CAP_PROP_EXPOSURE", None),
        "focus": getattr(cv2, "CAP_PROP_FOCUS", None),
        "white_balance": getattr(cv2, "CAP_PROP_WB_TEMPERATURE", None),
    }

    for key, prop in optional_map.items():
        if prop is not None and key in camera_cfg:
            try:
                cap.set(prop, float(camera_cfg[key]))
            except Exception:
                pass

    # Auto ustawienia - backend/kamera może różnie interpretować wartości.
    if hasattr(cv2, "CAP_PROP_AUTO_EXPOSURE") and "auto_exposure" in camera_cfg:
        try:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75 if camera_cfg["auto_exposure"] else 0.25)
        except Exception:
            pass

    if hasattr(cv2, "CAP_PROP_AUTOFOCUS") and "auto_focus" in camera_cfg:
        try:
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 1 if camera_cfg["auto_focus"] else 0)
        except Exception:
            pass

    if hasattr(cv2, "CAP_PROP_AUTO_WB") and "white_balance_auto" in camera_cfg:
        try:
            cap.set(cv2.CAP_PROP_AUTO_WB, 1 if camera_cfg["white_balance_auto"] else 0)
        except Exception:
            pass


def read_camera_state(cap, cv2) -> dict:
    props = {
        "width": cv2.CAP_PROP_FRAME_WIDTH,
        "height": cv2.CAP_PROP_FRAME_HEIGHT,
        "fps": cv2.CAP_PROP_FPS,
        "fourcc": cv2.CAP_PROP_FOURCC,
        "brightness": cv2.CAP_PROP_BRIGHTNESS,
        "contrast": cv2.CAP_PROP_CONTRAST,
        "saturation": cv2.CAP_PROP_SATURATION,
    }

    optional = ["CAP_PROP_GAIN", "CAP_PROP_EXPOSURE", "CAP_PROP_FOCUS", "CAP_PROP_AUTOFOCUS", "CAP_PROP_AUTO_EXPOSURE"]
    for name in optional:
        if hasattr(cv2, name):
            props[name.replace("CAP_PROP_", "").lower()] = getattr(cv2, name)

    out = {}
    for key, prop in props.items():
        try:
            out[key] = cap.get(prop)
        except Exception:
            out[key] = None
    return out
