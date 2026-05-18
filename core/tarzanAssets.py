import os

# =========================================================
# BASE PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

IMG_AXES_DIR = os.path.join(BASE_DIR, "img", "axes")
IMG_TAKE_DIR = os.path.join(BASE_DIR, "img", "take")
IMG_LOGO_DIR = os.path.join(BASE_DIR, "img", "logo")


# =========================================================
# AXIS MAP (pełne nazwy z projektu!)
# =========================================================

AXIS_ICON_MAP = {
    "oś pozioma kamery": "ta_os_pozioma_kamery_ico",
    "oś pionowa kamery": "ta_os_pionowa_kamery_ico",
    "oś pochyłu kamery": "ta_os_pochylu_kamery_ico",
    "oś pochyłu ramienia": "ta_os_pochylu_kamery_ico",
    "oś ostrości kamery": "ta_os_ostrosci_kamery_ico",
    "oś pionowa ramienia": "ta_os_pionowa_ramienia_ico",
    "oś pozioma ramienia": "ta_os_pozioma_ramienia_ico",
    "DRON": "ta_dron_ico",
}


# =========================================================
# AXIS ICON PATH BUILDER
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


# =========================================================
# TAKE ICONS
# =========================================================

def take_icon(size: int = 64, state: str = "closed", ext: str = "png") -> str:
    """
    size: 64 / 128 / 256 / 320
    state:
        'closed'  -> standard TAKE
        'open'    -> preview / kolejka
        'active'  -> aktualny TAKE (czerwone paski)
    ext: 'png' / 'ico'
    """

    filename = f"take_{state}_{size}.{ext}"
    return os.path.join(IMG_TAKE_DIR, filename)


# =========================================================
# TARZAN LOGO
# =========================================================

LOGO_KIND_DIR = {
    "with_wordmark": "logo_with_wordmark",
    "full": "logo_with_wordmark",
    "emblem": "logo_emblem_only",
    "logo": "logo_emblem_only",
    "wordmark": "wordmark",
}

LOGO_KIND_PREFIX = {
    "with_wordmark": "tarzan_logo_with_wordmark",
    "full": "tarzan_logo_with_wordmark",
    "emblem": "tarzan_logo_emblem",
    "logo": "tarzan_logo_emblem",
    "wordmark": "tarzan_wordmark",
}


def _logo_candidate(subdir: str, filename: str) -> str:
    """
    Najpierw używa struktury:
        img/logo/<subdir>/<filename>

    Jeśli pliki zostaną wrzucone płasko do img/logo,
    zwraca też poprawny fallback:
        img/logo/<filename>
    """

    nested = os.path.join(IMG_LOGO_DIR, subdir, filename)
    if os.path.exists(nested):
        return nested

    return os.path.join(IMG_LOGO_DIR, filename)


def tarzan_logo(kind: str = "with_wordmark", size: int = 512, ext: str = "png") -> str:
    """
    kind:
        'with_wordmark' / 'full' -> znak + napis TARZAN
        'emblem' / 'logo'        -> sam znak T w okręgu
        'wordmark'               -> sam napis TARZAN

    size:
        np. 128 / 256 / 320 / 512 / 1024 / 2048 / 3072 / 4096

    Przykład:
        tarzan_logo("with_wordmark", 1024)
        tarzan_logo("emblem", 512)
        tarzan_logo("wordmark", 2048)
    """

    if kind not in LOGO_KIND_DIR:
        raise ValueError(f"Nieznany typ logo: {kind}")

    filename = f"{LOGO_KIND_PREFIX[kind]}_{size}.{ext}"
    return _logo_candidate(LOGO_KIND_DIR[kind], filename)


def tarzan_logo_master(kind: str = "with_wordmark", ext: str = "png") -> str:
    """
    Zwraca plik master dla danego wariantu logo.
    """

    if kind not in LOGO_KIND_DIR:
        raise ValueError(f"Nieznany typ logo: {kind}")

    filename = f"{LOGO_KIND_PREFIX[kind]}_master.{ext}"
    return _logo_candidate(LOGO_KIND_DIR[kind], filename)


def tarzan_logo_header(
    kind: str = "with_wordmark",
    width: int = 1600,
    height: int = 600,
    ext: str = "png",
) -> str:
    """
    Wersje szerokie / header.

    kind:
        'with_wordmark' / 'full'
        'emblem' / 'logo'

    Przykład:
        tarzan_logo_header("with_wordmark", 1600, 600)
        tarzan_logo_header("emblem", 2400, 900)
    """

    if kind not in LOGO_KIND_DIR:
        raise ValueError(f"Nieznany typ logo: {kind}")

    if kind == "wordmark":
        raise ValueError("wordmark nie ma wersji header w tej funkcji")

    filename = f"{LOGO_KIND_PREFIX[kind]}_header_{width}x{height}.{ext}"
    return _logo_candidate(LOGO_KIND_DIR[kind], filename)


def tarzan_favicon(size: int = 32, ext: str = "png") -> str:
    """
    Ikony przeglądarkowe.

    size:
        16 / 32 / 48 / 64 / 96 / 180 / 192 / 512

    Dla ext='ico' zwraca favicon.ico.
    """

    if ext == "ico":
        return _logo_candidate("favicon", "favicon.ico")

    filename = f"favicon-{size}x{size}.{ext}"
    return _logo_candidate("favicon", filename)
