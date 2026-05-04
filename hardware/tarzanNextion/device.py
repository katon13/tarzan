from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None

from .protocol import command_bytes


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

    def open(self) -> bool:
        if self.connected:
            return True
        if serial is None:
            self.last_error = "Brak pakietu pyserial"
            return False
        try:
            self.serial_port = serial.Serial(self.port, self.baudrate, timeout=0, write_timeout=0)
            self.connected = True
            self.last_error = None
            return True
        except Exception as exc:
            self.serial_port = None
            self.connected = False
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

    def send_raw(self, payload: bytes) -> bool:
        if not self.connected and not self.open():
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
        if not self.connected or self.serial_port is None:
            return []
        try:
            waiting = int(getattr(self.serial_port, "in_waiting", 0) or 0)
            if waiting:
                self.read_buffer.extend(self.serial_port.read(waiting))
        except Exception as exc:
            self.last_error = str(exc)
            self.close()
            return []

        out: List[NextionEvent] = []
        terminator = b"\xff\xff\xff"
        while terminator in self.read_buffer:
            idx = self.read_buffer.index(terminator)
            packet = bytes(self.read_buffer[:idx])
            del self.read_buffer[: idx + len(terminator)]
            ev = NextionEvent(packet)
            out.append(ev)
        if out:
            self.events.extend(out)
            self.events = self.events[-50:]
        return out
