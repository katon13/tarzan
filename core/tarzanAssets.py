import os

# =========================================================
# BASE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

IMG_AXES_DIR = os.path.join(BASE_DIR, "img", "axes")


# =========================================================
# AXIS MAP (pełne nazwy z projektu!)
# =========================================================

AXIS_ICON_MAP = {
    "oś pozioma kamery": "ta_os_pozioma_kamery_ico",
    "oś pionowa kamery": "ta_os_pionowa_kamery_ico",
    "oś pochyłu kamery": "ta_os_pochylu_kamery_ico",
    "oś ostrości kamery": "ta_os_ostrości_kamery_ico",
    "oś pionowa ramienia": "ta_os_pionowa_ramienia_ico",
    "oś pozioma ramienia": "ta_os_pozioma_ramienia_ico",
    "dron": "ta_dron_ico",
}


# =========================================================
# ICON PATH BUILDER
# =========================================================

def axis_icon(axis_name: str, size: int = 64, state: str = "active", ext: str = "png") -> str:
    """
    axis_name: pełna nazwa osi (np. 'oś pozioma kamery')
    size: 64 / 96 / 128 / 320
    state: 'active' / 'inactive'
    ext: 'png' / 'ico'
    """

    key = AXIS_ICON_MAP.get(axis_name)

    if not key:
        raise ValueError(f"Nieznana oś: {axis_name}")

    filename = f"{key}_{size}_{state}.{ext}"
    return os.path.join(IMG_AXES_DIR, filename)


# =========================================================
# DIRECT ACCESS (jeśli masz key zamiast nazwy)
# =========================================================

def axis_icon_by_key(key: str, size: int = 64, state: str = "active", ext: str = "png") -> str:
    filename = f"{key}_{size}_{state}.{ext}"
    return os.path.join(IMG_AXES_DIR, filename)