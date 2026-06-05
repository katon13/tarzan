"""
Klient TSP — TARZAN Signal Protocol.

Docelowy klient TCP/JSONL dla tarzanStacja / PAR / EHR.
Może pracować interaktywnie albo wykonać szybki smoke run.
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, Optional

from .tarzanTspConfig import TSP_MINI_PC_HOST, TSP_PORT
from .tarzanTspProtocol import (
    CMD_CALL_ACTION,
    CMD_GET_SIGNAL,
    CMD_GET_SIGNAL_CATALOG,
    CMD_GET_STATE,
    CMD_HELLO,
    CMD_PING,
    CMD_SET_SIGNAL,
    CMD_SUBSCRIBE,
    CMD_TRACE_SIGNAL,
    decode_jsonl_line,
    encode_jsonl,
    now_ms,
)


class TarzanTspClient:
    def __init__(self, host: str = TSP_MINI_PC_HOST, port: int = TSP_PORT, name: str = "tarzanStacja") -> None:
        self.host = host
        self.port = port
        self.name = name
        self.sock: Optional[socket.socket] = None
        self.running = False
        self._rx_thread: Optional[threading.Thread] = None
        self._send_lock = threading.Lock()
        self.messages: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self.on_message: Optional[Callable[[Dict[str, Any]], None]] = None
        self.rx_count = 0
        self.tx_count = 0
        self.urgent_count = 0
        self.fast_count = 0
        self.normal_count = 0
        self.slow_count = 0
        self.health_count = 0

    # ------------------------------------------------------------------
    # START / STOP
    # ------------------------------------------------------------------

    def connect(self, timeout: float = 5.0) -> None:
        if self.running:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((self.host, self.port))
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(0.5)
        self.sock = sock
        self.running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, name="TSP-CLIENT-RX", daemon=True)
        self._rx_thread.start()

    def close(self) -> None:
        self.running = False
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    # ------------------------------------------------------------------
    # KOMENDY
    # ------------------------------------------------------------------

    def send(self, message: Dict[str, Any]) -> None:
        if self.sock is None:
            raise RuntimeError("TSP client is not connected")
        raw = encode_jsonl(message)
        with self._send_lock:
            self.sock.sendall(raw)
        self.tx_count += 1

    def hello(self) -> None:
        self.send({"cmd": CMD_HELLO, "node": self.name, "version": "1"})

    def ping(self) -> None:
        self.send({"cmd": CMD_PING, "ts": now_ms()})

    def subscribe(self, lanes: list[str] | None = None, signals: list[str] | None = None) -> None:
        self.send({"cmd": CMD_SUBSCRIBE, "lanes": lanes or ["fast", "normal", "slow", "health", "urgent"], "signals": signals or ["*"]})

    def get_catalog(self) -> None:
        self.send({"cmd": CMD_GET_SIGNAL_CATALOG})

    def get_state(self) -> None:
        self.send({"cmd": CMD_GET_STATE})

    def get_signal(self, name: str) -> None:
        self.send({"cmd": CMD_GET_SIGNAL, "name": name})

    def set_signal(self, name: str, value: Any) -> None:
        self.send({"cmd": CMD_SET_SIGNAL, "name": name, "value": value})

    def call_action(self, name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.send({"cmd": CMD_CALL_ACTION, "name": name, "payload": payload or {}})

    def trace_signal(self, name: str, seconds: int = 5) -> None:
        self.send({"cmd": CMD_TRACE_SIGNAL, "name": name, "seconds": seconds})

    # ------------------------------------------------------------------
    # RX
    # ------------------------------------------------------------------

    def _rx_loop(self) -> None:
        assert self.sock is not None
        buffer = b""
        while self.running:
            try:
                chunk = self.sock.recv(8192)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    message = decode_jsonl_line(line)
                    self._record_message(message)
                    if self.on_message:
                        self.on_message(message)
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as exc:
                self._record_message({"ok": False, "event": "client_error", "error": str(exc)})
        self.running = False

    def _record_message(self, message: Dict[str, Any]) -> None:
        self.rx_count += 1
        lane = message.get("lane")
        event = message.get("event")
        if lane == "fast":
            self.fast_count += 1
        elif lane == "normal":
            self.normal_count += 1
        elif lane == "slow":
            self.slow_count += 1
        elif lane == "health":
            self.health_count += 1
        if event == "urgent" or lane == "urgent":
            self.urgent_count += 1
        self.messages.append(message)

    def wait_for(self, predicate: Callable[[Dict[str, Any]], bool], timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        end = time.monotonic() + timeout
        checked = 0
        while time.monotonic() < end:
            items = list(self.messages)
            for item in items[checked:]:
                if predicate(item):
                    return item
            checked = len(items)
            time.sleep(0.01)
        return None

    def stats(self) -> Dict[str, Any]:
        return {
            "rx": self.rx_count,
            "tx": self.tx_count,
            "urgent": self.urgent_count,
            "fast": self.fast_count,
            "normal": self.normal_count,
            "slow": self.slow_count,
            "health": self.health_count,
        }


def run_smoke(host: str, port: int, seconds: float = 1.5) -> int:
    client = TarzanTspClient(host=host, port=port)
    client.connect()
    try:
        client.hello()
        client.ping()
        client.subscribe()
        client.get_catalog()
        client.set_signal("transport_state", "PLAY")
        client.set_signal("nextion_page", "rrp_main")
        client.call_action("clap")
        client.trace_signal("rrp_p1_value", seconds=1)
        time.sleep(seconds)
        client.set_signal("transport_state", "STOP")
        time.sleep(0.2)
        stats = client.stats()
        print("TSP CLIENT SMOKE OK", stats)
        if stats["fast"] <= 0 or stats["urgent"] <= 0:
            print("TSP CLIENT SMOKE FAIL: missing fast or urgent packets", file=sys.stderr)
            return 2
        return 0
    finally:
        client.close()


def run_interactive(host: str, port: int) -> None:
    client = TarzanTspClient(host=host, port=port)

    def show(message: Dict[str, Any]) -> None:
        event = message.get("event")
        lane = message.get("lane")
        if event == "snajper_packet" and lane == "fast":
            values = message.get("values") or {}
            print(f"FAST values={len(values)} sample_rrp={values.get('rrp_p1_value')}")
        else:
            print(message)

    client.on_message = show
    client.connect()
    client.hello()
    client.subscribe()
    client.ping()
    print("TSP CLIENT CONNECTED. Komendy: play, stop, clap, page <name>, catalog, state, trace <signal>, quit")
    try:
        while True:
            cmd = input("TSP> ").strip()
            if cmd in {"quit", "exit", "q"}:
                break
            if cmd == "play":
                client.set_signal("transport_state", "PLAY")
            elif cmd == "stop":
                client.set_signal("transport_state", "STOP")
            elif cmd == "clap":
                client.call_action("clap")
            elif cmd.startswith("page "):
                client.set_signal("nextion_page", cmd.split(" ", 1)[1].strip())
            elif cmd == "catalog":
                client.get_catalog()
            elif cmd == "state":
                client.get_state()
            elif cmd.startswith("trace "):
                client.trace_signal(cmd.split(" ", 1)[1].strip(), seconds=10)
            elif cmd.startswith("get "):
                client.get_signal(cmd.split(" ", 1)[1].strip())
            else:
                print("Nieznana komenda")
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="TARZAN TSP Client")
    parser.add_argument("--host", default=TSP_MINI_PC_HOST)
    parser.add_argument("--port", type=int, default=TSP_PORT)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seconds", type=float, default=1.5)
    args = parser.parse_args()

    if args.smoke:
        raise SystemExit(run_smoke(args.host, args.port, args.seconds))
    run_interactive(args.host, args.port)


if __name__ == "__main__":
    main()
