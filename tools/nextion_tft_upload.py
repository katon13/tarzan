#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXTION TFT SERVICE UPLOAD — narzędzie poza TARZAN runtime.

Cel:
    Wgrać gotowy plik .tft do fizycznego Nextiona podłączonego lokalnie
    do tarzanMiniPC, np. /dev/ttyUSB0.

To NIE jest część PAR/TSP/Snajpera/LKS runtime. To jest tryb serwisowy.

Protokół:
    Nextion Instruction Set: komenda whmi-wri filesize,baud,res0 + FF FF FF.
    Po gotowości ekran odsyła 0x05. Dane .tft wysyłamy blokami i czekamy
    na kolejne 0x05 po każdym bloku.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

TERMINATOR = b"\xff\xff\xff"
ACK_READY = b"\x05"
DEFAULT_CHUNK_SIZE = 4096


class NextionUploadError(RuntimeError):
    pass


def _require_pyserial():
    try:
        import serial  # type: ignore
        return serial
    except Exception as exc:  # pragma: no cover
        raise NextionUploadError(
            "Brak pyserial. Zainstaluj: apt install -y python3-serial albo pip install pyserial"
        ) from exc


def _read_until_ack(ser, timeout_s: float, label: str) -> bytes:
    """Czeka na bajt 0x05. Zwraca wszystko, co przyszło po drodze."""
    end = time.monotonic() + timeout_s
    seen = bytearray()
    while time.monotonic() < end:
        data = ser.read(1)
        if not data:
            continue
        seen.extend(data)
        if data == ACK_READY:
            return bytes(seen)
    raise NextionUploadError(
        f"Timeout: nie otrzymano ACK 0x05 ({label}). Odebrano: {bytes(seen)!r}"
    )


def _send_nextion_command(ser, command: str) -> None:
    raw = command.encode("ascii", errors="strict") + TERMINATOR
    ser.write(raw)
    ser.flush()


def _format_size(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.2f} MB"


def upload_tft(
    port: str,
    file_path: Path,
    initial_baud: int = 9600,
    upload_baud: Optional[int] = None,
    timeout: float = 10.0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    dry_run: bool = False,
) -> None:
    serial = _require_pyserial()
    upload_baud = int(upload_baud or initial_baud)

    if not file_path.exists() or not file_path.is_file():
        raise NextionUploadError(f"Nie ma pliku TFT: {file_path}")
    if file_path.suffix.lower() != ".tft":
        raise NextionUploadError(f"Plik nie ma rozszerzenia .tft: {file_path}")

    filesize = file_path.stat().st_size
    if filesize <= 0:
        raise NextionUploadError("Plik TFT ma rozmiar 0 B")

    print("NEXTION TFT SERVICE UPLOAD")
    print(f"PORT:         {port}")
    print(f"FILE:         {file_path}")
    print(f"SIZE:         {_format_size(filesize)} ({filesize} B)")
    print(f"INITIAL BAUD: {initial_baud}")
    print(f"UPLOAD BAUD:  {upload_baud}")
    print(f"CHUNK:        {chunk_size} B")

    if dry_run:
        print("DRY RUN: nie otwieram portu i nie wysyłam danych.")
        return

    # Nextion najczęściej pracuje jako 8N1, bez flow control.
    with serial.Serial(
        port=port,
        baudrate=initial_baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.2,
        write_timeout=timeout,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    ) as ser:
        # Czyścimy bufor, ale nie wysyłamy żadnych komend runtime TARZANA.
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.10)

        command = f"whmi-wri {filesize},{upload_baud},0"
        print(f"SEND: {command}")
        _send_nextion_command(ser, command)

        if upload_baud != initial_baud:
            # Po komendzie whmi-wri Nextion przechodzi na upload_baud.
            time.sleep(0.05)
            ser.baudrate = upload_baud
            time.sleep(0.05)

        print("WAIT: ACK 0x05 before file transfer...")
        seen = _read_until_ack(ser, timeout, "po whmi-wri")
        print(f"ACK:  {seen!r}")

        sent = 0
        started = time.monotonic()
        with file_path.open("rb") as f:
            chunk_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_index += 1
                ser.write(chunk)
                ser.flush()
                sent += len(chunk)

                # Nextion potwierdza gotowość do następnego bloku bajtem 0x05.
                _read_until_ack(ser, timeout, f"po bloku {chunk_index}")

                percent = (sent / filesize) * 100.0
                elapsed = max(0.001, time.monotonic() - started)
                speed = sent / elapsed
                print(
                    f"PROGRESS: {percent:6.2f}%  "
                    f"{_format_size(sent)}/{_format_size(filesize)}  "
                    f"{_format_size(int(speed))}/s",
                    flush=True,
                )

        elapsed = max(0.001, time.monotonic() - started)
        print(f"DONE: wysłano {_format_size(sent)} w {elapsed:.1f} s")
        print("Nextion powinien sam zrestartować HMI albo przejść do nowego projektu.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wgrywanie pliku .tft do Nextiona przez lokalny port serial mini PC."
    )
    parser.add_argument("--port", required=True, help="Port Nextiona, np. /dev/ttyUSB0")
    parser.add_argument("--file", required=True, help="Ścieżka do pliku .tft")
    parser.add_argument("--baud", type=int, default=9600, help="Aktualny baud ekranu przed uploadem")
    parser.add_argument(
        "--upload-baud",
        type=int,
        default=None,
        help="Baud użyty do transferu .tft; domyślnie taki sam jak --baud",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout ACK 0x05 w sekundach")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Rozmiar bloku danych")
    parser.add_argument("--dry-run", action="store_true", help="Tylko walidacja argumentów")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        upload_tft(
            port=args.port,
            file_path=Path(args.file).expanduser().resolve(),
            initial_baud=args.baud,
            upload_baud=args.upload_baud,
            timeout=args.timeout,
            chunk_size=args.chunk_size,
            dry_run=args.dry_run,
        )
        return 0
    except KeyboardInterrupt:
        print("Przerwano przez użytkownika.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
