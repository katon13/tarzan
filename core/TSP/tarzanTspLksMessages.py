from __future__ import annotations

"""TARZAN LKS-N5 — stałe scen, poziomów i kodów komunikatów.

Ten moduł nie dotyka sprzętu. Jest słownikiem znaczeń dla warstwy
wizualnej LKS-N5. Nextion 5 dalej tylko pokazuje wynik diagnozy miniPC.
"""

# Sceny / strony HMI Nextion 5.
SCENE_BOOT_INTRO = "boot_intro"
SCENE_BOOT_LOADING = "boot_loading"
SCENE_BOOT_LINUX = "boot_linux"
SCENE_BOOT_SERVICES = "boot_services"
SCENE_BOOT_HARDWARE = "boot_hardware"
SCENE_BOOT_TEST = "boot_test"
SCENE_INTRO_STATUS = "intro_status"
SCENE_READY = "ready_main"
SCENE_STATUS = "status_main"
SCENE_WARN = "warn_main"
SCENE_ERROR = "error_main"
SCENE_TAKE = "take_main"

# Poziomy logiczne komunikatów.
LEVEL_OK = 0
LEVEL_INFO = 1
LEVEL_WARN = 2
LEVEL_ERROR = 3

# Kody błędów / ostrzeżeń.
ERR_N5_PORT = "N5_PORT"
ERR_N7_OFFLINE = "N7_OFFLINE"
ERR_POKEYS_PLAY = "POK_PLAY_OFFLINE"
ERR_POKEYS_REC = "POK_REC_OFFLINE"
ERR_I2C_BUS = "I2C_BUS_FAIL"
ERR_TSP = "TSP_FAIL"
ERR_PAR = "PAR_LOST"
ERR_EHR = "EHR_LOST"
ERR_UNKNOWN = "UNKNOWN"

# Kody informacyjne.
CODE_READY = "READY"
CODE_WARN = "WARN"
CODE_ERROR = "ERROR"
CODE_TAKE = "TAKE"

BOOT_PROGRESS_LOADING = 10
BOOT_PROGRESS_LINUX = 30
BOOT_PROGRESS_SERVICES = 45
BOOT_PROGRESS_HARDWARE = 65
BOOT_PROGRESS_TEST = 80
BOOT_PROGRESS_READY = 100

SCENES = (
    SCENE_BOOT_INTRO,
    SCENE_BOOT_LOADING,
    SCENE_BOOT_LINUX,
    SCENE_BOOT_SERVICES,
    SCENE_BOOT_HARDWARE,
    SCENE_BOOT_TEST,
    SCENE_INTRO_STATUS,
    SCENE_READY,
    SCENE_STATUS,
    SCENE_WARN,
    SCENE_ERROR,
    SCENE_TAKE,
)


def validate_scene(name: str) -> str:
    scene = str(name or "").strip()
    if scene not in SCENES:
        raise KeyError(f"Unknown LKS-N5 scene: {scene}")
    return scene
