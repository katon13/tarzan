from __future__ import annotations

"""
TARZAN_SNAJPER — pełny katalog celów z aktualnego repo.

Ten plik jest dokumentacyjno-wykonawczym rdzeniem celowanych aktualizacji.
Nie zmienia żadnego istniejącego modułu sam z siebie.

Zasada:
    STRUKTURA -> pełny render tylko przy zmianie struktury
    WARTOŚĆ / POZYCJA / STATUS -> TarzanSnajper.fire_from_signal(...) albo fire(...)

Źródło prawdy:
    SignalBus

TarzanSnajper NIE jest:
    - nowym SignalBus
    - pętlą odświeżania
    - systemem skanowania
    - refresh_all

TarzanSnajper JEST:
    - mapą sygnał -> logiczny cel
    - mapą logiczny cel -> konkretne odbiorniki
    - last_value cache
    - wywołaniem adapterów tylko dla zmienionych celów
"""


# =============================================================================
# TARZAN_SNAJPER_ORGANIZATION_NOTE
# =============================================================================
# Ten plik został uporządkowany bez usuwania sygnałów i celów.
# Podział:
#   01-10: strategiczne grupy projektowe
#   11: pełny katalog komponentów HMI Nextion
#   12: pełny katalog Tkinter z automatycznego skanu
#   13: pełny katalog Canvas z automatycznego skanu
#   99: inne zachowane pozycje
#
# Zasada:
#   wszystko zostaje w pliku, ale jest rozdzielone na warstwę strategiczną
#   i katalogi techniczne. Dzięki temu Snajper może trzymać cały model,
#   a jednocześnie mapa jest czytelna.
# =============================================================================

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Protocol, Tuple


# =============================================================================
# PEŁNE SŁOWNIKI KONTRAKTU — UZUPEŁNIONE Z REPO
# =============================================================================

TARZAN_SNAJPER_ADAPTERS: Tuple[str, ...] = ('physical_nextion', 'canvas_preview', 'par_tkinter', 'ehr_canvas', 'ehr_tkinter', 'sandbox_canvas', 'sandbox_tkinter', 'timeline_canvas', 'layout_canvas', 'khr_canvas', 'khr_tkinter', 'tfd_adapter', 'take_adapter', 'log_adapter', 'signal_row')

TARZAN_SNAJPER_PROPS: Tuple[str, ...] = ('coords', 'en', 'pic', 'state', 'text', 'tim', 'txt', 'val', 'value', 'visible')

TARZAN_SNAJPER_SCOPE_GROUPS: Tuple[str, ...] = (
    "rrp_main",
    "take_main",
    "settings_main",
    "level_xyz",
    "page1",
    "boot",
    "sensors_main",
    "face_rec",
    "keybdA",
    "par_rrp",
    "par_timeline",
    "par_layout",
    "axis_panel",
    "sensors_panel",
    "take_panel",
    "status_panel",
    "nextion_panel",
    "ehr_main",
    "ehr_protocol",
    "ehr_axis_info",
    "ehr_take_slots",
    "sandbox",
    "khr",
    "khr_input",
    "khr_output",
)


@dataclass(frozen=True)
class TarzanSnajperTarget:
    """
    Pojedynczy cel Snajpera.

    adapter:
        Pełna lista adapterów w tym katalogu:
        - physical_nextion
        - canvas_preview
        - par_tkinter
        - ehr_canvas
        - ehr_tkinter
        - sandbox_canvas
        - sandbox_tkinter
        - timeline_canvas
        - layout_canvas
        - khr_canvas
        - khr_tkinter
        - tfd_adapter
        - take_adapter
        - log_adapter
        - signal_row

    scope:
        Obszar/ekran/panel. Scope może być stroną Nextiona, panelem PAR,
        ekranem EHR, timeline, sandboxem albo zakresem wygenerowanym z pliku.
        Najważniejsze scope:
        - rrp_main
        - take_main
        - settings_main
        - level_xyz
        - par_rrp
        - par_timeline
        - par_layout
        - ehr_main
        - ehr_protocol
        - ehr_axis_info
        - ehr_take_slots
        - sandbox
        - khr_input
        - khr_output

    target:
        Konkretny komponent, tag, item Canvas albo nazwa widgetu.
        Przykłady:
        - t_p1_val
        - t_p2_val
        - b_p1_dir
        - t_axis0
        - va0
        - p1_value_label
        - axis_3_curve
        - cursor
        - selected_cell

    prop:
        Pełna lista wspieranych właściwości w katalogu:
        - coords
        - en
        - pic
        - state
        - text
        - tim
        - txt
        - val
        - value
        - visible
    """
    adapter: str
    scope: str
    target: str
    prop: str


class TarzanSnajperAdapter(Protocol):
    def update_target(self, target: TarzanSnajperTarget, value: Any) -> None:
        ...


class TarzanSnajper:
    def __init__(self) -> None:
        self.signal_map: Dict[str, str] = {}
        self.targets: Dict[str, List[TarzanSnajperTarget]] = {}
        self.adapters: Dict[str, TarzanSnajperAdapter] = {}
        self.last_values: Dict[str, str] = {}
        self.enabled: bool = True

    def register_adapter(self, name: str, adapter: TarzanSnajperAdapter) -> None:
        self.adapters[name] = adapter

    def unregister_adapter(self, name: str) -> None:
        self.adapters.pop(name, None)

    def register_signal(self, raw_signal: str, logical_signal: str) -> None:
        self.signal_map[raw_signal] = logical_signal

    def register_signals(self, mapping: Dict[str, str]) -> None:
        self.signal_map.update(mapping)

    def register_target(self, logical_signal: str, target: TarzanSnajperTarget) -> None:
        self.targets.setdefault(logical_signal, []).append(target)

    def register_targets(self, mapping: Dict[str, Iterable[TarzanSnajperTarget]]) -> None:
        for logical_signal, targets in mapping.items():
            self.targets.setdefault(logical_signal, []).extend(list(targets))

    def clear_all(self) -> None:
        self.last_values.clear()

    def clear_scope(self, scope: str) -> None:
        prefix = f".{scope}."
        self.last_values = {
            key: value
            for key, value in self.last_values.items()
            if prefix not in key
        }

    def clear_adapter(self, adapter_name: str) -> None:
        prefix = f"{adapter_name}."
        self.last_values = {
            key: value
            for key, value in self.last_values.items()
            if not key.startswith(prefix)
        }

    def fire_from_signal(self, raw_signal: str, value: Any) -> None:
        if not self.enabled:
            return
        logical_signal = self.signal_map.get(raw_signal)
        if not logical_signal:
            return
        self.fire(logical_signal, value)

    def fire(self, logical_signal: str, value: Any) -> None:
        if not self.enabled:
            return
        normalized = self.normalize_value(value)
        for target in self.targets.get(logical_signal, []):
            cache_key = self._cache_key(target)
            if self.last_values.get(cache_key) == normalized:
                continue
            self.last_values[cache_key] = normalized
            adapter = self.adapters.get(target.adapter)
            if adapter is None:
                continue
            adapter.update_target(target, value)

    @staticmethod
    def normalize_value(value: Any) -> str:
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    @staticmethod
    def _cache_key(target: TarzanSnajperTarget) -> str:
        return f"{target.adapter}.{target.scope}.{target.target}.{target.prop}"


# =============================================================================
# ADAPTERY
# =============================================================================

class TkWidgetSnajperAdapter:
    def __init__(self) -> None:
        self.widgets: Dict[str, Any] = {}

    def register_widget(self, scope: str, target: str, widget: Any) -> None:
        self.widgets[f"{scope}.{target}"] = widget

    def unregister_widget(self, scope: str, target: str) -> None:
        self.widgets.pop(f"{scope}.{target}", None)

    def update_target(self, target: TarzanSnajperTarget, value: Any) -> None:
        widget = self.widgets.get(f"{target.scope}.{target.target}")
        if widget is None:
            return
        if target.prop in {"text", "txt"}:
            widget.configure(text=str(value))
            return
        if target.prop == "state":
            widget.configure(state=str(value))
            return
        if target.prop == "value":
            if hasattr(widget, "set"):
                widget.set(value)
            else:
                widget.configure(value=value)
            return
        if target.prop == "visible":
            widget.configure(text=str(value))
            return


class TkCanvasSnajperAdapter:
    def __init__(self) -> None:
        self.items: Dict[str, Tuple[Any, int]] = {}

    def register_item(self, scope: str, target: str, prop: str, canvas: Any, item_id: int) -> None:
        self.items[f"{scope}.{target}.{prop}"] = (canvas, item_id)

    def unregister_item(self, scope: str, target: str, prop: str) -> None:
        self.items.pop(f"{scope}.{target}.{prop}", None)

    def clear_scope(self, scope: str) -> None:
        prefix = f"{scope}."
        self.items = {
            key: value
            for key, value in self.items.items()
            if not key.startswith(prefix)
        }

    def update_target(self, target: TarzanSnajperTarget, value: Any) -> None:
        item = self.items.get(f"{target.scope}.{target.target}.{target.prop}")
        if item is None:
            return
        canvas, item_id = item
        if target.prop in {"text", "txt", "val", "state", "en", "tim", "pic"}:
            canvas.itemconfigure(item_id, text=str(value))
            return
        if target.prop == "coords":
            if isinstance(value, (list, tuple)):
                canvas.coords(item_id, *value)
            return
        if target.prop == "visible":
            canvas.itemconfigure(item_id, state="normal" if bool(value) else "hidden")
            return


class NextionPhysicalSnajperAdapter:
    def __init__(self, bridge: Any) -> None:
        self.bridge = bridge

    def update_target(self, target: TarzanSnajperTarget, value: Any) -> None:
        if not hasattr(self.bridge, "queue_snajper_command"):
            return
        self.bridge.queue_snajper_command(
            scope=target.scope,
            component=target.target,
            prop=target.prop,
            value=value,
        )


def T(adapter: str, scope: str, target: str, prop: str) -> TarzanSnajperTarget:
    return TarzanSnajperTarget(adapter=adapter, scope=scope, target=target, prop=prop)


# =============================================================================
# PEŁNA MAPA SYGNAŁÓW Z REPO / HMI / UI
# =============================================================================

# =============================================================================
# PEŁNA MAPA SYGNAŁÓW Z REPO / HMI / UI — UPORZĄDKOWANA, BEZ USUWANIA
# =============================================================================

# UWAGA:
# - ta mapa nadal zawiera pełny katalog: strategiczne sygnały + skan techniczny
# - create_default_tarzan_snajper() ładuje całość tak jak wcześniej
# - porządek poniżej jest dokumentacyjny i ułatwia późniejsze rozdzielenie

DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP: Dict[str, str] = {

    # -------------------------------------------------------------------------
    # 01_RRP_PAR_NEXTION: RRP / PAR / Nextion — strategiczne sterowanie ręczne
    # -------------------------------------------------------------------------
    'nextion_rrp_main_b_home_pic': 'nextion_rrp_main_b_home_pic',
    'rrp_main.b_home.pic': 'nextion_rrp_main_b_home_pic',
    'nextion_rrp_main_b_home_val': 'nextion_rrp_main_b_home_val',
    'rrp_main.b_home.val': 'nextion_rrp_main_b_home_val',
    'nextion_rrp_main_b_p1_arm_h_val': 'nextion_rrp_main_b_p1_arm_h_val',
    'rrp_main.b_p1_arm_h.val': 'nextion_rrp_main_b_p1_arm_h_val',
    'nextion_rrp_main_b_p1_arm_v_val': 'nextion_rrp_main_b_p1_arm_v_val',
    'rrp_main.b_p1_arm_v.val': 'nextion_rrp_main_b_p1_arm_v_val',
    'nextion_rrp_main_b_p1_cam_f_val': 'nextion_rrp_main_b_p1_cam_f_val',
    'rrp_main.b_p1_cam_f.val': 'nextion_rrp_main_b_p1_cam_f_val',
    'nextion_rrp_main_b_p1_cam_h_val': 'nextion_rrp_main_b_p1_cam_h_val',
    'rrp_main.b_p1_cam_h.val': 'nextion_rrp_main_b_p1_cam_h_val',
    'nextion_rrp_main_b_p1_cam_t_val': 'nextion_rrp_main_b_p1_cam_t_val',
    'rrp_main.b_p1_cam_t.val': 'nextion_rrp_main_b_p1_cam_t_val',
    'nextion_rrp_main_b_p1_cam_v_val': 'nextion_rrp_main_b_p1_cam_v_val',
    'rrp_main.b_p1_cam_v.val': 'nextion_rrp_main_b_p1_cam_v_val',
    'nextion_rrp_main_b_p1_dir_val': 'nextion_rrp_main_b_p1_dir_val',
    'rrp_main.b_p1_dir.val': 'nextion_rrp_main_b_p1_dir_val',
    'nextion_rrp_main_b_p2_arm_h_val': 'nextion_rrp_main_b_p2_arm_h_val',
    'rrp_main.b_p2_arm_h.val': 'nextion_rrp_main_b_p2_arm_h_val',
    'nextion_rrp_main_b_p2_arm_v_val': 'nextion_rrp_main_b_p2_arm_v_val',
    'rrp_main.b_p2_arm_v.val': 'nextion_rrp_main_b_p2_arm_v_val',
    'nextion_rrp_main_b_p2_cam_f_val': 'nextion_rrp_main_b_p2_cam_f_val',
    'rrp_main.b_p2_cam_f.val': 'nextion_rrp_main_b_p2_cam_f_val',
    'nextion_rrp_main_b_p2_cam_h_val': 'nextion_rrp_main_b_p2_cam_h_val',
    'rrp_main.b_p2_cam_h.val': 'nextion_rrp_main_b_p2_cam_h_val',
    'nextion_rrp_main_b_p2_cam_t_val': 'nextion_rrp_main_b_p2_cam_t_val',
    'rrp_main.b_p2_cam_t.val': 'nextion_rrp_main_b_p2_cam_t_val',
    'nextion_rrp_main_b_p2_cam_v_val': 'nextion_rrp_main_b_p2_cam_v_val',
    'rrp_main.b_p2_cam_v.val': 'nextion_rrp_main_b_p2_cam_v_val',
    'nextion_rrp_main_b_p2_dir_val': 'nextion_rrp_main_b_p2_dir_val',
    'rrp_main.b_p2_dir.val': 'nextion_rrp_main_b_p2_dir_val',
    'nextion_rrp_main_b_stop_pic': 'nextion_rrp_main_b_stop_pic',
    'rrp_main.b_stop.pic': 'nextion_rrp_main_b_stop_pic',
    'nextion_rrp_main_b_stop_val': 'nextion_rrp_main_b_stop_val',
    'rrp_main.b_stop.val': 'nextion_rrp_main_b_stop_val',
    'nextion_rrp_main_h_p1_sens_val': 'nextion_rrp_main_h_p1_sens_val',
    'rrp_main.h_p1_sens.val': 'nextion_rrp_main_h_p1_sens_val',
    'nextion_rrp_main_h_p2_sens_val': 'nextion_rrp_main_h_p2_sens_val',
    'rrp_main.h_p2_sens.val': 'nextion_rrp_main_h_p2_sens_val',
    'nextion_rrp_main_t_buf_p1_txt': 'nextion_rrp_main_t_buf_p1_txt',
    'rrp_main.t_buf_p1.txt': 'nextion_rrp_main_t_buf_p1_txt',
    'nextion_rrp_main_t_buf_p2_txt': 'nextion_rrp_main_t_buf_p2_txt',
    'rrp_main.t_buf_p2.txt': 'nextion_rrp_main_t_buf_p2_txt',
    'nextion_rrp_main_t_p1_val_txt': 'nextion_rrp_main_t_p1_val_txt',
    'rrp_main.t_p1_val.txt': 'nextion_rrp_main_t_p1_val_txt',
    'nextion_rrp_main_t_p2_val_txt': 'nextion_rrp_main_t_p2_val_txt',
    'rrp_main.t_p2_val.txt': 'nextion_rrp_main_t_p2_val_txt',
    'nextion_rrp_main_va_p1_axis_val': 'nextion_rrp_main_va_p1_axis_val',
    'rrp_main.va_p1_axis.val': 'nextion_rrp_main_va_p1_axis_val',
    'nextion_rrp_main_va_p1_dir_val': 'nextion_rrp_main_va_p1_dir_val',
    'rrp_main.va_p1_dir.val': 'nextion_rrp_main_va_p1_dir_val',
    'nextion_rrp_main_va_p1_val_val': 'nextion_rrp_main_va_p1_val_val',
    'rrp_main.va_p1_val.val': 'nextion_rrp_main_va_p1_val_val',
    'nextion_rrp_main_va_p2_axis_val': 'nextion_rrp_main_va_p2_axis_val',
    'rrp_main.va_p2_axis.val': 'nextion_rrp_main_va_p2_axis_val',
    'nextion_rrp_main_va_p2_dir_val': 'nextion_rrp_main_va_p2_dir_val',
    'rrp_main.va_p2_dir.val': 'nextion_rrp_main_va_p2_dir_val',
    'nextion_rrp_main_va_p2_val_val': 'nextion_rrp_main_va_p2_val_val',
    'rrp_main.va_p2_val.val': 'nextion_rrp_main_va_p2_val_val',
    'nextion_rrp_main_va_tmp_val': 'nextion_rrp_main_va_tmp_val',
    'rrp_main.va_tmp.val': 'nextion_rrp_main_va_tmp_val',
    'par_rrp_p1_dir': 'rrp_p1_dir',
    'par_rrp_p1_sens': 'rrp_p1_sens',
    'par_rrp_p1_val': 'rrp_p1_value',
    'par_rrp_p2_dir': 'rrp_p2_dir',
    'par_rrp_p2_sens': 'rrp_p2_sens',
    'par_rrp_p2_val': 'rrp_p2_value',

    # -------------------------------------------------------------------------
    # 02_TAKE_TFD: TAKE / TFD — timecode, clap, status ujęcia
    # -------------------------------------------------------------------------
    'nextion_take_main_b_clap_pic': 'nextion_take_main_b_clap_pic',
    'take_main.b_clap.pic': 'nextion_take_main_b_clap_pic',
    'nextion_take_main_b_clap_val': 'nextion_take_main_b_clap_val',
    'take_main.b_clap.val': 'nextion_take_main_b_clap_val',
    'nextion_take_main_b_home_pic': 'nextion_take_main_b_home_pic',
    'take_main.b_home.pic': 'nextion_take_main_b_home_pic',
    'nextion_take_main_b_home_val': 'nextion_take_main_b_home_val',
    'take_main.b_home.val': 'nextion_take_main_b_home_val',
    'nextion_take_main_p_axis0_pic': 'nextion_take_main_p_axis0_pic',
    'take_main.p_axis0.pic': 'nextion_take_main_p_axis0_pic',
    'nextion_take_main_p_axis1_pic': 'nextion_take_main_p_axis1_pic',
    'take_main.p_axis1.pic': 'nextion_take_main_p_axis1_pic',
    'nextion_take_main_p_axis2_pic': 'nextion_take_main_p_axis2_pic',
    'take_main.p_axis2.pic': 'nextion_take_main_p_axis2_pic',
    'nextion_take_main_p_axis3_pic': 'nextion_take_main_p_axis3_pic',
    'take_main.p_axis3.pic': 'nextion_take_main_p_axis3_pic',
    'nextion_take_main_p_axis4_pic': 'nextion_take_main_p_axis4_pic',
    'take_main.p_axis4.pic': 'nextion_take_main_p_axis4_pic',
    'nextion_take_main_p_axis5_pic': 'nextion_take_main_p_axis5_pic',
    'take_main.p_axis5.pic': 'nextion_take_main_p_axis5_pic',
    'nextion_take_main_p_laser_pic': 'nextion_take_main_p_laser_pic',
    'take_main.p_laser.pic': 'nextion_take_main_p_laser_pic',
    'nextion_take_main_p_light_pic': 'nextion_take_main_p_light_pic',
    'take_main.p_light.pic': 'nextion_take_main_p_light_pic',
    'nextion_take_main_p_limits_pic': 'nextion_take_main_p_limits_pic',
    'take_main.p_limits.pic': 'nextion_take_main_p_limits_pic',
    'nextion_take_main_p_shock_pic': 'nextion_take_main_p_shock_pic',
    'take_main.p_shock.pic': 'nextion_take_main_p_shock_pic',
    'nextion_take_main_p_temp_pic': 'nextion_take_main_p_temp_pic',
    'take_main.p_temp.pic': 'nextion_take_main_p_temp_pic',
    'nextion_take_main_p_xyz_pic': 'nextion_take_main_p_xyz_pic',
    'take_main.p_xyz.pic': 'nextion_take_main_p_xyz_pic',
    'nextion_take_main_t0_txt': 'nextion_take_main_t0_txt',
    'take_main.t0.txt': 'nextion_take_main_t0_txt',
    'nextion_take_main_t1_txt': 'nextion_take_main_t1_txt',
    'take_main.t1.txt': 'nextion_take_main_t1_txt',
    'nextion_take_main_t2_txt': 'nextion_take_main_t2_txt',
    'take_main.t2.txt': 'nextion_take_main_t2_txt',
    'nextion_take_main_t_axis0_txt': 'nextion_take_main_t_axis0_txt',
    'take_main.t_axis0.txt': 'nextion_take_main_t_axis0_txt',
    'nextion_take_main_t_axis1_txt': 'nextion_take_main_t_axis1_txt',
    'take_main.t_axis1.txt': 'nextion_take_main_t_axis1_txt',
    'nextion_take_main_t_axis2_txt': 'nextion_take_main_t_axis2_txt',
    'take_main.t_axis2.txt': 'nextion_take_main_t_axis2_txt',
    'nextion_take_main_t_axis3_txt': 'nextion_take_main_t_axis3_txt',
    'take_main.t_axis3.txt': 'nextion_take_main_t_axis3_txt',
    'nextion_take_main_t_axis4_txt': 'nextion_take_main_t_axis4_txt',
    'take_main.t_axis4.txt': 'nextion_take_main_t_axis4_txt',
    'nextion_take_main_t_axis5_txt': 'nextion_take_main_t_axis5_txt',
    'take_main.t_axis5.txt': 'nextion_take_main_t_axis5_txt',
    'nextion_take_main_t_clap_txt': 'nextion_take_main_t_clap_txt',
    'take_main.t_clap.txt': 'nextion_take_main_t_clap_txt',
    'nextion_take_main_t_laser_txt': 'nextion_take_main_t_laser_txt',
    'take_main.t_laser.txt': 'nextion_take_main_t_laser_txt',
    'nextion_take_main_t_light_txt': 'nextion_take_main_t_light_txt',
    'take_main.t_light.txt': 'nextion_take_main_t_light_txt',
    'nextion_take_main_t_limits_txt': 'nextion_take_main_t_limits_txt',
    'take_main.t_limits.txt': 'nextion_take_main_t_limits_txt',
    'nextion_take_main_t_shock_txt': 'nextion_take_main_t_shock_txt',
    'take_main.t_shock.txt': 'nextion_take_main_t_shock_txt',
    'nextion_take_main_t_status_txt': 'nextion_take_main_t_status_txt',
    'take_main.t_status.txt': 'nextion_take_main_t_status_txt',
    'nextion_take_main_t_take_txt': 'nextion_take_main_t_take_txt',
    'take_main.t_take.txt': 'nextion_take_main_t_take_txt',
    'nextion_take_main_t_temp_txt': 'nextion_take_main_t_temp_txt',
    'take_main.t_temp.txt': 'nextion_take_main_t_temp_txt',
    'nextion_take_main_t_xyz_txt': 'nextion_take_main_t_xyz_txt',
    'take_main.t_xyz.txt': 'nextion_take_main_t_xyz_txt',
    'take_timecode': 'take_timecode',

    # -------------------------------------------------------------------------
    # 03_OSIE: Osie — wartości i liczniki osi
    # -------------------------------------------------------------------------
    'axis_0_value': 'axis_0_value',
    'axis_1_value': 'axis_1_value',
    'axis_2_value': 'axis_2_value',
    'axis_3_value': 'axis_3_value',
    'axis_4_value': 'axis_4_value',
    'axis_5_value': 'axis_5_value',

    # -------------------------------------------------------------------------
    # 04_SENSORY_STATUS: Sensory / statusy / poziomica
    # -------------------------------------------------------------------------
    'sensor_level_x': 'level_x',
    'sensor_level_y': 'level_y',

    # -------------------------------------------------------------------------
    # 05_NEXTION_SETTINGS_UI_CUT: Nextion settings / UI CUT
    # -------------------------------------------------------------------------
    'nextion_settings_main_b_home_pic': 'nextion_settings_main_b_home_pic',
    'settings_main.b_home.pic': 'nextion_settings_main_b_home_pic',
    'nextion_settings_main_b_home_val': 'nextion_settings_main_b_home_val',
    'settings_main.b_home.val': 'nextion_settings_main_b_home_val',
    'nextion_settings_main_b_save_meta_pic': 'nextion_settings_main_b_save_meta_pic',
    'settings_main.b_save_meta.pic': 'nextion_settings_main_b_save_meta_pic',
    'nextion_settings_main_b_save_meta_val': 'nextion_settings_main_b_save_meta_val',
    'settings_main.b_save_meta.val': 'nextion_settings_main_b_save_meta_val',
    'nextion_settings_main_t_director_txt': 'nextion_settings_main_t_director_txt',
    'settings_main.t_director.txt': 'nextion_settings_main_t_director_txt',
    'nextion_settings_main_t_save_status_txt': 'nextion_settings_main_t_save_status_txt',
    'settings_main.t_save_status.txt': 'nextion_settings_main_t_save_status_txt',
    'nextion_settings_main_t_title_txt': 'nextion_settings_main_t_title_txt',
    'settings_main.t_title.txt': 'nextion_settings_main_t_title_txt',
    'nextion_ui_cut': 'nextion_ui_cut',

    # -------------------------------------------------------------------------
    # 06_EHR: EHR — krzywe, STEP preview, metryki, TAKE slots
    # -------------------------------------------------------------------------
    'ehr_axis_0_curve': 'ehr_axis_0_curve',
    'ehr_axis_0_metrics': 'ehr_axis_0_metrics',
    'ehr_axis_0_step_preview': 'ehr_axis_0_step_preview',
    'ehr_axis_1_curve': 'ehr_axis_1_curve',
    'ehr_axis_1_metrics': 'ehr_axis_1_metrics',
    'ehr_axis_1_step_preview': 'ehr_axis_1_step_preview',
    'ehr_axis_2_curve': 'ehr_axis_2_curve',
    'ehr_axis_2_metrics': 'ehr_axis_2_metrics',
    'ehr_axis_2_step_preview': 'ehr_axis_2_step_preview',
    'ehr_axis_3_curve': 'ehr_axis_3_curve',
    'ehr_axis_3_metrics': 'ehr_axis_3_metrics',
    'ehr_axis_3_step_preview': 'ehr_axis_3_step_preview',
    'ehr_axis_4_curve': 'ehr_axis_4_curve',
    'ehr_axis_4_metrics': 'ehr_axis_4_metrics',
    'ehr_axis_4_step_preview': 'ehr_axis_4_step_preview',
    'ehr_axis_5_curve': 'ehr_axis_5_curve',
    'ehr_axis_5_metrics': 'ehr_axis_5_metrics',
    'ehr_axis_5_step_preview': 'ehr_axis_5_step_preview',
    'ehr_take_slot_0_status': 'ehr_take_slot_0_status',
    'ehr_take_slot_1_status': 'ehr_take_slot_1_status',
    'ehr_take_slot_2_status': 'ehr_take_slot_2_status',
    'ehr_take_slot_3_status': 'ehr_take_slot_3_status',
    'ehr_take_slot_4_status': 'ehr_take_slot_4_status',
    'ehr_take_slot_5_status': 'ehr_take_slot_5_status',
    'ehr_take_slot_6_status': 'ehr_take_slot_6_status',
    'ehr_take_slot_7_status': 'ehr_take_slot_7_status',

    # -------------------------------------------------------------------------
    # 07_SANDBOX: Sandbox osi
    # -------------------------------------------------------------------------
    'sandbox_curve': 'sandbox_curve',
    'sandbox_metrics': 'sandbox_metrics',
    'sandbox_step_preview': 'sandbox_step_preview',

    # -------------------------------------------------------------------------
    # 08_TIMELINE: Timeline — cursor i markery
    # -------------------------------------------------------------------------
    'timeline_clap_marker': 'timeline_clap_marker',
    'timeline_cursor': 'timeline_cursor',
    'timeline_take_marker': 'timeline_take_marker',

    # -------------------------------------------------------------------------
    # 09_LAYOUT_DESIGNER: Layout designer
    # -------------------------------------------------------------------------
    'layout_panel_status': 'layout_panel_status',
    'layout_selected_cell': 'layout_selected_cell',
    'layout_zone_label': 'layout_zone_label',

    # -------------------------------------------------------------------------
    # 10_KHR: KHR — markery i status
    # -------------------------------------------------------------------------
    'khr_input_marker': 'khr_input_marker',
    'khr_output_marker': 'khr_output_marker',
    'khr_status': 'khr_status',

    # -------------------------------------------------------------------------
    # 11_NEXTION_HMI_KOMPONENTY: Pełny katalog komponentów HMI Nextion
    # -------------------------------------------------------------------------
    'boot.Event.en': 'nextion_boot_event_en',
    'nextion_boot_event_en': 'nextion_boot_event_en',
    'boot.Event.tim': 'nextion_boot_event_tim',
    'nextion_boot_event_tim': 'nextion_boot_event_tim',
    'boot.p0.pic': 'nextion_boot_p0_pic',
    'nextion_boot_p0_pic': 'nextion_boot_p0_pic',
    'boot.tm0.en': 'nextion_boot_tm0_en',
    'nextion_boot_tm0_en': 'nextion_boot_tm0_en',
    'boot.tm0.tim': 'nextion_boot_tm0_tim',
    'nextion_boot_tm0_tim': 'nextion_boot_tm0_tim',
    'boot.va0.val': 'nextion_boot_va0_val',
    'nextion_boot_va0_val': 'nextion_boot_va0_val',
    'face_rec.b_home.pic': 'nextion_face_rec_b_home_pic',
    'nextion_face_rec_b_home_pic': 'nextion_face_rec_b_home_pic',
    'face_rec.b_home.val': 'nextion_face_rec_b_home_val',
    'nextion_face_rec_b_home_val': 'nextion_face_rec_b_home_val',
    'face_rec.t0.txt': 'nextion_face_rec_t0_txt',
    'nextion_face_rec_t0_txt': 'nextion_face_rec_t0_txt',
    'keybdA.b0.pic': 'nextion_keybda_b0_pic',
    'nextion_keybda_b0_pic': 'nextion_keybda_b0_pic',
    'keybdA.b0.val': 'nextion_keybda_b0_val',
    'nextion_keybda_b0_val': 'nextion_keybda_b0_val',
    'keybdA.b1.pic': 'nextion_keybda_b1_pic',
    'nextion_keybda_b1_pic': 'nextion_keybda_b1_pic',
    'keybdA.b1.val': 'nextion_keybda_b1_val',
    'nextion_keybda_b1_val': 'nextion_keybda_b1_val',
    'keybdA.b200.pic': 'nextion_keybda_b200_pic',
    'nextion_keybda_b200_pic': 'nextion_keybda_b200_pic',
    'keybdA.b200.val': 'nextion_keybda_b200_val',
    'nextion_keybda_b200_val': 'nextion_keybda_b200_val',
    'keybdA.b201.pic': 'nextion_keybda_b201_pic',
    'nextion_keybda_b201_pic': 'nextion_keybda_b201_pic',
    'keybdA.b201.val': 'nextion_keybda_b201_val',
    'nextion_keybda_b201_val': 'nextion_keybda_b201_val',
    'keybdA.b20.pic': 'nextion_keybda_b20_pic',
    'nextion_keybda_b20_pic': 'nextion_keybda_b20_pic',
    'keybdA.b20.val': 'nextion_keybda_b20_val',
    'nextion_keybda_b20_val': 'nextion_keybda_b20_val',
    'keybdA.b210.pic': 'nextion_keybda_b210_pic',
    'nextion_keybda_b210_pic': 'nextion_keybda_b210_pic',
    'keybdA.b210.val': 'nextion_keybda_b210_val',
    'nextion_keybda_b210_val': 'nextion_keybda_b210_val',
    'keybdA.b21.pic': 'nextion_keybda_b21_pic',
    'nextion_keybda_b21_pic': 'nextion_keybda_b21_pic',
    'keybdA.b21.val': 'nextion_keybda_b21_val',
    'nextion_keybda_b21_val': 'nextion_keybda_b21_val',
    'keybdA.b220.pic': 'nextion_keybda_b220_pic',
    'nextion_keybda_b220_pic': 'nextion_keybda_b220_pic',
    'keybdA.b220.val': 'nextion_keybda_b220_val',
    'nextion_keybda_b220_val': 'nextion_keybda_b220_val',
    'keybdA.b22.pic': 'nextion_keybda_b22_pic',
    'nextion_keybda_b22_pic': 'nextion_keybda_b22_pic',
    'keybdA.b22.val': 'nextion_keybda_b22_val',
    'nextion_keybda_b22_val': 'nextion_keybda_b22_val',
    'keybdA.b230.pic': 'nextion_keybda_b230_pic',
    'nextion_keybda_b230_pic': 'nextion_keybda_b230_pic',
    'keybdA.b230.val': 'nextion_keybda_b230_val',
    'nextion_keybda_b230_val': 'nextion_keybda_b230_val',
    'keybdA.b231.pic': 'nextion_keybda_b231_pic',
    'nextion_keybda_b231_pic': 'nextion_keybda_b231_pic',
    'keybdA.b231.val': 'nextion_keybda_b231_val',
    'nextion_keybda_b231_val': 'nextion_keybda_b231_val',
    'keybdA.b232.pic': 'nextion_keybda_b232_pic',
    'nextion_keybda_b232_pic': 'nextion_keybda_b232_pic',
    'keybdA.b232.val': 'nextion_keybda_b232_val',
    'nextion_keybda_b232_val': 'nextion_keybda_b232_val',
    'keybdA.b23.pic': 'nextion_keybda_b23_pic',
    'nextion_keybda_b23_pic': 'nextion_keybda_b23_pic',
    'keybdA.b23.val': 'nextion_keybda_b23_val',
    'nextion_keybda_b23_val': 'nextion_keybda_b23_val',
    'keybdA.b240.pic': 'nextion_keybda_b240_pic',
    'nextion_keybda_b240_pic': 'nextion_keybda_b240_pic',
    'keybdA.b240.val': 'nextion_keybda_b240_val',
    'nextion_keybda_b240_val': 'nextion_keybda_b240_val',
    'keybdA.b241.pic': 'nextion_keybda_b241_pic',
    'nextion_keybda_b241_pic': 'nextion_keybda_b241_pic',
    'keybdA.b241.val': 'nextion_keybda_b241_val',
    'nextion_keybda_b241_val': 'nextion_keybda_b241_val',
    'keybdA.b242.pic': 'nextion_keybda_b242_pic',
    'nextion_keybda_b242_pic': 'nextion_keybda_b242_pic',
    'keybdA.b242.val': 'nextion_keybda_b242_val',
    'nextion_keybda_b242_val': 'nextion_keybda_b242_val',
    'keybdA.b243.pic': 'nextion_keybda_b243_pic',
    'nextion_keybda_b243_pic': 'nextion_keybda_b243_pic',
    'keybdA.b243.val': 'nextion_keybda_b243_val',
    'nextion_keybda_b243_val': 'nextion_keybda_b243_val',
    'keybdA.b244.pic': 'nextion_keybda_b244_pic',
    'nextion_keybda_b244_pic': 'nextion_keybda_b244_pic',
    'keybdA.b244.val': 'nextion_keybda_b244_val',
    'nextion_keybda_b244_val': 'nextion_keybda_b244_val',
    'keybdA.b249.pic': 'nextion_keybda_b249_pic',
    'nextion_keybda_b249_pic': 'nextion_keybda_b249_pic',
    'keybdA.b249.val': 'nextion_keybda_b249_val',
    'nextion_keybda_b249_val': 'nextion_keybda_b249_val',
    'keybdA.b24.pic': 'nextion_keybda_b24_pic',
    'nextion_keybda_b24_pic': 'nextion_keybda_b24_pic',
    'keybdA.b24.val': 'nextion_keybda_b24_val',
    'nextion_keybda_b24_val': 'nextion_keybda_b24_val',
    'keybdA.b251.pic': 'nextion_keybda_b251_pic',
    'nextion_keybda_b251_pic': 'nextion_keybda_b251_pic',
    'keybdA.b251.val': 'nextion_keybda_b251_val',
    'nextion_keybda_b251_val': 'nextion_keybda_b251_val',
    'keybdA.b25.pic': 'nextion_keybda_b25_pic',
    'nextion_keybda_b25_pic': 'nextion_keybda_b25_pic',
    'keybdA.b25.val': 'nextion_keybda_b25_val',
    'nextion_keybda_b25_val': 'nextion_keybda_b25_val',
    'keybdA.b26.pic': 'nextion_keybda_b26_pic',
    'nextion_keybda_b26_pic': 'nextion_keybda_b26_pic',
    'keybdA.b26.val': 'nextion_keybda_b26_val',
    'nextion_keybda_b26_val': 'nextion_keybda_b26_val',
    'keybdA.b27.pic': 'nextion_keybda_b27_pic',
    'nextion_keybda_b27_pic': 'nextion_keybda_b27_pic',
    'keybdA.b27.val': 'nextion_keybda_b27_val',
    'nextion_keybda_b27_val': 'nextion_keybda_b27_val',
    'keybdA.b28.pic': 'nextion_keybda_b28_pic',
    'nextion_keybda_b28_pic': 'nextion_keybda_b28_pic',
    'keybdA.b28.val': 'nextion_keybda_b28_val',
    'nextion_keybda_b28_val': 'nextion_keybda_b28_val',
    'keybdA.b2.pic': 'nextion_keybda_b2_pic',
    'nextion_keybda_b2_pic': 'nextion_keybda_b2_pic',
    'keybdA.b2.val': 'nextion_keybda_b2_val',
    'nextion_keybda_b2_val': 'nextion_keybda_b2_val',
    'keybdA.b3.pic': 'nextion_keybda_b3_pic',
    'nextion_keybda_b3_pic': 'nextion_keybda_b3_pic',
    'keybdA.b3.val': 'nextion_keybda_b3_val',
    'nextion_keybda_b3_val': 'nextion_keybda_b3_val',
    'keybdA.b40.pic': 'nextion_keybda_b40_pic',
    'nextion_keybda_b40_pic': 'nextion_keybda_b40_pic',
    'keybdA.b40.val': 'nextion_keybda_b40_val',
    'nextion_keybda_b40_val': 'nextion_keybda_b40_val',
    'keybdA.b41.pic': 'nextion_keybda_b41_pic',
    'nextion_keybda_b41_pic': 'nextion_keybda_b41_pic',
    'keybdA.b41.val': 'nextion_keybda_b41_val',
    'nextion_keybda_b41_val': 'nextion_keybda_b41_val',
    'keybdA.b42.pic': 'nextion_keybda_b42_pic',
    'nextion_keybda_b42_pic': 'nextion_keybda_b42_pic',
    'keybdA.b42.val': 'nextion_keybda_b42_val',
    'nextion_keybda_b42_val': 'nextion_keybda_b42_val',
    'keybdA.b43.pic': 'nextion_keybda_b43_pic',
    'nextion_keybda_b43_pic': 'nextion_keybda_b43_pic',
    'keybdA.b43.val': 'nextion_keybda_b43_val',
    'nextion_keybda_b43_val': 'nextion_keybda_b43_val',
    'keybdA.b44.pic': 'nextion_keybda_b44_pic',
    'nextion_keybda_b44_pic': 'nextion_keybda_b44_pic',
    'keybdA.b44.val': 'nextion_keybda_b44_val',
    'nextion_keybda_b44_val': 'nextion_keybda_b44_val',
    'keybdA.b45.pic': 'nextion_keybda_b45_pic',
    'nextion_keybda_b45_pic': 'nextion_keybda_b45_pic',
    'keybdA.b45.val': 'nextion_keybda_b45_val',
    'nextion_keybda_b45_val': 'nextion_keybda_b45_val',
    'keybdA.b46.pic': 'nextion_keybda_b46_pic',
    'nextion_keybda_b46_pic': 'nextion_keybda_b46_pic',
    'keybdA.b46.val': 'nextion_keybda_b46_val',
    'nextion_keybda_b46_val': 'nextion_keybda_b46_val',
    'keybdA.b4.pic': 'nextion_keybda_b4_pic',
    'nextion_keybda_b4_pic': 'nextion_keybda_b4_pic',
    'keybdA.b4.val': 'nextion_keybda_b4_val',
    'nextion_keybda_b4_val': 'nextion_keybda_b4_val',
    'keybdA.b5.pic': 'nextion_keybda_b5_pic',
    'nextion_keybda_b5_pic': 'nextion_keybda_b5_pic',
    'keybdA.b5.val': 'nextion_keybda_b5_val',
    'nextion_keybda_b5_val': 'nextion_keybda_b5_val',
    'keybdA.b6.pic': 'nextion_keybda_b6_pic',
    'nextion_keybda_b6_pic': 'nextion_keybda_b6_pic',
    'keybdA.b6.val': 'nextion_keybda_b6_val',
    'nextion_keybda_b6_val': 'nextion_keybda_b6_val',
    'keybdA.b7.pic': 'nextion_keybda_b7_pic',
    'nextion_keybda_b7_pic': 'nextion_keybda_b7_pic',
    'keybdA.b7.val': 'nextion_keybda_b7_val',
    'nextion_keybda_b7_val': 'nextion_keybda_b7_val',
    'keybdA.b8.pic': 'nextion_keybda_b8_pic',
    'nextion_keybda_b8_pic': 'nextion_keybda_b8_pic',
    'keybdA.b8.val': 'nextion_keybda_b8_val',
    'nextion_keybda_b8_val': 'nextion_keybda_b8_val',
    'keybdA.b9.pic': 'nextion_keybda_b9_pic',
    'nextion_keybda_b9_pic': 'nextion_keybda_b9_pic',
    'keybdA.b9.val': 'nextion_keybda_b9_val',
    'nextion_keybda_b9_val': 'nextion_keybda_b9_val',
    'keybdA.Event.en': 'nextion_keybda_event_en',
    'nextion_keybda_event_en': 'nextion_keybda_event_en',
    'keybdA.Event.tim': 'nextion_keybda_event_tim',
    'nextion_keybda_event_tim': 'nextion_keybda_event_tim',
    'keybdA.input.txt': 'nextion_keybda_input_txt',
    'nextion_keybda_input_txt': 'nextion_keybda_input_txt',
    'keybdA.inputlenth.val': 'nextion_keybda_inputlenth_val',
    'nextion_keybda_inputlenth_val': 'nextion_keybda_inputlenth_val',
    'keybdA.loadcmpid.val': 'nextion_keybda_loadcmpid_val',
    'nextion_keybda_loadcmpid_val': 'nextion_keybda_loadcmpid_val',
    'keybdA.loadpageid.val': 'nextion_keybda_loadpageid_val',
    'nextion_keybda_loadpageid_val': 'nextion_keybda_loadpageid_val',
    'keybdA.refshow.state': 'nextion_keybda_refshow_state',
    'nextion_keybda_refshow_state': 'nextion_keybda_refshow_state',
    'keybdA.show.txt': 'nextion_keybda_show_txt',
    'nextion_keybda_show_txt': 'nextion_keybda_show_txt',
    'keybdA.temp2.val': 'nextion_keybda_temp2_val',
    'nextion_keybda_temp2_val': 'nextion_keybda_temp2_val',
    'keybdA.temp.val': 'nextion_keybda_temp_val',
    'nextion_keybda_temp_val': 'nextion_keybda_temp_val',
    'keybdA.tempstr.txt': 'nextion_keybda_tempstr_txt',
    'nextion_keybda_tempstr_txt': 'nextion_keybda_tempstr_txt',
    'keybdA.tm0.en': 'nextion_keybda_tm0_en',
    'nextion_keybda_tm0_en': 'nextion_keybda_tm0_en',
    'keybdA.tm0.tim': 'nextion_keybda_tm0_tim',
    'nextion_keybda_tm0_tim': 'nextion_keybda_tm0_tim',
    'level_xyz.b_home.pic': 'nextion_level_xyz_b_home_pic',
    'nextion_level_xyz_b_home_pic': 'nextion_level_xyz_b_home_pic',
    'level_xyz.b_home.val': 'nextion_level_xyz_b_home_val',
    'nextion_level_xyz_b_home_val': 'nextion_level_xyz_b_home_val',
    'level_xyz.Event.en': 'nextion_level_xyz_event_en',
    'nextion_level_xyz_event_en': 'nextion_level_xyz_event_en',
    'level_xyz.Event.tim': 'nextion_level_xyz_event_tim',
    'nextion_level_xyz_event_tim': 'nextion_level_xyz_event_tim',
    'level_xyz.p0.pic': 'nextion_level_xyz_p0_pic',
    'nextion_level_xyz_p0_pic': 'nextion_level_xyz_p0_pic',
    'level_xyz.tm0.en': 'nextion_level_xyz_tm0_en',
    'nextion_level_xyz_tm0_en': 'nextion_level_xyz_tm0_en',
    'level_xyz.tm0.tim': 'nextion_level_xyz_tm0_tim',
    'nextion_level_xyz_tm0_tim': 'nextion_level_xyz_tm0_tim',
    'level_xyz.va0.val': 'nextion_level_xyz_va0_val',
    'nextion_level_xyz_va0_val': 'nextion_level_xyz_va0_val',
    'level_xyz.va1.val': 'nextion_level_xyz_va1_val',
    'nextion_level_xyz_va1_val': 'nextion_level_xyz_va1_val',
    'level_xyz.va2.val': 'nextion_level_xyz_va2_val',
    'nextion_level_xyz_va2_val': 'nextion_level_xyz_va2_val',
    'level_xyz.va3.val': 'nextion_level_xyz_va3_val',
    'nextion_level_xyz_va3_val': 'nextion_level_xyz_va3_val',
    'nextion_page1_b_face_pic': 'nextion_page1_b_face_pic',
    'page1.b_face.pic': 'nextion_page1_b_face_pic',
    'nextion_page1_b_face_val': 'nextion_page1_b_face_val',
    'page1.b_face.val': 'nextion_page1_b_face_val',
    'nextion_page1_b_level_pic': 'nextion_page1_b_level_pic',
    'page1.b_level.pic': 'nextion_page1_b_level_pic',
    'nextion_page1_b_level_val': 'nextion_page1_b_level_val',
    'page1.b_level.val': 'nextion_page1_b_level_val',
    'nextion_page1_b_rrp_pic': 'nextion_page1_b_rrp_pic',
    'page1.b_rrp.pic': 'nextion_page1_b_rrp_pic',
    'nextion_page1_b_rrp_val': 'nextion_page1_b_rrp_val',
    'page1.b_rrp.val': 'nextion_page1_b_rrp_val',
    'nextion_page1_b_sensors_pic': 'nextion_page1_b_sensors_pic',
    'page1.b_sensors.pic': 'nextion_page1_b_sensors_pic',
    'nextion_page1_b_sensors_val': 'nextion_page1_b_sensors_val',
    'page1.b_sensors.val': 'nextion_page1_b_sensors_val',
    'nextion_page1_b_settings_pic': 'nextion_page1_b_settings_pic',
    'page1.b_settings.pic': 'nextion_page1_b_settings_pic',
    'nextion_page1_b_settings_val': 'nextion_page1_b_settings_val',
    'page1.b_settings.val': 'nextion_page1_b_settings_val',
    'nextion_page1_b_take_pic': 'nextion_page1_b_take_pic',
    'page1.b_take.pic': 'nextion_page1_b_take_pic',
    'nextion_page1_b_take_val': 'nextion_page1_b_take_val',
    'page1.b_take.val': 'nextion_page1_b_take_val',
    'nextion_sensors_main_b_home_pic': 'nextion_sensors_main_b_home_pic',
    'sensors_main.b_home.pic': 'nextion_sensors_main_b_home_pic',
    'nextion_sensors_main_b_home_val': 'nextion_sensors_main_b_home_val',
    'sensors_main.b_home.val': 'nextion_sensors_main_b_home_val',
    'nextion_sensors_main_t0_txt': 'nextion_sensors_main_t0_txt',
    'sensors_main.t0.txt': 'nextion_sensors_main_t0_txt',

    # -------------------------------------------------------------------------
    # 12_TKINTER_SCAN_KATALOG: Pełny katalog Tkinter z automatycznego skanu
    # -------------------------------------------------------------------------
    'tk_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state': 'tk_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state',
    'tk_editor_editor_ehr_tarzanaxissandbox_step_canvas_state': 'tk_editor_editor_ehr_tarzanaxissandbox_step_canvas_state',
    'tk_editor_editor_ehr_tarzanehrui_axis_info_label_text': 'tk_editor_editor_ehr_tarzanehrui_axis_info_label_text',
    'tk_editor_editor_ehr_tarzanehrui_canvas_state': 'tk_editor_editor_ehr_tarzanehrui_canvas_state',
    'tk_editor_editor_ehr_tarzanehrui_curve_canvas_state': 'tk_editor_editor_ehr_tarzanehrui_curve_canvas_state',
    'tk_editor_editor_ehr_tarzanehrui_left_state': 'tk_editor_editor_ehr_tarzanehrui_left_state',
    'tk_editor_editor_ehr_tarzanehrui_protocol_box_state': 'tk_editor_editor_ehr_tarzanehrui_protocol_box_state',
    'tk_editor_editor_ehr_tarzanehrui_protocol_canvas_state': 'tk_editor_editor_ehr_tarzanehrui_protocol_canvas_state',
    'tk_editor_editor_ehr_tarzanehrui_protocol_holder_state': 'tk_editor_editor_ehr_tarzanehrui_protocol_holder_state',
    'tk_editor_editor_ehr_tarzanehrui_protocol_label_text': 'tk_editor_editor_ehr_tarzanehrui_protocol_label_text',
    'tk_editor_editor_ehr_tarzanehrui_protocol_text_text': 'tk_editor_editor_ehr_tarzanehrui_protocol_text_text',
    'tk_editor_editor_ehr_tarzanehrui_row_frame_state': 'tk_editor_editor_ehr_tarzanehrui_row_frame_state',
    'tk_editor_editor_ehr_tarzanehrui_save_button_text': 'tk_editor_editor_ehr_tarzanehrui_save_button_text',
    'tk_editor_editor_ehr_tarzanehrui_status_text': 'tk_editor_editor_ehr_tarzanehrui_status_text',
    'tk_editor_editor_ehr_tarzanehrui_step_canvas_state': 'tk_editor_editor_ehr_tarzanehrui_step_canvas_state',
    'tk_editor_editor_ehr_tarzanehrui_take_panel_state': 'tk_editor_editor_ehr_tarzanehrui_take_panel_state',
    'tk_editor_editor_ehr_tarzanehrui_timeline_canvas_state': 'tk_editor_editor_ehr_tarzanehrui_timeline_canvas_state',
    'tk_editor_editor_tarzanaxissandbox_curve_canvas_state': 'tk_editor_editor_tarzanaxissandbox_curve_canvas_state',
    'tk_editor_editor_tarzanaxissandbox_step_canvas_state': 'tk_editor_editor_tarzanaxissandbox_step_canvas_state',
    'tk_editor_editor_tarzanehrtakesandbox_canvas_state': 'tk_editor_editor_tarzanehrtakesandbox_canvas_state',
    'tk_editor_editor_tarzanehrtakesandbox_controls_wrap_state': 'tk_editor_editor_tarzanehrtakesandbox_controls_wrap_state',
    'tk_editor_editor_tarzanehrtakesandbox_protocol_canvas_state': 'tk_editor_editor_tarzanehrtakesandbox_protocol_canvas_state',
    'tk_editor_editor_tarzanehrtakesandbox_protocol_holder_state': 'tk_editor_editor_tarzanehrtakesandbox_protocol_holder_state',
    'tk_editor_editor_tarzanehrtakesandbox_row_frame_state': 'tk_editor_editor_tarzanehrtakesandbox_row_frame_state',
    'tk_editor_editor_tarzanehrtakesandbox_save_button_text': 'tk_editor_editor_tarzanehrtakesandbox_save_button_text',
    'tk_editor_editor_tarzantakeprotocollight_canvas_state': 'tk_editor_editor_tarzantakeprotocollight_canvas_state',
    'tk_editor_editor_tarzantakeprotocollight_protocol_canvas_state': 'tk_editor_editor_tarzantakeprotocollight_protocol_canvas_state',
    'tk_editor_editor_tarzantakeprotocollight_protocol_holder_state': 'tk_editor_editor_tarzantakeprotocollight_protocol_holder_state',
    'tk_editor_editor_tarzantakeprotocollight_row_frame_state': 'tk_editor_editor_tarzantakeprotocollight_row_frame_state',
    'tk_editor_editor_tarzantakeprotocollight_save_button_text': 'tk_editor_editor_tarzantakeprotocollight_save_button_text',
    'tk_editor_ehr_tarzanaxissandbox_curve_canvas_state': 'tk_editor_ehr_tarzanaxissandbox_curve_canvas_state',
    'tk_editor_ehr_tarzanaxissandbox_step_canvas_state': 'tk_editor_ehr_tarzanaxissandbox_step_canvas_state',
    'tk_editor_ehr_tarzanehrui_axis_info_label_text': 'tk_editor_ehr_tarzanehrui_axis_info_label_text',
    'tk_editor_ehr_tarzanehrui_canvas_state': 'tk_editor_ehr_tarzanehrui_canvas_state',
    'tk_editor_ehr_tarzanehrui_curve_canvas_state': 'tk_editor_ehr_tarzanehrui_curve_canvas_state',
    'tk_editor_ehr_tarzanehrui_left_state': 'tk_editor_ehr_tarzanehrui_left_state',
    'tk_editor_ehr_tarzanehrui_protocol_box_state': 'tk_editor_ehr_tarzanehrui_protocol_box_state',
    'tk_editor_ehr_tarzanehrui_protocol_canvas_state': 'tk_editor_ehr_tarzanehrui_protocol_canvas_state',
    'tk_editor_ehr_tarzanehrui_protocol_holder_state': 'tk_editor_ehr_tarzanehrui_protocol_holder_state',
    'tk_editor_ehr_tarzanehrui_protocol_label_text': 'tk_editor_ehr_tarzanehrui_protocol_label_text',
    'tk_editor_ehr_tarzanehrui_protocol_text_text': 'tk_editor_ehr_tarzanehrui_protocol_text_text',
    'tk_editor_ehr_tarzanehrui_row_frame_state': 'tk_editor_ehr_tarzanehrui_row_frame_state',
    'tk_editor_ehr_tarzanehrui_save_button_text': 'tk_editor_ehr_tarzanehrui_save_button_text',
    'tk_editor_ehr_tarzanehrui_selected_point_time_label_text': 'tk_editor_ehr_tarzanehrui_selected_point_time_label_text',
    'tk_editor_ehr_tarzanehrui_status_text': 'tk_editor_ehr_tarzanehrui_status_text',
    'tk_editor_ehr_tarzanehrui_step_canvas_state': 'tk_editor_ehr_tarzanehrui_step_canvas_state',
    'tk_editor_ehr_tarzanehrui_take_panel_state': 'tk_editor_ehr_tarzanehrui_take_panel_state',
    'tk_editor_ehr_tarzanehrui_timeline_canvas_state': 'tk_editor_ehr_tarzanehrui_timeline_canvas_state',
    'tk_editor_par_tarzannextionpreview_page_label_text': 'tk_editor_par_tarzannextionpreview_page_label_text',
    'tk_editor_par_tarzannextionpreview_screen_canvas_state': 'tk_editor_par_tarzannextionpreview_screen_canvas_state',
    'tk_editor_par_tarzannextionpreview_screen_frame_state': 'tk_editor_par_tarzannextionpreview_screen_frame_state',
    'tk_editor_par_tarzannextionpreview_status_text': 'tk_editor_par_tarzannextionpreview_status_text',
    'tk_editor_par_tarzanparapp_body_state': 'tk_editor_par_tarzanparapp_body_state',
    'tk_editor_par_tarzanparapp_bottom_state': 'tk_editor_par_tarzanparapp_bottom_state',
    'tk_editor_par_tarzanparapp_clock_text': 'tk_editor_par_tarzanparapp_clock_text',
    'tk_editor_par_tarzanparapp_footer_state': 'tk_editor_par_tarzanparapp_footer_state',
    'tk_editor_par_tarzanparapp_header_state': 'tk_editor_par_tarzanparapp_header_state',
    'tk_editor_par_tarzanparapp_layout_master_state': 'tk_editor_par_tarzanparapp_layout_master_state',
    'tk_editor_par_tarzanparapp_left_state': 'tk_editor_par_tarzanparapp_left_state',
    'tk_editor_par_tarzanparapp_middle_bottom_state': 'tk_editor_par_tarzanparapp_middle_bottom_state',
    'tk_editor_par_tarzanparapp_middle_top_state': 'tk_editor_par_tarzanparapp_middle_top_state',
    'tk_editor_par_tarzanparapp_mode_label_text': 'tk_editor_par_tarzanparapp_mode_label_text',
    'tk_editor_par_tarzanparapp_right_state': 'tk_editor_par_tarzanparapp_right_state',
    'tk_editor_par_tarzanparapp_top_state': 'tk_editor_par_tarzanparapp_top_state',
    'tk_editor_par_tarzanparpanels_log_text_text': 'tk_editor_par_tarzanparpanels_log_text_text',
    'tk_editor_par_tarzanparpanels_old_log_text_text': 'tk_editor_par_tarzanparpanels_old_log_text_text',
    'tk_editor_par_tarzanparpanels_timeline_canvas_state': 'tk_editor_par_tarzanparpanels_timeline_canvas_state',
    'tk_editor_par_tarzanparwidgets_body_state': 'tk_editor_par_tarzanparwidgets_body_state',
    'tk_editor_par_tarzanparwidgets_counter_label_text': 'tk_editor_par_tarzanparwidgets_counter_label_text',
    'tk_editor_par_tarzanparwidgets_motor_canvas_state': 'tk_editor_par_tarzanparwidgets_motor_canvas_state',
    'tk_editor_tarzanaxissandbox_curve_canvas_state': 'tk_editor_tarzanaxissandbox_curve_canvas_state',
    'tk_editor_tarzanaxissandbox_step_canvas_state': 'tk_editor_tarzanaxissandbox_step_canvas_state',
    'tk_editor_tarzanehrtakesandbox_canvas_state': 'tk_editor_tarzanehrtakesandbox_canvas_state',
    'tk_editor_tarzanehrtakesandbox_controls_wrap_state': 'tk_editor_tarzanehrtakesandbox_controls_wrap_state',
    'tk_editor_tarzanehrtakesandbox_protocol_canvas_state': 'tk_editor_tarzanehrtakesandbox_protocol_canvas_state',
    'tk_editor_tarzanehrtakesandbox_protocol_holder_state': 'tk_editor_tarzanehrtakesandbox_protocol_holder_state',
    'tk_editor_tarzanehrtakesandbox_row_frame_state': 'tk_editor_tarzanehrtakesandbox_row_frame_state',
    'tk_editor_tarzanehrtakesandbox_save_button_text': 'tk_editor_tarzanehrtakesandbox_save_button_text',
    'tk_editor_tarzankhr_btn_start_text': 'tk_editor_tarzankhr_btn_start_text',
    'tk_editor_tarzankhr_btn_stop_text': 'tk_editor_tarzankhr_btn_stop_text',
    'tk_editor_tarzankhr_input_canvas_state': 'tk_editor_tarzankhr_input_canvas_state',
    'tk_editor_tarzankhr_khr_canvas_state': 'tk_editor_tarzankhr_khr_canvas_state',
    'tk_editor_tarzankhr_output_canvas_state': 'tk_editor_tarzankhr_output_canvas_state',
    'tk_editor_tarzankhr_plugin_box_text': 'tk_editor_tarzankhr_plugin_box_text',
    'tk_editor_tarzankhr_preview_canvas_state': 'tk_editor_tarzankhr_preview_canvas_state',
    'tk_editor_tarzankhr_profile_box_text': 'tk_editor_tarzankhr_profile_box_text',
    'tk_editor_tarzankhr_profile_desc_text': 'tk_editor_tarzankhr_profile_desc_text',
    'tk_editor_tarzankhr_status_text': 'tk_editor_tarzankhr_status_text',
    'tk_editor_tarzantakeprotocollight_canvas_state': 'tk_editor_tarzantakeprotocollight_canvas_state',
    'tk_editor_tarzantakeprotocollight_protocol_canvas_state': 'tk_editor_tarzantakeprotocollight_protocol_canvas_state',
    'tk_editor_tarzantakeprotocollight_protocol_holder_state': 'tk_editor_tarzantakeprotocollight_protocol_holder_state',
    'tk_editor_tarzantakeprotocollight_row_frame_state': 'tk_editor_tarzantakeprotocollight_row_frame_state',
    'tk_editor_tarzantakeprotocollight_save_button_text': 'tk_editor_tarzantakeprotocollight_save_button_text',
    'tk_hardware_tarzannextion_tarzannextionsandbox_log_text': 'tk_hardware_tarzannextion_tarzannextionsandbox_log_text',
    'tk_mechanics_tarzanedytorchoreografiiruchu_global_canvas_state': 'tk_mechanics_tarzanedytorchoreografiiruchu_global_canvas_state',
    'tk_mechanics_tarzanedytorchoreografiiruchu_scroll_canvas_state': 'tk_mechanics_tarzanedytorchoreografiiruchu_scroll_canvas_state',
    'tk_mechanics_tarzanedytorchoreografiiruchu_tracks_frame_state': 'tk_mechanics_tarzanedytorchoreografiiruchu_tracks_frame_state',
    'tk_mechanics_tarzanpanelosi_row1_state': 'tk_mechanics_tarzanpanelosi_row1_state',
    'tk_mechanics_tarzanpanelosi_row2_state': 'tk_mechanics_tarzanpanelosi_row2_state',
    'tk_mechanics_tarzanpanelosi_row3_state': 'tk_mechanics_tarzanpanelosi_row3_state',
    'tk_mechanics_tarzanwykresosi_canvas_state': 'tk_mechanics_tarzanwykresosi_canvas_state',
    'tk_mechanics_tarzanwykresosi_limit_canvas_state': 'tk_mechanics_tarzanwykresosi_limit_canvas_state',
    'tk_mechanics_tarzanwykresosi_limit_panel_state': 'tk_mechanics_tarzanwykresosi_limit_panel_state',
    'tk_mechanics_tarzanwykresosi_meta_label_text': 'tk_mechanics_tarzanwykresosi_meta_label_text',
    'tk_mechanics_tarzanwykresosi_title_text': 'tk_mechanics_tarzanwykresosi_title_text',
    'tk_modes_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state': 'tk_modes_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state',
    'tk_modes_editor_editor_ehr_tarzanaxissandbox_step_canvas_state': 'tk_modes_editor_editor_ehr_tarzanaxissandbox_step_canvas_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_axis_info_label_text': 'tk_modes_editor_editor_ehr_tarzanehrui_axis_info_label_text',
    'tk_modes_editor_editor_ehr_tarzanehrui_canvas_state': 'tk_modes_editor_editor_ehr_tarzanehrui_canvas_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_curve_canvas_state': 'tk_modes_editor_editor_ehr_tarzanehrui_curve_canvas_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_left_state': 'tk_modes_editor_editor_ehr_tarzanehrui_left_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_box_state': 'tk_modes_editor_editor_ehr_tarzanehrui_protocol_box_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_state': 'tk_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_holder_state': 'tk_modes_editor_editor_ehr_tarzanehrui_protocol_holder_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_label_text': 'tk_modes_editor_editor_ehr_tarzanehrui_protocol_label_text',
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_text_text': 'tk_modes_editor_editor_ehr_tarzanehrui_protocol_text_text',
    'tk_modes_editor_editor_ehr_tarzanehrui_row_frame_state': 'tk_modes_editor_editor_ehr_tarzanehrui_row_frame_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_save_button_text': 'tk_modes_editor_editor_ehr_tarzanehrui_save_button_text',
    'tk_modes_editor_editor_ehr_tarzanehrui_status_text': 'tk_modes_editor_editor_ehr_tarzanehrui_status_text',
    'tk_modes_editor_editor_ehr_tarzanehrui_step_canvas_state': 'tk_modes_editor_editor_ehr_tarzanehrui_step_canvas_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_take_panel_state': 'tk_modes_editor_editor_ehr_tarzanehrui_take_panel_state',
    'tk_modes_editor_editor_ehr_tarzanehrui_timeline_canvas_state': 'tk_modes_editor_editor_ehr_tarzanehrui_timeline_canvas_state',
    'tk_modes_editor_editor_tarzanaxissandbox_curve_canvas_state': 'tk_modes_editor_editor_tarzanaxissandbox_curve_canvas_state',
    'tk_modes_editor_editor_tarzanaxissandbox_step_canvas_state': 'tk_modes_editor_editor_tarzanaxissandbox_step_canvas_state',
    'tk_modes_editor_editor_tarzanehrtakesandbox_canvas_state': 'tk_modes_editor_editor_tarzanehrtakesandbox_canvas_state',
    'tk_modes_editor_editor_tarzanehrtakesandbox_controls_wrap_state': 'tk_modes_editor_editor_tarzanehrtakesandbox_controls_wrap_state',
    'tk_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_state': 'tk_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_state',
    'tk_modes_editor_editor_tarzanehrtakesandbox_protocol_holder_state': 'tk_modes_editor_editor_tarzanehrtakesandbox_protocol_holder_state',
    'tk_modes_editor_editor_tarzanehrtakesandbox_row_frame_state': 'tk_modes_editor_editor_tarzanehrtakesandbox_row_frame_state',
    'tk_modes_editor_editor_tarzanehrtakesandbox_save_button_text': 'tk_modes_editor_editor_tarzanehrtakesandbox_save_button_text',
    'tk_modes_editor_editor_tarzantakeprotocollight_canvas_state': 'tk_modes_editor_editor_tarzantakeprotocollight_canvas_state',
    'tk_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_state': 'tk_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_state',
    'tk_modes_editor_editor_tarzantakeprotocollight_protocol_holder_state': 'tk_modes_editor_editor_tarzantakeprotocollight_protocol_holder_state',
    'tk_modes_editor_editor_tarzantakeprotocollight_row_frame_state': 'tk_modes_editor_editor_tarzantakeprotocollight_row_frame_state',
    'tk_modes_editor_editor_tarzantakeprotocollight_save_button_text': 'tk_modes_editor_editor_tarzantakeprotocollight_save_button_text',
    'tk_modes_editor_ehr_tarzanaxissandbox_curve_canvas_state': 'tk_modes_editor_ehr_tarzanaxissandbox_curve_canvas_state',
    'tk_modes_editor_ehr_tarzanaxissandbox_step_canvas_state': 'tk_modes_editor_ehr_tarzanaxissandbox_step_canvas_state',
    'tk_modes_editor_ehr_tarzanehrui_axis_info_label_text': 'tk_modes_editor_ehr_tarzanehrui_axis_info_label_text',
    'tk_modes_editor_ehr_tarzanehrui_canvas_state': 'tk_modes_editor_ehr_tarzanehrui_canvas_state',
    'tk_modes_editor_ehr_tarzanehrui_curve_canvas_state': 'tk_modes_editor_ehr_tarzanehrui_curve_canvas_state',
    'tk_modes_editor_ehr_tarzanehrui_left_state': 'tk_modes_editor_ehr_tarzanehrui_left_state',
    'tk_modes_editor_ehr_tarzanehrui_protocol_box_state': 'tk_modes_editor_ehr_tarzanehrui_protocol_box_state',
    'tk_modes_editor_ehr_tarzanehrui_protocol_canvas_state': 'tk_modes_editor_ehr_tarzanehrui_protocol_canvas_state',
    'tk_modes_editor_ehr_tarzanehrui_protocol_holder_state': 'tk_modes_editor_ehr_tarzanehrui_protocol_holder_state',
    'tk_modes_editor_ehr_tarzanehrui_protocol_label_text': 'tk_modes_editor_ehr_tarzanehrui_protocol_label_text',
    'tk_modes_editor_ehr_tarzanehrui_protocol_text_text': 'tk_modes_editor_ehr_tarzanehrui_protocol_text_text',
    'tk_modes_editor_ehr_tarzanehrui_row_frame_state': 'tk_modes_editor_ehr_tarzanehrui_row_frame_state',
    'tk_modes_editor_ehr_tarzanehrui_save_button_text': 'tk_modes_editor_ehr_tarzanehrui_save_button_text',
    'tk_modes_editor_ehr_tarzanehrui_selected_point_time_label_text': 'tk_modes_editor_ehr_tarzanehrui_selected_point_time_label_text',
    'tk_modes_editor_ehr_tarzanehrui_status_text': 'tk_modes_editor_ehr_tarzanehrui_status_text',
    'tk_modes_editor_ehr_tarzanehrui_step_canvas_state': 'tk_modes_editor_ehr_tarzanehrui_step_canvas_state',
    'tk_modes_editor_ehr_tarzanehrui_take_panel_state': 'tk_modes_editor_ehr_tarzanehrui_take_panel_state',
    'tk_modes_editor_ehr_tarzanehrui_timeline_canvas_state': 'tk_modes_editor_ehr_tarzanehrui_timeline_canvas_state',
    'tk_modes_editor_par_tarzannextionpreview_page_label_text': 'tk_modes_editor_par_tarzannextionpreview_page_label_text',
    'tk_modes_editor_par_tarzannextionpreview_screen_canvas_state': 'tk_modes_editor_par_tarzannextionpreview_screen_canvas_state',
    'tk_modes_editor_par_tarzannextionpreview_screen_frame_state': 'tk_modes_editor_par_tarzannextionpreview_screen_frame_state',
    'tk_modes_editor_par_tarzannextionpreview_status_text': 'tk_modes_editor_par_tarzannextionpreview_status_text',
    'tk_modes_editor_par_tarzanparapp_body_state': 'tk_modes_editor_par_tarzanparapp_body_state',
    'tk_modes_editor_par_tarzanparapp_bottom_state': 'tk_modes_editor_par_tarzanparapp_bottom_state',
    'tk_modes_editor_par_tarzanparapp_clock_text': 'tk_modes_editor_par_tarzanparapp_clock_text',
    'tk_modes_editor_par_tarzanparapp_footer_state': 'tk_modes_editor_par_tarzanparapp_footer_state',
    'tk_modes_editor_par_tarzanparapp_header_state': 'tk_modes_editor_par_tarzanparapp_header_state',
    'tk_modes_editor_par_tarzanparapp_layout_master_state': 'tk_modes_editor_par_tarzanparapp_layout_master_state',
    'tk_modes_editor_par_tarzanparapp_left_state': 'tk_modes_editor_par_tarzanparapp_left_state',
    'tk_modes_editor_par_tarzanparapp_middle_bottom_state': 'tk_modes_editor_par_tarzanparapp_middle_bottom_state',
    'tk_modes_editor_par_tarzanparapp_middle_top_state': 'tk_modes_editor_par_tarzanparapp_middle_top_state',
    'tk_modes_editor_par_tarzanparapp_mode_label_text': 'tk_modes_editor_par_tarzanparapp_mode_label_text',
    'tk_modes_editor_par_tarzanparapp_right_state': 'tk_modes_editor_par_tarzanparapp_right_state',
    'tk_modes_editor_par_tarzanparapp_top_state': 'tk_modes_editor_par_tarzanparapp_top_state',
    'tk_modes_editor_par_tarzanparpanels_log_text_text': 'tk_modes_editor_par_tarzanparpanels_log_text_text',
    'tk_modes_editor_par_tarzanparpanels_old_log_text_text': 'tk_modes_editor_par_tarzanparpanels_old_log_text_text',
    'tk_modes_editor_par_tarzanparpanels_timeline_canvas_state': 'tk_modes_editor_par_tarzanparpanels_timeline_canvas_state',
    'tk_modes_editor_par_tarzanparwidgets_body_state': 'tk_modes_editor_par_tarzanparwidgets_body_state',
    'tk_modes_editor_par_tarzanparwidgets_counter_label_text': 'tk_modes_editor_par_tarzanparwidgets_counter_label_text',
    'tk_modes_editor_par_tarzanparwidgets_motor_canvas_state': 'tk_modes_editor_par_tarzanparwidgets_motor_canvas_state',
    'tk_modes_editor_tarzanaxissandbox_curve_canvas_state': 'tk_modes_editor_tarzanaxissandbox_curve_canvas_state',
    'tk_modes_editor_tarzanaxissandbox_step_canvas_state': 'tk_modes_editor_tarzanaxissandbox_step_canvas_state',
    'tk_modes_editor_tarzanehrtakesandbox_canvas_state': 'tk_modes_editor_tarzanehrtakesandbox_canvas_state',
    'tk_modes_editor_tarzanehrtakesandbox_controls_wrap_state': 'tk_modes_editor_tarzanehrtakesandbox_controls_wrap_state',
    'tk_modes_editor_tarzanehrtakesandbox_protocol_canvas_state': 'tk_modes_editor_tarzanehrtakesandbox_protocol_canvas_state',
    'tk_modes_editor_tarzanehrtakesandbox_protocol_holder_state': 'tk_modes_editor_tarzanehrtakesandbox_protocol_holder_state',
    'tk_modes_editor_tarzanehrtakesandbox_row_frame_state': 'tk_modes_editor_tarzanehrtakesandbox_row_frame_state',
    'tk_modes_editor_tarzanehrtakesandbox_save_button_text': 'tk_modes_editor_tarzanehrtakesandbox_save_button_text',
    'tk_modes_editor_tarzankhr_btn_start_text': 'tk_modes_editor_tarzankhr_btn_start_text',
    'tk_modes_editor_tarzankhr_btn_stop_text': 'tk_modes_editor_tarzankhr_btn_stop_text',
    'tk_modes_editor_tarzankhr_input_canvas_state': 'tk_modes_editor_tarzankhr_input_canvas_state',
    'tk_modes_editor_tarzankhr_khr_canvas_state': 'tk_modes_editor_tarzankhr_khr_canvas_state',
    'tk_modes_editor_tarzankhr_output_canvas_state': 'tk_modes_editor_tarzankhr_output_canvas_state',
    'tk_modes_editor_tarzankhr_plugin_box_text': 'tk_modes_editor_tarzankhr_plugin_box_text',
    'tk_modes_editor_tarzankhr_preview_canvas_state': 'tk_modes_editor_tarzankhr_preview_canvas_state',
    'tk_modes_editor_tarzankhr_profile_box_text': 'tk_modes_editor_tarzankhr_profile_box_text',
    'tk_modes_editor_tarzankhr_profile_desc_text': 'tk_modes_editor_tarzankhr_profile_desc_text',
    'tk_modes_editor_tarzankhr_status_text': 'tk_modes_editor_tarzankhr_status_text',
    'tk_modes_editor_tarzantakeprotocollight_canvas_state': 'tk_modes_editor_tarzantakeprotocollight_canvas_state',
    'tk_modes_editor_tarzantakeprotocollight_protocol_canvas_state': 'tk_modes_editor_tarzantakeprotocollight_protocol_canvas_state',
    'tk_modes_editor_tarzantakeprotocollight_protocol_holder_state': 'tk_modes_editor_tarzantakeprotocollight_protocol_holder_state',
    'tk_modes_editor_tarzantakeprotocollight_row_frame_state': 'tk_modes_editor_tarzantakeprotocollight_row_frame_state',
    'tk_modes_editor_tarzantakeprotocollight_save_button_text': 'tk_modes_editor_tarzantakeprotocollight_save_button_text',
    'tk_modes_hardware_tarzannextion_tarzannextionsandbox_log_text': 'tk_modes_hardware_tarzannextion_tarzannextionsandbox_log_text',
    'tk_vision_tarzanvisionsetup_content_state': 'tk_vision_tarzanvisionsetup_content_state',

    # -------------------------------------------------------------------------
    # 13_CANVAS_SCAN_KATALOG: Pełny katalog Canvas z automatycznego skanu
    # -------------------------------------------------------------------------
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text',
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text': 'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords': 'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1911_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1911_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1920_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1920_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1953_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1953_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1954_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1954_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1981_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1981_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1982_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1982_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2720_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2720_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2727_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2727_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2736_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2736_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2809_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2809_text',
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2816_text': 'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2816_text',
    'canvas_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords': 'canvas_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords',
    'canvas_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords': 'canvas_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords',
    'canvas_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords': 'canvas_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords',
    'canvas_editor_editor_ehr_tarzanehrui_item_text': 'canvas_editor_editor_ehr_tarzanehrui_item_text',
    'canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords': 'canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords',
    'canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords': 'canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords',
    'canvas_editor_editor_ehr_tarzanehrui_row_window_coords': 'canvas_editor_editor_ehr_tarzanehrui_row_window_coords',
    'canvas_editor_editor_ehr_tarzanehrui_save_button_window_coords': 'canvas_editor_editor_ehr_tarzanehrui_save_button_window_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_826_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_826_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_833_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_833_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_852_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_852_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_859_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_859_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_871_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_871_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_872_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_872_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_886_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_886_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_898_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_898_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_900_coords': 'canvas_editor_editor_tarzanaxissandbox_c_line_line_900_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_oval_line_868_coords': 'canvas_editor_editor_tarzanaxissandbox_c_oval_line_868_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords': 'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords': 'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords': 'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords',
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_827_text': 'canvas_editor_editor_tarzanaxissandbox_c_text_line_827_text',
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_834_text': 'canvas_editor_editor_tarzanaxissandbox_c_text_line_834_text',
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_873_text': 'canvas_editor_editor_tarzanaxissandbox_c_text_line_873_text',
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_874_text': 'canvas_editor_editor_tarzanaxissandbox_c_text_line_874_text',
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_901_text': 'canvas_editor_editor_tarzanaxissandbox_c_text_line_901_text',
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_902_text': 'canvas_editor_editor_tarzanaxissandbox_c_text_line_902_text',
    'canvas_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': 'canvas_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords',
    'canvas_editor_editor_tarzanehrtakesandbox_item_text': 'canvas_editor_editor_tarzanehrtakesandbox_item_text',
    'canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': 'canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords',
    'canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': 'canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords',
    'canvas_editor_editor_tarzanehrtakesandbox_protocol_title_id_text': 'canvas_editor_editor_tarzanehrtakesandbox_protocol_title_id_text',
    'canvas_editor_editor_tarzanehrtakesandbox_row_window_coords': 'canvas_editor_editor_tarzanehrtakesandbox_row_window_coords',
    'canvas_editor_editor_tarzanehrtakesandbox_save_button_window_coords': 'canvas_editor_editor_tarzanehrtakesandbox_save_button_window_coords',
    'canvas_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords': 'canvas_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords',
    'canvas_editor_editor_tarzantakeprotocollight_item_text': 'canvas_editor_editor_tarzantakeprotocollight_item_text',
    'canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': 'canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords',
    'canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': 'canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords',
    'canvas_editor_editor_tarzantakeprotocollight_protocol_title_id_text': 'canvas_editor_editor_tarzantakeprotocollight_protocol_title_id_text',
    'canvas_editor_editor_tarzantakeprotocollight_row_window_coords': 'canvas_editor_editor_tarzantakeprotocollight_row_window_coords',
    'canvas_editor_editor_tarzantakeprotocollight_save_button_window_coords': 'canvas_editor_editor_tarzantakeprotocollight_save_button_window_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_827_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_827_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_834_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_834_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_841_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_841_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_853_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_854_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_854_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_868_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_868_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_880_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_880_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_882_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_line_line_882_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords': 'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords',
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_828_text': 'canvas_editor_ehr_tarzanaxissandbox_c_text_line_828_text',
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_835_text': 'canvas_editor_ehr_tarzanaxissandbox_c_text_line_835_text',
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_855_text': 'canvas_editor_ehr_tarzanaxissandbox_c_text_line_855_text',
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_856_text': 'canvas_editor_ehr_tarzanaxissandbox_c_text_line_856_text',
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_883_text': 'canvas_editor_ehr_tarzanaxissandbox_c_text_line_883_text',
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_884_text': 'canvas_editor_ehr_tarzanaxissandbox_c_text_line_884_text',
    'canvas_editor_ehr_tarzanehrui_c_image_line_3130_coords': 'canvas_editor_ehr_tarzanehrui_c_image_line_3130_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_1993_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_1993_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2002_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2002_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2013_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2013_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2020_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2020_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2048_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2048_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2049_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2049_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2068_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2068_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2080_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2080_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_2082_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_2082_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3081_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3081_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3102_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3102_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3105_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3105_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3145_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3145_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3153_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3153_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3161_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3161_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3176_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3176_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3217_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3217_coords',
    'canvas_editor_ehr_tarzanehrui_c_line_line_3231_coords': 'canvas_editor_ehr_tarzanehrui_c_line_line_3231_coords',
    'canvas_editor_ehr_tarzanehrui_c_oval_line_2044_coords': 'canvas_editor_ehr_tarzanehrui_c_oval_line_2044_coords',
    'canvas_editor_ehr_tarzanehrui_c_oval_line_3194_coords': 'canvas_editor_ehr_tarzanehrui_c_oval_line_3194_coords',
    'canvas_editor_ehr_tarzanehrui_c_oval_line_3210_coords': 'canvas_editor_ehr_tarzanehrui_c_oval_line_3210_coords',
    'canvas_editor_ehr_tarzanehrui_c_polygon_line_3226_coords': 'canvas_editor_ehr_tarzanehrui_c_polygon_line_3226_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords',
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords': 'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords',
    'canvas_editor_ehr_tarzanehrui_c_text_line_1994_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_1994_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_2003_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_2003_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_2050_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_2050_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_2051_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_2051_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_2083_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_2083_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_2084_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_2084_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_3115_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_3115_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_3122_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_3122_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_3132_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_3132_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_3228_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_3228_text',
    'canvas_editor_ehr_tarzanehrui_c_text_line_3239_text': 'canvas_editor_ehr_tarzanehrui_c_text_line_3239_text',
    'canvas_editor_ehr_tarzanehrui_canvas_image_line_760_coords': 'canvas_editor_ehr_tarzanehrui_canvas_image_line_760_coords',
    'canvas_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords': 'canvas_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords',
    'canvas_editor_ehr_tarzanehrui_canvas_window_line_1226_coords': 'canvas_editor_ehr_tarzanehrui_canvas_window_line_1226_coords',
    'canvas_editor_ehr_tarzanehrui_item_text': 'canvas_editor_ehr_tarzanehrui_item_text',
    'canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords': 'canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords',
    'canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords': 'canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords',
    'canvas_editor_ehr_tarzanehrui_row_window_coords': 'canvas_editor_ehr_tarzanehrui_row_window_coords',
    'canvas_editor_ehr_tarzanehrui_save_button_window_coords': 'canvas_editor_ehr_tarzanehrui_save_button_window_coords',
    'canvas_editor_par_tarzannextionpreview_edit_window_coords': 'canvas_editor_par_tarzannextionpreview_edit_window_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords': 'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text',
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text': 'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text',
    'canvas_editor_par_tarzanparapp_canvas_oval_line_1309_coords': 'canvas_editor_par_tarzanparapp_canvas_oval_line_1309_coords',
    'canvas_editor_par_tarzanparapp_canvas_oval_line_1402_coords': 'canvas_editor_par_tarzanparapp_canvas_oval_line_1402_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords',
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords': 'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords',
    'canvas_editor_par_tarzanparapp_canvas_text_line_1310_text': 'canvas_editor_par_tarzanparapp_canvas_text_line_1310_text',
    'canvas_editor_par_tarzanparapp_canvas_text_line_1434_text': 'canvas_editor_par_tarzanparapp_canvas_text_line_1434_text',
    'canvas_editor_par_tarzanparapp_canvas_text_line_1451_text': 'canvas_editor_par_tarzanparapp_canvas_text_line_1451_text',
    'canvas_editor_par_tarzanparapp_canvas_text_line_1455_text': 'canvas_editor_par_tarzanparapp_canvas_text_line_1455_text',
    'canvas_editor_par_tarzanparapp_led_oval_line_485_coords': 'canvas_editor_par_tarzanparapp_led_oval_line_485_coords',
    'canvas_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords': 'canvas_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords',
    'canvas_editor_par_tarzanparapp_text_id_text': 'canvas_editor_par_tarzanparapp_text_id_text',
    'canvas_editor_par_tarzanparpanels_can_image_line_1306_coords': 'canvas_editor_par_tarzanparpanels_can_image_line_1306_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_1298_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_1298_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_1299_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_1299_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_1304_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_1304_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_1311_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_1311_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_1326_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_1326_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_1327_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_1327_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_510_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_510_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_664_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_664_coords',
    'canvas_editor_par_tarzanparpanels_can_line_line_665_coords': 'canvas_editor_par_tarzanparpanels_can_line_line_665_coords',
    'canvas_editor_par_tarzanparpanels_can_oval_line_509_coords': 'canvas_editor_par_tarzanparpanels_can_oval_line_509_coords',
    'canvas_editor_par_tarzanparpanels_can_oval_line_511_coords': 'canvas_editor_par_tarzanparpanels_can_oval_line_511_coords',
    'canvas_editor_par_tarzanparpanels_can_oval_line_656_coords': 'canvas_editor_par_tarzanparpanels_can_oval_line_656_coords',
    'canvas_editor_par_tarzanparpanels_can_oval_line_920_coords': 'canvas_editor_par_tarzanparpanels_can_oval_line_920_coords',
    'canvas_editor_par_tarzanparpanels_can_polygon_line_921_coords': 'canvas_editor_par_tarzanparpanels_can_polygon_line_921_coords',
    'canvas_editor_par_tarzanparpanels_can_rectangle_line_899_coords': 'canvas_editor_par_tarzanparpanels_can_rectangle_line_899_coords',
    'canvas_editor_par_tarzanparpanels_can_rectangle_line_901_coords': 'canvas_editor_par_tarzanparpanels_can_rectangle_line_901_coords',
    'canvas_editor_par_tarzanparpanels_can_text_line_1307_text': 'canvas_editor_par_tarzanparpanels_can_text_line_1307_text',
    'canvas_editor_par_tarzanparpanels_can_text_line_1309_text': 'canvas_editor_par_tarzanparpanels_can_text_line_1309_text',
    'canvas_editor_par_tarzanparpanels_can_text_line_1310_text': 'canvas_editor_par_tarzanparpanels_can_text_line_1310_text',
    'canvas_editor_par_tarzanparpanels_can_text_line_1329_text': 'canvas_editor_par_tarzanparpanels_can_text_line_1329_text',
    'canvas_editor_par_tarzanparpanels_can_text_line_1331_text': 'canvas_editor_par_tarzanparpanels_can_text_line_1331_text',
    'canvas_editor_par_tarzanparpanels_canvas_line_line_825_coords': 'canvas_editor_par_tarzanparpanels_canvas_line_line_825_coords',
    'canvas_editor_par_tarzanparpanels_canvas_line_line_826_coords': 'canvas_editor_par_tarzanparpanels_canvas_line_line_826_coords',
    'canvas_editor_par_tarzanparpanels_canvas_oval_line_1575_coords': 'canvas_editor_par_tarzanparpanels_canvas_oval_line_1575_coords',
    'canvas_editor_par_tarzanparpanels_canvas_oval_line_830_coords': 'canvas_editor_par_tarzanparpanels_canvas_oval_line_830_coords',
    'canvas_editor_par_tarzanparpanels_canvas_polygon_line_828_coords': 'canvas_editor_par_tarzanparpanels_canvas_polygon_line_828_coords',
    'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords': 'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords',
    'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords': 'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords',
    'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords': 'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords',
    'canvas_editor_par_tarzanparpanels_old_c_line_line_3118_coords': 'canvas_editor_par_tarzanparpanels_old_c_line_line_3118_coords',
    'canvas_editor_par_tarzanparpanels_old_c_line_line_3119_coords': 'canvas_editor_par_tarzanparpanels_old_c_line_line_3119_coords',
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_1979_coords': 'canvas_editor_par_tarzanparpanels_old_c_oval_line_1979_coords',
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_1980_coords': 'canvas_editor_par_tarzanparpanels_old_c_oval_line_1980_coords',
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_2212_coords': 'canvas_editor_par_tarzanparpanels_old_c_oval_line_2212_coords',
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_3111_coords': 'canvas_editor_par_tarzanparpanels_old_c_oval_line_3111_coords',
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_344_coords': 'canvas_editor_par_tarzanparpanels_old_c_oval_line_344_coords',
    'canvas_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords': 'canvas_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_767_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_767_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_780_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_780_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_781_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_781_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_784_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_line_line_784_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords',
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1551_text': 'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1551_text',
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1554_text': 'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1554_text',
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1555_text': 'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1555_text',
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1586_text': 'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1586_text',
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_766_text': 'canvas_editor_par_tarzanparpanels_old_canvas_text_line_766_text',
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_785_text': 'canvas_editor_par_tarzanparpanels_old_canvas_text_line_785_text',
    'canvas_editor_par_tarzanparpanels_old_canvas_window_line_119_coords': 'canvas_editor_par_tarzanparpanels_old_canvas_window_line_119_coords',
    'canvas_editor_par_tarzanparpanels_old_dot_oval_line_378_coords': 'canvas_editor_par_tarzanparpanels_old_dot_oval_line_378_coords',
    'canvas_editor_par_tarzanparpanels_old_led_oval_line_1049_coords': 'canvas_editor_par_tarzanparpanels_old_led_oval_line_1049_coords',
    'canvas_editor_par_tarzanparpanels_old_led_oval_line_1050_coords': 'canvas_editor_par_tarzanparpanels_old_led_oval_line_1050_coords',
    'canvas_editor_par_tarzanparpanels_old_rect_coords': 'canvas_editor_par_tarzanparpanels_old_rect_coords',
    'canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords': 'canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords',
    'canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords': 'canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords',
    'canvas_editor_par_tarzanparpanels_old_window_id_coords': 'canvas_editor_par_tarzanparpanels_old_window_id_coords',
    'canvas_editor_par_tarzanparpanels_self_rectangle_line_185_coords': 'canvas_editor_par_tarzanparpanels_self_rectangle_line_185_coords',
    'canvas_editor_par_tarzanparpanels_window_id_coords': 'canvas_editor_par_tarzanparpanels_window_id_coords',
    'canvas_editor_par_tarzanparwidgets_c_line_line_304_coords': 'canvas_editor_par_tarzanparwidgets_c_line_line_304_coords',
    'canvas_editor_par_tarzanparwidgets_c_oval_line_299_coords': 'canvas_editor_par_tarzanparwidgets_c_oval_line_299_coords',
    'canvas_editor_par_tarzanparwidgets_c_oval_line_300_coords': 'canvas_editor_par_tarzanparwidgets_c_oval_line_300_coords',
    'canvas_editor_par_tarzanparwidgets_c_oval_line_305_coords': 'canvas_editor_par_tarzanparwidgets_c_oval_line_305_coords',
    'canvas_editor_par_tarzanparwidgets_self_oval_line_59_coords': 'canvas_editor_par_tarzanparwidgets_self_oval_line_59_coords',
    'canvas_editor_par_tarzanparwidgets_self_oval_line_60_coords': 'canvas_editor_par_tarzanparwidgets_self_oval_line_60_coords',
    'canvas_editor_par_tarzanparwidgets_self_oval_line_64_coords': 'canvas_editor_par_tarzanparwidgets_self_oval_line_64_coords',
    'canvas_editor_par_tarzanparwidgets_self_oval_line_65_coords': 'canvas_editor_par_tarzanparwidgets_self_oval_line_65_coords',
    'canvas_editor_par_tarzanparwidgets_self_rectangle_line_90_coords': 'canvas_editor_par_tarzanparwidgets_self_rectangle_line_90_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_826_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_826_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_833_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_833_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_852_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_852_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_859_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_859_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_871_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_871_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_872_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_872_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_886_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_886_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_898_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_898_coords',
    'canvas_editor_tarzanaxissandbox_c_line_line_900_coords': 'canvas_editor_tarzanaxissandbox_c_line_line_900_coords',
    'canvas_editor_tarzanaxissandbox_c_oval_line_868_coords': 'canvas_editor_tarzanaxissandbox_c_oval_line_868_coords',
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_812_coords': 'canvas_editor_tarzanaxissandbox_c_rectangle_line_812_coords',
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_819_coords': 'canvas_editor_tarzanaxissandbox_c_rectangle_line_819_coords',
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_editor_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_editor_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_880_coords': 'canvas_editor_tarzanaxissandbox_c_rectangle_line_880_coords',
    'canvas_editor_tarzanaxissandbox_c_text_line_827_text': 'canvas_editor_tarzanaxissandbox_c_text_line_827_text',
    'canvas_editor_tarzanaxissandbox_c_text_line_834_text': 'canvas_editor_tarzanaxissandbox_c_text_line_834_text',
    'canvas_editor_tarzanaxissandbox_c_text_line_873_text': 'canvas_editor_tarzanaxissandbox_c_text_line_873_text',
    'canvas_editor_tarzanaxissandbox_c_text_line_874_text': 'canvas_editor_tarzanaxissandbox_c_text_line_874_text',
    'canvas_editor_tarzanaxissandbox_c_text_line_901_text': 'canvas_editor_tarzanaxissandbox_c_text_line_901_text',
    'canvas_editor_tarzanaxissandbox_c_text_line_902_text': 'canvas_editor_tarzanaxissandbox_c_text_line_902_text',
    'canvas_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': 'canvas_editor_tarzanehrtakesandbox_canvas_image_line_553_coords',
    'canvas_editor_tarzanehrtakesandbox_item_text': 'canvas_editor_tarzanehrtakesandbox_item_text',
    'canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': 'canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords',
    'canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': 'canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords',
    'canvas_editor_tarzanehrtakesandbox_protocol_title_id_text': 'canvas_editor_tarzanehrtakesandbox_protocol_title_id_text',
    'canvas_editor_tarzanehrtakesandbox_row_window_coords': 'canvas_editor_tarzanehrtakesandbox_row_window_coords',
    'canvas_editor_tarzanehrtakesandbox_save_button_window_coords': 'canvas_editor_tarzanehrtakesandbox_save_button_window_coords',
    'canvas_editor_tarzankhr_c_image_line_1518_coords': 'canvas_editor_tarzankhr_c_image_line_1518_coords',
    'canvas_editor_tarzankhr_c_image_line_1533_coords': 'canvas_editor_tarzankhr_c_image_line_1533_coords',
    'canvas_editor_tarzankhr_c_image_line_623_coords': 'canvas_editor_tarzankhr_c_image_line_623_coords',
    'canvas_editor_tarzankhr_c_line_line_1545_coords': 'canvas_editor_tarzankhr_c_line_line_1545_coords',
    'canvas_editor_tarzankhr_c_line_line_1546_coords': 'canvas_editor_tarzankhr_c_line_line_1546_coords',
    'canvas_editor_tarzankhr_c_line_line_1555_coords': 'canvas_editor_tarzankhr_c_line_line_1555_coords',
    'canvas_editor_tarzankhr_c_line_line_1570_coords': 'canvas_editor_tarzankhr_c_line_line_1570_coords',
    'canvas_editor_tarzankhr_c_line_line_1571_coords': 'canvas_editor_tarzankhr_c_line_line_1571_coords',
    'canvas_editor_tarzankhr_c_line_line_1593_coords': 'canvas_editor_tarzankhr_c_line_line_1593_coords',
    'canvas_editor_tarzankhr_c_line_line_1597_coords': 'canvas_editor_tarzankhr_c_line_line_1597_coords',
    'canvas_editor_tarzankhr_c_oval_line_1589_coords': 'canvas_editor_tarzankhr_c_oval_line_1589_coords',
    'canvas_editor_tarzankhr_c_oval_line_1590_coords': 'canvas_editor_tarzankhr_c_oval_line_1590_coords',
    'canvas_editor_tarzankhr_c_polygon_line_1553_coords': 'canvas_editor_tarzankhr_c_polygon_line_1553_coords',
    'canvas_editor_tarzankhr_c_polygon_line_1602_coords': 'canvas_editor_tarzankhr_c_polygon_line_1602_coords',
    'canvas_editor_tarzankhr_c_rectangle_line_1548_coords': 'canvas_editor_tarzankhr_c_rectangle_line_1548_coords',
    'canvas_editor_tarzankhr_c_rectangle_line_1573_coords': 'canvas_editor_tarzankhr_c_rectangle_line_1573_coords',
    'canvas_editor_tarzankhr_c_text_line_1457_text': 'canvas_editor_tarzankhr_c_text_line_1457_text',
    'canvas_editor_tarzankhr_c_text_line_1465_text': 'canvas_editor_tarzankhr_c_text_line_1465_text',
    'canvas_editor_tarzankhr_c_text_line_1472_text': 'canvas_editor_tarzankhr_c_text_line_1472_text',
    'canvas_editor_tarzankhr_c_text_line_1473_text': 'canvas_editor_tarzankhr_c_text_line_1473_text',
    'canvas_editor_tarzankhr_c_text_line_1474_text': 'canvas_editor_tarzankhr_c_text_line_1474_text',
    'canvas_editor_tarzankhr_c_text_line_1481_text': 'canvas_editor_tarzankhr_c_text_line_1481_text',
    'canvas_editor_tarzankhr_c_text_line_1486_text': 'canvas_editor_tarzankhr_c_text_line_1486_text',
    'canvas_editor_tarzankhr_c_text_line_1496_text': 'canvas_editor_tarzankhr_c_text_line_1496_text',
    'canvas_editor_tarzankhr_c_text_line_1503_text': 'canvas_editor_tarzankhr_c_text_line_1503_text',
    'canvas_editor_tarzankhr_c_text_line_1520_text': 'canvas_editor_tarzankhr_c_text_line_1520_text',
    'canvas_editor_tarzankhr_c_text_line_1522_text': 'canvas_editor_tarzankhr_c_text_line_1522_text',
    'canvas_editor_tarzankhr_c_text_line_1525_text': 'canvas_editor_tarzankhr_c_text_line_1525_text',
    'canvas_editor_tarzankhr_c_text_line_1542_text': 'canvas_editor_tarzankhr_c_text_line_1542_text',
    'canvas_editor_tarzankhr_c_text_line_1549_text': 'canvas_editor_tarzankhr_c_text_line_1549_text',
    'canvas_editor_tarzankhr_c_text_line_1554_text': 'canvas_editor_tarzankhr_c_text_line_1554_text',
    'canvas_editor_tarzankhr_c_text_line_1556_text': 'canvas_editor_tarzankhr_c_text_line_1556_text',
    'canvas_editor_tarzankhr_c_text_line_1564_text': 'canvas_editor_tarzankhr_c_text_line_1564_text',
    'canvas_editor_tarzankhr_c_text_line_1569_text': 'canvas_editor_tarzankhr_c_text_line_1569_text',
    'canvas_editor_tarzankhr_c_text_line_1574_text': 'canvas_editor_tarzankhr_c_text_line_1574_text',
    'canvas_editor_tarzankhr_c_text_line_1576_text': 'canvas_editor_tarzankhr_c_text_line_1576_text',
    'canvas_editor_tarzankhr_c_text_line_1578_text': 'canvas_editor_tarzankhr_c_text_line_1578_text',
    'canvas_editor_tarzankhr_c_text_line_1579_text': 'canvas_editor_tarzankhr_c_text_line_1579_text',
    'canvas_editor_tarzankhr_c_text_line_1580_text': 'canvas_editor_tarzankhr_c_text_line_1580_text',
    'canvas_editor_tarzankhr_c_text_line_1603_text': 'canvas_editor_tarzankhr_c_text_line_1603_text',
    'canvas_editor_tarzankhr_c_text_line_1604_text': 'canvas_editor_tarzankhr_c_text_line_1604_text',
    'canvas_editor_tarzankhr_c_text_line_1605_text': 'canvas_editor_tarzankhr_c_text_line_1605_text',
    'canvas_editor_tarzankhr_c_text_line_615_text': 'canvas_editor_tarzankhr_c_text_line_615_text',
    'canvas_editor_tarzankhr_c_text_line_625_text': 'canvas_editor_tarzankhr_c_text_line_625_text',
    'canvas_editor_tarzankhr_c_text_line_627_text': 'canvas_editor_tarzankhr_c_text_line_627_text',
    'canvas_editor_tarzankhr_c_text_line_629_text': 'canvas_editor_tarzankhr_c_text_line_629_text',
    'canvas_editor_tarzantakeprotocollight_canvas_image_line_860_coords': 'canvas_editor_tarzantakeprotocollight_canvas_image_line_860_coords',
    'canvas_editor_tarzantakeprotocollight_item_text': 'canvas_editor_tarzantakeprotocollight_item_text',
    'canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': 'canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords',
    'canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': 'canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords',
    'canvas_editor_tarzantakeprotocollight_protocol_title_id_text': 'canvas_editor_tarzantakeprotocollight_protocol_title_id_text',
    'canvas_editor_tarzantakeprotocollight_row_window_coords': 'canvas_editor_tarzantakeprotocollight_row_window_coords',
    'canvas_editor_tarzantakeprotocollight_save_button_window_coords': 'canvas_editor_tarzantakeprotocollight_save_button_window_coords',
    'canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_305_coords': 'canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_305_coords',
    'canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_313_coords': 'canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_313_coords',
    'canvas_mechanics_tarzanedytorchoreografiiruchu_c_text_line_314_text': 'canvas_mechanics_tarzanedytorchoreografiiruchu_c_text_line_314_text',
    'canvas_mechanics_tarzanedytorchoreografiiruchu_scroll_window_coords': 'canvas_mechanics_tarzanedytorchoreografiiruchu_scroll_window_coords',
    'canvas_mechanics_tarzanwykresosi_c_line_line_1011_coords': 'canvas_mechanics_tarzanwykresosi_c_line_line_1011_coords',
    'canvas_mechanics_tarzanwykresosi_c_line_line_1012_coords': 'canvas_mechanics_tarzanwykresosi_c_line_line_1012_coords',
    'canvas_mechanics_tarzanwykresosi_c_line_line_754_coords': 'canvas_mechanics_tarzanwykresosi_c_line_line_754_coords',
    'canvas_mechanics_tarzanwykresosi_c_line_line_756_coords': 'canvas_mechanics_tarzanwykresosi_c_line_line_756_coords',
    'canvas_mechanics_tarzanwykresosi_c_line_line_757_coords': 'canvas_mechanics_tarzanwykresosi_c_line_line_757_coords',
    'canvas_mechanics_tarzanwykresosi_c_line_line_770_coords': 'canvas_mechanics_tarzanwykresosi_c_line_line_770_coords',
    'canvas_mechanics_tarzanwykresosi_c_oval_line_777_coords': 'canvas_mechanics_tarzanwykresosi_c_oval_line_777_coords',
    'canvas_mechanics_tarzanwykresosi_c_polygon_line_1013_coords': 'canvas_mechanics_tarzanwykresosi_c_polygon_line_1013_coords',
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_723_coords': 'canvas_mechanics_tarzanwykresosi_c_rectangle_line_723_coords',
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_732_coords': 'canvas_mechanics_tarzanwykresosi_c_rectangle_line_732_coords',
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_734_coords': 'canvas_mechanics_tarzanwykresosi_c_rectangle_line_734_coords',
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_751_coords': 'canvas_mechanics_tarzanwykresosi_c_rectangle_line_751_coords',
    'canvas_mechanics_tarzanwykresosi_c_text_line_1014_text': 'canvas_mechanics_tarzanwykresosi_c_text_line_1014_text',
    'canvas_mechanics_tarzanwykresosi_c_text_line_731_text': 'canvas_mechanics_tarzanwykresosi_c_text_line_731_text',
    'canvas_mechanics_tarzanwykresosi_c_text_line_735_text': 'canvas_mechanics_tarzanwykresosi_c_text_line_735_text',
    'canvas_mechanics_tarzanwykresosi_c_text_line_758_text': 'canvas_mechanics_tarzanwykresosi_c_text_line_758_text',
    'canvas_mechanics_tarzanwykresosi_c_text_line_759_text': 'canvas_mechanics_tarzanwykresosi_c_text_line_759_text',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text',
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text': 'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1911_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1911_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1920_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1920_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1953_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1953_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1954_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1954_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1981_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1981_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1982_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1982_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2720_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2720_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2727_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2727_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2736_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2736_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2809_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2809_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2816_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2816_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_item_text': 'canvas_modes_editor_editor_ehr_tarzanehrui_item_text',
    'canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_row_window_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_row_window_coords',
    'canvas_modes_editor_editor_ehr_tarzanehrui_save_button_window_coords': 'canvas_modes_editor_editor_ehr_tarzanehrui_save_button_window_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_826_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_826_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_833_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_833_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_852_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_852_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_859_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_859_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_871_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_871_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_872_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_872_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_886_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_886_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_898_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_898_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_900_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_900_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_oval_line_868_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_oval_line_868_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords': 'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_827_text': 'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_827_text',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_834_text': 'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_834_text',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_873_text': 'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_873_text',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_874_text': 'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_874_text',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_901_text': 'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_901_text',
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_902_text': 'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_902_text',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': 'canvas_modes_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_item_text': 'canvas_modes_editor_editor_tarzanehrtakesandbox_item_text',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': 'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': 'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_title_id_text': 'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_title_id_text',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_row_window_coords': 'canvas_modes_editor_editor_tarzanehrtakesandbox_row_window_coords',
    'canvas_modes_editor_editor_tarzanehrtakesandbox_save_button_window_coords': 'canvas_modes_editor_editor_tarzanehrtakesandbox_save_button_window_coords',
    'canvas_modes_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords': 'canvas_modes_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords',
    'canvas_modes_editor_editor_tarzantakeprotocollight_item_text': 'canvas_modes_editor_editor_tarzantakeprotocollight_item_text',
    'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': 'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords',
    'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': 'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords',
    'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_title_id_text': 'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_title_id_text',
    'canvas_modes_editor_editor_tarzantakeprotocollight_row_window_coords': 'canvas_modes_editor_editor_tarzantakeprotocollight_row_window_coords',
    'canvas_modes_editor_editor_tarzantakeprotocollight_save_button_window_coords': 'canvas_modes_editor_editor_tarzantakeprotocollight_save_button_window_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_827_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_827_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_834_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_834_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_841_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_841_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_853_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_854_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_854_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_868_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_868_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_880_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_880_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_882_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_882_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_828_text': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_828_text',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_835_text': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_835_text',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_855_text': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_855_text',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_856_text': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_856_text',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_883_text': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_883_text',
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_884_text': 'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_884_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_image_line_3130_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_image_line_3130_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_1993_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_1993_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2002_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2002_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2013_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2013_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2020_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2020_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2048_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2048_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2049_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2049_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2068_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2068_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2080_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2080_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2082_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2082_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3081_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3081_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3102_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3102_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3105_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3105_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3145_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3145_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3153_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3153_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3161_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3161_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3176_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3176_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3217_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3217_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3231_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3231_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_2044_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_2044_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3194_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3194_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3210_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3210_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_polygon_line_3226_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_polygon_line_3226_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords': 'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_1994_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_1994_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2003_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2003_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2050_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2050_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2051_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2051_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2083_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2083_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2084_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2084_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3115_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3115_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3122_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3122_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3132_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3132_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3228_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3228_text',
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3239_text': 'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3239_text',
    'canvas_modes_editor_ehr_tarzanehrui_canvas_image_line_760_coords': 'canvas_modes_editor_ehr_tarzanehrui_canvas_image_line_760_coords',
    'canvas_modes_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords': 'canvas_modes_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords',
    'canvas_modes_editor_ehr_tarzanehrui_canvas_window_line_1226_coords': 'canvas_modes_editor_ehr_tarzanehrui_canvas_window_line_1226_coords',
    'canvas_modes_editor_ehr_tarzanehrui_item_text': 'canvas_modes_editor_ehr_tarzanehrui_item_text',
    'canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords': 'canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords',
    'canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords': 'canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords',
    'canvas_modes_editor_ehr_tarzanehrui_row_window_coords': 'canvas_modes_editor_ehr_tarzanehrui_row_window_coords',
    'canvas_modes_editor_ehr_tarzanehrui_save_button_window_coords': 'canvas_modes_editor_ehr_tarzanehrui_save_button_window_coords',
    'canvas_modes_editor_par_tarzannextionpreview_edit_window_coords': 'canvas_modes_editor_par_tarzannextionpreview_edit_window_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text',
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text': 'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text',
    'canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1309_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1309_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1402_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1402_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords': 'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords',
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1310_text': 'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1310_text',
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1434_text': 'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1434_text',
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1451_text': 'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1451_text',
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1455_text': 'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1455_text',
    'canvas_modes_editor_par_tarzanparapp_led_oval_line_485_coords': 'canvas_modes_editor_par_tarzanparapp_led_oval_line_485_coords',
    'canvas_modes_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords': 'canvas_modes_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords',
    'canvas_modes_editor_par_tarzanparapp_text_id_text': 'canvas_modes_editor_par_tarzanparapp_text_id_text',
    'canvas_modes_editor_par_tarzanparpanels_can_image_line_1306_coords': 'canvas_modes_editor_par_tarzanparpanels_can_image_line_1306_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1298_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_1298_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1299_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_1299_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1304_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_1304_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1311_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_1311_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1326_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_1326_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1327_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_1327_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_510_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_510_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_664_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_664_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_665_coords': 'canvas_modes_editor_par_tarzanparpanels_can_line_line_665_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_509_coords': 'canvas_modes_editor_par_tarzanparpanels_can_oval_line_509_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_511_coords': 'canvas_modes_editor_par_tarzanparpanels_can_oval_line_511_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_656_coords': 'canvas_modes_editor_par_tarzanparpanels_can_oval_line_656_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_920_coords': 'canvas_modes_editor_par_tarzanparpanels_can_oval_line_920_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_polygon_line_921_coords': 'canvas_modes_editor_par_tarzanparpanels_can_polygon_line_921_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_899_coords': 'canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_899_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_901_coords': 'canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_901_coords',
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1307_text': 'canvas_modes_editor_par_tarzanparpanels_can_text_line_1307_text',
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1309_text': 'canvas_modes_editor_par_tarzanparpanels_can_text_line_1309_text',
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1310_text': 'canvas_modes_editor_par_tarzanparpanels_can_text_line_1310_text',
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1329_text': 'canvas_modes_editor_par_tarzanparpanels_can_text_line_1329_text',
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1331_text': 'canvas_modes_editor_par_tarzanparpanels_can_text_line_1331_text',
    'canvas_modes_editor_par_tarzanparpanels_canvas_line_line_825_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_line_line_825_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_line_line_826_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_line_line_826_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_1575_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_1575_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_830_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_830_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_polygon_line_828_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_polygon_line_828_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords',
    'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords': 'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3118_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3118_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3119_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3119_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1979_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1979_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1980_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1980_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_2212_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_2212_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_3111_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_3111_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_344_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_344_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords': 'canvas_modes_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_767_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_767_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_780_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_780_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_781_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_781_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_784_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_784_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1551_text': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1551_text',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1554_text': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1554_text',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1555_text': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1555_text',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1586_text': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1586_text',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_766_text': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_766_text',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_785_text': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_785_text',
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_window_line_119_coords': 'canvas_modes_editor_par_tarzanparpanels_old_canvas_window_line_119_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_dot_oval_line_378_coords': 'canvas_modes_editor_par_tarzanparpanels_old_dot_oval_line_378_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1049_coords': 'canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1049_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1050_coords': 'canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1050_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_rect_coords': 'canvas_modes_editor_par_tarzanparpanels_old_rect_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords': 'canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords': 'canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords',
    'canvas_modes_editor_par_tarzanparpanels_old_window_id_coords': 'canvas_modes_editor_par_tarzanparpanels_old_window_id_coords',
    'canvas_modes_editor_par_tarzanparpanels_self_rectangle_line_185_coords': 'canvas_modes_editor_par_tarzanparpanels_self_rectangle_line_185_coords',
    'canvas_modes_editor_par_tarzanparpanels_window_id_coords': 'canvas_modes_editor_par_tarzanparpanels_window_id_coords',
    'canvas_modes_editor_par_tarzanparwidgets_c_line_line_304_coords': 'canvas_modes_editor_par_tarzanparwidgets_c_line_line_304_coords',
    'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_299_coords': 'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_299_coords',
    'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_300_coords': 'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_300_coords',
    'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_305_coords': 'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_305_coords',
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_59_coords': 'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_59_coords',
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_60_coords': 'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_60_coords',
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_64_coords': 'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_64_coords',
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_65_coords': 'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_65_coords',
    'canvas_modes_editor_par_tarzanparwidgets_self_rectangle_line_90_coords': 'canvas_modes_editor_par_tarzanparwidgets_self_rectangle_line_90_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_826_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_826_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_833_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_833_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_852_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_852_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_859_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_859_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_871_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_871_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_872_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_872_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_886_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_886_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_898_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_898_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_900_coords': 'canvas_modes_editor_tarzanaxissandbox_c_line_line_900_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_oval_line_868_coords': 'canvas_modes_editor_tarzanaxissandbox_c_oval_line_868_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_812_coords': 'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_812_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_819_coords': 'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_819_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_820_coords': 'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_820_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_821_coords': 'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_821_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_880_coords': 'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_880_coords',
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_827_text': 'canvas_modes_editor_tarzanaxissandbox_c_text_line_827_text',
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_834_text': 'canvas_modes_editor_tarzanaxissandbox_c_text_line_834_text',
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_873_text': 'canvas_modes_editor_tarzanaxissandbox_c_text_line_873_text',
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_874_text': 'canvas_modes_editor_tarzanaxissandbox_c_text_line_874_text',
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_901_text': 'canvas_modes_editor_tarzanaxissandbox_c_text_line_901_text',
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_902_text': 'canvas_modes_editor_tarzanaxissandbox_c_text_line_902_text',
    'canvas_modes_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': 'canvas_modes_editor_tarzanehrtakesandbox_canvas_image_line_553_coords',
    'canvas_modes_editor_tarzanehrtakesandbox_item_text': 'canvas_modes_editor_tarzanehrtakesandbox_item_text',
    'canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': 'canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords',
    'canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': 'canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords',
    'canvas_modes_editor_tarzanehrtakesandbox_protocol_title_id_text': 'canvas_modes_editor_tarzanehrtakesandbox_protocol_title_id_text',
    'canvas_modes_editor_tarzanehrtakesandbox_row_window_coords': 'canvas_modes_editor_tarzanehrtakesandbox_row_window_coords',
    'canvas_modes_editor_tarzanehrtakesandbox_save_button_window_coords': 'canvas_modes_editor_tarzanehrtakesandbox_save_button_window_coords',
    'canvas_modes_editor_tarzankhr_c_image_line_1518_coords': 'canvas_modes_editor_tarzankhr_c_image_line_1518_coords',
    'canvas_modes_editor_tarzankhr_c_image_line_1533_coords': 'canvas_modes_editor_tarzankhr_c_image_line_1533_coords',
    'canvas_modes_editor_tarzankhr_c_image_line_623_coords': 'canvas_modes_editor_tarzankhr_c_image_line_623_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1545_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1545_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1546_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1546_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1555_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1555_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1570_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1570_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1571_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1571_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1593_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1593_coords',
    'canvas_modes_editor_tarzankhr_c_line_line_1597_coords': 'canvas_modes_editor_tarzankhr_c_line_line_1597_coords',
    'canvas_modes_editor_tarzankhr_c_oval_line_1589_coords': 'canvas_modes_editor_tarzankhr_c_oval_line_1589_coords',
    'canvas_modes_editor_tarzankhr_c_oval_line_1590_coords': 'canvas_modes_editor_tarzankhr_c_oval_line_1590_coords',
    'canvas_modes_editor_tarzankhr_c_polygon_line_1553_coords': 'canvas_modes_editor_tarzankhr_c_polygon_line_1553_coords',
    'canvas_modes_editor_tarzankhr_c_polygon_line_1602_coords': 'canvas_modes_editor_tarzankhr_c_polygon_line_1602_coords',
    'canvas_modes_editor_tarzankhr_c_rectangle_line_1548_coords': 'canvas_modes_editor_tarzankhr_c_rectangle_line_1548_coords',
    'canvas_modes_editor_tarzankhr_c_rectangle_line_1573_coords': 'canvas_modes_editor_tarzankhr_c_rectangle_line_1573_coords',
    'canvas_modes_editor_tarzankhr_c_text_line_1457_text': 'canvas_modes_editor_tarzankhr_c_text_line_1457_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1465_text': 'canvas_modes_editor_tarzankhr_c_text_line_1465_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1472_text': 'canvas_modes_editor_tarzankhr_c_text_line_1472_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1473_text': 'canvas_modes_editor_tarzankhr_c_text_line_1473_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1474_text': 'canvas_modes_editor_tarzankhr_c_text_line_1474_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1481_text': 'canvas_modes_editor_tarzankhr_c_text_line_1481_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1486_text': 'canvas_modes_editor_tarzankhr_c_text_line_1486_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1496_text': 'canvas_modes_editor_tarzankhr_c_text_line_1496_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1503_text': 'canvas_modes_editor_tarzankhr_c_text_line_1503_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1520_text': 'canvas_modes_editor_tarzankhr_c_text_line_1520_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1522_text': 'canvas_modes_editor_tarzankhr_c_text_line_1522_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1525_text': 'canvas_modes_editor_tarzankhr_c_text_line_1525_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1542_text': 'canvas_modes_editor_tarzankhr_c_text_line_1542_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1549_text': 'canvas_modes_editor_tarzankhr_c_text_line_1549_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1554_text': 'canvas_modes_editor_tarzankhr_c_text_line_1554_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1556_text': 'canvas_modes_editor_tarzankhr_c_text_line_1556_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1564_text': 'canvas_modes_editor_tarzankhr_c_text_line_1564_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1569_text': 'canvas_modes_editor_tarzankhr_c_text_line_1569_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1574_text': 'canvas_modes_editor_tarzankhr_c_text_line_1574_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1576_text': 'canvas_modes_editor_tarzankhr_c_text_line_1576_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1578_text': 'canvas_modes_editor_tarzankhr_c_text_line_1578_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1579_text': 'canvas_modes_editor_tarzankhr_c_text_line_1579_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1580_text': 'canvas_modes_editor_tarzankhr_c_text_line_1580_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1603_text': 'canvas_modes_editor_tarzankhr_c_text_line_1603_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1604_text': 'canvas_modes_editor_tarzankhr_c_text_line_1604_text',
    'canvas_modes_editor_tarzankhr_c_text_line_1605_text': 'canvas_modes_editor_tarzankhr_c_text_line_1605_text',
    'canvas_modes_editor_tarzankhr_c_text_line_615_text': 'canvas_modes_editor_tarzankhr_c_text_line_615_text',
    'canvas_modes_editor_tarzankhr_c_text_line_625_text': 'canvas_modes_editor_tarzankhr_c_text_line_625_text',
    'canvas_modes_editor_tarzankhr_c_text_line_627_text': 'canvas_modes_editor_tarzankhr_c_text_line_627_text',
    'canvas_modes_editor_tarzankhr_c_text_line_629_text': 'canvas_modes_editor_tarzankhr_c_text_line_629_text',
    'canvas_modes_editor_tarzantakeprotocollight_canvas_image_line_860_coords': 'canvas_modes_editor_tarzantakeprotocollight_canvas_image_line_860_coords',
    'canvas_modes_editor_tarzantakeprotocollight_item_text': 'canvas_modes_editor_tarzantakeprotocollight_item_text',
    'canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': 'canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords',
    'canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': 'canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords',
    'canvas_modes_editor_tarzantakeprotocollight_protocol_title_id_text': 'canvas_modes_editor_tarzantakeprotocollight_protocol_title_id_text',
    'canvas_modes_editor_tarzantakeprotocollight_row_window_coords': 'canvas_modes_editor_tarzantakeprotocollight_row_window_coords',
    'canvas_modes_editor_tarzantakeprotocollight_save_button_window_coords': 'canvas_modes_editor_tarzantakeprotocollight_save_button_window_coords',
    'canvas_vision_tarzanvisionsetup_window_id_coords': 'canvas_vision_tarzanvisionsetup_window_id_coords',
}


# =============================================================================
# PEŁNA MAPA CELÓW
# =============================================================================

# =============================================================================
# PEŁNA MAPA CELÓW — UPORZĄDKOWANA, BEZ USUWANIA
# =============================================================================

# UWAGA:
# - cele strategiczne i pełny skan techniczny zostają w jednym miejscu
# - nie usunięto celów z numerami linii; zostały przeniesione do sekcji skanów
# - późniejsze wdrożenie może ładować tylko strategiczne grupy, ale ten plik zachowuje wszystko

DEFAULT_TARZAN_SNAJPER_TARGETS: Dict[str, List[TarzanSnajperTarget]] = {

    # -------------------------------------------------------------------------
    # 01_RRP_PAR_NEXTION: RRP / PAR / Nextion — strategiczne sterowanie ręczne
    # -------------------------------------------------------------------------
    'rrp_p1_dir': [
        T('physical_nextion', 'rrp_main', 'b_p1_dir', 'val'),
        T('physical_nextion', 'rrp_main', 'va_p1_dir', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_dir', 'val'),
        T('par_tkinter', 'par_rrp', 'p1_dir_widget', 'state'),
    ],
    'rrp_p1_sens': [
        T('physical_nextion', 'rrp_main', 'h_p1_sens', 'val'),
        T('canvas_preview', 'rrp_main', 'h_p1_sens', 'val'),
        T('par_tkinter', 'par_rrp', 'p1_sens_slider', 'value'),
    ],
    'rrp_p1_value': [
        T('physical_nextion', 'rrp_main', 't_p1_val', 'txt'),
        T('canvas_preview', 'rrp_main', 't_p1_val', 'txt'),
        T('par_tkinter', 'par_rrp', 'p1_value_label', 'text'),
    ],
    'rrp_p2_dir': [
        T('physical_nextion', 'rrp_main', 'b_p2_dir', 'val'),
        T('physical_nextion', 'rrp_main', 'va_p2_dir', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_dir', 'val'),
        T('par_tkinter', 'par_rrp', 'p2_dir_widget', 'state'),
    ],
    'rrp_p2_sens': [
        T('physical_nextion', 'rrp_main', 'h_p2_sens', 'val'),
        T('canvas_preview', 'rrp_main', 'h_p2_sens', 'val'),
        T('par_tkinter', 'par_rrp', 'p2_sens_slider', 'value'),
    ],
    'rrp_p2_value': [
        T('physical_nextion', 'rrp_main', 't_p2_val', 'txt'),
        T('canvas_preview', 'rrp_main', 't_p2_val', 'txt'),
        T('par_tkinter', 'par_rrp', 'p2_value_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 02_TAKE_TFD: TAKE / TFD — timecode, clap, status ujęcia
    # -------------------------------------------------------------------------
    'take_timecode': [
        T('physical_nextion', 'take_main', 't0', 'txt'),
        T('canvas_preview', 'take_main', 't0', 'txt'),
        T('par_tkinter', 'take_panel', 'timecode_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 03_OSIE: Osie — wartości i liczniki osi
    # -------------------------------------------------------------------------
    'axis_0_value': [
        T('physical_nextion', 'take_main', 't_axis0', 'txt'),
        T('canvas_preview', 'take_main', 't_axis0', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_0_value_label', 'text'),
    ],
    'axis_1_value': [
        T('physical_nextion', 'take_main', 't_axis1', 'txt'),
        T('canvas_preview', 'take_main', 't_axis1', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_1_value_label', 'text'),
    ],
    'axis_2_value': [
        T('physical_nextion', 'take_main', 't_axis2', 'txt'),
        T('canvas_preview', 'take_main', 't_axis2', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_2_value_label', 'text'),
    ],
    'axis_3_value': [
        T('physical_nextion', 'take_main', 't_axis3', 'txt'),
        T('canvas_preview', 'take_main', 't_axis3', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_3_value_label', 'text'),
    ],
    'axis_4_value': [
        T('physical_nextion', 'take_main', 't_axis4', 'txt'),
        T('canvas_preview', 'take_main', 't_axis4', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_4_value_label', 'text'),
    ],
    'axis_5_value': [
        T('physical_nextion', 'take_main', 't_axis5', 'txt'),
        T('canvas_preview', 'take_main', 't_axis5', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_5_value_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 04_SENSORY_STATUS: Sensory / statusy / poziomica
    # -------------------------------------------------------------------------
    'level_x': [
        T('physical_nextion', 'level_xyz', 'va0', 'val'),
        T('canvas_preview', 'level_xyz', 'va0', 'val'),
        T('par_tkinter', 'sensors_panel', 'level_x_label', 'text'),
    ],
    'level_y': [
        T('physical_nextion', 'level_xyz', 'va1', 'val'),
        T('canvas_preview', 'level_xyz', 'va1', 'val'),
        T('par_tkinter', 'sensors_panel', 'level_y_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 05_NEXTION_SETTINGS_UI_CUT: Nextion settings / UI CUT
    # -------------------------------------------------------------------------
    'nextion_ui_cut': [
        T('physical_nextion', 'settings_main', 'b_ui_cut', 'val'),
        T('par_tkinter', 'nextion_panel', 'ui_cut_status_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 06_EHR: EHR — krzywe, STEP preview, metryki, TAKE slots
    # -------------------------------------------------------------------------
    'ehr_axis_0_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_0_curve', 'coords'),
    ],
    'ehr_axis_0_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_0_metrics', 'text'),
    ],
    'ehr_axis_0_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_0_step_bars', 'coords'),
    ],
    'ehr_axis_1_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_1_curve', 'coords'),
    ],
    'ehr_axis_1_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_1_metrics', 'text'),
    ],
    'ehr_axis_1_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_1_step_bars', 'coords'),
    ],
    'ehr_axis_2_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_2_curve', 'coords'),
    ],
    'ehr_axis_2_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_2_metrics', 'text'),
    ],
    'ehr_axis_2_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_2_step_bars', 'coords'),
    ],
    'ehr_axis_3_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_3_curve', 'coords'),
    ],
    'ehr_axis_3_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_3_metrics', 'text'),
    ],
    'ehr_axis_3_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_3_step_bars', 'coords'),
    ],
    'ehr_axis_4_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_4_curve', 'coords'),
    ],
    'ehr_axis_4_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_4_metrics', 'text'),
    ],
    'ehr_axis_4_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_4_step_bars', 'coords'),
    ],
    'ehr_axis_5_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_5_curve', 'coords'),
    ],
    'ehr_axis_5_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_5_metrics', 'text'),
    ],
    'ehr_axis_5_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_5_step_bars', 'coords'),
    ],
    'ehr_take_slot_0_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_0', 'state'),
    ],
    'ehr_take_slot_1_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_1', 'state'),
    ],
    'ehr_take_slot_2_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_2', 'state'),
    ],
    'ehr_take_slot_3_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_3', 'state'),
    ],
    'ehr_take_slot_4_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_4', 'state'),
    ],
    'ehr_take_slot_5_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_5', 'state'),
    ],
    'ehr_take_slot_6_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_6', 'state'),
    ],
    'ehr_take_slot_7_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_7', 'state'),
    ],

    # -------------------------------------------------------------------------
    # 07_SANDBOX: Sandbox osi
    # -------------------------------------------------------------------------
    'sandbox_curve': [
        T('sandbox_canvas', 'sandbox', 'curve', 'coords'),
    ],
    'sandbox_metrics': [
        T('sandbox_tkinter', 'sandbox', 'metrics_label', 'text'),
    ],
    'sandbox_step_preview': [
        T('sandbox_canvas', 'sandbox', 'step_bars', 'coords'),
    ],

    # -------------------------------------------------------------------------
    # 08_TIMELINE: Timeline — cursor i markery
    # -------------------------------------------------------------------------
    'timeline_clap_marker': [
        T('timeline_canvas', 'par_timeline', 'clap_marker', 'coords'),
    ],
    'timeline_cursor': [
        T('timeline_canvas', 'par_timeline', 'cursor', 'coords'),
    ],
    'timeline_take_marker': [
        T('timeline_canvas', 'par_timeline', 'take_marker', 'coords'),
    ],

    # -------------------------------------------------------------------------
    # 09_LAYOUT_DESIGNER: Layout designer
    # -------------------------------------------------------------------------
    'layout_panel_status': [
        T('layout_canvas', 'par_layout', 'panel_status', 'text'),
    ],
    'layout_selected_cell': [
        T('layout_canvas', 'par_layout', 'selected_cell', 'coords'),
    ],
    'layout_zone_label': [
        T('layout_canvas', 'par_layout', 'zone_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 10_KHR: KHR — markery i status
    # -------------------------------------------------------------------------
    'khr_input_marker': [
        T('khr_canvas', 'khr_input', 'marker', 'coords'),
    ],
    'khr_output_marker': [
        T('khr_canvas', 'khr_output', 'marker', 'coords'),
    ],
    'khr_status': [
        T('khr_tkinter', 'khr', 'status_label', 'text'),
    ],

    # -------------------------------------------------------------------------
    # 11_NEXTION_HMI_KOMPONENTY: Pełny katalog komponentów HMI Nextion
    # -------------------------------------------------------------------------
    'nextion_boot_event_en': [
        T('physical_nextion', 'boot', 'Event', 'en'),
        T('canvas_preview', 'boot', 'Event', 'en'),
    ],
    'nextion_boot_event_tim': [
        T('physical_nextion', 'boot', 'Event', 'tim'),
        T('canvas_preview', 'boot', 'Event', 'tim'),
    ],
    'nextion_boot_p0_pic': [
        T('physical_nextion', 'boot', 'p0', 'pic'),
        T('canvas_preview', 'boot', 'p0', 'pic'),
    ],
    'nextion_boot_tm0_en': [
        T('physical_nextion', 'boot', 'tm0', 'en'),
        T('canvas_preview', 'boot', 'tm0', 'en'),
    ],
    'nextion_boot_tm0_tim': [
        T('physical_nextion', 'boot', 'tm0', 'tim'),
        T('canvas_preview', 'boot', 'tm0', 'tim'),
    ],
    'nextion_boot_va0_val': [
        T('physical_nextion', 'boot', 'va0', 'val'),
        T('canvas_preview', 'boot', 'va0', 'val'),
    ],
    'nextion_face_rec_b_home_pic': [
        T('physical_nextion', 'face_rec', 'b_home', 'pic'),
        T('canvas_preview', 'face_rec', 'b_home', 'pic'),
    ],
    'nextion_face_rec_b_home_val': [
        T('physical_nextion', 'face_rec', 'b_home', 'val'),
        T('canvas_preview', 'face_rec', 'b_home', 'val'),
    ],
    'nextion_face_rec_t0_txt': [
        T('physical_nextion', 'face_rec', 't0', 'txt'),
        T('canvas_preview', 'face_rec', 't0', 'txt'),
    ],
    'nextion_keybda_b0_pic': [
        T('physical_nextion', 'keybdA', 'b0', 'pic'),
        T('canvas_preview', 'keybdA', 'b0', 'pic'),
    ],
    'nextion_keybda_b0_val': [
        T('physical_nextion', 'keybdA', 'b0', 'val'),
        T('canvas_preview', 'keybdA', 'b0', 'val'),
    ],
    'nextion_keybda_b1_pic': [
        T('physical_nextion', 'keybdA', 'b1', 'pic'),
        T('canvas_preview', 'keybdA', 'b1', 'pic'),
    ],
    'nextion_keybda_b1_val': [
        T('physical_nextion', 'keybdA', 'b1', 'val'),
        T('canvas_preview', 'keybdA', 'b1', 'val'),
    ],
    'nextion_keybda_b200_pic': [
        T('physical_nextion', 'keybdA', 'b200', 'pic'),
        T('canvas_preview', 'keybdA', 'b200', 'pic'),
    ],
    'nextion_keybda_b200_val': [
        T('physical_nextion', 'keybdA', 'b200', 'val'),
        T('canvas_preview', 'keybdA', 'b200', 'val'),
    ],
    'nextion_keybda_b201_pic': [
        T('physical_nextion', 'keybdA', 'b201', 'pic'),
        T('canvas_preview', 'keybdA', 'b201', 'pic'),
    ],
    'nextion_keybda_b201_val': [
        T('physical_nextion', 'keybdA', 'b201', 'val'),
        T('canvas_preview', 'keybdA', 'b201', 'val'),
    ],
    'nextion_keybda_b20_pic': [
        T('physical_nextion', 'keybdA', 'b20', 'pic'),
        T('canvas_preview', 'keybdA', 'b20', 'pic'),
    ],
    'nextion_keybda_b20_val': [
        T('physical_nextion', 'keybdA', 'b20', 'val'),
        T('canvas_preview', 'keybdA', 'b20', 'val'),
    ],
    'nextion_keybda_b210_pic': [
        T('physical_nextion', 'keybdA', 'b210', 'pic'),
        T('canvas_preview', 'keybdA', 'b210', 'pic'),
    ],
    'nextion_keybda_b210_val': [
        T('physical_nextion', 'keybdA', 'b210', 'val'),
        T('canvas_preview', 'keybdA', 'b210', 'val'),
    ],
    'nextion_keybda_b21_pic': [
        T('physical_nextion', 'keybdA', 'b21', 'pic'),
        T('canvas_preview', 'keybdA', 'b21', 'pic'),
    ],
    'nextion_keybda_b21_val': [
        T('physical_nextion', 'keybdA', 'b21', 'val'),
        T('canvas_preview', 'keybdA', 'b21', 'val'),
    ],
    'nextion_keybda_b220_pic': [
        T('physical_nextion', 'keybdA', 'b220', 'pic'),
        T('canvas_preview', 'keybdA', 'b220', 'pic'),
    ],
    'nextion_keybda_b220_val': [
        T('physical_nextion', 'keybdA', 'b220', 'val'),
        T('canvas_preview', 'keybdA', 'b220', 'val'),
    ],
    'nextion_keybda_b22_pic': [
        T('physical_nextion', 'keybdA', 'b22', 'pic'),
        T('canvas_preview', 'keybdA', 'b22', 'pic'),
    ],
    'nextion_keybda_b22_val': [
        T('physical_nextion', 'keybdA', 'b22', 'val'),
        T('canvas_preview', 'keybdA', 'b22', 'val'),
    ],
    'nextion_keybda_b230_pic': [
        T('physical_nextion', 'keybdA', 'b230', 'pic'),
        T('canvas_preview', 'keybdA', 'b230', 'pic'),
    ],
    'nextion_keybda_b230_val': [
        T('physical_nextion', 'keybdA', 'b230', 'val'),
        T('canvas_preview', 'keybdA', 'b230', 'val'),
    ],
    'nextion_keybda_b231_pic': [
        T('physical_nextion', 'keybdA', 'b231', 'pic'),
        T('canvas_preview', 'keybdA', 'b231', 'pic'),
    ],
    'nextion_keybda_b231_val': [
        T('physical_nextion', 'keybdA', 'b231', 'val'),
        T('canvas_preview', 'keybdA', 'b231', 'val'),
    ],
    'nextion_keybda_b232_pic': [
        T('physical_nextion', 'keybdA', 'b232', 'pic'),
        T('canvas_preview', 'keybdA', 'b232', 'pic'),
    ],
    'nextion_keybda_b232_val': [
        T('physical_nextion', 'keybdA', 'b232', 'val'),
        T('canvas_preview', 'keybdA', 'b232', 'val'),
    ],
    'nextion_keybda_b23_pic': [
        T('physical_nextion', 'keybdA', 'b23', 'pic'),
        T('canvas_preview', 'keybdA', 'b23', 'pic'),
    ],
    'nextion_keybda_b23_val': [
        T('physical_nextion', 'keybdA', 'b23', 'val'),
        T('canvas_preview', 'keybdA', 'b23', 'val'),
    ],
    'nextion_keybda_b240_pic': [
        T('physical_nextion', 'keybdA', 'b240', 'pic'),
        T('canvas_preview', 'keybdA', 'b240', 'pic'),
    ],
    'nextion_keybda_b240_val': [
        T('physical_nextion', 'keybdA', 'b240', 'val'),
        T('canvas_preview', 'keybdA', 'b240', 'val'),
    ],
    'nextion_keybda_b241_pic': [
        T('physical_nextion', 'keybdA', 'b241', 'pic'),
        T('canvas_preview', 'keybdA', 'b241', 'pic'),
    ],
    'nextion_keybda_b241_val': [
        T('physical_nextion', 'keybdA', 'b241', 'val'),
        T('canvas_preview', 'keybdA', 'b241', 'val'),
    ],
    'nextion_keybda_b242_pic': [
        T('physical_nextion', 'keybdA', 'b242', 'pic'),
        T('canvas_preview', 'keybdA', 'b242', 'pic'),
    ],
    'nextion_keybda_b242_val': [
        T('physical_nextion', 'keybdA', 'b242', 'val'),
        T('canvas_preview', 'keybdA', 'b242', 'val'),
    ],
    'nextion_keybda_b243_pic': [
        T('physical_nextion', 'keybdA', 'b243', 'pic'),
        T('canvas_preview', 'keybdA', 'b243', 'pic'),
    ],
    'nextion_keybda_b243_val': [
        T('physical_nextion', 'keybdA', 'b243', 'val'),
        T('canvas_preview', 'keybdA', 'b243', 'val'),
    ],
    'nextion_keybda_b244_pic': [
        T('physical_nextion', 'keybdA', 'b244', 'pic'),
        T('canvas_preview', 'keybdA', 'b244', 'pic'),
    ],
    'nextion_keybda_b244_val': [
        T('physical_nextion', 'keybdA', 'b244', 'val'),
        T('canvas_preview', 'keybdA', 'b244', 'val'),
    ],
    'nextion_keybda_b249_pic': [
        T('physical_nextion', 'keybdA', 'b249', 'pic'),
        T('canvas_preview', 'keybdA', 'b249', 'pic'),
    ],
    'nextion_keybda_b249_val': [
        T('physical_nextion', 'keybdA', 'b249', 'val'),
        T('canvas_preview', 'keybdA', 'b249', 'val'),
    ],
    'nextion_keybda_b24_pic': [
        T('physical_nextion', 'keybdA', 'b24', 'pic'),
        T('canvas_preview', 'keybdA', 'b24', 'pic'),
    ],
    'nextion_keybda_b24_val': [
        T('physical_nextion', 'keybdA', 'b24', 'val'),
        T('canvas_preview', 'keybdA', 'b24', 'val'),
    ],
    'nextion_keybda_b251_pic': [
        T('physical_nextion', 'keybdA', 'b251', 'pic'),
        T('canvas_preview', 'keybdA', 'b251', 'pic'),
    ],
    'nextion_keybda_b251_val': [
        T('physical_nextion', 'keybdA', 'b251', 'val'),
        T('canvas_preview', 'keybdA', 'b251', 'val'),
    ],
    'nextion_keybda_b25_pic': [
        T('physical_nextion', 'keybdA', 'b25', 'pic'),
        T('canvas_preview', 'keybdA', 'b25', 'pic'),
    ],
    'nextion_keybda_b25_val': [
        T('physical_nextion', 'keybdA', 'b25', 'val'),
        T('canvas_preview', 'keybdA', 'b25', 'val'),
    ],
    'nextion_keybda_b26_pic': [
        T('physical_nextion', 'keybdA', 'b26', 'pic'),
        T('canvas_preview', 'keybdA', 'b26', 'pic'),
    ],
    'nextion_keybda_b26_val': [
        T('physical_nextion', 'keybdA', 'b26', 'val'),
        T('canvas_preview', 'keybdA', 'b26', 'val'),
    ],
    'nextion_keybda_b27_pic': [
        T('physical_nextion', 'keybdA', 'b27', 'pic'),
        T('canvas_preview', 'keybdA', 'b27', 'pic'),
    ],
    'nextion_keybda_b27_val': [
        T('physical_nextion', 'keybdA', 'b27', 'val'),
        T('canvas_preview', 'keybdA', 'b27', 'val'),
    ],
    'nextion_keybda_b28_pic': [
        T('physical_nextion', 'keybdA', 'b28', 'pic'),
        T('canvas_preview', 'keybdA', 'b28', 'pic'),
    ],
    'nextion_keybda_b28_val': [
        T('physical_nextion', 'keybdA', 'b28', 'val'),
        T('canvas_preview', 'keybdA', 'b28', 'val'),
    ],
    'nextion_keybda_b2_pic': [
        T('physical_nextion', 'keybdA', 'b2', 'pic'),
        T('canvas_preview', 'keybdA', 'b2', 'pic'),
    ],
    'nextion_keybda_b2_val': [
        T('physical_nextion', 'keybdA', 'b2', 'val'),
        T('canvas_preview', 'keybdA', 'b2', 'val'),
    ],
    'nextion_keybda_b3_pic': [
        T('physical_nextion', 'keybdA', 'b3', 'pic'),
        T('canvas_preview', 'keybdA', 'b3', 'pic'),
    ],
    'nextion_keybda_b3_val': [
        T('physical_nextion', 'keybdA', 'b3', 'val'),
        T('canvas_preview', 'keybdA', 'b3', 'val'),
    ],
    'nextion_keybda_b40_pic': [
        T('physical_nextion', 'keybdA', 'b40', 'pic'),
        T('canvas_preview', 'keybdA', 'b40', 'pic'),
    ],
    'nextion_keybda_b40_val': [
        T('physical_nextion', 'keybdA', 'b40', 'val'),
        T('canvas_preview', 'keybdA', 'b40', 'val'),
    ],
    'nextion_keybda_b41_pic': [
        T('physical_nextion', 'keybdA', 'b41', 'pic'),
        T('canvas_preview', 'keybdA', 'b41', 'pic'),
    ],
    'nextion_keybda_b41_val': [
        T('physical_nextion', 'keybdA', 'b41', 'val'),
        T('canvas_preview', 'keybdA', 'b41', 'val'),
    ],
    'nextion_keybda_b42_pic': [
        T('physical_nextion', 'keybdA', 'b42', 'pic'),
        T('canvas_preview', 'keybdA', 'b42', 'pic'),
    ],
    'nextion_keybda_b42_val': [
        T('physical_nextion', 'keybdA', 'b42', 'val'),
        T('canvas_preview', 'keybdA', 'b42', 'val'),
    ],
    'nextion_keybda_b43_pic': [
        T('physical_nextion', 'keybdA', 'b43', 'pic'),
        T('canvas_preview', 'keybdA', 'b43', 'pic'),
    ],
    'nextion_keybda_b43_val': [
        T('physical_nextion', 'keybdA', 'b43', 'val'),
        T('canvas_preview', 'keybdA', 'b43', 'val'),
    ],
    'nextion_keybda_b44_pic': [
        T('physical_nextion', 'keybdA', 'b44', 'pic'),
        T('canvas_preview', 'keybdA', 'b44', 'pic'),
    ],
    'nextion_keybda_b44_val': [
        T('physical_nextion', 'keybdA', 'b44', 'val'),
        T('canvas_preview', 'keybdA', 'b44', 'val'),
    ],
    'nextion_keybda_b45_pic': [
        T('physical_nextion', 'keybdA', 'b45', 'pic'),
        T('canvas_preview', 'keybdA', 'b45', 'pic'),
    ],
    'nextion_keybda_b45_val': [
        T('physical_nextion', 'keybdA', 'b45', 'val'),
        T('canvas_preview', 'keybdA', 'b45', 'val'),
    ],
    'nextion_keybda_b46_pic': [
        T('physical_nextion', 'keybdA', 'b46', 'pic'),
        T('canvas_preview', 'keybdA', 'b46', 'pic'),
    ],
    'nextion_keybda_b46_val': [
        T('physical_nextion', 'keybdA', 'b46', 'val'),
        T('canvas_preview', 'keybdA', 'b46', 'val'),
    ],
    'nextion_keybda_b4_pic': [
        T('physical_nextion', 'keybdA', 'b4', 'pic'),
        T('canvas_preview', 'keybdA', 'b4', 'pic'),
    ],
    'nextion_keybda_b4_val': [
        T('physical_nextion', 'keybdA', 'b4', 'val'),
        T('canvas_preview', 'keybdA', 'b4', 'val'),
    ],
    'nextion_keybda_b5_pic': [
        T('physical_nextion', 'keybdA', 'b5', 'pic'),
        T('canvas_preview', 'keybdA', 'b5', 'pic'),
    ],
    'nextion_keybda_b5_val': [
        T('physical_nextion', 'keybdA', 'b5', 'val'),
        T('canvas_preview', 'keybdA', 'b5', 'val'),
    ],
    'nextion_keybda_b6_pic': [
        T('physical_nextion', 'keybdA', 'b6', 'pic'),
        T('canvas_preview', 'keybdA', 'b6', 'pic'),
    ],
    'nextion_keybda_b6_val': [
        T('physical_nextion', 'keybdA', 'b6', 'val'),
        T('canvas_preview', 'keybdA', 'b6', 'val'),
    ],
    'nextion_keybda_b7_pic': [
        T('physical_nextion', 'keybdA', 'b7', 'pic'),
        T('canvas_preview', 'keybdA', 'b7', 'pic'),
    ],
    'nextion_keybda_b7_val': [
        T('physical_nextion', 'keybdA', 'b7', 'val'),
        T('canvas_preview', 'keybdA', 'b7', 'val'),
    ],
    'nextion_keybda_b8_pic': [
        T('physical_nextion', 'keybdA', 'b8', 'pic'),
        T('canvas_preview', 'keybdA', 'b8', 'pic'),
    ],
    'nextion_keybda_b8_val': [
        T('physical_nextion', 'keybdA', 'b8', 'val'),
        T('canvas_preview', 'keybdA', 'b8', 'val'),
    ],
    'nextion_keybda_b9_pic': [
        T('physical_nextion', 'keybdA', 'b9', 'pic'),
        T('canvas_preview', 'keybdA', 'b9', 'pic'),
    ],
    'nextion_keybda_b9_val': [
        T('physical_nextion', 'keybdA', 'b9', 'val'),
        T('canvas_preview', 'keybdA', 'b9', 'val'),
    ],
    'nextion_keybda_event_en': [
        T('physical_nextion', 'keybdA', 'Event', 'en'),
        T('canvas_preview', 'keybdA', 'Event', 'en'),
    ],
    'nextion_keybda_event_tim': [
        T('physical_nextion', 'keybdA', 'Event', 'tim'),
        T('canvas_preview', 'keybdA', 'Event', 'tim'),
    ],
    'nextion_keybda_input_txt': [
        T('physical_nextion', 'keybdA', 'input', 'txt'),
        T('canvas_preview', 'keybdA', 'input', 'txt'),
    ],
    'nextion_keybda_inputlenth_val': [
        T('physical_nextion', 'keybdA', 'inputlenth', 'val'),
        T('canvas_preview', 'keybdA', 'inputlenth', 'val'),
    ],
    'nextion_keybda_loadcmpid_val': [
        T('physical_nextion', 'keybdA', 'loadcmpid', 'val'),
        T('canvas_preview', 'keybdA', 'loadcmpid', 'val'),
    ],
    'nextion_keybda_loadpageid_val': [
        T('physical_nextion', 'keybdA', 'loadpageid', 'val'),
        T('canvas_preview', 'keybdA', 'loadpageid', 'val'),
    ],
    'nextion_keybda_refshow_state': [
        T('physical_nextion', 'keybdA', 'refshow', 'state'),
        T('canvas_preview', 'keybdA', 'refshow', 'state'),
    ],
    'nextion_keybda_show_txt': [
        T('physical_nextion', 'keybdA', 'show', 'txt'),
        T('canvas_preview', 'keybdA', 'show', 'txt'),
    ],
    'nextion_keybda_temp2_val': [
        T('physical_nextion', 'keybdA', 'temp2', 'val'),
        T('canvas_preview', 'keybdA', 'temp2', 'val'),
    ],
    'nextion_keybda_temp_val': [
        T('physical_nextion', 'keybdA', 'temp', 'val'),
        T('canvas_preview', 'keybdA', 'temp', 'val'),
    ],
    'nextion_keybda_tempstr_txt': [
        T('physical_nextion', 'keybdA', 'tempstr', 'txt'),
        T('canvas_preview', 'keybdA', 'tempstr', 'txt'),
    ],
    'nextion_keybda_tm0_en': [
        T('physical_nextion', 'keybdA', 'tm0', 'en'),
        T('canvas_preview', 'keybdA', 'tm0', 'en'),
    ],
    'nextion_keybda_tm0_tim': [
        T('physical_nextion', 'keybdA', 'tm0', 'tim'),
        T('canvas_preview', 'keybdA', 'tm0', 'tim'),
    ],
    'nextion_level_xyz_b_home_pic': [
        T('physical_nextion', 'level_xyz', 'b_home', 'pic'),
        T('canvas_preview', 'level_xyz', 'b_home', 'pic'),
    ],
    'nextion_level_xyz_b_home_val': [
        T('physical_nextion', 'level_xyz', 'b_home', 'val'),
        T('canvas_preview', 'level_xyz', 'b_home', 'val'),
    ],
    'nextion_level_xyz_event_en': [
        T('physical_nextion', 'level_xyz', 'Event', 'en'),
        T('canvas_preview', 'level_xyz', 'Event', 'en'),
    ],
    'nextion_level_xyz_event_tim': [
        T('physical_nextion', 'level_xyz', 'Event', 'tim'),
        T('canvas_preview', 'level_xyz', 'Event', 'tim'),
    ],
    'nextion_level_xyz_p0_pic': [
        T('physical_nextion', 'level_xyz', 'p0', 'pic'),
        T('canvas_preview', 'level_xyz', 'p0', 'pic'),
    ],
    'nextion_level_xyz_tm0_en': [
        T('physical_nextion', 'level_xyz', 'tm0', 'en'),
        T('canvas_preview', 'level_xyz', 'tm0', 'en'),
    ],
    'nextion_level_xyz_tm0_tim': [
        T('physical_nextion', 'level_xyz', 'tm0', 'tim'),
        T('canvas_preview', 'level_xyz', 'tm0', 'tim'),
    ],
    'nextion_level_xyz_va0_val': [
        T('physical_nextion', 'level_xyz', 'va0', 'val'),
        T('canvas_preview', 'level_xyz', 'va0', 'val'),
    ],
    'nextion_level_xyz_va1_val': [
        T('physical_nextion', 'level_xyz', 'va1', 'val'),
        T('canvas_preview', 'level_xyz', 'va1', 'val'),
    ],
    'nextion_level_xyz_va2_val': [
        T('physical_nextion', 'level_xyz', 'va2', 'val'),
        T('canvas_preview', 'level_xyz', 'va2', 'val'),
    ],
    'nextion_level_xyz_va3_val': [
        T('physical_nextion', 'level_xyz', 'va3', 'val'),
        T('canvas_preview', 'level_xyz', 'va3', 'val'),
    ],
    'nextion_page1_b_face_pic': [
        T('physical_nextion', 'page1', 'b_face', 'pic'),
        T('canvas_preview', 'page1', 'b_face', 'pic'),
    ],
    'nextion_page1_b_face_val': [
        T('physical_nextion', 'page1', 'b_face', 'val'),
        T('canvas_preview', 'page1', 'b_face', 'val'),
    ],
    'nextion_page1_b_level_pic': [
        T('physical_nextion', 'page1', 'b_level', 'pic'),
        T('canvas_preview', 'page1', 'b_level', 'pic'),
    ],
    'nextion_page1_b_level_val': [
        T('physical_nextion', 'page1', 'b_level', 'val'),
        T('canvas_preview', 'page1', 'b_level', 'val'),
    ],
    'nextion_page1_b_rrp_pic': [
        T('physical_nextion', 'page1', 'b_rrp', 'pic'),
        T('canvas_preview', 'page1', 'b_rrp', 'pic'),
    ],
    'nextion_page1_b_rrp_val': [
        T('physical_nextion', 'page1', 'b_rrp', 'val'),
        T('canvas_preview', 'page1', 'b_rrp', 'val'),
    ],
    'nextion_page1_b_sensors_pic': [
        T('physical_nextion', 'page1', 'b_sensors', 'pic'),
        T('canvas_preview', 'page1', 'b_sensors', 'pic'),
    ],
    'nextion_page1_b_sensors_val': [
        T('physical_nextion', 'page1', 'b_sensors', 'val'),
        T('canvas_preview', 'page1', 'b_sensors', 'val'),
    ],
    'nextion_page1_b_settings_pic': [
        T('physical_nextion', 'page1', 'b_settings', 'pic'),
        T('canvas_preview', 'page1', 'b_settings', 'pic'),
    ],
    'nextion_page1_b_settings_val': [
        T('physical_nextion', 'page1', 'b_settings', 'val'),
        T('canvas_preview', 'page1', 'b_settings', 'val'),
    ],
    'nextion_page1_b_take_pic': [
        T('physical_nextion', 'page1', 'b_take', 'pic'),
        T('canvas_preview', 'page1', 'b_take', 'pic'),
    ],
    'nextion_page1_b_take_val': [
        T('physical_nextion', 'page1', 'b_take', 'val'),
        T('canvas_preview', 'page1', 'b_take', 'val'),
    ],
    'nextion_rrp_main_b_home_pic': [
        T('physical_nextion', 'rrp_main', 'b_home', 'pic'),
        T('canvas_preview', 'rrp_main', 'b_home', 'pic'),
    ],
    'nextion_rrp_main_b_home_val': [
        T('physical_nextion', 'rrp_main', 'b_home', 'val'),
        T('canvas_preview', 'rrp_main', 'b_home', 'val'),
    ],
    'nextion_rrp_main_b_p1_arm_h_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_arm_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_arm_h', 'val'),
    ],
    'nextion_rrp_main_b_p1_arm_v_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_arm_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_arm_v', 'val'),
    ],
    'nextion_rrp_main_b_p1_cam_f_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_f', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_f', 'val'),
    ],
    'nextion_rrp_main_b_p1_cam_h_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_h', 'val'),
    ],
    'nextion_rrp_main_b_p1_cam_t_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_t', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_t', 'val'),
    ],
    'nextion_rrp_main_b_p1_cam_v_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_v', 'val'),
    ],
    'nextion_rrp_main_b_p1_dir_val': [
        T('physical_nextion', 'rrp_main', 'b_p1_dir', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_dir', 'val'),
    ],
    'nextion_rrp_main_b_p2_arm_h_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_arm_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_arm_h', 'val'),
    ],
    'nextion_rrp_main_b_p2_arm_v_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_arm_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_arm_v', 'val'),
    ],
    'nextion_rrp_main_b_p2_cam_f_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_f', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_f', 'val'),
    ],
    'nextion_rrp_main_b_p2_cam_h_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_h', 'val'),
    ],
    'nextion_rrp_main_b_p2_cam_t_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_t', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_t', 'val'),
    ],
    'nextion_rrp_main_b_p2_cam_v_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_v', 'val'),
    ],
    'nextion_rrp_main_b_p2_dir_val': [
        T('physical_nextion', 'rrp_main', 'b_p2_dir', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_dir', 'val'),
    ],
    'nextion_rrp_main_b_stop_pic': [
        T('physical_nextion', 'rrp_main', 'b_stop', 'pic'),
        T('canvas_preview', 'rrp_main', 'b_stop', 'pic'),
    ],
    'nextion_rrp_main_b_stop_val': [
        T('physical_nextion', 'rrp_main', 'b_stop', 'val'),
        T('canvas_preview', 'rrp_main', 'b_stop', 'val'),
    ],
    'nextion_rrp_main_h_p1_sens_val': [
        T('physical_nextion', 'rrp_main', 'h_p1_sens', 'val'),
        T('canvas_preview', 'rrp_main', 'h_p1_sens', 'val'),
    ],
    'nextion_rrp_main_h_p2_sens_val': [
        T('physical_nextion', 'rrp_main', 'h_p2_sens', 'val'),
        T('canvas_preview', 'rrp_main', 'h_p2_sens', 'val'),
    ],
    'nextion_rrp_main_t_buf_p1_txt': [
        T('physical_nextion', 'rrp_main', 't_buf_p1', 'txt'),
        T('canvas_preview', 'rrp_main', 't_buf_p1', 'txt'),
    ],
    'nextion_rrp_main_t_buf_p2_txt': [
        T('physical_nextion', 'rrp_main', 't_buf_p2', 'txt'),
        T('canvas_preview', 'rrp_main', 't_buf_p2', 'txt'),
    ],
    'nextion_rrp_main_t_p1_val_txt': [
        T('physical_nextion', 'rrp_main', 't_p1_val', 'txt'),
        T('canvas_preview', 'rrp_main', 't_p1_val', 'txt'),
    ],
    'nextion_rrp_main_t_p2_val_txt': [
        T('physical_nextion', 'rrp_main', 't_p2_val', 'txt'),
        T('canvas_preview', 'rrp_main', 't_p2_val', 'txt'),
    ],
    'nextion_rrp_main_va_p1_axis_val': [
        T('physical_nextion', 'rrp_main', 'va_p1_axis', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p1_axis', 'val'),
    ],
    'nextion_rrp_main_va_p1_dir_val': [
        T('physical_nextion', 'rrp_main', 'va_p1_dir', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p1_dir', 'val'),
    ],
    'nextion_rrp_main_va_p1_val_val': [
        T('physical_nextion', 'rrp_main', 'va_p1_val', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p1_val', 'val'),
    ],
    'nextion_rrp_main_va_p2_axis_val': [
        T('physical_nextion', 'rrp_main', 'va_p2_axis', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p2_axis', 'val'),
    ],
    'nextion_rrp_main_va_p2_dir_val': [
        T('physical_nextion', 'rrp_main', 'va_p2_dir', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p2_dir', 'val'),
    ],
    'nextion_rrp_main_va_p2_val_val': [
        T('physical_nextion', 'rrp_main', 'va_p2_val', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p2_val', 'val'),
    ],
    'nextion_rrp_main_va_tmp_val': [
        T('physical_nextion', 'rrp_main', 'va_tmp', 'val'),
        T('canvas_preview', 'rrp_main', 'va_tmp', 'val'),
    ],
    'nextion_sensors_main_b_home_pic': [
        T('physical_nextion', 'sensors_main', 'b_home', 'pic'),
        T('canvas_preview', 'sensors_main', 'b_home', 'pic'),
    ],
    'nextion_sensors_main_b_home_val': [
        T('physical_nextion', 'sensors_main', 'b_home', 'val'),
        T('canvas_preview', 'sensors_main', 'b_home', 'val'),
    ],
    'nextion_sensors_main_t0_txt': [
        T('physical_nextion', 'sensors_main', 't0', 'txt'),
        T('canvas_preview', 'sensors_main', 't0', 'txt'),
    ],
    'nextion_settings_main_b_home_pic': [
        T('physical_nextion', 'settings_main', 'b_home', 'pic'),
        T('canvas_preview', 'settings_main', 'b_home', 'pic'),
    ],
    'nextion_settings_main_b_home_val': [
        T('physical_nextion', 'settings_main', 'b_home', 'val'),
        T('canvas_preview', 'settings_main', 'b_home', 'val'),
    ],
    'nextion_settings_main_b_save_meta_pic': [
        T('physical_nextion', 'settings_main', 'b_save_meta', 'pic'),
        T('canvas_preview', 'settings_main', 'b_save_meta', 'pic'),
    ],
    'nextion_settings_main_b_save_meta_val': [
        T('physical_nextion', 'settings_main', 'b_save_meta', 'val'),
        T('canvas_preview', 'settings_main', 'b_save_meta', 'val'),
    ],
    'nextion_settings_main_t_director_txt': [
        T('physical_nextion', 'settings_main', 't_director', 'txt'),
        T('canvas_preview', 'settings_main', 't_director', 'txt'),
    ],
    'nextion_settings_main_t_save_status_txt': [
        T('physical_nextion', 'settings_main', 't_save_status', 'txt'),
        T('canvas_preview', 'settings_main', 't_save_status', 'txt'),
    ],
    'nextion_settings_main_t_title_txt': [
        T('physical_nextion', 'settings_main', 't_title', 'txt'),
        T('canvas_preview', 'settings_main', 't_title', 'txt'),
    ],
    'nextion_take_main_b_clap_pic': [
        T('physical_nextion', 'take_main', 'b_clap', 'pic'),
        T('canvas_preview', 'take_main', 'b_clap', 'pic'),
    ],
    'nextion_take_main_b_clap_val': [
        T('physical_nextion', 'take_main', 'b_clap', 'val'),
        T('canvas_preview', 'take_main', 'b_clap', 'val'),
    ],
    'nextion_take_main_b_home_pic': [
        T('physical_nextion', 'take_main', 'b_home', 'pic'),
        T('canvas_preview', 'take_main', 'b_home', 'pic'),
    ],
    'nextion_take_main_b_home_val': [
        T('physical_nextion', 'take_main', 'b_home', 'val'),
        T('canvas_preview', 'take_main', 'b_home', 'val'),
    ],
    'nextion_take_main_p_axis0_pic': [
        T('physical_nextion', 'take_main', 'p_axis0', 'pic'),
        T('canvas_preview', 'take_main', 'p_axis0', 'pic'),
    ],
    'nextion_take_main_p_axis1_pic': [
        T('physical_nextion', 'take_main', 'p_axis1', 'pic'),
        T('canvas_preview', 'take_main', 'p_axis1', 'pic'),
    ],
    'nextion_take_main_p_axis2_pic': [
        T('physical_nextion', 'take_main', 'p_axis2', 'pic'),
        T('canvas_preview', 'take_main', 'p_axis2', 'pic'),
    ],
    'nextion_take_main_p_axis3_pic': [
        T('physical_nextion', 'take_main', 'p_axis3', 'pic'),
        T('canvas_preview', 'take_main', 'p_axis3', 'pic'),
    ],
    'nextion_take_main_p_axis4_pic': [
        T('physical_nextion', 'take_main', 'p_axis4', 'pic'),
        T('canvas_preview', 'take_main', 'p_axis4', 'pic'),
    ],
    'nextion_take_main_p_axis5_pic': [
        T('physical_nextion', 'take_main', 'p_axis5', 'pic'),
        T('canvas_preview', 'take_main', 'p_axis5', 'pic'),
    ],
    'nextion_take_main_p_laser_pic': [
        T('physical_nextion', 'take_main', 'p_laser', 'pic'),
        T('canvas_preview', 'take_main', 'p_laser', 'pic'),
    ],
    'nextion_take_main_p_light_pic': [
        T('physical_nextion', 'take_main', 'p_light', 'pic'),
        T('canvas_preview', 'take_main', 'p_light', 'pic'),
    ],
    'nextion_take_main_p_limits_pic': [
        T('physical_nextion', 'take_main', 'p_limits', 'pic'),
        T('canvas_preview', 'take_main', 'p_limits', 'pic'),
    ],
    'nextion_take_main_p_shock_pic': [
        T('physical_nextion', 'take_main', 'p_shock', 'pic'),
        T('canvas_preview', 'take_main', 'p_shock', 'pic'),
    ],
    'nextion_take_main_p_temp_pic': [
        T('physical_nextion', 'take_main', 'p_temp', 'pic'),
        T('canvas_preview', 'take_main', 'p_temp', 'pic'),
    ],
    'nextion_take_main_p_xyz_pic': [
        T('physical_nextion', 'take_main', 'p_xyz', 'pic'),
        T('canvas_preview', 'take_main', 'p_xyz', 'pic'),
    ],
    'nextion_take_main_t0_txt': [
        T('physical_nextion', 'take_main', 't0', 'txt'),
        T('canvas_preview', 'take_main', 't0', 'txt'),
    ],
    'nextion_take_main_t1_txt': [
        T('physical_nextion', 'take_main', 't1', 'txt'),
        T('canvas_preview', 'take_main', 't1', 'txt'),
    ],
    'nextion_take_main_t2_txt': [
        T('physical_nextion', 'take_main', 't2', 'txt'),
        T('canvas_preview', 'take_main', 't2', 'txt'),
    ],
    'nextion_take_main_t_axis0_txt': [
        T('physical_nextion', 'take_main', 't_axis0', 'txt'),
        T('canvas_preview', 'take_main', 't_axis0', 'txt'),
    ],
    'nextion_take_main_t_axis1_txt': [
        T('physical_nextion', 'take_main', 't_axis1', 'txt'),
        T('canvas_preview', 'take_main', 't_axis1', 'txt'),
    ],
    'nextion_take_main_t_axis2_txt': [
        T('physical_nextion', 'take_main', 't_axis2', 'txt'),
        T('canvas_preview', 'take_main', 't_axis2', 'txt'),
    ],
    'nextion_take_main_t_axis3_txt': [
        T('physical_nextion', 'take_main', 't_axis3', 'txt'),
        T('canvas_preview', 'take_main', 't_axis3', 'txt'),
    ],
    'nextion_take_main_t_axis4_txt': [
        T('physical_nextion', 'take_main', 't_axis4', 'txt'),
        T('canvas_preview', 'take_main', 't_axis4', 'txt'),
    ],
    'nextion_take_main_t_axis5_txt': [
        T('physical_nextion', 'take_main', 't_axis5', 'txt'),
        T('canvas_preview', 'take_main', 't_axis5', 'txt'),
    ],
    'nextion_take_main_t_clap_txt': [
        T('physical_nextion', 'take_main', 't_clap', 'txt'),
        T('canvas_preview', 'take_main', 't_clap', 'txt'),
    ],
    'nextion_take_main_t_laser_txt': [
        T('physical_nextion', 'take_main', 't_laser', 'txt'),
        T('canvas_preview', 'take_main', 't_laser', 'txt'),
    ],
    'nextion_take_main_t_light_txt': [
        T('physical_nextion', 'take_main', 't_light', 'txt'),
        T('canvas_preview', 'take_main', 't_light', 'txt'),
    ],
    'nextion_take_main_t_limits_txt': [
        T('physical_nextion', 'take_main', 't_limits', 'txt'),
        T('canvas_preview', 'take_main', 't_limits', 'txt'),
    ],
    'nextion_take_main_t_shock_txt': [
        T('physical_nextion', 'take_main', 't_shock', 'txt'),
        T('canvas_preview', 'take_main', 't_shock', 'txt'),
    ],
    'nextion_take_main_t_status_txt': [
        T('physical_nextion', 'take_main', 't_status', 'txt'),
        T('canvas_preview', 'take_main', 't_status', 'txt'),
    ],
    'nextion_take_main_t_take_txt': [
        T('physical_nextion', 'take_main', 't_take', 'txt'),
        T('canvas_preview', 'take_main', 't_take', 'txt'),
    ],
    'nextion_take_main_t_temp_txt': [
        T('physical_nextion', 'take_main', 't_temp', 'txt'),
        T('canvas_preview', 'take_main', 't_temp', 'txt'),
    ],
    'nextion_take_main_t_xyz_txt': [
        T('physical_nextion', 'take_main', 't_xyz', 'txt'),
        T('canvas_preview', 'take_main', 't_xyz', 'txt'),
    ],

    # -------------------------------------------------------------------------
    # 12_TKINTER_SCAN_KATALOG: Pełny katalog Tkinter z automatycznego skanu
    # -------------------------------------------------------------------------
    'tk_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanaxissandbox_step_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_axis_info_label_text': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'axis_info_label', 'text'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'canvas', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_curve_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'curve_canvas', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_left_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'left', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_protocol_box_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'protocol_box', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_protocol_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'protocol_canvas', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_protocol_holder_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'protocol_holder', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_protocol_label_text': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'protocol_label', 'text'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_protocol_text_text': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'protocol_text', 'text'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_row_frame_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'row_frame', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_save_button_text': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'save_button', 'text'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_status_text': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'status', 'text'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_step_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'step_canvas', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_take_panel_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'take_panel', 'state'),
    ],
    'tk_editor_editor_ehr_tarzanehrui_timeline_canvas_state': [
        T('ehr_tkinter', 'editor_editor_ehr_tarzanehrui', 'timeline_canvas', 'state'),
    ],
    'tk_editor_editor_tarzanaxissandbox_curve_canvas_state': [
        T('sandbox_tkinter', 'editor_editor_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_editor_editor_tarzanaxissandbox_step_canvas_state': [
        T('sandbox_tkinter', 'editor_editor_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_editor_editor_tarzanehrtakesandbox_canvas_state': [
        T('ehr_tkinter', 'editor_editor_tarzanehrtakesandbox', 'canvas', 'state'),
    ],
    'tk_editor_editor_tarzanehrtakesandbox_controls_wrap_state': [
        T('ehr_tkinter', 'editor_editor_tarzanehrtakesandbox', 'controls_wrap', 'state'),
    ],
    'tk_editor_editor_tarzanehrtakesandbox_protocol_canvas_state': [
        T('ehr_tkinter', 'editor_editor_tarzanehrtakesandbox', 'protocol_canvas', 'state'),
    ],
    'tk_editor_editor_tarzanehrtakesandbox_protocol_holder_state': [
        T('ehr_tkinter', 'editor_editor_tarzanehrtakesandbox', 'protocol_holder', 'state'),
    ],
    'tk_editor_editor_tarzanehrtakesandbox_row_frame_state': [
        T('ehr_tkinter', 'editor_editor_tarzanehrtakesandbox', 'row_frame', 'state'),
    ],
    'tk_editor_editor_tarzanehrtakesandbox_save_button_text': [
        T('ehr_tkinter', 'editor_editor_tarzanehrtakesandbox', 'save_button', 'text'),
    ],
    'tk_editor_editor_tarzantakeprotocollight_canvas_state': [
        T('par_tkinter', 'editor_editor_tarzantakeprotocollight', 'canvas', 'state'),
    ],
    'tk_editor_editor_tarzantakeprotocollight_protocol_canvas_state': [
        T('par_tkinter', 'editor_editor_tarzantakeprotocollight', 'protocol_canvas', 'state'),
    ],
    'tk_editor_editor_tarzantakeprotocollight_protocol_holder_state': [
        T('par_tkinter', 'editor_editor_tarzantakeprotocollight', 'protocol_holder', 'state'),
    ],
    'tk_editor_editor_tarzantakeprotocollight_row_frame_state': [
        T('par_tkinter', 'editor_editor_tarzantakeprotocollight', 'row_frame', 'state'),
    ],
    'tk_editor_editor_tarzantakeprotocollight_save_button_text': [
        T('par_tkinter', 'editor_editor_tarzantakeprotocollight', 'save_button', 'text'),
    ],
    'tk_editor_ehr_tarzanaxissandbox_curve_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_editor_ehr_tarzanaxissandbox_step_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_axis_info_label_text': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'axis_info_label', 'text'),
    ],
    'tk_editor_ehr_tarzanehrui_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'canvas', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_curve_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'curve_canvas', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_left_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'left', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_protocol_box_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'protocol_box', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_protocol_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'protocol_canvas', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_protocol_holder_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'protocol_holder', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_protocol_label_text': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'protocol_label', 'text'),
    ],
    'tk_editor_ehr_tarzanehrui_protocol_text_text': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'protocol_text', 'text'),
    ],
    'tk_editor_ehr_tarzanehrui_row_frame_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'row_frame', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_save_button_text': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'save_button', 'text'),
    ],
    'tk_editor_ehr_tarzanehrui_selected_point_time_label_text': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'selected_point_time_label', 'text'),
    ],
    'tk_editor_ehr_tarzanehrui_status_text': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'status', 'text'),
    ],
    'tk_editor_ehr_tarzanehrui_step_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'step_canvas', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_take_panel_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'take_panel', 'state'),
    ],
    'tk_editor_ehr_tarzanehrui_timeline_canvas_state': [
        T('ehr_tkinter', 'editor_ehr_tarzanehrui', 'timeline_canvas', 'state'),
    ],
    'tk_editor_par_tarzannextionpreview_page_label_text': [
        T('par_tkinter', 'editor_par_tarzannextionpreview', 'page_label', 'text'),
    ],
    'tk_editor_par_tarzannextionpreview_screen_canvas_state': [
        T('par_tkinter', 'editor_par_tarzannextionpreview', 'screen_canvas', 'state'),
    ],
    'tk_editor_par_tarzannextionpreview_screen_frame_state': [
        T('par_tkinter', 'editor_par_tarzannextionpreview', 'screen_frame', 'state'),
    ],
    'tk_editor_par_tarzannextionpreview_status_text': [
        T('par_tkinter', 'editor_par_tarzannextionpreview', 'status', 'text'),
    ],
    'tk_editor_par_tarzanparapp_body_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'body', 'state'),
    ],
    'tk_editor_par_tarzanparapp_bottom_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'bottom', 'state'),
    ],
    'tk_editor_par_tarzanparapp_clock_text': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'clock', 'text'),
    ],
    'tk_editor_par_tarzanparapp_footer_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'footer', 'state'),
    ],
    'tk_editor_par_tarzanparapp_header_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'header', 'state'),
    ],
    'tk_editor_par_tarzanparapp_layout_master_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'layout_master', 'state'),
    ],
    'tk_editor_par_tarzanparapp_left_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'left', 'state'),
    ],
    'tk_editor_par_tarzanparapp_middle_bottom_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'middle_bottom', 'state'),
    ],
    'tk_editor_par_tarzanparapp_middle_top_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'middle_top', 'state'),
    ],
    'tk_editor_par_tarzanparapp_mode_label_text': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'mode_label', 'text'),
    ],
    'tk_editor_par_tarzanparapp_right_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'right', 'state'),
    ],
    'tk_editor_par_tarzanparapp_top_state': [
        T('par_tkinter', 'editor_par_tarzanparapp', 'top', 'state'),
    ],
    'tk_editor_par_tarzanparpanels_log_text_text': [
        T('par_tkinter', 'editor_par_tarzanparpanels', 'log_text', 'text'),
    ],
    'tk_editor_par_tarzanparpanels_old_log_text_text': [
        T('par_tkinter', 'editor_par_tarzanparpanels_old', 'log_text', 'text'),
    ],
    'tk_editor_par_tarzanparpanels_timeline_canvas_state': [
        T('par_tkinter', 'editor_par_tarzanparpanels', 'timeline_canvas', 'state'),
    ],
    'tk_editor_par_tarzanparwidgets_body_state': [
        T('par_tkinter', 'editor_par_tarzanparwidgets', 'body', 'state'),
    ],
    'tk_editor_par_tarzanparwidgets_counter_label_text': [
        T('par_tkinter', 'editor_par_tarzanparwidgets', 'counter_label', 'text'),
    ],
    'tk_editor_par_tarzanparwidgets_motor_canvas_state': [
        T('par_tkinter', 'editor_par_tarzanparwidgets', 'motor_canvas', 'state'),
    ],
    'tk_editor_tarzanaxissandbox_curve_canvas_state': [
        T('sandbox_tkinter', 'editor_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_editor_tarzanaxissandbox_step_canvas_state': [
        T('sandbox_tkinter', 'editor_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_editor_tarzanehrtakesandbox_canvas_state': [
        T('ehr_tkinter', 'editor_tarzanehrtakesandbox', 'canvas', 'state'),
    ],
    'tk_editor_tarzanehrtakesandbox_controls_wrap_state': [
        T('ehr_tkinter', 'editor_tarzanehrtakesandbox', 'controls_wrap', 'state'),
    ],
    'tk_editor_tarzanehrtakesandbox_protocol_canvas_state': [
        T('ehr_tkinter', 'editor_tarzanehrtakesandbox', 'protocol_canvas', 'state'),
    ],
    'tk_editor_tarzanehrtakesandbox_protocol_holder_state': [
        T('ehr_tkinter', 'editor_tarzanehrtakesandbox', 'protocol_holder', 'state'),
    ],
    'tk_editor_tarzanehrtakesandbox_row_frame_state': [
        T('ehr_tkinter', 'editor_tarzanehrtakesandbox', 'row_frame', 'state'),
    ],
    'tk_editor_tarzanehrtakesandbox_save_button_text': [
        T('ehr_tkinter', 'editor_tarzanehrtakesandbox', 'save_button', 'text'),
    ],
    'tk_editor_tarzankhr_btn_start_text': [
        T('khr_tkinter', 'editor_tarzankhr', 'btn_start', 'text'),
    ],
    'tk_editor_tarzankhr_btn_stop_text': [
        T('khr_tkinter', 'editor_tarzankhr', 'btn_stop', 'text'),
    ],
    'tk_editor_tarzankhr_input_canvas_state': [
        T('khr_tkinter', 'editor_tarzankhr', 'input_canvas', 'state'),
    ],
    'tk_editor_tarzankhr_khr_canvas_state': [
        T('khr_tkinter', 'editor_tarzankhr', 'khr_canvas', 'state'),
    ],
    'tk_editor_tarzankhr_output_canvas_state': [
        T('khr_tkinter', 'editor_tarzankhr', 'output_canvas', 'state'),
    ],
    'tk_editor_tarzankhr_plugin_box_text': [
        T('khr_tkinter', 'editor_tarzankhr', 'plugin_box', 'text'),
    ],
    'tk_editor_tarzankhr_preview_canvas_state': [
        T('khr_tkinter', 'editor_tarzankhr', 'preview_canvas', 'state'),
    ],
    'tk_editor_tarzankhr_profile_box_text': [
        T('khr_tkinter', 'editor_tarzankhr', 'profile_box', 'text'),
    ],
    'tk_editor_tarzankhr_profile_desc_text': [
        T('khr_tkinter', 'editor_tarzankhr', 'profile_desc', 'text'),
    ],
    'tk_editor_tarzankhr_status_text': [
        T('khr_tkinter', 'editor_tarzankhr', 'status', 'text'),
    ],
    'tk_editor_tarzantakeprotocollight_canvas_state': [
        T('par_tkinter', 'editor_tarzantakeprotocollight', 'canvas', 'state'),
    ],
    'tk_editor_tarzantakeprotocollight_protocol_canvas_state': [
        T('par_tkinter', 'editor_tarzantakeprotocollight', 'protocol_canvas', 'state'),
    ],
    'tk_editor_tarzantakeprotocollight_protocol_holder_state': [
        T('par_tkinter', 'editor_tarzantakeprotocollight', 'protocol_holder', 'state'),
    ],
    'tk_editor_tarzantakeprotocollight_row_frame_state': [
        T('par_tkinter', 'editor_tarzantakeprotocollight', 'row_frame', 'state'),
    ],
    'tk_editor_tarzantakeprotocollight_save_button_text': [
        T('par_tkinter', 'editor_tarzantakeprotocollight', 'save_button', 'text'),
    ],
    'tk_hardware_tarzannextion_tarzannextionsandbox_log_text': [
        T('sandbox_tkinter', 'hardware_tarzannextion_tarzannextionsandbox', 'log', 'text'),
    ],
    'tk_mechanics_tarzanedytorchoreografiiruchu_global_canvas_state': [
        T('par_tkinter', 'mechanics_tarzanedytorchoreografiiruchu', 'global_canvas', 'state'),
    ],
    'tk_mechanics_tarzanedytorchoreografiiruchu_scroll_canvas_state': [
        T('par_tkinter', 'mechanics_tarzanedytorchoreografiiruchu', 'scroll_canvas', 'state'),
    ],
    'tk_mechanics_tarzanedytorchoreografiiruchu_tracks_frame_state': [
        T('par_tkinter', 'mechanics_tarzanedytorchoreografiiruchu', 'tracks_frame', 'state'),
    ],
    'tk_mechanics_tarzanpanelosi_row1_state': [
        T('par_tkinter', 'mechanics_tarzanpanelosi', 'row1', 'state'),
    ],
    'tk_mechanics_tarzanpanelosi_row2_state': [
        T('par_tkinter', 'mechanics_tarzanpanelosi', 'row2', 'state'),
    ],
    'tk_mechanics_tarzanpanelosi_row3_state': [
        T('par_tkinter', 'mechanics_tarzanpanelosi', 'row3', 'state'),
    ],
    'tk_mechanics_tarzanwykresosi_canvas_state': [
        T('par_tkinter', 'mechanics_tarzanwykresosi', 'canvas', 'state'),
    ],
    'tk_mechanics_tarzanwykresosi_limit_canvas_state': [
        T('par_tkinter', 'mechanics_tarzanwykresosi', 'limit_canvas', 'state'),
    ],
    'tk_mechanics_tarzanwykresosi_limit_panel_state': [
        T('par_tkinter', 'mechanics_tarzanwykresosi', 'limit_panel', 'state'),
    ],
    'tk_mechanics_tarzanwykresosi_meta_label_text': [
        T('par_tkinter', 'mechanics_tarzanwykresosi', 'meta_label', 'text'),
    ],
    'tk_mechanics_tarzanwykresosi_title_text': [
        T('par_tkinter', 'mechanics_tarzanwykresosi', 'title', 'text'),
    ],
    'tk_modes_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanaxissandbox_step_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_axis_info_label_text': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'axis_info_label', 'text'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'canvas', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_curve_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'curve_canvas', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_left_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'left', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_box_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_box', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_canvas', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_holder_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_holder', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_label_text': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_label', 'text'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_protocol_text_text': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_text', 'text'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_row_frame_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'row_frame', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_save_button_text': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'save_button', 'text'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_status_text': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'status', 'text'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_step_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'step_canvas', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_take_panel_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'take_panel', 'state'),
    ],
    'tk_modes_editor_editor_ehr_tarzanehrui_timeline_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_ehr_tarzanehrui', 'timeline_canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzanaxissandbox_curve_canvas_state': [
        T('sandbox_tkinter', 'modes_editor_editor_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzanaxissandbox_step_canvas_state': [
        T('sandbox_tkinter', 'modes_editor_editor_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzanehrtakesandbox_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_tarzanehrtakesandbox', 'canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzanehrtakesandbox_controls_wrap_state': [
        T('ehr_tkinter', 'modes_editor_editor_tarzanehrtakesandbox', 'controls_wrap', 'state'),
    ],
    'tk_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_state': [
        T('ehr_tkinter', 'modes_editor_editor_tarzanehrtakesandbox', 'protocol_canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzanehrtakesandbox_protocol_holder_state': [
        T('ehr_tkinter', 'modes_editor_editor_tarzanehrtakesandbox', 'protocol_holder', 'state'),
    ],
    'tk_modes_editor_editor_tarzanehrtakesandbox_row_frame_state': [
        T('ehr_tkinter', 'modes_editor_editor_tarzanehrtakesandbox', 'row_frame', 'state'),
    ],
    'tk_modes_editor_editor_tarzanehrtakesandbox_save_button_text': [
        T('ehr_tkinter', 'modes_editor_editor_tarzanehrtakesandbox', 'save_button', 'text'),
    ],
    'tk_modes_editor_editor_tarzantakeprotocollight_canvas_state': [
        T('par_tkinter', 'modes_editor_editor_tarzantakeprotocollight', 'canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_state': [
        T('par_tkinter', 'modes_editor_editor_tarzantakeprotocollight', 'protocol_canvas', 'state'),
    ],
    'tk_modes_editor_editor_tarzantakeprotocollight_protocol_holder_state': [
        T('par_tkinter', 'modes_editor_editor_tarzantakeprotocollight', 'protocol_holder', 'state'),
    ],
    'tk_modes_editor_editor_tarzantakeprotocollight_row_frame_state': [
        T('par_tkinter', 'modes_editor_editor_tarzantakeprotocollight', 'row_frame', 'state'),
    ],
    'tk_modes_editor_editor_tarzantakeprotocollight_save_button_text': [
        T('par_tkinter', 'modes_editor_editor_tarzantakeprotocollight', 'save_button', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanaxissandbox_curve_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanaxissandbox_step_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_axis_info_label_text': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'axis_info_label', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'canvas', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_curve_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'curve_canvas', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_left_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'left', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_protocol_box_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'protocol_box', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_protocol_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'protocol_canvas', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_protocol_holder_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'protocol_holder', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_protocol_label_text': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'protocol_label', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_protocol_text_text': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'protocol_text', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_row_frame_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'row_frame', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_save_button_text': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'save_button', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_selected_point_time_label_text': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'selected_point_time_label', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_status_text': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'status', 'text'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_step_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'step_canvas', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_take_panel_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'take_panel', 'state'),
    ],
    'tk_modes_editor_ehr_tarzanehrui_timeline_canvas_state': [
        T('ehr_tkinter', 'modes_editor_ehr_tarzanehrui', 'timeline_canvas', 'state'),
    ],
    'tk_modes_editor_par_tarzannextionpreview_page_label_text': [
        T('par_tkinter', 'modes_editor_par_tarzannextionpreview', 'page_label', 'text'),
    ],
    'tk_modes_editor_par_tarzannextionpreview_screen_canvas_state': [
        T('par_tkinter', 'modes_editor_par_tarzannextionpreview', 'screen_canvas', 'state'),
    ],
    'tk_modes_editor_par_tarzannextionpreview_screen_frame_state': [
        T('par_tkinter', 'modes_editor_par_tarzannextionpreview', 'screen_frame', 'state'),
    ],
    'tk_modes_editor_par_tarzannextionpreview_status_text': [
        T('par_tkinter', 'modes_editor_par_tarzannextionpreview', 'status', 'text'),
    ],
    'tk_modes_editor_par_tarzanparapp_body_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'body', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_bottom_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'bottom', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_clock_text': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'clock', 'text'),
    ],
    'tk_modes_editor_par_tarzanparapp_footer_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'footer', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_header_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'header', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_layout_master_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'layout_master', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_left_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'left', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_middle_bottom_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'middle_bottom', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_middle_top_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'middle_top', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_mode_label_text': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'mode_label', 'text'),
    ],
    'tk_modes_editor_par_tarzanparapp_right_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'right', 'state'),
    ],
    'tk_modes_editor_par_tarzanparapp_top_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparapp', 'top', 'state'),
    ],
    'tk_modes_editor_par_tarzanparpanels_log_text_text': [
        T('par_tkinter', 'modes_editor_par_tarzanparpanels', 'log_text', 'text'),
    ],
    'tk_modes_editor_par_tarzanparpanels_old_log_text_text': [
        T('par_tkinter', 'modes_editor_par_tarzanparpanels_old', 'log_text', 'text'),
    ],
    'tk_modes_editor_par_tarzanparpanels_timeline_canvas_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparpanels', 'timeline_canvas', 'state'),
    ],
    'tk_modes_editor_par_tarzanparwidgets_body_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparwidgets', 'body', 'state'),
    ],
    'tk_modes_editor_par_tarzanparwidgets_counter_label_text': [
        T('par_tkinter', 'modes_editor_par_tarzanparwidgets', 'counter_label', 'text'),
    ],
    'tk_modes_editor_par_tarzanparwidgets_motor_canvas_state': [
        T('par_tkinter', 'modes_editor_par_tarzanparwidgets', 'motor_canvas', 'state'),
    ],
    'tk_modes_editor_tarzanaxissandbox_curve_canvas_state': [
        T('sandbox_tkinter', 'modes_editor_tarzanaxissandbox', 'curve_canvas', 'state'),
    ],
    'tk_modes_editor_tarzanaxissandbox_step_canvas_state': [
        T('sandbox_tkinter', 'modes_editor_tarzanaxissandbox', 'step_canvas', 'state'),
    ],
    'tk_modes_editor_tarzanehrtakesandbox_canvas_state': [
        T('ehr_tkinter', 'modes_editor_tarzanehrtakesandbox', 'canvas', 'state'),
    ],
    'tk_modes_editor_tarzanehrtakesandbox_controls_wrap_state': [
        T('ehr_tkinter', 'modes_editor_tarzanehrtakesandbox', 'controls_wrap', 'state'),
    ],
    'tk_modes_editor_tarzanehrtakesandbox_protocol_canvas_state': [
        T('ehr_tkinter', 'modes_editor_tarzanehrtakesandbox', 'protocol_canvas', 'state'),
    ],
    'tk_modes_editor_tarzanehrtakesandbox_protocol_holder_state': [
        T('ehr_tkinter', 'modes_editor_tarzanehrtakesandbox', 'protocol_holder', 'state'),
    ],
    'tk_modes_editor_tarzanehrtakesandbox_row_frame_state': [
        T('ehr_tkinter', 'modes_editor_tarzanehrtakesandbox', 'row_frame', 'state'),
    ],
    'tk_modes_editor_tarzanehrtakesandbox_save_button_text': [
        T('ehr_tkinter', 'modes_editor_tarzanehrtakesandbox', 'save_button', 'text'),
    ],
    'tk_modes_editor_tarzankhr_btn_start_text': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'btn_start', 'text'),
    ],
    'tk_modes_editor_tarzankhr_btn_stop_text': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'btn_stop', 'text'),
    ],
    'tk_modes_editor_tarzankhr_input_canvas_state': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'input_canvas', 'state'),
    ],
    'tk_modes_editor_tarzankhr_khr_canvas_state': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'khr_canvas', 'state'),
    ],
    'tk_modes_editor_tarzankhr_output_canvas_state': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'output_canvas', 'state'),
    ],
    'tk_modes_editor_tarzankhr_plugin_box_text': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'plugin_box', 'text'),
    ],
    'tk_modes_editor_tarzankhr_preview_canvas_state': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'preview_canvas', 'state'),
    ],
    'tk_modes_editor_tarzankhr_profile_box_text': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'profile_box', 'text'),
    ],
    'tk_modes_editor_tarzankhr_profile_desc_text': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'profile_desc', 'text'),
    ],
    'tk_modes_editor_tarzankhr_status_text': [
        T('khr_tkinter', 'modes_editor_tarzankhr', 'status', 'text'),
    ],
    'tk_modes_editor_tarzantakeprotocollight_canvas_state': [
        T('par_tkinter', 'modes_editor_tarzantakeprotocollight', 'canvas', 'state'),
    ],
    'tk_modes_editor_tarzantakeprotocollight_protocol_canvas_state': [
        T('par_tkinter', 'modes_editor_tarzantakeprotocollight', 'protocol_canvas', 'state'),
    ],
    'tk_modes_editor_tarzantakeprotocollight_protocol_holder_state': [
        T('par_tkinter', 'modes_editor_tarzantakeprotocollight', 'protocol_holder', 'state'),
    ],
    'tk_modes_editor_tarzantakeprotocollight_row_frame_state': [
        T('par_tkinter', 'modes_editor_tarzantakeprotocollight', 'row_frame', 'state'),
    ],
    'tk_modes_editor_tarzantakeprotocollight_save_button_text': [
        T('par_tkinter', 'modes_editor_tarzantakeprotocollight', 'save_button', 'text'),
    ],
    'tk_modes_hardware_tarzannextion_tarzannextionsandbox_log_text': [
        T('sandbox_tkinter', 'modes_hardware_tarzannextion_tarzannextionsandbox', 'log', 'text'),
    ],
    'tk_vision_tarzanvisionsetup_content_state': [
        T('par_tkinter', 'vision_tarzanvisionsetup', 'content', 'state'),
    ],

    # -------------------------------------------------------------------------
    # 13_CANVAS_SCAN_KATALOG: Pełny katalog Canvas z automatycznego skanu
    # -------------------------------------------------------------------------
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_826', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_833', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_840', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_852', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_853', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_867', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_879', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_line_line_881', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_oval_line_849', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_812', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_819', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_861', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_text_line_827', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_text_line_834', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_text_line_854', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_text_line_855', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_text_line_882', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanaxissandbox', 'c_text_line_883', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_image_line_2734', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1910', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1919', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1930', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1937', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1951', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1952', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1966', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1978', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_1980', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2697', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2707', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2710', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2749', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2757', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2765', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2778', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_line_line_2801', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_oval_line_1947', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_oval_line_2792', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_oval_line_2794', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_polygon_line_2808', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1893', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1901', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1902', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1903', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1960', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2688', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2705', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2790', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2800', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1911_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_1911', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1920_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_1920', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1953_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_1953', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1954_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_1954', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1981_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_1981', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_1982_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_1982', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2720_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_2720', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2727_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_2727', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2736_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_2736', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2809_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_2809', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_c_text_line_2816_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'c_text_line_2816', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'canvas_image_line_712', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'canvas_rectangle_line_1244', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'canvas_window_line_1172', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_item_text': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'item', 'text'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_962', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_963', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_row_window_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'row_window', 'coords'),
    ],
    'canvas_editor_editor_ehr_tarzanehrui_save_button_window_coords': [
        T('ehr_canvas', 'editor_editor_ehr_tarzanehrui', 'save_button_window', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_826_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_826', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_833_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_833', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_852_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_852', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_859_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_859', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_871_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_871', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_872_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_872', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_886_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_886', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_898_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_898', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_line_line_900_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_line_line_900', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_oval_line_868_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_oval_line_868', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_rectangle_line_812', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_rectangle_line_819', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_rectangle_line_880', 'coords'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_827_text': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_text_line_827', 'text'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_834_text': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_text_line_834', 'text'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_873_text': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_text_line_873', 'text'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_874_text': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_text_line_874', 'text'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_901_text': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_text_line_901', 'text'),
    ],
    'canvas_editor_editor_tarzanaxissandbox_c_text_line_902_text': [
        T('sandbox_canvas', 'editor_editor_tarzanaxissandbox', 'c_text_line_902', 'text'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'canvas_image_line_553', 'coords'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_item_text': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'item', 'text'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1057', 'coords'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1058', 'coords'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_protocol_title_id_text': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'protocol_title_id', 'text'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_row_window_coords': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'row_window', 'coords'),
    ],
    'canvas_editor_editor_tarzanehrtakesandbox_save_button_window_coords': [
        T('ehr_canvas', 'editor_editor_tarzanehrtakesandbox', 'save_button_window', 'coords'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'canvas_image_line_860', 'coords'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_item_text': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'item', 'text'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1215', 'coords'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1216', 'coords'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_protocol_title_id_text': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'protocol_title_id', 'text'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_row_window_coords': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'row_window', 'coords'),
    ],
    'canvas_editor_editor_tarzantakeprotocollight_save_button_window_coords': [
        T('canvas_preview', 'editor_editor_tarzantakeprotocollight', 'save_button_window', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_827_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_827', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_834_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_834', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_841_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_841', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_853', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_854_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_854', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_868_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_868', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_880_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_880', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_line_line_882_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_line_line_882', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_oval_line_850', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_rectangle_line_813', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_rectangle_line_822', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_rectangle_line_862', 'coords'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_828_text': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_text_line_828', 'text'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_835_text': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_text_line_835', 'text'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_855_text': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_text_line_855', 'text'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_856_text': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_text_line_856', 'text'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_883_text': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_text_line_883', 'text'),
    ],
    'canvas_editor_ehr_tarzanaxissandbox_c_text_line_884_text': [
        T('ehr_canvas', 'editor_ehr_tarzanaxissandbox', 'c_text_line_884', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_image_line_3130_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_image_line_3130', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_1993_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_1993', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2002_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2002', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2013_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2013', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2020_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2020', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2048_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2048', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2049_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2049', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2068_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2068', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2080_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2080', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_2082_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_2082', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3081_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3081', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3102_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3102', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3105_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3105', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3145_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3145', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3153_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3153', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3161_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3161', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3176_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3176', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3217_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3217', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_line_line_3231_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_line_line_3231', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_oval_line_2044_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_oval_line_2044', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_oval_line_3194_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_oval_line_3194', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_oval_line_3210_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_oval_line_3210', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_polygon_line_3226_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_polygon_line_3226', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_1976', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_1984', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_1985', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_1986', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_2062', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_3072', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_3100', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_3192', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_rectangle_line_3216', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_1994_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_1994', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_2003_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_2003', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_2050_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_2050', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_2051_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_2051', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_2083_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_2083', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_2084_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_2084', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_3115_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_3115', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_3122_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_3122', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_3132_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_3132', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_3228_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_3228', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_c_text_line_3239_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'c_text_line_3239', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_canvas_image_line_760_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'canvas_image_line_760', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'canvas_rectangle_line_1300', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_canvas_window_line_1226_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'canvas_window_line_1226', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_item_text': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'item', 'text'),
    ],
    'canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_1010', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_1011', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_row_window_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'row_window', 'coords'),
    ],
    'canvas_editor_ehr_tarzanehrui_save_button_window_coords': [
        T('ehr_canvas', 'editor_ehr_tarzanehrui', 'save_button_window', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_edit_window_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', '_edit_window', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_image_line_591', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_image_line_623', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_image_line_640', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_image_line_692', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_image_line_718', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_line_line_415', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_line_line_432', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_line_line_445', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_line_line_737', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_line_line_738', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_line_line_818', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_oval_line_740', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_394', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_512', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_527', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_593', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_625', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_642', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_785', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_787', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_790', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_797', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_815', 'coords'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_400', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_414', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_421', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_425', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_466', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_483', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_518', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_529', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_594', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_603', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_626', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_643', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_791', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_798', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_799', 'text'),
    ],
    'canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text': [
        T('canvas_preview', 'editor_par_tarzannextionpreview', 'screen_canvas_text_line_816', 'text'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_oval_line_1309_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_oval_line_1309', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_oval_line_1402_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_oval_line_1402', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1286', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1303', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1314', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1315', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1316', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1329', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1387', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1414', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1415', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1416', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_rectangle_line_1431', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_text_line_1310_text': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_text_line_1310', 'text'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_text_line_1434_text': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_text_line_1434', 'text'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_text_line_1451_text': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_text_line_1451', 'text'),
    ],
    'canvas_editor_par_tarzanparapp_canvas_text_line_1455_text': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'canvas_text_line_1455', 'text'),
    ],
    'canvas_editor_par_tarzanparapp_led_oval_line_485_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'led_oval_line_485', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'panel_canvas_window_line_1076', 'coords'),
    ],
    'canvas_editor_par_tarzanparapp_text_id_text': [
        T('layout_canvas', 'editor_par_tarzanparapp', 'text_id', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_can_image_line_1306_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_image_line_1306', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_1298_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_1298', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_1299_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_1299', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_1304_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_1304', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_1311_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_1311', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_1326_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_1326', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_1327_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_1327', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_510_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_510', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_664_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_664', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_line_line_665_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_line_line_665', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_oval_line_509_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_oval_line_509', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_oval_line_511_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_oval_line_511', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_oval_line_656_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_oval_line_656', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_oval_line_920_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_oval_line_920', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_polygon_line_921_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_polygon_line_921', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_rectangle_line_899_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_rectangle_line_899', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_rectangle_line_901_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_rectangle_line_901', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_can_text_line_1307_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_text_line_1307', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_can_text_line_1309_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_text_line_1309', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_can_text_line_1310_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_text_line_1310', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_can_text_line_1329_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_text_line_1329', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_can_text_line_1331_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'can_text_line_1331', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_line_line_825_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_line_line_825', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_line_line_826_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_line_line_826', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_oval_line_1575_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_oval_line_1575', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_oval_line_830_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_oval_line_830', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_polygon_line_828_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_polygon_line_828', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_rectangle_line_1449', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_rectangle_line_1450', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'canvas_rectangle_line_1451', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_line_line_3118_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_line_line_3118', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_line_line_3119_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_line_line_3119', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_1979_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_oval_line_1979', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_1980_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_oval_line_1980', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_2212_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_oval_line_2212', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_3111_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_oval_line_3111', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_oval_line_344_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_oval_line_344', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'c_polygon_line_2213', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_image_line_1549', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1538', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1539', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1545', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1563', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1581', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1582', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1784', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_1785', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_2481', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_767_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_767', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_780_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_780', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_781_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_781', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_line_line_784_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_line_line_784', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_oval_line_1216', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_oval_line_1796', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_oval_line_2480', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_oval_line_2482', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_polygon_line_1786', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1113', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1114', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1116', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1117', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1313', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1314', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1315', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1551_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_text_line_1551', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1554_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_text_line_1554', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1555_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_text_line_1555', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_1586_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_text_line_1586', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_766_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_text_line_766', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_text_line_785_text': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_text_line_785', 'text'),
    ],
    'canvas_editor_par_tarzanparpanels_old_canvas_window_line_119_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'canvas_window_line_119', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_dot_oval_line_378_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'dot_oval_line_378', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_led_oval_line_1049_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'led_oval_line_1049', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_led_oval_line_1050_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'led_oval_line_1050', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_rect_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'rect', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'self_rectangle_line_1346', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'self_rectangle_line_1347', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_old_window_id_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels_old', 'window_id', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_self_rectangle_line_185_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'self_rectangle_line_185', 'coords'),
    ],
    'canvas_editor_par_tarzanparpanels_window_id_coords': [
        T('canvas_preview', 'editor_par_tarzanparpanels', 'window_id', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_c_line_line_304_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'c_line_line_304', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_c_oval_line_299_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'c_oval_line_299', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_c_oval_line_300_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'c_oval_line_300', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_c_oval_line_305_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'c_oval_line_305', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_self_oval_line_59_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'self_oval_line_59', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_self_oval_line_60_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'self_oval_line_60', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_self_oval_line_64_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'self_oval_line_64', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_self_oval_line_65_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'self_oval_line_65', 'coords'),
    ],
    'canvas_editor_par_tarzanparwidgets_self_rectangle_line_90_coords': [
        T('canvas_preview', 'editor_par_tarzanparwidgets', 'self_rectangle_line_90', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_826_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_826', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_833_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_833', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_852_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_852', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_859_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_859', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_871_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_871', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_872_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_872', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_886_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_886', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_898_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_898', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_line_line_900_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_line_line_900', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_oval_line_868_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_oval_line_868', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_812_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_rectangle_line_812', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_819_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_rectangle_line_819', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_rectangle_line_880_coords': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_rectangle_line_880', 'coords'),
    ],
    'canvas_editor_tarzanaxissandbox_c_text_line_827_text': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_text_line_827', 'text'),
    ],
    'canvas_editor_tarzanaxissandbox_c_text_line_834_text': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_text_line_834', 'text'),
    ],
    'canvas_editor_tarzanaxissandbox_c_text_line_873_text': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_text_line_873', 'text'),
    ],
    'canvas_editor_tarzanaxissandbox_c_text_line_874_text': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_text_line_874', 'text'),
    ],
    'canvas_editor_tarzanaxissandbox_c_text_line_901_text': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_text_line_901', 'text'),
    ],
    'canvas_editor_tarzanaxissandbox_c_text_line_902_text': [
        T('sandbox_canvas', 'editor_tarzanaxissandbox', 'c_text_line_902', 'text'),
    ],
    'canvas_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'canvas_image_line_553', 'coords'),
    ],
    'canvas_editor_tarzanehrtakesandbox_item_text': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'item', 'text'),
    ],
    'canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1057', 'coords'),
    ],
    'canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1058', 'coords'),
    ],
    'canvas_editor_tarzanehrtakesandbox_protocol_title_id_text': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'protocol_title_id', 'text'),
    ],
    'canvas_editor_tarzanehrtakesandbox_row_window_coords': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'row_window', 'coords'),
    ],
    'canvas_editor_tarzanehrtakesandbox_save_button_window_coords': [
        T('ehr_canvas', 'editor_tarzanehrtakesandbox', 'save_button_window', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_image_line_1518_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_image_line_1518', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_image_line_1533_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_image_line_1533', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_image_line_623_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_image_line_623', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1545_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1545', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1546_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1546', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1555_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1555', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1570_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1570', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1571_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1571', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1593_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1593', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_line_line_1597_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_line_line_1597', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_oval_line_1589_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_oval_line_1589', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_oval_line_1590_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_oval_line_1590', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_polygon_line_1553_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_polygon_line_1553', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_polygon_line_1602_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_polygon_line_1602', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_rectangle_line_1548_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_rectangle_line_1548', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_rectangle_line_1573_coords': [
        T('khr_canvas', 'editor_tarzankhr', 'c_rectangle_line_1573', 'coords'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1457_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1457', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1465_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1465', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1472_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1472', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1473_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1473', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1474_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1474', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1481_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1481', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1486_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1486', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1496_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1496', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1503_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1503', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1520_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1520', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1522_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1522', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1525_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1525', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1542_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1542', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1549_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1549', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1554_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1554', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1556_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1556', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1564_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1564', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1569_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1569', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1574_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1574', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1576_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1576', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1578_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1578', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1579_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1579', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1580_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1580', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1603_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1603', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1604_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1604', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_1605_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_1605', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_615_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_615', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_625_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_625', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_627_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_627', 'text'),
    ],
    'canvas_editor_tarzankhr_c_text_line_629_text': [
        T('khr_canvas', 'editor_tarzankhr', 'c_text_line_629', 'text'),
    ],
    'canvas_editor_tarzantakeprotocollight_canvas_image_line_860_coords': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'canvas_image_line_860', 'coords'),
    ],
    'canvas_editor_tarzantakeprotocollight_item_text': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'item', 'text'),
    ],
    'canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1215', 'coords'),
    ],
    'canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1216', 'coords'),
    ],
    'canvas_editor_tarzantakeprotocollight_protocol_title_id_text': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'protocol_title_id', 'text'),
    ],
    'canvas_editor_tarzantakeprotocollight_row_window_coords': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'row_window', 'coords'),
    ],
    'canvas_editor_tarzantakeprotocollight_save_button_window_coords': [
        T('canvas_preview', 'editor_tarzantakeprotocollight', 'save_button_window', 'coords'),
    ],
    'canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_305_coords': [
        T('canvas_preview', 'mechanics_tarzanedytorchoreografiiruchu', 'c_line_line_305', 'coords'),
    ],
    'canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_313_coords': [
        T('canvas_preview', 'mechanics_tarzanedytorchoreografiiruchu', 'c_line_line_313', 'coords'),
    ],
    'canvas_mechanics_tarzanedytorchoreografiiruchu_c_text_line_314_text': [
        T('canvas_preview', 'mechanics_tarzanedytorchoreografiiruchu', 'c_text_line_314', 'text'),
    ],
    'canvas_mechanics_tarzanedytorchoreografiiruchu_scroll_window_coords': [
        T('canvas_preview', 'mechanics_tarzanedytorchoreografiiruchu', 'scroll_window', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_line_line_1011_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_line_line_1011', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_line_line_1012_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_line_line_1012', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_line_line_754_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_line_line_754', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_line_line_756_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_line_line_756', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_line_line_757_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_line_line_757', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_line_line_770_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_line_line_770', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_oval_line_777_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_oval_line_777', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_polygon_line_1013_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_polygon_line_1013', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_723_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_rectangle_line_723', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_732_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_rectangle_line_732', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_734_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_rectangle_line_734', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_rectangle_line_751_coords': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_rectangle_line_751', 'coords'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_text_line_1014_text': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_text_line_1014', 'text'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_text_line_731_text': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_text_line_731', 'text'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_text_line_735_text': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_text_line_735', 'text'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_text_line_758_text': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_text_line_758', 'text'),
    ],
    'canvas_mechanics_tarzanwykresosi_c_text_line_759_text': [
        T('canvas_preview', 'mechanics_tarzanwykresosi', 'c_text_line_759', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_826', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_833', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_840', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_852', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_853', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_867', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_879', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_line_line_881', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_oval_line_849', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_812', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_819', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_861', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_text_line_827', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_text_line_834', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_text_line_854', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_text_line_855', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_text_line_882', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanaxissandbox', 'c_text_line_883', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_image_line_2734', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1910', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1919', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1930', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1937', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1951', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1952', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1966', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1978', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_1980', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2697', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2707', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2710', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2749', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2757', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2765', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2778', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_line_line_2801', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_oval_line_1947', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_oval_line_2792', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_oval_line_2794', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_polygon_line_2808', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1893', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1901', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1902', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1903', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_1960', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2688', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2705', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2790', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_rectangle_line_2800', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1911_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_1911', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1920_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_1920', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1953_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_1953', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1954_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_1954', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1981_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_1981', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1982_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_1982', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2720_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_2720', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2727_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_2727', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2736_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_2736', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2809_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_2809', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2816_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'c_text_line_2816', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'canvas_image_line_712', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'canvas_rectangle_line_1244', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'canvas_window_line_1172', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_item_text': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'item', 'text'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_962', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_963', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_row_window_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'row_window', 'coords'),
    ],
    'canvas_modes_editor_editor_ehr_tarzanehrui_save_button_window_coords': [
        T('ehr_canvas', 'modes_editor_editor_ehr_tarzanehrui', 'save_button_window', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_826_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_826', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_833_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_833', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_852_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_852', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_859_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_859', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_871_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_871', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_872_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_872', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_886_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_886', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_898_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_898', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_900_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_line_line_900', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_oval_line_868_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_oval_line_868', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_rectangle_line_812', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_rectangle_line_819', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_rectangle_line_880', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_827_text': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_text_line_827', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_834_text': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_text_line_834', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_873_text': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_text_line_873', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_874_text': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_text_line_874', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_901_text': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_text_line_901', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_902_text': [
        T('sandbox_canvas', 'modes_editor_editor_tarzanaxissandbox', 'c_text_line_902', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'canvas_image_line_553', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_item_text': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'item', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1057', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1058', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_title_id_text': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'protocol_title_id', 'text'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_row_window_coords': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'row_window', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzanehrtakesandbox_save_button_window_coords': [
        T('ehr_canvas', 'modes_editor_editor_tarzanehrtakesandbox', 'save_button_window', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'canvas_image_line_860', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_item_text': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'item', 'text'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1215', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1216', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_protocol_title_id_text': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'protocol_title_id', 'text'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_row_window_coords': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'row_window', 'coords'),
    ],
    'canvas_modes_editor_editor_tarzantakeprotocollight_save_button_window_coords': [
        T('canvas_preview', 'modes_editor_editor_tarzantakeprotocollight', 'save_button_window', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_827_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_827', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_834_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_834', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_841_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_841', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_853_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_853', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_854_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_854', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_868_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_868', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_880_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_880', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_882_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_line_line_882', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_oval_line_850', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_813', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_822', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_rectangle_line_862', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_828_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_text_line_828', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_835_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_text_line_835', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_855_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_text_line_855', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_856_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_text_line_856', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_883_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_text_line_883', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_884_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanaxissandbox', 'c_text_line_884', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_image_line_3130_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_image_line_3130', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_1993_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_1993', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2002_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2002', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2013_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2013', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2020_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2020', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2048_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2048', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2049_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2049', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2068_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2068', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2080_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2080', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_2082_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_2082', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3081_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3081', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3102_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3102', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3105_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3105', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3145_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3145', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3153_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3153', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3161_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3161', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3176_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3176', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3217_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3217', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_line_line_3231_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_line_line_3231', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_2044_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_oval_line_2044', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3194_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_oval_line_3194', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3210_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_oval_line_3210', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_polygon_line_3226_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_polygon_line_3226', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_1976', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_1984', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_1985', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_1986', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_2062', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_3072', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_3100', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_3192', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_rectangle_line_3216', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_1994_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_1994', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2003_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_2003', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2050_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_2050', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2051_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_2051', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2083_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_2083', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_2084_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_2084', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3115_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_3115', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3122_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_3122', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3132_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_3132', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3228_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_3228', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_c_text_line_3239_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'c_text_line_3239', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_canvas_image_line_760_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'canvas_image_line_760', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'canvas_rectangle_line_1300', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_canvas_window_line_1226_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'canvas_window_line_1226', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_item_text': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'item', 'text'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_1010', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'protocol_canvas_rectangle_line_1011', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_row_window_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'row_window', 'coords'),
    ],
    'canvas_modes_editor_ehr_tarzanehrui_save_button_window_coords': [
        T('ehr_canvas', 'modes_editor_ehr_tarzanehrui', 'save_button_window', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_edit_window_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', '_edit_window', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_image_line_591', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_image_line_623', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_image_line_640', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_image_line_692', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_image_line_718', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_line_line_415', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_line_line_432', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_line_line_445', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_line_line_737', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_line_line_738', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_line_line_818', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_oval_line_740', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_394', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_512', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_527', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_593', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_625', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_642', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_785', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_787', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_790', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_797', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_rectangle_line_815', 'coords'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_400', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_414', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_421', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_425', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_466', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_483', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_518', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_529', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_594', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_603', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_626', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_643', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_791', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_798', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_799', 'text'),
    ],
    'canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text': [
        T('canvas_preview', 'modes_editor_par_tarzannextionpreview', 'screen_canvas_text_line_816', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1309_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_oval_line_1309', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1402_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_oval_line_1402', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1286', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1303', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1314', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1315', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1316', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1329', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1387', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1414', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1415', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1416', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_rectangle_line_1431', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1310_text': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_text_line_1310', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1434_text': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_text_line_1434', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1451_text': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_text_line_1451', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparapp_canvas_text_line_1455_text': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'canvas_text_line_1455', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparapp_led_oval_line_485_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'led_oval_line_485', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'panel_canvas_window_line_1076', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparapp_text_id_text': [
        T('layout_canvas', 'modes_editor_par_tarzanparapp', 'text_id', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_image_line_1306_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_image_line_1306', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1298_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_1298', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1299_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_1299', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1304_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_1304', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1311_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_1311', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1326_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_1326', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_1327_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_1327', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_510_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_510', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_664_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_664', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_line_line_665_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_line_line_665', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_509_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_oval_line_509', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_511_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_oval_line_511', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_656_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_oval_line_656', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_oval_line_920_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_oval_line_920', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_polygon_line_921_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_polygon_line_921', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_899_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_rectangle_line_899', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_901_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_rectangle_line_901', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1307_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_text_line_1307', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1309_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_text_line_1309', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1310_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_text_line_1310', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1329_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_text_line_1329', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_can_text_line_1331_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'can_text_line_1331', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_line_line_825_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_line_line_825', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_line_line_826_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_line_line_826', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_1575_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_oval_line_1575', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_830_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_oval_line_830', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_polygon_line_828_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_polygon_line_828', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_rectangle_line_1449', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_rectangle_line_1450', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'canvas_rectangle_line_1451', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3118_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_line_line_3118', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3119_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_line_line_3119', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1979_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_oval_line_1979', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1980_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_oval_line_1980', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_2212_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_oval_line_2212', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_3111_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_oval_line_3111', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_344_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_oval_line_344', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'c_polygon_line_2213', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_image_line_1549', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1538', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1539', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1545', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1563', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1581', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1582', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1784', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_1785', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_2481', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_767_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_767', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_780_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_780', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_781_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_781', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_784_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_line_line_784', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_oval_line_1216', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_oval_line_1796', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_oval_line_2480', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_oval_line_2482', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_polygon_line_1786', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1113', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1114', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1116', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1117', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1313', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1314', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_rectangle_line_1315', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1551_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_text_line_1551', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1554_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_text_line_1554', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1555_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_text_line_1555', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1586_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_text_line_1586', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_766_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_text_line_766', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_785_text': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_text_line_785', 'text'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_canvas_window_line_119_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'canvas_window_line_119', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_dot_oval_line_378_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'dot_oval_line_378', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1049_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'led_oval_line_1049', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1050_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'led_oval_line_1050', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_rect_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'rect', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'self_rectangle_line_1346', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'self_rectangle_line_1347', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_old_window_id_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels_old', 'window_id', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_self_rectangle_line_185_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'self_rectangle_line_185', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparpanels_window_id_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparpanels', 'window_id', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_c_line_line_304_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'c_line_line_304', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_299_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'c_oval_line_299', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_300_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'c_oval_line_300', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_c_oval_line_305_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'c_oval_line_305', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_59_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'self_oval_line_59', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_60_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'self_oval_line_60', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_64_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'self_oval_line_64', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_self_oval_line_65_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'self_oval_line_65', 'coords'),
    ],
    'canvas_modes_editor_par_tarzanparwidgets_self_rectangle_line_90_coords': [
        T('canvas_preview', 'modes_editor_par_tarzanparwidgets', 'self_rectangle_line_90', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_826_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_826', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_833_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_833', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_852_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_852', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_859_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_859', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_871_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_871', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_872_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_872', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_886_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_886', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_898_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_898', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_line_line_900_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_line_line_900', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_oval_line_868_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_oval_line_868', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_812_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_rectangle_line_812', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_819_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_rectangle_line_819', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_820_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_rectangle_line_820', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_821_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_rectangle_line_821', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_880_coords': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_rectangle_line_880', 'coords'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_827_text': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_text_line_827', 'text'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_834_text': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_text_line_834', 'text'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_873_text': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_text_line_873', 'text'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_874_text': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_text_line_874', 'text'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_901_text': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_text_line_901', 'text'),
    ],
    'canvas_modes_editor_tarzanaxissandbox_c_text_line_902_text': [
        T('sandbox_canvas', 'modes_editor_tarzanaxissandbox', 'c_text_line_902', 'text'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_canvas_image_line_553_coords': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'canvas_image_line_553', 'coords'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_item_text': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'item', 'text'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1057', 'coords'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'protocol_canvas_rectangle_line_1058', 'coords'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_protocol_title_id_text': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'protocol_title_id', 'text'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_row_window_coords': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'row_window', 'coords'),
    ],
    'canvas_modes_editor_tarzanehrtakesandbox_save_button_window_coords': [
        T('ehr_canvas', 'modes_editor_tarzanehrtakesandbox', 'save_button_window', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_image_line_1518_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_image_line_1518', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_image_line_1533_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_image_line_1533', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_image_line_623_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_image_line_623', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1545_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1545', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1546_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1546', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1555_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1555', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1570_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1570', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1571_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1571', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1593_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1593', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_line_line_1597_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_line_line_1597', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_oval_line_1589_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_oval_line_1589', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_oval_line_1590_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_oval_line_1590', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_polygon_line_1553_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_polygon_line_1553', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_polygon_line_1602_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_polygon_line_1602', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_rectangle_line_1548_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_rectangle_line_1548', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_rectangle_line_1573_coords': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_rectangle_line_1573', 'coords'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1457_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1457', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1465_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1465', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1472_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1472', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1473_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1473', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1474_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1474', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1481_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1481', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1486_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1486', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1496_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1496', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1503_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1503', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1520_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1520', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1522_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1522', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1525_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1525', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1542_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1542', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1549_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1549', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1554_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1554', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1556_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1556', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1564_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1564', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1569_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1569', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1574_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1574', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1576_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1576', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1578_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1578', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1579_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1579', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1580_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1580', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1603_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1603', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1604_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1604', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_1605_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_1605', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_615_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_615', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_625_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_625', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_627_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_627', 'text'),
    ],
    'canvas_modes_editor_tarzankhr_c_text_line_629_text': [
        T('khr_canvas', 'modes_editor_tarzankhr', 'c_text_line_629', 'text'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_canvas_image_line_860_coords': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'canvas_image_line_860', 'coords'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_item_text': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'item', 'text'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1215', 'coords'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'protocol_canvas_rectangle_line_1216', 'coords'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_protocol_title_id_text': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'protocol_title_id', 'text'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_row_window_coords': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'row_window', 'coords'),
    ],
    'canvas_modes_editor_tarzantakeprotocollight_save_button_window_coords': [
        T('canvas_preview', 'modes_editor_tarzantakeprotocollight', 'save_button_window', 'coords'),
    ],
    'canvas_vision_tarzanvisionsetup_window_id_coords': [
        T('canvas_preview', 'vision_tarzanvisionsetup', 'window_id', 'coords'),
    ],
}


# =============================================================================
# KATALOGI ŹRÓDŁOWE — DO DOKUMENTACJI I WALIDACJI
# =============================================================================

NEXTION_HMI_TARGET_CATALOG = [
    {
        "page": "rrp_main",
        "component": "va_p1_axis",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 54
    },
    {
        "page": "rrp_main",
        "component": "va_p2_axis",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 60
    },
    {
        "page": "rrp_main",
        "component": "va_tmp",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 66
    },
    {
        "page": "rrp_main",
        "component": "va_p2_dir",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 72
    },
    {
        "page": "rrp_main",
        "component": "va_p1_dir",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 78
    },
    {
        "page": "rrp_main",
        "component": "va_p1_val",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 84
    },
    {
        "page": "rrp_main",
        "component": "va_p2_val",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 90
    },
    {
        "page": "rrp_main",
        "component": "t_p1_val",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "rrp_main.txt",
        "line": 96
    },
    {
        "page": "rrp_main",
        "component": "t_p2_val",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "rrp_main.txt",
        "line": 118
    },
    {
        "page": "rrp_main",
        "component": "t_buf_p1",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "rrp_main.txt",
        "line": 140
    },
    {
        "page": "rrp_main",
        "component": "t_buf_p2",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "rrp_main.txt",
        "line": 164
    },
    {
        "page": "rrp_main",
        "component": "h_p1_sens",
        "type": "Slider",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 188
    },
    {
        "page": "rrp_main",
        "component": "h_p2_sens",
        "type": "Slider",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 214
    },
    {
        "page": "rrp_main",
        "component": "b_home",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "rrp_main.txt",
        "line": 240
    },
    {
        "page": "rrp_main",
        "component": "b_stop",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "rrp_main.txt",
        "line": 271
    },
    {
        "page": "rrp_main",
        "component": "b_p1_cam_v",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 338
    },
    {
        "page": "rrp_main",
        "component": "b_p2_cam_v",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 391
    },
    {
        "page": "rrp_main",
        "component": "b_p1_dir",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 444
    },
    {
        "page": "rrp_main",
        "component": "b_p2_dir",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 479
    },
    {
        "page": "rrp_main",
        "component": "b_p1_cam_t",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 514
    },
    {
        "page": "rrp_main",
        "component": "b_p1_cam_f",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 567
    },
    {
        "page": "rrp_main",
        "component": "b_p1_cam_h",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 620
    },
    {
        "page": "rrp_main",
        "component": "b_p1_arm_h",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 673
    },
    {
        "page": "rrp_main",
        "component": "b_p1_arm_v",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 726
    },
    {
        "page": "rrp_main",
        "component": "b_p2_cam_t",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 779
    },
    {
        "page": "rrp_main",
        "component": "b_p2_cam_f",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 832
    },
    {
        "page": "rrp_main",
        "component": "b_p2_cam_h",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 885
    },
    {
        "page": "rrp_main",
        "component": "b_p2_arm_h",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 938
    },
    {
        "page": "rrp_main",
        "component": "b_p2_arm_v",
        "type": "Dual-state Button",
        "props": [
            "val"
        ],
        "source": "rrp_main.txt",
        "line": 991
    },
    {
        "page": "take_main",
        "component": "t_axis0",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 15
    },
    {
        "page": "take_main",
        "component": "t_axis1",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 39
    },
    {
        "page": "take_main",
        "component": "t_axis3",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 63
    },
    {
        "page": "take_main",
        "component": "t_axis2",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 87
    },
    {
        "page": "take_main",
        "component": "t_axis4",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 111
    },
    {
        "page": "take_main",
        "component": "t_axis5",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 135
    },
    {
        "page": "take_main",
        "component": "t_take",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 159
    },
    {
        "page": "take_main",
        "component": "t_clap",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 183
    },
    {
        "page": "take_main",
        "component": "t_laser",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 207
    },
    {
        "page": "take_main",
        "component": "t_limits",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 231
    },
    {
        "page": "take_main",
        "component": "t_status",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 255
    },
    {
        "page": "take_main",
        "component": "t_shock",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 279
    },
    {
        "page": "take_main",
        "component": "t_light",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 303
    },
    {
        "page": "take_main",
        "component": "t_temp",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 327
    },
    {
        "page": "take_main",
        "component": "t_xyz",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 351
    },
    {
        "page": "take_main",
        "component": "t0",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 375
    },
    {
        "page": "take_main",
        "component": "t1",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 399
    },
    {
        "page": "take_main",
        "component": "t2",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "take_main.txt",
        "line": 423
    },
    {
        "page": "take_main",
        "component": "p_axis0",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 447
    },
    {
        "page": "take_main",
        "component": "p_axis1",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 458
    },
    {
        "page": "take_main",
        "component": "p_axis5",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 469
    },
    {
        "page": "take_main",
        "component": "p_axis3",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 480
    },
    {
        "page": "take_main",
        "component": "p_axis2",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 491
    },
    {
        "page": "take_main",
        "component": "p_axis4",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 502
    },
    {
        "page": "take_main",
        "component": "p_laser",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 513
    },
    {
        "page": "take_main",
        "component": "p_limits",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 524
    },
    {
        "page": "take_main",
        "component": "p_light",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 535
    },
    {
        "page": "take_main",
        "component": "p_shock",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 546
    },
    {
        "page": "take_main",
        "component": "p_temp",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 557
    },
    {
        "page": "take_main",
        "component": "p_xyz",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "take_main.txt",
        "line": 568
    },
    {
        "page": "take_main",
        "component": "b_home",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "take_main.txt",
        "line": 579
    },
    {
        "page": "take_main",
        "component": "b_clap",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "take_main.txt",
        "line": 610
    },
    {
        "page": "settings_main",
        "component": "t_title",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "settings_main.txt",
        "line": 16
    },
    {
        "page": "settings_main",
        "component": "t_director",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "settings_main.txt",
        "line": 40
    },
    {
        "page": "settings_main",
        "component": "t_save_status",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "settings_main.txt",
        "line": 64
    },
    {
        "page": "settings_main",
        "component": "b_home",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "settings_main.txt",
        "line": 100
    },
    {
        "page": "settings_main",
        "component": "b_save_meta",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "settings_main.txt",
        "line": 131
    },
    {
        "page": "level_xyz",
        "component": "va0",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "level_xyz.txt",
        "line": 21
    },
    {
        "page": "level_xyz",
        "component": "va1",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "level_xyz.txt",
        "line": 27
    },
    {
        "page": "level_xyz",
        "component": "va2",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "level_xyz.txt",
        "line": 33
    },
    {
        "page": "level_xyz",
        "component": "va3",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "level_xyz.txt",
        "line": 39
    },
    {
        "page": "level_xyz",
        "component": "p0",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "level_xyz.txt",
        "line": 45
    },
    {
        "page": "level_xyz",
        "component": "b_home",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "level_xyz.txt",
        "line": 56
    },
    {
        "page": "level_xyz",
        "component": "tm0",
        "type": "Timer",
        "props": [
            "en",
            "tim"
        ],
        "source": "level_xyz.txt",
        "line": 87
    },
    {
        "page": "level_xyz",
        "component": "Event",
        "type": "Timer",
        "props": [
            "en",
            "tim"
        ],
        "source": "level_xyz.txt",
        "line": 95
    },
    {
        "page": "page1",
        "component": "b_face",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "page1.txt",
        "line": 15
    },
    {
        "page": "page1",
        "component": "b_level",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "page1.txt",
        "line": 42
    },
    {
        "page": "page1",
        "component": "b_rrp",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "page1.txt",
        "line": 69
    },
    {
        "page": "page1",
        "component": "b_sensors",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "page1.txt",
        "line": 96
    },
    {
        "page": "page1",
        "component": "b_settings",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "page1.txt",
        "line": 123
    },
    {
        "page": "page1",
        "component": "b_take",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "page1.txt",
        "line": 150
    },
    {
        "page": "boot",
        "component": "va0",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "boot.txt",
        "line": 22
    },
    {
        "page": "boot",
        "component": "p0",
        "type": "Picture",
        "props": [
            "pic"
        ],
        "source": "boot.txt",
        "line": 28
    },
    {
        "page": "boot",
        "component": "tm0",
        "type": "Timer",
        "props": [
            "en",
            "tim"
        ],
        "source": "boot.txt",
        "line": 46
    },
    {
        "page": "boot",
        "component": "Event",
        "type": "Timer",
        "props": [
            "en",
            "tim"
        ],
        "source": "boot.txt",
        "line": 54
    },
    {
        "page": "sensors_main",
        "component": "t0",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "sensors_main.txt",
        "line": 15
    },
    {
        "page": "sensors_main",
        "component": "b_home",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "sensors_main.txt",
        "line": 39
    },
    {
        "page": "face_rec",
        "component": "t0",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "face_rec.txt",
        "line": 15
    },
    {
        "page": "face_rec",
        "component": "b_home",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "face_rec.txt",
        "line": 39
    },
    {
        "page": "keybdA",
        "component": "loadpageid",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "keybdA.txt",
        "line": 58
    },
    {
        "page": "keybdA",
        "component": "loadcmpid",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "keybdA.txt",
        "line": 64
    },
    {
        "page": "keybdA",
        "component": "input",
        "type": "Variable (string)",
        "props": [
            "txt"
        ],
        "source": "keybdA.txt",
        "line": 70
    },
    {
        "page": "keybdA",
        "component": "temp",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "keybdA.txt",
        "line": 77
    },
    {
        "page": "keybdA",
        "component": "inputlenth",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "keybdA.txt",
        "line": 83
    },
    {
        "page": "keybdA",
        "component": "temp2",
        "type": "Variable (int32)",
        "props": [
            "val"
        ],
        "source": "keybdA.txt",
        "line": 89
    },
    {
        "page": "keybdA",
        "component": "tempstr",
        "type": "Variable (string)",
        "props": [
            "txt"
        ],
        "source": "keybdA.txt",
        "line": 95
    },
    {
        "page": "keybdA",
        "component": "show",
        "type": "Text",
        "props": [
            "txt"
        ],
        "source": "keybdA.txt",
        "line": 102
    },
    {
        "page": "keybdA",
        "component": "b0",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 126
    },
    {
        "page": "keybdA",
        "component": "b251",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 163
    },
    {
        "page": "keybdA",
        "component": "b210",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 193
    },
    {
        "page": "keybdA",
        "component": "b1",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 271
    },
    {
        "page": "keybdA",
        "component": "b2",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 308
    },
    {
        "page": "keybdA",
        "component": "b3",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 345
    },
    {
        "page": "keybdA",
        "component": "b4",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 382
    },
    {
        "page": "keybdA",
        "component": "b5",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 419
    },
    {
        "page": "keybdA",
        "component": "b6",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 456
    },
    {
        "page": "keybdA",
        "component": "b7",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 493
    },
    {
        "page": "keybdA",
        "component": "b8",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 530
    },
    {
        "page": "keybdA",
        "component": "b200",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 567
    },
    {
        "page": "keybdA",
        "component": "b20",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 600
    },
    {
        "page": "keybdA",
        "component": "b21",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 637
    },
    {
        "page": "keybdA",
        "component": "b22",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 674
    },
    {
        "page": "keybdA",
        "component": "b23",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 711
    },
    {
        "page": "keybdA",
        "component": "b24",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 748
    },
    {
        "page": "keybdA",
        "component": "b25",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 785
    },
    {
        "page": "keybdA",
        "component": "b26",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 822
    },
    {
        "page": "keybdA",
        "component": "b27",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 859
    },
    {
        "page": "keybdA",
        "component": "b28",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 896
    },
    {
        "page": "keybdA",
        "component": "b220",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 933
    },
    {
        "page": "keybdA",
        "component": "b40",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 979
    },
    {
        "page": "keybdA",
        "component": "b41",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1016
    },
    {
        "page": "keybdA",
        "component": "b42",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1053
    },
    {
        "page": "keybdA",
        "component": "b43",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1090
    },
    {
        "page": "keybdA",
        "component": "b44",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1127
    },
    {
        "page": "keybdA",
        "component": "b45",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1164
    },
    {
        "page": "keybdA",
        "component": "b46",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1201
    },
    {
        "page": "keybdA",
        "component": "b230",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1238
    },
    {
        "page": "keybdA",
        "component": "b240",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1275
    },
    {
        "page": "keybdA",
        "component": "b242",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1316
    },
    {
        "page": "keybdA",
        "component": "b241",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1353
    },
    {
        "page": "keybdA",
        "component": "b243",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1390
    },
    {
        "page": "keybdA",
        "component": "b231",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1427
    },
    {
        "page": "keybdA",
        "component": "b244",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1464
    },
    {
        "page": "keybdA",
        "component": "b249",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1501
    },
    {
        "page": "keybdA",
        "component": "b201",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1537
    },
    {
        "page": "keybdA",
        "component": "b9",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1574
    },
    {
        "page": "keybdA",
        "component": "b232",
        "type": "Button",
        "props": [
            "val",
            "pic"
        ],
        "source": "keybdA.txt",
        "line": 1611
    },
    {
        "page": "keybdA",
        "component": "refshow",
        "type": "Hotspot",
        "props": [
            "state"
        ],
        "source": "keybdA.txt",
        "line": 1648
    },
    {
        "page": "keybdA",
        "component": "tm0",
        "type": "Timer",
        "props": [
            "en",
            "tim"
        ],
        "source": "keybdA.txt",
        "line": 1742
    },
    {
        "page": "keybdA",
        "component": "Event",
        "type": "Timer",
        "props": [
            "en",
            "tim"
        ],
        "source": "keybdA.txt",
        "line": 1750
    }
]

PYTHON_TKINTER_TARGET_CATALOG = [
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 565,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 573,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 727,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 794,
        "widget": "save_button",
        "type": "Button",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 952,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 956,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 967,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1512,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1520,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2587,
        "widget": "take_panel",
        "type": "Frame",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2600,
        "widget": "left",
        "type": "Frame",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2608,
        "widget": "timeline_canvas",
        "type": "Canvas",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2617,
        "widget": "status",
        "type": "Label",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2625,
        "widget": "selected_point_time_label",
        "type": "Label",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2636,
        "widget": "axis_info_label",
        "type": "Label",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2641,
        "widget": "protocol_label",
        "type": "Label",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2645,
        "widget": "protocol_box",
        "type": "Frame",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2647,
        "widget": "protocol_text",
        "type": "Text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 165,
        "widget": "page_label",
        "type": "Label",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 168,
        "widget": "screen_frame",
        "type": "Frame",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 171,
        "widget": "screen_canvas",
        "type": "Canvas",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 186,
        "widget": "status",
        "type": "Label",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 466,
        "widget": "header",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 468,
        "widget": "body",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 470,
        "widget": "footer",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 474,
        "widget": "mode_label",
        "type": "Label",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 490,
        "widget": "layout_master",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 493,
        "widget": "left",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 494,
        "widget": "top",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 495,
        "widget": "middle_top",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 496,
        "widget": "middle_bottom",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 497,
        "widget": "bottom",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 498,
        "widget": "right",
        "type": "Frame",
        "scope": "editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 506,
        "widget": "clock",
        "type": "Label",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1242,
        "widget": "timeline_canvas",
        "type": "Canvas",
        "scope": "editor_par_tarzanparpanels",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1738,
        "widget": "log_text",
        "type": "Text",
        "scope": "editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 447,
        "widget": "log_text",
        "type": "Text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 103,
        "widget": "body",
        "type": "Frame",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "state"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 220,
        "widget": "counter_label",
        "type": "Label",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 224,
        "widget": "motor_canvas",
        "type": "Canvas",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "state"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 521,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 583,
        "widget": "save_button",
        "type": "Button",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 708,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 712,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 724,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 727,
        "widget": "controls_wrap",
        "type": "Frame",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 822,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 905,
        "widget": "save_button",
        "type": "Button",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1111,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1115,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1134,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 564,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 572,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 679,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 746,
        "widget": "save_button",
        "type": "Button",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 904,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 908,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 919,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1450,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1458,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2241,
        "widget": "take_panel",
        "type": "Frame",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2254,
        "widget": "left",
        "type": "Frame",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2262,
        "widget": "timeline_canvas",
        "type": "Canvas",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2271,
        "widget": "status",
        "type": "Label",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2278,
        "widget": "axis_info_label",
        "type": "Label",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2283,
        "widget": "protocol_label",
        "type": "Label",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2287,
        "widget": "protocol_box",
        "type": "Frame",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2289,
        "widget": "protocol_text",
        "type": "Text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 521,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 583,
        "widget": "save_button",
        "type": "Button",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 708,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 712,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 724,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 727,
        "widget": "controls_wrap",
        "type": "Frame",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 822,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 905,
        "widget": "save_button",
        "type": "Button",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1111,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1115,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1134,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 564,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 572,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 564,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 572,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 259,
        "widget": "preview_canvas",
        "type": "Canvas",
        "scope": "editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 262,
        "widget": "status",
        "type": "Label",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 777,
        "widget": "profile_box",
        "type": "Combobox",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 782,
        "widget": "plugin_box",
        "type": "Combobox",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 793,
        "widget": "btn_start",
        "type": "Button",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 795,
        "widget": "btn_stop",
        "type": "Button",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 810,
        "widget": "input_canvas",
        "type": "Canvas",
        "scope": "editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 813,
        "widget": "khr_canvas",
        "type": "Canvas",
        "scope": "editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 815,
        "widget": "output_canvas",
        "type": "Canvas",
        "scope": "editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 821,
        "widget": "profile_desc",
        "type": "Label",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "hardware/tarzanNextion/tarzanNextionSandbox.py",
        "line": 122,
        "widget": "log",
        "type": "Text",
        "scope": "hardware_tarzannextion_tarzannextionsandbox",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 95,
        "widget": "global_canvas",
        "type": "Canvas",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 102,
        "widget": "scroll_canvas",
        "type": "Canvas",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 109,
        "widget": "tracks_frame",
        "type": "Frame",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanPanelOsi.py",
        "line": 27,
        "widget": "row1",
        "type": "Frame",
        "scope": "mechanics_tarzanpanelosi",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanPanelOsi.py",
        "line": 30,
        "widget": "row2",
        "type": "Frame",
        "scope": "mechanics_tarzanpanelosi",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanPanelOsi.py",
        "line": 33,
        "widget": "row3",
        "type": "Frame",
        "scope": "mechanics_tarzanpanelosi",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 311,
        "widget": "limit_panel",
        "type": "Frame",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 315,
        "widget": "limit_canvas",
        "type": "Canvas",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "state"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 321,
        "widget": "title",
        "type": "Label",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 332,
        "widget": "meta_label",
        "type": "Label",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 343,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 565,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 573,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 727,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 794,
        "widget": "save_button",
        "type": "Button",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 952,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 956,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 967,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1512,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1520,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2587,
        "widget": "take_panel",
        "type": "Frame",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2600,
        "widget": "left",
        "type": "Frame",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2608,
        "widget": "timeline_canvas",
        "type": "Canvas",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2617,
        "widget": "status",
        "type": "Label",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2625,
        "widget": "selected_point_time_label",
        "type": "Label",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2636,
        "widget": "axis_info_label",
        "type": "Label",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2641,
        "widget": "protocol_label",
        "type": "Label",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2645,
        "widget": "protocol_box",
        "type": "Frame",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2647,
        "widget": "protocol_text",
        "type": "Text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 165,
        "widget": "page_label",
        "type": "Label",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 168,
        "widget": "screen_frame",
        "type": "Frame",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 171,
        "widget": "screen_canvas",
        "type": "Canvas",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 186,
        "widget": "status",
        "type": "Label",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 466,
        "widget": "header",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 468,
        "widget": "body",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 470,
        "widget": "footer",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 474,
        "widget": "mode_label",
        "type": "Label",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 490,
        "widget": "layout_master",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 493,
        "widget": "left",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 494,
        "widget": "top",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 495,
        "widget": "middle_top",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 496,
        "widget": "middle_bottom",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 497,
        "widget": "bottom",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 498,
        "widget": "right",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 506,
        "widget": "clock",
        "type": "Label",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1242,
        "widget": "timeline_canvas",
        "type": "Canvas",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1738,
        "widget": "log_text",
        "type": "Text",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 447,
        "widget": "log_text",
        "type": "Text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 103,
        "widget": "body",
        "type": "Frame",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "state"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 220,
        "widget": "counter_label",
        "type": "Label",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 224,
        "widget": "motor_canvas",
        "type": "Canvas",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 521,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 583,
        "widget": "save_button",
        "type": "Button",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 708,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 712,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 724,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 727,
        "widget": "controls_wrap",
        "type": "Frame",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 822,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 905,
        "widget": "save_button",
        "type": "Button",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1111,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1115,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1134,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 564,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 572,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 679,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 746,
        "widget": "save_button",
        "type": "Button",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 904,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 908,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 919,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1450,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1458,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2241,
        "widget": "take_panel",
        "type": "Frame",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2254,
        "widget": "left",
        "type": "Frame",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2262,
        "widget": "timeline_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2271,
        "widget": "status",
        "type": "Label",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2278,
        "widget": "axis_info_label",
        "type": "Label",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2283,
        "widget": "protocol_label",
        "type": "Label",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2287,
        "widget": "protocol_box",
        "type": "Frame",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2289,
        "widget": "protocol_text",
        "type": "Text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 521,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 583,
        "widget": "save_button",
        "type": "Button",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 708,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 712,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 724,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 727,
        "widget": "controls_wrap",
        "type": "Frame",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 822,
        "widget": "canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 905,
        "widget": "save_button",
        "type": "Button",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1111,
        "widget": "protocol_holder",
        "type": "Frame",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1115,
        "widget": "protocol_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1134,
        "widget": "row_frame",
        "type": "Frame",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 564,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 572,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 564,
        "widget": "curve_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 572,
        "widget": "step_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 259,
        "widget": "preview_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 262,
        "widget": "status",
        "type": "Label",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 777,
        "widget": "profile_box",
        "type": "Combobox",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 782,
        "widget": "plugin_box",
        "type": "Combobox",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 793,
        "widget": "btn_start",
        "type": "Button",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 795,
        "widget": "btn_stop",
        "type": "Button",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 810,
        "widget": "input_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 813,
        "widget": "khr_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 815,
        "widget": "output_canvas",
        "type": "Canvas",
        "scope": "modes_editor_tarzankhr",
        "prop": "state"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 821,
        "widget": "profile_desc",
        "type": "Label",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/hardware/tarzanNextion/tarzanNextionSandbox.py",
        "line": 122,
        "widget": "log",
        "type": "Text",
        "scope": "modes_hardware_tarzannextion_tarzannextionsandbox",
        "prop": "text"
    },
    {
        "file": "vision/tarzanVisionSetup.py",
        "line": 247,
        "widget": "content",
        "type": "Frame",
        "scope": "vision_tarzanvisionsetup",
        "prop": "state"
    }
]

PYTHON_CANVAS_TARGET_CATALOG = [
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 813,
        "item": "c_rectangle_line_813",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 822,
        "item": "c_rectangle_line_822",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_line_line_827",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 828,
        "item": "c_text_line_828",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_line_line_834",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 835,
        "item": "c_text_line_835",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 841,
        "item": "c_line_line_841",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 850,
        "item": "c_oval_line_850",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 853,
        "item": "c_line_line_853",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 854,
        "item": "c_line_line_854",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 855,
        "item": "c_text_line_855",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 856,
        "item": "c_text_line_856",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 862,
        "item": "c_rectangle_line_862",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 868,
        "item": "c_line_line_868",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 880,
        "item": "c_line_line_880",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 882,
        "item": "c_line_line_882",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 883,
        "item": "c_text_line_883",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 884,
        "item": "c_text_line_884",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 760,
        "item": "canvas_image_line_760",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 775,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 810,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 968,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1010,
        "item": "protocol_canvas_rectangle_line_1010",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1011,
        "item": "protocol_canvas_rectangle_line_1011",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1226,
        "item": "canvas_window_line_1226",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1300,
        "item": "canvas_rectangle_line_1300",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1976,
        "item": "c_rectangle_line_1976",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1984,
        "item": "c_rectangle_line_1984",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1985,
        "item": "c_rectangle_line_1985",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1986,
        "item": "c_rectangle_line_1986",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1993,
        "item": "c_line_line_1993",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1994,
        "item": "c_text_line_1994",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2002,
        "item": "c_line_line_2002",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2003,
        "item": "c_text_line_2003",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2013,
        "item": "c_line_line_2013",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2020,
        "item": "c_line_line_2020",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2044,
        "item": "c_oval_line_2044",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2048,
        "item": "c_line_line_2048",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2049,
        "item": "c_line_line_2049",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2050,
        "item": "c_text_line_2050",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2051,
        "item": "c_text_line_2051",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2062,
        "item": "c_rectangle_line_2062",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2068,
        "item": "c_line_line_2068",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2080,
        "item": "c_line_line_2080",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2082,
        "item": "c_line_line_2082",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2083,
        "item": "c_text_line_2083",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2084,
        "item": "c_text_line_2084",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3072,
        "item": "c_rectangle_line_3072",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3081,
        "item": "c_line_line_3081",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3100,
        "item": "c_rectangle_line_3100",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3102,
        "item": "c_line_line_3102",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3105,
        "item": "c_line_line_3105",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3115,
        "item": "c_text_line_3115",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3122,
        "item": "c_text_line_3122",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3130,
        "item": "c_image_line_3130",
        "canvas": "c",
        "type": "image",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3132,
        "item": "c_text_line_3132",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3145,
        "item": "c_line_line_3145",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3153,
        "item": "c_line_line_3153",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3161,
        "item": "c_line_line_3161",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3176,
        "item": "c_line_line_3176",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3192,
        "item": "c_rectangle_line_3192",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3194,
        "item": "c_oval_line_3194",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3210,
        "item": "c_oval_line_3210",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3216,
        "item": "c_rectangle_line_3216",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3217,
        "item": "c_line_line_3217",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3226,
        "item": "c_polygon_line_3226",
        "canvas": "c",
        "type": "polygon",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3228,
        "item": "c_text_line_3228",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3231,
        "item": "c_line_line_3231",
        "canvas": "c",
        "type": "line",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3239,
        "item": "c_text_line_3239",
        "canvas": "c",
        "type": "text",
        "scope": "editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 394,
        "item": "screen_canvas_rectangle_line_394",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 400,
        "item": "screen_canvas_text_line_400",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 414,
        "item": "screen_canvas_text_line_414",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 415,
        "item": "screen_canvas_line_line_415",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 421,
        "item": "screen_canvas_text_line_421",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 425,
        "item": "screen_canvas_text_line_425",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 432,
        "item": "screen_canvas_line_line_432",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 445,
        "item": "screen_canvas_line_line_445",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 466,
        "item": "screen_canvas_text_line_466",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 483,
        "item": "screen_canvas_text_line_483",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 512,
        "item": "screen_canvas_rectangle_line_512",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 518,
        "item": "screen_canvas_text_line_518",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 527,
        "item": "screen_canvas_rectangle_line_527",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 529,
        "item": "screen_canvas_text_line_529",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 591,
        "item": "screen_canvas_image_line_591",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 593,
        "item": "screen_canvas_rectangle_line_593",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 594,
        "item": "screen_canvas_text_line_594",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 603,
        "item": "screen_canvas_text_line_603",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 623,
        "item": "screen_canvas_image_line_623",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 625,
        "item": "screen_canvas_rectangle_line_625",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 626,
        "item": "screen_canvas_text_line_626",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 640,
        "item": "screen_canvas_image_line_640",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 642,
        "item": "screen_canvas_rectangle_line_642",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 643,
        "item": "screen_canvas_text_line_643",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 692,
        "item": "screen_canvas_image_line_692",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 718,
        "item": "screen_canvas_image_line_718",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 737,
        "item": "screen_canvas_line_line_737",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 738,
        "item": "screen_canvas_line_line_738",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 740,
        "item": "screen_canvas_oval_line_740",
        "canvas": "screen_canvas",
        "type": "oval",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 785,
        "item": "screen_canvas_rectangle_line_785",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 787,
        "item": "screen_canvas_rectangle_line_787",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 790,
        "item": "screen_canvas_rectangle_line_790",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 791,
        "item": "screen_canvas_text_line_791",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 797,
        "item": "screen_canvas_rectangle_line_797",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 798,
        "item": "screen_canvas_text_line_798",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 799,
        "item": "screen_canvas_text_line_799",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 815,
        "item": "screen_canvas_rectangle_line_815",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 816,
        "item": "screen_canvas_text_line_816",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 818,
        "item": "screen_canvas_line_line_818",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 1063,
        "item": "_edit_window",
        "canvas": "screen_canvas",
        "type": "window",
        "scope": "editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 485,
        "item": "led_oval_line_485",
        "canvas": "led",
        "type": "oval",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1076,
        "item": "panel_canvas_window_line_1076",
        "canvas": "panel_canvas",
        "type": "window",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1286,
        "item": "canvas_rectangle_line_1286",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1303,
        "item": "canvas_rectangle_line_1303",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1309,
        "item": "canvas_oval_line_1309",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1310,
        "item": "canvas_text_line_1310",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1314,
        "item": "canvas_rectangle_line_1314",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1315,
        "item": "canvas_rectangle_line_1315",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1316,
        "item": "canvas_rectangle_line_1316",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1326,
        "item": "text_id",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1329,
        "item": "canvas_rectangle_line_1329",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1387,
        "item": "canvas_rectangle_line_1387",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1402,
        "item": "canvas_oval_line_1402",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1414,
        "item": "canvas_rectangle_line_1414",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1415,
        "item": "canvas_rectangle_line_1415",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1416,
        "item": "canvas_rectangle_line_1416",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1431,
        "item": "canvas_rectangle_line_1431",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1434,
        "item": "canvas_text_line_1434",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1451,
        "item": "canvas_text_line_1451",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1455,
        "item": "canvas_text_line_1455",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 185,
        "item": "self_rectangle_line_185",
        "canvas": "self",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 282,
        "item": "window_id",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 509,
        "item": "can_oval_line_509",
        "canvas": "can",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 510,
        "item": "can_line_line_510",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 511,
        "item": "can_oval_line_511",
        "canvas": "can",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 656,
        "item": "can_oval_line_656",
        "canvas": "can",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 664,
        "item": "can_line_line_664",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 665,
        "item": "can_line_line_665",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 825,
        "item": "canvas_line_line_825",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 826,
        "item": "canvas_line_line_826",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 828,
        "item": "canvas_polygon_line_828",
        "canvas": "canvas",
        "type": "polygon",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 830,
        "item": "canvas_oval_line_830",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 899,
        "item": "can_rectangle_line_899",
        "canvas": "can",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 901,
        "item": "can_rectangle_line_901",
        "canvas": "can",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 920,
        "item": "can_oval_line_920",
        "canvas": "can",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 921,
        "item": "can_polygon_line_921",
        "canvas": "can",
        "type": "polygon",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1298,
        "item": "can_line_line_1298",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1299,
        "item": "can_line_line_1299",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1304,
        "item": "can_line_line_1304",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1306,
        "item": "can_image_line_1306",
        "canvas": "can",
        "type": "image",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1307,
        "item": "can_text_line_1307",
        "canvas": "can",
        "type": "text",
        "scope": "editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1309,
        "item": "can_text_line_1309",
        "canvas": "can",
        "type": "text",
        "scope": "editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1310,
        "item": "can_text_line_1310",
        "canvas": "can",
        "type": "text",
        "scope": "editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1311,
        "item": "can_line_line_1311",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1326,
        "item": "can_line_line_1326",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1327,
        "item": "can_line_line_1327",
        "canvas": "can",
        "type": "line",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1329,
        "item": "can_text_line_1329",
        "canvas": "can",
        "type": "text",
        "scope": "editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1331,
        "item": "can_text_line_1331",
        "canvas": "can",
        "type": "text",
        "scope": "editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1449,
        "item": "canvas_rectangle_line_1449",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1450,
        "item": "canvas_rectangle_line_1450",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1451,
        "item": "canvas_rectangle_line_1451",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1575,
        "item": "canvas_oval_line_1575",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 119,
        "item": "canvas_window_line_119",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 344,
        "item": "c_oval_line_344",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 378,
        "item": "dot_oval_line_378",
        "canvas": "dot",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 551,
        "item": "rect",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 766,
        "item": "canvas_text_line_766",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 767,
        "item": "canvas_line_line_767",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 780,
        "item": "canvas_line_line_780",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 781,
        "item": "canvas_line_line_781",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 784,
        "item": "canvas_line_line_784",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 785,
        "item": "canvas_text_line_785",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1049,
        "item": "led_oval_line_1049",
        "canvas": "led",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1050,
        "item": "led_oval_line_1050",
        "canvas": "led",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1113,
        "item": "canvas_rectangle_line_1113",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1114,
        "item": "canvas_rectangle_line_1114",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1116,
        "item": "canvas_rectangle_line_1116",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1117,
        "item": "canvas_rectangle_line_1117",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1216,
        "item": "canvas_oval_line_1216",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1313,
        "item": "canvas_rectangle_line_1313",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1314,
        "item": "canvas_rectangle_line_1314",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1315,
        "item": "canvas_rectangle_line_1315",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1346,
        "item": "self_rectangle_line_1346",
        "canvas": "self",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1347,
        "item": "self_rectangle_line_1347",
        "canvas": "self",
        "type": "rectangle",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1538,
        "item": "canvas_line_line_1538",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1539,
        "item": "canvas_line_line_1539",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1545,
        "item": "canvas_line_line_1545",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1549,
        "item": "canvas_image_line_1549",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1551,
        "item": "canvas_text_line_1551",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1554,
        "item": "canvas_text_line_1554",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1555,
        "item": "canvas_text_line_1555",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1563,
        "item": "canvas_line_line_1563",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1581,
        "item": "canvas_line_line_1581",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1582,
        "item": "canvas_line_line_1582",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1586,
        "item": "canvas_text_line_1586",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1784,
        "item": "canvas_line_line_1784",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1785,
        "item": "canvas_line_line_1785",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1786,
        "item": "canvas_polygon_line_1786",
        "canvas": "canvas",
        "type": "polygon",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1796,
        "item": "canvas_oval_line_1796",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1979,
        "item": "c_oval_line_1979",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1980,
        "item": "c_oval_line_1980",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2212,
        "item": "c_oval_line_2212",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2213,
        "item": "c_polygon_line_2213",
        "canvas": "c",
        "type": "polygon",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2480,
        "item": "canvas_oval_line_2480",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2481,
        "item": "canvas_line_line_2481",
        "canvas": "canvas",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2482,
        "item": "canvas_oval_line_2482",
        "canvas": "canvas",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2802,
        "item": "window_id",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3111,
        "item": "c_oval_line_3111",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3118,
        "item": "c_line_line_3118",
        "canvas": "c",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3119,
        "item": "c_line_line_3119",
        "canvas": "c",
        "type": "line",
        "scope": "editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 59,
        "item": "self_oval_line_59",
        "canvas": "self",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 60,
        "item": "self_oval_line_60",
        "canvas": "self",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 64,
        "item": "self_oval_line_64",
        "canvas": "self",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 65,
        "item": "self_oval_line_65",
        "canvas": "self",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 90,
        "item": "self_rectangle_line_90",
        "canvas": "self",
        "type": "rectangle",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 299,
        "item": "c_oval_line_299",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 300,
        "item": "c_oval_line_300",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 304,
        "item": "c_line_line_304",
        "canvas": "c",
        "type": "line",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 305,
        "item": "c_oval_line_305",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 553,
        "item": "canvas_image_line_553",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 568,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 599,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 716,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 725,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 1057,
        "item": "protocol_canvas_rectangle_line_1057",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 1058,
        "item": "protocol_canvas_rectangle_line_1058",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 860,
        "item": "canvas_image_line_860",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 883,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 921,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1125,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1135,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1215,
        "item": "protocol_canvas_rectangle_line_1215",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 1216,
        "item": "protocol_canvas_rectangle_line_1216",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 812,
        "item": "c_rectangle_line_812",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 819,
        "item": "c_rectangle_line_819",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 826,
        "item": "c_line_line_826",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_text_line_827",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 833,
        "item": "c_line_line_833",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_text_line_834",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 840,
        "item": "c_line_line_840",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 849,
        "item": "c_oval_line_849",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 852,
        "item": "c_line_line_852",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 853,
        "item": "c_line_line_853",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 854,
        "item": "c_text_line_854",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 855,
        "item": "c_text_line_855",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 861,
        "item": "c_rectangle_line_861",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 867,
        "item": "c_line_line_867",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 879,
        "item": "c_line_line_879",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 881,
        "item": "c_line_line_881",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 882,
        "item": "c_text_line_882",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 883,
        "item": "c_text_line_883",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 712,
        "item": "canvas_image_line_712",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 727,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 762,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 920,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 962,
        "item": "protocol_canvas_rectangle_line_962",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 963,
        "item": "protocol_canvas_rectangle_line_963",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1172,
        "item": "canvas_window_line_1172",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1244,
        "item": "canvas_rectangle_line_1244",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1893,
        "item": "c_rectangle_line_1893",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1901,
        "item": "c_rectangle_line_1901",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1902,
        "item": "c_rectangle_line_1902",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1903,
        "item": "c_rectangle_line_1903",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1910,
        "item": "c_line_line_1910",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1911,
        "item": "c_text_line_1911",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1919,
        "item": "c_line_line_1919",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1920,
        "item": "c_text_line_1920",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1930,
        "item": "c_line_line_1930",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1937,
        "item": "c_line_line_1937",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1947,
        "item": "c_oval_line_1947",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1951,
        "item": "c_line_line_1951",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1952,
        "item": "c_line_line_1952",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1953,
        "item": "c_text_line_1953",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1954,
        "item": "c_text_line_1954",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1960,
        "item": "c_rectangle_line_1960",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1966,
        "item": "c_line_line_1966",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1978,
        "item": "c_line_line_1978",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1980,
        "item": "c_line_line_1980",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1981,
        "item": "c_text_line_1981",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1982,
        "item": "c_text_line_1982",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2688,
        "item": "c_rectangle_line_2688",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2697,
        "item": "c_line_line_2697",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2705,
        "item": "c_rectangle_line_2705",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2707,
        "item": "c_line_line_2707",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2710,
        "item": "c_line_line_2710",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2720,
        "item": "c_text_line_2720",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2727,
        "item": "c_text_line_2727",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2734,
        "item": "c_image_line_2734",
        "canvas": "c",
        "type": "image",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2736,
        "item": "c_text_line_2736",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2749,
        "item": "c_line_line_2749",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2757,
        "item": "c_line_line_2757",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2765,
        "item": "c_line_line_2765",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2778,
        "item": "c_line_line_2778",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2790,
        "item": "c_rectangle_line_2790",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2792,
        "item": "c_oval_line_2792",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2794,
        "item": "c_oval_line_2794",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2800,
        "item": "c_rectangle_line_2800",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2801,
        "item": "c_line_line_2801",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2808,
        "item": "c_polygon_line_2808",
        "canvas": "c",
        "type": "polygon",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2809,
        "item": "c_text_line_2809",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2816,
        "item": "c_text_line_2816",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 553,
        "item": "canvas_image_line_553",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 568,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 599,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 716,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 725,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 1057,
        "item": "protocol_canvas_rectangle_line_1057",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 1058,
        "item": "protocol_canvas_rectangle_line_1058",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 860,
        "item": "canvas_image_line_860",
        "canvas": "canvas",
        "type": "image",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 883,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 921,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1125,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1135,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1215,
        "item": "protocol_canvas_rectangle_line_1215",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 1216,
        "item": "protocol_canvas_rectangle_line_1216",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 812,
        "item": "c_rectangle_line_812",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 819,
        "item": "c_rectangle_line_819",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 826,
        "item": "c_line_line_826",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_text_line_827",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 833,
        "item": "c_line_line_833",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_text_line_834",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 852,
        "item": "c_line_line_852",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 859,
        "item": "c_line_line_859",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 868,
        "item": "c_oval_line_868",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 871,
        "item": "c_line_line_871",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 872,
        "item": "c_line_line_872",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 873,
        "item": "c_text_line_873",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 874,
        "item": "c_text_line_874",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 880,
        "item": "c_rectangle_line_880",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 886,
        "item": "c_line_line_886",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 898,
        "item": "c_line_line_898",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 900,
        "item": "c_line_line_900",
        "canvas": "c",
        "type": "line",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 901,
        "item": "c_text_line_901",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 902,
        "item": "c_text_line_902",
        "canvas": "c",
        "type": "text",
        "scope": "editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 812,
        "item": "c_rectangle_line_812",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 819,
        "item": "c_rectangle_line_819",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 826,
        "item": "c_line_line_826",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_text_line_827",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 833,
        "item": "c_line_line_833",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_text_line_834",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 852,
        "item": "c_line_line_852",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 859,
        "item": "c_line_line_859",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 868,
        "item": "c_oval_line_868",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 871,
        "item": "c_line_line_871",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 872,
        "item": "c_line_line_872",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 873,
        "item": "c_text_line_873",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 874,
        "item": "c_text_line_874",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 880,
        "item": "c_rectangle_line_880",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 886,
        "item": "c_line_line_886",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 898,
        "item": "c_line_line_898",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 900,
        "item": "c_line_line_900",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 901,
        "item": "c_text_line_901",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 902,
        "item": "c_text_line_902",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 615,
        "item": "c_text_line_615",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 623,
        "item": "c_image_line_623",
        "canvas": "c",
        "type": "image",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 625,
        "item": "c_text_line_625",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 627,
        "item": "c_text_line_627",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 629,
        "item": "c_text_line_629",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1457,
        "item": "c_text_line_1457",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1465,
        "item": "c_text_line_1465",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1472,
        "item": "c_text_line_1472",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1473,
        "item": "c_text_line_1473",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1474,
        "item": "c_text_line_1474",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1481,
        "item": "c_text_line_1481",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1486,
        "item": "c_text_line_1486",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1496,
        "item": "c_text_line_1496",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1503,
        "item": "c_text_line_1503",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1518,
        "item": "c_image_line_1518",
        "canvas": "c",
        "type": "image",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1520,
        "item": "c_text_line_1520",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1522,
        "item": "c_text_line_1522",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1525,
        "item": "c_text_line_1525",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1533,
        "item": "c_image_line_1533",
        "canvas": "c",
        "type": "image",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1542,
        "item": "c_text_line_1542",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1545,
        "item": "c_line_line_1545",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1546,
        "item": "c_line_line_1546",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1548,
        "item": "c_rectangle_line_1548",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1549,
        "item": "c_text_line_1549",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1553,
        "item": "c_polygon_line_1553",
        "canvas": "c",
        "type": "polygon",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1554,
        "item": "c_text_line_1554",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1555,
        "item": "c_line_line_1555",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1556,
        "item": "c_text_line_1556",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1564,
        "item": "c_text_line_1564",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1569,
        "item": "c_text_line_1569",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1570,
        "item": "c_line_line_1570",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1571,
        "item": "c_line_line_1571",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1573,
        "item": "c_rectangle_line_1573",
        "canvas": "c",
        "type": "rectangle",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1574,
        "item": "c_text_line_1574",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1576,
        "item": "c_text_line_1576",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1578,
        "item": "c_text_line_1578",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1579,
        "item": "c_text_line_1579",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1580,
        "item": "c_text_line_1580",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1589,
        "item": "c_oval_line_1589",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1590,
        "item": "c_oval_line_1590",
        "canvas": "c",
        "type": "oval",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1593,
        "item": "c_line_line_1593",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1597,
        "item": "c_line_line_1597",
        "canvas": "c",
        "type": "line",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1602,
        "item": "c_polygon_line_1602",
        "canvas": "c",
        "type": "polygon",
        "scope": "editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1603,
        "item": "c_text_line_1603",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1604,
        "item": "c_text_line_1604",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1605,
        "item": "c_text_line_1605",
        "canvas": "c",
        "type": "text",
        "scope": "editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 110,
        "item": "scroll_window",
        "canvas": "scroll_canvas",
        "type": "window",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 305,
        "item": "c_line_line_305",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 313,
        "item": "c_line_line_313",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 314,
        "item": "c_text_line_314",
        "canvas": "c",
        "type": "text",
        "scope": "mechanics_tarzanedytorchoreografiiruchu",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 723,
        "item": "c_rectangle_line_723",
        "canvas": "c",
        "type": "rectangle",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 731,
        "item": "c_text_line_731",
        "canvas": "c",
        "type": "text",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 732,
        "item": "c_rectangle_line_732",
        "canvas": "c",
        "type": "rectangle",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 734,
        "item": "c_rectangle_line_734",
        "canvas": "c",
        "type": "rectangle",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 735,
        "item": "c_text_line_735",
        "canvas": "c",
        "type": "text",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 751,
        "item": "c_rectangle_line_751",
        "canvas": "c",
        "type": "rectangle",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 754,
        "item": "c_line_line_754",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 756,
        "item": "c_line_line_756",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 757,
        "item": "c_line_line_757",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 758,
        "item": "c_text_line_758",
        "canvas": "c",
        "type": "text",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 759,
        "item": "c_text_line_759",
        "canvas": "c",
        "type": "text",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 770,
        "item": "c_line_line_770",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 777,
        "item": "c_oval_line_777",
        "canvas": "c",
        "type": "oval",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 1011,
        "item": "c_line_line_1011",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 1012,
        "item": "c_line_line_1012",
        "canvas": "c",
        "type": "line",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 1013,
        "item": "c_polygon_line_1013",
        "canvas": "c",
        "type": "polygon",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "coords"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 1014,
        "item": "c_text_line_1014",
        "canvas": "c",
        "type": "text",
        "scope": "mechanics_tarzanwykresosi",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 813,
        "item": "c_rectangle_line_813",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 822,
        "item": "c_rectangle_line_822",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_line_line_827",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 828,
        "item": "c_text_line_828",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_line_line_834",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 835,
        "item": "c_text_line_835",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 841,
        "item": "c_line_line_841",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 850,
        "item": "c_oval_line_850",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 853,
        "item": "c_line_line_853",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 854,
        "item": "c_line_line_854",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 855,
        "item": "c_text_line_855",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 856,
        "item": "c_text_line_856",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 862,
        "item": "c_rectangle_line_862",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 868,
        "item": "c_line_line_868",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 880,
        "item": "c_line_line_880",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 882,
        "item": "c_line_line_882",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 883,
        "item": "c_text_line_883",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 884,
        "item": "c_text_line_884",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 760,
        "item": "canvas_image_line_760",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 775,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 810,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 968,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1010,
        "item": "protocol_canvas_rectangle_line_1010",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1011,
        "item": "protocol_canvas_rectangle_line_1011",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1226,
        "item": "canvas_window_line_1226",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1300,
        "item": "canvas_rectangle_line_1300",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1976,
        "item": "c_rectangle_line_1976",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1984,
        "item": "c_rectangle_line_1984",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1985,
        "item": "c_rectangle_line_1985",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1986,
        "item": "c_rectangle_line_1986",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1993,
        "item": "c_line_line_1993",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1994,
        "item": "c_text_line_1994",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2002,
        "item": "c_line_line_2002",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2003,
        "item": "c_text_line_2003",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2013,
        "item": "c_line_line_2013",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2020,
        "item": "c_line_line_2020",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2044,
        "item": "c_oval_line_2044",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2048,
        "item": "c_line_line_2048",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2049,
        "item": "c_line_line_2049",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2050,
        "item": "c_text_line_2050",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2051,
        "item": "c_text_line_2051",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2062,
        "item": "c_rectangle_line_2062",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2068,
        "item": "c_line_line_2068",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2080,
        "item": "c_line_line_2080",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2082,
        "item": "c_line_line_2082",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2083,
        "item": "c_text_line_2083",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2084,
        "item": "c_text_line_2084",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3072,
        "item": "c_rectangle_line_3072",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3081,
        "item": "c_line_line_3081",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3100,
        "item": "c_rectangle_line_3100",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3102,
        "item": "c_line_line_3102",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3105,
        "item": "c_line_line_3105",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3115,
        "item": "c_text_line_3115",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3122,
        "item": "c_text_line_3122",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3130,
        "item": "c_image_line_3130",
        "canvas": "c",
        "type": "image",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3132,
        "item": "c_text_line_3132",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3145,
        "item": "c_line_line_3145",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3153,
        "item": "c_line_line_3153",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3161,
        "item": "c_line_line_3161",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3176,
        "item": "c_line_line_3176",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3192,
        "item": "c_rectangle_line_3192",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3194,
        "item": "c_oval_line_3194",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3210,
        "item": "c_oval_line_3210",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3216,
        "item": "c_rectangle_line_3216",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3217,
        "item": "c_line_line_3217",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3226,
        "item": "c_polygon_line_3226",
        "canvas": "c",
        "type": "polygon",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3228,
        "item": "c_text_line_3228",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3231,
        "item": "c_line_line_3231",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3239,
        "item": "c_text_line_3239",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 394,
        "item": "screen_canvas_rectangle_line_394",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 400,
        "item": "screen_canvas_text_line_400",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 414,
        "item": "screen_canvas_text_line_414",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 415,
        "item": "screen_canvas_line_line_415",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 421,
        "item": "screen_canvas_text_line_421",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 425,
        "item": "screen_canvas_text_line_425",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 432,
        "item": "screen_canvas_line_line_432",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 445,
        "item": "screen_canvas_line_line_445",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 466,
        "item": "screen_canvas_text_line_466",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 483,
        "item": "screen_canvas_text_line_483",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 512,
        "item": "screen_canvas_rectangle_line_512",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 518,
        "item": "screen_canvas_text_line_518",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 527,
        "item": "screen_canvas_rectangle_line_527",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 529,
        "item": "screen_canvas_text_line_529",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 591,
        "item": "screen_canvas_image_line_591",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 593,
        "item": "screen_canvas_rectangle_line_593",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 594,
        "item": "screen_canvas_text_line_594",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 603,
        "item": "screen_canvas_text_line_603",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 623,
        "item": "screen_canvas_image_line_623",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 625,
        "item": "screen_canvas_rectangle_line_625",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 626,
        "item": "screen_canvas_text_line_626",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 640,
        "item": "screen_canvas_image_line_640",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 642,
        "item": "screen_canvas_rectangle_line_642",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 643,
        "item": "screen_canvas_text_line_643",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 692,
        "item": "screen_canvas_image_line_692",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 718,
        "item": "screen_canvas_image_line_718",
        "canvas": "screen_canvas",
        "type": "image",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 737,
        "item": "screen_canvas_line_line_737",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 738,
        "item": "screen_canvas_line_line_738",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 740,
        "item": "screen_canvas_oval_line_740",
        "canvas": "screen_canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 785,
        "item": "screen_canvas_rectangle_line_785",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 787,
        "item": "screen_canvas_rectangle_line_787",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 790,
        "item": "screen_canvas_rectangle_line_790",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 791,
        "item": "screen_canvas_text_line_791",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 797,
        "item": "screen_canvas_rectangle_line_797",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 798,
        "item": "screen_canvas_text_line_798",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 799,
        "item": "screen_canvas_text_line_799",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 815,
        "item": "screen_canvas_rectangle_line_815",
        "canvas": "screen_canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 816,
        "item": "screen_canvas_text_line_816",
        "canvas": "screen_canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 818,
        "item": "screen_canvas_line_line_818",
        "canvas": "screen_canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 1063,
        "item": "_edit_window",
        "canvas": "screen_canvas",
        "type": "window",
        "scope": "modes_editor_par_tarzannextionpreview",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 485,
        "item": "led_oval_line_485",
        "canvas": "led",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1076,
        "item": "panel_canvas_window_line_1076",
        "canvas": "panel_canvas",
        "type": "window",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1286,
        "item": "canvas_rectangle_line_1286",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1303,
        "item": "canvas_rectangle_line_1303",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1309,
        "item": "canvas_oval_line_1309",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1310,
        "item": "canvas_text_line_1310",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1314,
        "item": "canvas_rectangle_line_1314",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1315,
        "item": "canvas_rectangle_line_1315",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1316,
        "item": "canvas_rectangle_line_1316",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1326,
        "item": "text_id",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1329,
        "item": "canvas_rectangle_line_1329",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1387,
        "item": "canvas_rectangle_line_1387",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1402,
        "item": "canvas_oval_line_1402",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1414,
        "item": "canvas_rectangle_line_1414",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1415,
        "item": "canvas_rectangle_line_1415",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1416,
        "item": "canvas_rectangle_line_1416",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1431,
        "item": "canvas_rectangle_line_1431",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1434,
        "item": "canvas_text_line_1434",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1451,
        "item": "canvas_text_line_1451",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1455,
        "item": "canvas_text_line_1455",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparapp",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 185,
        "item": "self_rectangle_line_185",
        "canvas": "self",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 282,
        "item": "window_id",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 509,
        "item": "can_oval_line_509",
        "canvas": "can",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 510,
        "item": "can_line_line_510",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 511,
        "item": "can_oval_line_511",
        "canvas": "can",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 656,
        "item": "can_oval_line_656",
        "canvas": "can",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 664,
        "item": "can_line_line_664",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 665,
        "item": "can_line_line_665",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 825,
        "item": "canvas_line_line_825",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 826,
        "item": "canvas_line_line_826",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 828,
        "item": "canvas_polygon_line_828",
        "canvas": "canvas",
        "type": "polygon",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 830,
        "item": "canvas_oval_line_830",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 899,
        "item": "can_rectangle_line_899",
        "canvas": "can",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 901,
        "item": "can_rectangle_line_901",
        "canvas": "can",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 920,
        "item": "can_oval_line_920",
        "canvas": "can",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 921,
        "item": "can_polygon_line_921",
        "canvas": "can",
        "type": "polygon",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1298,
        "item": "can_line_line_1298",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1299,
        "item": "can_line_line_1299",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1304,
        "item": "can_line_line_1304",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1306,
        "item": "can_image_line_1306",
        "canvas": "can",
        "type": "image",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1307,
        "item": "can_text_line_1307",
        "canvas": "can",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1309,
        "item": "can_text_line_1309",
        "canvas": "can",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1310,
        "item": "can_text_line_1310",
        "canvas": "can",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1311,
        "item": "can_line_line_1311",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1326,
        "item": "can_line_line_1326",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1327,
        "item": "can_line_line_1327",
        "canvas": "can",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1329,
        "item": "can_text_line_1329",
        "canvas": "can",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1331,
        "item": "can_text_line_1331",
        "canvas": "can",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1449,
        "item": "canvas_rectangle_line_1449",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1450,
        "item": "canvas_rectangle_line_1450",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1451,
        "item": "canvas_rectangle_line_1451",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1575,
        "item": "canvas_oval_line_1575",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 119,
        "item": "canvas_window_line_119",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 344,
        "item": "c_oval_line_344",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 378,
        "item": "dot_oval_line_378",
        "canvas": "dot",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 551,
        "item": "rect",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 766,
        "item": "canvas_text_line_766",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 767,
        "item": "canvas_line_line_767",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 780,
        "item": "canvas_line_line_780",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 781,
        "item": "canvas_line_line_781",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 784,
        "item": "canvas_line_line_784",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 785,
        "item": "canvas_text_line_785",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1049,
        "item": "led_oval_line_1049",
        "canvas": "led",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1050,
        "item": "led_oval_line_1050",
        "canvas": "led",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1113,
        "item": "canvas_rectangle_line_1113",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1114,
        "item": "canvas_rectangle_line_1114",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1116,
        "item": "canvas_rectangle_line_1116",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1117,
        "item": "canvas_rectangle_line_1117",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1216,
        "item": "canvas_oval_line_1216",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1313,
        "item": "canvas_rectangle_line_1313",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1314,
        "item": "canvas_rectangle_line_1314",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1315,
        "item": "canvas_rectangle_line_1315",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1346,
        "item": "self_rectangle_line_1346",
        "canvas": "self",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1347,
        "item": "self_rectangle_line_1347",
        "canvas": "self",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1538,
        "item": "canvas_line_line_1538",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1539,
        "item": "canvas_line_line_1539",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1545,
        "item": "canvas_line_line_1545",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1549,
        "item": "canvas_image_line_1549",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1551,
        "item": "canvas_text_line_1551",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1554,
        "item": "canvas_text_line_1554",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1555,
        "item": "canvas_text_line_1555",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1563,
        "item": "canvas_line_line_1563",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1581,
        "item": "canvas_line_line_1581",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1582,
        "item": "canvas_line_line_1582",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1586,
        "item": "canvas_text_line_1586",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "text"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1784,
        "item": "canvas_line_line_1784",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1785,
        "item": "canvas_line_line_1785",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1786,
        "item": "canvas_polygon_line_1786",
        "canvas": "canvas",
        "type": "polygon",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1796,
        "item": "canvas_oval_line_1796",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1979,
        "item": "c_oval_line_1979",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1980,
        "item": "c_oval_line_1980",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2212,
        "item": "c_oval_line_2212",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2213,
        "item": "c_polygon_line_2213",
        "canvas": "c",
        "type": "polygon",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2480,
        "item": "canvas_oval_line_2480",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2481,
        "item": "canvas_line_line_2481",
        "canvas": "canvas",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2482,
        "item": "canvas_oval_line_2482",
        "canvas": "canvas",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2802,
        "item": "window_id",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3111,
        "item": "c_oval_line_3111",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3118,
        "item": "c_line_line_3118",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3119,
        "item": "c_line_line_3119",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_par_tarzanparpanels_old",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 59,
        "item": "self_oval_line_59",
        "canvas": "self",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 60,
        "item": "self_oval_line_60",
        "canvas": "self",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 64,
        "item": "self_oval_line_64",
        "canvas": "self",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 65,
        "item": "self_oval_line_65",
        "canvas": "self",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 90,
        "item": "self_rectangle_line_90",
        "canvas": "self",
        "type": "rectangle",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 299,
        "item": "c_oval_line_299",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 300,
        "item": "c_oval_line_300",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 304,
        "item": "c_line_line_304",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 305,
        "item": "c_oval_line_305",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_par_tarzanparwidgets",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 553,
        "item": "canvas_image_line_553",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 568,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 599,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 716,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 725,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 1057,
        "item": "protocol_canvas_rectangle_line_1057",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 1058,
        "item": "protocol_canvas_rectangle_line_1058",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 860,
        "item": "canvas_image_line_860",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 883,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 921,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1125,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1135,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1215,
        "item": "protocol_canvas_rectangle_line_1215",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 1216,
        "item": "protocol_canvas_rectangle_line_1216",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 812,
        "item": "c_rectangle_line_812",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 819,
        "item": "c_rectangle_line_819",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 826,
        "item": "c_line_line_826",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_text_line_827",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 833,
        "item": "c_line_line_833",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_text_line_834",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 840,
        "item": "c_line_line_840",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 849,
        "item": "c_oval_line_849",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 852,
        "item": "c_line_line_852",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 853,
        "item": "c_line_line_853",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 854,
        "item": "c_text_line_854",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 855,
        "item": "c_text_line_855",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 861,
        "item": "c_rectangle_line_861",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 867,
        "item": "c_line_line_867",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 879,
        "item": "c_line_line_879",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 881,
        "item": "c_line_line_881",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 882,
        "item": "c_text_line_882",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 883,
        "item": "c_text_line_883",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 712,
        "item": "canvas_image_line_712",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 727,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 762,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 920,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 962,
        "item": "protocol_canvas_rectangle_line_962",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 963,
        "item": "protocol_canvas_rectangle_line_963",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1172,
        "item": "canvas_window_line_1172",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1244,
        "item": "canvas_rectangle_line_1244",
        "canvas": "canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1893,
        "item": "c_rectangle_line_1893",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1901,
        "item": "c_rectangle_line_1901",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1902,
        "item": "c_rectangle_line_1902",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1903,
        "item": "c_rectangle_line_1903",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1910,
        "item": "c_line_line_1910",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1911,
        "item": "c_text_line_1911",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1919,
        "item": "c_line_line_1919",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1920,
        "item": "c_text_line_1920",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1930,
        "item": "c_line_line_1930",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1937,
        "item": "c_line_line_1937",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1947,
        "item": "c_oval_line_1947",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1951,
        "item": "c_line_line_1951",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1952,
        "item": "c_line_line_1952",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1953,
        "item": "c_text_line_1953",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1954,
        "item": "c_text_line_1954",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1960,
        "item": "c_rectangle_line_1960",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1966,
        "item": "c_line_line_1966",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1978,
        "item": "c_line_line_1978",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1980,
        "item": "c_line_line_1980",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1981,
        "item": "c_text_line_1981",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1982,
        "item": "c_text_line_1982",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2688,
        "item": "c_rectangle_line_2688",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2697,
        "item": "c_line_line_2697",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2705,
        "item": "c_rectangle_line_2705",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2707,
        "item": "c_line_line_2707",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2710,
        "item": "c_line_line_2710",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2720,
        "item": "c_text_line_2720",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2727,
        "item": "c_text_line_2727",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2734,
        "item": "c_image_line_2734",
        "canvas": "c",
        "type": "image",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2736,
        "item": "c_text_line_2736",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2749,
        "item": "c_line_line_2749",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2757,
        "item": "c_line_line_2757",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2765,
        "item": "c_line_line_2765",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2778,
        "item": "c_line_line_2778",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2790,
        "item": "c_rectangle_line_2790",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2792,
        "item": "c_oval_line_2792",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2794,
        "item": "c_oval_line_2794",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2800,
        "item": "c_rectangle_line_2800",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2801,
        "item": "c_line_line_2801",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2808,
        "item": "c_polygon_line_2808",
        "canvas": "c",
        "type": "polygon",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2809,
        "item": "c_text_line_2809",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2816,
        "item": "c_text_line_2816",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_ehr_tarzanehrui",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 553,
        "item": "canvas_image_line_553",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 568,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 599,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 716,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 725,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 1057,
        "item": "protocol_canvas_rectangle_line_1057",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 1058,
        "item": "protocol_canvas_rectangle_line_1058",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanehrtakesandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 860,
        "item": "canvas_image_line_860",
        "canvas": "canvas",
        "type": "image",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 883,
        "item": "item",
        "canvas": "canvas",
        "type": "text",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 921,
        "item": "save_button_window",
        "canvas": "canvas",
        "type": "window",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1125,
        "item": "protocol_title_id",
        "canvas": "protocol_canvas",
        "type": "text",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1135,
        "item": "row_window",
        "canvas": "protocol_canvas",
        "type": "window",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1215,
        "item": "protocol_canvas_rectangle_line_1215",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 1216,
        "item": "protocol_canvas_rectangle_line_1216",
        "canvas": "protocol_canvas",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzantakeprotocollight",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 812,
        "item": "c_rectangle_line_812",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 819,
        "item": "c_rectangle_line_819",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 826,
        "item": "c_line_line_826",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_text_line_827",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 833,
        "item": "c_line_line_833",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_text_line_834",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 852,
        "item": "c_line_line_852",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 859,
        "item": "c_line_line_859",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 868,
        "item": "c_oval_line_868",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 871,
        "item": "c_line_line_871",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 872,
        "item": "c_line_line_872",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 873,
        "item": "c_text_line_873",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 874,
        "item": "c_text_line_874",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 880,
        "item": "c_rectangle_line_880",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 886,
        "item": "c_line_line_886",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 898,
        "item": "c_line_line_898",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 900,
        "item": "c_line_line_900",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 901,
        "item": "c_text_line_901",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 902,
        "item": "c_text_line_902",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 812,
        "item": "c_rectangle_line_812",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 819,
        "item": "c_rectangle_line_819",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 820,
        "item": "c_rectangle_line_820",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 821,
        "item": "c_rectangle_line_821",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 826,
        "item": "c_line_line_826",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 827,
        "item": "c_text_line_827",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 833,
        "item": "c_line_line_833",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 834,
        "item": "c_text_line_834",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 852,
        "item": "c_line_line_852",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 859,
        "item": "c_line_line_859",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 868,
        "item": "c_oval_line_868",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 871,
        "item": "c_line_line_871",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 872,
        "item": "c_line_line_872",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 873,
        "item": "c_text_line_873",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 874,
        "item": "c_text_line_874",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 880,
        "item": "c_rectangle_line_880",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 886,
        "item": "c_line_line_886",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 898,
        "item": "c_line_line_898",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 900,
        "item": "c_line_line_900",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 901,
        "item": "c_text_line_901",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 902,
        "item": "c_text_line_902",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzanaxissandbox",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 615,
        "item": "c_text_line_615",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 623,
        "item": "c_image_line_623",
        "canvas": "c",
        "type": "image",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 625,
        "item": "c_text_line_625",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 627,
        "item": "c_text_line_627",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 629,
        "item": "c_text_line_629",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1457,
        "item": "c_text_line_1457",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1465,
        "item": "c_text_line_1465",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1472,
        "item": "c_text_line_1472",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1473,
        "item": "c_text_line_1473",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1474,
        "item": "c_text_line_1474",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1481,
        "item": "c_text_line_1481",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1486,
        "item": "c_text_line_1486",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1496,
        "item": "c_text_line_1496",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1503,
        "item": "c_text_line_1503",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1518,
        "item": "c_image_line_1518",
        "canvas": "c",
        "type": "image",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1520,
        "item": "c_text_line_1520",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1522,
        "item": "c_text_line_1522",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1525,
        "item": "c_text_line_1525",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1533,
        "item": "c_image_line_1533",
        "canvas": "c",
        "type": "image",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1542,
        "item": "c_text_line_1542",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1545,
        "item": "c_line_line_1545",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1546,
        "item": "c_line_line_1546",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1548,
        "item": "c_rectangle_line_1548",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1549,
        "item": "c_text_line_1549",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1553,
        "item": "c_polygon_line_1553",
        "canvas": "c",
        "type": "polygon",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1554,
        "item": "c_text_line_1554",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1555,
        "item": "c_line_line_1555",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1556,
        "item": "c_text_line_1556",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1564,
        "item": "c_text_line_1564",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1569,
        "item": "c_text_line_1569",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1570,
        "item": "c_line_line_1570",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1571,
        "item": "c_line_line_1571",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1573,
        "item": "c_rectangle_line_1573",
        "canvas": "c",
        "type": "rectangle",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1574,
        "item": "c_text_line_1574",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1576,
        "item": "c_text_line_1576",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1578,
        "item": "c_text_line_1578",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1579,
        "item": "c_text_line_1579",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1580,
        "item": "c_text_line_1580",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1589,
        "item": "c_oval_line_1589",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1590,
        "item": "c_oval_line_1590",
        "canvas": "c",
        "type": "oval",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1593,
        "item": "c_line_line_1593",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1597,
        "item": "c_line_line_1597",
        "canvas": "c",
        "type": "line",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1602,
        "item": "c_polygon_line_1602",
        "canvas": "c",
        "type": "polygon",
        "scope": "modes_editor_tarzankhr",
        "prop": "coords"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1603,
        "item": "c_text_line_1603",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1604,
        "item": "c_text_line_1604",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1605,
        "item": "c_text_line_1605",
        "canvas": "c",
        "type": "text",
        "scope": "modes_editor_tarzankhr",
        "prop": "text"
    },
    {
        "file": "vision/tarzanVisionSetup.py",
        "line": 248,
        "item": "window_id",
        "canvas": "canvas",
        "type": "window",
        "scope": "vision_tarzanvisionsetup",
        "prop": "coords"
    }
]

REFRESH_REPLACEMENT_CATALOG = [
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 535,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 598,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 704,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 711,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 733,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 739,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 744,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 749,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 754,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 759,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 764,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 811,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 860,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 905,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 931,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 936,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 961,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 968,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanAxisSandbox.py",
        "line": 976,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 752,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1299,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1473,
        "kind": "refresh_all",
        "code": "self._refresh_all(reason=\"INIT\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1718,
        "kind": "refresh_all",
        "code": "self.master_window._refresh_all(light=False)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1741,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\", reason=\"STEP_TUNING_LIVE\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1753,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\", reason=\"MECHANICS_PRESET\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1847,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano ustawienia osi: {path}\", reason=\"LOAD_JSON\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1884,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\", reason=\"LOAD_TUNING_TXT\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1896,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\", reason=\"RESET_STEP_TUNING\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1907,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\", reason=\"TEST_SINUS\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1918,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\", reason=\"TEST_NEGATIVE\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1929,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\", reason=\"TEST_ZERO_CROSS\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1940,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\", reason=\"TEST_FLAT_ZERO\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1950,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\", reason=\"RESET_NODES\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 1974,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2060,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2146,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_AXIS_DIALOG._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2147,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None, reason: str = \"unknown\") -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2370,
        "kind": "refresh_all",
        "code": "self.master_window._refresh_all(light=False)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2464,
        "kind": "refresh_all",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2464,
        "kind": "after_refresh",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2732,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=status)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2762,
        "kind": "refresh_all",
        "code": "dlg._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2763,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=\"Zastosowano ustawienia MAIN TAKE.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 2890,
        "kind": "after_refresh",
        "code": "self._configure_after_id = self.after(40, self._flush_configure_refresh)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3067,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3442,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_MAIN._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3443,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, light: bool = False, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/EHR/tarzanEhrUi.py",
        "line": 3844,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=f\"Wczytano TAKE TXT: {path.name}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 354,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 361,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 472,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 581,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 598,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 688,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 710,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanNextionPreview.py",
        "line": 772,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 230,
        "kind": "self_nextion_tick",
        "code": "self.after(50, self.nextion_tick)",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 939,
        "kind": "draw_preview",
        "code": "fg=COLORS[\"text\"], insertbackground=COLORS[\"text\"], command=lambda: draw_preview() if \"draw_preview\" in locals() else None).grid(row=2, column=1, sticky=\"w\", padx=8)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 988,
        "kind": "draw_preview",
        "code": "refresh_zone_buttons()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 992,
        "kind": "draw_preview",
        "code": "refresh_zone_buttons()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 993,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 997,
        "kind": "draw_preview",
        "code": "def refresh_zone_buttons():",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1046,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1123,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1130,
        "kind": "draw_preview",
        "code": "command=draw_preview).pack(side=\"left\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1135,
        "kind": "draw_preview",
        "code": "opt = tk.OptionMenu(row, data[\"zone\"], *zone_map.keys(), command=lambda _=None: draw_preview())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1150,
        "kind": "draw_preview",
        "code": "command=draw_preview,",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1153,
        "kind": "draw_preview",
        "code": "col_spin.bind(\"<KeyRelease>\", lambda _event: draw_preview())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1165,
        "kind": "draw_preview",
        "code": "command=draw_preview,",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1168,
        "kind": "draw_preview",
        "code": "row_spin.bind(\"<KeyRelease>\", lambda _event: draw_preview())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1189,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1225,
        "kind": "draw_preview",
        "code": "def draw_preview(*_):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1226,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1590,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1601,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1628,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1648,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1698,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1722,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1743,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1754,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1776,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1828,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1848,
        "kind": "draw_preview",
        "code": "refresh_zone_buttons()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1849,
        "kind": "draw_preview",
        "code": "win.after(200, draw_preview)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1850,
        "kind": "draw_preview",
        "code": "win.after(800, draw_preview)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1898,
        "kind": "def_nextion_tick",
        "code": "def nextion_tick(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1902,
        "kind": "nextion_refresh_previews",
        "code": "if hasattr(self.panels, \"nextion_refresh_previews\"):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1903,
        "kind": "nextion_refresh_previews",
        "code": "self.panels.nextion_refresh_previews()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParApp.py",
        "line": 1907,
        "kind": "self_nextion_tick",
        "code": "self.after(50, self.nextion_tick)",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 182,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 358,
        "kind": "refresh_axis_card",
        "code": "self._register_signal_proxy(sig, lambda v, k=key: self.refresh_axis_card(k))",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 404,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 407,
        "kind": "refresh_axis_cards",
        "code": "def refresh_axis_cards(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 409,
        "kind": "refresh_axis_card",
        "code": "self.refresh_axis_card(axis)",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 411,
        "kind": "refresh_axis_card",
        "code": "def refresh_axis_card(self, axis: str):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 496,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 655,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\"); cx, cy, r = 40, 40, 30",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 823,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\"); cx, cy = w//2, h//2",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 899,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\"); can.create_rectangle(14, 5, 24, h-5, fill=COLORS[\"green\"], outline=\"#063c0a\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 917,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1230,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1237,
        "kind": "draw_timeline",
        "code": "self._schedule_timeline_redraw()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1244,
        "kind": "draw_timeline",
        "code": "self.timeline_canvas.bind(\"<Configure>\", lambda e: self.draw_timeline())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1245,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1248,
        "kind": "draw_timeline",
        "code": "def _schedule_timeline_redraw(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1250,
        "kind": "draw_timeline",
        "code": "self._timeline_after_id = self.app.after(_TIMELINE_DEBOUNCE_MS, self._do_draw_timeline)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1252,
        "kind": "draw_timeline",
        "code": "def _do_draw_timeline(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1254,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1278,
        "kind": "draw_timeline",
        "code": "def draw_timeline(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1281,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1446,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1574,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1761,
        "kind": "nextion_refresh_previews",
        "code": "def nextion_refresh_previews(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels.py",
        "line": 1788,
        "kind": "widget_refresh",
        "code": "widget.refresh()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 187,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 680,
        "kind": "draw_timeline",
        "code": "canvas.bind(\"<Configure>\", lambda e: self.draw_timeline())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 681,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 735,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 738,
        "kind": "refresh_axis_cards",
        "code": "def refresh_axis_cards(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 755,
        "kind": "draw_timeline",
        "code": "def draw_timeline(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 759,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1044,
        "kind": "canvas_delete_all",
        "code": "led.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1111,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1215,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1310,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1343,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1452,
        "kind": "draw_timeline",
        "code": "def _schedule_timeline_redraw(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1459,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1469,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1497,
        "kind": "draw_timeline",
        "code": "command=lambda: (self.bus.history.clear(), self.draw_timeline()),",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1503,
        "kind": "draw_timeline",
        "code": "canvas.bind(\"<Configure>\", lambda _e: self._schedule_timeline_redraw())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1504,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1512,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1674,
        "kind": "draw_timeline",
        "code": "self._schedule_timeline_redraw()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1734,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1780,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 1964,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2209,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 2470,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3107,
        "kind": "canvas_delete_all",
        "code": "c.delete('all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3184,
        "kind": "refresh_axis_cards",
        "code": "TarzanParPanels.refresh_axis_cards = _tarzan_refresh_axis_cards_final_v2",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3186,
        "kind": "draw_timeline",
        "code": "TarzanParPanels._schedule_timeline_redraw = _schedule_timeline_redraw",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParPanels_old.py",
        "line": 3188,
        "kind": "draw_timeline",
        "code": "TarzanParPanels.draw_timeline = _par_draw_timeline_final",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 54,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 83,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/PAR/tarzanParWidgets.py",
        "line": 287,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/TarzanEhrTakeSandbox.py",
        "line": 545,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 35,
        "kind": "refresh_all",
        "code": "# - nie używa _refresh_all.",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/TarzanTakeProtocolLight.py",
        "line": 852,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 534,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 595,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 703,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 710,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 732,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 738,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 743,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 748,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 753,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 758,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 763,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 810,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 859,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 904,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 930,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 935,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 960,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 967,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 975,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 704,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1243,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1411,
        "kind": "refresh_all",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1411,
        "kind": "after_refresh",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1657,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano ustawienia osi.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1666,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1677,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1770,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano ustawienia osi: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1807,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1818,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1828,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1838,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1848,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1858,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1867,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1891,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 1958,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2017,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_AXIS_DIALOG._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2018,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2095,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2107,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2120,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2211,
        "kind": "refresh_all",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2211,
        "kind": "after_refresh",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2366,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=True, status=status)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2395,
        "kind": "refresh_all",
        "code": "dlg._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2396,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=\"Zastosowano ustawienia MAIN TAKE.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2509,
        "kind": "refresh_all",
        "code": "self._refresh_all(",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2520,
        "kind": "after_refresh",
        "code": "self._configure_after_id = self.after(40, self._flush_configure_refresh)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2683,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2960,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_MAIN._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 2961,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, light: bool = False, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 3029,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=True, status=None)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/EHR/tarzanEhrUi.py",
        "line": 3232,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=f\"Wczytano TAKE TXT: {path.name}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/TarzanEhrTakeSandbox.py",
        "line": 545,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 35,
        "kind": "refresh_all",
        "code": "# - nie używa _refresh_all.",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/TarzanTakeProtocolLight.py",
        "line": 852,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 534,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 595,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 703,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 710,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 732,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 738,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 743,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 748,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 753,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 758,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 763,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 810,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 878,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 923,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 949,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 954,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 979,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 986,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/editor/tarzanAxisSandbox.py",
        "line": 994,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 534,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 595,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 703,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 710,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 732,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 738,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 743,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 748,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 753,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 758,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 763,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 810,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 878,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 923,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 949,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 954,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 979,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 986,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanAxisSandbox.py",
        "line": 994,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 611,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 950,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 991,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1094,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1158,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1161,
        "kind": "after_refresh",
        "code": "self.after(self._camera_preview_refresh_ms, self._camera_preview_loop)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1372,
        "kind": "after_refresh",
        "code": "self.after(self._ui_refresh_ms, self._ui_loop)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1434,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1435,
        "kind": "draw_khr",
        "code": "self._draw_khr()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1436,
        "kind": "draw_khr",
        "code": "self._draw_output()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1438,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_input\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1439,
        "kind": "draw_khr",
        "code": "def _draw_input(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1441,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1444,
        "kind": "draw_khr",
        "code": "self._draw_camera_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1476,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_camera_input\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1477,
        "kind": "draw_khr",
        "code": "def _draw_camera_input(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1558,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_khr\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1559,
        "kind": "draw_khr",
        "code": "def _draw_khr(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1561,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1582,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_output\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1583,
        "kind": "draw_khr",
        "code": "def _draw_output(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "editor/tarzanKHR.py",
        "line": 1585,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "mechanics/tarzanEdytorChoreografiiRuchu.py",
        "line": 302,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 721,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 739,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "mechanics/tarzanWykresOsi.py",
        "line": 1008,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 535,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 598,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 704,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 711,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 733,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 739,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 744,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 749,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 754,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 759,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 764,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 811,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 860,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 905,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 931,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 936,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 961,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 968,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanAxisSandbox.py",
        "line": 976,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 752,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1299,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1473,
        "kind": "refresh_all",
        "code": "self._refresh_all(reason=\"INIT\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1718,
        "kind": "refresh_all",
        "code": "self.master_window._refresh_all(light=False)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1741,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\", reason=\"STEP_TUNING_LIVE\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1753,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\", reason=\"MECHANICS_PRESET\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1847,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano ustawienia osi: {path}\", reason=\"LOAD_JSON\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1884,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\", reason=\"LOAD_TUNING_TXT\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1896,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\", reason=\"RESET_STEP_TUNING\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1907,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\", reason=\"TEST_SINUS\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1918,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\", reason=\"TEST_NEGATIVE\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1929,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\", reason=\"TEST_ZERO_CROSS\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1940,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\", reason=\"TEST_FLAT_ZERO\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1950,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\", reason=\"RESET_NODES\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 1974,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2060,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2146,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_AXIS_DIALOG._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2147,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None, reason: str = \"unknown\") -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2370,
        "kind": "refresh_all",
        "code": "self.master_window._refresh_all(light=False)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2464,
        "kind": "refresh_all",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2464,
        "kind": "after_refresh",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2732,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=status)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2762,
        "kind": "refresh_all",
        "code": "dlg._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2763,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=\"Zastosowano ustawienia MAIN TAKE.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 2890,
        "kind": "after_refresh",
        "code": "self._configure_after_id = self.after(40, self._flush_configure_refresh)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3067,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3442,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_MAIN._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3443,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, light: bool = False, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/EHR/tarzanEhrUi.py",
        "line": 3844,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=f\"Wczytano TAKE TXT: {path.name}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 354,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 361,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 472,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 581,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 598,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 688,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 710,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanNextionPreview.py",
        "line": 772,
        "kind": "canvas_delete_all",
        "code": "self.screen_canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 230,
        "kind": "self_nextion_tick",
        "code": "self.after(50, self.nextion_tick)",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 939,
        "kind": "draw_preview",
        "code": "fg=COLORS[\"text\"], insertbackground=COLORS[\"text\"], command=lambda: draw_preview() if \"draw_preview\" in locals() else None).grid(row=2, column=1, sticky=\"w\", padx=8)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 988,
        "kind": "draw_preview",
        "code": "refresh_zone_buttons()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 992,
        "kind": "draw_preview",
        "code": "refresh_zone_buttons()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 993,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 997,
        "kind": "draw_preview",
        "code": "def refresh_zone_buttons():",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1046,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1123,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1130,
        "kind": "draw_preview",
        "code": "command=draw_preview).pack(side=\"left\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1135,
        "kind": "draw_preview",
        "code": "opt = tk.OptionMenu(row, data[\"zone\"], *zone_map.keys(), command=lambda _=None: draw_preview())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1150,
        "kind": "draw_preview",
        "code": "command=draw_preview,",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1153,
        "kind": "draw_preview",
        "code": "col_spin.bind(\"<KeyRelease>\", lambda _event: draw_preview())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1165,
        "kind": "draw_preview",
        "code": "command=draw_preview,",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1168,
        "kind": "draw_preview",
        "code": "row_spin.bind(\"<KeyRelease>\", lambda _event: draw_preview())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1189,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1225,
        "kind": "draw_preview",
        "code": "def draw_preview(*_):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1226,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1590,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1601,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1628,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1648,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1698,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1722,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1743,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1754,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1776,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1828,
        "kind": "draw_preview",
        "code": "draw_preview()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1848,
        "kind": "draw_preview",
        "code": "refresh_zone_buttons()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1849,
        "kind": "draw_preview",
        "code": "win.after(200, draw_preview)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1850,
        "kind": "draw_preview",
        "code": "win.after(800, draw_preview)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1898,
        "kind": "def_nextion_tick",
        "code": "def nextion_tick(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1902,
        "kind": "nextion_refresh_previews",
        "code": "if hasattr(self.panels, \"nextion_refresh_previews\"):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1903,
        "kind": "nextion_refresh_previews",
        "code": "self.panels.nextion_refresh_previews()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParApp.py",
        "line": 1907,
        "kind": "self_nextion_tick",
        "code": "self.after(50, self.nextion_tick)",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 182,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 358,
        "kind": "refresh_axis_card",
        "code": "self._register_signal_proxy(sig, lambda v, k=key: self.refresh_axis_card(k))",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 404,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 407,
        "kind": "refresh_axis_cards",
        "code": "def refresh_axis_cards(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 409,
        "kind": "refresh_axis_card",
        "code": "self.refresh_axis_card(axis)",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 411,
        "kind": "refresh_axis_card",
        "code": "def refresh_axis_card(self, axis: str):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 496,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 655,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\"); cx, cy, r = 40, 40, 30",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 823,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\"); cx, cy = w//2, h//2",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 899,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\"); can.create_rectangle(14, 5, 24, h-5, fill=COLORS[\"green\"], outline=\"#063c0a\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 917,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1230,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1237,
        "kind": "draw_timeline",
        "code": "self._schedule_timeline_redraw()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1244,
        "kind": "draw_timeline",
        "code": "self.timeline_canvas.bind(\"<Configure>\", lambda e: self.draw_timeline())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1245,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1248,
        "kind": "draw_timeline",
        "code": "def _schedule_timeline_redraw(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1250,
        "kind": "draw_timeline",
        "code": "self._timeline_after_id = self.app.after(_TIMELINE_DEBOUNCE_MS, self._do_draw_timeline)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1252,
        "kind": "draw_timeline",
        "code": "def _do_draw_timeline(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1254,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1278,
        "kind": "draw_timeline",
        "code": "def draw_timeline(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1281,
        "kind": "canvas_delete_all",
        "code": "can.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1446,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1574,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1761,
        "kind": "nextion_refresh_previews",
        "code": "def nextion_refresh_previews(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels.py",
        "line": 1788,
        "kind": "widget_refresh",
        "code": "widget.refresh()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 187,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 680,
        "kind": "draw_timeline",
        "code": "canvas.bind(\"<Configure>\", lambda e: self.draw_timeline())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 681,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 735,
        "kind": "refresh_axis_cards",
        "code": "self.refresh_axis_cards()",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 738,
        "kind": "refresh_axis_cards",
        "code": "def refresh_axis_cards(self):",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 755,
        "kind": "draw_timeline",
        "code": "def draw_timeline(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 759,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1044,
        "kind": "canvas_delete_all",
        "code": "led.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1111,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1215,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1310,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1343,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1452,
        "kind": "draw_timeline",
        "code": "def _schedule_timeline_redraw(self):",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1459,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1469,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1497,
        "kind": "draw_timeline",
        "code": "command=lambda: (self.bus.history.clear(), self.draw_timeline()),",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1503,
        "kind": "draw_timeline",
        "code": "canvas.bind(\"<Configure>\", lambda _e: self._schedule_timeline_redraw())",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1504,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1512,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1674,
        "kind": "draw_timeline",
        "code": "self._schedule_timeline_redraw()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1734,
        "kind": "draw_timeline",
        "code": "self.draw_timeline()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1780,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 1964,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2209,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 2470,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3107,
        "kind": "canvas_delete_all",
        "code": "c.delete('all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3184,
        "kind": "refresh_axis_cards",
        "code": "TarzanParPanels.refresh_axis_cards = _tarzan_refresh_axis_cards_final_v2",
        "action": "WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3186,
        "kind": "draw_timeline",
        "code": "TarzanParPanels._schedule_timeline_redraw = _schedule_timeline_redraw",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParPanels_old.py",
        "line": 3188,
        "kind": "draw_timeline",
        "code": "TarzanParPanels.draw_timeline = _par_draw_timeline_final",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 54,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 83,
        "kind": "canvas_delete_all",
        "code": "self.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/PAR/tarzanParWidgets.py",
        "line": 287,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/TarzanEhrTakeSandbox.py",
        "line": 545,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 35,
        "kind": "refresh_all",
        "code": "# - nie używa _refresh_all.",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/TarzanTakeProtocolLight.py",
        "line": 852,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 534,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 595,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 703,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 710,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 732,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 738,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 743,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 748,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 753,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 758,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 763,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 810,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 859,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 904,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 930,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 935,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 960,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 967,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanAxisSandbox.py",
        "line": 975,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 704,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1243,
        "kind": "canvas_delete_all",
        "code": "canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1411,
        "kind": "refresh_all",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1411,
        "kind": "after_refresh",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1657,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano ustawienia osi.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1666,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1677,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1770,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano ustawienia osi: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1807,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1818,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1828,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1838,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1848,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1858,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1867,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1891,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 1958,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2017,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_AXIS_DIALOG._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2018,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2095,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2107,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2120,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2211,
        "kind": "refresh_all",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2211,
        "kind": "after_refresh",
        "code": "self.after_idle(self._refresh_all)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2366,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=True, status=status)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2395,
        "kind": "refresh_all",
        "code": "dlg._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2396,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=\"Zastosowano ustawienia MAIN TAKE.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2509,
        "kind": "refresh_all",
        "code": "self._refresh_all(",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2520,
        "kind": "after_refresh",
        "code": "self._configure_after_id = self.after(40, self._flush_configure_refresh)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2683,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2960,
        "kind": "refresh_all",
        "code": "@profile_method('EHR_MAIN._refresh_all')",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 2961,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, light: bool = False, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 3029,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=True, status=None)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/EHR/tarzanEhrUi.py",
        "line": 3232,
        "kind": "refresh_all",
        "code": "self._refresh_all(light=False, status=f\"Wczytano TAKE TXT: {path.name}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/TarzanEhrTakeSandbox.py",
        "line": 545,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 35,
        "kind": "refresh_all",
        "code": "# - nie używa _refresh_all.",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/TarzanTakeProtocolLight.py",
        "line": 852,
        "kind": "canvas_delete_all",
        "code": "self.canvas.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 534,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 595,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 703,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 710,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 732,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 738,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 743,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 748,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 753,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 758,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 763,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 810,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 878,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 923,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 949,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 954,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 979,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 986,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/editor/tarzanAxisSandbox.py",
        "line": 994,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 534,
        "kind": "refresh_all",
        "code": "self._refresh_all()",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 595,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"VIEW Y SCALE\", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 596,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"MOUSE PRECISION\", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 597,
        "kind": "refresh_all",
        "code": "self._scale_row(box, \"TOP/BOTTOM MARGIN\", self.top_bottom_margin, 8, 60, 1, self._refresh_all)",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 703,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zastosowano strojenie STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 710,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano parametry mechaniki: {mechanics.axis_name}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 732,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wczytano preset TXT: {path}\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 738,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono domyślne parametry STEP.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 743,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Sinus test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 748,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Negative test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 753,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Zero cross test ustawiony.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 758,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Linia wyzerowana.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 763,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Przywrócono ostatni stan bazowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 810,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 878,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 923,
        "kind": "refresh_all",
        "code": "def _refresh_all(self, status: str | None = None) -> None:",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 949,
        "kind": "refresh_all",
        "code": "self._refresh_all(f\"Wybrano punkt {idx}.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 954,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"PAN linii.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 979,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Gotowy.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 986,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Dodano punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanAxisSandbox.py",
        "line": 994,
        "kind": "refresh_all",
        "code": "self._refresh_all(\"Usunięto punkt.\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 611,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 950,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 991,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1094,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1158,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1161,
        "kind": "after_refresh",
        "code": "self.after(self._camera_preview_refresh_ms, self._camera_preview_loop)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1372,
        "kind": "after_refresh",
        "code": "self.after(self._ui_refresh_ms, self._ui_loop)",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1434,
        "kind": "draw_khr",
        "code": "self._draw_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1435,
        "kind": "draw_khr",
        "code": "self._draw_khr()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1436,
        "kind": "draw_khr",
        "code": "self._draw_output()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1438,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_input\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1439,
        "kind": "draw_khr",
        "code": "def _draw_input(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1441,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1444,
        "kind": "draw_khr",
        "code": "self._draw_camera_input()",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1476,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_camera_input\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1477,
        "kind": "draw_khr",
        "code": "def _draw_camera_input(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1558,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_khr\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1559,
        "kind": "draw_khr",
        "code": "def _draw_khr(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1561,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1582,
        "kind": "draw_khr",
        "code": "@khr_profiled(\"KHR_UI._draw_output\")",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1583,
        "kind": "draw_khr",
        "code": "def _draw_output(self) -> None:",
        "action": "ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER"
    },
    {
        "file": "modes/editor/tarzanKHR.py",
        "line": 1585,
        "kind": "canvas_delete_all",
        "code": "c.delete(\"all\")",
        "action": "ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER"
    }
]


def create_default_tarzan_snajper() -> TarzanSnajper:
    """
    Tworzy Snajpera z pełną mapą sygnałów i celów wygenerowaną z repo.

    Adaptery rejestruje moduł, który ma realne obiekty:
        snajper.register_adapter("par_tkinter", TkWidgetSnajperAdapter())
        snajper.register_adapter("canvas_preview", TkCanvasSnajperAdapter())
        snajper.register_adapter("physical_nextion", NextionPhysicalSnajperAdapter(bridge))

    W EHR/KHR/Sandbox/Layout moduły rejestrują własne adaptery:
        ehr_canvas
        ehr_tkinter
        sandbox_canvas
        sandbox_tkinter
        timeline_canvas
        layout_canvas
        khr_canvas
        khr_tkinter
    """
    snajper = TarzanSnajper()
    snajper.register_signals(DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP)
    snajper.register_targets(DEFAULT_TARZAN_SNAJPER_TARGETS)
    return snajper


TARZAN_SNAJPER_USAGE_CONTRACT = """
1. SignalBus zostaje źródłem prawdy.
2. TarzanSnajper nie jest SignalBus i nie przechowuje prawdy systemu.
3. TarzanSnajper nie ma własnej pętli i nie skanuje celów.
4. TarzanSnajper jest aktywowany przez zmianę sygnału lub realną akcję.
5. nextion_tick znika jako model.
6. nextion_snajper_tick może tylko robić poll + flush_snajper_commands + after.
7. Dynamicznie nie używać refresh_all / widget.refresh / nextion_refresh_previews / refresh_axis_cards / canvas.delete("all").
8. Pełny render zostaje tylko dla struktury.
9. Po pełnym renderze trzeba zarejestrować itemy/widgety jako cele Snajpera.
10. Jedna zmiana = jeden strzał w konkretne cele.
"""
