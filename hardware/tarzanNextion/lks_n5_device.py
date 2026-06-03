from __future__ import annotations

"""LKS-N5 / Nextion 5 low-level serial device.

Ten moduł jest najniższą warstwą komunikacji miniPC -> Nextion 5.
Nie robi diagnostyki sprzętu i nie steruje ruchem. Wysyła wyłącznie
bezpieczne komendy Nextion Instruction Set zakończone FF FF FF.

Uruchomienie testu ręcznego na miniPC:

    python3 -m hardware.tarzanNextion.lks_n5_device \
        --port /dev/serial/by-id/TARZAN_NEXTION5 \
        --test

Test suchy bez portu:

    python3 -m hardware.tarzanNextion.lks_n5_device --dry-run --test
"""

import argparse
import sys
import time
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover - miniPC ma mieć pyserial; repo ma się importować także bez niego.
    serial = None  # type: ignore

TERMINATOR = b"\xff\xff\xff"
DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT = 0.2


@dataclass
class LksN5Event:
    """Pojedynczy pakiet odebrany z Nextion 5."""

    raw: bytes
    timestamp: float = field(default_factory=time.time)

    @property
    def text(self) -> str:
        return self.raw.decode("ascii", errors="replace")


class TarzanLksN5Device:
    """Niski poziom komunikacji z Nextion 5 dla LKS-N5.

    Odpowiedzialność tej klasy:
    - otwarcie i zamknięcie portu serial,
    - wysłanie komendy z terminatorem FF FF FF,
    - proste helpery: page/txt/val/vis/bkcmd,
    - odczyt eventów serwisowych z Nextiona,
    - przechowywanie last_tx/last_rx/last_error.

    Ta klasa celowo nie zna TSP, PAR, EHR, Snajpera ani diagnostyki hardware.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        write_timeout: float = 0.5,
        dry_run: bool = False,
        encoding: str = "ascii",
    ) -> None:
        self.port = str(port or "")
        self.baudrate = int(baudrate)
        self.timeout = float(timeout)
        self.write_timeout = float(write_timeout)
        self.dry_run = bool(dry_run)
        self.encoding = encoding

        self.serial_port = None
        self.read_buffer = bytearray()
        self.events: List[LksN5Event] = []
        self.tx_history: List[str] = []

        self.last_tx: str = ""
        self.last_rx: bytes = b""
        self.last_error: str = ""
        self.connected: bool = False

    def connect(self) -> None:
        """Otwiera port serial. W trybie dry-run nie otwiera niczego."""
        if self.dry_run:
            self.connected = True
            self.last_error = ""
            return

        if self.serial_port is not None:
            self.connected = True
            return

        if serial is None:
            self.connected = False
            self.last_error = "Brak pakietu pyserial. Zainstaluj: pip install pyserial"
            raise RuntimeError(self.last_error)

        if not self.port:
            self.connected = False
            self.last_error = "Brak portu Nextion 5"
            raise RuntimeError(self.last_error)

        try:
            self.serial_port = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
                write_timeout=self.write_timeout,
            )
            self.connected = True
            self.last_error = ""
        except Exception as exc:  # pragma: no cover - zależne od sprzętu
            self.serial_port = None
            self.connected = False
            self.last_error = str(exc)
            raise RuntimeError(f"Nie można otworzyć portu LKS-N5 {self.port}: {exc}") from exc

    def open(self) -> bool:
        """Zgodność z istniejącym stylem hardware/tarzanNextion/device.py."""
        try:
            self.connect()
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self.serial_port is not None:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None
        self.connected = False

    def __enter__(self) -> "TarzanLksN5Device":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def command_bytes(self, text: str) -> bytes:
        """Buduje komendę Nextion zakończoną FF FF FF."""
        command = str(text).strip()
        return command.encode(self.encoding, errors="replace") + TERMINATOR

    def cmd(self, text: str) -> None:
        """Wysyła surową komendę Nextion, np. page status_main."""
        command = str(text).strip()
        if not command:
            return

        self.last_tx = command
        self.tx_history.append(command)
        self.tx_history = self.tx_history[-200:]

        payload = self.command_bytes(command)

        if self.dry_run:
            print(f"DRY-RUN LKS-N5 TX: {command}")
            return

        if self.serial_port is None:
            self.connect()

        try:
            assert self.serial_port is not None
            self.serial_port.write(payload)
            self.serial_port.flush()
            self.last_error = ""
        except Exception as exc:  # pragma: no cover - zależne od sprzętu
            self.last_error = str(exc)
            self.close()
            raise RuntimeError(f"Błąd wysyłania do LKS-N5: {exc}") from exc

    def send_cmd(self, text: str) -> None:
        """Alias dla starszego nazewnictwa z dokumentacji roboczej."""
        self.cmd(text)

    def page(self, name: str) -> None:
        self.cmd(f"page {name}")

    def txt(self, component: str, value: str) -> None:
        safe = str(value).replace("\\", "\\\\").replace('"', "'")
        self.cmd(f'{component}.txt="{safe}"')

    def val(self, component: str, value: int) -> None:
        self.cmd(f"{component}.val={int(value)}")

    def vis(self, component: str, visible: bool) -> None:
        self.cmd(f"vis {component},{1 if visible else 0}")

    def bkcmd(self, level: int = 3) -> None:
        self.cmd(f"bkcmd={int(level)}")

    def clear_rx(self) -> None:
        self.read_buffer.clear()
        if self.serial_port is not None:
            try:
                self.serial_port.reset_input_buffer()
            except Exception:
                pass

    def poll_events(self) -> List[LksN5Event]:
        """Czyta kompletne pakiety zakończone FF FF FF."""
        if self.dry_run or self.serial_port is None:
            return []

        try:
            waiting = int(getattr(self.serial_port, "in_waiting", 0) or 0)
            if waiting > 0:
                self.read_buffer.extend(self.serial_port.read(waiting))
        except Exception as exc:  # pragma: no cover - zależne od sprzętu
            self.last_error = f"Błąd odczytu LKS-N5: {exc}"
            self.close()
            return []

        out: List[LksN5Event] = []
        while TERMINATOR in self.read_buffer:
            idx = self.read_buffer.index(TERMINATOR)
            raw = bytes(self.read_buffer[:idx])
            del self.read_buffer[: idx + len(TERMINATOR)]
            event = LksN5Event(raw=raw)
            out.append(event)
            self.last_rx = raw

        if out:
            self.events.extend(out)
            self.events = self.events[-100:]
        return out

    def read_event(self, wait_s: Optional[float] = None) -> Optional[LksN5Event]:
        """Czeka krótko na jeden event z Nextiona."""
        deadline = time.time() + float(self.timeout if wait_s is None else wait_s)
        while time.time() <= deadline:
            events = self.poll_events()
            if events:
                return events[0]
            time.sleep(0.01)
        return None

    def send_sequence(self, commands: Iterable[str], delay_s: float = 0.05) -> None:
        for command in commands:
            self.cmd(command)
            if delay_s > 0:
                time.sleep(delay_s)

    def run_basic_test(self) -> None:
        """Test ręczny zgodny z dokumentacją ETAPU 2."""
        self.bkcmd(3)
        self.page("boot_linux")
        self.txt("t_title", "LINUX OK")
        self.txt("t_line1", "TEST FROM MINI PC")
        self.txt("t_line2", "NEXTION 5 ONLINE")
        self.txt("t_status", "LKS-N5 SERIAL OK")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 / Nextion 5 serial device")
    parser.add_argument("--port", default="", help="Port Nextion 5, najlepiej /dev/serial/by-id/...")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="Domyślnie 9600")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--dry-run", action="store_true", help="Nie otwiera portu; wypisuje komendy")
    parser.add_argument("--test", action="store_true", help="Wysyła test ETAPU 2")
    parser.add_argument("--cmd", action="append", default=[], help="Surowa komenda Nextion, można podać wiele razy")
    parser.add_argument("--read", action="store_true", help="Po komendach odczytaj jeden event z Nextiona")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    if not args.dry_run and not args.port:
        print("BŁĄD: podaj --port albo użyj --dry-run", file=sys.stderr)
        return 2

    device = TarzanLksN5Device(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    try:
        with device:
            if args.test:
                device.run_basic_test()
            for command in args.cmd:
                device.cmd(command)
            if args.read:
                event = device.read_event(wait_s=args.timeout)
                if event is None:
                    print("RX: brak eventu")
                else:
                    print(f"RX: {event.raw!r} / {event.text}")
    except Exception as exc:
        print(f"BŁĄD LKS-N5: {exc}", file=sys.stderr)
        return 1

    if device.last_tx:
        print(f"OK LKS-N5 TX: {device.last_tx}")
    else:
        print("OK LKS-N5")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
