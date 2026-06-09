from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None

from .protocol import command_bytes

TERMINATOR = b"\xff\xff\xff"


@dataclass
class NextionEvent:
    raw: bytes
    timestamp: float = field(default_factory=time.time)


class TarzanNextionDevice:
    def __init__(self, name: str, port: str, baudrate: int = 115200) -> None:
        self.name = name
        self.port = port
        self.baudrate = int(baudrate)
        self.serial_port = None
        self.read_buffer = bytearray()
        self.events: List[NextionEvent] = []
        self.last_error: Optional[str] = None
        self.connected = False
        self.handshake_ok = False
        self.last_handshake: str = ""

    def open(self) -> bool:
        if self.serial_port is not None:
            return True
        if serial is None:
            self.last_error = "Brak pakietu pyserial"
            return False
        try:
            self.serial_port = serial.Serial(self.port, self.baudrate, timeout=0.05, write_timeout=0.2)
            # Jak w Nextion 5: samo otwarcie portu oznacza aktywny transport.
            # comok/handshake to diagnostyka, a nie warunek działania RX.
            self.last_error = None
            self.connected = True
            self.handshake_ok = False
            self.last_handshake = ""
            return True
        except Exception as exc:
            self.serial_port = None
            self.connected = False
            self.handshake_ok = False
            self.last_error = str(exc)
            return False

    def close(self) -> None:
        if self.serial_port is not None:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None
        self.connected = False
        self.handshake_ok = False

    def clear_rx(self) -> None:
        self.read_buffer.clear()
        if self.serial_port is not None:
            try:
                self.serial_port.reset_input_buffer()
            except Exception:
                pass

    def send_raw(self, payload: bytes) -> bool:
        if self.serial_port is None and not self.open():
            return False
        try:
            assert self.serial_port is not None
            self.serial_port.write(payload)
            try:
                self.serial_port.flush()
            except Exception:
                pass
            self.connected = True
            return True
        except Exception as exc:
            self.last_error = str(exc)
            self.close()
            return False

    def send_command(self, command: str) -> bool:
        return self.send_raw(command_bytes(command))

    def _drain_packets(self) -> List[NextionEvent]:
        out: List[NextionEvent] = []
        while TERMINATOR in self.read_buffer:
            idx = self.read_buffer.index(TERMINATOR)
            packet = bytes(self.read_buffer[:idx])
            del self.read_buffer[: idx + len(TERMINATOR)]
            if packet:
                out.append(NextionEvent(packet))
        # Ochrona przed śmieciami na RX bez terminatora. Nie wolno dopuścić,
        # żeby szum UART zjadał CPU i pamięć. Zostawiamy końcówkę bufora,
        # bo terminator może przyjść w następnym odczycie.
        if len(self.read_buffer) > 2048:
            del self.read_buffer[:-256]
        if out:
            self.events.extend(out)
            self.events = self.events[-50:]
        return out

    def poll(self) -> List[NextionEvent]:
        if self.serial_port is None:
            return []

        try:
            waiting = int(getattr(self.serial_port, "in_waiting", 0) or 0)
            if waiting > 0:
                self.read_buffer.extend(self.serial_port.read(waiting))
        except Exception as exc:
            self.last_error = f"Błąd odczytu: {exc}"
            self.close()
            return []

        return self._drain_packets()

    def poll_blocking(self, timeout_s: float = 0.25) -> List[NextionEvent]:
        """Blokujący odczyt RX dla lokalnego HMI.

        To nie jest nowe odświeżanie UI. To odpowiednik spokojnego czekania
        na UART: wątek śpi w serial.read(), a Snajper nadal decyduje o wysyłce
        zmian na ekran.
        """
        if self.serial_port is None:
            return []
        deadline = time.monotonic() + max(0.02, float(timeout_s or 0.25))
        while time.monotonic() < deadline:
            try:
                chunk = self.serial_port.read(1)
                if chunk:
                    self.read_buffer.extend(chunk)
                    waiting = int(getattr(self.serial_port, "in_waiting", 0) or 0)
                    if waiting > 0:
                        self.read_buffer.extend(self.serial_port.read(waiting))
                    out = self._drain_packets()
                    if out:
                        return out
                # Jeśli read(1) wrócił pusty (timeout portu), to kontynuujemy pętlę do deadline.
                # Nie wracamy przedwcześnie, żeby nie obciążać pętli nadrzędnej (CPU).
            except Exception as exc:
                self.last_error = f"Błąd odczytu blokującego: {exc}"
                self.close()
                return []
        return self._drain_packets()

    def handshake(self, wait_ms: int = 100) -> bool:
        if self.serial_port is None and not self.open():
            return False
        self.clear_rx()
        if not self.send_command("connect"):
            return False

        # Nextion może odpowiedzieć po chwili, a nie zawsze odsyła comok przy
        # każdej konfiguracji HMI. Portu nie zamykamy i nie uznajemy za martwy
        # tylko dlatego, że comok nie wrócił.
        deadline = time.time() + max(0.02, wait_ms / 1000.0)
        while time.time() < deadline:
            try:
                if self.serial_port and self.serial_port.in_waiting:
                    self.read_buffer.extend(self.serial_port.read(self.serial_port.in_waiting))
            except Exception as exc:
                self.last_error = f"Błąd handshake: {exc}"
                return False
            events = self.poll()
            for ev in events:
                if ev.raw.startswith(b"comok"):
                    try:
                        self.last_handshake = ev.raw.decode("ascii", errors="replace")
                    except Exception:
                        self.last_handshake = repr(ev.raw)
                    self.connected = True
                    self.handshake_ok = True
                    self.last_error = None
                    return True
            time.sleep(0.01)

        self.connected = bool(self.serial_port is not None)
        self.handshake_ok = False
        self.last_error = self.last_error or f"Port otwarty; brak comok w {wait_ms} ms"
        return False
