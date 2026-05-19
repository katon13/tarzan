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
import re


# =============================================================================
# PEŁNE SŁOWNIKI KONTRAKTU — UZUPEŁNIONE Z REPO
# =============================================================================

TARZAN_SNAJPER_ADAPTERS: Tuple[str, ...] = ('physical_nextion', 'canvas_preview', 'par_tkinter', 'ehr_canvas', 'ehr_tkinter', 'sandbox_canvas', 'sandbox_tkinter', 'timeline_canvas', 'layout_canvas', 'khr_canvas', 'khr_tkinter', 'tfd_adapter', 'take_adapter', 'log_adapter', 'signal_row')

TARZAN_SNAJPER_PROPS: Tuple[str, ...] = ('coords', 'en', 'pco', 'pic', 'state', 'text', 'tim', 'txt', 'val', 'value', 'visible')

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
            # Próbujemy pobrać z busa (prefiks par_ lub bezpośrednio)
            val = None
            
            # PRIORYTET TFD_STATE: tfd_state jeśli dostępny globalnie
            try:
                from editor.TFD.tfd_state import tfd_state
                if tfd_state:
                    if logical == "tfd_title": val = tfd_state.title
                    elif logical == "tfd_director": val = tfd_state.director
                    elif logical == "take_number": val = tfd_state.take_number
                    elif logical == "take_status": val = tfd_state.status
                    elif logical == "tfd_save_status_visible": val = 1 if getattr(tfd_state, "save_status_visible", False) else 0
                    elif logical == "tfd_save_status": val = getattr(tfd_state, "save_status_text", "")
            except:
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

            # Czyścimy cache tylko dla tego konkretnego celu na fizycznym urządzeniu
            # tak aby fire(...) zawsze wygenerowało komendę do adaptera.
            for target in self.targets.get(logical, []):
                if target.adapter == "physical_nextion":
                    cache_key = self._cache_key(target)
                    self.last_values.pop(cache_key, None)
            
            # Odpalamy fire - trafi na physical_nextion bez blokady cache
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
            # Podmieniamy metodę w panelu, aby każde wywołanie trafiało też do adaptera
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

        # Zachowujemy kierunek dla koloru licznika osi take_main
        if target.scope == "take_main" and target.target.startswith("t_axis") and target.prop == "pco":
            self._axis_dir[target.target] = self._dir_int(value)

        # Zachowujemy kierunek dla koloru licznika osi rrp_main
        if target.scope == "rrp_main" and target.target.endswith("_val") and target.prop == "pco":
             # Tu value to kierunek: 1 (PLUS) lub 0 (MINUS)
             self._axis_dir[target.target] = self._dir_int(value)

        out_value = self._format_value(target, value)
        self.bridge.queue_snajper_command(
            scope=target.scope,
            component=target.target,
            prop=target.prop,
            value=out_value,
        )

    def _format_value(self, target: TarzanSnajperTarget, value: Any) -> Any:
        if target.scope == "rrp_main" and target.target in {"t_p1_val", "t_p2_val"} and target.prop in {"txt", "text"}:
            return self._axis_counter(value, self._axis_dir.get(target.target, 0))
        if target.scope == "rrp_main" and target.target in {"t_p1_val", "t_p2_val"} and target.prop == "pco":
            return self.GREEN_565 if self._dir_int(value) == 1 else self.RED_565

        if target.scope == "level_xyz" and target.target in {"va0", "va1", "va2", "va3"} and target.prop == "val":
            return self._clamp_int(value, -100, 100)
        if target.scope == "take_main" and target.target == "t0" and target.prop in {"txt", "text"}:
            return self._tc_text(value)
        if target.scope == "take_main" and target.target in {"tx", "ty", "tz"} and target.prop in {"txt", "text"}:
            return self._xyz_axis_text(target.target, value)
        if target.scope == "take_main" and target.target in {"tx", "ty", "tz"} and target.prop == "pco":
            sign = self._xyz_axis_sign(target.target, value)
            if sign == 1: return self.GREEN_565
            if sign == -1: return self.RED_565
            return 65535 # Biały dla 0
        if target.scope == "take_main" and target.target.startswith("t_axis") and target.prop in {"txt", "text"}:
            return self._axis_counter(value, self._axis_dir.get(target.target, 0))
        if target.scope == "take_main" and target.target.startswith("t_axis") and target.prop == "pco":
            return self.GREEN_565 if self._dir_int(value) == 1 else self.RED_565
        if target.scope == "take_main" and target.target == "t_light" and target.prop in {"txt", "text"}:
            return self._one_decimal(value, suffix="")
        if target.scope == "take_main" and target.target == "t_temp" and target.prop in {"txt", "text"}:
            return self._one_decimal(value, suffix=" C")
        if target.scope == "take_main" and target.target in {"t_laser", "t_shock"} and target.prop in {"txt", "text"}:
            return self._binary(value)
        if target.scope == "take_main" and target.target == "t_status" and target.prop in {"txt", "text"}:
            return self._mode_text(value)
        if target.scope == "take_main" and target.target == "t_take" and target.prop in {"txt", "text"}:
            return self._take_label(value)
        if target.scope == "take_main" and target.target == "p5" and target.prop == "pic":
            # Ikona CLAP: 51 = aktywny (czerwony), 50 = standard
            return 51 if bool(value) else 50
        return value

    @staticmethod
    def _clamp_int(value: Any, minimum: int, maximum: int) -> int:
        try:
            return max(minimum, min(maximum, int(round(float(value)))))
        except Exception:
            return minimum

    @staticmethod
    def _axis_counter(value: Any, direction: int = 0) -> str:
        # Licznik impulsów jest wartością stałą/narastającą.
        # Kierunek pokazuje kolor .pco, więc tekst nie ma znaku +/-.
        try:
            mag = abs(int(round(float(value))))
            return f"{mag:06d}"
        except Exception:
            text = str(value).strip()
            if text.startswith(("+", "-")):
                text = text[1:]
            return text

    @staticmethod
    def _one_decimal(value: Any, suffix: str = "") -> str:
        try:
            return f"{float(value):.1f}{suffix}"
        except Exception:
            return str(value)

    @staticmethod
    def _binary(value: Any) -> str:
        try:
            return "1" if int(float(value or 0)) else "0"
        except Exception:
            text = str(value).strip().upper()
            return "1" if text in {"1", "ON", "TRUE", "YES", "HIGH"} else "0"

    @staticmethod
    def _dir_int(value: Any) -> int:
        try:
            return 1 if int(float(value or 0)) == 1 else 0
        except Exception:
            return 1 if str(value).strip() in {"1", "+", "PLUS", "RIGHT", "UP"} else 0

    @staticmethod
    def _xyz_components(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return {
                "tx": value.get("x", value.get("tx", 0)),
                "ty": value.get("y", value.get("ty", 0)),
                "tz": value.get("z", value.get("tz", 0)),
            }
        if isinstance(value, (list, tuple)):
            vals = list(value)[:3]
        else:
            text = str(value).strip()
            if "," in text or ";" in text or " " in text:
                vals = [p for p in re.split(r"[;,\s]+", text) if p][:3]
            else:
                vals = [value]
        while len(vals) < 3:
            vals.append(0)
        return {"tx": vals[0], "ty": vals[1], "tz": vals[2]}

    @staticmethod
    def _xyz_axis_number(axis_target: str, value: Any) -> int:
        # Jeżeli Snajper odpala osobny sygnał level_x/level_y/level_z,
        # do targetu tx/ty/tz trafia pojedyncza liczba i trzeba ją traktować
        # jako wartość tej konkretnej osi, nie jako pierwszy element pakietu XYZ.
        if not isinstance(value, (dict, list, tuple)):
            text = str(value).strip()
            if not ("," in text or ";" in text or " " in text):
                raw = value
            else:
                components = NextionPhysicalSnajperAdapter._xyz_components(value)
                raw = components.get(axis_target, 0)
        else:
            components = NextionPhysicalSnajperAdapter._xyz_components(value)
            raw = components.get(axis_target, 0)
        try:
            return max(-100, min(100, int(round(float(raw)))))
        except Exception:
            return 0

    @staticmethod
    def _xyz_axis_text(axis_target: str, value: Any) -> str:
        # Nowe HMI ma trzy osobne pola: tx, ty, tz.
        # Tekst nie ma znaku +/-; znak pokazuje kolor .pco danego pola.
        number = NextionPhysicalSnajperAdapter._xyz_axis_number(axis_target, value)
        return f"{abs(number):03d}"

    @staticmethod
    def _xyz_axis_sign(axis_target: str, value: Any) -> int:
        number = NextionPhysicalSnajperAdapter._xyz_axis_number(axis_target, value)
        if number > 0: return 1
        if number < 0: return -1
        return 0

    @staticmethod
    def _take_label(value: Any) -> str:
        text = str(value).strip()
        if not text:
            return text
        m = re.search(r"TAKE[_\s-]*(\d+).*?[vV](\d+)", text)
        if m:
            return f"{int(m.group(1))} v{int(m.group(2))}"
        m = re.search(r"(\d{1,3})[_\s-]*[vV](\d+)", text)
        if m:
            return f"{int(m.group(1))} v{int(m.group(2))}"
        return text

    @staticmethod
    def _tc_text(value: Any) -> str:
        text = str(value).strip()
        if not text:
            return "00:00:00:000"
        if ":" in text:
            return text
        try:
            ms = max(0, int(round(float(text))))
            h = ms // 3_600_000
            ms %= 3_600_000
            m = ms // 60_000
            ms %= 60_000
            sec = ms // 1000
            milli = ms % 1000
            return f"{h:02d}:{m:02d}:{sec:02d}:{milli:03d}"
        except Exception:
            return text

    @staticmethod
    def _mode_text(value: Any) -> str:
        try:
            iv = int(float(value))
            if iv == 0:
                return "TEST"
            if iv == 1:
                return "LIVE"
            if iv == 2:
                return "MIX"
        except Exception:
            pass
        return str(value).upper()


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

    # MAPOWANIE SYGNAŁÓW SENSORÓW DLA SNAJPERA
    'par_shock': 'sensor_shock',
    'par_laser': 'sensor_laser',
    'par_limits': 'sensor_limits',
    'par_light': 'sensor_light',
    'par_temp': 'sensor_temp',
    'par_xyz': 'sensor_xyz',
    'par_level_x': 'level_x',
    'par_level_y': 'level_y',
    'par_level_z': 'level_z',
    'par_take_number': 'take_number',
    'par_take_status': 'take_status',
    'par_take_timecode': 'take_timecode',
    'par_take_clap': 'take_clap',

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
}
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
5. snajper_removed_legacy_tick znika jako model.
6. nextion_snajper_tick może tylko robić poll + flush_snajper_commands + after.
7. Dynamicznie nie używać refresh_all / snajper_removed_widget_refresh / snajper_removed_nextion_previews / snajper_removed_axis_cards / canvas.snajper_removed_delete_all().
8. Pełny render zostaje tylko dla struktury.
9. Po pełnym renderze trzeba zarejestrować itemy/widgety jako cele Snajpera.
10. Jedna zmiana = jeden strzał w konkretne cele.
"""


# TARZAN_SNAJPER_STAGE2_SECTION_ALIASES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "sensor_temp_c": "sensor_temp",
    "temperature_c": "sensor_temp",
    "sensor_light_lux": "sensor_light",
    "light_lux": "sensor_light",
    "sensor_xyz": "sensor_xyz",
    "sensor_level_z": "sensor_xyz",
    "step_dir_stream": "step_dir_stream",
    "protocol_tick": "step_dir_stream",
})


# TARZAN_SNAJPER_STAGE3_SECTION_ALIASES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "ehr_axis_curve": "ehr_axis_0_curve",
    "ehr_step_preview": "ehr_axis_0_step_preview",
    "ehr_axis_metrics": "ehr_axis_0_metrics",
    "sandbox_curve": "sandbox_curve",
    "sandbox_step_preview": "sandbox_step_preview",
    "sandbox_metrics": "sandbox_metrics",
    "khr_input_marker": "khr_input_marker",
    "khr_output_marker": "khr_output_marker",
    "khr_status": "khr_status",
})


# TARZAN_SNAJPER_STAGE4_STEP_DIR_LIVE_ALIASES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "axis_0_step": "step_dir_stream",
    "axis_1_step": "step_dir_stream",
    "axis_2_step": "step_dir_stream",
    "axis_3_step": "step_dir_stream",
    "axis_4_step": "step_dir_stream",
    "axis_5_step": "step_dir_stream",
    "axis_0_dir": "step_dir_stream",
    "axis_1_dir": "step_dir_stream",
    "axis_2_dir": "step_dir_stream",
    "axis_3_dir": "step_dir_stream",
    "axis_4_dir": "step_dir_stream",
    "axis_5_dir": "step_dir_stream",
    "axis_0_ctr": "step_dir_stream",
    "axis_1_ctr": "step_dir_stream",
    "axis_2_ctr": "step_dir_stream",
    "axis_3_ctr": "step_dir_stream",
    "axis_4_ctr": "step_dir_stream",
    "axis_5_ctr": "step_dir_stream",
    "step_dir_stream": "step_dir_stream",
    "protocol_tick": "step_dir_stream",
})
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("step_dir_stream", [])


# TARZAN_SNAJPER_LOGI_TAKE_NEXTION_ALIASES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "take_time_ms": "take_time_ms",
    "take_timecode": "take_timecode",
    "take_number": "take_number",
    "take_status": "take_status",
    "par_log": "par_log",
    "log_event": "par_log",
    "system_status": "system_status",
    "par_error": "par_error",
    "nextion_ui_cut": "nextion_ui_cut",
})


# TARZAN_SNAJPER_LOGI_NEXTION_BRIDGE_FIX_ALIASES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "take_time_ms": "take_time_ms",
    "take_timecode": "take_timecode",
    "tfd_tc": "take_timecode",
    "par_mode": "par_mode",
    "sensor_light_lux": "sensor_light_lux",
    "sensor_temp_c": "sensor_temp_c",
    "sensor_limits_status": "sensor_limits_status",
    "sensor_shock_state": "sensor_shock_state",
    "sensor_laser_set": "sensor_laser_set",
})


# TARZAN_SNAJPER_OBECNE_ZASADY_ALIASES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "take_time_ms": "take_time_ms",
    "take_timecode": "take_timecode",
    "tfd_tc": "take_timecode",
    "par_mode": "par_mode",
    "sensor_light_lux": "sensor_light_lux",
    "sensor_temp_c": "sensor_temp_c",
    "sensor_limits_status": "sensor_limits_status",
    "sensor_shock_state": "sensor_shock_state",
    "sensor_laser_set": "sensor_laser_set",
})


# TARZAN_SNAJPER_NEXTION_PHYSICAL_BINDINGS
# Fizyczny Nextion korzysta z istniejącego katalogu celów Snajpera.
# Nie ma tu ręcznej mapy panelu PAR: to są brakujące aliasy i targety katalogowe.
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "take_time_ms": "take_time_ms",
    "take_timecode": "take_timecode",
    "tfd_tc": "take_timecode",
    "take_number": "take_number",
    "take_status": "take_status",
    "axis_0_value": "axis_0_value",
    "axis_1_value": "axis_1_value",
    "axis_2_value": "axis_2_value",
    "axis_3_value": "axis_3_value",
    "axis_4_value": "axis_4_value",
    "axis_5_value": "axis_5_value",
    "axis_cam_h_pulses": "axis_0_value",
    "axis_cam_v_pulses": "axis_1_value",
    "axis_cam_t_pulses": "axis_2_value",
    "axis_cam_f_pulses": "axis_3_value",
    "axis_arm_h_pulses": "axis_4_value",
    "axis_arm_v_pulses": "axis_5_value",
    "sensor_level_x": "level_x",
    "sensor_level_y": "level_y",
    "level_x": "level_x",
    "level_y": "level_y",
    "sensor_xyz": "sensor_xyz",
    "sensor_level_z": "sensor_xyz",
    "sensor_light_lux": "sensor_light_lux",
    "light_lux": "sensor_light_lux",
    "sensor_temp_c": "sensor_temp_c",
    "temperature_c": "sensor_temp_c",
    "sensor_limits_status": "sensor_limits_status",
    "sensor_laser_set": "sensor_laser_set",
    "sensor_shock_state": "sensor_shock_state",
    "par_mode": "par_mode",
    "live_test_mode": "par_mode",
    "system_status": "system_status",
    "settings_main.t_title.txt": "nextion_settings_main_t_title_txt",
    "settings_main.t_director.txt": "nextion_settings_main_t_director_txt",

    # TARZAN_TFD_META: jeden logiczny sygnał metadanych, dwa istniejące cele Snajpera.
    # settings_main służy do edycji, take_main.t1/t2 do podglądu w TAKE.
    "tfd_title": "tfd_title",
    "take_title": "tfd_title",
    "movie_title": "tfd_title",
    "title": "tfd_title",
    "tfd_director": "tfd_director",
    "take_director": "tfd_director",
    "movie_director": "tfd_director",
    "director": "tfd_director",
})

DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("take_time_ms", [
    T("physical_nextion", "take_main", "t0", "txt"),
    T("canvas_preview", "take_main", "t0", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("take_number", [
    T("physical_nextion", "take_main", "t_take", "txt"),
    T("canvas_preview", "take_main", "t_take", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("take_status", [
    T("physical_nextion", "take_main", "t_status", "txt"),
    T("canvas_preview", "take_main", "t_status", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_xyz", [
    T("physical_nextion", "take_main", "t_xyz", "txt"),
    T("canvas_preview", "take_main", "t_xyz", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_light_lux", [
    T("physical_nextion", "take_main", "t_light", "txt"),
    T("canvas_preview", "take_main", "t_light", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_temp_c", [
    T("physical_nextion", "take_main", "t_temp", "txt"),
    T("canvas_preview", "take_main", "t_temp", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_limits_status", [
    T("physical_nextion", "take_main", "t_limits", "txt"),
    T("canvas_preview", "take_main", "t_limits", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_laser_set", [
    T("physical_nextion", "take_main", "t_laser", "txt"),
    T("canvas_preview", "take_main", "t_laser", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_shock_state", [
    T("physical_nextion", "take_main", "t_shock", "txt"),
    T("canvas_preview", "take_main", "t_shock", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("par_mode", [
    T("physical_nextion", "take_main", "t_status", "txt"),
    T("canvas_preview", "take_main", "t_status", "txt"),
])
DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("system_status", [
    T("physical_nextion", "take_main", "t_status", "txt"),
    T("canvas_preview", "take_main", "t_status", "txt"),
])

# TARZAN_SNAJPER_NEXTION_PHYSICAL_FORMAT_FIXES
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "take_tc": "take_timecode",
    "tc": "take_timecode",
    "timecode": "take_timecode",
    "TAKE_TIME_MS": "take_time_ms",
    "TAKE_TC": "take_timecode",
    "take_version": "take_number",
    "take_file": "take_number",
    "take_path": "take_number",
    "active_take_path": "take_number",
    "axis_0_dir": "axis_0_dir",
    "axis_1_dir": "axis_1_dir",
    "axis_2_dir": "axis_2_dir",
    "axis_3_dir": "axis_3_dir",
    "axis_4_dir": "axis_4_dir",
    "axis_5_dir": "axis_5_dir",
    "level_z": "sensor_xyz",
    "shock_state": "sensor_shock_state",
    "laser_state": "sensor_laser_set",
})

DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "axis_cam_h_dir": "axis_0_dir",
    "axis_cam_v_dir": "axis_1_dir",
    "axis_cam_t_dir": "axis_2_dir",
    "axis_cam_f_dir": "axis_3_dir",
    "axis_arm_h_dir": "axis_4_dir",
    "axis_arm_v_dir": "axis_5_dir",
    "axis_cam_h_pos": "axis_0_value",
    "axis_cam_v_pos": "axis_1_value",
    "axis_cam_t_pos": "axis_2_value",
    "axis_cam_f_pos": "axis_3_value",
    "axis_arm_h_pos": "axis_4_value",
    "axis_arm_v_pos": "axis_5_value",
})

DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("take_timecode", [
    T("physical_nextion", "take_main", "t0", "txt"),
    T("canvas_preview", "take_main", "t0", "txt"),
])

for _idx in range(6):
    DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(f"axis_{_idx}_dir", [
        T("physical_nextion", "take_main", f"t_axis{_idx}", "pco"),
        T("canvas_preview", "take_main", f"t_axis{_idx}", "pco"),
    ])


# TARZAN_SNAJPER_NEXTION_REAL_REPO_BINDINGS_2026_05_18
# Dopięcie istniejących sygnałów repo do istniejących celów Snajpera.
# Bez ręcznego targetu panelowego, bez nowego bridge, bez refresh_all.
_DEFAULT_NEXTION_AXIS_DIR = {
    "axis_cam_h_dir": "axis_0_dir",
    "axis_cam_v_dir": "axis_1_dir",
    "axis_cam_t_dir": "axis_2_dir",
    "axis_cam_f_dir": "axis_3_dir",
    "axis_arm_h_dir": "axis_4_dir",
    "axis_arm_v_dir": "axis_5_dir",
}
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update(_DEFAULT_NEXTION_AXIS_DIR)
for _idx in range(6):
    _logical = f"axis_{_idx}_dir"
    _targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(_logical, [])
    _target = T("physical_nextion", "take_main", f"t_axis{_idx}", "pco")
    if _target not in _targets:
        _targets.append(_target)

# TAKE numer/wersja i TC wracają przez Snajpera jako zwykłe sygnały BUS.
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "loaded_take_path": "take_number",
    "take_label": "take_number",
    "TAKE_TIME_MS": "take_time_ms",
})
for _logical, _target in {
    "take_time_ms": T("physical_nextion", "take_main", "t0", "txt"),
    "take_timecode": T("physical_nextion", "take_main", "t0", "txt"),
    "take_number": T("physical_nextion", "take_main", "t_take", "txt"),
}.items():
    _targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(_logical, [])
    if _target not in _targets:
        _targets.append(_target)


# TARZAN_SNAJPER_NEXTION_REAL_SIGNALS_FIX_2026_05_18
# Istniejące cele Snajpera. Bez ręcznych map panelu, bez nowego bridge.
# Rzeczywista kolejność osi w obecnym PAR/SOK: CAM_H, CAM_V, ARM_T, CAM_F, ARM_H, ARM_V.
_TARZAN_NEXTION_AXIS_BINDINGS = {
    "axis_cam_h": 0,
    "axis_cam_v": 1,
    "axis_arm_t": 2,
    "axis_cam_f": 3,
    "axis_arm_h": 4,
    "axis_arm_v": 5,
}
for _base, _idx in _TARZAN_NEXTION_AXIS_BINDINGS.items():
    DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
        f"{_base}_pulses": f"axis_{_idx}_value",
        f"{_base}_pos": f"axis_{_idx}_value",
        f"{_base}_dir": f"axis_{_idx}_dir",
        f"{_base}_auto_dir": f"axis_{_idx}_dir",
        f"{_base}_rec_dir": f"axis_{_idx}_dir",
        f"{_base}_step": "step_dir_stream",
        f"{_base}_auto_step": "step_dir_stream",
        f"{_base}_rec_step": "step_dir_stream",
    })
    _value_target = T("physical_nextion", "take_main", f"t_axis{_idx}", "txt")
    _value_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(f"axis_{_idx}_value", [])
    if _value_target not in _value_targets:
        _value_targets.append(_value_target)
    _dir_target = T("physical_nextion", "take_main", f"t_axis{_idx}", "pco")
    _dir_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(f"axis_{_idx}_dir", [])
    if _dir_target not in _dir_targets:
        _dir_targets.append(_dir_target)

# SOK PAN/TILT stare sygnały przycisków są tylko wejściem. Snajper strzela do istniejących celów osi.
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "rec_p17_bridge_play_dir_x": "axis_0_dir",
    "rec_p20_bridge_play_ctr_x": "step_dir_stream",
    "rec_p18_bridge_play_dir_y": "axis_1_dir",
    "rec_p21_bridge_play_ctr_y": "step_dir_stream",
})

# TAKE/TC muszą mieć jawne targety po ostatniej wartości, aby t0 i t_take odświeżały się przez Snajpera.
for _logical, _target in {
    "take_time_ms": T("physical_nextion", "take_main", "t0", "txt"),
    "take_timecode": T("physical_nextion", "take_main", "t0", "txt"),
    "take_number": T("physical_nextion", "take_main", "t_take", "txt"),
    "take_status": T("physical_nextion", "take_main", "t_status", "txt"),
}.items():
    _targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(_logical, [])
    if _target not in _targets:
        _targets.append(_target)


# TARZAN_SNAJPER_TC_SINGLE_PHYSICAL_TARGET_2026_05_18
# Fizyczny komponent take_main.t0 dostaje tylko gotowy TC.
# take_time_ms zostaje sygnałem BUS dla logiki, ale nie dubluje strzału na t0.
_take_ms_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.get("take_time_ms", [])
DEFAULT_TARZAN_SNAJPER_TARGETS["take_time_ms"] = [
    _target for _target in _take_ms_targets
    if not (
        _target.adapter == "physical_nextion"
        and _target.scope == "take_main"
        and _target.target == "t0"
        and _target.prop in {"txt", "text"}
    )
]
_tc_target = T("physical_nextion", "take_main", "t0", "txt")
_tc_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("take_timecode", [])
if _tc_target not in _tc_targets:
    _tc_targets.append(_tc_target)

# TARZAN_SNAJPER_NEXTION_XYZ_SIGNED_TEXT_2026_05_18
# XYZ zostaje w jednym komponencie t_xyz, więc znak +/- jest w tekście.
# Nie wysyłamy .pco dla t_xyz, żeby Snajper nie zmieniał koloru całego pola.
_xyz_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_xyz", [])
DEFAULT_TARZAN_SNAJPER_TARGETS["sensor_xyz"] = [
    _target for _target in _xyz_targets
    if not (
        _target.adapter == "physical_nextion"
        and _target.scope == "take_main"
        and _target.target == "t_xyz"
        and _target.prop == "pco"
    )
]

# TARZAN_SNAJPER_TC_TARGET_GUARD_2026_05_18
# TC ma tylko jeden fizyczny tekstowy cel na take_main: t0.txt.
# t_status jest polem LIVE/TEST/status i nie może dostać TC ani stanów CLAP.
_tc_clean_targets = []
for _target in DEFAULT_TARZAN_SNAJPER_TARGETS.get("take_timecode", []):
    if _target.adapter == "physical_nextion" and _target.scope == "take_main" and _target.target == "t_status":
        continue
    if _target.adapter == "canvas_preview" and _target.scope == "take_main" and _target.target == "t_status":
        continue
    _tc_clean_targets.append(_target)
_tc_main_target = T("physical_nextion", "take_main", "t0", "txt")
if _tc_main_target not in _tc_clean_targets:
    _tc_clean_targets.append(_tc_main_target)
DEFAULT_TARZAN_SNAJPER_TARGETS["take_timecode"] = _tc_clean_targets

_status_clean_targets = []
for _target in DEFAULT_TARZAN_SNAJPER_TARGETS.get("take_status", []):
    # status zostaje na t_status, ale bez dopinania t0/tc.
    if _target.scope == "take_main" and _target.target == "t0":
        continue
    _status_clean_targets.append(_target)
DEFAULT_TARZAN_SNAJPER_TARGETS["take_status"] = _status_clean_targets


# TARZAN_SNAJPER_NEXTION_XYZ_SPLIT_FIELDS_2026_05_18
# Aktualny take_main ma trzy osobne pola XYZ: tx, ty, tz.
# Tekst jest bez +/-; znak wartości pokazuje osobny kolor .pco każdego pola.
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "sensor_level_x": "level_x",
    "sensor_level_y": "level_y",
    "sensor_level_z": "level_z",
    "level_x": "level_x",
    "level_y": "level_y",
    "level_z": "level_z",
    "sensor_xyz": "sensor_xyz",
})

# Usuwamy fizyczny stary komponent t_xyz z celów, bo w HMI zastąpiły go tx/ty/tz.
for _logical in ("sensor_xyz", "level_x", "level_y", "level_z"):
    _old_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.get(_logical, [])
    DEFAULT_TARZAN_SNAJPER_TARGETS[_logical] = [
        _target for _target in _old_targets
        if not (
            _target.adapter == "physical_nextion"
            and _target.scope == "take_main"
            and _target.target == "t_xyz"
        )
    ]

# Wspólny sygnał sensor_xyz może przyjść jako dict/lista i aktualizuje wszystkie trzy pola.
_xyz_split_targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault("sensor_xyz", [])
for _target in (
    T("physical_nextion", "take_main", "tx", "txt"),
    T("physical_nextion", "take_main", "tx", "pco"),
    T("physical_nextion", "take_main", "ty", "txt"),
    T("physical_nextion", "take_main", "ty", "pco"),
    T("physical_nextion", "take_main", "tz", "txt"),
    T("physical_nextion", "take_main", "tz", "pco"),
):
    if _target not in _xyz_split_targets:
        _xyz_split_targets.append(_target)

# Osobne sygnały poziomicy też trafiają w swoje osobne pola.
for _logical, _component in (("level_x", "tx"), ("level_y", "ty"), ("level_z", "tz")):
    _targets = DEFAULT_TARZAN_SNAJPER_TARGETS.setdefault(_logical, [])
    for _target in (
        T("physical_nextion", "take_main", _component, "txt"),
        T("physical_nextion", "take_main", _component, "pco"),
    ):
        if _target not in _targets:
            _targets.append(_target)


# TARZAN_SNAJPER_TFD_META_TARGETS_2026_05_18
# TITLE/DIRECTOR są już celami Snajpera: take_main.t1/t2 oraz settings_main.t_title/t_director.
# Bridge ma tylko odpalić sygnał tfd_title/tfd_director; Snajper sam wybiera aktywny scope i flushuje.
DEFAULT_TARZAN_SNAJPER_TARGETS["tfd_title"] = [
    T("physical_nextion", "take_main", "t1", "txt"),
    T("physical_nextion", "settings_main", "t_title", "txt"),
    T("canvas_preview", "take_main", "t1", "txt"),
    T("canvas_preview", "settings_main", "t_title", "txt"),
]
DEFAULT_TARZAN_SNAJPER_TARGETS["tfd_director"] = [
    T("physical_nextion", "take_main", "t2", "txt"),
    T("physical_nextion", "settings_main", "t_director", "txt"),
    T("canvas_preview", "take_main", "t2", "txt"),
    T("canvas_preview", "settings_main", "t_director", "txt"),
]

# TARZAN_SNAJPER_TFD_SAVE_STATUS_TARGETS_2026_05_18
# Komunikat SAVE/SAVED na settings_main idzie przez Snajpera, nie przez ręczne queue.
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "tfd_save_status": "tfd_save_status",
    "tfd_save_status_visible": "tfd_save_status_visible",
    "tfd_save_sound": "tfd_save_sound",
})
DEFAULT_TARZAN_SNAJPER_TARGETS["tfd_save_status"] = [
    T("physical_nextion", "settings_main", "t_save_status", "txt"),
    T("canvas_preview", "settings_main", "t_save_status", "txt"),
]
DEFAULT_TARZAN_SNAJPER_TARGETS["tfd_save_status_visible"] = [
    T("physical_nextion", "settings_main", "t_save_status", "visible"),
    T("canvas_preview", "settings_main", "t_save_status", "visible"),
]

# TARZAN_SNAJPER_UNIFICATION_FIX_2026_05_18
# Poprawiamy mapowanie sygnałów RAW -> LOGICAL dla osi i RRP,
# aby kolory (.pco) i wartości (.txt) mogły być celowane niezależnie.
for i in range(6):
    DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
        f"par_axis_{i}_val": f"axis_{i}_value",
        f"axis_{i}_value": f"axis_{i}_value",
        f"par_axis_{i}_dir": f"axis_{i}_dir",
        f"axis_{i}_dir": f"axis_{i}_dir",
    })

DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP.update({
    "par_rrp_p1_val": "rrp_p1_value",
    "rrp_p1_value": "rrp_p1_value",
    "par_rrp_p1_dir": "rrp_p1_dir",
    "rrp_p1_dir": "rrp_p1_dir",
    "par_rrp_p2_val": "rrp_p2_value",
    "rrp_p2_value": "rrp_p2_value",
    "par_rrp_p2_dir": "rrp_p2_dir",
    "rrp_p2_dir": "rrp_p2_dir",
    "tfd_title_pco": "tfd_title_pco",
    "tfd_director_pco": "tfd_director_pco", "take_number": "take_number", "take_timecode": "take_timecode", "take_status": "take_status",
})

# =============================================================================
# TARZAN_SNAJPER_CONSOLIDATED_TARGET_MAP_2026_05_18
# Pełna implementacja celów we wszystkich warstwach (Nextion, Canvas, Tkinter).
# =============================================================================
_FINAL_MAP = {
    "tfd_title": [
        T("physical_nextion", "take_main", "t1", "txt"),
        T("physical_nextion", "settings_main", "t_title", "txt"),
        T("canvas_preview", "take_main", "t1", "txt"),
        T("canvas_preview", "settings_main", "t_title", "txt"),
        T("par_tkinter", "take_panel", "movie_title_label", "text"),
        T("ehr_tkinter", "ehr_main", "protocol_label", "text"),
    ],
    "tfd_title_pco": [
        T("physical_nextion", "take_main", "t1", "pco"),
        T("physical_nextion", "settings_main", "t_title", "pco"),
        T("canvas_preview", "take_main", "t1", "pco"),
        T("canvas_preview", "settings_main", "t_title", "pco"),
    ],
    "tfd_director": [
        T("physical_nextion", "take_main", "t2", "txt"),
        T("physical_nextion", "settings_main", "t_director", "txt"),
        T("canvas_preview", "take_main", "t2", "txt"),
        T("canvas_preview", "settings_main", "t_director", "txt"),
        T("par_tkinter", "take_panel", "director_label", "text"),
    ],
    "tfd_director_pco": [
        T("physical_nextion", "take_main", "t2", "pco"),
        T("physical_nextion", "settings_main", "t_director", "pco"),
        T("canvas_preview", "take_main", "t2", "pco"),
        T("canvas_preview", "settings_main", "t_director", "pco"),
    ],
    "take_number": [
        T("physical_nextion", "take_main", "t_take", "txt"),
        T("canvas_preview", "take_main", "t_take", "txt"),
        T("par_tkinter", "take_panel", "take_label", "text"),
    ],
    "take_timecode": [
        T("physical_nextion", "take_main", "t0", "txt"),
        T("canvas_preview", "take_main", "t0", "txt"),
        T("par_tkinter", "take_panel", "timecode_label", "text"),
    ],
    "take_status": [
        T("physical_nextion", "take_main", "t_status", "txt"),
        T("canvas_preview", "take_main", "t_status", "txt"),
        T("par_tkinter", "status_panel", "status_label", "text"),
    ],
    "rrp_p1_value": [
        T("physical_nextion", "rrp_main", "t_p1_val", "txt"),
        T("canvas_preview", "rrp_main", "t_p1_val", "txt"),
        T("par_tkinter", "rrp_panel", "p1_value_label", "text"),
    ],
    "rrp_p1_dir": [
        T("physical_nextion", "rrp_main", "b_p1_dir", "val"),
        T("physical_nextion", "rrp_main", "va_p1_dir", "val"),
        T("physical_nextion", "rrp_main", "t_p1_val", "pco"),
        T("canvas_preview", "rrp_main", "b_p1_dir", "val"),
        T("canvas_preview", "rrp_main", "t_p1_val", "pco"),
        T("par_tkinter", "par_rrp", "p1_dir_widget", "state"),
    ],
    "rrp_p2_value": [
        T("physical_nextion", "rrp_main", "t_p2_val", "txt"),
        T("canvas_preview", "rrp_main", "t_p2_val", "txt"),
        T("par_tkinter", "rrp_panel", "p2_value_label", "text"),
    ],
    "rrp_p2_dir": [
        T("physical_nextion", "rrp_main", "b_p2_dir", "val"),
        T("physical_nextion", "rrp_main", "va_p2_dir", "val"),
        T("physical_nextion", "rrp_main", "t_p2_val", "pco"),
        T("canvas_preview", "rrp_main", "b_p2_dir", "val"),
        T("canvas_preview", "rrp_main", "t_p2_val", "pco"),
        T("par_tkinter", "par_rrp", "p2_dir_widget", "state"),
    ],
    "sensor_xyz": [
        T("physical_nextion", "take_main", "tx", "txt"),
        T("physical_nextion", "take_main", "ty", "txt"),
        T("physical_nextion", "take_main", "tz", "txt"),
        T("physical_nextion", "take_main", "tx", "pco"),
        T("physical_nextion", "take_main", "ty", "pco"),
        T("physical_nextion", "take_main", "tz", "pco"),
        T("canvas_preview", "take_main", "tx", "txt"),
        T("canvas_preview", "take_main", "ty", "txt"),
        T("canvas_preview", "take_main", "tz", "txt"),
        T("canvas_preview", "take_main", "tx", "pco"),
        T("canvas_preview", "take_main", "ty", "pco"),
        T("canvas_preview", "take_main", "tz", "pco"),
        T("par_tkinter", "sensors_panel", "xyz_label", "text"),
    ],
    "level_x": [
        T("physical_nextion", "level_xyz", "va0", "val"),
        T("canvas_preview", "level_xyz", "va0", "val"),
        T("par_tkinter", "sensors_panel", "level_x_label", "text"),
    ],
    "level_y": [
        T("physical_nextion", "level_xyz", "va1", "val"),
        T("canvas_preview", "level_xyz", "va1", "val"),
        T("par_tkinter", "sensors_panel", "level_y_label", "text"),
    ],
    "sensor_shock": [
        T("physical_nextion", "take_main", "t_shock", "txt"),
        T("canvas_preview", "take_main", "t_shock", "txt"),
        T("par_tkinter", "sensors_panel", "shock_label", "text"),
    ],
    "sensor_laser": [
        T("physical_nextion", "take_main", "t_laser", "txt"),
        T("canvas_preview", "take_main", "t_laser", "txt"),
        T("par_tkinter", "sensors_panel", "laser_label", "text"),
    ],
    "sensor_limits": [
        T("physical_nextion", "take_main", "t_limits", "txt"),
        T("canvas_preview", "take_main", "t_limits", "txt"),
        T("par_tkinter", "sensors_panel", "limits_label", "text"),
    ],
    "sensor_light": [
        T("physical_nextion", "take_main", "t_light", "txt"),
        T("canvas_preview", "take_main", "t_light", "txt"),
        T("par_tkinter", "sensors_panel", "light_label", "text"),
    ],
    "sensor_temp": [
        T("physical_nextion", "take_main", "t_temp", "txt"),
        T("canvas_preview", "take_main", "t_temp", "txt"),
        T("par_tkinter", "sensors_panel", "temp_label", "text"),
    ],
    "take_clap": [
        T("physical_nextion", "take_main", "sound", "play"),
        T("physical_nextion", "take_main", "t_clap", "txt"),
        T("physical_nextion", "take_main", "p5", "pic"),
        T("canvas_preview", "take_main", "t_clap", "txt"),
        T("canvas_preview", "take_main", "p5", "pic"),
    ],
    "tfd_save_sound": [
        T("physical_nextion", "settings_main", "sound", "play"),
    ],
    "nextion_ui_cut": [
        T("physical_nextion", "settings_main", "b_ui_cut", "val"),
        T("par_tkinter", "nextion_panel", "ui_cut_status_label", "text"),
        T("par_tkinter", "nextion_panel", "ui_cut_button", "state"),
        T("canvas_preview", "nextion_7", "screen", "ui_cut"),
    ],
    "tfd_save_status": [
        T("physical_nextion", "settings_main", "t_save_status", "txt"),
        T("canvas_preview", "settings_main", "t_save_status", "txt"),
    ],
    "tfd_save_status_visible": [
        T("physical_nextion", "settings_main", "t_save_status", "visible"),
        T("canvas_preview", "settings_main", "t_save_status", "visible"),
    ],
    "tfd_axis_0_active": [T("tfd_adapter", "axis0", "active", "visible")],
    "tfd_axis_1_active": [T("tfd_adapter", "axis1", "active", "visible")],
    "tfd_axis_2_active": [T("tfd_adapter", "axis2", "active", "visible")],
    "tfd_axis_3_active": [T("tfd_adapter", "axis3", "active", "visible")],
    "tfd_axis_4_active": [T("tfd_adapter", "axis4", "active", "visible")],
    "tfd_axis_5_active": [T("tfd_adapter", "axis5", "active", "visible")],
    "tfd_laser_active": [T("tfd_adapter", "sensors", "laser", "visible")],
    "tfd_laser_error": [T("tfd_adapter", "sensors", "laser", "error")],
    "tfd_limits_active": [T("tfd_adapter", "sensors", "limits", "visible")],
    "tfd_shock_active": [T("tfd_adapter", "sensors", "shock", "visible")],
}

for i in range(6):
    _FINAL_MAP[f"axis_{i}_value"] = [
        T("physical_nextion", "take_main", f"t_axis{i}", "txt"),
        T("canvas_preview", "take_main", f"t_axis{i}", "txt"),
        T("par_tkinter", "axis_panel", f"axis_{i}_value_label", "text"),
    ]
    _FINAL_MAP[f"axis_{i}_dir"] = [
        T("physical_nextion", "take_main", f"t_axis{i}", "pco"),
        T("canvas_preview", "take_main", f"t_axis{i}", "pco"),
    ]

for _logical, _targets in _FINAL_MAP.items():
    DEFAULT_TARZAN_SNAJPER_TARGETS[_logical] = _targets
