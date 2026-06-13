from __future__ import annotations

"""TARZAN LKS-N5 — realna matrix testów ikon status_main.

Ten plik NIE wykonuje sprzętu. Trzyma jeden kontrakt:
status_main ikona -> component_id -> sygnały -> tester -> metoda -> oczekiwany ACK.

Wykonanie fizyczne zostaje w core/tarzanHardwareBridge.py / core/tarzanPoKeys.py.
Brak wpisu w matrix oznacza błąd NO_TEST_MATRIX, a nie fallback opisowy.
"""

from typing import Any, Dict, Iterable, Mapping, Tuple

from core.TSP.tarzanTspLksStatusMap import LKS_STATUS_COMPONENT_IDS
from core.tarzanZmienneSygnalowe import WSZYSTKIE_SYGNALY


def _signals_by_group(group: str) -> Tuple[str, ...]:
    wanted = str(group or "").upper()
    return tuple(
        name
        for name, sig in WSZYSTKIE_SYGNALY.items()
        if str(getattr(sig, "grupa", "") or "").upper() == wanted
    )


AXIS_EXPECTED_SIGNAL_CONFIG: Dict[str, Dict[str, Any]] = {
    "cnc_x_cam_h_ctr": {"plytka": "CNC", "pin": None, "kanal": "X / ID1", "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_x_cam_h_dir": {"plytka": "CNC", "pin": None, "kanal": "X / ID1", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_x_cam_h_en": {"plytka": "CNC", "pin": None, "kanal": "X / ID1", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "rec_p01_copy_ctr_cam_h": {"plytka": "REC", "pin": 1, "kanal": None, "typ": "CTR", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "rec_p03_copy_dir_cam_h": {"plytka": "REC", "pin": 3, "kanal": None, "typ": "LH", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "cnc_y_cam_v_ctr": {"plytka": "CNC", "pin": None, "kanal": "Y / ID2", "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_y_cam_v_dir": {"plytka": "CNC", "pin": None, "kanal": "Y / ID2", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_y_cam_v_en": {"plytka": "CNC", "pin": None, "kanal": "Y / ID2", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "rec_p02_copy_ctr_cam_v": {"plytka": "REC", "pin": 2, "kanal": None, "typ": "CTR", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "rec_p04_copy_dir_cam_v": {"plytka": "REC", "pin": 4, "kanal": None, "typ": "LH", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "cnc_z_focus_ctr": {"plytka": "CNC", "pin": None, "kanal": "Z / ID3", "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_z_focus_dir": {"plytka": "CNC", "pin": None, "kanal": "Z / ID3", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_z_focus_en": {"plytka": "CNC", "pin": None, "kanal": "Z / ID3", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "rec_p05_copy_ctr_focus": {"plytka": "REC", "pin": 5, "kanal": None, "typ": "CTR", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "rec_p07_copy_dir_focus": {"plytka": "REC", "pin": 7, "kanal": None, "typ": "LH", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "cnc_a_arm_tilt_ctr": {"plytka": "CNC", "pin": None, "kanal": "A / ID4", "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_a_arm_tilt_dir": {"plytka": "CNC", "pin": None, "kanal": "A / ID4", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "rec_p06_copy_ctr_tilt": {"plytka": "REC", "pin": 6, "kanal": None, "typ": "CTR", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "rec_p08_copy_dir_tilt": {"plytka": "REC", "pin": 8, "kanal": None, "typ": "LH", "kierunek": "IN", "hardware_function": "GPIO", "pin_is_fixed": True},
    "play_p46_step_ctr_arm_h": {"plytka": "PLAY", "pin": 46, "kanal": None, "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "play_p38_step_dir_arm_h": {"plytka": "PLAY", "pin": 38, "kanal": None, "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "play_p50_step_en_arm_h": {"plytka": "PLAY", "pin": 50, "kanal": None, "typ": "LH", "kierunek": "OUT", "hardware_function": "GPIO", "pin_is_fixed": True},
    "cnc_b_arm_h_ctr": {"plytka": "CNC", "pin": None, "kanal": "B / ID5", "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_b_arm_h_dir": {"plytka": "CNC", "pin": None, "kanal": "B / ID5", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "play_p48_step_ctr_arm_v": {"plytka": "PLAY", "pin": 48, "kanal": None, "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "play_p39_step_dir_arm_v": {"plytka": "PLAY", "pin": 39, "kanal": None, "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "play_p51_step_en_arm_v": {"plytka": "PLAY", "pin": 51, "kanal": None, "typ": "LH", "kierunek": "OUT", "hardware_function": "GPIO", "pin_is_fixed": True},
    "cnc_c_arm_v_ctr": {"plytka": "CNC", "pin": None, "kanal": "C / ID6", "typ": "CTR", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
    "cnc_c_arm_v_dir": {"plytka": "CNC", "pin": None, "kanal": "C / ID6", "typ": "LH", "kierunek": "OUT", "hardware_function": "PULSE_ENGINE", "pin_is_fixed": True},
}


def _axis_expected(*names: str) -> Dict[str, Dict[str, Any]]:
    return {name: dict(AXIS_EXPECTED_SIGNAL_CONFIG[name]) for name in names}


LKS_TEST_MATRIX: Dict[str, Dict[str, Any]] = {
    # System / runtime — realny stan procesu, usług, klienta albo SignalBus.
    "linux_sys": {
        "component_id": 1,
        "tester": "runtime_state",
        "method": "linux_runtime_alive",
        "signals": ("runtime_state", "system_state"),
        "expect": "RUNTIME_ACK",
    },
    "snajper_sys": {
        "component_id": 2,
        "tester": "runtime_state",
        "method": "snajper_alive",
        "signals": ("control_owner", "hardware_realtime_required"),
        "expect": "RUNTIME_ACK",
    },
    "take_sys": {
        "component_id": 28,
        "tester": "runtime_state",
        "method": "take_state",
        "signals": ("transport_state",),
        "expect": "RUNTIME_ACK",
    },
    "par_sys": {
        "component_id": 29,
        "tester": "runtime_state",
        "method": "par_tsp_client",
        "signals": ("par_state",),
        "expect": "TSP_CLIENT_ACK",
    },
    "ehr_sys": {
        "component_id": 30,
        "tester": "runtime_state",
        "method": "ehr_tsp_client",
        "signals": ("ehr_state",),
        "expect": "TSP_CLIENT_ACK",
    },

    # PoKeys / POKSYG.
    "pok_play": {
        "component_id": 3,
        "tester": "poksyg_device",
        "method": "pokeys_identity",
        "board": "PLAY",
        "signals": (),
        "expect": "POKEYS_PLAY_ACK",
    },
    "pok_rec": {
        "component_id": 5,
        "tester": "poksyg_device",
        "method": "pokeys_identity",
        "board": "REC",
        "signals": (),
        "expect": "POKEYS_REC_ACK",
    },

    # SOK — fizycznie dwa SOK-i, każdy po dwa kanały. Nie ma trzeciego SOK-a.
    "sok_poz": {
        "component_id": 4,
        "tester": "poksyg_signals",
        "method": "read_input_signals",
        "signals": (
            "rec_p01_copy_ctr_cam_h",
            "rec_p02_copy_ctr_cam_v",
            "rec_p03_copy_dir_cam_h",
            "rec_p04_copy_dir_cam_v",
        ),
        "expect": "INPUT_READ_ACK",
    },
    "sok_pion": {
        "component_id": 7,
        "tester": "poksyg_signals",
        "method": "read_input_signals",
        "signals": (
            "rec_p05_copy_ctr_focus",
            "rec_p06_copy_ctr_tilt",
            "rec_p07_copy_dir_focus",
            "rec_p08_copy_dir_tilt",
        ),
        "expect": "INPUT_READ_ACK",
    },

    # RRP.
    "rrp": {
        "component_id": 6,
        "tester": "poksyg_signals",
        "method": "read_analog_signals",
        "signals": ("play_p45_rrp_pot_h", "play_p47_rrp_pot_v"),
        "expect": "ANALOG_READ_ACK",
    },

    # UI lokalne.
    "next_7": {
        "component_id": 8,
        "tester": "nextion_serial",
        "method": "nextion7_port_exists",
        "signals": (),
        "expect": "UART_PORT_ACK",
    },
    "lcd_1602": {
        "component_id": 9,
        "tester": "poksyg_function",
        "method": "lcd_1602_ack",
        "signals": (),
        "expect": "LCD_ACK",
    },
    "matrix_led": {
        "component_id": 10,
        "tester": "poksyg_function",
        "method": "matrix_led_ack",
        "signals": (),
        "expect": "MATRIX_LED_ACK",
    },
    "keypad": {
        "component_id": 11,
        "tester": "poksyg_function",
        "method": "keypad_read_ack",
        "signals": (),
        "expect": "KEYPAD_READ_ACK",
    },
    "f_button": {
        "component_id": 12,
        "tester": "poksyg_signals",
        "method": "read_input_signals",
        "signals": ("rec_p45_sw_f1", "rec_p47_sw_f2", "rec_p49_sw_f3", "rec_p51_sw_f4"),
        "expect": "INPUT_READ_ACK",
    },
    "f_led": {
        "component_id": 18,
        "tester": "poksyg_function",
        "method": "f_led_ack",
        "signals": ("rec_p46_led_f1", "rec_p48_led_f2", "rec_p50_led_f3", "rec_p52_led_f4"),
        "expect": "LED_WRITE_ACK",
    },

    # I2C / sensory.
    "i2c_bus": {
        "component_id": 27,
        "tester": "poksyg_i2c",
        "method": "scan_i2c",
        "signals": ("i2c_bus_ok",),
        "expect": "I2C_SCAN_ACK",
    },
    "light_bh1750": {
        "component_id": 16,
        "tester": "poksyg_i2c",
        "method": "bh1750_read",
        "signals": (),
        "expect": "BH1750_READ_ACK",
    },
    "level_xyz": {
        "component_id": 14,
        "tester": "poksyg_i2c",
        "method": "xyz_read",
        "signals": (),
        "expect": "XYZ_READ_ACK",
    },
    "light_laser": {
        "component_id": 15,
        "tester": "poksyg_i2c",
        "method": "laser_bh1750_read",
        "signals": (),
        "expect": "BH1750_PLAY_0x5C_READ_ACK",
    },
    "shock_alarm": {
        "component_id": 13,
        "tester": "poksyg_signals",
        "method": "read_input_signals",
        "signals": ("rec_p39_shock_sensor",),
        "expect": "INPUT_READ_ACK",
    },
    "kranc": {
        "component_id": 17,
        "tester": "poksyg_signals",
        "method": "read_input_signals",
        "signals": _signals_by_group("KRAŃCÓWKI"),
        "expect": "LIMITS_READ_ACK",
    },

    # Osie — test toru/mapy/ACK bez ruchu mechanicznego w LKS POINT_TEST.
    "kam_poz": {
        "component_id": 19,
        "tester": "poksyg_axis",
        "method": "axis_wiring_ack_no_motion",
        "signals": ("cnc_x_cam_h_ctr", "cnc_x_cam_h_dir", "cnc_x_cam_h_en", "rec_p01_copy_ctr_cam_h", "rec_p03_copy_dir_cam_h"),
        "expected_config": _axis_expected("cnc_x_cam_h_ctr", "cnc_x_cam_h_dir", "cnc_x_cam_h_en", "rec_p01_copy_ctr_cam_h", "rec_p03_copy_dir_cam_h"),
        "expect": "AXIS_WIRING_ACK_NO_MOTION",
    },
    "kam_pion": {
        "component_id": 20,
        "tester": "poksyg_axis",
        "method": "axis_wiring_ack_no_motion",
        "signals": ("cnc_y_cam_v_ctr", "cnc_y_cam_v_dir", "cnc_y_cam_v_en", "rec_p02_copy_ctr_cam_v", "rec_p04_copy_dir_cam_v"),
        "expected_config": _axis_expected("cnc_y_cam_v_ctr", "cnc_y_cam_v_dir", "cnc_y_cam_v_en", "rec_p02_copy_ctr_cam_v", "rec_p04_copy_dir_cam_v"),
        "expect": "AXIS_WIRING_ACK_NO_MOTION",
    },
    "kam_ostr": {
        "component_id": 21,
        "tester": "poksyg_axis",
        "method": "axis_wiring_ack_no_motion",
        "signals": ("cnc_z_focus_ctr", "cnc_z_focus_dir", "cnc_z_focus_en", "rec_p05_copy_ctr_focus", "rec_p07_copy_dir_focus"),
        "expected_config": _axis_expected("cnc_z_focus_ctr", "cnc_z_focus_dir", "cnc_z_focus_en", "rec_p05_copy_ctr_focus", "rec_p07_copy_dir_focus"),
        "expect": "AXIS_WIRING_ACK_NO_MOTION",
    },
    "kam_poch": {
        "component_id": 22,
        "tester": "poksyg_axis",
        "method": "axis_wiring_ack_no_motion",
        "signals": ("cnc_a_arm_tilt_ctr", "cnc_a_arm_tilt_dir", "rec_p06_copy_ctr_tilt", "rec_p08_copy_dir_tilt"),
        "expected_config": _axis_expected("cnc_a_arm_tilt_ctr", "cnc_a_arm_tilt_dir", "rec_p06_copy_ctr_tilt", "rec_p08_copy_dir_tilt"),
        "expect": "AXIS_WIRING_ACK_NO_MOTION",
    },
    "ram_poziom": {
        "component_id": 23,
        "tester": "poksyg_axis",
        "method": "axis_wiring_ack_no_motion",
        "signals": ("play_p46_step_ctr_arm_h", "play_p38_step_dir_arm_h", "play_p50_step_en_arm_h", "cnc_b_arm_h_ctr", "cnc_b_arm_h_dir"),
        "expected_config": _axis_expected("play_p46_step_ctr_arm_h", "play_p38_step_dir_arm_h", "play_p50_step_en_arm_h", "cnc_b_arm_h_ctr", "cnc_b_arm_h_dir"),
        "expect": "AXIS_WIRING_ACK_NO_MOTION",
    },
    "ram_pion": {
        "component_id": 24,
        "tester": "poksyg_axis",
        "method": "axis_wiring_ack_no_motion",
        "signals": ("play_p48_step_ctr_arm_v", "play_p39_step_dir_arm_v", "play_p51_step_en_arm_v", "cnc_c_arm_v_ctr", "cnc_c_arm_v_dir"),
        "expected_config": _axis_expected("play_p48_step_ctr_arm_v", "play_p39_step_dir_arm_v", "play_p51_step_en_arm_v", "cnc_c_arm_v_ctr", "cnc_c_arm_v_dir"),
        "expect": "AXIS_WIRING_ACK_NO_MOTION",
    },

    # Kamery USB.
    "cam_main": {
        "component_id": 25,
        "tester": "usb_camera",
        "method": "open_video_node",
        "signals": (),
        "camera_index": 0,
        "expect": "USB_CAMERA_OPEN_ACK",
    },
    "cam_track": {
        "component_id": 26,
        "tester": "usb_camera",
        "method": "open_video_node",
        "signals": (),
        "camera_index": 1,
        "expect": "USB_CAMERA_OPEN_ACK",
    },
}


COMPONENT_BY_ID: Dict[int, str] = {int(v["component_id"]): k for k, v in LKS_TEST_MATRIX.items()}


def get_lks_test(component: str) -> Mapping[str, Any]:
    return LKS_TEST_MATRIX[str(component)]


def has_lks_test(component: str) -> bool:
    return str(component) in LKS_TEST_MATRIX


def components() -> Tuple[str, ...]:
    return tuple(LKS_TEST_MATRIX.keys())


def hardwarebridge_components() -> Tuple[str, ...]:
    return components()


def validate_lks_test_matrix() -> Tuple[str, ...]:
    errors = []
    expected_ids = dict(LKS_STATUS_COMPONENT_IDS)
    for component, entry in LKS_TEST_MATRIX.items():
        cid = int(entry.get("component_id", -1))
        expected_component = expected_ids.get(cid)
        if expected_component != component:
            errors.append(f"{component}: component_id={cid} expected={expected_component}")
        for signal in entry.get("signals", ()):
            if signal and signal not in WSZYSTKIE_SYGNALY:
                errors.append(f"{component}: missing signal {signal}")
        expected_config = entry.get("expected_config") or {}
        for signal, expected in expected_config.items():
            sig = WSZYSTKIE_SYGNALY.get(signal)
            if sig is None:
                errors.append(f"{component}: expected_config missing signal {signal}")
                continue
            for field, expected_value in expected.items():
                actual_value = getattr(sig, field, None)
                if actual_value != expected_value:
                    errors.append(f"{component}: {signal}.{field}={actual_value!r} expected={expected_value!r}")
    for cid, component in expected_ids.items():
        if component not in LKS_TEST_MATRIX:
            errors.append(f"missing matrix entry {component} id={cid}")
    return tuple(errors)


MATRIX_ERRORS = validate_lks_test_matrix()
