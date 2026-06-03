from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 10: realne testery urządzeń.

Ten moduł zamienia inwentaryzację ETAPU 9 na konserwatywne wyniki
``status_main``. Zielony status pojawia się tylko wtedy, gdy mamy realny
fakt z miniPC albo bezpieczny test read-only. Repo marker nie jest już OK.

Zakaz pozostaje bez zmian: zero STEP, zero DIR, zero ENABLE, zero ruchu osi,
zero nieznanych wyjść wykonawczych.
"""

import argparse
import glob
import importlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

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
from core.TSP.tarzanTspLksHardwareTests import TarzanTspLksHardwareTests, LksHardwareTestResult


DEFAULT_INVENTORY_PATH = "data/lks_n5/lks_n5_hardware_inventory.json"
DEFAULT_REQUIREMENTS_PATH = "data/lks_n5/lks_n5_hardware_requirements.json"


@dataclass
class LksCheckResult:
    """Pojedynczy wynik testu LKS-N5."""

    key: str
    component: str
    ok: bool
    label: str
    detail: str = ""
    error: str = ""
    duration_ms: int = 0


class _InventoryView:
    """Mały adapter po JSON ETAPU 9."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        self.data = dict(data or {})
        self.items = {str(item.get("key", "")): dict(item) for item in self.data.get("items", [])}

    def item(self, key: str) -> Mapping[str, Any]:
        return self.items.get(key, {})

    def status(self, key: str) -> str:
        return str(self.item(key).get("status", "missing"))

    def is_present(self, key: str) -> bool:
        return self.status(key) == "present"

    def detail(self, key: str) -> str:
        item = self.item(key)
        return str(item.get("detail", "") or item.get("error", ""))

    def values(self, key: str) -> Mapping[str, Any]:
        values = self.item(key).get("values", {})
        return values if isinstance(values, Mapping) else {}

    def text_blob(self, key: str) -> str:
        item = self.item(key)
        return "\n".join(
            [
                str(item.get("detail", "")),
                str(item.get("error", "")),
                json.dumps(item.get("values", {}), ensure_ascii=False),
            ]
        )


class TarzanTspLksDiagnostics:
    """Konserwatywna diagnostyka status_main dla LKS-N5.

    Etap 10 używa pliku inwentaryzacji z ETAPU 9. Jeżeli pliku nie ma, moduł
    może zebrać inwentaryzację na żywo, ale wynik dalej jest traktowany
    konserwatywnie: ``unknown`` i ``repo marker only`` nie zapalają zielonego.
    """

    def __init__(
        self,
        repo_root: Optional[str] = None,
        required_bus_devices: Optional[Sequence[str]] = None,
        inventory_path: Optional[str] = None,
        requirements_path: Optional[str] = None,
        collect_inventory_if_missing: bool = True,
    ) -> None:
        self.repo_root = Path(repo_root or self._detect_repo_root()).resolve()
        self.required_bus_devices = tuple(required_bus_devices or REQUIRED_BUS_DEVICES)
        self.inventory_path = self._resolve_path(inventory_path or DEFAULT_INVENTORY_PATH)
        self.requirements_path = self._resolve_path(requirements_path or DEFAULT_REQUIREMENTS_PATH)
        self.collect_inventory_if_missing = bool(collect_inventory_if_missing)
        self.results: List[LksCheckResult] = []
        self.statuses: Dict[str, bool] = empty_statuses(False)
        self.inventory = _InventoryView(self._load_or_collect_inventory())
        self.requirements = self._load_requirements()
        self.hardware_tests = TarzanTspLksHardwareTests(repo_root=str(self.repo_root))
        # Domyślnie pełna diagnostyka jest cicha. Boot może świadomie włączyć
        # krótkie, widoczne wzorce tylko dla wyjść operatorskich: LCD, Matrix, LED.
        self._operator_visible_run_all = False

    def _detect_repo_root(self) -> str:
        here = Path(__file__).resolve()
        try:
            return str(here.parents[2])
        except Exception:
            return os.getcwd()

    def _resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        return p if p.is_absolute() else self.repo_root / p

    def _load_or_collect_inventory(self) -> Mapping[str, Any]:
        if self.inventory_path.exists():
            return json.loads(self.inventory_path.read_text(encoding="utf-8"))
        if not self.collect_inventory_if_missing:
            return {"items": []}
        try:
            from core.TSP.tarzanTspLksInventory import TarzanTspLksInventory

            return TarzanTspLksInventory(repo_root=str(self.repo_root)).collect()
        except Exception as exc:
            return {
                "schema": "tarzan-lks-n5-inventory-missing",
                "items": [
                    {
                        "key": "inventory_load",
                        "status": "error",
                        "label": "Inventory load/collect",
                        "error": str(exc),
                    }
                ],
            }

    def _load_requirements(self) -> Mapping[str, Any]:
        if not self.requirements_path.exists():
            return {}
        try:
            return json.loads(self.requirements_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _run(self, command: Sequence[str], timeout: float = 1.0) -> Mapping[str, Any]:
        try:
            proc = subprocess.run(
                list(command),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
        except Exception as exc:
            return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}

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
            # Tymczasowo wpisujemy ostatni wynik; po grupie i po run_all robimy finalizację ALL().
            self.statuses[component_name] = bool(ok)
        return item

    def _hardware_result(self, key: str, probe: LksHardwareTestResult, start: Optional[float] = None) -> LksCheckResult:
        """Zamienia wynik suwerennego testera sprzętu na LksCheckResult."""
        return self._result(
            key=key,
            component=probe.component,
            ok=bool(probe.ok),
            label=probe.label,
            detail=probe.detail or probe.visible_action,
            error=probe.error,
            start=start,
        )

    def _try_hardware_probe(self, component: str, visible: bool = False) -> Optional[LksHardwareTestResult]:
        try:
            probe = self.hardware_tests.test_component(component, visible=visible)
        except Exception as exc:
            return LksHardwareTestResult(component=component, ok=False, supported=True, label=f"{component} sovereign hardware test", error=str(exc))
        return probe if probe.supported else None

    def _check_import(self, module_name: str, key: str, component: str, label: str, required: bool = True) -> LksCheckResult:
        start = time.time()
        try:
            importlib.import_module(module_name)
            return self._result(key, component, True, label, detail=module_name, start=start)
        except Exception as exc:
            return self._result(key, component, False if required else True, label, detail=module_name, error=str(exc), start=start)

    def _glob_any(self, patterns: Iterable[str]) -> List[str]:
        found: List[str] = []
        for pattern in patterns:
            found.extend(glob.glob(pattern))
        return sorted(set(found))

    def _finalize_statuses_for(self, components: Optional[Iterable[str]] = None) -> None:
        selected = set(validate_component(c) for c in components) if components is not None else None
        by_component: Dict[str, List[LksCheckResult]] = {}
        for item in self.results:
            if not item.component:
                continue
            if selected is not None and item.component not in selected:
                continue
            by_component.setdefault(item.component, []).append(item)
        for component, items in by_component.items():
            self.statuses[component] = bool(items) and all(item.ok for item in items)
        self.statuses["i2c_bus"] = bus_ok_from_statuses(self.statuses)

    # ------------------------------------------------------------------
    # Testery realne / konserwatywne
    # ------------------------------------------------------------------
    def check_system(self) -> List[LksCheckResult]:
        before = len(self.results)
        inv = self.inventory
        self._result("system_identity", "linux_sys", inv.is_present("system_identity"), "Linux/Python identity", detail=inv.detail("system_identity"), error="inventory missing" if not inv.is_present("system_identity") else "")
        self._result("repo_structure", "linux_sys", inv.is_present("repo_structure"), "TARZAN repo structure", detail=inv.detail("repo_structure"), error="repo structure not confirmed" if not inv.is_present("repo_structure") else "")
        self._result("system_time", "linux_sys", inv.is_present("system_time"), "System time synchronized/available", detail=inv.detail("system_time"), error="time not confirmed" if not inv.is_present("system_time") else "")
        self._result("service_lks_n5", "linux_sys", inv.is_present("service_lks_n5"), "LKS-N5 systemd service", detail=inv.detail("service_lks_n5"), error="service not active" if not inv.is_present("service_lks_n5") else "")

        self._check_import("core.TSP.tarzanTspSignals", "snajper_import", "snajper_sys", "Snajper/signal layer import")

        take_ok = inv.is_present("process_tsp") and inv.is_present("repo_marker_take")
        self._result("take_runtime", "take_sys", take_ok, "TAKE runtime marker + TSP process", detail=f"{inv.detail('process_tsp')} | {inv.detail('repo_marker_take')}", error="TSP process or TAKE data not confirmed" if not take_ok else "")

        # PAR/EHR: repo marker nie wystarcza. Do zielonego potrzebny proces/heartbeat/klient TSP.
        proc_text = inv.detail("process_tsp").lower()
        network_text = inv.detail("network_links")
        par_runtime = "par" in proc_text or "par_sys=1" in proc_text
        ehr_runtime = "ehr" in proc_text or "ehr_sys=1" in proc_text
        self._result("par_runtime", "par_sys", par_runtime, "PAR runtime/heartbeat", detail=network_text, error="repo marker only or no PAR heartbeat" if not par_runtime else "")
        self._result("ehr_runtime", "ehr_sys", ehr_runtime, "EHR runtime/heartbeat", detail=network_text, error="repo marker only or no EHR heartbeat" if not ehr_runtime else "")

        self._finalize_statuses_for(GROUP_SYSTEM)
        return self.results[before:]

    def check_pokeys(self) -> List[LksCheckResult]:
        before = len(self.results)
        text = self.inventory.text_blob("usb_lsusb")
        lib_seen = self.inventory.is_present("repo_marker_pokeys_lib") or self.inventory.is_present("usb_pokeys_hint")

        for component, board, pattern in (
            ("pok_play", "PLAY", r"PoLabs\s+PLAYER|PLAYER|PLAY"),
            ("pok_rec", "REC", r"PoLabs\s+RECK|RECK|REC"),
        ):
            probe = self._try_hardware_probe(component, visible=False)
            if probe is not None:
                self._hardware_result(f"{component}_sovereign_pokeys", probe)
                continue
            seen = bool(lib_seen and re.search(pattern, text, re.IGNORECASE))
            self._result(
                f"{component}_usb_identity",
                component,
                seen,
                f"PoKeys {board} USB identity",
                detail=text[:500],
                error=f"PoKeys {board} not identified or no real PoKeys wrapper" if not seen else "",
            )

        self._finalize_statuses_for(GROUP_POKEYS)
        return self.results[before:]

    def _configured_i2c_addresses(self) -> Mapping[str, Any]:
        return self.requirements.get("i2c_addresses", {}) if isinstance(self.requirements.get("i2c_addresses", {}), Mapping) else {}

    def _i2c_scan_text(self) -> str:
        return self.inventory.text_blob("i2c_scan")

    def _i2c_has_address(self, raw: Any) -> bool:
        if raw in (None, "", []):
            return False
        values = raw if isinstance(raw, list) else [raw]
        scan = self._i2c_scan_text().lower()
        if not scan:
            return False
        for value in values:
            token = str(value).strip().lower().replace("0x", "")
            if not token:
                continue
            token = token.zfill(2)[-2:]
            if re.search(rf"\b{re.escape(token)}\b", scan):
                return True
        return False

    def check_bus(self) -> List[LksCheckResult]:
        before = len(self.results)
        inv = self.inventory
        has_i2c_nodes = inv.is_present("i2c_nodes")
        has_i2c_scan = inv.is_present("i2c_scan") or inv.status("i2c_scan") == "unknown"
        self._result("i2c_nodes", "i2c_bus", has_i2c_nodes, "I2C device nodes", detail=inv.detail("i2c_nodes"), error="no /dev/i2c-*" if not has_i2c_nodes else "")

        addresses = self._configured_i2c_addresses()
        component_labels = {
            "lcd_1602": "LCD 1602 real bus test",
            "matrix_led": "Matrix LED real bus test",
            "keypad": "Keypad real bus test",
            "light_bh1750": "BH1750 real bus test",
            "level_xyz": "LEVEL XYZ real bus test",
            "shock_alarm": "Shock/alarm real bus test",
            "light_laser": "Laser/light module real bus test",
        }
        visible_output_components = {"lcd_1602", "matrix_led"}
        for component, label in component_labels.items():
            visible = bool(self._operator_visible_run_all and component in visible_output_components)
            probe = self._try_hardware_probe(component, visible=visible)
            if probe is not None:
                self._hardware_result(f"real_{component}_sovereign", probe)
                continue
            configured = component in addresses
            ok = bool(has_i2c_nodes and configured and self._i2c_has_address(addresses.get(component)))
            if not has_i2c_nodes:
                error = "no /dev/i2c-* and no sovereign PoKeys tester confirmed"
            elif not configured:
                error = "no configured I2C address/test path"
            elif not has_i2c_scan:
                error = "no i2c scan result"
            else:
                error = "configured address not detected"
            self._result(
                f"real_{component}",
                component,
                ok,
                label,
                detail=f"configured={addresses.get(component, '')} scan={inv.detail('i2c_scan')}",
                error="" if ok else error,
            )

        self._finalize_statuses_for(GROUP_BUS)
        return self.results[before:]

    def check_io(self) -> List[LksCheckResult]:
        before = len(self.results)
        io_cfg = self.requirements.get("io_paths", {}) if isinstance(self.requirements.get("io_paths", {}), Mapping) else {}
        for component, label in (
            ("f_button", "F1-F4 buttons read path"),
            ("f_led", "F1-F4 LED whitelist path"),
            ("kranc", "Limit switches read path"),
        ):
            # W boot nie czekamy na przyciski ani krańcówki. Widoczny wzorzec
            # dotyczy tylko LED F1-F4, bo to wyjście operatorskie.
            visible = bool(self._operator_visible_run_all and component == "f_led")
            probe = self._try_hardware_probe(component, visible=visible)
            if probe is not None:
                self._hardware_result(f"real_{component}_sovereign", probe)
                continue
            paths = io_cfg.get(component, [])
            if isinstance(paths, str):
                paths = [paths]
            existing = [p for p in paths if Path(str(p)).exists()]
            ok = bool(paths and existing)
            self._result(f"real_{component}", component, ok, label, detail=", ".join(existing), error="no configured real read path" if not ok else "")
        self._finalize_statuses_for(GROUP_IO)
        return self.results[before:]

    def check_cameras(self) -> List[LksCheckResult]:
        before = len(self.results)
        values = self.inventory.values("video_nodes")
        nodes = list(values.get("nodes", [])) if isinstance(values.get("nodes", []), list) else []
        self._result("cam_main_video", "cam_main", len(nodes) >= 1, "Main camera /dev/video", detail=", ".join(nodes), error="no /dev/video*" if len(nodes) < 1 else "")
        self._result("cam_track_video", "cam_track", len(nodes) >= 2, "Tracking camera /dev/video", detail=", ".join(nodes), error="second camera not confirmed" if len(nodes) < 2 else "")
        self._finalize_statuses_for(GROUP_CAMERA)
        return self.results[before:]

    def check_axes_and_sok_read_only(self) -> List[LksCheckResult]:
        before = len(self.results)
        # ETAP 10: repo marker nie wystarcza. Zielone dopiero po jawnej konfiguracji
        # read-only status path albo po przyszłym driver status API. Nie ruszamy osi.
        axis_cfg = self.requirements.get("axis_status_paths", {}) if isinstance(self.requirements.get("axis_status_paths", {}), Mapping) else {}
        for component in GROUP_AXIS:
            path = str(axis_cfg.get(component, "") or "")
            ok = bool(path and Path(path).exists())
            self._result(f"axis_{component}_readonly_status", component, ok, f"{component} read-only driver status", detail=path, error="repo marker only; no read-only driver status path" if not ok else "")

        sok_cfg = self.requirements.get("sok_status_paths", {}) if isinstance(self.requirements.get("sok_status_paths", {}), Mapping) else {}
        for component in GROUP_SOK:
            path = str(sok_cfg.get(component, "") or "")
            ok = bool(path and Path(path).exists())
            self._result(f"sok_{component}_readonly_status", component, ok, f"{component} real module status", detail=path, error="repo marker only; no real SOK mapping" if not ok else "")

        rrp_runtime = "rrp" in self.inventory.detail("process_tsp").lower()
        self._result("rrp_runtime", "rrp", rrp_runtime, "RRP runtime/heartbeat", detail=self.inventory.detail("process_tsp"), error="repo marker only; no runtime heartbeat" if not rrp_runtime else "")

        n7_candidates = self.inventory.values("nextion7_candidates").get("candidates", [])
        n7_ok = bool(n7_candidates and self.requirements.get("nextion7_port"))
        self._result("nextion7_mapping", "next_7", n7_ok, "Nextion 7 explicit serial mapping", detail=str(n7_candidates), error="no explicit Nextion 7 mapping on miniPC" if not n7_ok else "")

        self._finalize_statuses_for(tuple(GROUP_AXIS) + tuple(GROUP_SOK) + ("rrp", "next_7"))
        return self.results[before:]

    # ------------------------------------------------------------------
    # Tryby uruchamiania
    # ------------------------------------------------------------------
    def run_component(self, component: str, operator_visible: bool = True) -> List[LksCheckResult]:
        """Uruchamia diagnostykę punktową tylko dla wskazanego ogniwa."""
        name = validate_component(component)
        self.results.clear()
        self.statuses = empty_statuses(False)

        probe = self._try_hardware_probe(name, visible=bool(operator_visible))
        if probe is not None:
            self._hardware_result(f"{name}_sovereign_point_test", probe)
        elif name in GROUP_SYSTEM:
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
            self._result(f"{name}_diagnostic_missing", name, False, f"{name} diagnostic", error="no point diagnostic assigned")

        self._finalize_statuses_for([name])
        selected = [item for item in self.results if item.component == name]
        if not selected:
            self._result(f"{name}_not_checked", name, False, f"{name} point diagnostic", error="component was not checked")
            selected = [item for item in self.results if item.component == name]
        self.statuses[name] = all(item.ok for item in selected)
        if name == "i2c_bus" or name in GROUP_BUS:
            self.statuses["i2c_bus"] = bus_ok_from_statuses(self.statuses)
        return selected

    def run_all(self, operator_visible: bool = False) -> List[LksCheckResult]:
        """Uruchamia pełną diagnostykę.

        ``operator_visible=False`` zachowuje dotychczasowy, cichy tryb.
        ``operator_visible=True`` jest przeznaczone dla bootu LKS-N5 i włącza
        krótkie wzorce tylko na bezpiecznych wyjściach operatorskich:
        LCD 1602, Matrix LED i F1-F4 LED. Nie dotyka osi, STEP/DIR/ENABLE,
        homingu ani Pulse Engine. Nie czeka też na ręczne naciskanie przycisków.
        """
        self.results.clear()
        self.statuses = empty_statuses(False)
        previous_visible = self._operator_visible_run_all
        self._operator_visible_run_all = bool(operator_visible)
        try:
            self.check_system()
            self.check_pokeys()
            self.check_bus()
            self.check_io()
            self.check_cameras()
            self.check_axes_and_sok_read_only()
            self._finalize_statuses_for()
            return list(self.results)
        finally:
            self._operator_visible_run_all = previous_visible

    def status_map(self) -> Dict[str, bool]:
        return dict(self.statuses)


class DryRunLksN5:
    """Minimalny adapter do testu diagnostyki bez ekranu."""

    def show_status(self, reset: bool = False) -> None:
        print(f"DRY-RUN LKS-N5 DIAG: page status_main reset={reset}")

    def set_many_statuses(self, statuses: Mapping[str, bool]) -> None:
        for key, ok in statuses.items():
            print(f"DRY-RUN LKS-N5 DIAG: {key}.val={1 if ok else 0}")

    def show_warn(self, **kwargs: Any) -> None:
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
        print(f"{mark:3} {item.component:14} {item.key:34} {item.label} {extra}")


def _print_statuses(statuses: Mapping[str, bool]) -> None:
    for key in sorted(statuses):
        print(f"{key:14}={1 if statuses[key] else 0}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 ETAP 10 real diagnostics")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--inventory", default="", help=f"Inventory JSON from ETAP 9, default {DEFAULT_INVENTORY_PATH}")
    parser.add_argument("--requirements", default="", help=f"Optional requirements JSON, default {DEFAULT_REQUIREMENTS_PATH}")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-results", action="store_true")
    parser.add_argument("--print-statuses", action="store_true")
    parser.add_argument("--component", default="", help="Test punktowy jednego komponentu status_main")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        diagnostics = TarzanTspLksDiagnostics(
            repo_root=args.repo_root or None,
            inventory_path=args.inventory or None,
            requirements_path=args.requirements or None,
        )
        if args.component:
            results = diagnostics.run_component(args.component)
        elif args.dry_run:
            n5 = DryRunLksN5()
            results = apply_diagnostics_to_n5(n5, diagnostics)
        else:
            results = diagnostics.run_all()
        if args.print_results:
            _print_results(results)
        if args.print_statuses:
            _print_statuses(diagnostics.status_map())
        print(summarize_results(results))
    except Exception as exc:
        print(f"BŁĄD LKS-N5 DIAGNOSTICS: {exc}", file=sys.stderr)
        return 1
    print("OK LKS-N5 DIAGNOSTICS")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
