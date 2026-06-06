"""
LKS — Lampka Kontrolna Systemu dla tarzanMiniPC.

To nie jest UI i nie jest PAR. To lekka tekstowa wizualizacja TTY,
pokazująca czy TSP żyje, czy tarzanStacja jest połączona oraz jakie
ostatnie ramki RX/TX/URGENT/HEALTH przeszły przez protokół.

Zasada pracy:
- odświeżanie maksymalnie co ok. 1 s,
- natychmiastowe odświeżenie tylko po ważnym zdarzeniu,
- bez parsowania journalctl,
- bez zapisu pakietów na dysk,
- tylko odczyt stanu TSP z RAM.
"""

from __future__ import annotations

import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class TarzanTspLks:
    """Lekki monitor tekstowy TSP na lokalnym TTY mini PC."""

    def __init__(
        self,
        server: Any,
        tty_path: str = "/dev/tty1",
        refresh_interval_s: float = 1.0,
        enabled: bool = True,
    ) -> None:
        self.server = server
        self.tty_path = tty_path
        self.refresh_interval_s = max(0.25, float(refresh_interval_s))
        self.enabled = bool(enabled)
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._event = threading.Event()
        self._last_render_monotonic = 0.0
        self._last_reason = "start"
        self._screen_initialized = False
        self._last_lines: list[str] = []

    def start(self) -> None:
        if not self.enabled or self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, name="TSP-LKS", daemon=True)
        self._thread.start()
        self.mark_dirty("start")

    def stop(self) -> None:
        self.running = False
        self._event.set()
        self._show_cursor_safe()

    def mark_dirty(self, reason: str = "event") -> None:
        """Zgłasza ważne zdarzenie do szybszego odświeżenia ekranu.

        FAST nie powinien wywoływać natychmiastowego redraw. Monitor i tak
        pokaże jego aktualny stan w cyklu 1 s, bez mielenia CPU.
        """
        if not self.enabled:
            return
        self._last_reason = str(reason or "event")
        self._event.set()

    def _loop(self) -> None:
        while self.running:
            self._event.wait(self.refresh_interval_s)
            self._event.clear()
            now = time.monotonic()
            if now - self._last_render_monotonic < 0.20:
                continue
            self._last_render_monotonic = now
            try:
                self.render()
            except Exception:
                # LKS nie może wpływać na TSP. Każdy błąd ekranu ignorujemy.
                pass

    def render(self) -> None:
        text = self.build_screen()
        if self.tty_path == "-":
            print(text, flush=True)
            return

        path = Path(self.tty_path)
        if not path.exists():
            return

        # Bez migania: NIE czyścimy całego ekranu przy każdym odświeżeniu.
        # Pierwszy render robi tylko jednorazowe czyszczenie, kolejne rendery
        # nadpisują zmienione linie w miejscu. Dzięki temu LKS zachowuje się
        # jak delikatna lampka kontrolna, a nie migający ekran logów.
        lines = text.splitlines()
        with path.open("w", encoding="utf-8", errors="replace") as f:
            if not self._screen_initialized:
                f.write("\033[?25l")      # hide cursor
                f.write("\033[2J\033[H")  # one-time clear + home
                self._screen_initialized = True
                self._last_lines = []

            max_lines = max(len(lines), len(self._last_lines))
            for idx in range(max_lines):
                new_line = lines[idx] if idx < len(lines) else ""
                old_line = self._last_lines[idx] if idx < len(self._last_lines) else None
                if new_line == old_line:
                    continue
                f.write(f"\033[{idx + 1};1H")
                f.write(new_line)
                f.write("\033[K")  # clear to end of line only

            f.flush()
        self._last_lines = lines

    def _show_cursor_safe(self) -> None:
        if self.tty_path == "-":
            return
        try:
            path = Path(self.tty_path)
            if path.exists():
                with path.open("w", encoding="utf-8", errors="replace") as f:
                    f.write("\033[?25h")
                    f.flush()
        except Exception:
            pass

    def build_screen(self) -> str:
        snapshot = self.server.debug.snapshot()
        stats = snapshot.get("stats", {})
        clients = self._clients_snapshot()
        columns = shutil.get_terminal_size((100, 30)).columns
        width = max(80, min(120, columns))
        line = "─" * width
        now_txt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = [
            "TARZAN LKS — LAMPKA KONTROLNA SYSTEMU"[:width],
            line,
            f"NODE: {self.server.node_name}   TSP: RUNNING {self.server.host}:{self.server.port}   TIME: {now_txt}",
            f"CLIENTS: {len(clients)}   RX: {stats.get('packets_rx', 0)}   TX: {stats.get('packets_tx', 0)}   ERR: {stats.get('errors', 0)}   DROP: {stats.get('dropped', 0)}",
            f"LAST: {self._last_reason}",
            self._format_poksyg_last_forced(),
        ]

        if clients:
            header.append("CLIENT: " + ", ".join(clients[:3]))
        else:
            header.append("CLIENT: brak połączenia tarzanStacja")

        lanes = stats.get("lane_packets") or {}
        if lanes:
            header.append("LANES: " + self._compact_dict(lanes, max_items=8))

        body = [
            line,
            "RX — ostatnie komendy przychodzące:",
            *self._format_ring(snapshot.get("rx", []), direction="<-", limit=6),
            line,
            "TX — ostatnie sygnały/ramki wychodzące:",
            *self._format_ring(snapshot.get("tx", []), direction="->", limit=6),
            line,
            "ERROR — ostatnie błędy:",
            *self._format_errors(snapshot.get("errors", []), limit=3),
            line,
            "LKS: tylko podgląd | odświeżanie 1 s albo ważne zdarzenie | bez UI/PAR/sterowania",
        ]

        return "\n".join(self._clip(row, width) for row in [*header, *body]) + "\n"

    def _format_poksyg_last_forced(self) -> str:
        """Jedna trwała linia statusu POKSYG dla LKS-TTY.

        Korzysta z istniejących statusów SignalBus przez metodę serwera.
        Nie odpytuje sprzętu i nie uruchamia diagnostyki w pętli.
        """
        try:
            reader = getattr(self.server, "_read_poksyg_last_forced_status", None)
            status = reader() if callable(reader) else None
        except Exception:
            status = None
        if not status:
            return "POKSYG: brak ostatniego ACK"

        signal = str(status.get("signal", "")).strip()
        value = str(status.get("value", "")).strip()
        ack_txt = "ACK OK" if bool(status.get("ack_ok", False)) else "ACK ERROR"
        if signal == "play_p37_step_disconnect_manual":
            return f"POKSYG: PLAY P37={value} {ack_txt}"
        short_signal = signal or "UNKNOWN"
        return f"POKSYG: {short_signal}={value} {ack_txt}"

    def _clients_snapshot(self) -> list[str]:
        try:
            return [f"{c.address[0]}:{c.address[1]}" for c in self.server.clients()]
        except Exception:
            return []

    def _format_ring(self, items: Iterable[Dict[str, Any]], direction: str, limit: int) -> list[str]:
        rows: list[str] = []
        all_items = list(items)

        # Ring RX ma czasem parę: RAW + zdekodowana komenda.
        # LKS pokazuje przede wszystkim formę zdekodowaną, żeby ekran był czytelny.
        decoded = [
            item for item in all_items
            if not (isinstance(item.get("message"), dict) and "raw" in item.get("message", {}))
        ]
        source = decoded if decoded else all_items

        if direction == "->":
            source = self._thin_tx_items(source, limit)
        else:
            source = source[-limit:]

        for item in source:
            rows.append(self._format_event_item(item, direction))
        if not rows:
            rows.append("  —")
        return rows[-limit:]

    def _thin_tx_items(self, items: list[Dict[str, Any]], limit: int) -> list[Dict[str, Any]]:
        """Czytelny wybór TX: nie zalewamy LKS samymi pakietami FAST."""
        selected_rev: list[Dict[str, Any]] = []
        fast_seen = 0
        health_seen = 0
        normal_seen = 0

        for item in reversed(items):
            message = item.get("message") or {}
            if not isinstance(message, dict):
                selected_rev.append(item)
            else:
                lane = str(message.get("lane") or "").lower()
                event = str(message.get("event") or "").lower()
                if lane == "fast" and event == "snajper_packet":
                    if fast_seen >= 2:
                        continue
                    fast_seen += 1
                elif lane == "health":
                    if health_seen >= 1:
                        continue
                    health_seen += 1
                elif lane == "normal":
                    if normal_seen >= 2:
                        continue
                    normal_seen += 1
                selected_rev.append(item)

            if len(selected_rev) >= limit:
                break

        return list(reversed(selected_rev))

    def _format_errors(self, items: Iterable[Dict[str, Any]], limit: int) -> list[str]:
        rows: list[str] = []
        for item in list(items)[-limit:]:
            ts = self._time_from_ms(item.get("ts"))
            error = item.get("error", "error")
            context = item.get("context") or {}
            rows.append(f"{ts} !! {error} {self._compact_dict(context, max_items=3) if context else ''}".rstrip())
        if not rows:
            rows.append("  brak")
        return rows[-limit:]

    def _format_event_item(self, item: Dict[str, Any], direction: str) -> str:
        ts = self._time_from_ms(item.get("ts"))
        client = item.get("client")
        message = item.get("message") or {}
        if isinstance(message, dict) and "raw" in message:
            raw = str(message.get("raw", "")).strip()
            return f"{ts} {direction} RAW {raw[:90]}"
        if not isinstance(message, dict):
            return f"{ts} {direction} {message}"

        if message.get("event") == "snajper_packet":
            lane = message.get("lane", "?")
            values = message.get("values") or {}
            sample = self._compact_dict(values, max_items=4) if isinstance(values, dict) else str(values)
            return f"{ts} {direction} {lane.upper()} {sample}"

        if message.get("event") == "urgent":
            return f"{ts} {direction} URGENT {message.get('name')}={message.get('value')} reason={message.get('reason')}"

        if message.get("event") == "health":
            stats = message.get("stats") or {}
            return f"{ts} {direction} HEALTH clients={message.get('clients')} err={stats.get('errors', 0)} drop={stats.get('dropped', 0)}"

        cmd = message.get("cmd")
        ok = message.get("ok")
        if cmd:
            suffix = self._command_suffix(message)
            prefix = f"{ts} {direction} {cmd}"
            if ok is not None:
                prefix += f" ok={ok}"
            if client:
                prefix += f" [{client}]"
            return (prefix + suffix).rstrip()

        lane = message.get("lane") or message.get("event") or "MSG"
        return f"{ts} {direction} {lane} {self._compact_dict(message, max_items=5)}"

    def _command_suffix(self, message: Dict[str, Any]) -> str:
        parts = []
        for key in ("name", "value", "lane", "lanes", "signals", "path", "error"):
            if key in message:
                parts.append(f"{key}={message.get(key)}")
        return " " + " ".join(parts) if parts else ""

    def _compact_dict(self, data: Dict[str, Any], max_items: int = 4) -> str:
        if not data:
            return "{}"
        parts = []
        for idx, (key, value) in enumerate(data.items()):
            if idx >= max_items:
                parts.append("…")
                break
            parts.append(f"{key}={value}")
        return "{" + ", ".join(parts) + "}"

    def _time_from_ms(self, value: Any) -> str:
        try:
            ts = int(value) / 1000.0
            return datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        except Exception:
            return "--:--:--"

    def _clip(self, text: str, width: int) -> str:
        if len(text) <= width:
            return text
        return text[: max(0, width - 1)] + "…"
