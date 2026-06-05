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
        # ETAP 1D: tryb LIVE utrzymujemy własną flagą, nie samym bus.mode.
        # Snapshot z miniPC albo lokalna zmiana stanu nie może zabić wątku TSP.
        self._tsp_active: bool = False
        # ETAP 1C: na starcie LIVE nie bierzemy FAST/*, bo PAR może zostać zalany
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
        if mode == "LIVE":
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

    def _send_to_tsp_if_ready(self, send_fn: Callable[[TarzanTspClient], Any], action_name: str) -> bool:
        """Wysyła do TSP tylko po pełnym połączeniu; w fazie LIVE-start nie wolno wywalać UI."""
        if self.bus.mode != "LIVE" or not self._client_is_connected():
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

        ETAP 1D: jeżeli połączenie spadnie po kliknięciu LIVE, PAR nie może
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

                    self._bus_log("TSP", f"Connected to {self.tsp_host}. Sending HELLO...")
                    self._bus_set_input("par_state", "CONNECTED", source="TSP_LIVE")
                    client.hello()
                else:
                    # ETAP 1F: LIVE ma się trzymać. Wysyłamy lekki heartbeat,
                    # żeby martwy socket został wykryty i pętla mogła zrobić reconnect.
                    try:
                        assert self.tsp_client is not None
                        self.tsp_client.ping()
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
            self.tsp_client.close()
            self.tsp_client = None
        self._tsp_subscribed = False
        self._tsp_thread = None

    def _handle_tsp_message(self, message: Dict[str, Any]) -> None:
        event = message.get("event")
        cmd = message.get("cmd")
        ok = message.get("ok", True)

        if event == "snajper_packet":
            values = message.get("values", {})
            # ETAP 6-7: Apply snapshot do lokalnego SignalBus PAR
            # Unikamy pętli zwrotnej przez apply_snapshot (filtrowanie w Bus)
            self.bus.apply_snapshot(values, source="TSP_LIVE")
        
        elif cmd == "get_state" and ok:
            # ETAP 4: Synchronizacja stanu początkowego
            state = message.get("state", {})
            if state:
                self.bus.log("TSP", f"GET_STATE OK: signals={len(state.get('signals', state))}")
                self.bus.apply_snapshot(state, source="TSP_INITIAL")

        elif (event == "hello") or (cmd == "hello" and ok):
            node = message.get("node") or message.get("node_name") or message.get("node_id", "unknown")
            self.bus.log("TSP", f"Handshake OK: {node}")
            # ETAP 1C: pierwszy LIVE ma być lekki. Nie subskrybujemy FAST ani "*".
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

        elif event == "error" or (not ok and (message.get("error") or message.get("message"))):
            err_code = message.get("error", "unknown_error")
            err_msg = message.get("message") or message.get("reason") or err_code
            self.bus.log("TSP_ERROR", f"TSP Error ({err_code}): {err_msg}")
            
            # ETAP 8: Powiadamianie UI o błędzie
            self.bus.set_input("par_last_error", f"{err_code}: {err_msg}", source="TSP_LIVE")
            
            # Specjalna obsługa odmowy zapisu dla UI (Etap 7-8)
            if err_code == "write_denied":
                self.bus.log("TSP_ERROR", f"Access Denied: {message.get('reason', 'control_owner_conflict')}")
                self.bus.set_input("par_write_denied_event", 1, source="TSP_LIVE")
                # Resetujemy flagę zdarzenia po chwili, żeby mogła "mignąć" w UI
                threading.Timer(1.0, lambda: self.bus.set_input("par_write_denied_event", 0, source="TSP_LIVE")).start()

        elif event == "disconnect":
            self.bus.log("TSP", "Server disconnected.")
            self._drop_tsp_client(reason="server_disconnect_event")

        elif event == "log_event":
            # ETAP 16: Odbieranie logów z MiniPC
            src = message.get("source", "REMOTE")
            msg = message.get("message", "")
            # Wpisujemy do lokalnego busa, co automatycznie odświeży panel logów PAR
            self.bus.log(f"MINI:{src}", msg)

        elif event == "trace":
            # ETAP 16: Odbieranie danych trace w czasie rzeczywistym
            name = message.get("signal", "unknown")
            val = message.get("value", 0)
            self.bus.force_signal(f"trace_{name}", val, source="TSP_TRACE")

    def nextion_connect(self):
        return self.nextion.connect_enabled()

    def nextion_sync(self, force: bool = False):
        return self.nextion.sync(force=force)

    def poll(self):
        return self.nextion.poll()

    def flush_snajper_commands(self):
        if hasattr(self.nextion, "flush_snajper_commands"):
            return self.nextion.flush_snajper_commands()

    def queue_snajper_command(self, scope: str, component: str, prop: str, value):
        if hasattr(self.nextion, "queue_snajper_command"):
            return self.nextion.queue_snajper_command(scope, component, prop, value)

    def read_input(self, name: str, default: Any = 0) -> Any:
        return self.bus.read_input(name, default)

    def set_input(self, name: str, value: Any, source: str = "PAR") -> bool:
        if self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"set_input {name}"):
            return True
        return self.bus.set_input(name, value, source=source)

    def write_output(self, name: str, value: Any, source: str = "PAR") -> bool:
        if self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"write_output {name}"):
            return True
        return self.bus.write_output(name, value, source=source)

    def force_signal(self, name: str, value: Any, source: str = "PAR_FORCE") -> bool:
        if self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"force_signal {name}"):
            return True
        return self.bus.force_signal(name, value, source=source)

    def set_signal(self, name: str, value: Any, source: str = "PAR") -> bool:
        """Alias dla ujednoliconego zapisu sygnału w obu trybach (Etap 7-8)."""
        if self._send_to_tsp_if_ready(lambda c: c.set_signal(name, value), f"set_signal {name}"):
            return True

        m = self.bus.get_meta(name)
        if not m:
            return self.bus.force_signal(name, value, source=source)
        if m.is_input() or name.startswith("par_"):
            return self.bus.set_input(name, value, source=source)
        else:
            return self.bus.write_output(name, value, source=source)

    def call_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Wysyła komendę administracyjną do TSP (Etap 8)."""
        if name == "trace_signal" and payload:
            sig = payload.get("name")
            sec = payload.get("seconds", 30)
            if sig and self._send_to_tsp_if_ready(lambda c: c.trace_signal(sig, seconds=sec), f"trace_signal {sig}"):
                return True

        if self._send_to_tsp_if_ready(lambda c: c.call_action(name, payload), f"call_action {name}"):
            return True

        self.bus.log("PAR", f"Action {name} ignored (TSP not connected)")
        return False

    def snapshot(self, include_meta: bool = False) -> Dict[str, Any]:
        return self.bus.snapshot(include_meta=include_meta)

    def load_take(self, path: str | Path) -> TarzanTakeData:
        data = self.take_player.load(path)
        if self._client_is_connected() and self.bus.mode == "LIVE":
            # ETAP 14: Przesyłanie danych TAKE do MiniPC
            payload = {
                "name": Path(path).name,
                "columns": data.columns,
                "rows": data.rows,
                "metadata": data.metadata,
                "duration_ms": data.duration_ms()
            }
            self.tsp_client.load_take(payload)
        return data

    def play_take(self) -> None:
        if self._client_is_connected() and self.bus.mode == "LIVE":
            self.call_action("play_take")
        else:
            self.take_player.play()

    def pause_take(self) -> None:
        if self._client_is_connected() and self.bus.mode == "LIVE":
            self.call_action("pause_take")
        else:
            self.take_player.pause()

    def stop_take(self) -> None:
        if self._client_is_connected() and self.bus.mode == "LIVE":
            self.call_action("stop_take")
        else:
            self.take_player.stop()

    def step_take_index(self, index: int):
        return self.take_player.step_to_index(index)

    def step_take_time(self, time_ms: int):
        return self.take_player.step_time(time_ms)

    def take_column_map(self):
        return self.mapper.map_take_columns()
