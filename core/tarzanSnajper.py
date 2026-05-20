from __future__ import annotations

"""
TARZAN_SNAJPER

Snajper strzela / odświeża.

Podział warstw:
    Caliber = ujednolica nazwę sygnału
    Bullet  = przygotowuje wartość/payload
    Target  = wskazuje cel
    Snajper = strzela/odświeża
    Bridge  = obsługuje fizyczny Nextion

Źródło prawdy:
    SignalBus
"""

from typing import Any, Dict, Iterable, List, Protocol, Tuple

from core.tarzanSnajperBullet import dir_int as bullet_dir_int, format_nextion_bullet
from core.tarzanSnajperCaliber import DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP, resolve_caliber
from core.tarzanSnajperTarget import (
    DEFAULT_TARZAN_SNAJPER_TARGETS,
    TARZAN_SNAJPER_ADAPTERS,
    TARZAN_SNAJPER_PROPS,
    TARZAN_SNAJPER_SCOPE_GROUPS,
    TarzanSnajperTarget,
    T,
)


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
        self._rrp_selected_axis: Dict[str, str] = {
            "p1": "",
            "p2": "",
        }

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

        logical_signal = self.signal_map.get(raw_signal) or resolve_caliber(raw_signal)

        self._remember_rrp_selected_axis(raw_signal, logical_signal, value)

        if not logical_signal:
            return

        self.fire(logical_signal, value)
        self._fire_rrp_value_from_axis_pulses(raw_signal, value)

    def _remember_rrp_selected_axis(self, raw_signal: str, logical_signal: str | None, value: Any) -> None:
        signal_names = {str(raw_signal or "").strip(), str(logical_signal or "").strip()}

        if signal_names.intersection({"rrp_p1_selected_axis", "par_rrp_p1_selected_axis", "par_rrp_p1_axis"}):
            self._rrp_selected_axis["p1"] = str(value or "").strip()
            return

        if signal_names.intersection({"rrp_p2_selected_axis", "par_rrp_p2_selected_axis", "par_rrp_p2_axis"}):
            self._rrp_selected_axis["p2"] = str(value or "").strip()
            return

    def _fire_rrp_value_from_axis_pulses(self, raw_signal: str, value: Any) -> None:
        raw = str(raw_signal or "").strip()

        if not raw.startswith("axis_") or not raw.endswith("_pulses"):
            return

        selected_axis = raw[len("axis_"):-len("_pulses")]

        if self._rrp_selected_axis.get("p1") == selected_axis:
            self.fire("rrp_p1_value", value)

        if self._rrp_selected_axis.get("p2") == selected_axis:
            self.fire("rrp_p2_value", value)

    def fire_many(self, updates: Dict[str, Any]) -> None:
        for logical_signal, value in updates.items():
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

    def fire_nextion_physical_resync(self, bus: Any, fast: bool = False) -> None:
        """
        Wymuszona ponowna wysyłka whitelisted pól trwałych tylko na fizyczny Nextion.
        fast=True (100ms) -> bez statycznego samoleczenia TAKE/settings
        fast=False (2000ms) -> bez TITLE/DIRECTOR; one idą po sendme / PAGE
        """
        # NEXTION_SNAJPER_V8: Cache i czas odświeżania są zarządzane wyłącznie tutaj.
        if fast:
            # FAST nie wymusza już statycznych pól TAKE/settings.
            # Pola live (osie, TC, sensory) idą normalnymi strzałami SignalBus/Snajpera.
            whitelist = {}
        else:
            # SLOW (2000ms) nie obsługuje już TITLE/DIRECTOR.
            # Te pola idą tylko po sendme / PAGE przez fire_nextion_page_loaded_resync().
            whitelist = {}

        # HOT FIELDS (10ms) are handled by normal SignalBus fires or live calls.
        # We don't resync HOT fields here unless specifically requested.
        if hasattr(self, "_resync_hot_counter"):
            self._resync_hot_counter += 1
        else:
            self._resync_hot_counter = 1

        for logical, bus_key in whitelist.items():
            val = None

            try:
                from editor.TFD.tfd_state import tfd_state
                if tfd_state:
                    if logical == "tfd_title":
                        val = tfd_state.title
                    elif logical == "tfd_director":
                        val = tfd_state.director
                    elif logical == "take_number":
                        val = tfd_state.take_number
                    elif logical == "take_status":
                        val = tfd_state.status
                    elif logical == "tfd_save_status_visible":
                        val = 1 if getattr(tfd_state, "save_status_visible", False) else 0
                    elif logical == "tfd_save_status":
                        val = getattr(tfd_state, "save_status_text", "")
            except Exception:
                pass

            if val is None:
                if hasattr(bus, "get"):
                    val = bus.get(f"par_{bus_key}")
                    if val is None:
                        val = bus.get(bus_key)
                else:
                    val = getattr(bus, f"par_{bus_key}", None)
                    if val is None:
                        val = getattr(bus, bus_key, None)

            if val is None:
                continue

            for target in self.targets.get(logical, []):
                if target.adapter == "physical_nextion":
                    cache_key = self._cache_key(target)
                    self.last_values.pop(cache_key, None)

            self.fire(logical, val)

    def fire_nextion_page_loaded_resync(self, bus: Any, page_id: str) -> int:
        """Jednorazowo odświeża statyczne metadane po sendme / PAGE Nextiona."""
        if not self.enabled:
            return 0

        page_id = str(page_id or "")
        page_targets = {
            "take_main": {
                "tfd_title": ("t1", "txt"),
                "tfd_director": ("t2", "txt"),
                "take_number": ("t_take", "txt"),
                "take_status": ("t_status", "txt"),
            },
            "settings_main": {
                "tfd_title": ("t_title", "txt"),
                "tfd_director": ("t_director", "txt"),
                "nextion_ui_cut": ("b_ui_cut", "val"),
            },
        }
        logical_to_component = page_targets.get(page_id)
        if not logical_to_component:
            return 0

        values = {
            "tfd_title": self._read_tfd_meta_value(
                bus,
                attr="title",
                fallback_keys=("par_tfd_title", "tfd_title", "take_title", "movie_title", "title"),
            ),
            "tfd_director": self._read_tfd_meta_value(
                bus,
                attr="director",
                fallback_keys=("par_tfd_director", "tfd_director", "take_director", "movie_director", "director"),
            ),
            "take_number": self._read_tfd_meta_value(
                bus,
                attr="take_number",
                fallback_keys=("par_take_number", "take_number", "take_label", "loaded_take_path"),
            ),
            "take_status": self._read_tfd_meta_value(
                bus,
                attr="status",
                fallback_keys=("par_take_status", "take_status", "par_mode", "system_status"),
            ),
            "nextion_ui_cut": self._read_tfd_meta_value(
                bus,
                attr="nextion_ui_cut",
                fallback_keys=("par_nextion_ui_cut", "nextion_ui_cut"),
            ),
        }

        adapter = self.adapters.get("physical_nextion")
        if adapter is None:
            return 0

        fired = 0
        for logical, target_spec in logical_to_component.items():
            component, prop = target_spec
            value = values.get(logical)
            if value is None:
                value = 0 if prop == "val" else ""
            if prop == "val" and isinstance(value, bool):
                value = 1 if value else 0
            normalized = self.normalize_value(value)

            for target in self.targets.get(logical, []):
                if target.adapter != "physical_nextion":
                    continue
                if target.scope != page_id:
                    continue
                if target.target != component:
                    continue
                if target.prop != prop:
                    continue

                cache_key = self._cache_key(target)
                self.last_values.pop(cache_key, None)
                adapter.update_target(target, value)
                self.last_values[cache_key] = normalized
                fired += 1

        return fired

    @staticmethod
    def _read_tfd_meta_value(bus: Any, attr: str, fallback_keys: Tuple[str, ...]) -> Any:
        """Czyta TITLE/DIRECTOR najpierw z TFDState, potem awaryjnie z SignalBus."""
        try:
            from editor.TFD.tfd_state import tfd_state
            if tfd_state is not None:
                value = getattr(tfd_state, attr, None)
                if value is not None:
                    return value
        except Exception:
            pass

        for key in fallback_keys:
            try:
                if hasattr(bus, "get"):
                    value = bus.get(key)
                else:
                    value = getattr(bus, key, None)
            except Exception:
                value = None
            if value is not None:
                return value

        return None

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
        self.panels: Dict[str, Any] = {}

    def register_item(self, scope: str, target: str, prop: str, canvas: Any, item_id: int) -> None:
        self.items[f"{scope}.{target}.{prop}"] = (canvas, item_id)

    def register_canvas_panel(self, scope: str, panel: Any) -> None:
        """
        Rejestruje cały panel podglądu Nextiona w Snajperze.
        Panel musi posiadać metodę register_snajper_canvas_item.
        """
        self.panels[scope] = panel
        if hasattr(panel, "register_snajper_canvas_item"):
            original_register = panel.register_snajper_canvas_item

            def wrapped_register(page: str, component: str, prop: str, item_id: int):
                original_register(page, component, prop, item_id)
                self.register_item(scope, component, prop, panel.screen_canvas, item_id)

            panel.register_snajper_canvas_item = wrapped_register

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
        if target.prop == "ui_cut":
            panel = self.panels.get(target.scope)
            if panel and hasattr(panel, "set_ui_cut"):
                panel.set_ui_cut(value)
            return

        item = self.items.get(f"{target.scope}.{target.target}.{target.prop}")
        if item is None:
            return
        canvas, item_id = item
        if target.prop in {"text", "txt", "val", "state", "en", "tim", "pic"}:
            canvas.itemconfigure(item_id, text=str(value))
            return
        if target.prop == "pco":
            color_hex = self._nextion_color_to_hex(str(value))
            canvas.itemconfigure(item_id, fill=color_hex)
            return
        if target.prop == "coords":
            if isinstance(value, (list, tuple)):
                canvas.coords(item_id, *value)
            return
        if target.prop == "visible":
            canvas.itemconfigure(item_id, state="normal" if bool(value) else "hidden")
            return

    @staticmethod
    def _nextion_color_to_hex(nextion_color: str) -> str:
        try:
            val = int(nextion_color)
            r = (val >> 11) & 0x1F
            g = (val >> 5) & 0x3F
            b = val & 0x1F
            r = int(r * 255 / 31)
            g = int(g * 255 / 63)
            b = int(b * 255 / 31)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#ffffff"


class NextionPhysicalSnajperAdapter:
    RED_565 = 63488
    GREEN_565 = 2016

    def __init__(self, bridge: Any) -> None:
        self.bridge = bridge
        self._xyz = {"x": 0, "y": 0, "z": 0}
        self._axis_dir: Dict[str, int] = {f"t_axis{i}": 0 for i in range(6)}

    def update_target(self, target: TarzanSnajperTarget, value: Any) -> None:
        if not hasattr(self.bridge, "queue_snajper_command"):
            return

        # Zachowujemy kierunek dla koloru licznika osi take_main.
        if target.scope == "take_main" and target.target.startswith("t_axis") and target.prop == "pco":
            self._axis_dir[target.target] = bullet_dir_int(value)

        # Zachowujemy kierunek dla koloru licznika osi rrp_main.
        if target.scope == "rrp_main" and target.target.endswith("_val") and target.prop == "pco":
            self._axis_dir[target.target] = bullet_dir_int(value)

        out_value = self._format_value(target, value)
        self.bridge.queue_snajper_command(
            scope=target.scope,
            component=target.target,
            prop=target.prop,
            value=out_value,
        )

    def _format_value(self, target: TarzanSnajperTarget, value: Any) -> Any:
        return format_nextion_bullet(
            target=target,
            value=value,
            axis_dir_get=self._axis_dir.get,
        )


def create_default_tarzan_snajper() -> TarzanSnajper:
    """
    Tworzy Snajpera z pełną mapą sygnałów i celów.

    Adaptery rejestruje moduł, który ma realne obiekty:
        snajper.register_adapter("par_tkinter", TkWidgetSnajperAdapter())
        snajper.register_adapter("canvas_preview", TkCanvasSnajperAdapter())
        snajper.register_adapter("physical_nextion", NextionPhysicalSnajperAdapter(bridge))
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
5. Caliber ujednolica nazwę sygnału.
6. Bullet przygotowuje wartość/payload.
7. Target wskazuje cel.
8. Snajper strzela/odświeża.
9. Bridge obsługuje fizyczny Nextion.
10. Jedna zmiana = jeden strzał w konkretne cele.
"""
