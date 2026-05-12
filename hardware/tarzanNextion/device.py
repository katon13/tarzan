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
            self.last_error = None
            self.connected = False
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
            return True
        except Exception as exc:
            self.last_error = str(exc)
            self.close()
            return False

    def send_command(self, command: str) -> bool:
        return self.send_raw(command_bytes(command))

    def poll(self) -> List[NextionEvent]:
        if self.serial_port is None:
            return []
        
        # Czytamy dostępne dane z portu
        try:
            if self.serial_port.in_waiting > 0:
                self.read_buffer.extend(self.serial_port.read(self.serial_port.in_waiting))
        except Exception as exc:
            self.last_error = f"Błąd odczytu: {exc}"
            self.close()
            return []

        out: List[NextionEvent] = []
        
        # Szukamy pakietów w buforze
        while True:
            # 1. Standardowy terminator Nextion
            if TERMINATOR in self.read_buffer:
                idx = self.read_buffer.index(TERMINATOR)
                packet = bytes(self.read_buffer[:idx])
                del self.read_buffer[: idx + len(TERMINATOR)]
                out.append(NextionEvent(packet))
                continue
            

            break

        if out:
            self.events.extend(out)
            self.events = self.events[-50:]
        return out

    def handshake(self, wait_ms: int = 100) -> bool:
        if self.serial_port is None and not self.open():
            return False
        self.clear_rx()
        if not self.send_command("connect"):
            return False
        time.sleep(max(0.01, wait_ms / 1000.0))
        # Czytamy wszystko co przyszło
        if self.serial_port and self.serial_port.in_waiting:
            self.read_buffer.extend(self.serial_port.read(self.serial_port.in_waiting))
        
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
        self.connected = False
        self.handshake_ok = False
        self.last_error = self.last_error or f"Brak odpowiedzi na connect w {wait_ms} ms"
        return False
