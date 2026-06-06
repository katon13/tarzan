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
import multiprocessing
import time
import json
import os
import platform
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
    CMD_LOAD_TAKE,
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
from .tarzanTspLksInventory import TarzanTspLksInventory


def _diagnostics_worker(inventory_dict: Dict[str, Any], queue: multiprocessing.Queue) -> None:
    """
    Izolowany proces diagnostyczny dla ochrony przed crashami libusb/PoKeys (ETAP 3).
    Uruchamiany w osobnym procesie, aby crash w natywnej bibliotece nie zabił serwera TSP.
    """
    try:
        from core.TSP.tarzanTspLksDiagnostics import TarzanTspLksDiagnostics
        diag = TarzanTspLksDiagnostics(collect_inventory_if_missing=False)
        diag._inventory = inventory_dict
        diag.run_all()
        queue.put({"ok": True, "results": diag.status_map()})
    except Exception as exc:
        queue.put({"ok": False, "error": str(exc)})

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
    node_name: Optional[str] = None  # Ustawiane przez CMD_HELLO
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
        self._loaded_take: Optional[Dict[str, Any]] = None
        self._take_playback_start_ms: int = 0
        self._take_playback_row_idx: int = 0

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

            # ETAP 13: od momentu startu usługi systemd Linux przejmuje ekran
            # i pokazuje realne kroki bootu. boot_loading pozostaje wyłącznie
            # ekranem oczekiwania przed startem usługi.
            try:
                from .tarzanTspLksBootCheck import TarzanTspLksBootCheck

                # ETAP 1N: boot-check musi dostać aktywny HardwareBridge.
                # Inaczej startowa diagnostyka fizyczna idzie starą ścieżką,
                # próbuje drugi raz otwierać PoKeys i statusy USB/LCD/I2C/Matrix
                # nie przechodzą na starcie, choć klik punktowy działa.
                boot = TarzanTspLksBootCheck(
                    self.lks_n5,
                    pause_s=0.12,
                    hardware_bridge=getattr(self, "hw_bridge", None),
                )
                boot.run()
                self._lks_n5_status_page_ready = True
                self._lks_n5_status_cache = dict(getattr(boot, "statuses", {}) or {})

                # ETAP 1L: Snajper na miniPC jest tworzony przed startem LKS-N5
                # i subskrybuje SignalBus. Boot-check nie może czekać na późniejszy
                # klik operatora, żeby dopiero wtedy zazielenić snajper_sys.
                # Jeżeli runtime Snajpera istnieje, od razu pokazujemy status OK.
                snajper_ok = getattr(self, "snajper", None) is not None
                self._lks_n5_status_cache["snajper_sys"] = bool(snajper_ok)
                try:
                    self.lks_n5.set_status("snajper_sys", bool(snajper_ok))
                except Exception:
                    pass

                self._lks_n5_dirty = False
                self._lks_n5_dirty_reason = ""
            except Exception as boot_exc:
                # Błąd boot progress nie może zatrzymać TSP. Wtedy pokazujemy
                # minimalny Linux OK i pozwalamy pętli spokojnie przejąć status.
                self.debug.record_error("lks_n5_boot_progress_failed", {"error": str(boot_exc)})
                self.logger.warning("LKS-N5 boot progress failed: %s", boot_exc)
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

            # ETAP 1I: PAR/EHR nie są lokalnym sprzętem miniPC. Ich status na
            # LKS-N5 ma wynikać z realnego połączenia klienta TSP, a nie z
            # konserwatywnej diagnostyki repo/procesów, która nie widzi aplikacji
            # PAR uruchomionej na stacji operatorskiej. Dzięki temu kliknięcie
            # ikony PAR na Nextion 5 sprawdza prawdziwy stan LIVE: czy PAR jest
            # podłączony i heartbeat/ping przechodzi przez TSP.
            if name == "par_sys":
                ok = len(self.clients()) > 0
            else:
                bridge_components = {"pok_play", "pok_rec", "lcd_1602", "matrix_led", "f_button", "f_led", "keypad", "i2c_bus", "light_bh1750"}
                hw_bridge = getattr(self, "hw_bridge", None)
                if name in bridge_components and hw_bridge is not None and hasattr(hw_bridge, "test_lks_component"):
                    result = hw_bridge.test_lks_component(name, visible=True)
                    ok = bool(result.get("ok", False))
                    detail = str(result.get("detail", "") or result.get("error", ""))
                    if detail:
                        self.logger.info("LKS-N5 POINT TEST DETAIL component=%s %s", name, detail)
                else:
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


    def _read_poksyg_last_forced_status(self) -> Optional[Dict[str, Any]]:
        """Czyta trwały status ostatniego wymuszonego sygnału POKSYG z SignalBus."""
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            signal = bus.read("poksyg_last_forced_signal", "")
            if not signal:
                return None
            return {
                "signal": signal,
                "value": bus.read("poksyg_last_forced_value", ""),
                "ack_ok": bool(bus.read("poksyg_last_forced_ack_ok", 0)),
                "message": bus.read("poksyg_last_forced_message", ""),
            }
        except Exception:
            return None

    def _push_poksyg_last_forced_to_lks_n5(self) -> None:
        """Utrzymuje na LKS-N5 ostatni wymuszony sygnał, żeby ACK nie znikał po sekundzie."""
        if self.lks_n5 is None:
            return
        status = self._read_poksyg_last_forced_status()
        if not status:
            return
        try:
            self.lks_n5.set_poksyg_last_forced_status(
                str(status.get("signal", "")),
                status.get("value", ""),
                bool(status.get("ack_ok", False)),
                str(status.get("message", "")),
            )
            self._lks_n5_status_cache["pok_play"] = bool(status.get("ack_ok", False))
        except Exception as exc:
            self.debug.record_error("lks_n5_poksyg_last_forced_failed", {"error": str(exc)})

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

            _poksyg_last = self._read_poksyg_last_forced_status()
            _pok_play_status = bool(_poksyg_last.get("ack_ok")) if _poksyg_last else True

            desired_statuses: Dict[str, bool] = {
                "linux_sys": True,
                "snajper_sys": getattr(self, "snajper", None) is not None,
                "take_sys": True,
                "par_sys": client_count > 0,
                "ehr_sys": client_count > 0,
                "pok_play": _pok_play_status,
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

            self._push_poksyg_last_forced_to_lks_n5()

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
        # Upewniamy się, że multiprocessing używa 'spawn' na Linuxie dla izolacji libusb/PoKeys
        if platform.system().lower() != "windows":
            try:
                multiprocessing.set_start_method('spawn', force=True)
            except Exception:
                pass

        self._stopping = False
        self.running = True

        # ETAP 2: Centralny SignalBus + system_state = BOOTING
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            bus.set_input("system_state", "BOOTING", source="TSP_START")
            bus.set_input("runtime_state", "STARTING", source="TSP_START")
            bus.set_input("control_owner", "TSP_BOOT", source="TSP_START")
            bus.log("TSP", "TARZAN MAIN RUNTIME Starting...")
        except Exception as exc:
            self.logger.error("Could not init SignalBus in TarzanTspServer: %s", exc)

        # ETAP 5: Spięcie SignalBus z Hardware Bridge na miniPC (tor wykonawczy)
        try:
            from core.tarzanHardwareBridge import TarzanHardwareBridge
            self.hw_bridge = TarzanHardwareBridge(bus)
            self.hw_bridge.start()
            
            from core.tarzanSnajper import create_default_tarzan_snajper
            self.snajper = create_default_tarzan_snajper()
            # Na miniPC Snajper subskrybuje SignalBus i strzela do zarejestrowanych adapterów (hardware)
            bus.subscribe(lambda name, state: self.snajper.fire_from_signal(name, state.value))
            bus.log("TSP", "Hardware Bridge and Snajper connected to SignalBus on miniPC.")
        except Exception as e:
            self.logger.error("Could not init Hardware Bridge/Snajper on miniPC: %s", e)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(10)
        self._sock.settimeout(0.5)
        self.logger.info("TSP SERVER START host=%s port=%s node=%s", self.host, self.port, self.node_name)

        # ETAP 16: Forwarding logów z SignalBus do TSP
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            bus.subscribe_log(self._handle_bus_log)
        except Exception:
            pass

        self.lks.start()
        self._init_lks_n5()
        self._accept_thread = threading.Thread(target=self._accept_loop, name="TSP-ACCEPT", daemon=True)
        self._lane_thread = threading.Thread(target=self._lane_loop, name="TSP-LANES", daemon=True)
        self._accept_thread.start()
        self._lane_thread.start()

        # ETAP 2-3: Ustawienie statusów gotowości TCP dla PAR (BOOTING jest już widoczny)
        try:
            bus.set_input("tsp_state", "READY", source="TSP_START")
            bus.log("TSP", "TSP Server is now available for clients.")
        except Exception:
            pass

        # ETAP 3: Asynchroniczna diagnostyka LKS
        diag_thread = threading.Thread(target=self._run_diagnostics, name="TSP-DIAG", daemon=True)
        diag_thread.start()

        # Etap 12: Uruchomienie logiki trybów (MODE)
        try:
            from core.tarzanMode import start_mode_logic
            self._mode_logic = start_mode_logic()
            self.logger.info("Tarzan Mode Logic: STARTED")
        except Exception as e:
            self.logger.error("Tarzan Mode Logic: FAILED to start: %s", e)

        # ETAP 4: Sprawdzanie dostępności stacji PAR (asynchronicznie)
        par_thread = threading.Thread(target=self._check_par_availability, name="TSP-PAR-CHECK", daemon=True)
        par_thread.start()

    def _check_par_availability(self) -> None:
        """
        Asynchronicznie sprawdza, czy stacja PAR jest dostępna w sieci (Etap 4).
        """
        from .tarzanTspConfig import TSP_STACJA_HOST
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            bus.log("TSP", f"Checking PAR station availability at {TSP_STACJA_HOST}...")
            
            # Prosty test socketowy na port TSP (jeśli PAR też by go miał) 
            # lub po prostu ping (ale ping wymaga uprawnień lub subprocess).
            # Spróbujemy połączyć się z portem TSP na stacji (jeśli PAR nasłuchuje na komendy zwrotne)
            # ale PAR jest klientem. Więc może po prostu sprawdzić czy host żyje.
            
            import subprocess
            import platform
            
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", TSP_STACJA_HOST]
            
            res = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res == 0:
                bus.log("TSP", f"PAR station {TSP_STACJA_HOST} is ONLINE.")
                bus.set_input("par_state", "AVAILABLE", source="TSP_CHECK")
            else:
                bus.log("TSP", f"PAR station {TSP_STACJA_HOST} is OFFLINE or unreachable.")
                bus.set_input("par_state", "OFFLINE", source="TSP_CHECK")
                
        except Exception as exc:
            self.logger.debug("PAR check failed: %s", exc)

    def _run_diagnostics(self) -> None:
        """
        Asynchroniczna diagnostyka systemu (ETAP 3).
        Wypełnia SignalBus wynikami testów i ustawia READY_FOR_PAR.
        W pełni izolowana w osobnym procesie (spawn), aby crash libusb nie zabił serwera.
        """
        from core.tarzanSignalBus import get_signal_bus
        bus = get_signal_bus()
        
        try:
            bus.set_input("runtime_state", "TESTING", source="TSP_DIAG")
            bus.log("TSP", "Starting LKS Hardware Diagnostics (Isolated Spawn Process)...")

            # 1. Inwentaryzacja (bezpieczna, bez libPoKeys)
            inventory = TarzanTspLksInventory()
            inventory.collect()
            inventory_dict = inventory.to_dict()
            
            # 2. Diagnostyka szczegółowa (RISKY - running in SPAWNED process)
            # Używamy context 'spawn' dla pełnej separacji libusb
            diag_results = {}
            diag_crashed = False
            
            try:
                # Na Windowsie nie używamy spawn w ten sposób, bo to skomplikowane,
                # ale na miniPC (Linux) to kluczowe.
                if platform.system().lower() != "windows":
                    ctx = multiprocessing.get_context('spawn')
                    queue = ctx.Queue()
                    process = ctx.Process(
                        target=_diagnostics_worker,
                        args=(inventory_dict, queue),
                        name="TSP_Diag_Worker",
                        daemon=True
                    )
                    process.start()
                    
                    try:
                        msg = queue.get(timeout=45.0)
                        if isinstance(msg, dict) and msg.get("ok"):
                            diag_results = msg.get("results", {})
                        elif isinstance(msg, Exception):
                            self.logger.error("LKS Diagnostics Worker internal error: %s", msg)
                            diag_crashed = True
                        elif isinstance(msg, dict) and not msg.get("ok"):
                            self.logger.error("LKS Diagnostics Worker error: %s", msg.get("error"))
                            diag_crashed = True
                    except Exception:
                        if process.is_alive():
                            self.logger.warning("LKS Diagnostics Worker TIMEOUT - terminating.")
                            process.terminate()
                        else:
                            self.logger.error("LKS Diagnostics Worker CRASHED (libusb/PoKeys core-dump detected).")
                        diag_crashed = True
                    
                    process.join(timeout=2.0)
                    if process.is_alive(): process.kill()
                else:
                    # Windows / Dev mode - run inline or simple Thread if spawn is problematic
                    from core.TSP.tarzanTspLksDiagnostics import TarzanTspLksDiagnostics
                    diag = TarzanTspLksDiagnostics(collect_inventory_if_missing=False)
                    diag._inventory = inventory_dict
                    diag.run_all()
                    diag_results = diag.status_map()

            except Exception as exc:
                self.logger.error("LKS Diagnostics Process spawn failed: %s", exc)
                diag_crashed = True
            
            # 3. Publikacja wyników do SignalBus
            mapping = {
                "linux": "linux_ok",
                "tsp": "tsp_ok",
                "signalbus": "signalbus_ok",
                "snajper": "snajper_ok",
                "nextion5": "nextion5_ok",
                "pokeys": "pokeys_ok",
                "i2c_bus": "i2c_bus_ok",
                "lcd_1602": "lcd_1602_ok",
                "matrix_led": "matrix_led_ok",
                "f_led": "f_led_ok",
                "axis_inventory": "axis_inventory_ok"
            }
            
            for lks_key, sig_name in mapping.items():
                is_ok = diag_results.get(lks_key, False)
                if bus.exists(sig_name):
                    bus.set_input(sig_name, 1 if is_ok else 0, source="TSP_DIAG")
            
            # 4. Finalizacja stanu - zawsze dążymy do READY_FOR_PAR
            all_ok = all(diag_results.get(k, False) for k in ["linux", "tsp", "signalbus", "pokeys"])
            
            if all_ok and not diag_crashed:
                bus.set_input("hardware_state", "READY", source="TSP_DIAG")
                bus.log("TSP", "LKS Diagnostics: SUCCESS. Hardware READY.")
            else:
                bus.set_input("hardware_state", "ERROR" if diag_crashed else "PARTIAL_ERROR", source="TSP_DIAG")
                bus.log("TSP", f"LKS Diagnostics: COMPLETED with issues (Crashed={diag_crashed}).")

            # READY_FOR_PAR ustawiamy niezależnie od wyniku PoKeys
            bus.set_input("runtime_state", "READY_FOR_PAR", source="TSP_DIAG")
            bus.set_input("tarzan_ready", 1, source="TSP_DIAG")
            
            # Odświeżamy LKS-N5 (Etap 3)
            self.mark_lks_outputs_dirty("diag_finished", immediate_n5=True)

        except Exception as exc:
            self.logger.error("LKS Diagnostics CRASHED (outer): %s", exc)
            try:
                bus.set_input("runtime_state", "READY_FOR_PAR", source="TSP_DIAG")
                bus.set_input("tarzan_ready", 1, source="TSP_DIAG")
            except Exception: pass

    def _poll_system_commands(self) -> None:
        """Sprawdza i wykonuje komendy systemowe z SignalBus (Etap 8)."""
        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            
            # 1. Diagnostyka
            if bus.read("cmd_run_diagnostics", 0):
                bus.set_input("cmd_run_diagnostics", 0, source="TSP_SYSTEM") # Reset flagi
                diag_thread = threading.Thread(target=self._run_diagnostics, name="TSP-DIAG-MANUAL", daemon=True)
                diag_thread.start()
            
            # 2. Reboot (tylko na Linuxie)
            if bus.read("cmd_system_reboot", 0):
                bus.set_input("cmd_system_reboot", 0, source="TSP_SYSTEM")
                bus.log("TSP", "SYSTEM REBOOT INITIATED!")
                if platform.system().lower() != "windows":
                    os.system("sudo reboot")
                else:
                    self.logger.warning("REBOOT skipped (Windows Dev Mode)")

        except Exception as exc:
            self.logger.debug("System commands poll failed: %s", exc)

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
        if hasattr(self, "hw_bridge") and self.hw_bridge:
            self.hw_bridge.stop()
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
        
        # ETAP 4 i 9: Aktualizacja stanu klienta po rozłączeniu
        if client.node_name:
            try:
                from core.tarzanSignalBus import get_signal_bus
                bus = get_signal_bus()
                if "tarzanPAR" in client.node_name:
                    bus.set_input("par_state", "OFFLINE", source="TSP_DISCONNECT")
                elif "tarzanEHR" in client.node_name:
                    bus.set_input("ehr_state", "OFFLINE", source="TSP_DISCONNECT")
                elif "tarzanKHR" in client.node_name:
                    bus.set_input("khr_state", "OFFLINE", source="TSP_DISCONNECT")
            except Exception:
                pass

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
            node = payload.get("node", "unknown")
            client.node_name = node
            # ETAP 4 i 9: Rejestracja stanu klienta w SignalBus
            try:
                from core.tarzanSignalBus import get_signal_bus
                bus = get_signal_bus()
                if "tarzanPAR" in node:
                    bus.set_input("par_state", "CONNECTED", source="TSP_HELLO")
                    # PAR przejmuje kontrolę administracyjną
                    if bus.read("control_owner") in {"TSP_BOOT", "TSP_SERVICE"}:
                        bus.set_input("control_owner", "PAR_LIVE", source="TSP_HELLO")
                elif "tarzanEHR" in node:
                    bus.set_input("ehr_state", "CONNECTED", source="TSP_HELLO")
                elif "tarzanKHR" in node:
                    bus.set_input("khr_state", "CONNECTED", source="TSP_HELLO")
                bus.log("TSP", f"Client HELLO: {node}")
            except Exception:
                pass
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
            # Używamy node_name klienta jako źródła, jeśli jest dostępna
            source = client.node_name if client.node_name else f"client_{client.client_id}"
            result = self.provider.set_signal(name, payload.get("value"), source=source)
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

        if cmd == CMD_GET_STATE:
            # Etap 4: Zwracamy pełny stan runtime, liczbę klientów i statystyki
            return ok_response(
                cmd, 
                state=self.provider.state_summary(), 
                clients=len(self.clients()), 
                stats=self.debug.stats.as_dict()
            )

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

        if cmd == CMD_LOAD_TAKE:
            take_data = payload.get("take")
            if not take_data:
                return error_response(cmd, "missing_take_data")
            self._loaded_take = take_data
            self._take_playback_row_idx = 0
            self._take_playback_start_ms = 0
            self.logger.info("TAKE loaded from %s: duration=%s ms", client.name, take_data.get("duration_ms"))
            return ok_response(cmd, status="loaded")

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

            # ETAP 14: Obsługa playbacku TAKE na MiniPC
            self._handle_take_playback()

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
                
                # Etap 16: Publikacja FAST_STATS do SignalBus
                try:
                    from core.tarzanSignalBus import get_signal_bus
                    bus = get_signal_bus()
                    if bus.exists("tsp_fast_stats"):
                        bus.set_input("tsp_fast_stats", json.dumps(stats), source="TSP_STATS")
                except Exception:
                    pass

            # 4. LKS-N5 — spokojna praca:
            if not self._stopping and self.lks_n5 is not None:
                self._poll_lks_n5_events()
                if self._lks_n5_dirty:
                    self._refresh_lks_n5(reason=self._lks_n5_dirty_reason or "event", immediate=False)

            # 5. Komendy systemowe (ETAP 8)
            self._poll_system_commands()

            # 6. Traces
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

    def _handle_take_playback(self) -> None:
        """Pętla odtwarzania TAKE (ETAP 14)."""
        if not hasattr(self, "_loaded_take") or not self._loaded_take:
            return

        try:
            from core.tarzanSignalBus import get_signal_bus
            bus = get_signal_bus()
            
            # Pobieramy transport_state z SignalBus
            transport = str(bus.read("transport_state", "STOP")).upper()
            
            if transport == "STOP":
                if self._take_playback_start_ms > 0:
                    self._take_playback_start_ms = 0
                    self._take_playback_row_idx = 0
                    bus.log("TSP", "Playback STOPPED.")
                return

            if transport == "PAUSE":
                self._take_playback_start_ms = 0
                return

            if transport != "PLAY":
                return

            now = monotonic_ms()
            
            # Inicjalizacja startu przy przejściu STOP/PAUSE -> PLAY
            rows = self._loaded_take.get("rows", [])
            if self._take_playback_start_ms == 0:
                if self._take_playback_row_idx < len(rows):
                    current_row_time = int(rows[self._take_playback_row_idx].get("time_ms", 0))
                    self._take_playback_start_ms = now - current_row_time
                else:
                    self._take_playback_start_ms = now
                    self._take_playback_row_idx = 0
                bus.log("TSP", f"Playback START/RESUME: {self._loaded_take.get('name')} at row {self._take_playback_row_idx}")
            
            elapsed = now - self._take_playback_start_ms
            
            # Aplikujemy wiersze
            while self._take_playback_row_idx < len(rows):
                row = rows[self._take_playback_row_idx]
                row_time = int(row.get("time_ms", 0))
                
                if row_time <= elapsed:
                    for name, value in row.items():
                        if name != "time_ms" and bus.exists(name):
                            bus.force_signal(name, value, source="TSP_PLAYBACK")
                    self._take_playback_row_idx += 1
                else:
                    break
            
            if self._take_playback_row_idx >= len(rows):
                bus.force_signal("transport_state", "STOP", source="TSP_PLAYBACK")
                bus.log("TSP", "Playback FINISHED.")
                self._take_playback_start_ms = 0
                self._take_playback_row_idx = 0

        except Exception as e:
            self.logger.error("Playback loop error: %s", e)

    def broadcast_lane(self, lane: str, dt_ms: int, clients: Optional[list[TarzanTspClientSession]] = None) -> None:
        values = self.provider.get_lane_values(lane, None)
        if not values:
            return
        packet = snajper_packet(lane, values, dt_ms=dt_ms)
        self.broadcast(packet, lane=lane, clients=clients)

    def _handle_bus_log(self, source: str, message: str) -> None:
        """Forwarduje logi systemowe do klientów TSP (ETAP 16)."""
        if not self.running:
            return
        event = {
            "event": "log_event",
            "source": source,
            "message": message,
            "ts": now_ms()
        }
        self.broadcast(event, lane=LANE_URGENT)

        # ETAP 1V: prosta kontrolka LKS dla odpowiedzi POKSYG PLAY P37.
        # Bez nowej sekcji i bez rozbudowy HMI: używamy istniejącej kontrolki pok_play.
        try:
            if str(source).upper() == "POKSYG" and "PLAY P37" in str(message):
                ok = "ACK OK" in str(message)
                if self.lks_n5 is not None:
                    self.lks_n5.set_status("pok_play", ok)
                    self._lks_n5_status_cache["pok_play"] = ok
                    self._push_poksyg_last_forced_to_lks_n5()
        except Exception:
            pass

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
