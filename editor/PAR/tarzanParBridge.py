"""Most PAR ↔ SignalBus ↔ TAKE."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from core.tarzanSignalBus import TarzanSignalBus, get_signal_bus
from core.TSP.tarzanTspClient import TarzanTspClient
from core.TSP.tarzanTspConfig import TSP_MINI_PC_HOST
try:
    from editor.PAR.tarzanParProtocolMapper import TarzanParProtocolMapper
except ModuleNotFoundError:
    from tarzanParProtocolMapper import TarzanParProtocolMapper
try:
    from editor.PAR.tarzanParTakePlayer import TarzanParTakePlayer, TarzanTakeData
except ModuleNotFoundError:
    from tarzanParTakePlayer import TarzanParTakePlayer, TarzanTakeData


class TarzanParBridge:
    def __init__(
        self,
        bus: Optional[TarzanSignalBus] = None,
        after: Optional[Callable[..., Any]] = None,
        after_cancel: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.tsp_host = TSP_MINI_PC_HOST
        self.bus = bus or get_signal_bus("TEST")
        self.mapper = TarzanParProtocolMapper(self.bus.names())
        self.take_player = TarzanParTakePlayer(self.bus, self.mapper)
        self._after = after
        self._after_cancel = after_cancel
        if after is not None and after_cancel is not None:
            self.take_player.set_scheduler(after, after_cancel)
        
        # NEXTION SNAJPER: fizyczny most Nextiona jako pod-komponent
        from hardware.tarzanNextion.bridge import TarzanNextionBridge
        self.nextion = TarzanNextionBridge(self.bus)

        # TSP CLIENT: dla trybu LIVE
        self.tsp_client: Optional[TarzanTspClient] = None
        self._tsp_thread: Optional[threading.Thread] = None
        self._tsp_subscribed: bool = False
        self._tsp_last_state_sync_ts: float = 0.0
        # tryb LIVE utrzymujemy własną flagą, nie samym bus.mode.
        # Snapshot z miniPC albo lokalna zmiana stanu nie może zabić wątku TSP.
        self._tsp_active: bool = False
        # na starcie LIVE nie bierzemy FAST/*, bo PAR może zostać zalany
        # paczkami i TSP rozłącza klienta przez send_failed timed out.
        self._tsp_boot_signals = [
            "system_state",
            "runtime_state",
            "tsp_state",
            "lks_state",
            "par_state",
            "ehr_state",
            "hardware_state",
            "control_owner",
            "tarzan_ready",
            "safety_axis_unlock",
        ]
        self._remote_nextion_monitor: Dict[str, Any] = {}
        self._remote_nextion_log: list[str] = []
        self._last_remote_poll_ts: float = 0.0
        self._remote_poll_interval_s: float = 0.25

    def _ui_call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Wykonuje zmianę UI/SignalBus bezpiecznie w wątku Tkintera, gdy mamy scheduler."""
        if self._after is None:
            try:
                fn(*args, **kwargs)
            except Exception:
                pass
            return
        try:
            self._after(0, lambda: fn(*args, **kwargs))
        except Exception:
            try:
                fn(*args, **kwargs)
            except Exception:
                pass

    def _bus_log(self, source: str, message: str) -> None:
        self._ui_call(self.bus.log, source, message)

    def _bus_set_input(self, name: str, value: Any, source: str = "TSP_LIVE") -> None:
        self._ui_call(self.bus.set_input, name, value, source=source)

    def _queue_tsp_message(self, message: Dict[str, Any]) -> None:
        """RX klienta TSP działa w tle; obsługę wpisów do busa robimy przez Tk after()."""
        self._ui_call(self._handle_tsp_message, message)

    def set_mode(self, mode: str) -> None:
        self.bus.set_mode(mode)
        # PAR ma tylko dwa robocze tryby TEST/LIVE, ale oba pracują przez miniPC/TSP,
        # jeżeli połączenie jest dostępne. Różni się rola pracy, nie tor komunikacji.
        if mode in {"TEST", "LIVE", "MIX"}:
            self._tsp_active = True
            self._start_tsp()
        else:
            self._stop_tsp()

    def _start_tsp(self) -> None:
        if self._tsp_thread and self._tsp_thread.is_alive():
            return
        self._bus_log("TSP", "Starting TSP connector thread (LIVE)...")
        self._tsp_thread = threading.Thread(target=self._tsp_connector_loop, name="TSP-CONNECTOR", daemon=True)
        self._tsp_thread.start()

    def _client_is_connected(self) -> bool:
        """Zwraca prawdziwy stan połączenia TSP bez założenia, czy is_connected jest property czy metodą."""
        client = self.tsp_client
        if client is None:
            return False
        state = getattr(client, "is_connected", False)
        try:
            return bool(state() if callable(state) else state)
        except Exception:
            return False

    def _drop_tsp_client(self, reason: str = "connection_lost") -> None:
        """Zamyka martwego klienta i pozwala pętli LIVE połączyć się ponownie."""
        client = self.tsp_client
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        self.tsp_client = None
        self._tsp_subscribed = False
        self._bus_log("TSP", f"Client dropped: {reason}. Reconnect pending...")

    def _par_runtime_state(self) -> str:
        mode = str(getattr(self.bus, "mode", "TEST") or "TEST").upper()
        if mode == "LIVE":
            return "PAR_LIVE"
        return "PAR_TEST"

    def _announce_par_live_to_tsp(self) -> None:
        """KROK ZERO: jawne potwierdzenie stanu PAR -> TSP bez obejść lokalnych."""
        client = self.tsp_client
        if client is None or not self._client_is_connected():
            return
        try:
            client.set_signal("par_state", self._par_runtime_state())
            self._tsp_last_state_sync_ts = time.monotonic()
        except Exception as exc:
            self._bus_log("TSP_ERROR", f"PAR state announce failed: {exc}")
            self._drop_tsp_client(reason="par_state_announce_failed")

    def _sync_zero_state_with_tsp(self) -> None:
        """KROK ZERO: lekki odczyt stanu miniPC + potwierdzenie PAR_LIVE co kilka sekund."""
        client = self.tsp_client
        if client is None or not self._client_is_connected():
            return
        now = time.monotonic()
        if now - self._tsp_last_state_sync_ts < 5.0:
            return
        try:
            client.get_state()
            client.set_signal("par_state", self._par_runtime_state())
            self._tsp_last_state_sync_ts = now
        except Exception as exc:
            self._bus_log("TSP_ERROR", f"KROK ZERO state sync failed: {exc}")
            self._drop_tsp_client(reason="krok_zero_state_sync_failed")

    def _send_to_tsp_if_ready(self, send_fn: Callable[[TarzanTspClient], Any], action_name: str) -> bool:
        """Wysyła do TSP po połączeniu z miniPC. TEST i LIVE używają tego samego toru."""
        if not self._tsp_active or not self._client_is_connected():
            return False
        try:
            assert self.tsp_client is not None
            send_fn(self.tsp_client)
            return True
        except Exception as exc:
            self._bus_log("TSP_ERROR", f"{action_name} failed: {exc}")
            self._drop_tsp_client(reason=f"send_failed:{action_name}")
            return False

    def _tsp_connector_loop(self) -> None:
        """Pętla dbająca o połączenie i podtrzymanie sesji TSP.

        jeżeli połączenie spadnie po kliknięciu LIVE, PAR nie może
        wyjść z LIVE ani zostawić klienta martwego. Wątek ma spróbować
        ponownie połączyć się z miniPC.
        """
        while self._tsp_active:
            try:
                if self.tsp_client is None or not self._client_is_connected():
                    if self.tsp_client is not None:
                        self._bus_log("TSP_ERROR", "CONNECTION LOST: MiniPC offline or client closed. Reconnecting...")
                        try:
                            self.tsp_client.close()
                        except Exception:
                            pass
                        self.tsp_client = None
                        self._tsp_subscribed = False

                    self._bus_set_input("par_state", "CONNECTING", source="TSP_LIVE")
                    client = TarzanTspClient(host=self.tsp_host, name="tarzanPAR")
                    client.on_message = self._queue_tsp_message
                    client.connect()
                    self.tsp_client = client
                    self._tsp_subscribed = False
                    self._tsp_last_state_sync_ts = 0.0

                    self._bus_log("TSP", f"Connected to {self.tsp_host}. Sending HELLO...")
                    self._bus_set_input("par_state", "CONNECTED", source="TSP_LIVE")
                    client.hello()
                else:
                    # LIVE ma się trzymać. Wysyłamy lekki heartbeat,
                    # żeby martwy socket został wykryty i pętla mogła zrobić reconnect.
                    try:
                        assert self.tsp_client is not None
                        self.tsp_client.ping()
                        self._sync_zero_state_with_tsp()
                    except Exception as exc:
                        self._bus_log("TSP_ERROR", f"Heartbeat failed: {exc}")
                        self._drop_tsp_client(reason="heartbeat_failed")

            except Exception as exc:
                self._bus_log("TSP_ERROR", f"Connector loop error: {exc}")
                self._bus_set_input("par_state", "OFFLINE", source="TSP_LIVE")
                self._drop_tsp_client(reason="connector_exception")

            time.sleep(1.0)

        self._bus_log("TSP", "TSP connector thread stopped.")

    def _stop_tsp(self) -> None:
        self._tsp_active = False
        if self.tsp_client:
            self._bus_log("TSP", "Disconnecting from MiniPC...")
            try:
                if self._client_is_connected():
                    self.tsp_client.set_signal("par_state", "DISCONNECTED")
            except Exception:
                pass
            self.tsp_client.close()
            self.tsp_client = None
        self._tsp_subscribed = False
        self._tsp_thread = None

    def _handle_tsp_message(self, message: Dict[str, Any]) -> None:
        event = message.get("event")
        cmd = message.get("cmd")
        ok = message.get("ok", True)
        self._remember_parcore_response(message)

        if event == "snajper_packet":
            values = message.get("values", {})
            # Apply snapshot do lokalnego SignalBus PAR
            # Unikamy pętli zwrotnej przez apply_snapshot (filtrowanie w Bus)
            self.bus.apply_snapshot(values, source="TSP_LIVE")
        
        elif cmd == "get_state" and ok:
            # Synchronizacja stanu początkowego
            state = message.get("state", {})
            if state:
                self.bus.log("TSP", f"GET_STATE OK: signals={len(state.get('signals', state))}")
                self.bus.apply_snapshot(state, source="TSP_INITIAL")

        elif (event == "hello") or (cmd == "hello" and ok):
            node = message.get("node") or message.get("node_name") or message.get("node_id", "unknown")
            self.bus.log("TSP", f"Handshake OK: {node}")
            # pierwszy LIVE ma być lekki. Nie subskrybujemy FAST ani "*".
            # Najpierw potwierdzamy stabilny most PAR <-> TSP na sygnałach systemowych.
            if self.tsp_client and not self._tsp_subscribed:
                self._tsp_subscribed = True
                self.tsp_client.ping()
                self.tsp_client.get_state()
                self.tsp_client.subscribe(
                    lanes=["normal", "slow", "health", "urgent"],
                    signals=self._tsp_boot_signals,
                )
        
        elif cmd == "subscribe" and ok:
            self.bus.log("TSP", "SUBSCRIBE OK: receiving live updates.")
            self._announce_par_live_to_tsp()
            try:
                if self.tsp_client and self._client_is_connected():
                    self.tsp_client.get_state()
            except Exception as exc:
                self.bus.log("TSP_ERROR", f"GET_STATE after subscribe failed: {exc}")

        elif event == "error" or (not ok and (message.get("error") or message.get("message"))):
            err_code = message.get("error", "unknown_error")
            err_msg = message.get("message") or message.get("reason") or err_code
            self.bus.log("TSP_ERROR", f"TSP Error ({err_code}): {err_msg}")
            
            # Powiadamianie UI o błędzie
            self.bus.set_input("par_last_error", f"{err_code}: {err_msg}", source="TSP_LIVE")
            
            # Specjalna obsługa odmowy zapisu dla UI (8)
            if err_code == "write_denied":
                self.bus.log("TSP_ERROR", f"Access Denied: {message.get('reason', 'control_owner_conflict')}")
                self.bus.set_input("par_write_denied_event", 1, source="TSP_LIVE")
                # Resetujemy flagę zdarzenia po chwili, żeby mogła "mignąć" w UI
                threading.Timer(1.0, lambda: self.bus.set_input("par_write_denied_event", 0, source="TSP_LIVE")).start()

        elif event == "disconnect":
            self.bus.log("TSP", "Server disconnected.")
            self._drop_tsp_client(reason="server_disconnect_event")

        elif event == "log_event":
            # Odbieranie logów z MiniPC
            src = message.get("source", "REMOTE")
            msg = message.get("message", "")
            # Wpisujemy do lokalnego busa, co automatycznie odświeży panel logów PAR
            self.bus.log(f"MINI:{src}", msg)

        elif event == "trace":
            # Odbieranie danych trace w czasie rzeczywistym
            name = message.get("signal", "unknown")
            val = message.get("value", 0)
            self.bus.force_signal(f"trace_{name}", val, source="TSP_TRACE")


    def _remember_parcore_response(self, message: Dict[str, Any]) -> None:
        if message.get("cmd") != "call_action" or not message.get("ok", True):
            return
        action = str(message.get("action") or message.get("name") or "").strip()
        result = message.get("result")
        if action == "get_nextion_monitor_state" and isinstance(result, dict):
            self._remote_nextion_monitor = dict(result)
        elif action in {"build_nextion7_log_preview", "get_nextion7_log"}:
            if isinstance(result, str):
                self._remote_nextion_log = [line for line in result.splitlines() if line.strip()]
            elif isinstance(result, (list, tuple)):
                self._remote_nextion_log = [str(line) for line in result]

    def _is_minipc_screen(self, screen_key: str = "nextion_7") -> bool:
        key = str(screen_key or "").lower()
        return key in {"nextion_7", "nextion7", "n7", "nextion_5", "nextion5", "n5"}

    def _block_minipc_owned(self, what: str) -> bool:
        self.bus.log("MINIPC", f"{what} blocked: miniPC/PARcore not connected")
        self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED: {what}", source="PAR_BRIDGE")
        return False

    def connect_screen(self, screen_key: str = "nextion_7") -> bool:
        if self._is_minipc_screen(screen_key):
            if self.parcore_action("connect_screen", {"screen_key": screen_key}):
                return True
            return self._block_minipc_owned(f"{screen_key}.connect_screen")
        if hasattr(self.nextion, "connect_screen"):
            return bool(self.nextion.connect_screen(screen_key))
        return bool(self.nextion_connect())

    def disconnect_screen(self, screen_key: str = "nextion_7") -> bool:
        if self._is_minipc_screen(screen_key):
            if self.parcore_action("disconnect_screen", {"screen_key": screen_key}):
                return True
            return self._block_minipc_owned(f"{screen_key}.disconnect_screen")
        if hasattr(self.nextion, "disconnect_screen"):
            self.nextion.disconnect_screen(screen_key)
            return True
        return False

    def sync(self, force: bool = False, screen_key: str = "nextion_7") -> Any:
        # Globalna zasada: fizyczny Nextion należy do miniPC/PARcore.
        if self._is_minipc_screen(screen_key):
            if self.parcore_action("sync", {"force": bool(force), "screen_key": screen_key}):
                return True
            return self._block_minipc_owned(f"{screen_key}.sync")
        return False

    def get_nextion_monitor_state(self, screen_key: str = "nextion_7") -> Dict[str, Any]:
        if self._is_minipc_screen(screen_key):
            self.parcore_action("get_nextion_monitor_state", {"screen_key": screen_key})
            if self._remote_nextion_monitor:
                return dict(self._remote_nextion_monitor)
            return {"screen_key": screen_key, "connected": False, "port": "miniPC", "baudrate": 115200, "last_error": "remote status pending", "page": "", "ui_cut": 0, "pending": 0}
        if hasattr(self.nextion, "get_nextion_monitor_state"):
            return dict(self.nextion.get_nextion_monitor_state(screen_key))
        return {}

    def get_recent_transport_log(self, screen_key: str = "nextion_7", limit: int = 120) -> list[str]:
        if self._is_minipc_screen(screen_key):
            self.parcore_action("build_nextion7_log_preview", {"limit": int(limit), "screen_key": screen_key})
            return list(self._remote_nextion_log)[-int(limit):]
        if hasattr(self.nextion, "get_recent_transport_log"):
            return list(self.nextion.get_recent_transport_log(screen_key, limit=limit))
        return []

    def clear_transport_log(self, screen_key: str | None = None) -> None:
        self._remote_nextion_log.clear()
        target = screen_key or "nextion_7"
        if self._is_minipc_screen(target):
            self.parcore_action("clear_transport_log", {"screen_key": target})
            return
        if hasattr(self.nextion, "clear_transport_log"):
            try:
                self.nextion.clear_transport_log(screen_key)
            except TypeError:
                self.nextion.clear_transport_log()

    def nextion_connect(self):
        if self.parcore_action("connect_enabled", {"screen_key": "nextion_7"}):
            return True
        return self._block_minipc_owned("nextion_7.connect_enabled")

    def nextion_sync(self, force: bool = False):
        return self.sync(force=force)

    def poll(self):
        # PAR-GUI jest klonem/REMOTE. Nie wolno spamować call_action co tick
        # podglądu; miniPC/PARcore ma własną pętlę RX Nextion 7. Tu tylko
        # okresowy lekki poll na żądanie podglądu.
        now = time.monotonic()
        if (now - self._last_remote_poll_ts) < self._remote_poll_interval_s:
            return True
        self._last_remote_poll_ts = now
        if self.parcore_action("nextion_poll", {"screen_key": "nextion_7"}):
            return True
        return False

    def flush_snajper_commands(self):
        if self.parcore_action("flush_snajper_commands", {"screen_key": "nextion_7"}):
            return True
        return False

    def queue_snajper_command(self, scope: str, component: str, prop: str, value):
        return self.parcore_action("queue_snajper_command", {
            "screen_key": "nextion_7",
            "scope": scope,
            "component": component,
            "prop": prop,
            "value": value,
        })


    # ------------------------------------------------------------------
    # PAR-GUI jako HMI: każde wykonanie idzie przez TSP → PARcore.
    # ------------------------------------------------------------------
    def parcore_available(self) -> bool:
        return bool(self._tsp_active and self._client_is_connected())

    def _parcore_call(self, action: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        payload = dict(payload or {})
        if not self.parcore_available():
            return False
        return self._send_to_tsp_if_ready(
            lambda c: c.call_action(action, payload),
            f"parcore_action {action}",
        )

    def parcore_action(self, action: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Jawne wejście dla PAR-GUI: TSP → PARcore.call_action(...)."""
        return self._parcore_call(action, payload)

    def parcore_set_signal(self, name: str, value: Any, source: str = "PAR_GUI") -> bool:
        return self._parcore_call("set_signal", {"name": name, "value": value, "source": source})

    def parcore_force_signal(self, name: str, value: Any, source: str = "PAR_GUI_FORCE") -> bool:
        return self._parcore_call("force_signal", {"name": name, "value": value, "source": source})

    def read_input(self, name: str, default: Any = 0) -> Any:
        return self.bus.read_input(name, default)

    def set_input(self, name: str, value: Any, source: str = "PAR") -> bool:
        # PAR-GUI nie wykonuje prawdy lokalnie; wysyła komendę do PARcore.
        if self.parcore_set_signal(name, value, source=source):
            return True
        if self._requires_minipc_connection(name):
            self.bus.log("MINIPC", f"{name} blocked: miniPC/PARcore not connected")
            self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED: {name}", source="PAR_BRIDGE")
            return False
        return self.bus.set_input(name, value, source=source)

    def write_output(self, name: str, value: Any, source: str = "PAR") -> bool:
        # wyjścia fizyczne zawsze przez PARcore, gdy TSP jest dostępny.
        if self.parcore_set_signal(name, value, source=source):
            return True
        if self._requires_minipc_connection(name):
            self.bus.log("MINIPC", f"{name} blocked: miniPC/PARcore not connected")
            self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED: {name}", source="PAR_BRIDGE")
            return False
        return self.bus.write_output(name, value, source=source)

    def force_signal(self, name: str, value: Any, source: str = "PAR_FORCE") -> bool:
        # force z PAR-GUI też idzie przez PARcore, nie lokalny drugi PAR.
        if self.parcore_force_signal(name, value, source=source):
            return True
        if self._requires_minipc_connection(name):
            self.bus.log("MINIPC", f"{name} blocked: miniPC/PARcore not connected")
            self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED: {name}", source="PAR_BRIDGE")
            return False
        return self.bus.force_signal(name, value, source=source)


    def _requires_minipc_connection(self, name: str) -> bool:
        """Czy zapis z PAR dotyczy realnej elektroniki i nie może udawać lokalnie.

        TEST i LIVE mają pracować przez miniPC/TSP. Gdy miniPC nie jest
        połączony, PAR może pokazać panel, ale nie ma potwierdzać fizycznych
        testów lokalnym SignalBus.
        """
        n = str(name or "")
        physical_prefixes = (
            "play_", "rec_", "axis_", "sok_", "rrp_", "limit_", "sensor_",
            "par_lcd_", "par_matrix_", "par_f_led_", "par_rrp_", "par_mass_",
        )
        physical_names = {
            "par_manual_disconnect",
            "sensor_limits_status",
        }
        return n.startswith(physical_prefixes) or n in physical_names

    def set_signal(self, name: str, value: Any, source: str = "PAR") -> bool:
        """PAR-GUI → TSP → PARcore.set_signal(...). Lokalny zapis tylko dla HMI/test bez miniPC."""
        if self.parcore_set_signal(name, value, source=source):
            return True

        if self._requires_minipc_connection(name):
            self.bus.log("MINIPC", f"{name} blocked: miniPC/PARcore not connected")
            self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED: {name}", source="PAR_BRIDGE")
            return False

        m = self.bus.get_meta(name)
        if not m:
            return self.bus.force_signal(name, value, source=source)
        if m.is_output:
            self.bus.log("MINIPC", f"{name} blocked: miniPC/PARcore not connected")
            self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED: {name}", source="PAR_BRIDGE")
            return False
        return self.bus.set_input(name, value, source=source)

    def call_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """PAR-GUI → TSP → PARcore.call_action(...)."""
        payload = dict(payload or {})
        if name == "trace_signal" and payload:
            sig = payload.get("name")
            sec = payload.get("seconds", 30)
            if sig and self._send_to_tsp_if_ready(lambda c: c.trace_signal(sig, seconds=sec), f"trace_signal {sig}"):
                return True

        if self._parcore_call(name, payload):
            return True

        self.bus.log("PAR", f"Action {name} ignored (TSP/PARcore not connected)")
        self.bus.set_input("par_last_error", f"MINIPC_NOT_CONNECTED_ACTION: {name}", source="PAR_BRIDGE")
        return False

    def snapshot(self, include_meta: bool = False) -> Dict[str, Any]:
        return self.bus.snapshot(include_meta=include_meta)

    def load_take(self, path: str | Path) -> TarzanTakeData:
        data = self.take_player.load(path)
        payload = {
            "path": str(path),
            "name": Path(path).name,
            "columns": data.columns,
            "rows": data.rows,
            "metadata": getattr(data, "metadata", getattr(data, "header", {})),
            "header": getattr(data, "header", {}),
            "duration_ms": data.duration_ms() if callable(getattr(data, "duration_ms", None)) else getattr(data, "duration_ms", 0),
        }
        # EHR/TAKE z PAR-GUI trafia do PARcore jako TAKE payload.
        if self._parcore_call("take_load", payload):
            return data
        if self._client_is_connected():
            try:
                self.tsp_client.load_take(payload)
            except Exception as exc:
                self.bus.log("TSP_ERROR", f"LOAD_TAKE legacy failed: {exc}")
        return data

    def play_take(self) -> None:
        if not self.call_action("take_play"):
            self.take_player.play()

    def pause_take(self) -> None:
        if not self.call_action("take_pause"):
            self.take_player.pause()

    def stop_take(self) -> None:
        if not self.call_action("take_stop"):
            self.take_player.stop()

    def step_take_index(self, index: int):
        return self.take_player.step_to_index(index)

    def step_take_time(self, time_ms: int):
        return self.take_player.step_time(time_ms)

    def take_column_map(self):
        return self.mapper.map_take_columns()
