from __future__ import annotations

try:
    from editor.TFD.tfd_state import tfd_state
except (ImportError, ModuleNotFoundError):
    tfd_state = None

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any, Callable
import math
import re
import time

from core.tarzanSignalBus import TarzanSignalBus, TarzanSignalState, TarzanSignalMeta
try:
    from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
except Exception:
    CZAS_PROBKOWANIA_MS = 10
try:
    from editor.PAR.tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, AxisCard, Led, Panel, SignalRow

try:
    from editor.PAR.tarzanNextionPreview import TarzanNextionPreviewPanel
except ModuleNotFoundError:
    from tarzanNextionPreview import TarzanNextionPreviewPanel

try:
    from core.tarzanProfiler import profile_method, profile_block
except Exception:
    def profile_method(name=None):
        def deco(func): return func
        return deco
    
# =============================================================================
# TARZAN_SNAJPER — SEKCJE PAR
# =============================================================================

TARZAN_SNAJPER_PAR_SECTIONS = {
    "rrp": {
        "par_rrp_p1_val", "par_rrp_p2_val",
        "par_rrp_p1_dir", "par_rrp_p2_dir",
        "par_rrp_p1_sens", "par_rrp_p2_sens",
        "par_rrp_p1_axis", "par_rrp_p2_axis",
    },
    "motor_cards": {
        "axis_0_value", "axis_1_value", "axis_2_value",
        "axis_3_value", "axis_4_value", "axis_5_value",
        "axis_cam_v_pulses", "axis_cam_t_pulses", "axis_cam_f_pulses",
        "axis_cam_h_pulses", "axis_arm_h_pulses", "axis_arm_v_pulses",
    },
    "step_dir_preview": {
        "axis_0_step", "axis_1_step", "axis_2_step",
        "axis_3_step", "axis_4_step", "axis_5_step",
        "axis_0_dir", "axis_1_dir", "axis_2_dir",
        "axis_3_dir", "axis_4_dir", "axis_5_dir",
        "step_dir_stream", "protocol_tick", "take_timecode",
    },
    "temperature": {
        "sensor_temp_c", "temperature_c", "par_temp_c",
    },
    "light": {
        "sensor_light_lux", "light_lux", "par_light_lux",
    },
    "xyz": {
        "sensor_xyz", "sensor_level_x", "sensor_level_y", "sensor_level_z",
        "level_x", "level_y", "level_z",
    },
    "limits": {
        "sensor_limits_status", "limit_state", "krańcówki", "krancowki",
    },
    "shock_laser": {
        "sensor_shock_state", "sensor_laser_set", "shock_state", "laser_state",
    },
    "sok": {
        "sok_pan", "sok_tilt", "sok_focus", "sok_cam",
    },
    "cnc": {
        "cnc_status", "cnc_signal", "cnc_step", "cnc_dir",
    },
    "logs": {
        "system_status", "log_event", "par_log",
    },
}



# TARZAN_SNAJPER_STAGE4_STEP_DIR_LIVE:
# Podgląd sygnałów STEP/DIR działa jako sekcja live.
# Zmiana STEP/DIR/CTR osi aktualizuje sekcję Podgląd sygnałów,
# nie cały PAR i nie cały layout.


# =============================================================================
# TARZAN_SNAJPER — STEP/DIR MULTI TARGET

# =============================================================================
# TARZAN_SNAJPER — STEP/DIR DIRECT FIRE

# =============================================================================
# TARZAN_SNAJPER — STEP/DIR DIRECT TARGET
# =============================================================================


# =============================================================================
# TARZAN_SNAJPER — REALNY CEL STEP/DIR


# =============================================================================
# TARZAN_SNAJPER — REALNE CELE LOGI / TAKE / NEXTION
# =============================================================================

class TarzanLogSnajperTarget:
    """
    Cel Snajpera dla panelu LOGI.
    Podpięty bezpośrednio pod bus.log().
    Nie robi refreshu panelu.
    """

    def __init__(self, widget=None) -> None:
        self.widget = widget
        self.last_line = None
        self.max_lines = 600

    def set_widget(self, widget) -> None:
        self.widget = widget

    def snajper_log_fire(self, line: str) -> None:
        if not line or line == self.last_line:
            return
        self.last_line = line

        widget = self.widget
        if widget is None:
            return

        try:
            if hasattr(widget, "insert"):
                widget.insert("end", line + "\n")
                try:
                    current = int(float(widget.index("end-1c").split(".")[0]))
                    if current > self.max_lines:
                        widget.delete("1.0", f"{current - self.max_lines}.0")
                except Exception:
                    pass
                if hasattr(widget, "see"):
                    widget.see("end")
                return
            if hasattr(widget, "configure"):
                widget.configure(text=line)
        except Exception:
            return


class TarzanTakeSnajperTarget:
    """
    Cel Snajpera dla TAKE — ODTWARZACZ PROTOKOŁU.
    Aktualizuje tylko status / czas TAKE, gdy TAKE jest otwarty i idą ms.
    """

    def __init__(self, panels) -> None:
        self.panels = panels
        self.last = {}

    def snajper_take_fire(self, signal: str, value, state: dict | None = None) -> None:
        self.last[signal] = value

        # Najpierw dokładny label aplikacji, jeśli istnieje.
        app = getattr(self.panels, "app", None)
        if app is not None and hasattr(app, "update_take_label"):
            try:
                app.update_take_label()
            except Exception:
                pass

        # Potem znane lokalne labelki panelu TAKE, jeśli są zarejestrowane.
        label = getattr(self.panels, "take_status_label", None)
        if label is not None:
            try:
                take_time = self.last.get("take_time_ms", self.last.get("take_timecode", value))
                label.configure(text=f"TAKE: {take_time} ms")
            except Exception:
                pass

        time_label = getattr(self.panels, "take_time_label", None)
        if time_label is not None:
            try:
                time_label.configure(text=f"{value} ms")
            except Exception:
                pass


# NEXTION fizyczny nie ma już lokalnego celu ani ręcznych map.
# Sygnał BUS -> TarzanSnajper.fire_from_signal(...) -> physical_nextion -> queue_snajper_command(...).


class TarzanStepDirPreviewTarget:
    """
    Własny cel Snajpera dla panelu PODGLĄD SYGNAŁÓW — STEP / DIR.

    To nie jest nakładka na stary draw_timeline.
    Ten target sam prowadzi canvas tej sekcji:
    - układ i styl jak w oryginalnym oknie PAR,
    - ikony osi po lewej,
    - linie S/D/H/L,
    - czerwony marker chwili odczytu,
    - czytelne strzały Snajpera na właściwych liniach,
    - opisy sygnałów w kontrolowanym miejscu.

    Nie robi refresh_all.
    Nie używa PAR_APP.tick.
    Nie zapisuje do BUS.
    """

    AXIS_ORDER = ("arm_h", "arm_v", "cam_h", "cam_v", "arm_t", "cam_f")
    AXIS_LABELS = {
        "arm_h": "ARM_H",
        "arm_v": "ARM_V",
        "cam_h": "CAM_H",
        "cam_v": "CAM_V",
        "arm_t": "ARM_T",
        "cam_f": "CAM_F",
    }

    def __init__(self, panels, canvas) -> None:
        self.panels = panels
        self.canvas = canvas
        self.items = {}
        self.state = {axis: {"step": 0, "dir": 0, "ctr": 0, "pulses": 0, "pos": 0} for axis in self.AXIS_ORDER}
        self.event_index = 0
        self.geometry = {}
        self._rendered = False

    def redraw(self) -> None:
        self._render_base()
        self._render_values()

    def snajper_step_dir_fire(self, axis: str, kind: str, signal: str, value, state: dict) -> None:
        if axis not in self.AXIS_ORDER:
            axis = self._normalize_axis(axis)

        if axis not in self.AXIS_ORDER:
            return

        self.event_index += 1

        if kind in {"auto_step", "rec_step"}:
            kind = "step"

        if kind in {"step", "dir", "ctr", "pulses", "pos"}:
            self.state.setdefault(axis, {})[kind] = value

        self.state[axis]["last_signal"] = signal
        self.state[axis]["last_value"] = value
        self.state[axis]["last_kind"] = kind

        if not self._rendered:
            self._render_base()

        self._fire_axis(axis, kind, value)
        self._render_axis_values(axis)

    def _normalize_axis(self, axis: str) -> str:
        s = str(axis).lower()
        if "arm_h" in s:
            return "arm_h"
        if "arm_v" in s:
            return "arm_v"
        if "arm_t" in s or "tilt" in s:
            return "arm_t"
        if "cam_h" in s:
            return "cam_h"
        if "cam_v" in s:
            return "cam_v"
        if "cam_f" in s or "focus" in s:
            return "cam_f"
        return s

    def _render_base(self) -> None:
        can = self.canvas
        try:
            can.delete("step_dir_owned")
        except Exception:
            return

        w = max(can.winfo_width(), 760)
        h = max(can.winfo_height(), 330)

        left = 132
        right = w - 14
        top = 18
        # Każda oś ma teraz własny pas danych pod STEP/DIR.
        # Zwiększony row_gap daje większy margines nad i pod pomarańczowym tekstem PULS/POS/CTR.
        row_gap = max(50, int((h - 64) / max(1, len(self.AXIS_ORDER))))
        self.geometry = {"left": left, "right": right, "top": top, "row_gap": row_gap, "w": w, "h": h}

        # tło
        can.create_rectangle(0, 0, w, h, fill="#070b0e", outline="", tags="step_dir_owned")

        # pionowa siatka
        for t in range(6):
            x = left + t * ((right - left) / 5)
            can.create_line(x, top - 6, x, h - 28, fill="#162129", tags="step_dir_owned")

        mid_x = left + (right - left) / 2
        can.create_line(mid_x, top - 8, mid_x, h - 28, fill="#ff2b22", width=1, tags="step_dir_owned")
        self.items[("marker",)] = can.create_line(mid_x, top - 8, mid_x, h - 28, fill="#ff2b22", width=1, tags="step_dir_owned")

        for idx, axis in enumerate(self.AXIS_ORDER):
            base_y = top + idx * row_gap
            step_y = base_y + 7
            dir_y = base_y + 21
            data_line_y = base_y + 31
            desc_y = base_y + 40
            self.geometry[(axis, "step_y")] = step_y
            self.geometry[(axis, "dir_y")] = dir_y
            self.geometry[(axis, "data_line_y")] = data_line_y
            self.geometry[(axis, "desc_y")] = desc_y

            # separator
            can.create_line(4, base_y - 5, right, base_y - 5, fill="#101a20", tags="step_dir_owned")

            # ikona osi z istniejącego stylu
            icon = None
            try:
                icon = self.panels._load_timeline_icon(self.AXIS_LABELS[axis])
            except Exception:
                icon = None

            if icon:
                can.create_image(34, base_y + 15, image=icon, anchor="center", tags="step_dir_owned")
            else:
                can.create_text(34, base_y + 15, text=self.AXIS_LABELS[axis], anchor="center",
                                fill=COLORS["muted"], font=("Segoe UI", 7, "bold"), tags="step_dir_owned")

            # S/D i H/L
            can.create_text(58, step_y, text="S", anchor="center", fill=COLORS["green"],
                            font=("Segoe UI", 8, "bold"), tags="step_dir_owned")
            can.create_text(58, dir_y, text="D", anchor="center", fill=COLORS["blue"],
                            font=("Segoe UI", 8, "bold"), tags="step_dir_owned")

            self.items[(axis, "step_hl")] = can.create_text(77, step_y, text="L", anchor="center",
                                                            fill=_TIMELINE_L_COLOR, font=("Segoe UI", 8, "bold"),
                                                            tags="step_dir_owned")
            self.items[(axis, "dir_hl")] = can.create_text(77, dir_y, text="L", anchor="center",
                                                           fill=_TIMELINE_L_COLOR, font=("Segoe UI", 8, "bold"),
                                                           tags="step_dir_owned")

            # linie bazowe jak w Twoim oknie
            can.create_line(left, step_y, right, step_y, fill=COLORS["green"], width=2, tags="step_dir_owned")
            can.create_line(left, dir_y, right, dir_y, fill=COLORS["blue"], width=2, tags="step_dir_owned")

            # Osobny pas danych osi: cienka linia + PULS/POS/CTR pod ikoną i pod S/D/H/L.
            can.create_line(8, data_line_y, 116, data_line_y,
                            fill="#1a252c", width=1, tags="step_dir_owned")
            self.items[(axis, "desc")] = can.create_text(62, desc_y, text="", anchor="center",
                                                         fill="#ff9d00", font=("Segoe UI", 7, "bold"),
                                                         tags="step_dir_owned")

        can.create_text(left, h - 8,
                        text="czerwona linia = chwila odczytu; H/L = aktualny stan STEP/DIR; PULS/POS/CTR = dane osi",
                        anchor="w", fill=COLORS["muted"], font=("Segoe UI", 7), tags="step_dir_owned")
        self._rendered = True

    def _render_values(self) -> None:
        for axis in self.AXIS_ORDER:
            self._render_axis_values(axis)

    def _render_axis_values(self, axis: str) -> None:
        can = self.canvas
        st = self.state.get(axis, {})
        step_val = self._to_level(st.get("step", 0))
        dir_val = self._to_level(st.get("dir", 0))

        step_item = self.items.get((axis, "step_hl"))
        if step_item:
            can.itemconfigure(step_item, text="H" if step_val else "L",
                              fill=_TIMELINE_H_COLOR if step_val else _TIMELINE_L_COLOR)

        dir_item = self.items.get((axis, "dir_hl"))
        if dir_item:
            can.itemconfigure(dir_item, text="H" if dir_val else "L",
                              fill=_TIMELINE_H_COLOR if dir_val else _TIMELINE_L_COLOR)

        desc_item = self.items.get((axis, "desc"))
        if desc_item:
            desc = []
            if st.get("pulses") not in (None, "", 0):
                desc.append(f"PULS:{st.get('pulses')}")
            if st.get("pos") not in (None, "", 0):
                desc.append(f"POS:{st.get('pos')}")
            if st.get("ctr") not in (None, "", 0):
                desc.append(f"CTR:{st.get('ctr')}")
            can.itemconfigure(desc_item, text="  ".join(desc[:3]))

    def _fire_axis(self, axis: str, kind: str, value) -> None:
        can = self.canvas
        g = self.geometry
        if not g:
            return

        left, right = g["left"], g["right"]
        x = left + 16 + ((self.event_index * 13) % max(30, right - left - 38))

        if kind == "dir":
            y = g.get((axis, "dir_y"), 20)
            color = COLORS["blue"]
        elif kind in {"ctr", "pulses", "pos"}:
            y = g.get((axis, "step_y"), 20) - 8
            color = "#ff9d00" if kind != "ctr" else "#ff3333"
        else:
            y = g.get((axis, "step_y"), 20)
            color = COLORS["green"]

        old_key = (axis, kind, "shot")
        old = self.items.get(old_key)
        if old:
            try:
                can.delete(old)
            except Exception:
                pass

        # Krótki, czytelny strzał — nie gęsty prostokąt.
        if kind == "step":
            pts = [x, y + 6, x, y - 6, x + 10, y - 6, x + 10, y + 6, x + 22, y + 6]
            self.items[old_key] = can.create_line(*pts, fill=color, width=2, tags="step_dir_owned")
        else:
            self.items[old_key] = can.create_line(x, y, x + 28, y, fill=color, width=4, tags="step_dir_owned")

        marker = self.items.get(("marker",))
        if marker:
            can.coords(marker, x, g["top"] - 8, x, g["h"] - 28)

    def _to_level(self, value) -> int:
        try:
            return 1 if int(value) > 0 else 0
        except Exception:
            return 1 if str(value).strip().upper() in {"H", "HIGH", "TRUE", "ON", "1"} else 0

class TarzanStepDirMultiSnajper:
    """
    Snajper STEP/DIR bez zgadywania.

    Nie szuka widgetów.
    Nie skanuje Canvasów.
    Nie próbuje wielu metod.

    Wymaga jawnego celu:
        panels.step_dir_snajper_target

    Ten cel musi mieć metodę:
        snajper_step_dir_fire(axis, kind, signal, value, state)

    Jeżeli celu nie ma, Snajper nie udaje refreshu.
    """

    AXIS_ORDER = ("cam_h", "cam_v", "cam_t", "cam_f", "arm_h", "arm_v", "arm_t", "global")

    def __init__(self, panels) -> None:
        self.panels = panels
        self.last_values = {}
        self.axis_state = {}
        self._in_fire = False

    def is_step_dir_signal(self, name: str) -> bool:
        s = str(name).lower()
        return (
            "step" in s or "_stp" in s or
            "dir" in s or "ctr" in s or
            "pulse" in s or "puls" in s or
            s.endswith("_pos") or "_pos" in s or
            s.startswith("axis_") or s.startswith("par_") or
            s.startswith("cnc_") or s.startswith("play_") or s.startswith("rec_")
        )

    def fire(self, name: str, value) -> None:
        if self._in_fire:
            return
        if not self.is_step_dir_signal(name):
            return

        key = str(name)
        normalized = str(value)
        if self.last_values.get(key) == normalized:
            return
        self.last_values[key] = normalized

        axis = self._axis_from_signal(key)
        kind = self._kind_from_signal(key)

        state = self.axis_state.setdefault(axis, {})
        state[kind] = value
        state["last_signal"] = key
        state["last_value"] = value

        target = getattr(self.panels, "step_dir_snajper_target", None)
        if target is None:
            return

        fire_method = getattr(target, "snajper_step_dir_fire", None)
        if fire_method is None:
            return

        self._in_fire = True
        try:
            fire_method(axis, kind, key, value, dict(state))
        finally:
            self._in_fire = False

    def _axis_from_signal(self, name: str) -> str:
        s = name.lower()
        aliases = (
            ("cam_h", ("cam_h", "camera_h", "pozioma_kamery")),
            ("cam_v", ("cam_v", "camera_v", "pionowa_kamery")),
            ("cam_t", ("cam_t", "tilt", "pochyl")),
            ("cam_f", ("cam_f", "focus", "ostrosc", "ostrość")),
            ("arm_h", ("arm_h", "ramie_h", "pozioma_ramienia")),
            ("arm_v", ("arm_v", "ramie_v", "pionowa_ramienia")),
            ("arm_t", ("arm_t", "arm_tilt", "ramie_tilt")),
        )
        for axis, keys in aliases:
            if any(k in s for k in keys):
                return axis
        m = re.search(r"axis[_-]?(\d+)", s)
        if m:
            idx = int(m.group(1))
            if 0 <= idx < len(self.AXIS_ORDER):
                return self.AXIS_ORDER[idx]
            return f"axis_{idx}"
        return "global"

    def _kind_from_signal(self, name: str) -> str:
        s = name.lower()
        if "dir" in s:
            return "dir"
        if "ctr" in s:
            return "ctr"
        if "rec_step" in s:
            return "rec_step"
        if "auto_step" in s:
            return "auto_step"
        if "step" in s or "_stp" in s:
            return "step"
        if "pulse" in s or "puls" in s:
            return "pulses"
        if "_pos" in s or s.endswith("pos"):
            return "pos"
        return "value"


class TarzanParSectionSnajper:
    """
    Snajper sekcyjny PAR.

    Nie robi refresh_all.
    Nie czyści całego Canvas.
    Jedna zmiana sygnału uruchamia tylko sekcję, której dotyczy sygnał.
    Sekcja może odświeżyć kilka własnych elementów, ale nie cały PAR.
    """

    def __init__(self, panels) -> None:
        self.panels = panels
        self.last_values = {}
        self.signal_to_sections = {}
        for section, signals in TARZAN_SNAJPER_PAR_SECTIONS.items():
            for signal in signals:
                self.signal_to_sections.setdefault(signal, set()).add(section)

    def fire(self, signal_name: str, value) -> None:
        if getattr(self, "_in_fire", False):
            return

        key = str(signal_name)
        normalized = str(value)
        if self.last_values.get(key) == normalized:
            return
        self.last_values[key] = normalized

        sections = set(self.signal_to_sections.get(key, set()))
        sections.update(self._infer_sections(key))

        self._in_fire = True
        try:
            for section in sorted(sections):
                self.update_section(section, key, value)
        finally:
            self._in_fire = False

    def _infer_sections(self, signal_name: str) -> set[str]:
        s = signal_name.lower()
        sections = set()

        # RRP / potencjometry operatora
        if "rrp" in s or "p1" in s or "p2" in s:
            sections.add("rrp")

        # OSIE + STEP/DIR. To jest najważniejszy tor live dla podglądu sygnałów.
        if (
            "axis" in s or "os_" in s or "step" in s or "_stp" in s or
            "dir" in s or "_ctr" in s or "ctr" in s or "pulse" in s or
            "puls" in s or "cnc_" in s or "play_" in s
        ):
            sections.add("motor_cards")
            sections.add("step_dir_preview")

        # TAKE time also przesuwa podgląd STEP/DIR.
        if "timecode" in s or "take_time" in s or "protocol_tick" in s:
            sections.add("step_dir_preview")

        if "temp" in s:
            sections.add("temperature")

        if "light" in s or "lux" in s or "bh1750" in s:
            sections.add("light")

        if "xyz" in s or "level" in s or "mma" in s:
            sections.add("xyz")

        if "limit" in s or "kranc" in s or "krańc" in s:
            sections.add("limits")

        if "shock" in s or "shok" in s or "laser" in s:
            sections.add("shock_laser")

        if "sok" in s:
            sections.add("sok")

        if "cnc" in s:
            sections.add("cnc")
            sections.add("step_dir_preview")

        if "status" in s or "log" in s:
            sections.add("logs")

        return sections


    def update_section(self, section: str, signal_name: str, value) -> None:
        method = getattr(self.panels, f"_snajper_update_section_{section}", None)
        if method is not None:
            method(signal_name, value)
            return
        self.panels._snajper_update_section_generic(section, signal_name, value)

class profile_block:
        def __init__(self, name): self.name = name
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

try:
    from core.tarzanAssets import axis_icon
except Exception:
    axis_icon = None

# =====================================================================
# KONFIGURACJA I MAPOWANIA (1:1 Z ORYGINAŁEM)
# =====================================================================

LIMIT_LABELS = {
    "arm_h_auto_limit": "X HOME",
    "arm_h_limit_right": "X MAX",
    "arm_h_limit_left": "X MIN",
    "arm_v_auto_limit": "Y HOME",
    "arm_v_limit_up": "Y MAX",
    "arm_v_limit_down": "Y MIN",
    "cam_h_limit_right": "PAN MAX",
    "cam_h_limit_left": "PAN MIN",
    "cam_v_limit_up": "TILT MAX",
    "cam_v_limit_down": "TILT MIN",
    "cam_tilt_limit": "TILT HOME",
    "cart_limit_end": "CART END",
    "mass_reg_limit_add": "MASS MAX",
    "mass_reg_limit_remove": "MASS MIN",
    "copy_cam_v_limit_up": "TILT MAX",
}

SENSOR_LABELS = {
    "i2c_scl": "MAGISTRALA I2C SCL",
    "i2c_sda": "MAGISTRALA I2C SDA",
    "shock_sensor": "CZUJNIK WSTRZĄSU",
    "rrp_pot_h": "POTENCJOMETR RRP X",
    "rrp_pot_v": "POTENCJOMETR RRP Y",
    "free_aux_pot": "POTENCJOMETR AUX",
    "sw_f1": "PRZYCISK F1",
    "sw_f2": "PRZYCISK F2",
    "sw_f3": "PRZYCISK F3",
    "sw_f4": "PRZYCISK F4",
    "temp_c": "CZUJNIK TEMPERATURY",
}

AXIS_SIGNAL_BINDINGS = {
    "CAM_H": {"step": ["axis_cam_h_step", "axis_cam_h_auto_step", "axis_cam_h_rec_step"], "dir": ["axis_cam_h_dir", "axis_cam_h_auto_dir", "axis_cam_h_rec_dir"], "en": ["axis_cam_h_en"], "pulses": ["axis_cam_h_pulses"], "pos": ["axis_cam_h_pos"], "left": ["sensor_cam_h_limit_left"], "right": ["sensor_cam_h_limit_right"]},
    "CAM_V": {"step": ["axis_cam_v_step", "axis_cam_v_auto_step", "axis_cam_v_rec_step"], "dir": ["axis_cam_v_dir", "axis_cam_v_auto_dir", "axis_cam_v_rec_dir"], "en": ["axis_cam_v_en"], "pulses": ["axis_cam_v_pulses"], "pos": ["axis_cam_v_pos"], "left": ["sensor_cam_v_limit_down"], "right": ["sensor_cam_v_limit_up"]},
    "ARM_T": {"step": ["axis_arm_t_step", "axis_arm_t_auto_step", "axis_arm_t_rec_step"], "dir": ["axis_arm_t_dir", "axis_arm_t_auto_dir", "axis_arm_t_rec_dir"], "en": ["axis_arm_t_en"], "pulses": ["axis_arm_t_pulses"], "pos": ["axis_arm_t_pos"], "left": ["sensor_cam_t_limit"], "right": ["sensor_cam_t_limit"]},
    "CAM_F": {"step": ["axis_cam_f_step", "axis_cam_f_auto_step", "axis_cam_f_rec_step"], "dir": ["axis_cam_f_dir", "axis_cam_f_auto_dir", "axis_cam_f_rec_dir"], "en": ["axis_cam_f_en"], "pulses": ["axis_cam_f_pulses"], "pos": ["axis_cam_f_pos"], "left": [], "right": []},
    "ARM_H": {"step": ["axis_arm_h_step", "axis_arm_h_auto_step", "axis_arm_h_rec_step"], "dir": ["axis_arm_h_dir", "axis_arm_h_auto_dir", "axis_arm_h_rec_dir"], "en": ["axis_arm_h_en"], "pulses": ["axis_arm_h_pulses"], "pos": ["axis_arm_h_pos"], "left": ["sensor_arm_h_limit_left"], "right": ["sensor_arm_h_limit_right"]},
    "ARM_V": {"step": ["axis_arm_v_step", "axis_arm_v_auto_step", "axis_arm_v_rec_step"], "dir": ["axis_arm_v_dir", "axis_arm_v_auto_dir", "axis_arm_v_rec_dir"], "en": ["axis_arm_v_en"], "pulses": ["axis_arm_v_pulses"], "pos": ["axis_arm_v_pos"], "left": ["sensor_arm_v_limit_down"], "right": ["sensor_arm_v_limit_up"]},
    "DRON": {"step": ["axis_dron_step"], "dir": ["axis_dron_dir"], "en": ["axis_dron_en"], "pulses": ["axis_dron_pulses"], "pos": ["axis_dron_pos"], "left": [], "right": []},
}

_AXIS_TIMELINE_ROWS = [
    ("ARM_H", "STEP", ["axis_arm_h_step", "axis_arm_h_auto_step", "axis_arm_h_rec_step"], COLORS["green"]),
    ("ARM_H", "DIR",  ["axis_arm_h_dir", "axis_arm_h_auto_dir", "axis_arm_h_rec_dir"],  COLORS["blue"]),
    ("ARM_V", "STEP", ["axis_arm_v_step", "axis_arm_v_auto_step", "axis_arm_v_rec_step"], COLORS["green"]),
    ("ARM_V", "DIR",  ["axis_arm_v_dir", "axis_arm_v_auto_dir", "axis_arm_v_rec_dir"],  COLORS["blue"]),
    ("CAM_H", "STEP", ["axis_cam_h_step", "axis_cam_h_auto_step", "axis_cam_h_rec_step"], COLORS["green"]),
    ("CAM_H", "DIR",  ["axis_cam_h_dir", "axis_cam_h_auto_dir", "axis_cam_h_rec_dir"],  COLORS["blue"]),
    ("CAM_V", "STEP", ["axis_cam_v_step", "axis_cam_v_auto_step", "axis_cam_v_rec_step"], COLORS["green"]),
    ("CAM_V", "DIR",  ["axis_cam_v_dir", "axis_cam_v_auto_dir", "axis_cam_v_rec_dir"],  COLORS["blue"]),
    ("ARM_T", "STEP", ["axis_arm_t_step", "axis_arm_t_auto_step", "axis_arm_t_rec_step"], COLORS["green"]),
    ("ARM_T", "DIR",  ["axis_arm_t_dir", "axis_arm_t_auto_dir", "axis_arm_t_rec_dir"],  COLORS["blue"]),
    ("CAM_F", "STEP", ["axis_cam_f_step", "axis_cam_f_auto_step", "axis_cam_f_rec_step"], COLORS["green"]),
    ("CAM_F", "DIR",  ["axis_cam_f_dir", "axis_cam_f_auto_dir", "axis_cam_f_rec_dir"],  COLORS["blue"]),
]

_LINKED_SIGNAL_GROUPS = {
    "limit_mass_reg_add": ["limit_mass_reg_add", "par_mass_reg_limit_add"],
    "limit_mass_reg_remove": ["limit_mass_reg_remove", "par_mass_reg_limit_remove"],
    "axis_arm_h_en": ["axis_arm_h_en", "rec_p36_mass_reg_enable", "par_mass_reg_enable"],
    "ui_action_led": ["ui_action_led", "par_lamp_auto_active"],
    "sensor_shock_state": ["sensor_shock_state", "par_shock_sensor_state"],
}

_SIGNAL_LABEL_OVERRIDES = {
    "play_p15_rrp_dir_h_res": "PLAY P15  play_p15_rrp_dir_h_res  REZERWA RRP DIR H",
    "play_p42_res": "PLAY P42  play_p42_res  REZERWA",
    "play_p43_res": "PLAY P43  play_p43_res  REZERWA",
    "play_p44_res": "PLAY P44  play_p44_res  REZERWA",
    "play_p53_rrp_en_res": "PLAY P53  play_p53_rrp_en_res  REZERWA RRP EN",
    "play_p55_bridge_rec_enable": "PLAY P55  play_p55_bridge_rec_enable  MOSTEK / REZERWA",
    "rec_p27_free_limit_res": "REC P27  rec_p27_free_limit_res  PIN WOLNY",
    "rec_p35_free_keyboard_old": "REC P35  rec_p35_free_keyboard_old  PIN WOLNY",
    "rec_p40_free_limit_res": "REC P40  rec_p40_free_limit_res  PIN WOLNY",
    "rec_p41_free_aux_pot": "REC P41  rec_p41_free_aux_pot  REZERWA",
    "rec_p42_free_keyboard_old": "REC P42  rec_p42_free_keyboard_old  REZERWA",
    "rec_p43_free_keyboard_old": "REC P43  rec_p43_free_keyboard_old  REZERWA",
    "rec_p44_free_keyboard_old": "REC P44  CZUJNIK TEMPERATURY",
    "rec_p55_free_cart_spare": "REC P55  rec_p55_free_cart_spare  REZERWA / ZAPAS",
}

_VIOLET_NAME_PARTS = ("kb", "lcd_", "i2c_", "led_data", "led_latch", "led_clk", "poextbus", "res", "free")
_GRAY_NAME_PARTS = ("bridge_",)

_AXIS_ICON_DESCRIPTIONS = {
    "ARM_H": "oś pozioma ramienia",
    "ARM_V": "oś pionowa ramienia",
    "CAM_H": "oś pozioma kamery",
    "CAM_V": "oś pionowa kamery",
    "ARM_T": "oś pochyłu ramienia",
    "CAM_F": "oś ostrości kamery",
}

_AXIS_ICON_NAMES = {
    "ARM_H": "oś pozioma ramienia",
    "ARM_V": "oś pionowa ramienia",
    "CAM_H": "oś pozioma kamery",
    "CAM_V": "oś pionowa kamery",
    "ARM_T": "oś pochyłu ramienia",
    "CAM_F": "oś ostrości kamery",
    "DRON": "DRON",
}

_TIMELINE_HISTORY_LIMIT = 600
_TIMELINE_POINTS_LIMIT = 140
_TIMELINE_H_COLOR = COLORS.get("red", "#ff2b22")
_TIMELINE_L_COLOR = COLORS.get("muted", "#a9b5bd")
_TIMELINE_DEBOUNCE_MS = 80

_ALL_SIGNALS_FORCE_CLICK = {
    "play_p15_rrp_dir_h_res", "play_p38_step_dir_arm_h", "play_p39_step_dir_arm_v", "play_p40_step_dir_arm_tilt",
    "play_p41_mass_reg_enable", "play_p42_res", "play_p43_res", "play_p44_res",
    "play_p46_step_ctr_arm_h", "play_p48_step_ctr_arm_v", "play_p49_step_ctr_arm_tilt",
    "play_p50_step_en_arm_h", "play_p51_step_en_arm_v", "play_p52_step_en_arm_tilt", "play_p53_rrp_en_res",
    "rec_p12_rec_dir_arm_h", "rec_p13_rec_dir_arm_v", "rec_p15_rec_ctr_arm_h", "rec_p16_rec_ctr_arm_v",
    "rec_p27_free_limit_res", "rec_p35_free_keyboard_old", "rec_p36_mass_reg_enable", "rec_p38_auto_enable",
    "rec_p40_free_limit_res", "rec_p41_free_aux_pot", "rec_p42_free_keyboard_old", "rec_p43_free_keyboard_old", "rec_p44_free_keyboard_old",
    "rec_p46_led_f1", "rec_p48_led_f2", "rec_p50_led_f3", "rec_p52_led_f4",
    "rec_p53_copy_cam_v_limit_up",
}

class _ParMassLedV14(tk.Canvas):
    def __init__(self, parent, color_on: str, size: int = 24):
        super().__init__(parent, width=size, height=size, bg=COLORS.get("panel3", "#0c1217"), highlightthickness=0, bd=0)
        self.size = size
        self.color_on = color_on
        self.color_off = "#2a3238"
        self.border_off = "#52636d"
        self.border_on = color_on
        self.value = 0
        self.draw()
    def set(self, value):
        self.value = 1 if value else 0
        self.draw()
    def draw(self):
        self.delete("all")
        fill = self.color_on if self.value else self.color_off
        border = self.border_on if self.value else self.border_off
        self.create_rectangle(2, 2, self.size-2, self.size-2, fill=fill, outline=border, width=2)

_ALL_SIGNALS_PASSIVE = {
    "play_p17_bridge_rec_dir_x", "play_p18_bridge_rec_dir_y", "play_p19_bridge_rec_dir_z",
    "play_p20_bridge_rec_ctr_x", "play_p21_bridge_rec_ctr_y", "play_p22_bridge_rec_ctr_z",
    "rec_p17_bridge_play_dir_x", "rec_p18_bridge_play_dir_y", "rec_p19_bridge_play_dir_z",
    "rec_p20_bridge_play_ctr_x", "rec_p21_bridge_play_ctr_y", "rec_p22_bridge_play_ctr_z",
    "rec_p37_bridge_play_rec_in", "rec_p54_bridge_play_rec_out", "play_p55_bridge_rec_enable",
}

# =====================================================================
# POMOCNICZE KLASY I PROXY
# =====================================================================

class _RowRegistry(dict):
    def __setitem__(self, key, value):
        if key in self:
            current = dict.__getitem__(self, key)
            if isinstance(current, list):
                current.append(value)
                dict.__setitem__(self, key, current)
            else:
                dict.__setitem__(self, key, [current, value])
            return
        dict.__setitem__(self, key, value)

    def set_value(self, key, value):
        current = dict.get(self, key)
        if current is None: return
        if isinstance(current, list):
            for proxy in list(current):
                try: proxy.set(value)
                except Exception: pass
            return
        try: current.set(value)
        except Exception: pass

class _ParValueProxy:
    def __init__(self, callback): self.callback = callback
    def set(self, value):
        try: self.callback(value)
        except Exception: pass

class _CsvProxy:
    def __init__(self, fn): self.fn = fn
    def set(self, value):
        try: self.fn(value)
        except Exception: pass

# =====================================================================
# GŁÓWNA KLASA PANELI PAR
# =====================================================================

class TarzanParPanels:
    def __init__(self, app, bus: TarzanSignalBus) -> None:
        self.app = app
        self.bus = bus
        self.rows: Dict[str, Any] = _RowRegistry()
        self.axis_cards: Dict[str, AxisCard] = {}
        self.log_text: Optional[tk.Text] = None
        self.timeline_canvas: Optional[tk.Canvas] = None
        self._timeline_icon_cache = {}
        self._timeline_after_id = None
        self.nextion_preview_widgets = {}
        self._last_step_states = {}
        self._last_step_states = {}
        self._last_step_states = {}
        self._last_log_snapshot = ()
        self._rrp_operator_updaters = []
        self._last_rrp_refresh_rev = None
        self._last_preview_state = {}
        
        # Logging debounce / deadbands
        self._last_log_values = {}
        self._last_log_times = {}
        
        # Centralny system RRP
        self._rrp_start_ts = time.time()
        self._update_limits_status()
        
        # Subskrypcja sygnałów z SignalBus do aktualizacji widgetów w rows
        self.bus.subscribe(self._on_bus_signal_change)

        # Reset sygnałów jako osobny przycisk w górnym prawym rogu PAR, obok ikony ustawień.
        # Przycisk jest dokładany po zbudowaniu paska aplikacji, bez przebudowy układu PAR.
        self._top_reset_button = None
        try:
            self.app.after_idle(self._install_top_reset_button)
        except Exception:
            try:
                self.app.after(200, self._install_top_reset_button)
            except Exception:
                pass

    def _on_bus_signal_change(self, name: str, state: TarzanSignalState):
        self.snajper_fire_log_take_nextion(name, state.value)
        self._ensure_step_dir_multi_snajper()
        self.step_dir_multi_snajper.fire(name, state.value)
        """Przekazuje zmiany z SignalBus do rejestru rows paneli PAR."""
        self.rows.set_value(name, state.value)

    def panel(self, key: str, parent, title: str) -> Panel:
        return Panel(parent, title=title, on_hide=lambda: self.app.hide_panel(key))

    def reset_signals(self):
        """Reset sygnałów PAR — wydzielona metoda używana przez panel ustawień i górny przycisk."""
        try:
            self.bus.reset_to_defaults()
        except Exception as exc:
            try:
                messagebox.showerror("RESET SYGNAŁÓW", f"Nie udało się zresetować sygnałów:\n{exc}")
            except Exception:
                pass

    def _install_top_reset_button(self):
        """Dodaje jeden przycisk RESET SYGNAŁÓW obok istniejącej ikony ustawień w prawym górnym rogu PAR."""
        if getattr(self, "_top_reset_button", None) is not None:
            try:
                if self._top_reset_button.winfo_exists():
                    return
            except Exception:
                pass

        settings_button = self._find_settings_button(getattr(self, "app", None))
        if settings_button is None:
            try:
                self.app.after(300, self._install_top_reset_button)
            except Exception:
                pass
            return

        parent = settings_button.master
        btn = tk.Button(
            parent,
            text="RESET SYGNAŁÓW",
            bg="#7a251f",
            fg="white",
            activebackground="#9b2f27",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            command=self.reset_signals,
        )

        try:
            pack_info = settings_button.pack_info()
            side = pack_info.get("side", "right")
            pady = pack_info.get("pady", 0)
            btn.pack(side=side, padx=(0, 6), pady=pady)
        except Exception:
            try:
                grid_info = settings_button.grid_info()
                row = int(grid_info.get("row", 0))
                column = int(grid_info.get("column", 0))
                btn.grid(row=row, column=max(0, column - 1), padx=(0, 6), pady=grid_info.get("pady", 0), sticky=grid_info.get("sticky", ""))
            except Exception:
                try:
                    btn.place(in_=parent, relx=1.0, rely=0.0, x=-62, y=4, anchor="ne")
                except Exception:
                    return

        self._top_reset_button = btn

    def _find_settings_button(self, root):
        if root is None:
            return None
        try:
            children = root.winfo_children()
        except Exception:
            return None

        for child in children:
            try:
                if isinstance(child, tk.Button):
                    text = str(child.cget("text"))
                    if text.strip() in {"⚙", "⚙️"} or "USTAW" in text.upper():
                        return child
            except Exception:
                pass

            found = self._find_settings_button(child)
            if found is not None:
                return found

        return None

    def _register_signal_proxy(self, name: str, callback: Callable[[Any], None]):
        self.rows[name] = _ParValueProxy(callback)

    def _scroll_body(self, panel: Panel):
        """Nowoczesny przewijalny korpus panelu z obsługą kółka myszy (v5)."""
        canvas = tk.Canvas(panel.body, bg=COLORS['panel'], highlightthickness=0, bd=0)
        inner = tk.Frame(canvas, bg=COLORS['panel'])
        window_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        def _on_inner_configure(_e=None):
            try: canvas.configure(scrollregion=canvas.bbox('all'))
            except Exception: pass

        def _on_canvas_configure(e):
            try:
                canvas.itemconfigure(window_id, width=e.width)
                canvas.configure(scrollregion=canvas.bbox('all'))
            except Exception: pass

        def _on_mousewheel(event):
            try:
                if getattr(event, 'delta', 0):
                    delta = int(-1 * (event.delta / 120))
                    if delta: canvas.yview_scroll(delta, 'units')
                elif getattr(event, 'num', None) == 4: canvas.yview_scroll(-1, 'units')
                elif getattr(event, 'num', None) == 5: canvas.yview_scroll(1, 'units')
            except Exception: pass
            return 'break'

        def _bind_mousewheel_recursive(widget):
            try:
                widget.bind('<MouseWheel>', _on_mousewheel, add='+')
                widget.bind('<Button-4>', _on_mousewheel, add='+')
                widget.bind('<Button-5>', _on_mousewheel, add='+')
                for child in widget.winfo_children(): _bind_mousewheel_recursive(child)
            except Exception: pass

        inner.bind('<Configure>', lambda e: (_on_inner_configure(e), _bind_mousewheel_recursive(inner)), add='+')
        canvas.bind('<Configure>', _on_canvas_configure)
        panel.body.bind('<MouseWheel>', _on_mousewheel, add='+')
        _bind_mousewheel_recursive(canvas)
        
        canvas.pack(fill='both', expand=True)
        return inner

    # --- SEKCA: OSIE I SILNIKI ---

    def axes(self, parent):
        panel = self.panel("axes", parent, "OSIE — KARTY SILNIKÓW")
        cards_frame = tk.Frame(panel.body, bg=COLORS["panel"])
        cards_frame.pack(fill="both", expand=True)
        
        axes_list = [
            ("ARM_H", "1. OŚ POZIOMA RAMIENIA", "↔"),
            ("ARM_V", "2. OŚ PIONOWA RAMIENIA", "↕"),
            ("CAM_H", "3. OŚ POZIOMA KAMERY", "⟳"),
            ("CAM_V", "4. OŚ PIONOWA KAMERY", "↕"),
            ("ARM_T", "5. OŚ POCHYŁU RAMIENIA", "↧"),
            ("CAM_F", "6. OŚ OSTROŚCI KAMERY", "◎"),
        ]

        for col, (key, title, fallback) in enumerate(axes_list):
            icon_path = None
            if axis_icon:
                try:
                    desc = _AXIS_ICON_DESCRIPTIONS.get(key, "")
                    icon_path = axis_icon(desc, size=64, state="active", ext="png")
                except Exception: pass

            card = AxisCard(
                cards_frame,
                title,
                fallback,
                image_path=icon_path,
                on_step_left=lambda a=key: self._manual_axis_step(a, 0),
                on_step_right=lambda a=key: self._manual_axis_step(a, 1),
            )
            card.grid(row=0, column=col, sticky="nsew", padx=5, pady=4)
            cards_frame.grid_columnconfigure(col, weight=1)
            # Rejestracja proxy dla wszystkich nazw w bindowaniu, aby karta odświeżała się w czasie rzeczywistym
            bind = AXIS_SIGNAL_BINDINGS.get(key, {})
            for group_name, signals in bind.items():
                for sig in signals:
                    self._register_signal_proxy(sig, lambda v, k=key: self.refresh_axis_card(k))

            self.axis_cards[key] = card

        # ETAP 13: Odświeżanie kart przy zmianie blokady bezpieczeństwa
        self._register_signal_proxy("safety_axis_unlock", lambda v: self.refresh_axis_cards())

        # FIX: Tytuł CAM_H
        card_h = self.axis_cards.get("CAM_H")
        if card_h:
            for child in card_h.winfo_children():
                if isinstance(child, tk.Label) and "OŚ POZIOMA KAMERY" in str(child.cget("text")):
                    child.configure(text="3. OŚ POZIOMA KAMERY")

        # FIX: ARM_T STOP label
        card_t = self.axis_cards.get("ARM_T")
        if card_t:
            try:
                left_p = getattr(card_t.end_left, 'master', None)
                if left_p:
                    for c in left_p.winfo_children():
                        if isinstance(c, tk.Label): c.configure(text="STOP")
                right_p = getattr(card_t.end_right, 'master', None)
                if right_p:
                    for c in right_p.winfo_children():
                        if isinstance(c, tk.Label): c.configure(text="")
            except Exception: pass

        # Integracja Mass Regulatora na ARM_V
        card_v = self.axis_cards.get("ARM_V")
        if card_v:
            try:
                led_row = card_v.en.master.master
                add_led = self._add_mass_led_box(led_row, "+MASA", COLORS["amber"])
                rem_led = self._add_mass_led_box(led_row, "−MASA", COLORS["blue"])
                def update_mass_leds(_v=None):
                    add = bool(self.bus.get("sensor_mass_reg_limit_add") or self.bus.get("par_mass_reg_limit_add") or self.bus.get("play_p13_mass_reg_limit_add"))
                    rem = bool(self.bus.get("sensor_mass_reg_limit_remove") or self.bus.get("par_mass_reg_limit_remove") or self.bus.get("play_p23_mass_reg_limit_remove"))
                    add_led.set(add)
                    rem_led.set(rem)
                
                # Register proxies for both canonical and hardware names
                for s in ["sensor_mass_reg_limit_add", "par_mass_reg_limit_add", "play_p13_mass_reg_limit_add", 
                          "sensor_mass_reg_limit_remove", "par_mass_reg_limit_remove", "play_p23_mass_reg_limit_remove"]:
                    self.rows[s] = _ParValueProxy(update_mass_leds)
                
                update_mass_leds()
            except Exception: pass

        self.refresh_axis_cards()
        return panel

    def refresh_axis_cards(self):
        for axis in self.axis_cards:
            self.refresh_axis_card(axis)

    def refresh_axis_card(self, axis: str):
        card = self.axis_cards.get(axis)
        if not card: return
        
        bind = AXIS_SIGNAL_BINDINGS.get(axis, {})
        card.set_step(self._first_value(bind.get("step", [])))
        card.set_dir(self._first_value(bind.get("dir", [])))
        en_names = bind.get("en", [])
        card.set_en(self._first_value(en_names) if en_names else 1)
        card.set_end_left(self._first_value(bind.get("left", [])))
        card.set_end_right(self._first_value(bind.get("right", [])))

        # Odczyt licznika z SignalBus (Źródło Prawdy)
        pulses = self.bus.get(f"axis_{axis.lower()}_pulses")
        if pulses is None or pulses == 0:
            pulses = self.bus.get(f"par_{axis.lower()}_pulses", 0)
        
        card.set_counter(int(float(pulses)))

        # ETAP 13: Odczyt statusów sprzętowych z miniPC
        axis_low = axis.lower()
        ready = self.bus.get(f"axis_{axis_low}_ready", 1)
        alarm = self.bus.get(f"axis_{axis_low}_alarm", 0)
        card.set_ready(ready)
        card.set_alarm(alarm)

        # ETAP 13: Wizualizacja blokady bezpieczeństwa
        locked = not bool(self.bus.get("safety_axis_unlock", 0))
        card.set_locked(locked)

        # Logger silnika — Snajper/LOGI: jeden wpis ruchu osi, nie każdy impuls STEP.
        if not hasattr(card, "_has_logger"):
            def _mk_logger(ax_key, c_ref):
                def _logger():
                    try:
                        now = time.time()
                        dir_val = 1 if c_ref.dir.state else 0
                        key = f"PAR_MOTOR_{ax_key}"
                        state = (dir_val, bool(c_ref.step.state))
                        last_state = self._last_log_values.get(key)
                        last_time = self._last_log_times.get(key, 0)
                        if state != last_state or now - last_time >= 1.0:
                            self._last_log_values[key] = state
                            self._last_log_times[key] = now
                            self.bus.log("PAR_MOTOR", f"{ax_key}: RUCH DIR={dir_val} SRC=PAR_MOTOR")
                    except Exception:
                        pass
                return _logger
            card.on_motor_step_log = _mk_logger(axis, card)
            card._has_logger = True

        # Specjalna obsługa ARM_T Home Limit
        if axis == "ARM_T":
            val = 1 if (self.bus.get("sensor_cam_t_limit") or self.bus.get("cam_tilt_limit") or self.bus.get("play_p10_cam_tilt_limit")) else 0
            card.set_end_left(val)
            card.set_end_right(0)

    # --- SEKCA: OPERATOR (RRP) ---

    def operator(self, parent):
        panel = self.panel("operator", parent, "STEROWANIE OPERATORA (RRP)")
        root = tk.Frame(panel.body, bg=COLORS["panel"])
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        self._rrp_operator_updaters = []

        # TARZAN_SNAJPER: Rejestracja widgetów RRP
        snajper = getattr(self.app, "tarzan_snajper", None)
        tk_adapter = snajper.adapters.get("par_tkinter") if snajper else None

        def _rrp_selected_axis(player: str) -> str:
            return str(self.bus.get(f"par_rrp_{player}_selected_axis", "") or "").upper()

        def _rrp_step_signal(player: str) -> str:
            return str(self.bus.get(f"par_rrp_{player}_step_signal", "") or "")

        def _rrp_dir_signal(player: str) -> str:
            return str(self.bus.get(f"par_rrp_{player}_dir_signal", "") or "")

        def _rrp_pot_signal(player: str) -> str:
            fallback = "sensor_rrp_pot_h" if player == "p1" else "sensor_rrp_pot_v"
            return str(self.bus.get(f"par_rrp_{player}_pot_signal", fallback) or fallback)

        def knob(cell, title, signal, player):
            box = tk.Frame(cell, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
            box.pack(fill="both", expand=True, padx=4, pady=4)
            tk.Label(box, text=title, bg=COLORS["panel3"], fg=COLORS["text"], font=("Segoe UI", 9, "bold")).pack(fill="x")

            # P1/P2 to kanały operatora. Potencjometr nie jest osią; oś jest wybierana osobno z Nextiona.
            knob_signal = _rrp_pot_signal(player)
            speed_signal = f"rrp_{player}_speed_mul"

            state = {
                "value": float(self.bus.get(knob_signal, self.bus.get(signal, 0))),
                "after_id": None,
                "last_step_val": -1,
                "speed_mul": int(float(self.bus.get(speed_signal, 1) or 1)),
                "tick_busy": False,
                "pulse_accumulator": 0.0,
                "last_tick_ts": time.monotonic(),
            }

            val_lbl = tk.Label(box, text="0", bg="#0f171d", fg=COLORS["green"], font=("Consolas", 18, "bold"), pady=4)
            val_lbl.pack(fill="x", padx=6)
            if tk_adapter: tk_adapter.register_widget("rrp_panel", f"{player}_value_label", val_lbl)

            axis_frame = tk.Frame(box, bg=COLORS["panel3"])
            axis_frame.pack(pady=2)
            
            axis_icon_lbl = tk.Label(axis_frame, bg=COLORS["panel3"])
            axis_icon_lbl.pack(side="left", padx=2)
            
            axis_lbl = tk.Label(axis_frame, text="STOP", bg=COLORS["panel3"], fg="#5f6b72", font=("Segoe UI", 10, "bold"))
            axis_lbl.pack(side="left", padx=2)
            if tk_adapter: tk_adapter.register_widget("rrp_panel", f"{player}_axis_label", axis_lbl)

            can = tk.Canvas(box, width=122, height=122, bg=COLORS["panel3"], highlightthickness=0, takefocus=True)
            can.pack(pady=(8, 4))

            # RRP SPEED — lokalne sterowanie istniejącym generatorem impulsów.
            # X1..X4 nie skraca zegara poniżej CZAS_PROBKOWANIA_MS.
            # Czułość ustawia zakres 0..50 imp/s, potencjometr płynnie go koryguje,
            # a mnożnik X1..X4 podbija zakres bez przekraczania twardego limitu 50 imp/s.
            speed_frame = tk.Frame(box, bg=COLORS["panel3"])
            speed_frame.pack(fill="x", padx=8, pady=(0, 8))
            speed_buttons = []

            def paint_speed_buttons():
                active_mul = int(float(state.get("speed_mul", 1) or 1))
                for mul, btn in speed_buttons:
                    active = mul == active_mul
                    btn.configure(
                        bg=COLORS["green"] if active else "#2a3238",
                        fg="#061006" if active else COLORS["text"],
                        activebackground=COLORS["green"],
                        activeforeground="#061006",
                    )

            def set_speed_mul(mul, *, write_bus=True):
                try:
                    mul = int(float(mul or 1))
                except Exception:
                    mul = 1
                if mul not in {1, 2, 3, 4}:
                    mul = 1
                state["speed_mul"] = mul
                paint_speed_buttons()
                if write_bus:
                    self._force_signal(speed_signal, mul, source="PAR_RRP_SPEED")

            for mul in (1, 2, 3, 4):
                btn = tk.Button(
                    speed_frame,
                    text=f"X{mul}",
                    bg="#2a3238",
                    fg=COLORS["text"],
                    activebackground=COLORS["green"],
                    activeforeground="#061006",
                    relief="flat",
                    font=("Segoe UI", 7, "bold"),
                    padx=3,
                    pady=1,
                    command=lambda m=mul: set_speed_mul(m),
                )
                btn.pack(side="left", expand=True, fill="x", padx=1)
                speed_buttons.append((mul, btn))
            set_speed_mul(state["speed_mul"], write_bus=False)

            def drw(v=None):
                if v is not None:
                    state["value"] = max(0.0, min(4095.0, float(v)))
                can.delete("all")
                cx, cy, r = 61, 61, 40
                can.create_arc(cx-r, cy-r, cx+r, cy+r, start=225, extent=270, style="arc", outline="#5f6b72", width=8)
                frac = state["value"] / 4095.0
                angle_deg = 225 + 270 * frac
                angle = math.radians(angle_deg)
                x = cx + math.cos(angle) * (r - 5)
                y = cy - math.sin(angle) * (r - 5)
                
                axis_name = _rrp_selected_axis(player)
                is_active = bool(axis_name)

                knob_color = COLORS["red"] if is_active else "#5f6b72"
                can.create_oval(cx-26, cy-26, cx+26, cy+26, fill="#101820", outline=COLORS["border"], width=2)
                can.create_line(cx, cy, x, y, fill=knob_color, width=4, capstyle=tk.ROUND)
                can.create_oval(cx-5, cy-5, cx+5, cy+5, fill="#dfe6e9", outline="#111")

                axis_lbl.configure(text=axis_name if axis_name else "STOP", fg=COLORS["red"] if is_active else "#5f6b72")
                val_lbl.configure(text=str(int(state["value"])))
                
                # Zespolenie ikon osi
                if is_active and axis_icon:
                    try:
                        desc = _AXIS_ICON_DESCRIPTIONS.get(axis_name, "")
                        path = axis_icon(desc, size=32, state="active")
                        img = self._load_timeline_icon(axis_name) # używamy cache z timeline lub ładujemy małą
                        axis_icon_lbl.configure(image=img)
                        axis_icon_lbl.image = img
                    except Exception: 
                        axis_icon_lbl.configure(image="")
                else:
                    axis_icon_lbl.configure(image="")

            def gen_tick():
                # Generator RRP pracuje na stałej próbce TARZAN.
                # Nie schodzi poniżej CZAS_PROBKOWANIA_MS; prędkość wynika z częstotliwości impulsów/s.
                if state.get("tick_busy"):
                    try:
                        state["after_id"] = self.app.after(max(1, int(CZAS_PROBKOWANIA_MS)), gen_tick)
                    except Exception:
                        pass
                    return

                state["tick_busy"] = True
                sample_ms = max(1, int(CZAS_PROBKOWANIA_MS))
                next_delay = sample_ms
                try:
                    pot_signal = _rrp_pot_signal(player)
                    pot_val = max(0.0, min(4095.0, float(self.bus.get(pot_signal, self.bus.get(signal, 0)))))
                    sens = max(0.0, min(100.0, float(self.bus.get(f"par_rrp_{player}_sens", 50))))
                    pot_norm = pot_val / 4095.0
                    sens_norm = sens / 100.0
                    intensity = pot_norm * sens_norm

                    try:
                        speed_mul = int(float(self.bus.get(speed_signal, state.get("speed_mul", 1)) or 1))
                    except Exception:
                        speed_mul = int(float(state.get("speed_mul", 1) or 1))
                    if speed_mul not in {1, 2, 3, 4}:
                        speed_mul = 1
                    if speed_mul != state.get("speed_mul"):
                        state["speed_mul"] = speed_mul
                        paint_speed_buttons()

                    step_signal = _rrp_step_signal(player)
                    dir_signal = _rrp_dir_signal(player)

                    if intensity > 0.001 and step_signal and dir_signal:
                        # Model prędkości RRP — 20x szybszy w tej samej proporcji:
                        # - zegar generatora zostaje 10 ms (CZAS_PROBKOWANIA_MS),
                        # - czułość 0..100 ustawia bazowy zakres,
                        # - potencjometr płynnie wybiera 0..100% z tego zakresu,
                        # - X1..X4 podbija zakres,
                        # - docelowy sufit jest 20x wyższy niż poprzednie 50 imp/s: 1000 imp/s.
                        max_rrp_rate_hz = 1000.0
                        rate_hz = max_rrp_rate_hz * sens_norm * float(speed_mul) * pot_norm
                        rate_hz = max(0.0, min(max_rrp_rate_hz, rate_hz))

                        now = time.monotonic()
                        last_ts = float(state.get("last_tick_ts", now))
                        elapsed_s = max(0.0, min(0.1, now - last_ts))
                        state["last_tick_ts"] = now

                        state["pulse_accumulator"] = min(30.0, float(state.get("pulse_accumulator", 0.0)) + rate_hz * elapsed_s)

                        pulse_count = int(state["pulse_accumulator"])
                        if pulse_count > 0:
                            # Przy 1000 imp/s i ticku 10 ms nominalnie wypada do 10 impulsów na tick.
                            # Zostawiamy akumulator, ale nie zalewamy Tkintera więcej niż 10 impulsami naraz.
                            pulse_count = min(10, pulse_count)
                            state["pulse_accumulator"] -= pulse_count

                            direction = int(self.bus.get(f"par_rrp_{player}_dir", 0))
                            self._force_signal(dir_signal, direction, source="PAR_GEN")

                            pulse_gap_ms = max(1, sample_ms // max(1, pulse_count))
                            for pulse_idx in range(pulse_count):
                                on_delay = pulse_idx * pulse_gap_ms
                                off_delay = on_delay + 1
                                self.app.after(
                                    on_delay,
                                    lambda name=step_signal: self._force_signal(name, 1, source="PAR_GEN"),
                                )
                                self.app.after(
                                    off_delay,
                                    lambda name=step_signal: self._force_signal(name, 0, source="PAR_GEN"),
                                )

                        # Wartość panelowa pokazuje realną docelową częstotliwość impulsów/s.
                        step_val = int(round(rate_hz))
                        if abs(step_val - state["last_step_val"]) >= 1:
                            state["last_step_val"] = step_val
                            self._set_signal(f"par_rrp_{player}_val", step_val, source="PAR_GEN")
                            self._set_signal(f"rrp_{player}_val", step_val, source="PAR_GEN")
                    else:
                        state["pulse_accumulator"] = 0.0
                        state["last_tick_ts"] = time.monotonic()
                        next_delay = 80
                except Exception:
                    next_delay = 200
                finally:
                    state["tick_busy"] = False
                    try:
                        state["after_id"] = self.app.after(next_delay, gen_tick)
                    except Exception:
                        pass

            def on_wheel(event):
                delta = 0
                if getattr(event, "delta", 0):
                    delta = 1 if event.delta > 0 else -1
                elif getattr(event, "num", None) == 4:
                    delta = 1
                elif getattr(event, "num", None) == 5:
                    delta = -1
                if delta:
                    nv = max(0, min(4095, int(state["value"] + delta * 128)))
                    state["value"] = nv
                    self._force_signal(knob_signal, nv, source="PAR_RRP_POT")
                    drw()
                return "break"

            for w in (can, box, val_lbl, axis_lbl, axis_icon_lbl):
                w.bind("<MouseWheel>", on_wheel)
                w.bind("<Button-4>", on_wheel)
                w.bind("<Button-5>", on_wheel)
                w.bind("<Enter>", lambda e, target=can: target.focus_set())
            
            box.bind("<Destroy>", lambda e: self.app.after_cancel(state["after_id"]) if state.get("after_id") else None)

            self._register_signal_proxy(f"par_rrp_{player}_selected_axis", lambda v: drw())
            self._register_signal_proxy(f"par_rrp_{player}_step_signal", lambda v: drw())
            self._register_signal_proxy(f"par_rrp_{player}_dir_signal", lambda v: drw())
            self._register_signal_proxy(speed_signal, lambda v: set_speed_mul(v, write_bus=False))
            self._register_signal_proxy(knob_signal, lambda v: drw(v))
            self._register_signal_proxy(signal, lambda v: drw(v))
            self._rrp_operator_updaters.append(drw)
            
            drw()
            gen_tick()

        l_f = tk.Frame(root, bg=COLORS["panel"]); l_f.grid(row=0, column=0, sticky="nsew")
        r_f = tk.Frame(root, bg=COLORS["panel"]); r_f.grid(row=0, column=1, sticky="nsew")
        knob(l_f, "POTENCJOMETR RRP X (P1)", "sensor_rrp_pot_h", "p1")
        knob(r_f, "POTENCJOMETR RRP Y (P2)", "sensor_rrp_pot_v", "p2")
        return panel

    # --- SEKCA: SOK (STEROWNIK OBROTOWY) ---

    def sok_panel(self, parent):
        panel = self.panel('sok', parent, 'SOK — STEROWNIK OBROTOWY KURKOWY')
        grid = tk.Frame(panel.body, bg=COLORS['panel'])
        grid.pack(fill='both', expand=True)
        for i in range(2):
            grid.grid_rowconfigure(i, weight=1)
            grid.grid_columnconfigure(i, weight=1)

        sections = [
            ('SOKPan', 'rec_p17_bridge_play_dir_x', 'rec_p20_bridge_play_ctr_x', (), ()),
            ('SOKTilt', 'rec_p18_bridge_play_dir_y', 'rec_p21_bridge_play_ctr_y', (), ()),
            ('SOKFokus', 'rec_p07_copy_dir_focus', 'rec_p05_copy_ctr_focus', (), ('FOKUS', 'POCHYŁ')),
            ('SOKCam', 'rec_p04_copy_dir_cam_v', 'rec_p02_copy_ctr_cam_v', (), ('POZIOM', 'PION')),
        ]

        def draw_section(p_grid, title, ds, cs, extras, opts):
            box = tk.Frame(p_grid, bg=COLORS['panel3'], highlightthickness=1, highlightbackground="#333")
            tk.Label(box, text=title, bg=COLORS['panel3'], fg="white", font=("Segoe UI", 9, "bold")).pack(pady=2)
            
            mode_var = tk.StringVar(value=opts[0] if opts else '')
            if opts:
                mode_buttons = []
                r = tk.Frame(box, bg=COLORS['panel3']);
                r.pack(fill='x', padx=4)

                def paint_mode_buttons():
                    for opt, btn in mode_buttons:
                        active = mode_var.get() == opt
                        btn.configure(
                            bg=COLORS["green"] if active else COLORS["button"],
                            fg="#061006" if active else COLORS["text"],
                        )

                for o in opts:
                    btn = tk.Button(
                        r,
                        text=o,
                        bg=COLORS['button'],
                        fg=COLORS['text'],
                        activebackground=COLORS['button'],
                        activeforeground=COLORS['text'],
                        font=('Segoe UI', 7, 'bold'),
                        command=lambda v=o: (mode_var.set(v), paint_mode_buttons()),
                    )
                    btn.pack(side='left', expand=1, fill='x', padx=1)
                    mode_buttons.append((o, btn))

                paint_mode_buttons()

            can = tk.Canvas(box, width=80, height=80, bg=COLORS['panel3'], highlightthickness=0); can.pack()
            st = {"a": 0}
            
            def dr(ang=0):
                can.delete("all"); cx, cy, r = 40, 40, 30
                can.create_oval(cx-r, cy-r, cx+r, cy+r, fill='#101820', outline='#8d99a3', width=2)
                rd = math.radians(ang)
                for j in range(24):
                    a = math.radians(j * 15 + ang)
                    x1 = cx + math.cos(a) * (r - 2)
                    y1 = cy + math.sin(a) * (r - 2)
                    x2 = cx + math.cos(a) * (r - 10)
                    y2 = cy + math.sin(a) * (r - 10)
                    can.create_line(x1, y1, x2, y2, fill='#dfe6e9', width=2)
                can.create_line(cx, 8, cx, 18, fill=COLORS['red'], width=4, capstyle=tk.ROUND)
            
            def step(d):
                st["a"] = (st["a"] + (30 if d else -30)) % 360; dr(st["a"])
                m = mode_var.get()
                if not m:
                    m = "PAN" if title == "SOKPan" else ("TILT" if title == "SOKTilt" else "")
                sig_map = {
                    'PAN':   (['axis_cam_h_dir'], ['axis_cam_h_step']),
                    'TILT':  (['axis_cam_v_dir'], ['axis_cam_v_step']),
                    'FOKUS': (['axis_cam_f_dir'], ['axis_cam_f_step']),
                    'POCHYŁ':(['axis_arm_t_dir'], ['axis_arm_t_step']),
                    'POZIOM':(['axis_arm_h_dir'], ['axis_arm_h_step']),
                    'PION':  (['axis_arm_v_dir'], ['axis_arm_v_step']),
                }
                dirs, ctrs = sig_map.get(m, ([ds], [cs]))
                for n in dirs: self._force_signal(n, d, source="PAR_SOK")
                self._pulse_many_signals(ctrs, delay_ms=70, src="PAR_SOK")

            btns = tk.Frame(box, bg=COLORS['panel3']); btns.pack(fill='x', padx=4, pady=4)
            tk.Button(
                btns,
                text="◀ LEWO",
                bg=COLORS["button"],
                fg=COLORS["text"],
                activebackground=COLORS["green"],
                activeforeground="#061006",
                command=lambda: step(0),
            ).pack(side="left", expand=1, fill="x")

            tk.Button(
                btns,
                text="PRAWO ▶",
                bg=COLORS["button"],
                fg=COLORS["text"],
                activebackground=COLORS["green"],
                activeforeground="#061006",
                command=lambda: step(1),
            ).pack(side="left", expand=1, fill="x")
            dr(); return box

        for idx, (t, ds, cs, ex, op) in enumerate(sections):
            b = draw_section(grid, t, ds, cs, ex, op)
            b.grid(row=idx//2, column=idx%2, sticky="nsew", padx=4, pady=4)
        return panel

    # --- SEKCA: INFO I LOGI ---

    def info_panel(self, parent):
        panel = self.panel("info", parent, "PANEL INFORMACYJNY")
        names = self.bus.names()
        in_count = out_count = f_count = reserved_count = active_count = 0
        boards = {"PLAY": 0, "REC": 0, "CNC": 0, "VIRTUAL": 0, "SYSTEM": 0}
        for name in names:
            meta = self.bus.get_meta(name)
            value = self.bus.get(name)
            if value not in (0, None, "", False):
                active_count += 1
            if not meta:
                boards["VIRTUAL"] = boards.get("VIRTUAL", 0) + 1
                continue
            boards[meta.plytka] = boards.get(meta.plytka, 0) + 1
            if meta.is_input:
                in_count += 1
            elif meta.is_output:
                out_count += 1
            elif meta.typ == "F" or meta.kierunek == "F":
                f_count += 1
            elif meta.typ == "RESERVED" or meta.kierunek == "RESERVED":
                reserved_count += 1

        def line(label, value, color=None):
            row = tk.Frame(panel.body, bg=COLORS["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["muted"], anchor="w",
                     font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row, text=str(value), bg=COLORS["panel"], fg=color or COLORS["text"], anchor="e",
                     font=("Segoe UI", 9, "bold")).pack(side="right")

        line("Tryb magistrali", self.bus.mode, COLORS["amber"] if self.bus.mode == "TEST" else COLORS["green"])
        line("Sygnały razem", len(names))
        line("Aktywne teraz", active_count, COLORS["green"])
        line("IN / OUT", f"{in_count} / {out_count}")
        line("F / RESERVED", f"{f_count} / {reserved_count}")
        line("PLAY / REC / CNC", f"{boards.get('PLAY',0)} / {boards.get('REC',0)} / {boards.get('CNC',0)}")
        line("Virtual/System", f"{boards.get('VIRTUAL',0)} / {boards.get('SYSTEM',0)}")
        line("TAKE czas", f"{self.bus.take_time_ms} ms")
        line("Historia zmian", len(self.bus.history))
        line("Log", len(self.bus.log_lines))
        
        tk.Label(panel.body, text="TEST: PAR podaje wejścia. OUT: pokazuje logika/TAKE.\nF i RESERVED: widoczne, ale zablokowane.",
                 bg=COLORS["panel"], fg=COLORS["text"], justify="left", anchor="w",
                 font=("Segoe UI", 8)).pack(fill="x", pady=(8, 2))
        return panel

    # --- SEKCA: SYGNAŁY ---

    def all_signals(self, parent):
        panel = self.panel('all_signals', parent, 'WSZYSTKIE SYGNAŁY')
        inner = self._scroll_body(panel)
        for name in self.bus.names():
            self._csv_signal_row(inner, name, self._all_signals_label(name), mode="auto")
        return panel

    def limits(self, parent):
        panel = self.panel("limits", parent, "KRAŃCÓWKI")
        body = tk.Frame(panel.body, bg=COLORS["panel"])
        body.pack(fill="both", expand=True)
        names = self._get_clean_limit_names()
        
        cols = 3
        for i, n in enumerate(names):
            cell = tk.Frame(body, bg=COLORS["panel"])
            cell.grid(row=i//cols, column=i%cols, sticky="ew", padx=3, pady=1)
            cell.grid_columnconfigure(1, weight=1)
            
            bl = self._signal_blocked(n)
            led = Led(cell, size=17, bg=COLORS["panel"], blocked=bl)
            led.grid(row=0, column=0, sticky="w", padx=(0, 4))
            led.set(self.bus.get(n))
            
            l = tk.Label(cell, text=f"{i+1:02d} {self.limit_label(n)}", bg=COLORS["panel"], fg=COLORS["muted"] if bl else COLORS["text"], font=("Segoe UI", 8, "bold"), anchor="w")
            l.grid(row=0, column=1, sticky="ew")
            
            self.rows[n] = _ParValueProxy(led.set)
            if self._signal_clickable_input(n):
                def clk(_e, name=n): self.bus.toggle_input(name, source="PAR_LIMIT")
                for w in (cell, led, l): w.bind("<Button-1>", clk)
        for i in range(cols): body.grid_columnconfigure(i, weight=1, uniform="limit_col")
        return panel

    def sensors(self, parent):
        panel = self.panel("sensors", parent, "CZUJNIKI / ANALOG / I2C")
        body = self._scroll_body(panel)
        for n in self._group_or_search("CZUJNIKI", ["sw_", "sensor", "i2c_", "pot_", "analog"]):
            meta = self.bus.get_meta(n)
            if meta and getattr(meta, "is_input", False) and ("pot_" in n or "analog" in n):
                self._analog_row(body, n, self.sensor_label(n))
            else:
                self._csv_signal_row(body, n, self.sensor_label(n))
        return panel

    # --- SEKCA: CZUJNIKI SPECJALNE ---

    def level_xyz_panel(self, parent):
        panel = self.panel("level_xyz", parent, "CZUJNIK POZIOMU XYZ (MMA7660)")
        body = tk.Frame(panel.body, bg=COLORS["panel"])
        body.pack(fill="both", expand=True)
        w, h = 138, 94
        canvas = tk.Canvas(body, width=w, height=h, bg="#070b0e", highlightthickness=1, highlightbackground=COLORS["border"])
        canvas.pack(side="left", padx=(0, 9), pady=1)
        v_f = tk.Frame(body, bg=COLORS["panel"]); v_f.pack(side="left", fill="both", expand=True)

        # TARZAN_SNAJPER: Rejestracja poziomic
        snajper = getattr(self.app, "tarzan_snajper", None)
        tk_adapter = snajper.adapters.get("par_tkinter") if snajper else None

        # Use canonical names sensor_level_*
        st = {"x": float(self.bus.get("sensor_level_x") or 0), "y": float(self.bus.get("sensor_level_y") or 0), "z": float(self.bus.get("sensor_level_z") or 100)}
        vrs = {a: tk.StringVar(value=f"{a} +0") for a in ("X", "Y", "Z")}
        lbls = {}

        def clamp(v): return max(-100.0, min(100.0, float(v)))
        def calc_z(x, y): return math.sqrt(max(0, 10000 - (x*x + y*y)))

        def draw():
            canvas.delete("all"); cx, cy = w//2, h//2
            x, y, z = clamp(st["x"]), clamp(st["y"]), clamp(st["z"])
            canvas.create_line(9, cy, w-9, cy, fill="#31414a")
            canvas.create_line(cx, 8, cx, h-8, fill="#31414a")
            ox, oy = x*0.08, y*0.08
            canvas.create_polygon(28+ox, 28-oy, 110+ox, 30+oy, 108-ox, 70+oy, 30-ox, 68-oy, fill="#0d222c", outline="#386271", width=2)
            px, py, sz = cx+(x/100)*44, cy-(y/100)*31, 7+(max(0,z)/100)*3
            canvas.create_oval(px-sz, py-sz, px+sz, py+sz, fill=COLORS["green"], outline="#061006")
            for a in "XYZ": vrs[a].set(f"{a} {int(round(st[a.lower()])):+d}")

        def set_a(a, v):
            st[a] = clamp(v)
            sig = f"sensor_level_{a}"
            if a in ("x", "y"): 
                st["z"] = calc_z(st["x"], st["y"])
                self._set_signal("sensor_level_z", st["z"])
            self._set_signal(sig, st[a], source="PAR_XYZ")
            draw()

        cx, cy = w//2, h//2
        for a in ("X", "Y", "Z"):
            r = tk.Frame(v_f, bg=COLORS["panel"]); r.pack(fill="x")
            l = tk.Label(r, textvariable=vrs[a], bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 13, "bold"), anchor="w", width=6)
            l.pack(side="left")
            lbls[a.lower()] = l
            if tk_adapter and a.lower() in ("x", "y"):
                tk_adapter.register_widget("sensors_panel", f"level_{a.lower()}_label", l)
            for t, d in [("X", None), ("+", 1), ("-", -1)]:
                tk.Button(
                    r,
                    text=t,
                    width=2,
                    bg=COLORS["button"],
                    fg=COLORS["green"],
                    activebackground=COLORS["button"],
                    activeforeground=COLORS["green"],
                    command=lambda aa=a.lower(), dd=d: set_a(aa, 0 if dd is None else st[aa] + dd),
                ).pack(side="right", padx=1)

        def drag(e): set_a("x", (e.x-cx)/44*100); set_a("y", -(e.y-cy)/31*100)
        canvas.bind("<B1-Motion>", drag)
        
        # Register in rows for external updates
        for a in ("x", "y", "z"):
            self.rows[f"sensor_level_{a}"] = _ParValueProxy(lambda v, aa=a: set_a_from_bus(aa, v))
        
        def set_a_from_bus(a, v):
            st[a] = clamp(v)
            if a in ("x", "y"): st["z"] = calc_z(st["x"], st["y"])
            draw()

        draw(); return panel

    def _par_click_sensor_panel(self, parent, *, key, title, signal, on_text, off_text, led_size=72):
        panel = self.panel(key, parent, title)
        led = Led(panel.body, size=led_size, bg=COLORS["panel"])
        led.pack(pady=10)
        lbl = tk.Label(panel.body, text=off_text, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"))
        lbl.pack(pady=5)
        
        # TARZAN_SNAJPER: Rejestracja sensora binarnego
        snajper = getattr(self.app, "tarzan_snajper", None)
        tk_adapter = snajper.adapters.get("par_tkinter") if snajper else None
        if tk_adapter: tk_adapter.register_widget("sensors_panel", f"{key}_label", lbl)

        def dr(v=None):
            val = self.bus.get(signal) if v is None else v
            led.set(val); lbl.configure(text=on_text if val else off_text, fg=COLORS["green"] if val else COLORS["text"])
        def tg(_e=None): v=1-(1 if self.bus.get(signal) else 0); self._set_signal(signal, v); dr(v)
        for w in (led, lbl, panel.body): w.bind("<Button-1>", tg)
        self.rows[signal] = _ParValueProxy(dr); dr(); return panel

    def _par_canvas_sensor_slider_panel(self, parent, *, key, title, signal, unit, start, end, decimals=0):
        panel = self.panel(key, parent, title)
        w = tk.Frame(panel.body, bg=COLORS["panel"]); w.pack(fill="both", expand=True)
        h, cw = 88, 38
        can = tk.Canvas(w, width=cw, height=h, bg=COLORS["panel"], highlightthickness=0)
        can.pack(side="left", padx=(0, 7))
        v_l = tk.Label(w, text="", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 15, "bold"))
        v_l.pack(side="left", fill="both", expand=True)
        
        # TARZAN_SNAJPER: Rejestracja sensora analogowego
        snajper = getattr(self.app, "tarzan_snajper", None)
        tk_adapter = snajper.adapters.get("par_tkinter") if snajper else None
        if tk_adapter: tk_adapter.register_widget("sensors_panel", f"{key}_label", v_l)

        def clamp(v):
            try: return max(float(start), min(float(end), float(v or start)))
            except: return float(start)
        def fmt(v): fv = clamp(v); return f"{fv:.{decimals}f} {unit}" if decimals else f"{int(round(fv))} {unit}"
        def dr(v=None):
            curr = clamp(v if v is not None else self.bus.get(signal, start))
            can.delete("all"); can.create_rectangle(14, 5, 24, h-5, fill=COLORS["green"], outline="#063c0a")
            y = 7 + (float(end)-curr)/(max(1.0, float(end)-float(start)))*(h-14)
            can.create_rectangle(5, y-7, 33, y+7, fill="#7b1730", outline="#d65c78", width=2)
            v_l.configure(text=fmt(curr))
        def dg(e): nv = float(end) - ((max(7, min(h-7, e.y))-7)/(h-14))*(max(1.0, float(end)-float(start))); self._set_signal(signal, nv); dr(nv)
        can.bind("<B1-Motion>", dg); self.rows[signal] = _ParValueProxy(dr); dr(); return panel

    def temperature_panel(self, p): return self._par_canvas_sensor_slider_panel(p, key="temp", title="TEMPERATURA (\u00b0C)", signal="sensor_temp_c", unit="\u00b0C", start=-20, end=50, decimals=1)
    def light_bh1750_panel(self, p): return self._par_canvas_sensor_slider_panel(p, key="light", title="ŚWIATŁO (BH1750)", signal="sensor_light_lux", unit="lx", start=0, end=120000)
    def shock_sensor_panel(self, p): return self._par_click_sensor_panel(p, key="shock", title="SHOK", signal="sensor_shock_state", on_text="WSTRZĄS WYKRYTY", off_text="BRAK WSTRZĄSÓW")
    def laser_panel(self, p): return self._par_click_sensor_panel(p, key="laser", title="LASER", signal="sensor_laser_set", on_text="LASER ON", off_text="LASER OFF")

    def automatyka_panel(self, parent):
        panel = self.panel("automatyka", parent, "AUTOMATYKA")
        can = tk.Canvas(panel.body, width=80, height=80, bg=COLORS["panel"], highlightthickness=0)
        can.pack(pady=5)
        status_l = tk.Label(panel.body, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold"), justify="center")
        status_l.pack(fill="x", pady=(0, 4))

        # PLAY P37: krytyczny sygnał bezpieczeństwa mechaniki ramienia.
        # 0 = AUTOMATYKA aktywna, nie wolno ręcznie ruszać ramieniem, piorun czerwony.
        # 1 = NAGRYWANIE RĘCZNE, sterowniki STEP odłączone, automatyka szara.
        sig = "play_p37_step_disconnect_manual"

        def _par_auto_log(msg):
            try:
                self.bus.log("AUTOMATYKA", msg)
                self.update_log()
            except Exception:
                pass

        def draw_bolt(v):
            try:
                manual_disconnect = 1 if int(v or 0) else 0
            except Exception:
                manual_disconnect = 0
            can.delete("all")
            auto_active = not bool(manual_disconnect)
            glow = "#5a1613" if auto_active else "#2c343a"
            body = COLORS["red"] if auto_active else "#66707a"
            can.create_oval(8, 8, 70, 70, fill=glow, outline="")
            can.create_polygon([39, 12, 26, 39, 34, 39, 29, 65, 53, 31, 42, 31, 50, 12], fill=body, outline="#111",
                               width=1)
            if manual_disconnect:
                status_l.configure(text="NAGRYWANIE RĘCZNE\nPLAY P37=HIGH — STEP ODŁĄCZONE", fg=COLORS["muted"])
            else:
                status_l.configure(text="AUTOMATYKA AKTYWNA\nPLAY P37=LOW — NIE RUSZAĆ RĘCZNIE", fg=COLORS["red"])

        draw_bolt(self.bus.get(sig, 0))

        def tg(_e):
            nv = 0 if self.bus.get(sig, 0) else 1
            if nv:
                _par_auto_log("SENT PLAY P37=1 — aktywny systemowy sygnał odłączenia STEP")
                _par_auto_log("PLAY P37=1: aktywny systemowy sygnał odłączenia STEP, silniki odłączone")
            else:
                _par_auto_log("SENT PLAY P37=0 — automatyka aktywna, żądanie przywrócenia STEP")
                _par_auto_log("AUTOMATYKA: PLAY P37=0, automatyka aktywna, zakaz ręcznego ruchu ramieniem")
            self._set_signal(sig, nv, "PAR_AUTOMATYKA")
            draw_bolt(nv)

        can.bind("<Button-1>", tg)
        try:
            can.configure(cursor="hand2")
        except Exception:
            pass
        self._register_signal_proxy(sig, draw_bolt)
        return panel

    def _analog_row(self, parent, name, label):
        frame = tk.Frame(parent, bg=COLORS["panel"])
        frame.pack(fill="x", pady=3)
        tk.Label(frame, text="▰", bg=COLORS["panel"], fg=COLORS["amber"], width=2).pack(side="left")
        tk.Label(frame, text=label, bg=COLORS["panel"], fg=COLORS["text"], width=22, anchor="w").pack(side="left")
        val_lbl = tk.Label(frame, text=str(self.bus.get(name, 0)), bg=COLORS["panel"], fg=COLORS["green"], width=7)
        val_lbl.pack(side="right")
        
        def on_scale(v):
            v_int = int(float(v))
            self._set_signal(name, v_int)
            val_lbl.config(text=str(v_int))
            
        scale = tk.Scale(frame, from_=0, to=4095, orient="horizontal", bg=COLORS["panel"], troughcolor="#263741",
                         fg=COLORS["text"], highlightthickness=0, showvalue=False,
                         command=on_scale)
        scale.set(self.bus.get(name, 0))
        scale.pack(side="right", fill="x", expand=True, padx=5)
        self._register_signal_proxy(name, lambda v: [scale.set(v), val_lbl.config(text=str(v))])
        return frame

    def _set_signal(self, name, value, source="PAR_SIM"):
        try:
            # ETAP 8: Delegacja przez Bridge (który obsłuży LIVE)
            if hasattr(self.app, "bridge"):
                m = self.bus.get_meta(name)
                is_input = getattr(m, "is_input", False) or name.startswith("par_")
                if is_input:
                    self.app.bridge.set_input(name, value, source=source)
                else:
                    self.app.bridge.write_output(name, value, source=source)
                return

            m = self.bus.get_meta(name)
            if not m:
                self.bus.force_signal(name, value, source=source)
                return
            if getattr(m, "is_input", False) or name.startswith("par_"):
                self.bus.set_input(name, value, source=source)
            else:
                self.bus.write_output(name, value, source=source)
        except Exception: pass

    def _force_signal(self, name, value, source="PAR_FORCE"):
        """Wymusza sygnał przez Bridge (obsługa LIVE) (Etap 7)."""
        try:
            if hasattr(self.app, "bridge"):
                self.app.bridge.force_signal(name, value, source=source)
                return
            self.bus.force_signal(name, value, source=source)
        except Exception: pass

    def _final_force_or_toggle(self, name: str):
        try:
            curr = self.bus.get(name, 0)
            nv = 1 if curr == 0 else 0
            self._set_signal(name, nv)
        except Exception: pass

    def _final_signal_style(self, name: str):
        lower = (name or "").lower()
        meta = self.bus.get_meta(name)
        if name == "play_p15_rrp_dir_h_res": return "neutral"
        if name in _ALL_SIGNALS_PASSIVE or "bridge_" in lower: return "gray"
        if lower.startswith("cnc_"): return "gray"
        if any(k in lower for k in ("kb", "lcd_", "i2c_", "led_data", "led_latch", "led_clk", "poextbus")): return "violet"
        if any(k in lower for k in ("_res", "free_", "_free")): return "violet"
        if meta and (getattr(meta, "is_forbidden", False) or getattr(meta, "typ", "") in {"F", "RESERVED"} or getattr(meta, "kierunek", "") in {"F", "RESERVED"}):
            return "violet"
        return "normal"

    def _all_signals_clickable(self, name: str):
        if name in _ALL_SIGNALS_PASSIVE: return False
        if name in _ALL_SIGNALS_FORCE_CLICK: return True
        meta = self.bus.get_meta(name)
        if meta is None: return True
        if getattr(meta, "is_input", False): return True
        return False

    def _all_signals_label(self, name: str):
        if name in _SIGNAL_LABEL_OVERRIDES: return _SIGNAL_LABEL_OVERRIDES[name]
        meta = self.bus.get_meta(name)
        board = str(meta.plytka).upper() if (meta and meta.plytka) else ""
        pin = str(meta.pin if (meta and meta.pin is not None) else (meta.kanal if meta and meta.kanal else "-")).upper()
        opis = " ".join(str(meta.opis or "").split()) if meta else ""
        extra = ""
        lower = name.lower()
        if name in _ALL_SIGNALS_PASSIVE or "bridge_" in lower: extra = "  [MOSTEK]"
        elif any(k in lower for k in ("_res", "free_", "_free")): extra = "  [REZERWA]"
        elif lower.startswith("cnc_"): extra = "  [CNC]"

        # zmiana wyswielania nazwy
        #if opis: return f"{board} {pin}  {name}  {opis}{extra}"
        #return f"{board} {pin}  {name}{extra}"

        if opis: return f"{board} {pin}  {name}"
        return f"{board} {pin}  {name}"

    def _csv_signal_row(self, parent, name, label, mode="normal", clickable=None):
        f = tk.Frame(parent, bg=COLORS["panel"])
        f.pack(fill="x", pady=1)

        style = mode if mode != "auto" else self._final_signal_style(name)
        is_clickable = clickable if clickable is not None else self._all_signals_clickable(name)
        meta = self.bus.get_meta(name)

        # Diody po lewej ( side="left" ) 1:1 z oryginałem
        led = Led(f, size=22, bg=COLORS["panel"], blocked=(style=="violet"))
        led.pack(side="left", padx=(5, 10))
        led.set(self.bus.get(name, 0))
        self.rows[name] = _ParValueProxy(led.set)

        fg = COLORS.get(style, COLORS["text"]) if style in {"violet", "gray"} else COLORS["text"]
        lbl = tk.Label(f, text=label, bg=COLORS["panel"], fg=fg, anchor="w", font=("Segoe UI", 10))
        lbl.pack(side="left", fill="x", expand=True)

        if meta and meta.typ == "ANALOG":
            # Suwak dla sygnałów analogowych
            sc = tk.Scale(f, from_=0, to=255, orient="horizontal", showvalue=0, width=8,
                        bg=COLORS["panel"], highlightthickness=0, command=lambda v: self._set_signal(name, int(v)))
            sc.set(self.bus.get(name, 0))
            sc.pack(side="right", padx=5)
            sc.configure(length=60)
            self.rows[name] = _ParValueProxy(lambda v, s=sc, l=led: (s.set(v), l.set(v)))

        if is_clickable:
            def clk(e): self._final_force_or_toggle(name)
            for w in (f, lbl, led): 
                w.bind("<Button-1>", clk)
                w.configure(cursor="hand2")
        return f

    def _add_mass_led_box(self, parent, label, col):
        f = tk.Frame(parent, bg=COLORS["panel3"], padx=4)
        f.pack(side="left", padx=2, fill="x", expand=True)
        tk.Label(f, text=label, fg=col, bg=COLORS["panel3"], font=("Segoe UI", 8, "bold")).pack()
        led = _ParMassLedV14(f, color_on=col, size=24)
        led.pack(pady=2)
        return led

    def _increment_axis_counter(self, ax, dir_val, amount=1):
        """Mechanizm pomocniczy - liczniki są teraz w SignalBus."""
        pass

    def _manual_axis_step(self, ax, dir):
        b = AXIS_SIGNAL_BINDINGS.get(ax, {})
        # Każdy generator produkuje STEP/DIR
        for n in b.get("dir", []): 
            if hasattr(self.app, "bridge"):
                self.app.bridge.force_signal(n, dir, source="PAR_MANUAL")
            else:
                self._force_signal(n, dir, source="PAR_MANUAL")
        
        # Wygeneruj 10 zboczy narastających na szynie (zostaną zliczone przez on_state_change)
        # Używamy lekkiego opóźnienia, aby UI i Timeline nadążyły z rysowaniem
        for i in range(10):
            def f1(steps=b.get("step", [])):
                for n in steps:
                    self._force_signal(n, 1, source="PAR_MANUAL")
            def f2(steps=b.get("step", [])):
                for n in steps:
                    self._force_signal(n, 0, source="PAR_MANUAL")
            
            self.app.after(i * 15, f1)
            self.app.after(i * 15 + 7, f2)

    def _pulse_many_signals(self, names, delay_ms=10, src="PAR_PULSE"):
        for n in names:
            self._force_signal(n, 1, source=src)
            self.app.after(delay_ms, lambda name=n: self._force_signal(name, 0, source=src))

    def _first_value(self, names: List[str]):
        for n in names:
            if self.bus.exists(n): return 1 if self.bus.get(n) else 0
        return 0

    def _group_or_search(self, group: str, needles: List[str]):
        res = []
        for name in self.bus.names():
            m = self.bus.get_meta(name)
            if (m and m.grupa == group) or any(k in name.lower() for k in needles): res.append(name)
        return sorted(list(set(res)))

    def _get_clean_limit_names(self):
        raw = self._group_or_search("KRAŃCÓWKI", ["limit"])
        names, seen = [], set()
        for n in raw:
            lbl = self.limit_label(n)
            if any(k in f"{n} {lbl}".upper() for k in ("WOLNY", "FREE", "STATUS")): continue
            if lbl.upper() in seen: continue
            seen.add(lbl.upper()); names.append(n)
        return names

    def _update_limits_status(self):
        names = self._get_clean_limit_names()
        active = [str(i+1) for i, n in enumerate(names) if self.bus.get(n)]
        res = "0" if not active else ",".join(active)
        self._force_signal("sensor_limits_status", res, source="PAR_LIMIT_MONITOR")

    def limit_label(self, name: str):
        clean = name
        if clean.startswith(("play_p", "rec_p")):
            parts = clean.split("_", 3)
            if len(parts) >= 3: clean = "_".join(parts[2:])
        elif clean.startswith("par_"):
            clean = clean[4:]
        return LIMIT_LABELS.get(clean, clean.upper().replace("_", " "))
    def sensor_label(self, name: str):
        clean = name
        if clean.startswith("sensor_"): clean = clean[7:]
        return SENSOR_LABELS.get(clean, clean.upper().replace("_", " "))

    def _signal_blocked(self, n): m = self.bus.get_meta(n); return bool(m and getattr(m, "is_forbidden", False))
    def _signal_clickable_input(self, n): m = self.bus.get_meta(n); return bool(m and m.is_input)

    # --- SYNCHRONIZACJA I TIMELINE ---




    def register_step_dir_snajper_target(self, target) -> None:
        """
        Jawne podpięcie celu STEP/DIR.
        target musi mieć:
            snajper_step_dir_fire(axis, kind, signal, value, state)
        """
        self.step_dir_snajper_target = target




    def _ensure_log_take_nextion_snajper_targets(self) -> None:
        if not hasattr(self, "log_snajper_target") or self.log_snajper_target is None:
            self.log_snajper_target = TarzanLogSnajperTarget()
        if not hasattr(self, "take_snajper_target") or self.take_snajper_target is None:
            self.take_snajper_target = TarzanTakeSnajperTarget(self)
        # NEXTION fizyczny idzie przez app.tarzan_snajper i adapter physical_nextion.
        self.nextion_snajper_target = None

    def register_log_snajper_widget(self, widget) -> None:
        self._ensure_log_take_nextion_snajper_targets()
        self.log_snajper_target.set_widget(widget)

    def _ensure_step_dir_multi_snajper(self) -> None:
        if not hasattr(self, "step_dir_multi_snajper") or self.step_dir_multi_snajper is None:
            self.step_dir_multi_snajper = TarzanStepDirMultiSnajper(self)

    def _ensure_section_snajper(self) -> None:
        """
        TARZAN_SNAJPER STAGE5:
        Gwarantuje, że sekcyjny Snajper istnieje zanim on_state_change
        zacznie obsługiwać szybkie sygnały z BUS.
        """
        if not hasattr(self, "section_snajper") or self.section_snajper is None:
            self.section_snajper = TarzanParSectionSnajper(self)


    def snajper_fire_log_take_nextion(self, name: str, value) -> None:
        """
        Celowe strzały Snajpera dla LOGI / TAKE / NEXTION.
        Nie odświeża całych paneli.
        Nie zapisuje do BUS.
        """
        self._ensure_log_take_nextion_snajper_targets()

        s = str(name).lower()

        # LOGI — tylko sygnały log/status/error, żeby nie zalewać logu STEPami.
        if "log" in s or "status" in s or "error" in s or "par_error" in s:
            pass
# TAKE — gdy jest otwarty TAKE i idą ms / TC.
        if (
            "take_time" in s or "take_timecode" in s or
            "take_ms" in s or "time_ms" in s or
            "take_number" in s or "take_status" in s
        ):
            self.take_snajper_target.snajper_take_fire(name, value, None)

        # NEXTION — przez centralny katalog celów Snajpera, bez lokalnych map panelu.
        app = getattr(self, "app", None)
        snajper = getattr(app, "tarzan_snajper", None) if app is not None else None
        if snajper is not None:
            snajper.fire_from_signal(name, value)

        # Usunięto: cykliczne update_log() i refresh_axis_cards()
        # Te akcje powinny iść przez Snajpera lub być wyzwalane zdarzeniowo.
        if "keyboard" in s or "free_keyboard" in s or "rec_p41" in s or "rec_p42" in s or "rec_p43" in s:
            if value: # Tylko przy aktywacji/wpisaniu
                self.update_log()

    def on_state_change(self, name, state):
        is_limit = "limit" in name.lower() or (self.bus.get_meta(name) and self.bus.get_meta(name).grupa == "KRAŃCÓWKI")
        if is_limit: 
            self._update_limits_status()
        
        val = state.value
        self.snajper_fire_log_take_nextion(name, val)
        if name in {"sensor_level_x", "sensor_level_y", "sensor_level_z", "level_x", "level_y", "level_z"}:
            app = getattr(self, "app", None)
            snajper = getattr(app, "tarzan_snajper", None) if app is not None else None
            if snajper is not None:
                xyz_value = {
                    "x": self.bus.get("sensor_level_x", self.bus.get("level_x", 0)),
                    "y": self.bus.get("sensor_level_y", self.bus.get("level_y", 0)),
                    "z": self.bus.get("sensor_level_z", self.bus.get("level_z", 0)),
                }
                snajper.fire("sensor_xyz", xyz_value)
        self._ensure_step_dir_multi_snajper()
        self.step_dir_multi_snajper.fire(name, val)
        self.rows.set_value(name, val)
        self._ensure_section_snajper()
        self.section_snajper.fire(name, val)

        # Logowanie krańcówek
        if is_limit and name != "sensor_limits_status" and val != state.previous_value:
            limit_names = self._get_clean_limit_names()
            if name in limit_names:
                idx = limit_names.index(name)
                nr = f"{idx+1:02d}"
                lbl = self.limit_label(name)
                status = "AKTYWACJA" if val == 1 else "OK"
                self.bus.log("LIMIT", f"{nr} {status}: {lbl} SRC={state.source}")
        
                # --- ROZSZERZONE LOGOWANIE (Zgodnie z wytycznymi) ---
        if val != state.previous_value:
            if name == "sensor_laser_set":
                self.bus.log("LASER", ("ON" if val else "OFF") + f" SRC={state.source}")
            elif name == "sensor_shock_state":
                self.bus.log("SHOCK", ("AKTYWACJA" if val else "OK") + f" SRC={state.source}")
            elif name == "ui_action_led":
                self.bus.log("PRACA", ("START" if val else "STOP") + f" SRC={state.source}")
            elif name in {"ui_f1_sw", "ui_f2_sw", "ui_f3_sw", "ui_f4_sw"} and val == 1:
                f_name = name.split("_")[-1].upper()
                self.bus.log("PRZYCISK", f"{f_name} AKTYWACJA SRC={state.source}")
            elif name == "sensor_temp_c":
                last = self._last_log_values.get(name, -999)
                if abs(val - last) >= 0.5:
                    self._last_log_values[name] = val
                    self.bus.log("SENSOR", f"TEMPERATURA {val:.1f}C SRC={state.source}")
            elif name == "sensor_light_lux":
                last = self._last_log_values.get(name, -999)
                diff = abs(val - last)
                if diff >= 500 or (last > 0 and diff >= 0.2 * last):
                    self._last_log_values[name] = val
                    self.bus.log("SENSOR", f"ŚWIATŁO {int(val)}lx SRC={state.source}")
            elif name in {"sensor_level_x", "sensor_level_y", "sensor_level_z"}:
                last = self._last_log_values.get(name, -999)
                if abs(val - last) >= 10:
                    self._last_log_values[name] = val
                    axis = name.split("_")[-1].upper()
                    self.bus.log("SENSOR", f"POZIOM {axis}: {int(val)} SRC={state.source}")
            elif name == "par_rrp_refresh_needed":
                # Celowane odświeżenie kart osi bez refresh_all
                if val:
                    self.refresh_axis_cards()

        if val == 1 and state.previous_value == 0:
            # SOK: System Odczytu Kierunku przez nazwy kanoniczne
            sok_map = {
                "axis_cam_h_step": ("PAN", "axis_cam_h_dir"),
                "axis_cam_v_step": ("TILT", "axis_cam_v_dir"),
                "axis_cam_f_step": ("FOKUS", "axis_cam_f_dir"),
                "axis_arm_t_step": ("POCHYŁ", "axis_arm_t_dir"),
                "axis_arm_h_step": ("RAMIĘ H", "axis_arm_h_dir"),
                "axis_arm_v_step": ("RAMIĘ V", "axis_arm_v_dir")
            }
            if name in sok_map:
                sec, d_sig = sok_map[name]
                now = time.time()
                if now - self._last_log_times.get(name, 0) >= 0.5:
                    self._last_log_times[name] = now
                    dir_val = self.bus.get(d_sig, 0)
                    kier = "PRAWO" if dir_val else "LEWO"
                    self.bus.log("SOK", f"{sec} RUCH {kier} SRC={state.source}")

        # --- CENTRALNE ZLICZANIE Z DEDUPLIKACJĄ ---
        # Pominięto: liczniki impulsów są teraz obsługiwane przez SignalBus natywnie.

        # Linki sygnałów
        if name in _LINKED_SIGNAL_GROUPS:
            for extra in _LINKED_SIGNAL_GROUPS[name]:
                if extra != name and self.bus.exists(extra):
                    if self.bus.get(extra) != val:
                        self._force_signal(extra, val, source="PAR_LINK_SYNC")

        # Specyficzne linki dla osi i innych grup (1:1 z oryginałem)
        try:
            if name in {"play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"}:
                for extra in ["play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_enable"]:
                    if extra != name and self.bus.exists(extra):
                        self._force_signal(extra, val, source="PAR_LINK")
            elif name in {"play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"}:
                for extra in ["play_p13_mass_reg_limit_add", "par_mass_reg_limit_add"]:
                    if extra != name and self.bus.exists(extra):
                        self._force_signal(extra, val, source="PAR_LINK")
            elif name in {"play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"}:
                for extra in ["play_p23_mass_reg_limit_remove", "par_mass_reg_limit_remove"]:
                    if extra != name and self.bus.exists(extra):
                        self._force_signal(extra, val, source="PAR_LINK")
            elif name in {"par_lamp_auto_active", "play_p16_action_led"}:
                for extra in ["par_lamp_auto_active", "play_p16_action_led"]:
                    if extra != name and self.bus.exists(extra):
                        self._force_signal(extra, val, source="PAR_LINK")
            elif name in {"par_shock_sensor_state", "rec_p39_shock_sensor"}:
                for extra in ["par_shock_sensor_state", "rec_p39_shock_sensor"]:
                    if extra != name and self.bus.exists(extra):
                        self._force_signal(extra, val, source="PAR_LINK")
        except Exception: pass

        # Odświeżanie kart osi (wizualizacja Step/Dir) - WYŁĄCZONE DLA SNAJPERA
        # for b in AXIS_SIGNAL_BINDINGS.values():
        #     if any(name in group for group in b.values()):
        #         now = time.time()
        #         if now - getattr(self, "_last_axis_card_refresh", 0) > 0.1: # max 10 FPS dla kart osi (oszczędność CPU)
        #             self._last_axis_card_refresh = now
        #             self.refresh_axis_cards()
        #         break

        # STEP/DIR Snajper:
        # Nie wołamy redraw po sygnale live, bo redraw czyści canvas i usuwa strzały.
        # Strzały są wykonywane wcześniej przez self.step_dir_multi_snajper.fire(...).

        # LOGI: odśwież, gdy zmieni się dowolna istniejąca kolejka logów BUS.
        try:
            log_count = 0
            for attr in ("log_lines", "logs", "log_queue", "events"):
                if hasattr(self.bus, attr):
                    candidate = getattr(self.bus, attr)
                    if candidate is not None:
                        log_count = len(candidate)
                        break
            if log_count != getattr(self, "_last_seen_log_count", -1):
                self._last_seen_log_count = log_count
                self.update_log()
        except Exception:
            pass


    def timeline(self, parent):
        p = self.panel("timeline", parent, "PODGLĄD SYGNAŁÓW — STEP / DIR")
        self.timeline_canvas = tk.Canvas(p.body, bg="#070b0e", height=330, highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True, pady=4)
        self.step_dir_canvas = self.timeline_canvas
        target = TarzanStepDirPreviewTarget(self, self.timeline_canvas)
        self.register_step_dir_snajper_target(target)
        self.timeline_canvas.bind("<Configure>", lambda e, t=target: t.redraw())
        self.timeline_canvas.after_idle(target.redraw)
        return p

    def _schedule_timeline_redraw(self):
        target = getattr(self, "step_dir_snajper_target", None)
        if target is not None and hasattr(target, "redraw"):
            target.redraw()

    def _do_draw_timeline(self):
        self._timeline_after_id = None
        target = getattr(self, "step_dir_snajper_target", None)
        if target is not None and hasattr(target, "redraw"):
            target.redraw()

    def _axis_icon_path(self, axis_key: str):
        if not axis_icon: return None
        try: return axis_icon(_AXIS_ICON_NAMES.get(axis_key, axis_key), size=64, state="active", ext="png")
        except Exception: return None

    def _load_timeline_icon(self, axis_key: str):
        if not hasattr(self, "_timeline_icon_cache"): self._timeline_icon_cache = {}
        if axis_key in self._timeline_icon_cache: return self._timeline_icon_cache[axis_key]
        path = self._axis_icon_path(axis_key)
        photo = None
        if path:
            try:
                from pathlib import Path as _Path
                if _Path(path).exists():
                    photo = tk.PhotoImage(file=str(path))
                    if photo.width() > 36:
                        factor = max(1, int(round(photo.width() / 32)))
                        photo = photo.subsample(factor, factor)
            except Exception: photo = None
        self._timeline_icon_cache[axis_key] = photo
        return photo

    def draw_timeline(self):
        target = getattr(self, "step_dir_snajper_target", None)
        if target is not None and hasattr(target, "redraw"):
            target.redraw()

    def ui_panel(self, p): return self.ui(p)
    def ui(self, parent):
        p = self.panel("ui", parent, "UI PANEL PLAY / REC")
        g = tk.Frame(p.body, bg=COLORS["panel"])
        g.pack(fill="x")
        btns = [("F1", "rec_p45_sw_f1", "rec_p46_led_f1"), ("F2", "rec_p47_sw_f2", "rec_p48_led_f2"),
                ("F3", "rec_p49_sw_f3", "rec_p50_led_f3"), ("F4", "rec_p51_sw_f4", "rec_p52_led_f4")]
        for i, (l, sw, ls) in enumerate(btns):
            c = tk.Frame(g, bg="#0f171d", highlightbackground="#30424f", highlightthickness=1)
            c.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            led = Led(c, size=28, bg="#0f171d")
            led.pack(pady=(7, 4))
            led.set(self.bus.get(ls))

            b = tk.Button(
                c,
                text=l,
                bg="#1a242d",
                fg="#f2f7fb",
                activebackground=COLORS["green"],
                activeforeground="#061006",
                relief="flat",
                font=("Segoe UI", 16, "bold"),
                height=2,
            )

            b.pack(fill="x", padx=7, pady=(0, 3))
            
            # Podkreślenie aktywnego klawisza
            f_led = tk.Frame(c, bg="#30424f", height=4)
            f_led.pack(fill="x", padx=7, pady=(0, 7))

            def _par_ui_log(kind, msg):
                try:
                    self.bus.log(kind, msg)
                    self.update_log()
                except Exception:
                    pass

            def _f_button_press(_event=None, sig=sw, label=l):
                _par_ui_log("UI_PANEL", f"{label} BUTTON PRESS -> {sig}=1")
                self._set_signal(sig, 1, "PAR_UI_BUTTON")
                try:
                    self.update_log()
                except Exception:
                    pass

            def _f_button_release(_event=None, sig=sw, label=l):
                _par_ui_log("UI_PANEL", f"{label} BUTTON RELEASE -> {sig}=0")
                self._set_signal(sig, 0, "PAR_UI_BUTTON")
                try:
                    self.update_log()
                except Exception:
                    pass

            def _f_led_toggle(_event=None, sig=ls, label=l, ld=led):
                try:
                    nv = 0 if int(getattr(ld, "state", self.bus.get(sig, 0)) or 0) else 1
                except Exception:
                    nv = 1
                # To jest osobny sygnał PoKeys LED.
                # Kliknięcie diody zmienia UI od razu i dopiero wysyła fizyczny test LED przez Bridge/TSP.
                try:
                    ld.set(nv)
                except Exception:
                    pass
                _par_ui_log("UI_PANEL", f"{label} LED {'ON' if nv else 'OFF'} -> {sig}={nv}")
                self._set_signal(sig, nv, "PAR_UI_LED")
                try:
                    self.update_log()
                except Exception:
                    pass

            b.bind("<ButtonPress-1>", _f_button_press)
            b.bind("<ButtonRelease-1>", _f_button_release)
            b.bind("<Leave>", _f_button_release)
            led.bind("<Button-1>", _f_led_toggle)
            try:
                led.configure(cursor="hand2")
            except Exception:
                pass
            
            self.rows[ls] = _ParValueProxy(lambda v, ld=led: ld.set(v))
            self.rows[sw] = _ParValueProxy(lambda v, bt=b, fl=f_led: (
                bt.configure(bg=COLORS["green"] if v else "#1a242d", fg="#061006" if v else "#f2f7fb"),
                fl.configure(bg=COLORS["green"] if v else "#30424f")
            ))
        for i in range(4): g.grid_columnconfigure(i, weight=1)
        return p

    def mass_regulator_panel(self, parent):
        p = self.panel("mass_regulator", parent, "REGULATOR MASY")
        eb = tk.Frame(p.body, bg=COLORS["panel3"], highlightbackground=COLORS["border"], highlightthickness=1)
        eb.pack(fill="x", pady=(0, 6))
        el = Led(eb, size=26, bg=COLORS["panel3"])
        el.pack(pady=6)
        bs = tk.Frame(p.body, bg=COLORS["panel"])
        bs.pack(fill="x")
        ba = tk.Button(bs, text="DODAJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"))
        ba.pack(side="left", expand=1, fill="both", padx=(0, 4), pady=2)
        br = tk.Button(bs, text="UJMIJ\nMASY", bg=COLORS["button"], fg=COLORS["text"], relief="raised", font=("Segoe UI", 10, "bold"))
        br.pack(side="left", expand=1, fill="both", padx=(4, 0), pady=2)
        
        def sm(m):
            va = 1 if (m=="A" and not self.bus.get("par_mass_reg_limit_add")) else 0
            vr = 1 if (m=="R" and not self.bus.get("par_mass_reg_limit_remove")) else 0
            ve = 1 if (va or vr) else 0
            for s, v in [("par_mass_reg_limit_add", va), ("play_p13_mass_reg_limit_add", va),
                         ("par_mass_reg_limit_remove", vr), ("play_p23_mass_reg_limit_remove", vr),
                         ("par_mass_reg_enable", ve), ("play_p41_mass_reg_enable", ve), ("rec_p36_mass_reg_enable", ve)]:
                self._force_signal(s, v, source="PAR_MASS_EXCLUSIVE")
        
        ba.configure(command=lambda: sm("A"))
        br.configure(command=lambda: sm("R"))
        
        def pt(_v=None):
            en = self.bus.get("par_mass_reg_enable")
            eb.configure(bg="#143d16" if en else COLORS["panel3"])
            el.set(en)
            ba.configure(bg=COLORS["green"] if self.bus.get("par_mass_reg_limit_add") else COLORS["button"], fg="#061006" if self.bus.get("par_mass_reg_limit_add") else COLORS["text"])
            br.configure(bg=COLORS["blue"] if self.bus.get("par_mass_reg_limit_remove") else COLORS["button"], fg="#061006" if self.bus.get("par_mass_reg_limit_remove") else COLORS["text"])
            
        for s in ["par_mass_reg_enable", "play_p41_mass_reg_enable", "rec_p36_mass_reg_enable", "par_mass_reg_limit_add", "play_p13_mass_reg_limit_add", "par_mass_reg_limit_remove", "play_p23_mass_reg_limit_remove"]:
            self.rows[s] = _ParValueProxy(pt)
        pt(); return p

    def dron(self, p):
        pan = self.panel("dron", p, "DRON")
        r = tk.Frame(pan.body, bg=COLORS["panel"]); r.pack(fill="x", padx=6, pady=4)
        tk.Label(r, text="ZWOLNIENIE", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 13, "bold")).pack(side="left")
        led = Led(r, size=28, bg=COLORS["panel"]); led.pack(side="right"); led.set(self.bus.get("play_p14_drone_release"))
        tk.Button(
            pan.body,
            text="ZWOLNIJ DRONA",
            bg="#7a251f",
            fg="white",
            font=("Segoe UI", 14, "bold"),
            height=2,
            command=lambda: self.bus.toggle_input("play_p14_drone_release"),
        ).pack(fill="x", pady=5)
        self.rows["play_p14_drone_release"] = _ParValueProxy(led.set); return pan

    def bridge(self, p):
        pan = self.panel("bridge", p, "MOSTEK (BRIDGE)")
        b = self._scroll_body(pan)
        for n in [n for n in self.bus.names() if "bridge_" in n.lower()]: self._csv_signal_row(b, n, n.upper(), mode="gray")
        return pan

    def lamp_panel(self, p):
        pan = self.panel("lamp", p, "PRACA")
        canvas = tk.Canvas(pan.body, width=100, height=70, bg=COLORS["panel"], highlightthickness=0)
        canvas.pack(anchor="center", padx=6, pady=6)
        state = {"value": 1 if self.bus.get("par_lamp_auto_active") else 0}

        def draw(v=None):
            if v is not None:
                state["value"] = 1 if v else 0
            canvas.delete("all")
            color = COLORS["red"] if state["value"] else "#5b6268"
            glow = "#5a1613" if state["value"] else "#20282d"
            canvas.create_rectangle(5, 8, 95, 62, fill=glow, outline="")
            canvas.create_rectangle(13, 15, 87, 55, fill=color, outline="#111", width=2)
            canvas.create_rectangle(18, 19, 44, 28, fill="#ffffff", outline="", stipple="gray50")

        def toggle(_event=None):
            self.bus.toggle_input("par_lamp_auto_active", source="PAR_LAMP")

        canvas.bind("<Button-1>", toggle)
        pan.body.bind("<Button-1>", toggle)
        draw()
        self.rows["par_lamp_auto_active"] = _ParValueProxy(draw)
        return pan

    def poextbus_cnc(self, p):
        pan = self.panel("poextbus_cnc", p, "POEXTBUS CNC")
        b = self._scroll_body(pan)
        for n in [n for n in self.bus.names() if "poextbus" in n.lower()]: self._csv_signal_row(b, n, n.upper(), mode="violet")
        return pan
    def poextbus(self, p): return self.poextbus_cnc(p)
    def functions(self, p):
        pan = self.panel("functions", p, "FUNKCJE / REZERWY")
        b = self._scroll_body(pan)
        for n in [n for n in self.bus.names() if any(k in n.lower() for k in ("res", "free", "spare"))]:
            self._csv_signal_row(b, n, self._all_signals_label(n), mode="violet")
        return pan

    def lcd(self, parent):
        panel = self.panel("lcd", parent, "WYŚWIETLACZE LCD 1602")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="x")

        def lcd_box(title, sig1, sig2, default1, default2):
            box = tk.Frame(wrap, bg="#07110a", highlightbackground="#284130", highlightthickness=1)
            box.pack(fill="x", pady=4)
            tk.Label(
                box,
                text=title,
                bg="#07110a",
                fg=COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
                anchor="w",
            ).pack(fill="x", padx=7, pady=(4, 0))

            row = tk.Frame(box, bg="#07110a")
            row.pack(fill="x", padx=7, pady=(3, 6))

            display = tk.Frame(row, bg="#07110a")
            display.pack(side="left", fill="both", expand=True)

            line1 = tk.StringVar(value=str(self.bus.get(sig1, default1))[:16])
            line2 = tk.StringVar(value=str(self.bus.get(sig2, default2))[:16])

            e1 = tk.Entry(
                display,
                textvariable=line1,
                bg="#0b1c10",
                fg="#38ff6a",
                insertbackground="#38ff6a",
                font=("Consolas", 12, "bold"),
                relief="flat",
                width=16,
            )
            e2 = tk.Entry(
                display,
                textvariable=line2,
                bg="#0b1c10",
                fg="#38ff6a",
                insertbackground="#38ff6a",
                font=("Consolas", 12, "bold"),
                relief="flat",
                width=16,
            )
            e1.pack(fill="x", pady=(0, 2))
            e2.pack(fill="x")

            def send():
                l1 = line1.get()[:16].ljust(16)
                l2 = line2.get()[:16].ljust(16)
                line1.set(l1)
                line2.set(l2)

                raw_l1 = line1.get()
                raw_l2 = line2.get()
                self.bus.log("LCD1602", f"{title} SET TEXT='{raw_l1}|{raw_l2}'")
                self.bus.log("LCD1602", f"{title} SEND TEXT='{l1}|{l2}' -> {sig1}, {sig2}")

                self._set_signal(sig1, l1, "PAR_LCD")
                self._set_signal(sig2, l2, "PAR_LCD")

                if title.upper().startswith("PLAY"):
                    self.bus.log("LCD1602", f"{title} SEND MIRROR TEXT='{l1}|{l2}' -> par_lcd_line1, par_lcd_line2")
                    self._set_signal("par_lcd_line1", l1, "PAR_LCD")
                    self._set_signal("par_lcd_line2", l2, "PAR_LCD")

                self.update_log()

            tk.Button(
                row,
                text="SEND",
                bg=COLORS["green"],
                fg="#061006",
                activebackground="#43ff4e",
                relief="raised",
                font=("Segoe UI", 8, "bold"),
                width=5,
                command=send,
            ).pack(side="right", padx=(6, 0), fill="y")

        lcd_box("PLAY LCD 1602", "par_lcd_play_line1", "par_lcd_play_line2", "TARZAN PLAY", "READY")
        lcd_box("REC LCD 1602", "par_lcd_rec_line1", "par_lcd_rec_line2", "TARZAN REC", "READY")
        return panel

    def matrix(self, parent):
        panel = self.panel("matrix", parent, "MATRIX LED 8x8")
        holder = tk.Frame(panel.body, bg=COLORS["panel"])
        holder.pack(fill="both", expand=True)
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)

        center = tk.Frame(holder, bg=COLORS["panel"])
        center.grid(row=0, column=0, sticky="nsew")
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(0, weight=1)

        grid = tk.Frame(center, bg=COLORS["panel"])
        grid.grid(row=0, column=0, sticky="")
        cells = []
        state = [[0 for _ in range(8)] for _ in range(8)]

        def draw_cell(r, c):
            canvas = cells[r][c]
            canvas.delete("all")
            canvas.create_oval(2, 2, 12, 12, fill=COLORS["green"] if state[r][c] else "#123018", outline="")

        def toggle(r, c):
            state[r][c] = 0 if state[r][c] else 1
            draw_cell(r, c)

        for r in range(8):
            row = []
            for c in range(8):
                dot = tk.Canvas(grid, width=14, height=14, bg=COLORS["panel"], highlightthickness=0)
                dot.grid(row=r, column=c, padx=1, pady=1)
                dot.bind("<Button-1>", lambda _e, rr=r, cc=c: toggle(rr, cc))
                row.append(dot)
            cells.append(row)

        for r in range(8):
            for c in range(8):
                state[r][c] = 1 if (r in (1, 6) and 1 <= c <= 6) or (c in (1, 6) and 1 <= r <= 6) else 0
                draw_cell(r, c)

        def update():
            pattern = "/".join("".join("1" if state[r][c] else "0" for c in range(8)) for r in range(8))
            self.bus.log("MATRIX_LED", f"SET pattern={pattern}")
            self._set_signal("par_matrix_pattern", pattern, "PAR_MATRIX")
            self.bus.log("MATRIX_LED", f"SEND par_matrix_pattern={pattern}")
            self.update_log()

        tk.Button(holder, text="UPDATE MATRIX", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=update).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return panel

    def keyboard(self, parent):
        pan = self.panel("keyboard", parent, "KLAWIATURA")
        g = tk.Frame(pan.body, bg=COLORS["panel"])
        g.pack(anchor="center")
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, k in enumerate(keys):
            tk.Button(
                g,
                text=k,
                bg="#202b33",
                fg=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 12, "bold"),
                width=3,
                height=1,
                command=lambda val=k: (self.bus.log("KEYBOARD", f"KEY {val}"), self.update_log())
            ).grid(row=i // 3, column=i % 3, sticky="nsew", padx=3, pady=3)
        for i in range(3):
            g.grid_columnconfigure(i, weight=1)
        return pan

    def settings(self, p):
        pan = self.panel("settings", p, "USTAWIENIA PULPITU")
        b = tk.Frame(pan.body, bg=COLORS["panel"], padx=10, pady=10); b.pack(fill="x")
        
        # Statystyki sesji
        uptime = int(time.time() - getattr(self.app, 'start_time', time.time()))
        tk.Label(b, text=f"UPTIME: {uptime}s", bg=COLORS["panel"], fg=COLORS["green"]).pack(anchor="w")
        
        debug_var = tk.BooleanVar(value=getattr(self.bus, 'debug_override_outputs', False))
        def tg_db(): self.bus.debug_override_outputs = bool(debug_var.get()); self.bus.log("PAR", f"DEBUG override OUT = {self.bus.debug_override_outputs}")
        tk.Checkbutton(b, text="DEBUG override OUT", variable=debug_var, command=tg_db, bg=COLORS["panel"], fg=COLORS["text"], selectcolor="#101820").pack(anchor="w", pady=3)
        tk.Button(b, text="RESET SYGNAŁÓW", bg="#7a251f", fg="white", command=self.reset_signals).pack(fill="x", pady=5)
        tk.Button(b, text="SAVE LAYOUT", bg=COLORS["button"], fg="white", command=self.app.save_layout).pack(fill="x", pady=5)
        return pan

    def take(self, p):
        pan = self.panel("take", p, "TAKE — ODTWARZACZ PROTOKOŁU")

        # TARZAN_SNAJPER: Rejestracja widgetów TFD
        snajper = getattr(self.app, "tarzan_snajper", None)
        tk_adapter = snajper.adapters.get("par_tkinter") if snajper else None

        self.movie_title_label = tk.Label(pan.body, text="TYTUŁ: ---", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10))
        self.movie_title_label.pack(fill="x")
        if tk_adapter: tk_adapter.register_widget("take_panel", "movie_title_label", self.movie_title_label)

        self.director_label = tk.Label(pan.body, text="REŻYSER: ---", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10))
        self.director_label.pack(fill="x")
        if tk_adapter: tk_adapter.register_widget("take_panel", "director_label", self.director_label)

        # TAKE META INIT:
        # Widgety TITLE/DIRECTOR są już zarejestrowane w adapterze par_tkinter.
        # Teraz wymuszamy tylko ponowny strzał istniejącym Snajperem, bez lokalnych map
        # i bez ręcznego grzebania w cache pojedynczych targetów.
        try:
            if snajper is not None:
                if hasattr(snajper, "clear_scope"):
                    snajper.clear_scope("take_panel")

                title = getattr(tfd_state, "title", None) if tfd_state is not None else None
                director = getattr(tfd_state, "director", None) if tfd_state is not None else None

                if title is None:
                    title = self.bus.get("tfd_title", self.bus.get("par_tfd_title", ""))
                if director is None:
                    director = self.bus.get("tfd_director", self.bus.get("par_tfd_director", ""))

                snajper.fire_from_signal("tfd_title", "" if title is None else title)
                snajper.fire_from_signal("tfd_director", "" if director is None else director)
        except Exception:
            pass

        self.timecode_label = tk.Label(pan.body, text="00:00:00:0000", bg=COLORS["panel2"], fg=COLORS["green"], font=("Consolas", 18, "bold"))
        self.timecode_label.pack(fill="x", pady=5)
        if tk_adapter: tk_adapter.register_widget("take_panel", "timecode_label", self.timecode_label)

        top = tk.Frame(pan.body, bg=COLORS["panel"])
        top.pack(fill="x")

        center = tk.Frame(top, bg=COLORS["panel"])
        center.pack(anchor="center", pady=2)

        tk.Button(center, text="LOAD", bg="#d7dde2", fg="#101820", font=("Segoe UI", 11, "bold"), width=8,
                  height=1, command=self.app.load_take_dialog).pack(side="left", padx=5, pady=3)
        for txt, cmd, bg, fg in [
            ("PLAY", self.app.play_take, COLORS["green"], "#061006"),
            ("PAUSE", self.app.pause_take, "#bf8b18", "#ffffff"),
            ("STOP", self.app.stop_take, "#ae241d", "#ffffff"),
        ]:
            tk.Button(center, text=txt, bg=bg, fg=fg, font=("Segoe UI", 12, "bold"), width=8, height=1,
                      command=cmd).pack(side="left", padx=5, pady=3)

        self.app.take_label = tk.Label(
            pan.body,
            text="TAKE: brak",
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 14),
        )
        self.app.take_label.pack(fill="x", pady=8)
        if tk_adapter: tk_adapter.register_widget("take_panel", "take_label", self.app.take_label)

        return pan

    def camera(self, p):
        panel = self.panel("camera", p, "KAMERA I KHR")
        b = tk.Frame(panel.body, bg=COLORS["panel"], padx=10, pady=10)
        b.pack(fill="both", expand=True)

        # Sekcja kamery
        tk.Label(b, text="KAMERA OPERATORSKA:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
        f_cam = tk.Frame(b, bg=COLORS["panel"], pady=5)
        f_cam.pack(fill="x")
        tk.Button(f_cam, text="REC START/STOP", bg="#7a251f", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self._set_signal("par_camera_rec", 1)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Sekcja KHR
        tk.Label(b, text="KOREKTA KHR (AI/LEVEL/FACE):", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        
        # Tryb KHR
        f_mode = tk.Frame(b, bg=COLORS["panel"])
        f_mode.pack(fill="x")
        
        modes = ["OFF", "LEVEL", "FACE", "AI"]
        for m in modes:
            def set_m(val=m): self._set_signal("khr_active_mode", val)
            btn = tk.Button(f_mode, text=m, bg=COLORS["button"], font=("Segoe UI", 8), command=set_m)
            btn.pack(side="left", fill="x", expand=True, padx=1)
            # Podświetlenie aktywnego trybu
            def update_btn(v, b_ref=btn, m_ref=m):
                bg = COLORS["green"] if v == m_ref else COLORS["button"]
                fg = "black" if v == m_ref else COLORS["text"]
                b_ref.configure(bg=bg, fg=fg)
            self.rows[f"khr_mode_{m}"] = _ParValueProxy(lambda v, m=m, b=btn: update_btn(v, b, m))

        # Czułość KHR
        tk.Label(b, text="CZUŁOŚĆ KOREKTY:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(10, 0))
        f_sens = tk.Frame(b, bg=COLORS["panel"])
        f_sens.pack(fill="x")
        
        sens_val = tk.Label(f_sens, text="1.0", bg=COLORS["panel"], fg=COLORS["green"], width=4)
        sens_val.pack(side="right")
        
        sc = tk.Scale(f_sens, from_=0.1, to=5.0, resolution=0.1, orient="horizontal", bg=COLORS["panel"], 
                     troughcolor="#263741", highlightthickness=0, showvalue=False,
                     command=lambda v: self._set_signal("khr_sensitivity", float(v)))
        sc.set(1.0)
        sc.pack(side="left", fill="x", expand=True)
        
        def update_sens(v):
            try:
                val = float(v)
                sc.set(val)
                sens_val.configure(text=f"{val:.1f}")
            except: pass
        self.rows["khr_sensitivity"] = _ParValueProxy(update_sens)

        # Przyciski sterujące KHR
        f_ctrl = tk.Frame(b, bg=COLORS["panel"], pady=10)
        f_ctrl.pack(fill="x")
        tk.Button(f_ctrl, text="START KHR", bg=COLORS["green"], fg="black", font=("Segoe UI", 9, "bold"),
                  command=lambda: self._set_signal("cmd_khr_start", 1)).pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(f_ctrl, text="STOP KHR", bg=COLORS["red"], fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self._set_signal("cmd_khr_stop", 1)).pack(side="left", fill="x", expand=True, padx=(2, 0))

        return panel

    def autostatus(self, parent):
        panel = self.panel("autostatus", parent, "AUTO STATUS")
        wrap = tk.Frame(panel.body, bg=COLORS["panel"])
        wrap.pack(fill="both", expand=True)

        sig = "par_auto_mode"

        led = Led(wrap, size=62, bg=COLORS["panel"])
        led.pack(anchor="center", pady=10)
        led.set(self.bus.get(sig, 0))

        def click(_e=None):
            nv = 0 if self.bus.get(sig, 0) else 1
            self._force_signal(sig, nv, source="PAR_AUTO_WINDOW")
            led.set(nv)

        led.bind("<Button-1>", click)
        wrap.bind("<Button-1>", click)

        self.rows[sig] = _ParValueProxy(led.set)
        return panel

    def system(self, p):
        panel = self.panel("system", p, "SYSTEM")
        b = tk.Frame(panel.body, bg=COLORS["panel"], padx=10, pady=10); b.pack(fill="x")
        
        # TARZAN_SNAJPER: Rejestracja statusu systemowego
        snajper = getattr(self.app, "tarzan_snajper", None)
        tk_adapter = snajper.adapters.get("par_tkinter") if snajper else None

        tk.Label(b, text="TARZAN OS v2.4", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        self.status_label = tk.Label(b, text="STATUS: LIVE", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 11, "bold"))
        self.status_label.pack(anchor="w", pady=5)
        if tk_adapter: tk_adapter.register_widget("status_panel", "status_label", self.status_label)

        # CONTROL OWNER STATUS (ETAP 8)
        self.owner_label = tk.Label(b, text="OWNER: UNKNOWN", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 10, "bold"))
        self.owner_label.pack(anchor="w", pady=(0, 10))
        def update_owner(v):
            color = COLORS["green"] if v == "PAR_LIVE" else COLORS["muted"]
            if v == "EMERGENCY_STOP": color = COLORS["red"]
            self.owner_label.configure(text=f"CONTROL OWNER: {v}", fg=color)
        self.rows["control_owner"] = _ParValueProxy(update_owner)
        update_owner(self.bus.get("control_owner", "TSP_BOOT"))

        # LKS DIAGNOSTICS (ETAP 8)
        st_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        st_frame.pack(fill="x")
        
        tk.Label(st_frame, text="LKS HARDWARE STATUS (from miniPC):", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        signals = [
            ("linux_ok", "LINUX / SERVICE"),
            ("tsp_ok", "TSP SERVER"),
            ("signalbus_ok", "SIGNAL BUS"),
            ("pokeys_ok", "POKEYS (USB)"),
            ("i2c_bus_ok", "I2C BUS"),
            ("nextion5_ok", "NEXTION 5"),
            ("axis_inventory_ok", "AXIS INVENTORY"),
            ("tarzan_ready", "READY FOR PAR"),
        ]
        
        for i, (sig, label) in enumerate(signals):
            row = i + 1
            tk.Label(st_frame, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", padx=(5, 10))
            led = Led(st_frame, size=14)
            led.grid(row=row, column=1, sticky="w", pady=2)
            
            # Mapowanie stanów tekstowych na 0/1 dla LED
            def _set_led(v, led_ref=led):
                if isinstance(v, str):
                    state = 1 if v in ("CONNECTED", "READY", "ACTIVE", "BOOTING", "OK") else 0
                    led_ref.set(state)
                else:
                    led_ref.set(v)

            self.rows[sig] = _ParValueProxy(_set_led)
            _set_led(self.bus.get(sig, 0))

        # MODUŁY OPERATORSKIE STATUS (ETAP 8)
        mod_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        mod_frame.pack(fill="x")
        tk.Label(mod_frame, text="OPERATOR MODULES STATUS:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        modules = [
            ("par_state", "PAR CONSOLE"),
            ("par_write_denied_event", "WRITE DENIED"),
            ("rrp_state", "RRP REGULATOR"),
            ("sok_state", "SOK SENSOR"),
            ("nextion7_state", "NEXTION 7"),
        ]
        
        for i, (sig, label) in enumerate(modules):
            row = i + 1
            tk.Label(mod_frame, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", padx=(5, 10))
            
            # Specjalna dioda dla WRITE DENIED (Etap 8)
            l_color = COLORS["red"] if sig == "par_write_denied_event" else COLORS["green"]
            led = Led(mod_frame, size=14, color_on=l_color)
            led.grid(row=row, column=1, sticky="w", pady=2)
            
            def _set_mod_led(v, led_ref=led, s=sig):
                if s == "par_write_denied_event":
                    led_ref.set(int(v))
                else:
                    state = 1 if v in ("CONNECTED", "READY", "ACTIVE", "LIVE", 1) else 0
                    led_ref.set(state)

            self.rows[sig] = _ParValueProxy(_set_mod_led)
            _set_mod_led(self.bus.get(sig, 0))

        # LAST ERROR BAR (ETAP 8)
        err_frame = tk.Frame(b, bg="#100505", pady=5)
        err_frame.pack(fill="x", pady=5)
        tk.Label(err_frame, text="LAST ERROR:", bg="#100505", fg=COLORS["muted"], font=("Segoe UI", 8, "bold")).pack(side="left", padx=5)
        self.err_lbl = tk.Label(err_frame, text="NONE", bg="#100505", fg=COLORS["red"], font=("Consolas", 9))
        self.err_lbl.pack(side="left", fill="x", expand=True)
        self.rows["par_last_error"] = _ParValueProxy(lambda v: self.err_lbl.configure(text=str(v) if v else "NONE"))

        # RRP / SOK QUICK VIEW (ETAP 8)
        quick_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        quick_frame.pack(fill="x")
        tk.Label(quick_frame, text="RRP / SOK SELECTION (LIVE):", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        rrp_sels = [
            ("par_rrp_p1_selected_axis", "RRP P1 AXIS"),
            ("par_rrp_p2_selected_axis", "RRP P2 AXIS"),
        ]
        
        for i, (sig, label) in enumerate(rrp_sels):
            row = i + 1
            tk.Label(quick_frame, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", padx=(5, 10))
            v_lbl = tk.Label(quick_frame, text="NONE", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 8, "bold"))
            v_lbl.grid(row=row, column=1, sticky="w", pady=2)
            
            def _set_sel_lbl(v, lbl_ref=v_lbl):
                lbl_ref.configure(text=str(v).upper() if v else "NONE")

            self.rows[sig] = _ParValueProxy(_set_sel_lbl)
            _set_sel_lbl(self.bus.get(sig, ""))

        # ACTIONS PANEL (ETAP 8)
        act_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        act_frame.pack(fill="x")
        tk.Label(act_frame, text="ADMIN ACTIONS:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        btn_opts = {"bg": COLORS["header"], "fg": COLORS["green"], "font": ("Segoe UI", 8, "bold"), "relief": "flat", "padx": 10, "pady": 5, "cursor": "hand2"}
        
        def run_diag():
            if self.bus.mode != "LIVE":
                self.bus.log("PAR", "Diagnostics action only available in LIVE mode.")
                return
            self.app.bridge.call_action("run_diagnostics")
            self.bus.log("PAR", "Requested LKS Diagnostics on miniPC.")
            
        def take_control():
            if self.bus.mode != "LIVE":
                self.bus.log("PAR", "Take control only available in LIVE mode.")
                return
            self.app.bridge.call_action("set_owner", {"owner": "PAR_LIVE"})
            self.bus.log("PAR", "Requested PAR_LIVE control owner.")

        def reboot():
            if self.bus.mode != "LIVE": return
            self.app.bridge.call_action("reboot")
            self.bus.log("PAR", "Requested miniPC REBOOT.")

        def clear_errors():
            if self.bus.mode != "LIVE": return
            # Wysyłamy komendę do HardwareBridge na miniPC
            self.app.bridge.call_action("axis_status", {"cmd": "clear_alarms"})
            self.bus.log("PAR", "Requested AXIS ALARMS CLEAR.")

        tk.Button(act_frame, text="RUN DIAGNOSTICS", command=run_diag, **btn_opts).pack(side="left", padx=2)
        tk.Button(act_frame, text="TAKE CONTROL", command=take_control, **btn_opts).pack(side="left", padx=2)
        tk.Button(act_frame, text="CLEAR ERRORS", command=clear_errors, **btn_opts).pack(side="left", padx=2)
        tk.Button(act_frame, text="REBOOT miniPC", command=reboot, **btn_opts).pack(side="left", padx=2)

        # TRACE SIGNAL PANEL (ETAP 16)
        trace_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        trace_frame.pack(fill="x")
        tk.Label(trace_frame, text="TRACE SIGNAL (Live Monitor):", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        trace_inner = tk.Frame(trace_frame, bg="#050810", padx=5, pady=5)
        trace_inner.pack(fill="x")
        
        tk.Label(trace_inner, text="Signal Name:", bg="#050810", fg=COLORS["muted"]).pack(side="left")
        trace_ent = tk.Entry(trace_inner, bg="#101825", fg=COLORS["green"], insertbackground="white", borderwidth=0, width=25)
        trace_ent.pack(side="left", padx=5)
        
        def run_trace():
            name = trace_ent.get().strip()
            if not name or self.bus.mode != "LIVE": return
            self.app.bridge.tsp_client.trace_signal(name, seconds=30)
            self.bus.log("PAR", f"Started TRACE for signal: {name} (30s)")

        tk.Button(trace_inner, text="START TRACE", command=run_trace, bg=COLORS["green"], fg="black", font=("Segoe UI", 8, "bold"), relief="flat", padx=10).pack(side="left", padx=5)

        # HARDWARE SAFETY STATUS (ETAP 13)
        safe_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        safe_frame.pack(fill="x")
        
        tk.Label(safe_frame, text="HARDWARE SAFETY UNLOCK:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(side="left")
        
        safe_led = Led(safe_frame, size=18)
        safe_led.pack(side="left", padx=10)
        
        safe_lbl = tk.Label(safe_frame, text="LOCKED (Safety)", bg=COLORS["panel"], fg=COLORS["red"], font=("Segoe UI", 9, "bold"))
        safe_lbl.pack(side="left")
        
        def update_safe(v):
            v_bool = (int(v) == 1)
            safe_led.set(v_bool)
            if v_bool:
                safe_lbl.configure(text="UNLOCKED (Ready to move)", fg=COLORS["green"])
            else:
                safe_lbl.configure(text="LOCKED (Safety)", fg=COLORS["red"])
        
        def toggle_unlock():
            if self.bus.mode != "LIVE": return
            current = int(self.bus.get("safety_axis_unlock", 0))
            new_val = 1 if current == 0 else 0
            self.app.bridge.set_signal("cmd_unlock_axes", new_val)
            self.bus.log("PAR", f"Requesting physical axis {'UNLOCK' if new_val else 'LOCK'}.")

        tk.Button(safe_frame, text="TOGGLE UNLOCK", command=toggle_unlock, bg="#7a251f", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", padx=10).pack(side="right")
        
        self.rows["safety_axis_unlock"] = _ParValueProxy(update_safe)
        update_safe(self.bus.get("safety_axis_unlock", 0))

        # EHR / KHR REMOTE CONTROL (ETAP 8-9)
        ehr_khr_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        ehr_khr_frame.pack(fill="x")
        tk.Label(ehr_khr_frame, text="REMOTE BLOCKS (EHR/KHR):", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))

        def ehr_cmd(action):
            if self.bus.mode != "LIVE": return
            sig = f"cmd_ehr_{action}"
            self.app.bridge.write_output(sig, 1)
            self.bus.log("PAR", f"Sent EHR {action.upper()} command.")

        def khr_cmd(action):
            if self.bus.mode != "LIVE": return
            sig = f"cmd_khr_{action}"
            self.app.bridge.write_output(sig, 1)
            self.bus.log("PAR", f"Sent KHR {action.upper()} command.")

        row_ehr = tk.Frame(ehr_khr_frame, bg=COLORS["panel"])
        row_ehr.pack(fill="x", pady=2)
        tk.Label(row_ehr, text="EHR:", bg=COLORS["panel"], fg=COLORS["muted"], width=6, anchor="w").pack(side="left")
        
        ehr_led = Led(row_ehr, size=14)
        ehr_led.pack(side="left", padx=2)

        ehr_st_label = tk.Label(row_ehr, text="OFF", bg="#050810", fg=COLORS["muted"], font=("Consolas", 8, "bold"), width=10)
        ehr_st_label.pack(side="left", padx=5)
        
        def update_ehr_st(v):
            # Update Text
            color = COLORS["green"] if v in ("READY", "ACTIVE") else COLORS["muted"]
            if v == "ERROR": color = COLORS["red"]
            ehr_st_label.configure(text=str(v).upper(), fg=color)
            # Update LED
            state = 1 if v in ("CONNECTED", "READY", "ACTIVE") else 0
            ehr_led.set(state)

        self.rows["ehr_state"] = _ParValueProxy(update_ehr_st)
        update_ehr_st(self.bus.get("ehr_state", "OFF"))

        tk.Button(row_ehr, text="START", command=lambda: ehr_cmd("start"), **btn_opts).pack(side="left", padx=2)
        tk.Button(row_ehr, text="STOP", command=lambda: ehr_cmd("stop"), **btn_opts).pack(side="left", padx=2)

        row_khr = tk.Frame(ehr_khr_frame, bg=COLORS["panel"])
        row_khr.pack(fill="x", pady=2)
        tk.Label(row_khr, text="KHR:", bg=COLORS["panel"], fg=COLORS["muted"], width=6, anchor="w").pack(side="left")
        
        khr_led = Led(row_khr, size=14)
        khr_led.pack(side="left", padx=2)

        khr_st_label = tk.Label(row_khr, text="OFF", bg="#050810", fg=COLORS["muted"], font=("Consolas", 8, "bold"), width=10)
        khr_st_label.pack(side="left", padx=5)

        def update_khr_st(v):
            # Update Text
            color = COLORS["green"] if v in ("READY", "ACTIVE") else COLORS["muted"]
            if v == "ERROR": color = COLORS["red"]
            khr_st_label.configure(text=str(v).upper(), fg=color)
            # Update LED
            state = 1 if v in ("CONNECTED", "READY", "ACTIVE") else 0
            khr_led.set(state)

        self.rows["khr_state"] = _ParValueProxy(update_khr_st)
        update_khr_st(self.bus.get("khr_state", "OFF"))

        tk.Button(row_khr, text="START", command=lambda: khr_cmd("start"), **btn_opts).pack(side="left", padx=2)
        tk.Button(row_khr, text="STOP", command=lambda: khr_cmd("stop"), **btn_opts).pack(side="left", padx=2)

        tk.Label(b, text="CPU: 12%", bg=COLORS["panel"], fg=COLORS["green"]).pack(anchor="w", pady=(10, 0))
        tk.Label(b, text="IP: 192.168.1.10", bg=COLORS["panel"], fg=COLORS["muted"]).pack(anchor="w")

        # TSP FAST STATS (ETAP 16)
        tsp_frame = tk.Frame(b, bg=COLORS["panel"], pady=10)
        tsp_frame.pack(fill="x")
        tk.Label(tsp_frame, text="TSP NETWORK STATS:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.tsp_stats_label = tk.Label(tsp_frame, text="RX: 0 | TX: 0 | ERR: 0 | DROP: 0", bg="#050810", fg=COLORS["green"], font=("Consolas", 9), padx=5, pady=5)
        self.tsp_stats_label.pack(fill="x")
        
        def update_tsp_stats(v):
            try:
                import json
                stats = json.loads(v)
                txt = f"RX: {stats.get('packets_rx', 0)} | TX: {stats.get('packets_tx', 0)} | ERR: {stats.get('errors', 0)} | DROP: {stats.get('dropped', 0)}"
                self.tsp_stats_label.configure(text=txt)
            except Exception: pass
            
        self.rows["tsp_fast_stats"] = _ParValueProxy(update_tsp_stats)

        return panel

    def update_log(self):
        """
        Istniejący target LOGI.
        Odświeża tylko self.log_text i tylko wtedy, gdy kolejka logów realnie się zmieniła.
        Bez limitu ilości wpisów.
        """
        if not hasattr(self, "log_text"):
            return
        try:
            lines = None
            for attr in ("log_lines", "logs", "log_queue", "events"):
                if hasattr(self.bus, attr):
                    candidate = getattr(self.bus, attr)
                    if candidate is not None:
                        lines = list(candidate)
                        break

            if lines is None:
                return

            snapshot = tuple(str(line) for line in lines)
            if snapshot == getattr(self, "_last_log_snapshot", ()):
                return
            self._last_log_snapshot = snapshot

            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", "\n".join(snapshot))
            if snapshot:
                self.log_text.insert("end", "\n")
            self.log_text.see("end")
        except Exception:
            return

    def log_panel(self, p):
        panel = self.panel("log", p, "LOGI")
        self.log_text = tk.Text(panel.body, height=8, bg="#070b0e", fg=COLORS["green"], font=("Consolas", 8)); self.log_text.pack(fill="both", expand=True)
        self.register_log_snajper_widget(self.log_text)
        # TARZAN_SNAJPER_LOGI_INITIAL_QUEUE: pokaż kolejkę, która powstała przed renderem panelu.
        self.update_log()
        return panel

    def diagnostics(self, p):
        panel = self.panel("diagnostics", p, "DIAGNOSTYKA I TRACE")
        b = tk.Frame(panel.body, bg=COLORS["panel"], padx=10, pady=10)
        b.pack(fill="both", expand=True)
        
        # TRACE CONTROL
        tk.Label(b, text="TRACE SIGNAL (Real-time from MiniPC):", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
        
        f_trace = tk.Frame(b, bg=COLORS["panel"], pady=5)
        f_trace.pack(fill="x")
        
        sig_var = tk.StringVar(value="axis_arm_h_pos")
        tk.Entry(f_trace, textvariable=sig_var, bg="#050810", fg=COLORS["green"], font=("Consolas", 10)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        txt_box = tk.Text(b, height=8, bg="#050810", fg=COLORS["green"], font=("Consolas", 8), borderwidth=0)

        def run_trace():
            if self.bus.mode != "LIVE":
                self.bus.log("PAR", "Trace requires LIVE mode.")
                return
            sig = sig_var.get().strip()
            if not sig: return
            if hasattr(self.app, "bridge"):
                self.app.bridge.call_action("trace_signal", {"name": sig, "seconds": 30})
                self.bus.log("PAR", f"Started trace for: {sig}")
                # Rejestrujemy proxy dla wyników trace
                trace_key = f"trace_{sig}"
                self.rows[trace_key] = _ParValueProxy(lambda v: [txt_box.insert("1.0", f"{v}\n"), txt_box.delete("50.0", "end")])

        def stop_trace():
            if self.bus.mode != "LIVE": return
            sig = sig_var.get().strip()
            if not sig: return
            if hasattr(self.app, "bridge"):
                self.app.bridge.call_action("trace_signal", {"name": sig, "seconds": 0})
                self.bus.log("PAR", f"Stopped trace for: {sig}")

        tk.Button(f_trace, text="START", command=run_trace, bg=COLORS["button"], font=("Segoe UI", 9, "bold")).pack(side="right", padx=(5, 0))
        tk.Button(f_trace, text="STOP", command=stop_trace, bg="#7a251f", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=2)

        # SAFETY & LIMITS
        tk.Label(b, text="SAFETY & LIMITS:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        
        f_safety = tk.Frame(b, bg=COLORS["panel"])
        f_safety.pack(fill="x")
        
        safety_var = tk.BooleanVar(value=False)
        def toggle_safety():
            val = 1 if safety_var.get() else 0
            self._set_signal("cmd_unlock_axes", val)
            self.bus.log("PAR", f"Safety axis unlock command: {val}")

        cb = tk.Checkbutton(f_safety, text="UNLOCK PHYSICAL AXIS (DANGEROUS)", variable=safety_var, command=toggle_safety,
                          bg=COLORS["panel"], fg=COLORS["orange"], activebackground=COLORS["panel"],
                          selectcolor="#050810", font=("Segoe UI", 9, "bold"))
        cb.pack(side="left")
        self.rows["safety_axis_unlock"] = _ParValueProxy(lambda v: safety_var.set(bool(v)))

        tk.Label(b, text="SYSTEM STATUS & METRICS:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        
        metrics = [
            ("tsp_fast_stats", "Network"),
            ("system_state", "System"),
            ("control_owner", "Owner"),
            ("runtime_state", "Runtime")
        ]
        
        for sig, lbl in metrics:
            row = tk.Frame(b, bg=COLORS["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{lbl}:", bg=COLORS["panel"], fg=COLORS["muted"], width=10, anchor="w").pack(side="left")
            val_lbl = tk.Label(row, text="---", bg="#050810", fg=COLORS["green"], font=("Consolas", 9), anchor="w")
            val_lbl.pack(side="left", fill="x", expand=True)
            
            def update_val(v, l=val_lbl, s=sig):
                l.configure(text=str(v))
            
            self.rows[sig] = _ParValueProxy(update_val)

        tk.Label(b, text="TRACE LOG:", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(10, 0))
        txt_box.pack(fill="both", expand=True, pady=5)
        
        return panel

    def cnc_signals_panel(self, p):
        panel = self.panel("cnc", p, "CNC")
        b = self._scroll_body(panel)
        for n in [n for n in self.bus.names() if n.startswith("cnc_")]:
            self._csv_signal_row(b, n, str(n).upper(), mode="gray", clickable=False)
        return panel

    def functions_panel(self, p): return self.functions(p)
    def take_control(self, p): return self.take(p)
    def dron_panel(self, p): return self.dron(p)


    def nextion_7_preview(self, parent):
        panel = self.panel("nextion_7_preview", parent, "NEXTION 7")
        bridge = self.app.bridge.nextion if hasattr(self.app.bridge, "nextion") and self.app.bridge.nextion is not None else self.app.bridge
        widget = TarzanNextionPreviewPanel(panel.body, bridge, "nextion_7", "NEXTION 7 — PODGLĄD")
        widget.pack(fill="both", expand=True)
        self.nextion_preview_widgets["nextion_7"] = widget
        return panel

    def nextion_refresh_previews(self):
        """
        Model cyklicznego odświeżania podglądu został usunięty.
        Zastąpiono przez TARZAN_SNAJPER.fire_from_signal(...) w on_state_change.
        Ta metoda może być wywołana tylko raz przy wejściu na stronę dla pełnego renderu struktury.
        """
        pass

    # -------------------------------------------------------------------------
    # TARZAN_SNAJPER — aktualizacje sekcyjne PAR
    # -------------------------------------------------------------------------

    def _snajper_update_section_generic(self, section: str, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets(section, signal_name, value)

    def _snajper_touch_known_widgets(self, section: str, signal_name: str, value) -> None:
        """
        Celowana aktualizacja znanych widgetów sekcji.
        Działa bez refresh_all i bez przebudowy całego PAR.
        """
        candidates = [
            signal_name,
            signal_name.replace("sensor_", ""),
            signal_name.replace("par_", ""),
            signal_name.replace("_c", ""),
            signal_name.replace("_lux", ""),
        ]
        for name in candidates:
            for suffix in ("_label", "_value_label", "_value", "_text", "_var"):
                widget = getattr(self, f"{name}{suffix}", None)
                if widget is not None:
                    self._snajper_set_widget_value(widget, value)

    def _snajper_set_widget_value(self, widget, value) -> None:
        try:
            # Rejestracja widgetu w Snajperze przy pierwszym użyciu, jeśli jeszcze nie jest zarejestrowany
            app = getattr(self, "app", None)
            snajper = getattr(app, "tarzan_snajper", None)
            if snajper:
                # Próbujemy znaleźć nazwę widgetu dla rejestracji w Snajperze
                for attr_name in dir(self):
                    if getattr(self, attr_name) is widget:
                        snajper.register_widget("par_tkinter", attr_name, widget)
                        break

            if hasattr(widget, "set"):
                widget.set(value)
                return
            if hasattr(widget, "configure"):
                try:
                    keys = widget.keys() if hasattr(widget, "keys") else ()
                    if "text" in keys:
                        widget.configure(text=str(value))
                except Exception:
                    pass
                return
            if hasattr(widget, "itemconfigure"):
                return
        except Exception:
            return

    def _snajper_update_section_rrp(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("rrp", signal_name, value)

    def _snajper_update_section_temperature(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("temperature", signal_name, value)
        for name in ("temperature_panel", "temp_panel", "temperature_widget", "temp_widget"):
            widget = getattr(self, name, None)
            if hasattr(widget, "set_value"):
                widget.set_value(value)

    def _snajper_update_section_light(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("light", signal_name, value)
        for name in ("light_panel", "bh1750_panel", "light_widget"):
            widget = getattr(self, name, None)
            if hasattr(widget, "set_value"):
                widget.set_value(value)

    def _snajper_update_section_xyz(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("xyz", signal_name, value)
        for name in ("xyz_panel", "level_panel", "level_xyz_panel", "level_widget"):
            widget = getattr(self, name, None)
            if hasattr(widget, "set_value"):
                widget.set_value(signal_name, value)
            elif hasattr(widget, "update_xyz"):
                widget.update_xyz(signal_name, value)

    def _snajper_update_section_motor_cards(self, signal_name: str, value) -> None:
        cards = getattr(self, "axis_cards", None) or getattr(self, "_axis_cards", None)
        if isinstance(cards, dict):
            for key, card in cards.items():
                if str(key) in signal_name or f"axis_{key}" in signal_name:
                    try:
                        if hasattr(card, "set_value"):
                            card.set_value(signal_name, value)
                        elif hasattr(card, "update_value"):
                            card.update_value(signal_name, value)
                        # Nie ustawiamy configure(text=...) na kartach osi,
                        # bo część z nich to Frame/Canvas i Tkinter zwraca unknown option "-text".
                    except Exception:
                        pass

    def _snajper_update_section_step_dir_preview(self, signal_name: str, value) -> None:
        """
        Live podgląd sygnałów STEP/DIR.

        To nie jest refresh_all.
        To jest odświeżenie tylko sekcji "PODGLĄD SYGNAŁÓW — STEP / DIR".
        Sekcja może wykonać swój lokalny repaint/rysowanie, bo to jej obszar działania.
        """

        # 1. Preferowany model: istniejący widget/panel ma własną metodę live-update.
        for name in (
            "step_dir_preview",
            "signals_preview",
            "protocol_preview",
            "step_preview_panel",
            "step_dir_panel",
            "signals_step_dir_panel",
        ):
            widget = getattr(self, name, None)
            if widget is None:
                continue
            for method_name in (
                "update_signal",
                "update_live_signal",
                "set_signal_value",
                "set_value",
                "snajper_update",
            ):
                method = getattr(widget, method_name, None)
                if method is not None:
                    try:
                        method(signal_name, value)
                        return
                    except TypeError:
                        try:
                            method(value)
                            return
                        except Exception:
                            pass
                    except Exception:
                        pass

        # 2. Drugi model: panel jest budowany jako Canvas/Frame i ma metodę rysowania sekcji.
        # To jest lokalny repaint sekcji STEP/DIR, dozwolony w Snajperze sekcyjnym.
        for method_name in (
            "_draw_step_dir_preview",
            "_draw_signals_preview",
            "_draw_protocol_preview",
            "_render_step_dir_preview",
            "_refresh_step_dir_preview_section",
            "_refresh_protocol_preview_section",
            "_update_step_dir_preview",
        ):
            method = getattr(self, method_name, None)
            if method is not None:
                try:
                    method()
                    return
                except TypeError:
                    try:
                        method(signal_name, value)
                        return
                    except Exception:
                        pass
                except Exception:
                    pass

        # 3. Trzeci model: jeśli istnieje canvas tej sekcji, poruszamy markerem czasu
        # albo dopisujemy minimalną informację tekstową, bez ruszania całego PAR.
        canvas = None
        for name in (
            "step_dir_canvas",
            "signals_preview_canvas",
            "protocol_preview_canvas",
            "step_preview_canvas",
        ):
            candidate = getattr(self, name, None)
            if candidate is not None:
                canvas = candidate
                break

        if canvas is not None:
            try:
                marker = getattr(self, "_snajper_step_dir_marker", None)
                width = max(1, int(canvas.winfo_width()))
                x = (hash(str(signal_name)) % width)
                if marker is None:
                    self._snajper_step_dir_marker = canvas.create_line(x, 0, x, max(1, canvas.winfo_height()), fill="red")
                else:
                    canvas.coords(marker, x, 0, x, max(1, canvas.winfo_height()))
                return
            except Exception:
                pass

        # 4. Ostatecznie aktualizujemy rows/log — bez pełnego refreshu.
        self._snajper_touch_known_widgets("step_dir_preview", signal_name, value)


    def _snajper_update_section_limits(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("limits", signal_name, value)

    def _snajper_update_section_shock_laser(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("shock_laser", signal_name, value)

    def _snajper_update_section_sok(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("sok", signal_name, value)

    def _snajper_update_section_cnc(self, signal_name: str, value) -> None:
        self._snajper_touch_known_widgets("cnc", signal_name, value)

    def _snajper_update_section_logs(self, signal_name: str, value) -> None:
        if hasattr(self, "log"):
            try:
                self.log(f"{signal_name}: {value}")
            except Exception:
                pass

