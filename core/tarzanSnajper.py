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

from typing import Any, Callable, Dict, Iterable, List, Protocol, Tuple

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


# Centralne polityki odświeżania Snajpera.
# Snajper nie liczy ADRR i nie zna algorytmów EHR; decyduje tylko,
# jak często wolno strzelać w dany typ cięższego celu.
TARZAN_SNAJPER_REFRESH_POLICIES_MS: Dict[str, int] = {
    "IMMEDIATE": 0,
    "FINAL": 0,
    "LIVE_FAST": 50,
    "LIVE_MATRIX": 300,
    "PAGE_RESYNC": 0,
    "SLOW_RESYNC": 2000,
}

TarzanSnajperScheduler = Callable[[int, Callable[[], None]], Any]


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
        self.refresh_policies_ms: Dict[str, int] = dict(TARZAN_SNAJPER_REFRESH_POLICIES_MS)
        self._policy_pending: Dict[str, Tuple[str, Any]] = {}
        self._policy_scheduled: Dict[str, bool] = {}
        self._policy_generation: Dict[str, int] = {}

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

    def refresh_policy_interval_ms(self, policy: str) -> int:
        """Zwraca interwał polityki odświeżania zarządzanej przez Snajpera."""
        return max(0, int(self.refresh_policies_ms.get(str(policy or "IMMEDIATE"), 0)))

    def set_refresh_policy(self, policy: str, interval_ms: int) -> None:
        """Pozwala modułowi ustawić interwał bez rozlewania stałych po UI."""
        self.refresh_policies_ms[str(policy)] = max(0, int(interval_ms))

    def _policy_key(self, policy: str, logical_signal: str | None = None) -> str:
        """Buduje klucz harmonogramu Snajpera.

        LIVE_MATRIX jest ciężkim celem EHR i musi być rozdzielony per konkretny
        matrix/sygnał. Nie może być globalnym kubełkiem, bo wtedy jedna oś albo
        jeden FINAL mógłby skasować/nadpisać oczekujący live refresh innej osi.
        Pozostałe polityki zostają globalne dopóki nie dostaną własnego
        precyzyjnego kontraktu.
        """
        policy_name = str(policy or "IMMEDIATE")
        signal = str(logical_signal or "").strip()
        if policy_name == "LIVE_MATRIX" and signal:
            return f"{policy_name}:{signal}"
        return policy_name

    @staticmethod
    def _live_matrix_signal_for_final(logical_signal: str) -> str | None:
        """Zwraca odpowiadający live matrix dla finalnego matrixa osi EHR."""
        signal = str(logical_signal or "").strip()
        if signal.startswith("ehr_axis_") and signal.endswith("_final_matrix"):
            return signal[:-len("_final_matrix")] + "_live_matrix"
        return None

    def cancel_refresh_policy(self, policy: str, logical_signal: str | None = None) -> None:
        """Kasuje oczekujące zgłoszenie polityki i unieważnia stare callbacki.

        Gdy logical_signal jest podany, kasowany jest tylko dokładny cel
        polityki, np. LIVE_MATRIX:ehr_axis_0_live_matrix. Bez logical_signal
        kasowane są wszystkie klucze tej polityki; to zostaje jako narzędzie
        awaryjne, ale FINAL używa wariantu celowanego.
        """
        policy_name = str(policy or "")
        if not policy_name:
            return

        if logical_signal is not None:
            keys = [self._policy_key(policy_name, logical_signal)]
        else:
            prefix = f"{policy_name}:"
            keys = [
                key
                for key in set(self._policy_generation) | set(self._policy_pending) | set(self._policy_scheduled)
                if key == policy_name or key.startswith(prefix)
            ]
            if not keys:
                keys = [policy_name]

        for key in keys:
            self._policy_generation[key] = self._policy_generation.get(key, 0) + 1
            self._policy_pending.pop(key, None)
            self._policy_scheduled.pop(key, None)

    def fire_with_policy(
        self,
        logical_signal: str,
        value: Any,
        *,
        policy: str = "IMMEDIATE",
        scheduler: TarzanSnajperScheduler | None = None,
    ) -> None:
        """Strzela zgodnie z centralną polityką odświeżania Snajpera.

        IMMEDIATE/FINAL strzelają od razu.
        LIVE_MATRIX i inne polityki z interwałem większym od zera są
        koaleskowane: wiele zgłoszeń w czasie ruchu operatora daje jeden
        strzał z ostatnią wartością po upływie interwału. Snajper trzyma
        zasadę częstotliwości; zewnętrzny moduł dostarcza tylko mechanizm
        harmonogramu, np. Tk.after.
        """
        if not self.enabled:
            return

        policy_name = str(policy or "IMMEDIATE")
        # Finalny strzał po puszczeniu elementu ma pierwszeństwo nad
        # odpowiadającym mu LIVE_MATRIX. Kasujemy wyłącznie live matrix tej
        # samej osi, nie globalną politykę LIVE_MATRIX.
        if policy_name == "FINAL":
            live_matrix_signal = self._live_matrix_signal_for_final(logical_signal)
            if live_matrix_signal:
                self.cancel_refresh_policy("LIVE_MATRIX", logical_signal=live_matrix_signal)

        interval_ms = self.refresh_policy_interval_ms(policy_name)
        if interval_ms <= 0 or scheduler is None:
            self.fire(logical_signal, value)
            return

        policy_key = self._policy_key(policy_name, logical_signal)
        self._policy_pending[policy_key] = (logical_signal, value)
        if self._policy_scheduled.get(policy_key):
            return

        self._policy_scheduled[policy_key] = True
        generation = self._policy_generation.get(policy_key, 0)

        def _flush() -> None:
            self._flush_policy(policy_key, generation)

        scheduler(interval_ms, _flush)

    def _flush_policy(self, policy_key: str, generation: int) -> None:
        if generation != self._policy_generation.get(policy_key, 0):
            return
        self._policy_scheduled.pop(policy_key, None)
        item = self._policy_pending.pop(policy_key, None)
        if item is None:
            return
        logical_signal, value = item
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
4a. Cięższe odświeżenia live, np. LIVE_MATRIX, są koaleskowane polityką Snajpera.
5. Caliber ujednolica nazwę sygnału.
6. Bullet przygotowuje wartość/payload.
7. Target wskazuje cel.
8. Snajper strzela/odświeża.
9. Bridge obsługuje fizyczny Nextion.
10. Jedna zmiana = jeden strzał w konkretne cele.
"""


# ======================================================================
# SNAJPER HARDWARE POLICY — AKCJA -> REAKCJA, BRAK AKCJI -> IDLE
# ======================================================================
class TarzanSnajperHardwarePolicy:
    """Centralna polityka wybudzania hardware.

    To nie jest sterownik USB. Snajper wyznacza, czy dana zmiana/akcja jest
    fizycznym strzałem w hardware. HardwareBridge dopiero wykonuje połączenie
    PoKeys/I2C/wyjście i po krótkim oknie wraca do IDLE.
    """

    IDLE_MODES = {"", "tm", "idle", "stop", "none", "null", "manual_idle"}
    EXEC_MODES = {"taa", "tat", "auto", "play", "rec", "take", "ehr", "khr", "live_exec"}
    EXEC_TRANSPORT = {"PLAY", "REC", "RUN", "ACTIVE"}

    # Fizyczne zapisy/komendy, które wymagają PoKeys albo toru wykonawczego.
    PHYSICAL_SIGNAL_PREFIXES = (
        "par_lcd_",
        "par_matrix_",
        "par_f_led_",
    )
    PHYSICAL_SIGNAL_NAMES = {
        "play_p37_step_disconnect_manual",
        "cmd_run_diagnostics",
        "cmd_clear_alarms",
        "cmd_unlock_axes",
        "safety_axis_unlock",
        "rec_p46_led_f1",
        "rec_p48_led_f2",
        "rec_p50_led_f3",
        "rec_p52_led_f4",
    }
    PHYSICAL_ACTIONS = {
        "play_take",
        "take_play",
        "record_take",
        "take_record",
        "run_diagnostics",
        "test_lks_component",
        "lks_test_component",
        "test_component",
        "test_axis",
        "axis_test",
        "sensor_test",
        "sensor_read",
        "manual_record_arm",
        "manual_axis_step",
        "axis_enable",
        "clear_axis_errors",
        "set_mode_exec",
        "ehr_cmd",
        "khr_cmd",
        "camera_mode",
        "remote_action",
        "sok_set",
    }
    LIGHT_ACTIONS = {
        "hello",
        "get_state",
        "health",
        "ping",
        "connect",
        "disconnect",
        "nextion_connect",
        "nextion_sync",
        "sync",
        "set_page",
        "clear_transport_log",
        "preview_rrp_tap",
        "preview_rrp_set_value",
        "clap",
        "load_take",
        "take_load",
        "pause_take",
        "take_pause",
        "stop_take",
        "take_stop",
        "stop",
    }
    LKS_POKEYS_COMPONENTS = {
        "pok_play",
        "pok_rec",
        "lcd_1602",
        "matrix_led",
        "f_led",
        "f_button",
        "keypad",
        "i2c_bus",
        "light_bh1750",
    }
    LKS_LIGHT_COMPONENTS = {
        "linux_sys",
        "tsp_lan",
        "signalbus_sys",
        "snajper_sys",
        "next_5",
        "next_7",
        "cam_main",
        "cam_track",
        "par_sys",
        "ehr_sys",
        "take_sys",
    }

    @staticmethod
    def truthy(value: Any) -> bool:
        text = str(value).strip().lower()
        return text not in {"", "0", "false", "off", "none", "null", "stop", "idle", "tm"}

    @staticmethod
    def normalize_component(component: Any) -> str:
        raw = str(component or "").strip().lower()
        aliases = {
            "play": "pok_play",
            "pokeys_play": "pok_play",
            "pokeys_player": "pok_play",
            "player": "pok_play",
            "rec": "pok_rec",
            "reck": "pok_rec",
            "pokeys_rec": "pok_rec",
            "pokeys_reck": "pok_rec",
            "lcd": "lcd_1602",
            "lcd1602": "lcd_1602",
            "matrix": "matrix_led",
            "matrix8x8": "matrix_led",
            "led_matrix": "matrix_led",
            "f_buttons": "f_button",
            "buttons": "f_button",
            "f_leds": "f_led",
            "leds": "f_led",
            "bh1750": "light_bh1750",
            "light": "light_bh1750",
            "i2c": "i2c_bus",
            "bus": "i2c_bus",
            "nextion7": "next_7",
            "nextion_7": "next_7",
            "n7": "next_7",
            "nextion5": "next_5",
            "nextion_5": "next_5",
            "n5": "next_5",
            "par": "par_sys",
            "ehr": "ehr_sys",
            "take": "take_sys",
        }
        return aliases.get(raw, raw)

    def lks_component_needs_pokeys(self, component: Any) -> bool:
        return self.normalize_component(component) in self.LKS_POKEYS_COMPONENTS

    def lks_component_is_light(self, component: Any) -> bool:
        return self.normalize_component(component) in self.LKS_LIGHT_COMPONENTS

    def should_wake_for_signal(self, name: Any, value: Any, source: str = "") -> bool:
        sig = str(name or "").strip()
        if not sig:
            return False

        # Impuls wybudzenia sam w sobie jest obsługiwany przez HardwareBridge.
        if sig in {"cmd_hardware_awake", "hardware_realtime_required", "hardware_connected"}:
            return False

        if sig == "transport_state":
            return str(value).strip().upper() in {"PLAY", "REC"}

        if sig == "active_mode":
            mode = str(value).strip().lower()
            return mode in self.EXEC_MODES and mode not in self.IDLE_MODES

        # Ruch osi budzi tylko wtedy, gdy jest realna wartość wykonawcza.
        if sig.startswith("axis_"):
            if sig.endswith(("_dir", "_step", "_pulses", "_enable", "_speed", "_target")):
                return self.truthy(value)
            return False

        # RRP/SOK budzą tylko przy realnym ruchu/wartości, nie przy samym wyborze osi/statusie.
        if sig.startswith("rrp_"):
            if any(token in sig for token in ("value", "speed", "dir", "move", "step", "pulse")):
                return self.truthy(value)
            return False

        if sig.startswith("sok_"):
            if any(token in sig for token in ("value", "speed", "dir", "move", "step", "pulse", "set")):
                return self.truthy(value)
            return False

        if sig.startswith(self.PHYSICAL_SIGNAL_PREFIXES):
            return True

        if sig in self.PHYSICAL_SIGNAL_NAMES:
            return self.truthy(value)

        return False

    def should_wake_for_action(self, name: Any, payload: Any = None, source: str = "") -> bool:
        action = str(name or "").strip()
        if not action:
            return False
        if action in self.LIGHT_ACTIONS:
            return False

        data = payload if isinstance(payload, dict) else {}
        component = data.get("component") or data.get("name") or data.get("target") or data.get("device")
        if component and self.lks_component_needs_pokeys(component):
            return True
        if action in self.PHYSICAL_ACTIONS:
            return True
        if action.startswith(("axis_", "manual_axis_", "test_axis_", "sensor_", "hardware_", "lks_test")):
            return True
        return False

    def runtime_requires_realtime(
        self,
        *,
        active_mode: Any = "tM",
        transport_state: Any = "STOP",
        control_owner: Any = "",
        cmd_hardware_awake: Any = 0,
    ) -> bool:
        if self.truthy(cmd_hardware_awake):
            return True
        if str(transport_state or "").strip().upper() in {"PLAY", "REC"}:
            return True
        mode = str(active_mode or "").strip().lower()
        if mode in self.EXEC_MODES and mode not in self.IDLE_MODES:
            return True
        return False

    def grace_ms_for(self, kind: str = "default") -> int:
        """Krótki czas wybudzenia hardware po strzale Snajpera.

        Nie trzymamy PoKeys długo po teście. Klik LKS/PAR ma szybko dostać
        reakcję, a po zakończeniu akcji hardware wraca do IDLE.
        """
        key = str(kind or "default").lower()
        if key in {"lks", "diagnostic", "test"}:
            return 1500
        if key in {"move", "axis", "take", "rec", "play"}:
            return 2500
        if key in {"par", "nextion7", "ui"}:
            return 1200
        return 1500
