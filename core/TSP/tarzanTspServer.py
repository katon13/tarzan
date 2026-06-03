"""
Serwer TSP — TARZAN Signal Protocol.

Docelowy serwer TCP/JSONL dla TARZAN Signal Node.
Na tym etapie pracuje z TarzanTspSignalProvider z core/TSP/tarzanTspSignals.py.
Później ten provider zostanie podpięty pod SignalBus.
"""

from __future__ import annotations

import argparse
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .tarzanTspConfig import (
    TSP_BIND_HOST,
    TSP_FAST_INTERVAL_MS,
    TSP_HEALTH_INTERVAL_MS,
    TSP_LOG_DIR,
    TSP_NORMAL_INTERVAL_MS,
    TSP_PORT,
    TSP_SLOW_INTERVAL_MS,
    TSP_STATS_LOG_INTERVAL_MS,
)
from .tarzanTspLog import TarzanTspDebug, setup_tsp_logger
from .tarzanTspProtocol import (
    ALL_LANES,
    CMD_CALL_ACTION,
    CMD_DUMP_SNAPSHOT,
    CMD_GET_ALL_SIGNALS,
    CMD_GET_SIGNAL,
    CMD_GET_SIGNAL_CATALOG,
    CMD_GET_STATE,
    CMD_HELLO,
    CMD_PING,
    CMD_SET_SIGNAL,
    CMD_SUBSCRIBE,
    CMD_TRACE_SIGNAL,
    CMD_UNSUBSCRIBE,
    LANE_FAST,
    LANE_HEALTH,
    LANE_NORMAL,
    LANE_SLOW,
    LANE_URGENT,
    TspCommand,
    TspProtocolError,
    decode_jsonl_line,
    encode_jsonl,
    error_response,
    health_packet,
    hello_response,
    monotonic_ms,
    now_ms,
    ok_response,
    snajper_packet,
)
from .tarzanTspSignals import TarzanTspSignalProvider
from .tarzanTspLks import TarzanTspLks
from .tarzanTspLksStatusMap import component_from_nextion_id, validate_component
from .tarzanTspLksDiagnostics import TarzanTspLksDiagnostics

try:
    from .tarzanTspLksNextion5 import TarzanTspLksNextion5
except Exception as exc:  # pragma: no cover - LKS-N5 ma nie blokować TSP
    TarzanTspLksNextion5 = None  # type: ignore
    _LKS_N5_IMPORT_ERROR = exc
else:
    _LKS_N5_IMPORT_ERROR = None


@dataclass
class TarzanTspClientSession:
    client_id: int
    sock: socket.socket
    address: tuple[str, int]
    server: "TarzanTspServer"
    active: bool = True
    subscribed_lanes: set[str] = field(default_factory=lambda: {LANE_URGENT})
    subscribed_signals: set[str] = field(default_factory=set)
    trace_signals: Dict[str, int] = field(default_factory=dict)  # signal -> end_monotonic_ms
    trace_last_emit_ms: int = 0
    last_rx_ms: int = field(default_factory=monotonic_ms)
    last_tx_ms: int = field(default_factory=monotonic_ms)
    _send_lock: threading.Lock = field(default_factory=threading.Lock)
    _thread: Optional[threading.Thread] = None

    @property
    def name(self) -> str:
        return f"client#{self.client_id} {self.address[0]}:{self.address[1]}"

    def start(self) -> None:
        self._thread = threading.Thread(target=self._rx_loop, name=f"TSP-RX-{self.client_id}", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self.active = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def send(self, message: Dict[str, Any]) -> bool:
        if not self.active:
            return False
        raw = encode_jsonl(message)
        try:
            with self._send_lock:
                self.sock.sendall(raw)
            self.last_tx_ms = monotonic_ms()
            self.server.debug.record_tx(message, len(raw))
            self.server.mark_lks_for_message(message, direction="tx")
            return True
        except OSError as exc:
            self.server.debug.record_error("send_failed", {"client": self.name, "error": str(exc)})
            self.server.logger.warning("DISCONNECT %s reason=send_failed error=%s", self.name, exc)
            self.close()
            return False

    def wants_lane(self, lane: str) -> bool:
        return lane in self.subscribed_lanes

    def wants_signal(self, signal: str) -> bool:
        return not self.subscribed_signals or "*" in self.subscribed_signals or signal in self.subscribed_signals

    def filter_values(self, lane: str, values: Dict[str, Any]) -> Dict[str, Any]:
        if not values:
            return {}
        if not self.subscribed_signals or "*" in self.subscribed_signals:
            return values
        return {name: value for name, value in values.items() if name in self.subscribed_signals}

    def _rx_loop(self) -> None:
        buffer = b""
        self.sock.settimeout(0.5)
        while self.active and self.server.running:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    self.last_rx_ms = monotonic_ms()
                    self.server.debug.record_rx({"raw": line.decode("utf-8", errors="replace")}, len(line) + 1)
                    try:
                        message = decode_jsonl_line(line)
                        self.server.debug.rx.append({"ts": now_ms(), "client": self.name, "message": message})
                        self.server.mark_lks_dirty("rx")
                        response = self.server.handle_message(self, message)
                    except TspProtocolError as exc:
                        self.server.debug.record_error("protocol_error", {"client": self.name, "error": str(exc)})
                        self.server.mark_lks_dirty("error")
                        response = error_response("unknown", "protocol_error", detail=str(exc))
                    except Exception as exc:  # bezpieczeństwo serwera
                        self.server.debug.record_error("handler_error", {"client": self.name, "error": str(exc)})
                        self.server.mark_lks_dirty("error")
                        response = error_response("unknown", "handler_error", detail=str(exc))
                    if response is not None:
                        self.send(response)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as exc:
                self.server.debug.record_error("rx_loop_error", {"client": self.name, "error": str(exc)})
                self.server.mark_lks_dirty("error")
                break

        self.active = False
        self.server.remove_client(self)


class TarzanTspServer:
    def __init__(
        self,
        host: str = TSP_BIND_HOST,
        port: int = TSP_PORT,
        node_name: str = "tarzanMiniPC",
        provider: Optional[TarzanTspSignalProvider] = None,
        enable_lks: bool = True,
        lks_tty: str = "/dev/tty1",
        enable_lks_n5: bool = False,
        lks_n5_port: str = "",
        lks_n5_baudrate: int = 9600,
        lks_n5_dry_run: bool = False,
        lks_n5_refresh_interval_s: float = 2.0,
    ) -> None:
        self.host = host
        self.port = port
        self.node_name = node_name
        self.provider = provider or TarzanTspSignalProvider(node_name=node_name)
        self.debug = TarzanTspDebug()
        self.logger = setup_tsp_logger("TSP.SERVER")
        self.running = False
        self._stopping = False
        self._sock: Optional[socket.socket] = None
        self._clients: Dict[int, TarzanTspClientSession] = {}
        self._clients_lock = threading.Lock()
        self._next_client_id = 1
        self._accept_thread: Optional[threading.Thread] = None
        self._lane_thread: Optional[threading.Thread] = None
        self._last_stats_ms = monotonic_ms()
        self.lks = TarzanTspLks(self, tty_path=lks_tty, enabled=enable_lks)
        self.lks_n5 = None
        self._lks_n5_enabled = bool(enable_lks_n5)
        self._lks_n5_port = lks_n5_port
        self._lks_n5_baudrate = int(lks_n5_baudrate)
        self._lks_n5_dry_run = bool(lks_n5_dry_run)
        self._lks_n5_refresh_interval_s = max(0.5, float(lks_n5_refresh_interval_s))
        self._lks_n5_last_refresh_ms = 0
        self._lks_n5_dirty = False
        self._lks_n5_dirty_reason = ""
        # Antymruganie Nextiona 5:
        # - page status_main i reset kontrolek wykonujemy tylko raz, gdy trzeba wejść na stronę,
        # - cykl pracy wysyła potem wyłącznie zmienione .val, bez page i bez resetowania całej tablicy.
        self._lks_n5_status_page_ready = False
        self._lks_n5_status_cache: Dict[str, bool] = {}
        self._lks_n5_last_poll_ms = 0
        self._lks_n5_last_point_test_ms = 0

    # ------------------------------------------------------------------
    # LKS — LAMPKA KONTROLNA SYSTEMU
    # ------------------------------------------------------------------

    def mark_lks_dirty(self, reason: str = "event") -> None:
        if not self.lks:
            return

        # Filtrujemy zbyt częste zdarzenia, które nie są krytyczne dla LKS.
        # Budzimy LKS (odświeżamy ekran) natychmiast tylko dla błędów, urgent, connect/disconnect.
        # "rx" i zwykłe "tx" nie muszą budzić LKS natychmiast, bo on i tak odświeża się co 1 s.
        important = {"error", "urgent", "connect", "disconnect", "health", "urgent_event"}
        reason_low = reason.lower()
        if any(word in reason_low for word in important):
            self.lks.mark_dirty(reason)

    def mark_lks_for_message(self, message: Dict[str, Any], direction: str = "tx") -> None:
        lane = str(message.get("lane") or "").lower()
        event = str(message.get("event") or "").lower()
        cmd = str(message.get("cmd") or "").lower()

        # FAST nie wymusza natychmiastowego rysowania. LKS pokaże go w rytmie 1 s.
        if lane == LANE_FAST and event == "snajper_packet":
            return

        if lane in {LANE_URGENT, LANE_HEALTH} or event in {"urgent", "health"} or cmd:
            reason = f"{direction}:{lane or event or cmd}"
            immediate_n5 = lane == LANE_URGENT or event == "urgent" or "error" in reason
            self.mark_lks_outputs_dirty(reason, immediate_n5=immediate_n5)

    # ------------------------------------------------------------------
    # LKS-N5 — NEXTION 5, WYJŚCIE RÓWNOLEGŁE DO LKS-TTY
    # ------------------------------------------------------------------

    def _init_lks_n5(self) -> None:
        """Uruchamia opcjonalne wyjście LKS-N5.

        Błąd Nextiona 5 nie może zatrzymać TSP ani LKS-TTY.
        FAST/Snajper nie odświeża ekranu natychmiast; ekran ma cykl kontrolny.
        """
        if not self._lks_n5_enabled:
            return
        if self.lks_n5 is not None:
            return
        if TarzanTspLksNextion5 is None:
            self.debug.record_error("lks_n5_import_error", {"error": str(_LKS_N5_IMPORT_ERROR)})
            self.logger.warning("LKS-N5 disabled: import error=%s", _LKS_N5_IMPORT_ERROR)
            return
        if not self._lks_n5_dry_run and not self._lks_n5_port:
            self.debug.record_error("lks_n5_missing_port")
            self.logger.warning("LKS-N5 disabled: missing --lks-n5-port")
            return
        try:
            self.lks_n5 = TarzanTspLksNextion5(
                port=self._lks_n5_port,
                baudrate=self._lks_n5_baudrate,
                dry_run=self._lks_n5_dry_run,
                command_delay_s=0.02,
            )
            self.lks_n5.connect()
            self.lks_n5.bkcmd(3)
            self.lks_n5.show_boot_linux()
            self._lks_n5_status_page_ready = False
            self._lks_n5_status_cache = {}
            self._lks_n5_dirty = True
            self._lks_n5_dirty_reason = "startup"
            self._lks_n5_last_refresh_ms = monotonic_ms()
            self.logger.info("LKS-N5 START port=%s baudrate=%s dry_run=%s", self._lks_n5_port, self._lks_n5_baudrate, self._lks_n5_dry_run)
        except Exception as exc:
            self.debug.record_error("lks_n5_start_failed", {"error": str(exc)})
            self.logger.warning("LKS-N5 start failed: %s", exc)
            self.lks_n5 = None

    def _stop_lks_n5(self) -> None:
        """Zamyka LKS-N5 po zatrzymaniu pętli serwera.

        Najpierw gasimy flagi odświeżania, potem zamykamy port.
        Dzięki temu przy CTRL+C/systemd stop nie powstaje fałszywy warning
        typu "Bad file descriptor" z ostatniego cyklu refresh.
        """
        self._lks_n5_dirty = False
        self._lks_n5_dirty_reason = ""
        self._lks_n5_status_page_ready = False
        self._lks_n5_status_cache = {}
        device = self.lks_n5
        self.lks_n5 = None
        if device is None:
            return
        try:
            device.close()
        except Exception as exc:
            self.debug.record_error("lks_n5_stop_failed", {"error": str(exc)})

    def mark_lks_n5_dirty(self, reason: str = "event", immediate: bool = False) -> None:
        """Oznacza LKS-N5 do lekkiego odświeżenia.

        Ten mechanizm celowo nie budzi ekranu po każdym pakiecie FAST.
        Natychmiastowe odświeżanie zostaje tylko dla URGENT/ERROR/connect/disconnect.
        """
        if not self._lks_n5_enabled or self._stopping:
            return
        self._lks_n5_dirty = True
        self._lks_n5_dirty_reason = reason
        if immediate:
            self._refresh_lks_n5(reason=reason, immediate=True)

    def mark_lks_outputs_dirty(self, reason: str = "event", immediate_n5: bool = False) -> None:
        """Wspólny dyspozytor: LKS-TTY + LKS-N5.

        LKS-TTY zostaje bez zmian, LKS-N5 dochodzi równolegle.
        """
        self.mark_lks_dirty(reason)
        self.mark_lks_n5_dirty(reason, immediate=immediate_n5)


    def _decode_lks_n5_touch_event(self, event: object) -> Optional[str]:
        """Dekoduje kliknięcie status_main z Nextiona 5.

        Obsługiwany format Nextion: 0x65 page_id component_id touch_event.
        Test punktowy uruchamiamy tylko na release, czyli touch_event=1.
        """
        raw = bytes(getattr(event, "raw", b"") or b"")
        if len(raw) < 4 or raw[0] != 0x65:
            return None
        _page_id = int(raw[1])
        component_id = int(raw[2])
        touch_event = int(raw[3])
        if touch_event != 1:
            return None
        try:
            return component_from_nextion_id(component_id)
        except Exception as exc:
            self.debug.record_error("lks_n5_unknown_touch", {"component_id": component_id, "error": str(exc)})
            return None

    def _poll_lks_n5_events(self) -> None:
        """Czyta kliknięcia operatora z LKS-N5.

        Praca ciągła jest spokojna: samo czytanie RX jest lekkie, a pełniejszy test
        uruchamiamy dopiero po kliknięciu konkretnego elementu status_main.
        """
        if self._stopping or self.lks_n5 is None:
            return
        try:
            for event in self.lks_n5.read_events():
                component = self._decode_lks_n5_touch_event(event)
                if component:
                    self._run_lks_n5_point_test(component)
        except Exception as exc:
            self.debug.record_error("lks_n5_event_poll_failed", {"error": str(exc)})
            self.logger.warning("LKS-N5 event poll failed: %s", exc)

    def _run_lks_n5_point_test(self, component: str) -> None:
        """Testuje jeden kliknięty komponent i aktualizuje tylko jego kontrolkę."""
        if self._stopping or self.lks_n5 is None:
            return
        now = monotonic_ms()
        if now - self._lks_n5_last_point_test_ms < 300:
            return
        self._lks_n5_last_point_test_ms = now
        name = validate_component(component)
        try:
            if not self._lks_n5_status_page_ready:
                self.lks_n5.show_status(reset=True)
                self._lks_n5_status_page_ready = True
                self._lks_n5_status_cache = {}

            base = bool(self._lks_n5_status_cache.get(name, False))
            self.logger.info("LKS-N5 POINT TEST component=%s", name)
            self.lks_n5.blink_component(name, base_value=base)
            diagnostics = TarzanTspLksDiagnostics()
            diagnostics.run_component(name)
            ok = bool(diagnostics.status_map().get(name, False))
            self.lks_n5.set_status(name, ok)
            self._lks_n5_status_cache[name] = ok
            self.logger.info("LKS-N5 POINT TEST DONE component=%s ok=%s", name, ok)
        except Exception as exc:
            self.debug.record_error("lks_n5_point_test_failed", {"component": name, "error": str(exc)})
            self.logger.warning("LKS-N5 point test failed component=%s error=%s", name, exc)
            try:
                self.lks_n5.set_status(name, False)
                self._lks_n5_status_cache[name] = False
            except Exception:
                pass

    def _refresh_lks_n5(self, reason: str = "cycle", immediate: bool = False) -> None:
        if self._stopping or self.lks_n5 is None:
            return
        now = monotonic_ms()
        if not immediate and now - self._lks_n5_last_refresh_ms < int(self._lks_n5_refresh_interval_s * 1000):
            return

        try:
            clients = self.clients()
            client_count = len(clients)
            reason_low = reason.lower()

            desired_statuses: Dict[str, bool] = {
                "linux_sys": True,
                "snajper_sys": reason_low.startswith("health"),
                "take_sys": True,
                "par_sys": client_count > 0,
                "ehr_sys": client_count > 0,
                "pok_play": True,
                "pok_rec": True,
            }

            # WAŻNE: antymruganie.
            # Nie wolno w cyklu robić show_status(reset=True), bo to wysyła page + reset 30 kontrolek
            # i fizyczny Nextion wygląda jakby mrugał. Stronę ustawiamy tylko raz, a dalej lecą
            # wyłącznie zmienione wartości .val.
            if not self._lks_n5_status_page_ready:
                self.lks_n5.show_status(reset=True)
                self._lks_n5_status_page_ready = True
                self._lks_n5_status_cache = {}

            changed_statuses = {
                name: value
                for name, value in desired_statuses.items()
                if self._lks_n5_status_cache.get(name) != value
            }

            if changed_statuses:
                self.lks_n5.set_many_statuses(changed_statuses)
                self._lks_n5_status_cache.update(changed_statuses)

            self._lks_n5_last_refresh_ms = now
            self._lks_n5_dirty = False
            self._lks_n5_dirty_reason = ""
        except Exception as exc:
            self.debug.record_error("lks_n5_refresh_failed", {"reason": reason, "error": str(exc)})
            self.logger.warning("LKS-N5 refresh failed reason=%s error=%s", reason, exc)

    # ------------------------------------------------------------------
    # START / STOP
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self.running:
            return
        self._stopping = False
        self.running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(10)
        self._sock.settimeout(0.5)
        self.logger.info("TSP SERVER START host=%s port=%s node=%s", self.host, self.port, self.node_name)
        self.lks.start()
        self._init_lks_n5()
        self._accept_thread = threading.Thread(target=self._accept_loop, name="TSP-ACCEPT", daemon=True)
        self._lane_thread = threading.Thread(target=self._lane_loop, name="TSP-LANES", daemon=True)
        self._accept_thread.start()
        self._lane_thread.start()

    def serve_forever(self) -> None:
        self.start()
        try:
            while self.running:
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.logger.info("TSP SERVER STOP requested=KeyboardInterrupt")
        finally:
            self.stop()

    def stop(self) -> None:
        # Kolejność jest ważna dla LKS-N5:
        # 1) zatrzymać pętle,
        # 2) poczekać aż lane-loop przestanie odświeżać,
        # 3) dopiero zamknąć port serial.
        self._stopping = True
        self.running = False
        self._lks_n5_dirty = False
        self._lks_n5_dirty_reason = ""

        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

        with self._clients_lock:
            clients = list(self._clients.values())
            self._clients.clear()
        for client in clients:
            client.close()

        for thread in (self._accept_thread, self._lane_thread):
            if thread is not None and thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=1.0)

        self._stop_lks_n5()
        self.lks.stop()
        self.logger.info("TSP SERVER STOPPED")

    # ------------------------------------------------------------------
    # KLIENCI
    # ------------------------------------------------------------------

    def _accept_loop(self) -> None:
        while self.running:
            try:
                assert self._sock is not None
                sock, address = self._sock.accept()
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                with self._clients_lock:
                    client_id = self._next_client_id
                    self._next_client_id += 1
                    session = TarzanTspClientSession(client_id, sock, address, self)
                    self._clients[client_id] = session
                self.logger.info("CONNECT %s", session.name)
                self.mark_lks_outputs_dirty("connect", immediate_n5=True)
                session.start()
                session.send(hello_response(self.node_name, "server", self.provider.signal_count()))
            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    self.debug.record_error("accept_os_error")
                break
            except Exception as exc:
                self.debug.record_error("accept_error", {"error": str(exc)})

    def remove_client(self, client: TarzanTspClientSession) -> None:
        with self._clients_lock:
            self._clients.pop(client.client_id, None)
        client.close()
        self.logger.info("DISCONNECT %s", client.name)
        self.mark_lks_outputs_dirty("disconnect", immediate_n5=True)

    def clients(self) -> list[TarzanTspClientSession]:
        with self._clients_lock:
            return [c for c in self._clients.values() if c.active]

    # ------------------------------------------------------------------
    # KOMENDY
    # ------------------------------------------------------------------

    def handle_message(self, client: TarzanTspClientSession, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        command = TspCommand.from_message(message)
        cmd = command.cmd
        payload = command.payload

        if cmd == CMD_HELLO:
            return hello_response(self.node_name, "server", self.provider.signal_count())

        if cmd == CMD_PING:
            return ok_response(CMD_PING, pong=True, client_ts=payload.get("ts"))

        if cmd == CMD_GET_SIGNAL:
            name = str(payload.get("name", ""))
            try:
                value = self.provider.get_signal(name)
                return ok_response(cmd, name=name, value=value)
            except KeyError:
                return error_response(cmd, "unknown_signal", name=name)

        if cmd == CMD_SET_SIGNAL:
            name = str(payload.get("name", ""))
            result = self.provider.set_signal(name, payload.get("value"), source=f"client_{client.client_id}")
            if not result.get("ok"):
                self.debug.record_error(str(result.get("error", "set_signal_failed")), {"client": client.name, "name": name})
                # Nie przekazujemy pola "error" drugi raz jako **kwargs, bo error_response()
                # ma je już jako argument pozycyjny. Dzięki temu odmowy typu write_denied
                # wracają czytelnie, a nie jako handler_error.
                fields = {k: v for k, v in result.items() if k not in {"ok", "error"}}
                return error_response(cmd, str(result.get("error", "set_signal_failed")), **fields)
            return ok_response(cmd, **{k: v for k, v in result.items() if k != "ok"})

        if cmd == CMD_GET_SIGNAL_CATALOG:
            return ok_response(cmd, signals=self.provider.catalog())

        if cmd == CMD_GET_ALL_SIGNALS:
            return ok_response(cmd, values=self.provider.get_all())

        if cmd == CMD_SUBSCRIBE:
            lanes = payload.get("lanes") or payload.get("lane") or [LANE_FAST, LANE_NORMAL, LANE_SLOW, LANE_HEALTH, LANE_URGENT]
            if isinstance(lanes, str):
                lanes = [lanes]
            lane_set = {str(l).lower() for l in lanes if str(l).lower() in ALL_LANES}
            signals = payload.get("signals") or ["*"]
            if isinstance(signals, str):
                signals = [signals]
            client.subscribed_lanes.update(lane_set or {LANE_URGENT})
            client.subscribed_signals.update(str(x) for x in signals)
            self.logger.info("SUBSCRIBE %s lanes=%s signals=%s", client.name, sorted(client.subscribed_lanes), len(client.subscribed_signals))
            return ok_response(cmd, lanes=sorted(client.subscribed_lanes), signals=sorted(client.subscribed_signals))

        if cmd == CMD_UNSUBSCRIBE:
            lanes = payload.get("lanes") or payload.get("lane") or []
            if isinstance(lanes, str):
                lanes = [lanes]
            for lane in lanes:
                client.subscribed_lanes.discard(str(lane).lower())
            signals = payload.get("signals") or []
            if isinstance(signals, str):
                signals = [signals]
            for signal in signals:
                client.subscribed_signals.discard(str(signal))
            return ok_response(cmd, lanes=sorted(client.subscribed_lanes), signals=sorted(client.subscribed_signals))

        if cmd == CMD_GET_STATE:
            return ok_response(cmd, state=self.provider.state_summary(), clients=len(self.clients()), stats=self.debug.stats.as_dict())

        if cmd == CMD_CALL_ACTION:
            name = str(payload.get("name", ""))
            result = self.provider.call_action(name, payload.get("payload") or {})
            if not result.get("ok"):
                fields = {k: v for k, v in result.items() if k not in {"ok", "error"}}
                return error_response(cmd, str(result.get("error", "action_failed")), **fields)
            return ok_response(cmd, **{k: v for k, v in result.items() if k != "ok"})

        if cmd == CMD_TRACE_SIGNAL:
            name = str(payload.get("name", ""))
            seconds = int(payload.get("seconds", 15))
            if not name:
                return error_response(cmd, "missing_signal")
            client.trace_signals[name] = monotonic_ms() + seconds * 1000
            return ok_response(cmd, name=name, seconds=seconds)

        if cmd == CMD_DUMP_SNAPSHOT:
            path = self.debug.dump_snapshot(TSP_LOG_DIR)
            return ok_response(cmd, path=str(path))

        return error_response(cmd, "unknown_cmd")

    # ------------------------------------------------------------------
    # PASMA / BROADCAST
    # ------------------------------------------------------------------

    def _lane_loop(self) -> None:
        # Stabilne czasy pasm
        last_fast = last_normal = last_slow = last_health = monotonic_ms()
        self._last_stats_ms = last_fast

        while self.running:
            now = monotonic_ms()

            # Pobieramy listę klientów raz na obieg pętli
            clients = self.clients()
            client_count = len(clients)

            # Tick providera wykonujemy przed pasmami, żeby dane były świeże
            self.provider.tick(client_count=client_count)

            # 1. Obsługa URGENT — najwyższy priorytet, bez celowego opóźniania
            urgent_items = self.provider.pop_urgent_events()
            has_urgent = len(urgent_items) > 0
            for item in urgent_items:
                self.broadcast(item, lane=LANE_URGENT, immediate=True, clients=clients)

            # 2. Pasma regularne (FAST, NORMAL, SLOW, HEALTH)
            # FAST ~10ms
            if now - last_fast >= TSP_FAST_INTERVAL_MS:
                dt = now - last_fast
                last_fast = now
                self.broadcast_lane(LANE_FAST, dt, clients=clients)

            # NORMAL ~50ms
            if now - last_normal >= TSP_NORMAL_INTERVAL_MS:
                dt = now - last_normal
                last_normal = now
                self.broadcast_lane(LANE_NORMAL, dt, clients=clients)

            # SLOW ~500ms
            if now - last_slow >= TSP_SLOW_INTERVAL_MS:
                dt = now - last_slow
                last_slow = now
                self.broadcast_lane(LANE_SLOW, dt, clients=clients)

            # HEALTH ~1000ms
            if now - last_health >= TSP_HEALTH_INTERVAL_MS:
                last_health = now
                health = health_packet(
                    node=self.node_name,
                    clients=client_count,
                    stats=self.debug.stats.as_dict(),
                    state=self.provider.state_summary(),
                )
                self.broadcast(health, lane=LANE_HEALTH, clients=clients)

            # 3. Logi statystyk
            if now - self._last_stats_ms >= TSP_STATS_LOG_INTERVAL_MS:
                self._last_stats_ms = now
                stats = self.debug.stats.as_dict()
                self.logger.info(
                    "TSP_STATS clients=%s tx=%s rx=%s errors=%s dropped=%s lanes=%s",
                    client_count, stats["packets_tx"], stats["packets_rx"], stats["errors"], stats["dropped"], stats["lane_packets"],
                )

            # 4. LKS-N5 — spokojna praca:
            # - nie robimy pełnych testów w pętli,
            # - nie resetujemy status_main cyklicznie,
            # - czytamy tylko lekkie eventy dotyku,
            # - status odświeżamy wyłącznie, gdy stan został oznaczony jako dirty.
            if not self._stopping and self.lks_n5 is not None:
                self._poll_lks_n5_events()
                if self._lks_n5_dirty:
                    self._refresh_lks_n5(reason=self._lks_n5_dirty_reason or "event", immediate=False)

            # 5. Traces
            self._emit_traces(clients=clients, now=now)

            # 5. Adaptacyjne usypianie pętli
            self._sleep_until_next_lane(
                now_ms=monotonic_ms(),
                last_fast=last_fast,
                last_normal=last_normal,
                last_slow=last_slow,
                last_health=last_health,
                has_urgent=has_urgent
            )

    def _sleep_until_next_lane(
        self,
        now_ms: int,
        last_fast: int,
        last_normal: int,
        last_slow: int,
        last_health: int,
        has_urgent: bool = False,
    ) -> None:
        # Jeśli właśnie wysłaliśmy pilne zdarzenia, śpimy bardzo krótko (1ms),
        # żeby sprawdzić czy nie ma kolejnych w buforze providera.
        if has_urgent:
            time.sleep(0.001)
            return

        # Obliczamy czas do najbliższego wymaganego pasma
        next_due_ms = min(
            last_fast + TSP_FAST_INTERVAL_MS,
            last_normal + TSP_NORMAL_INTERVAL_MS,
            last_slow + TSP_SLOW_INTERVAL_MS,
            last_health + TSP_HEALTH_INTERVAL_MS,
            self._last_stats_ms + TSP_STATS_LOG_INTERVAL_MS,
        )

        remaining_ms = next_due_ms - now_ms

        # Jeśli już czas na pasmo (lub spóźnienie), nie śpimy długo.
        if remaining_ms <= 0:
            time.sleep(0.001)
            return

        # Adaptacyjny sleep: śpimy do najbliższego pasma, ale nie więcej niż 10ms (FAST),
        # aby zachować responsywność na nowe URGENT z providera.
        sleep_s = min(0.010, remaining_ms / 1000.0)

        # Zgodnie z wymaganiem: sleep zazwyczaj w zakresie kilku ms.
        if sleep_s < 0.002:
            sleep_s = 0.002

        time.sleep(sleep_s)

    def broadcast_lane(self, lane: str, dt_ms: int, clients: Optional[list[TarzanTspClientSession]] = None) -> None:
        values = self.provider.get_lane_values(lane, None)
        if not values:
            return
        packet = snajper_packet(lane, values, dt_ms=dt_ms)
        self.broadcast(packet, lane=lane, clients=clients)

    def broadcast(self, message: Dict[str, Any], lane: str, immediate: bool = False, clients: Optional[list[TarzanTspClientSession]] = None) -> None:
        target_clients = clients if clients is not None else self.clients()
        for client in target_clients:
            if not client.wants_lane(lane):
                continue
            outgoing = message
            if message.get("event") == "snajper_packet" and isinstance(message.get("values"), dict):
                values = client.filter_values(lane, message["values"])
                if not values:
                    continue
                outgoing = dict(message)
                outgoing["values"] = values
            client.send(outgoing)

    def _emit_traces(self, clients: Optional[list[TarzanTspClientSession]] = None, now: Optional[int] = None) -> None:
        now = now or monotonic_ms()
        target_clients = clients if clients is not None else self.clients()
        for client in target_clients:
            expired = [name for name, end_ms in client.trace_signals.items() if end_ms <= now]
            for name in expired:
                client.trace_signals.pop(name, None)
            if not client.trace_signals:
                continue
            # Trace ma rytm FAST, nie pętli 1 ms. Dzięki temu nie zalewa klienta.
            if client.trace_last_emit_ms and now - client.trace_last_emit_ms < TSP_FAST_INTERVAL_MS:
                continue
            client.trace_last_emit_ms = now
            for name in list(client.trace_signals):
                try:
                    value = self.provider.get_signal(name)
                except KeyError:
                    continue
                client.send({"event": "trace", "lane": "trace", "ts": now, "signal": name, "value": value})


def main() -> None:
    parser = argparse.ArgumentParser(description="TARZAN TSP Server")
    parser.add_argument("--host", default=TSP_BIND_HOST)
    parser.add_argument("--port", type=int, default=TSP_PORT)
    parser.add_argument("--node", default="tarzanMiniPC")
    parser.add_argument("--lks", dest="lks", action="store_true", default=True, help="Włącz LKS na lokalnym TTY")
    parser.add_argument("--no-lks", dest="lks", action="store_false", help="Wyłącz LKS")
    parser.add_argument("--lks-tty", default="/dev/tty1", help="Ścieżka TTY dla LKS, np. /dev/tty1 albo -")
    parser.add_argument("--lks-n5", dest="lks_n5", action="store_true", default=False, help="Włącz równoległe wyjście LKS-N5 / Nextion 5")
    parser.add_argument("--lks-n5-port", default="", help="Port Nextion 5, najlepiej /dev/serial/by-id/...")
    parser.add_argument("--lks-n5-baudrate", type=int, default=9600)
    parser.add_argument("--lks-n5-dry-run", action="store_true", help="Test integracji LKS-N5 bez portu serial")
    parser.add_argument("--lks-n5-refresh", type=float, default=2.0, help="Lekki interwał odświeżania LKS-N5 w sekundach")
    args = parser.parse_args()

    server = TarzanTspServer(
        host=args.host,
        port=args.port,
        node_name=args.node,
        enable_lks=args.lks,
        lks_tty=args.lks_tty,
        enable_lks_n5=args.lks_n5,
        lks_n5_port=args.lks_n5_port,
        lks_n5_baudrate=args.lks_n5_baudrate,
        lks_n5_dry_run=args.lks_n5_dry_run,
        lks_n5_refresh_interval_s=args.lks_n5_refresh,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
