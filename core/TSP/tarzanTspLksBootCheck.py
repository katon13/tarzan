from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 5: realny, bezpieczny boot-check miniPC.

Ten moduł wykonuje tylko testy obecności i odczytu. Nie wysyła STEP/DIR/ENABLE,
nie rusza osi i nie wykonuje testów wyjść wykonawczych. Wyniki pokazuje przez
warstwę scen ``TarzanTspLksNextion5``.
"""

import argparse
import glob
import importlib
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from core.TSP.tarzanTspLksStatusMap import REQUIRED_BUS_DEVICES, empty_statuses, bus_ok_from_statuses
from core.TSP.tarzanTspLksDiagnostics import TarzanTspLksDiagnostics


@dataclass
class LksBootCheckResult:
    key: str
    component: str
    ok: bool
    label: str
    detail: str = ""
    error: str = ""
    duration_ms: int = 0


class TarzanTspLksBootCheck:
    """Bezpieczna sekwencja boot-check dla LKS-N5.

    Odpowiedzialność:
    - przełączyć realne plansze startowe,
    - sprawdzić tylko bezpieczne fakty systemowe/obecnościowe,
    - zbudować statusy dla ``status_main``.

    Diagnostyka pełnych podzespołów przyjdzie w ETAPIE 6.
    """

    def __init__(self, n5: object, repo_root: Optional[str] = None, pause_s: float = 0.35, hardware_bridge: Optional[Any] = None) -> None:
        self.n5 = n5
        self.repo_root = Path(repo_root or self._detect_repo_root()).resolve()
        self.pause_s = float(pause_s)
        self.hardware_bridge = hardware_bridge
        self.results: List[LksBootCheckResult] = []
        self.statuses: Dict[str, bool] = empty_statuses(False)

    def _detect_repo_root(self) -> str:
        here = Path(__file__).resolve()
        # core/TSP/tarzanTspLksBootCheck.py -> repo root = parents[2]
        try:
            return str(here.parents[2])
        except Exception:
            return os.getcwd()

    def _pause(self) -> None:
        if self.pause_s > 0:
            time.sleep(self.pause_s)

    def _result(self, key: str, component: str, ok: bool, label: str, detail: str = "", error: str = "", start: Optional[float] = None) -> LksBootCheckResult:
        duration_ms = int((time.time() - start) * 1000) if start is not None else 0
        item = LksBootCheckResult(
            key=key,
            component=component,
            ok=bool(ok),
            label=label,
            detail=detail,
            error=error,
            duration_ms=duration_ms,
        )
        self.results.append(item)
        if component:
            self.statuses[component] = bool(ok)
        return item

    def _check_module(self, module_name: str, key: str, component: str, label: str) -> LksBootCheckResult:
        start = time.time()
        try:
            importlib.import_module(module_name)
            return self._result(key, component, True, label, detail=module_name, start=start)
        except Exception as exc:
            return self._result(key, component, False, label, detail=module_name, error=str(exc), start=start)

    def _check_path_exists(self, path: Path, key: str, component: str, label: str) -> LksBootCheckResult:
        start = time.time()
        ok = path.exists()
        return self._result(key, component, ok, label, detail=str(path), error="" if ok else "not found", start=start)

    def _systemctl_is_active(self, service_name: str) -> bool:
        try:
            proc = subprocess.run(
                ["systemctl", "is-active", "--quiet", service_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=0.8,
                check=False,
            )
            return proc.returncode == 0
        except Exception:
            return False

    def check_services(self) -> List[LksBootCheckResult]:
        before = len(self.results)
        # Linux/Python/TSP/LKS obecność modułów — bezpieczne, read-only.
        python_ok = bool(sys.version_info.major >= 3)
        self._result("python", "linux_sys", python_ok, "Python runtime", detail=sys.version.split()[0])
        self._check_module("core.TSP.tarzanTsp", "tsp_module", "linux_sys", "TSP module")
        self._check_module("core.TSP.tarzanTspLks", "lks_tty_module", "linux_sys", "LKS-TTY module")

        # SSH jest informacyjne. Brak aktywnego ssh nie zatrzymuje boot-check.
        ssh_ok = self._systemctl_is_active("ssh") or self._systemctl_is_active("sshd")
        self._result("ssh_service", "linux_sys", ssh_ok, "SSH service", detail="ssh/sshd")

        # TAKE/PAR/EHR jako obecność modułów/katalogów, bez uruchamiania UI.
        self._check_path_exists(self.repo_root / "data" / "take", "take_dir", "take_sys", "TAKE data dir")
        self._check_path_exists(self.repo_root / "editor" / "PAR", "par_dir", "par_sys", "PAR module dir")
        self._check_path_exists(self.repo_root / "editor" / "EHR", "ehr_dir", "ehr_sys", "EHR module dir")
        return self.results[before:]

    def check_hardware_presence(self) -> List[LksBootCheckResult]:
        before = len(self.results)
        serial_by_id = Path("/dev/serial/by-id")
        serial_links = sorted(glob.glob("/dev/serial/by-id/*"))
        tty_links = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
        i2c_links = sorted(glob.glob("/dev/i2c-*"))

        self._result(
            "serial_by_id",
            "i2c_bus",
            bool(serial_by_id.exists() and serial_links),
            "Serial/USB by-id",
            detail=", ".join(serial_links[:4]) or str(serial_by_id),
            error="no serial devices" if not serial_links else "",
        )
        self._result(
            "tty_usb",
            "i2c_bus",
            bool(tty_links),
            "TTY USB/ACM ports",
            detail=", ".join(tty_links[:4]),
            error="no ttyUSB/ttyACM" if not tty_links else "",
        )
        self._result(
            "i2c_dev",
            "i2c_bus",
            bool(i2c_links),
            "I2C device node",
            detail=", ".join(i2c_links[:4]),
            error="no /dev/i2c-*" if not i2c_links else "",
        )

        # PoKeys: na tym etapie tylko obecność możliwego modułu/biblioteki, bez wyjść.
        pokeys_candidates = list((self.repo_root / "hardware" / "pokeys").glob("PoKeys*"))
        pokeys_lib_candidates = list(self.repo_root.glob("**/libPoKeys.so*"))
        pokeys_seen = bool(pokeys_candidates or pokeys_lib_candidates)
        self._result(
            "pokeys_presence",
            "pok_play",
            pokeys_seen,
            "PoKeys presence",
            detail=", ".join(str(p) for p in (pokeys_lib_candidates[:2] or pokeys_candidates[:2])),
            error="no PoKeys module/lib found" if not pokeys_seen else "",
        )
        self._result(
            "pokeys_presence_rec",
            "pok_rec",
            pokeys_seen,
            "PoKeys REC presence",
            detail="same safe presence check as PLAY",
            error="no PoKeys module/lib found" if not pokeys_seen else "",
        )
        return self.results[before:]

    def check_safe_devices(self) -> List[LksBootCheckResult]:
        before = len(self.results)
        # ETAP 5: jeszcze nie robimy pełnych testów sprzętu. Tylko potwierdzamy,
        # że automatyczny boot-check nie dotyka STEP/DIR/ENABLE i oznaczamy
        # elementy szczegółowe jako WAIT/OFF do ETAPU 6.
        for component, label in (
            ("lcd_1602", "LCD 1602 communication"),
            ("matrix_led", "Matrix LED communication"),
            ("keypad", "Keypad read"),
            ("f_button", "F1-F4 buttons read"),
            ("f_led", "F1-F4 LED whitelist pending"),
            ("light_bh1750", "BH1750 read"),
            ("level_xyz", "LEVEL XYZ read"),
            ("shock_alarm", "Shock/alarm read"),
            ("light_laser", "Laser/light module"),
            ("kranc", "Limits read"),
            ("cam_main", "Main camera presence"),
            ("cam_track", "Tracking camera presence"),
        ):
            self._result(f"safe_wait_{component}", component, False, label, detail="ETAP 6")

        # Osie i SOK zostają read-only/WAIT do diagnostyki sterowników.
        for component in ("kam_poz", "kam_pion", "kam_ostr", "kam_poch", "ram_poziom", "ram_pion", "sok_poz", "sok_pion", "rrp", "next_7", "snajper_sys"):
            self._result(f"safe_wait_{component}", component, False, component, detail="read-only later")

        # i2c_bus jako agregat wymaganych urządzeń: TRUE dopiero kiedy wszystkie
        # wymagane urządzenia magistrali mają TRUE. Na ETAPIE 5 zwykle pozostanie FALSE.
        for required in REQUIRED_BUS_DEVICES:
            self.statuses.setdefault(required, False)
        self.statuses["i2c_bus"] = bus_ok_from_statuses(self.statuses)
        return self.results[before:]

    def _service_lines(self, results: Iterable[LksBootCheckResult]) -> Mapping[str, str]:
        by_key = {item.key: item for item in results}
        ssh = "SSH: OK" if by_key.get("ssh_service", LksBootCheckResult("", "", False, "")).ok else "SSH: WAIT"
        tsp = "TSP: OK" if by_key.get("tsp_module", LksBootCheckResult("", "", False, "")).ok else "TSP: FAIL"
        lks = "LKS: OK" if by_key.get("lks_tty_module", LksBootCheckResult("", "", False, "")).ok else "LKS: FAIL"
        return {"ssh": ssh, "tsp": tsp, "lks": lks}

    def _hardware_lines(self, results: Iterable[LksBootCheckResult]) -> Mapping[str, str]:
        by_key = {item.key: item for item in results}
        pok = by_key.get("pokeys_presence")
        serial = by_key.get("serial_by_id")
        i2c = by_key.get("i2c_dev")
        return {
            "line1": "PLAY: SEEN" if pok and pok.ok else "PLAY: WAIT",
            "line2": "REC: SEEN" if pok and pok.ok else "REC: WAIT",
            "line3": "BUS: OK" if (serial and serial.ok and i2c and i2c.ok) else "BUS: CHECK",
        }

    def run(self) -> List[LksBootCheckResult]:
        """Wykonuje realny boot progress ETAPU 13 i pokazuje wynik na Nextion 5.

        Starsze metody check_services/check_hardware_presence pozostają w pliku jako
        kompatybilne testy pomocnicze, ale właściwa sekwencja startu jest teraz
        prowadzona przez TarzanTspLksBootProgress: każdy procent wynika z realnego
        kroku Linux/systemd/sprzęt/diagnostyka.
        """
        from core.TSP.tarzanTspLksBootProgress import TarzanTspLksBootProgress

        progress = TarzanTspLksBootProgress(
            self.n5,
            repo_root=str(self.repo_root),
            pause_s=self.pause_s,
            hardware_bridge=self.hardware_bridge,
        )
        progress_results = progress.run()
        self.statuses = dict(progress.statuses)
        self.results = [
            LksBootCheckResult(
                key=item.key,
                component=item.component,
                ok=item.ok,
                label=item.label,
                detail=item.detail,
                error=item.error,
                duration_ms=item.duration_ms,
            )
            for item in progress_results
        ]
        return list(self.results)


def summarize_results(results: Iterable[LksBootCheckResult]) -> str:
    ok = 0
    fail = 0
    for item in results:
        if item.ok:
            ok += 1
        else:
            fail += 1
    return f"boot-check ok={ok} wait/fail={fail}"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 ETAP 5 boot-check")
    parser.add_argument("--port", default="", help="Port Nextion 5, najlepiej /dev/serial/by-id/...")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=float, default=0.03)
    parser.add_argument("--pause", type=float, default=0.35)
    parser.add_argument("--repo-root", default="")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not args.dry_run and not args.port:
        print("BŁĄD: podaj --port albo użyj --dry-run", file=sys.stderr)
        return 2

    try:
        from core.TSP.tarzanTspLksNextion5 import TarzanTspLksNextion5

        with TarzanTspLksNextion5(
            port=args.port,
            baudrate=args.baudrate,
            timeout=args.timeout,
            dry_run=args.dry_run,
            command_delay_s=args.delay,
        ) as n5:
            runner = TarzanTspLksBootCheck(n5, repo_root=args.repo_root or None, pause_s=args.pause)
            results = runner.run()
            print(summarize_results(results))
    except Exception as exc:
        print(f"BŁĄD LKS-N5 BOOT-CHECK: {exc}", file=sys.stderr)
        return 1

    print("OK LKS-N5 BOOT-CHECK")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
