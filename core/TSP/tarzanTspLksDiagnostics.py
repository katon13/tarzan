from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 6: bezpieczna diagnostyka podzespołów.

Ten moduł wykonuje wyłącznie diagnostykę read-only / presence-check.
Nie wysyła STEP, DIR, ENABLE, nie porusza osi i nie steruje wyjściami
wykonawczymi. Wynikiem jest mapa statusów dla strony ``status_main``.
"""

import argparse
import glob
import importlib
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from core.TSP.tarzanTspLksStatusMap import (
    GROUP_AXIS,
    GROUP_BUS,
    GROUP_CAMERA,
    GROUP_IO,
    GROUP_POKEYS,
    GROUP_SOK,
    GROUP_SYSTEM,
    REQUIRED_BUS_DEVICES,
    bus_ok_from_statuses,
    empty_statuses,
    validate_component,
)


@dataclass
class LksCheckResult:
    """Pojedynczy wynik testu LKS-N5.

    ``component`` musi odpowiadać komponentowi ``status_main`` albo kluczowi
    logicznemu z mapy. ``ok=True`` oznacza, że kontrolka może zostać zapalona.
    """

    key: str
    component: str
    ok: bool
    label: str
    detail: str = ""
    error: str = ""
    duration_ms: int = 0


class TarzanTspLksDiagnostics:
    """Bezpieczna diagnostyka status_main dla LKS-N5.

    Diagnostyka jest ostrożna: sprawdza obecność modułów, katalogów, portów,
    węzłów urządzeń i możliwość bezpiecznego odczytu. Nie dotyka ruchu.
    """

    def __init__(self, repo_root: Optional[str] = None, required_bus_devices: Optional[Sequence[str]] = None) -> None:
        self.repo_root = Path(repo_root or self._detect_repo_root()).resolve()
        self.required_bus_devices = tuple(required_bus_devices or REQUIRED_BUS_DEVICES)
        self.results: List[LksCheckResult] = []
        self.statuses: Dict[str, bool] = empty_statuses(False)

    def _detect_repo_root(self) -> str:
        here = Path(__file__).resolve()
        try:
            return str(here.parents[2])
        except Exception:
            return os.getcwd()

    def _result(
        self,
        key: str,
        component: str,
        ok: bool,
        label: str,
        detail: str = "",
        error: str = "",
        start: Optional[float] = None,
    ) -> LksCheckResult:
        duration_ms = int((time.time() - start) * 1000) if start is not None else 0
        component_name = validate_component(component) if component else ""
        item = LksCheckResult(
            key=str(key),
            component=component_name,
            ok=bool(ok),
            label=str(label),
            detail=str(detail or ""),
            error=str(error or ""),
            duration_ms=duration_ms,
        )
        self.results.append(item)
        if component_name:
            self.statuses[component_name] = bool(ok)
        return item

    def _check_import(self, module_name: str, key: str, component: str, label: str) -> LksCheckResult:
        start = time.time()
        try:
            importlib.import_module(module_name)
            return self._result(key, component, True, label, detail=module_name, start=start)
        except Exception as exc:
            return self._result(key, component, False, label, detail=module_name, error=str(exc), start=start)

    def _check_path(self, path: Path, key: str, component: str, label: str) -> LksCheckResult:
        start = time.time()
        ok = path.exists()
        return self._result(key, component, ok, label, detail=str(path), error="" if ok else "not found", start=start)

    def _glob_any(self, patterns: Iterable[str]) -> List[str]:
        found: List[str] = []
        for pattern in patterns:
            found.extend(glob.glob(pattern))
        return sorted(set(found))

    def check_system(self) -> List[LksCheckResult]:
        before = len(self.results)
        self._result("python_runtime", "linux_sys", sys.version_info.major >= 3, "Python runtime", detail=sys.version.split()[0])
        self._check_import("core.TSP.tarzanTsp", "tsp_module", "linux_sys", "TSP module")
        self._check_import("core.TSP.tarzanTspLks", "lks_tty_module", "linux_sys", "LKS-TTY module")
        self._check_import("core.TSP.tarzanTspSignals", "signals_module", "snajper_sys", "Signal/Snajper layer")
        self._check_path(self.repo_root / "data" / "take", "take_dir", "take_sys", "TAKE data directory")
        self._check_path(self.repo_root / "editor" / "PAR", "par_dir", "par_sys", "PAR module directory")
        self._check_path(self.repo_root / "editor" / "EHR", "ehr_dir", "ehr_sys", "EHR module directory")
        return self.results[before:]

    def check_pokeys(self) -> List[LksCheckResult]:
        before = len(self.results)
        candidates = []
        candidates.extend(str(p) for p in (self.repo_root / "hardware" / "pokeys").glob("PoKeys*"))
        candidates.extend(str(p) for p in self.repo_root.glob("**/libPoKeys.so*"))
        candidates.extend(str(p) for p in self.repo_root.glob("**/PoKeyslib.dll"))
        ok = bool(candidates)
        detail = ", ".join(candidates[:4])
        self._result("pokeys_play_presence", "pok_play", ok, "PoKeys PLAY presence", detail=detail, error="PoKeys lib/module not found" if not ok else "")
        self._result("pokeys_rec_presence", "pok_rec", ok, "PoKeys REC presence", detail=detail or "same source", error="PoKeys lib/module not found" if not ok else "")
        return self.results[before:]

    def check_bus(self) -> List[LksCheckResult]:
        before = len(self.results)
        i2c_nodes = self._glob_any(["/dev/i2c-*"])
        serial_nodes = self._glob_any(["/dev/serial/by-id/*", "/dev/ttyUSB*", "/dev/ttyACM*"])
        has_i2c = bool(i2c_nodes)
        has_serial = bool(serial_nodes)

        # Safe presence/read-only checks. Szczegółowe adresy I2C można dopiąć później
        # w konfiguracji, bez zmiany kontraktu .val=0/1.
        self._result("bus_serial", "i2c_bus", has_serial, "UART/USB serial bus", detail=", ".join(serial_nodes[:4]), error="no serial ports" if not has_serial else "")
        self._result("bus_i2c_node", "i2c_bus", has_i2c, "I2C device node", detail=", ".join(i2c_nodes[:4]), error="no /dev/i2c-*" if not has_i2c else "")

        bus_detail = ", ".join(i2c_nodes[:3]) or ", ".join(serial_nodes[:3])
        bus_error = "no safe bus node" if not (has_i2c or has_serial) else ""
        for component, label in (
            ("lcd_1602", "LCD 1602 communication path"),
            ("matrix_led", "Matrix LED communication path"),
            ("keypad", "Keypad read path"),
            ("light_bh1750", "BH1750 read path"),
            ("level_xyz", "LEVEL XYZ read path"),
            ("shock_alarm", "Shock/alarm read path"),
            ("light_laser", "Laser/light module path"),
        ):
            # Elementy I2C wymagają I2C; laser/light zostaje OK przy dowolnej magistrali.
            if component == "light_laser":
                ok = has_i2c or has_serial
            else:
                ok = has_i2c
            self._result(f"bus_{component}", component, ok, label, detail=bus_detail, error="no I2C node" if not ok else "")

        # Agregat i2c_bus: prawdziwy dopiero gdy wymagane elementy są OK.
        self.statuses["i2c_bus"] = bus_ok_from_statuses(self.statuses)
        return self.results[before:]

    def check_io(self) -> List[LksCheckResult]:
        before = len(self.results)
        # Read-only/presence. Bez zapalania LED i bez ustawiania outputów.
        gpio_paths = self._glob_any(["/sys/class/gpio/*", "/sys/class/leds/*"])
        has_gpio_or_leds = bool(gpio_paths)
        self._result("f_buttons_read_path", "f_button", has_gpio_or_leds, "F1-F4 buttons read path", detail=", ".join(gpio_paths[:4]), error="no GPIO/LED sysfs path" if not has_gpio_or_leds else "")
        self._result("f_led_whitelist_path", "f_led", has_gpio_or_leds, "F1-F4 LED whitelist path", detail="read-only presence, no output toggled", error="no GPIO/LED sysfs path" if not has_gpio_or_leds else "")
        self._result("limits_read_path", "kranc", has_gpio_or_leds, "Limit switches read path", detail="read-only presence", error="no GPIO path" if not has_gpio_or_leds else "")
        return self.results[before:]

    def check_cameras(self) -> List[LksCheckResult]:
        before = len(self.results)
        video_nodes = self._glob_any(["/dev/video*"])
        has_camera = bool(video_nodes)
        detail = ", ".join(video_nodes[:4])
        self._result("cam_main_presence", "cam_main", has_camera, "Main camera device", detail=detail, error="no /dev/video*" if not has_camera else "")
        # Tracking camera wymaga drugiego urządzenia albo zostaje OFF.
        self._result("cam_track_presence", "cam_track", len(video_nodes) >= 2, "Tracking camera device", detail=detail, error="less than two cameras" if len(video_nodes) < 2 else "")
        return self.results[before:]

    def check_axes_and_sok_read_only(self) -> List[LksCheckResult]:
        before = len(self.results)
        # ETAP 6 nadal nie robi ruchu. Sterowniki osi/SOK oznaczamy tylko, jeśli
        # znajdziemy bezpieczne ślady konfiguracji/modułów. Nie wysyłamy nic do driverów.
        axis_markers = list(self.repo_root.glob("**/*step*")) + list(self.repo_root.glob("**/*axis*"))
        has_axis_config = bool(axis_markers)
        for component in GROUP_AXIS:
            self._result(f"axis_{component}_config", component, has_axis_config, f"{component} driver/config presence", detail="read-only config scan", error="no axis config marker" if not has_axis_config else "")

        sok_markers = [p for p in self.repo_root.glob("**/*sok*") if p.is_file()]
        has_sok = bool(sok_markers)
        for component in GROUP_SOK:
            self._result(f"sok_{component}_presence", component, has_sok, f"{component} presence", detail=", ".join(str(p) for p in sok_markers[:3]), error="no SOK marker" if not has_sok else "")

        # RRP jako obecność modułu/struktury, bez sterowania.
        rrp_markers = [p for p in self.repo_root.glob("**/*rrp*") if p.is_file()]
        self._result("rrp_presence", "rrp", bool(rrp_markers), "RRP module presence", detail=", ".join(str(p) for p in rrp_markers[:3]), error="no RRP marker" if not rrp_markers else "")

        # Nextion 7 jako obecność eksportu/konfiguracji, bez komunikacji z panelem operatora.
        n7_markers = [p for p in self.repo_root.glob("**/*nextion*7*") if p.is_file()]
        self._result("nextion7_presence", "next_7", bool(n7_markers), "Nextion 7 config/export presence", detail=", ".join(str(p) for p in n7_markers[:3]), error="no Nextion 7 marker" if not n7_markers else "")
        return self.results[before:]


    def run_component(self, component: str) -> List[LksCheckResult]:
        """Uruchamia diagnostykę punktową tylko dla wybranego ogniwa.

        To jest tryb kliknięcia z Nextiona 5. Nie wykonuje pełnego ``run_all``
        i nie resetuje całej tablicy status_main. Sprawdza tylko najbliższą
        logiczną grupę potrzebną do ustalenia wyniku wskazanego komponentu.
        Nadal obowiązuje zakaz STEP/DIR/ENABLE i zakaz ruchu osi.
        """
        name = validate_component(component)
        self.results.clear()
        self.statuses = empty_statuses(False)

        if name in GROUP_SYSTEM:
            self.check_system()
        elif name in GROUP_POKEYS:
            self.check_pokeys()
        elif name in GROUP_BUS:
            self.check_bus()
        elif name in GROUP_IO:
            self.check_io()
        elif name in GROUP_CAMERA:
            self.check_cameras()
        elif name in GROUP_AXIS or name in GROUP_SOK or name in {"rrp", "next_7"}:
            self.check_axes_and_sok_read_only()
        else:
            self._result(
                key=f"{name}_diagnostic_missing",
                component=name,
                ok=False,
                label=f"{name} diagnostic",
                error="no point diagnostic assigned",
            )

        if name == "i2c_bus" or name in GROUP_BUS:
            self.statuses["i2c_bus"] = bus_ok_from_statuses(self.statuses)

        selected = [item for item in self.results if item.component == name]
        if not selected:
            self._result(
                key=f"{name}_not_checked",
                component=name,
                ok=False,
                label=f"{name} point diagnostic",
                error="component was not checked",
            )
            selected = [item for item in self.results if item.component == name]

        # Wynik końcowy przycisku: OK tylko gdy wszystkie wyniki tego elementu są OK.
        self.statuses[name] = all(item.ok for item in selected)
        return selected

    def run_all(self) -> List[LksCheckResult]:
        self.results.clear()
        self.statuses = empty_statuses(False)
        self.check_system()
        self.check_pokeys()
        self.check_bus()
        self.check_io()
        self.check_cameras()
        self.check_axes_and_sok_read_only()
        self.statuses["i2c_bus"] = bus_ok_from_statuses(self.statuses)
        return list(self.results)

    def status_map(self) -> Dict[str, bool]:
        return dict(self.statuses)


class DryRunLksN5:
    """Minimalny adapter do testu diagnostyki bez ekranu."""

    def show_status(self, reset: bool = False) -> None:
        print(f"DRY-RUN LKS-N5 DIAG: page status_main reset={reset}")

    def set_many_statuses(self, statuses: Mapping[str, bool]) -> None:
        for key, ok in statuses.items():
            print(f"DRY-RUN LKS-N5 DIAG: {key}.val={1 if ok else 0}")

    def show_warn(self, **kwargs) -> None:
        print(f"DRY-RUN LKS-N5 DIAG WARN: {kwargs}")


def apply_diagnostics_to_n5(n5: object, diagnostics: TarzanTspLksDiagnostics) -> List[LksCheckResult]:
    results = diagnostics.run_all()
    n5.show_status(reset=True)
    n5.set_many_statuses(diagnostics.status_map())
    return results


def summarize_results(results: Iterable[LksCheckResult]) -> str:
    ok = 0
    fail = 0
    for item in results:
        if item.ok:
            ok += 1
        else:
            fail += 1
    return f"diagnostics ok={ok} off/fail={fail}"


def _print_results(results: Iterable[LksCheckResult]) -> None:
    for item in results:
        mark = "OK" if item.ok else "OFF"
        extra = item.detail or item.error
        print(f"{mark:3} {item.component:14} {item.key:24} {item.label} {extra}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 ETAP 6 diagnostics")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-results", action="store_true")
    parser.add_argument("--component", default="", help="Test punktowy jednego komponentu status_main")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        diagnostics = TarzanTspLksDiagnostics(repo_root=args.repo_root or None)
        if args.component:
            results = diagnostics.run_component(args.component)
        elif args.dry_run:
            n5 = DryRunLksN5()
            results = apply_diagnostics_to_n5(n5, diagnostics)
        else:
            results = diagnostics.run_all()
        if args.print_results:
            _print_results(results)
        print(summarize_results(results))
    except Exception as exc:
        print(f"BŁĄD LKS-N5 DIAGNOSTICS: {exc}", file=sys.stderr)
        return 1
    print("OK LKS-N5 DIAGNOSTICS")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
