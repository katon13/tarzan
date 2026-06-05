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
        if after is not None and after_cancel is not None:
            self.take_player.set_scheduler(after, after_cancel)
        
        # NEXTION SNAJPER: fizyczny most Nextiona jako pod-komponent
        from hardware.tarzanNextion.bridge import TarzanNextionBridge
        self.nextion = TarzanNextionBridge(self.bus)

        # TSP CLIENT: dla trybu LIVE
        self.tsp_client: Optional[TarzanTspClient] = None
        self._tsp_thread: Optional[threading.Thread] = None

    def set_mode(self, mode: str) -> None:
        self.bus.set_mode(mode)
        if mode == "LIVE":
            self._start_tsp()
        else:
            self._stop_tsp()

    def _start_tsp(self) -> None:
        if self._tsp_thread and self._tsp_thread.is_alive():
            return
        self.bus.log("TSP", "Starting TSP connector thread (LIVE)...")
        self._tsp_thread = threading.Thread(target=self._tsp_connector_loop, name="TSP-CONNECTOR", daemon=True)
        self._tsp_thread.start()

    def _tsp_connector_loop(self) -> None:
        """Pętla dbająca o połączenie i podtrzymanie sesji TSP."""
        while self.bus.mode == "LIVE":
            if self.tsp_client is None:
                try:
                    self.tsp_client = TarzanTspClient(host=self.tsp_host, name="tarzanPAR")
                    self.tsp_client.on_message = self._handle_tsp_message
                    self.tsp_client.connect()
                    
                    # Handshake
                    self.bus.log("TSP", f"Connected to {TSP_MINI_PC_HOST}. Sending HELLO...")
                    self.tsp_client.hello()
                except Exception as e:
                    self.bus.log("TSP", f"Connection failed: {e}")
                    self.tsp_client = None
            
            time.sleep(5.0) # Re-check co 5s

    def _stop_tsp(self) -> None:
        if self.tsp_client:
            self.bus.log("TSP", "Disconnecting from MiniPC...")
            self.tsp_client.close()
            self.tsp_client = None
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
            # Pełna sekwencja po połączeniu
            if self.tsp_client:
                self.tsp_client.ping()
                self.tsp_client.get_state()
                self.tsp_client.subscribe(lanes=["fast", "normal", "slow", "health", "urgent"])
        
        elif cmd == "subscribe" and ok:
            self.bus.log("TSP", "SUBSCRIBE OK: receiving live updates.")

        elif event == "error" or (not ok and (message.get("error") or message.get("message"))):
            err_code = message.get("error", "unknown_error")
            err_msg = message.get("message") or message.get("reason") or err_code
            self.bus.log("TSP_ERROR", f"TSP Error ({err_code}): {err_msg}")
            # Specjalna obsługa odmowy zapisu dla UI (Etap 7-8)
            if err_code == "write_denied":
                self.bus.log("TSP_ERROR", f"Access Denied: {message.get('reason', 'control_owner_conflict')}")

        elif event == "disconnect":
            self.bus.log("TSP", "Server disconnected.")

        elif event == "log_event":
            # ETAP 16: Odbieranie logów z MiniPC
            src = message.get("source", "REMOTE")
            msg = message.get("message", "")
            # Wpisujemy do lokalnego busa, co automatycznie odświeży panel logów PAR
            self.bus.log(f"MINI:{src}", msg)

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
        if self.tsp_client and self.bus.mode == "LIVE":
            # W trybie LIVE wysyłamy do TSP zamiast pisać lokalnie (Etap 7-8)
            self.tsp_client.set_signal(name, value)
            return True
        return self.bus.set_input(name, value, source=source)

    def write_output(self, name: str, value: Any, source: str = "PAR") -> bool:
        if self.tsp_client and self.bus.mode == "LIVE":
            self.tsp_client.set_signal(name, value)
            return True
        return self.bus.write_output(name, value, source=source)

    def force_signal(self, name: str, value: Any, source: str = "PAR_FORCE") -> bool:
        if self.tsp_client and self.bus.mode == "LIVE":
            # ETAP 7: Delegacja wymuszenia do TSP
            self.tsp_client.set_signal(name, value)
            return True
        return self.bus.force_signal(name, value, source=source)

    def call_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Wysyła komendę administracyjną do TSP (Etap 8)."""
        if self.tsp_client and self.bus.mode == "LIVE":
            self.tsp_client.call_action(name, payload)
            return True
        self.bus.log("PAR", f"Action {name} ignored (not in LIVE mode)")
        return False

    def snapshot(self, include_meta: bool = False) -> Dict[str, Any]:
        return self.bus.snapshot(include_meta=include_meta)

    def load_take(self, path: str | Path) -> TarzanTakeData:
        data = self.take_player.load(path)
        if self.tsp_client and self.bus.mode == "LIVE":
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
        if self.tsp_client and self.bus.mode == "LIVE":
            self.call_action("play_take")
        else:
            self.take_player.play()

    def pause_take(self) -> None:
        if self.tsp_client and self.bus.mode == "LIVE":
            self.call_action("pause_take")
        else:
            self.take_player.pause()

    def stop_take(self) -> None:
        if self.tsp_client and self.bus.mode == "LIVE":
            self.call_action("stop_take")
        else:
            self.take_player.stop()

    def step_take_index(self, index: int):
        return self.take_player.step_to_index(index)

    def step_take_time(self, time_ms: int):
        return self.take_player.step_time(time_ms)

    def take_column_map(self):
        return self.mapper.map_take_columns()
