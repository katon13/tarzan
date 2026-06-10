"""
Źródło sygnałów dla TSP.

Moduł generuje własne sygnały uruchomieniowe pod pełny protokół TSP.
Nie jest to osobna architektura — ta sama klasa zostanie później spięta z SignalBus.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Iterable, Optional

from .tarzanTspLog import setup_tsp_logger
from .tarzanTspProtocol import (
    LANE_FAST,
    LANE_HEALTH,
    LANE_NORMAL,
    LANE_SLOW,
    PRIORITY_HIGH,
    PRIORITY_INFO,
    PRIORITY_MARKER,
    PRIORITY_SAFETY,
    monotonic_ms,
    urgent_event,
)

LOGIKA_DOZWOLONY = "DOZWOLONY"
LOGIKA_TYLKO_ODCZYT = "TYLKO_ODCZYT"
LOGIKA_ZABRONIONY = "ZABRONIONY"


@dataclass(frozen=True)
class TarzanTspSignalDef:
    name: str
    lane: str
    value_type: str
    default: Any
    logika_trybow: str = LOGIKA_DOZWOLONY
    rola_logiki: str = "STATUS"
    opis: str = ""

    def as_catalog_item(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "lane": self.lane,
            "type": self.value_type,
            "default": self.default,
            "logika_trybow": self.logika_trybow,
            "rola_logiki": self.rola_logiki,
            "opis": self.opis,
        }


class TarzanTspSignalProvider:
    """
    Provider sygnałów TSP.

    Obecnie generuje pełny zestaw sygnałów uruchomieniowych:
    - FAST: pulsy osi, RRP, TC,
    - NORMAL: tryby, transport, Nextion,
    - SLOW: sensory,
    - HEALTH: stan node.

    Późniejsza integracja: metody get_signal/set_signal/catalog zostają,
    a wnętrze zostanie spięte z SignalBus.
    """

    def __init__(self, node_name: str = "tarzanMiniPC") -> None:
        self.node_name = node_name
        self.logger = setup_tsp_logger("TSP.PROVIDER")
        self._lock = Lock()
        self._start_ms = monotonic_ms()
        self._last_ms = self._start_ms
        self._urgent_queue: list[Dict[str, Any]] = []
        self.parcore: Any = None  # MAIN Runtime podpina wykonawczy PARcore.
        self._catalog: Dict[str, TarzanTspSignalDef] = {}
        self._build_catalog()


    # ------------------------------------------------------------------
    # delegacja CALL_ACTION z TSP do PARcore.
    # Provider zostaje katalogiem/protokolem TSP, a wykonanie PAR idzie do jednego rdzenia.
    # ------------------------------------------------------------------
    def bind_parcore(self, parcore: Any) -> None:
        self.parcore = parcore
        try:
            self.logger.info("PARcore delegate bound to TSP provider")
        except Exception:
            pass

    def set_parcore_delegate(self, parcore: Any) -> None:
        self.bind_parcore(parcore)

    def set_runtime_delegate(self, parcore: Any) -> None:
        self.bind_parcore(parcore)

    # ------------------------------------------------------------------
    # KATALOG
    # ------------------------------------------------------------------

    def _add(self, item: TarzanTspSignalDef) -> None:
        self._catalog[item.name] = item

    def _build_catalog(self) -> None:
        # Budujemy katalog wyłącznie na podstawie SignalBus / tarzanZmienneSygnalowe (MAIN/LIVE)
        try:
            from core.tarzanSignalBus import get_signal_bus
            from core.tarzanZmienneSygnalowe import WSZYSTKIE_SYGNALY
            
            # Budujemy katalog na podstawie WSZYSTKIE_SYGNALY
            for name, syg in WSZYSTKIE_SYGNALY.items():
                lane = LANE_NORMAL
                # Klasyfikacja na pasma
                if syg.typ == "CTR" or syg.grupa in ("COPY_CAMERA", "ENCODERY", "RRP"):
                    lane = LANE_FAST
                elif syg.rola_logiki == "SENSOR":
                    lane = LANE_SLOW
                elif syg.rola_logiki == "SYSTEM":
                    lane = LANE_HEALTH
                
                self._add(TarzanTspSignalDef(
                    name=name,
                    lane=lane,
                    value_type="int" if syg.typ == "LH" else "float" if syg.typ == "ANALOG" else "str",
                    default=syg.default,
                    logika_trybow=syg.logika_trybow,
                    rola_logiki=syg.rola_logiki,
                    opis=syg.opis
                ))
            
            # Dodatki specyficzne dla TSP

            # PAR -> miniPC: komendy wykonawcze panelu PAR.
            # To nie są lokalne inputy PAR; TSP przekazuje je do SignalBus/HardwareBridge.
            par_exec_signals = {
                "par_lcd_play_line1": "PAR LCD PLAY linia 1",
                "par_lcd_play_line2": "PAR LCD PLAY linia 2",
                "par_lcd_rec_line1": "PAR LCD REC linia 1",
                "par_lcd_rec_line2": "PAR LCD REC linia 2",
                "par_lcd_line1": "PAR LCD wspólna linia 1",
                "par_lcd_line2": "PAR LCD wspólna linia 2",
                "par_matrix_pattern": "PAR Matrix LED 8x8 pattern rows 01010101/...",
                "par_f_led_f1": "PAR test LED F1",
                "par_f_led_f2": "PAR test LED F2",
                "par_f_led_f3": "PAR test LED F3",
                "par_f_led_f4": "PAR test LED F4",
            }
            for sig_name, sig_desc in par_exec_signals.items():
                if sig_name not in self._catalog:
                    value_type = "str" if sig_name in {"par_matrix_pattern", "par_lcd_play_line1", "par_lcd_play_line2", "par_lcd_rec_line1", "par_lcd_rec_line2", "par_lcd_line1", "par_lcd_line2"} else "int"
                    default = "" if value_type == "str" else 0
                    self._add(TarzanTspSignalDef(sig_name, LANE_NORMAL, value_type, default, "DOZWOLONY", "SYSTEM", sig_desc))

            if 'par_mode' not in self._catalog:
                self._add(TarzanTspSignalDef('par_mode', LANE_HEALTH, 'int', 1, 'DOZWOLONY', 'SYSTEM', 'Tryb pracy PAR (0=TEST, 1=LIVE, 2=MIX).'))
            if 'node_name' not in self._catalog:
                self._add(TarzanTspSignalDef("node_name", LANE_HEALTH, "str", self.node_name, "TYLKO_ODCZYT", "STATUS", "Nazwa node."))
            if "tsp_clients" not in self._catalog:
                self._add(TarzanTspSignalDef("tsp_clients", LANE_HEALTH, "int", 0, "TYLKO_ODCZYT", "STATUS", "Liczba klientów TSP."))

            self.logger.info("Catalog built from SignalBus: %d signals", len(self._catalog))
        except Exception as exc:
            self.logger.error("FATAL: Could not build catalog from SignalBus: %s", exc)

    def _reset_values(self) -> None:
        for name, item in self._catalog.items():
            self._signals[name] = item.default

    def catalog(self) -> list[Dict[str, Any]]:
        with self._lock:
            return [item.as_catalog_item() for item in self._catalog.values()]

    def signal_count(self) -> int:
        with self._lock:
            return len(self._catalog)

    # ------------------------------------------------------------------
    # ODCZYT / ZAPIS
    # ------------------------------------------------------------------

    def get_signal(self, name: str) -> Any:
        # Provider polega wyłącznie na SignalBus (MAIN/LIVE)
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        if bus.exists(name):
            return bus.read(name)
        
        # Jeśli sygnał nie istnieje w busie, a jest w katalogu, zwracamy default
        with self._lock:
            item = self._catalog.get(name)
            if item: return item.default
            raise KeyError(name)

    def get_all(self) -> Dict[str, Any]:
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        res = bus.values_snapshot()
        
        # Uzupełniamy o brakujące w busie sygnały z katalogu
        with self._lock:
            for name, item in self._catalog.items():
                if name not in res:
                    res[name] = item.default
        return res

    def get_lane_values(self, lane: str, names: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        
        with self._lock:
            if names is None or "*" in set(names):
                wanted = [name for name, item in self._catalog.items() if item.lane == lane]
            else:
                wanted = [name for name in names if name in self._catalog and self._catalog[name].lane == lane]
            
        res = {}
        for name in wanted:
            if bus.exists(name):
                res[name] = bus.read(name)
            else:
                with self._lock:
                    res[name] = self._catalog[name].default
        return res

    def set_signal(self, name: str, value: Any, source: str = "tsp") -> Dict[str, Any]:
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        
        # ZASADA SNAJPERA: wybudzanie hardware jest teraz zarządzane przez PARcore
        # lub bezpośrednio w HardwareBridge na podstawie typu sygnału.
        # Nie używamy już ogólnego, ślepego cmd_hardware_awake=1 w tym miejscu.
        
        if not bus.exists(name):
            with self._lock:
                if name not in self._catalog:
                    return {"ok": False, "error": "unknown_signal", "name": name}
        
        # Sprawdzanie control_owner (Bezpieczeństwo)
        owner = bus.read("control_owner", "TSP_BOOT")
        
        # Jeśli właścicielem jest EHR, odrzucamy ręczne sterowanie osiami z TSP/PAR
        is_axis = any(sub in name for sub in ["axis_", "rrp_", "sok_"])
        if owner == "EHR_PLAYBACK" and is_axis and "tarzanEHR" not in source:
            return {
                "ok": False, 
                "error": "write_denied", 
                "name": name, 
                "reason": "control_owner_conflict",
                "owner": owner
            }

        old = bus.read(name)
        
        meta = bus.get_meta(name)

        # centralny rejestr komend PAR wykonywanych fizycznie na miniPC.
        # Nie opieramy się już na samym kierunku z katalogu, bo część starych
        # sygnałów testowych PAR ma historycznie opis IN, mimo że w trybie TEST
        # ma wykonać zapis na sprzęcie przez HardwareBridge.
        par_exec_prefixes = ("par_lcd_", "par_matrix_", "par_f_led_")
        par_exec_names = {
            "rec_p46_led_f1", "rec_p48_led_f2", "rec_p50_led_f3", "rec_p52_led_f4",
            # AUTOMATYKA / mechanika ramienia: PLAY P37 musi wykonać fizyczne
            # odłączenie STEP w trybie nagrywania ręcznego, mimo historycznego IN.
            "play_p37_step_disconnect_manual",
        }
        is_par_exec = name.startswith(par_exec_prefixes) or name in par_exec_names

        if (meta and meta.kierunek == "OUT") or is_par_exec:
            bus.write_output(name, value, source=source)
        else:
            bus.set_input(name, value, source=source)
        
        new = bus.read(name)
        urgent = self._urgent_for_change(name, old, new, source)
        if urgent:
            with self._lock:
                self._urgent_queue.append(urgent)
                
        return {"ok": True, "name": name, "value": new}

    def _coerce_value(self, value: Any, value_type: str) -> Any:
        if value_type == "int":
            return int(value)
        if value_type == "float":
            return float(value)
        if value_type == "bool":
            return bool(value)
        if value_type == "str":
            return str(value)
        return value

    def _urgent_for_change(self, name: str, old: Any, new: Any, source: str) -> Optional[Dict[str, Any]]:
        if old == new:
            return None
        if name == "transport_state" and str(new).upper() in {"STOP", "PLAY", "REC", "PAUSE"}:
            priority = PRIORITY_SAFETY if str(new).upper() == "STOP" else PRIORITY_HIGH
            return urgent_event(name, new, f"transport_changed_by_{source}", priority)
        if name == "active_mode":
            return urgent_event(name, new, f"mode_changed_by_{source}", PRIORITY_HIGH)
        if name == "nextion_page":
            return urgent_event(name, new, "page_changed", PRIORITY_HIGH)
        if name in {"rrp_p1_axis_index", "rrp_p2_axis_index"}:
            return urgent_event(name, new, "rrp_axis_changed", PRIORITY_HIGH)
        if name in {"clap_event", "take_marker"}:
            return urgent_event(name, new, "take_marker", PRIORITY_MARKER)
        return None

    # ------------------------------------------------------------------
    # TICK
    # ------------------------------------------------------------------

    def tick(self, client_count: int = 0) -> None:
        """
        Aktualizuje stan providera.
        W trybie produkcyjnym wszystkie dane pochodzą z SignalBus.
        """
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            
            # Aktualizujemy statystyki węzła bezpośrednio w SignalBus
            uptime = monotonic_ms() - self._start_ms
            bus.force_signal("node_uptime_ms", uptime, source="TSP_STATS")
            bus.force_signal("tsp_clients", client_count, source="TSP_STATS")
            
        except Exception as exc:
            self.logger.debug("Tick: SignalBus not available: %s", exc)

    def pop_urgent_events(self) -> list[Dict[str, Any]]:
        with self._lock:
            items = list(self._urgent_queue)
            self._urgent_queue.clear()
            return items

    def has_urgent_events(self) -> bool:
        with self._lock:
            return len(self._urgent_queue) > 0

    def call_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        
        # ZASADA SNAJPERA: wybudzanie hardware dla akcji jest zarządzane w PARcore.call_action.
        # Nie używamy już ogólnego cmd_hardware_awake=1 tutaj.
        
        payload = payload or {}
        parcore = getattr(self, "parcore", None)
        if parcore is not None:
            try:
                result = parcore.route_client_command("PAR-GUI", name, payload)
                if isinstance(result, dict) and "ok" in result:
                    return result
                return {"ok": True, "action": name, "result": result}
            except ValueError:
                # Stare akcje TSP, których PARcore jeszcze nie zna, przechodzą niżej
                # przez dotychczasowy provider. Nie tworzymy drugiego modelu PAR.
                pass
            except Exception as exc:
                return {"ok": False, "action": name, "error": str(exc), "source": "PARcore"}

        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        
        with self._lock:
            if name == "force_signal":
                sig_name = payload.get("name")
                sig_value = payload.get("value")
                sig_source = payload.get("source", "TSP_FORCE")
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal(sig_name, sig_value, source=sig_source)
                    return {"ok": True, "action": name, "name": sig_name, "value": sig_value}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "clap":
                count = int(bus.read("clap_event", 0)) + 1
                bus.force_signal("clap_event", count, source="TSP_ACTION")
                bus.force_signal("take_marker", f"CLAP_{count:03d}", source="TSP_ACTION")
                self._urgent_queue.append(
                    urgent_event("clap_event", count, "operator_clap", PRIORITY_MARKER, marker=f"CLAP_{count:03d}")
                )
                return {"ok": True, "action": name, "clap_event": count, "take_marker": f"CLAP_{count:03d}"}
            
            if name == "stop":
                bus.force_signal("transport_state", "STOP", source="TSP_ACTION")
                self._urgent_queue.append(urgent_event("transport_state", "STOP", "operator_stop", PRIORITY_SAFETY))
                return {"ok": True, "action": name, "transport_state": "STOP"}
            
            # Akcje administracyjne PAR
            if name == "play_take":
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("transport_state", "PLAY", source="TSP_ACTION")
                    bus.log("TSP", "Action: PLAY TAKE requested.")
                    return {"ok": True, "action": name, "status": "playing"}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "pause_take":
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("transport_state", "PAUSE", source="TSP_ACTION")
                    bus.log("TSP", "Action: PAUSE TAKE requested.")
                    return {"ok": True, "action": name, "status": "paused"}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "stop_take":
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("transport_state", "STOP", source="TSP_ACTION")
                    bus.log("TSP", "Action: STOP TAKE requested.")
                    return {"ok": True, "action": name, "status": "stopped"}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "run_diagnostics":
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("cmd_run_diagnostics", 1, source="TSP_ACTION")
                    bus.log("TSP", "Action: Manual Diagnostics requested by PAR.")
                    return {"ok": True, "action": name, "status": "requested"}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "set_owner":
                owner = payload.get("owner", "PAR_LIVE")
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("control_owner", owner, source="TSP_ACTION")
                    bus.log("TSP", f"Action: Control owner changed to {owner} by PAR.")
                    return {"ok": True, "action": name, "owner": owner}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "reboot":
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("cmd_system_reboot", 1, source="TSP_ACTION")
                    bus.log("TSP", "Action: System REBOOT requested by PAR.")
                    return {"ok": True, "action": name, "status": "requested"}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "set_mode":
                mode = payload.get("mode", "TEST")
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.set_mode(mode)
                    return {"ok": True, "action": name, "mode": mode}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "set_transport":
                state = str(payload.get("state", "STOP")).upper()
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("transport_state", state, source="TSP_ACTION")
                    return {"ok": True, "action": name, "state": state}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "rrp_set":
                player = payload.get("player", "p1")
                axis_idx = payload.get("axis_index", 0)
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    signal_name = f"rrp_{player}_axis_index"
                    if bus.exists(signal_name):
                        bus.force_signal(signal_name, axis_idx, source="TSP_ACTION")
                        return {"ok": True, "action": name, "player": player, "axis_index": axis_idx}
                    return {"ok": False, "error": "unknown_player", "player": player}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "sok_set":
                axis = payload.get("axis")
                state = payload.get("state", 0)
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    # SOK to zazwyczaj włącznik/blokada dla osi
                    signal_name = f"sok_{axis}_active"
                    if bus.exists(signal_name):
                        bus.force_signal(signal_name, state, source="TSP_ACTION")
                        return {"ok": True, "action": name, "axis": axis, "state": state}
                    return {"ok": False, "error": "unknown_axis", "axis": axis}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "module_status":
                module = payload.get("module")
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    if not module:
                        # Zwróć wszystkie statusy modułów
                        modules = ["ehr", "khr", "lks", "par", "nextion5", "nextion7"]
                        data = {m: bus.read(f"{m}_state", "UNKNOWN") for m in modules}
                        return {"ok": True, "action": name, "modules": data}
                    
                    val = bus.read(f"{module}_state", "UNKNOWN")
                    return {"ok": True, "action": name, "module": module, "state": val}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "axis_inventory":
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    bus.force_signal("cmd_run_diagnostics", 1, source="TSP_ACTION")
                    # Zwracamy listę osi z SignalBus (klasyfikacja)
                    axes = [n for n in bus.names() if n.startswith("axis_") and n.endswith("_step")]
                    return {"ok": True, "action": name, "status": "requested", "axes": axes}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            if name == "axis_status":
                axis = payload.get("axis")
                cmd_param = payload.get("cmd")
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    
                    if cmd_param == "clear_alarms":
                        bus.force_signal("cmd_clear_alarms", 1, source="TSP_ACTION")
                        return {"ok": True, "action": name, "status": "clear_requested"}

                    if not axis:
                        # Zwróć wszystkie osie
                        axis_data = {n: bus.read(n) for n in bus.names() if n.startswith("axis_")}
                        return {"ok": True, "action": name, "axes": axis_data}
                    
                    # Konkretna oś
                    data = {
                        "ready": bus.read(f"axis_{axis}_ready", 0),
                        "alarm": bus.read(f"axis_{axis}_alarm", 0),
                        "pos": bus.read(f"axis_{axis}_pos", 0),
                        "pulses": bus.read(f"axis_{axis}_pulses", 0)
                    }
                    return {"ok": True, "action": name, "axis": axis, "status": data}
                except Exception as e:
                    return {"ok": False, "error": str(e), "action": name}

            return {"ok": False, "error": "unknown_action", "action": name}

    def state_summary(self) -> Dict[str, Any]:
        # W trybie MAIN/LIVE pobieramy pełny stan z SignalBus dla synchronizacji HMI
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            
            # Pobieramy snapshot wszystkich wartości
            all_values = bus.values_snapshot()
            
            # Podstawowe metadane sesji
            summary = {
                "node": self.node_name,
                "signal_count": bus.names_count() if hasattr(bus, "names_count") else len(bus.names()),
                "uptime_ms": bus.read("node_uptime_ms", 0),
            }
            
            # Łączymy w jedną płaską strukturę (zgodnie z Mapą: miniPC to prawda stanu)
            summary.update(all_values)
            return summary
            
        except Exception as exc:
            self.logger.error("state_summary error: %s", exc)
            with self._lock:
                return {
                    "node": self.node_name,
                    "signal_count": len(self._catalog),
                    "active_mode": self._signals.get("active_mode"),
                    "transport_state": self._signals.get("transport_state"),
                    "nextion_page": self._signals.get("nextion_page"),
                    "uptime_ms": self._signals.get("node_uptime_ms", 0),
                }

    @staticmethod
    def _format_timecode(ms: int, fps: int = 25) -> str:
        total_seconds = ms // 1000
        frame = int((ms % 1000) / (1000 / fps))
        seconds = total_seconds % 60
        minutes = (total_seconds // 60) % 60
        hours = total_seconds // 3600
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"
