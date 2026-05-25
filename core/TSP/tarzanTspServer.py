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
    ok_response,
    snajper_packet,
)
from .tarzanTspSignals import TarzanTspSignalProvider


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
                        self.server.debug.rx.append({"ts": monotonic_ms(), "client": self.name, "message": message})
                        response = self.server.handle_message(self, message)
                    except TspProtocolError as exc:
                        self.server.debug.record_error("protocol_error", {"client": self.name, "error": str(exc)})
                        response = error_response("unknown", "protocol_error", detail=str(exc))
                    except Exception as exc:  # bezpieczeństwo serwera
                        self.server.debug.record_error("handler_error", {"client": self.name, "error": str(exc)})
                        response = error_response("unknown", "handler_error", detail=str(exc))
                    if response is not None:
                        self.send(response)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as exc:
                self.server.debug.record_error("rx_loop_error", {"client": self.name, "error": str(exc)})
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
    ) -> None:
        self.host = host
        self.port = port
        self.node_name = node_name
        self.provider = provider or TarzanTspSignalProvider(node_name=node_name)
        self.debug = TarzanTspDebug()
        self.logger = setup_tsp_logger("TSP.SERVER")
        self.running = False
        self._sock: Optional[socket.socket] = None
        self._clients: Dict[int, TarzanTspClientSession] = {}
        self._clients_lock = threading.Lock()
        self._next_client_id = 1
        self._accept_thread: Optional[threading.Thread] = None
        self._lane_thread: Optional[threading.Thread] = None
        self._last_stats_ms = monotonic_ms()

    # ------------------------------------------------------------------
    # START / STOP
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(10)
        self._sock.settimeout(0.5)
        self.logger.info("TSP SERVER START host=%s port=%s node=%s", self.host, self.port, self.node_name)
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
        self.running = False
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
        last_fast = last_normal = last_slow = last_health = monotonic_ms()
        while self.running:
            now = monotonic_ms()
            clients = self.clients()
            self.provider.tick(client_count=len(clients))

            urgent_items = self.provider.pop_urgent_events()
            for item in urgent_items:
                self.broadcast(item, lane=LANE_URGENT, immediate=True)

            if now - last_fast >= TSP_FAST_INTERVAL_MS:
                last_fast = now
                self.broadcast_lane(LANE_FAST, TSP_FAST_INTERVAL_MS)

            if now - last_normal >= TSP_NORMAL_INTERVAL_MS:
                last_normal = now
                self.broadcast_lane(LANE_NORMAL, TSP_NORMAL_INTERVAL_MS)

            if now - last_slow >= TSP_SLOW_INTERVAL_MS:
                last_slow = now
                self.broadcast_lane(LANE_SLOW, TSP_SLOW_INTERVAL_MS)

            if now - last_health >= TSP_HEALTH_INTERVAL_MS:
                last_health = now
                health = health_packet(
                    node=self.node_name,
                    clients=len(clients),
                    stats=self.debug.stats.as_dict(),
                    state=self.provider.state_summary(),
                )
                self.broadcast(health, lane=LANE_HEALTH)

            if now - self._last_stats_ms >= TSP_STATS_LOG_INTERVAL_MS:
                self._last_stats_ms = now
                stats = self.debug.stats.as_dict()
                self.logger.info(
                    "TSP_STATS clients=%s tx=%s rx=%s errors=%s dropped=%s lanes=%s",
                    len(clients), stats["packets_tx"], stats["packets_rx"], stats["errors"], stats["dropped"], stats["lane_packets"],
                )

            self._emit_traces()
            time.sleep(0.001)

    def broadcast_lane(self, lane: str, dt_ms: int) -> None:
        values = self.provider.get_lane_values(lane, None)
        if not values:
            return
        packet = snajper_packet(lane, values, dt_ms=dt_ms)
        self.broadcast(packet, lane=lane)

    def broadcast(self, message: Dict[str, Any], lane: str, immediate: bool = False) -> None:
        for client in self.clients():
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

    def _emit_traces(self) -> None:
        now = monotonic_ms()
        for client in self.clients():
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
    args = parser.parse_args()

    server = TarzanTspServer(host=args.host, port=args.port, node_name=args.node)
    server.serve_forever()


if __name__ == "__main__":
    main()
