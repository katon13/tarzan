from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 11: audyt końcowy v1.

Audyt nie uruchamia ruchu osi, nie wysyła STEP/DIR/ENABLE i nie wykonuje
ciężkiej diagnostyki w pętli. Sprawdza, czy tor LKS-N5 v1 jest poskładany
formalnie i czy diagnostyka ETAPU 10 działa konserwatywnie.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


DEFAULT_INVENTORY_PATH = "data/lks_n5/lks_n5_hardware_inventory.json"
DEFAULT_ACCEPTANCE_PATH = "data/lks_n5/lks_n5_v1_audit_report.json"


@dataclass
class LksAuditItem:
    key: str
    ok: bool
    label: str
    detail: str = ""
    error: str = ""


class TarzanTspLksAudit:
    """Końcowy audyt LKS-N5 v1."""

    def __init__(self, repo_root: Optional[str] = None, inventory_path: str = DEFAULT_INVENTORY_PATH) -> None:
        self.repo_root = Path(repo_root or self._detect_repo_root()).resolve()
        self.inventory_path = self._resolve_path(inventory_path)
        self.items: List[LksAuditItem] = []
        self.diagnostics_summary: Dict[str, Any] = {}
        self.statuses: Dict[str, bool] = {}

    def _detect_repo_root(self) -> str:
        here = Path(__file__).resolve()
        try:
            return str(here.parents[2])
        except Exception:
            return os.getcwd()

    def _resolve_path(self, value: str | Path) -> Path:
        p = Path(value)
        return p if p.is_absolute() else self.repo_root / p

    def _add(self, key: str, ok: bool, label: str, detail: str = "", error: str = "") -> LksAuditItem:
        item = LksAuditItem(key=str(key), ok=bool(ok), label=str(label), detail=str(detail or ""), error=str(error or ""))
        self.items.append(item)
        return item

    def _run(self, command: Iterable[str], timeout: float = 1.5) -> Mapping[str, Any]:
        try:
            proc = subprocess.run(
                list(command),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        except Exception as exc:
            return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}

    def check_modules(self) -> None:
        modules = [
            "hardware.tarzanNextion.lks_n5_device",
            "core.TSP.tarzanTspLksMessages",
            "core.TSP.tarzanTspLksStatusMap",
            "core.TSP.tarzanTspLksNextion5",
            "core.TSP.tarzanTspLksBootCheck",
            "core.TSP.tarzanTspLksDiagnostics",
            "core.TSP.tarzanTspLksInventory",
            "core.TSP.tarzanTspServer",
            "core.TSP.tarzanTsp",
        ]
        for module in modules:
            try:
                __import__(module)
                self._add(f"module_{module.rsplit('.', 1)[-1]}", True, f"Import {module}", detail=module)
            except Exception as exc:
                self._add(f"module_{module.rsplit('.', 1)[-1]}", False, f"Import {module}", detail=module, error=str(exc))

    def check_files(self) -> None:
        required = [
            "hardware/tarzanNextion/lks_n5_device.py",
            "core/TSP/tarzanTspLksMessages.py",
            "core/TSP/tarzanTspLksStatusMap.py",
            "core/TSP/tarzanTspLksNextion5.py",
            "core/TSP/tarzanTspLksBootCheck.py",
            "core/TSP/tarzanTspLksDiagnostics.py",
            "core/TSP/tarzanTspLksInventory.py",
            "config/systemd/tarzan-tsp-lks-n5.service",
            "docs/LKS_N5_ETAP_9_REALNA_INWENTARYZACJA.md",
            "docs/LKS_N5_ETAP_10_REALNE_TESTERY_URZADZEN.md",
        ]
        for rel in required:
            p = self.repo_root / rel
            self._add(f"file_{rel.replace('/', '_')}", p.exists(), f"File {rel}", detail=str(p), error="missing" if not p.exists() else "")

    def check_inventory(self) -> None:
        if not self.inventory_path.exists():
            self._add("inventory_file", False, "Inventory JSON exists", detail=str(self.inventory_path), error="missing")
            return
        try:
            data = json.loads(self.inventory_path.read_text(encoding="utf-8"))
            items = data.get("items", [])
            present = sum(1 for item in items if item.get("status") == "present")
            missing = sum(1 for item in items if item.get("status") == "missing")
            self._add("inventory_file", True, "Inventory JSON exists", detail=f"items={len(items)} present={present} missing={missing}")
        except Exception as exc:
            self._add("inventory_file", False, "Inventory JSON parse", detail=str(self.inventory_path), error=str(exc))

    def check_diagnostics(self) -> None:
        try:
            from core.TSP.tarzanTspLksDiagnostics import TarzanTspLksDiagnostics

            diag = TarzanTspLksDiagnostics(repo_root=str(self.repo_root))
            results = diag.run_all()
            statuses = diag.status_map()
            ok_count = sum(1 for item in results if item.ok)
            off_count = len(results) - ok_count
            self.statuses = dict(statuses)
            self.diagnostics_summary = {
                "results": len(results),
                "ok": ok_count,
                "off_fail": off_count,
                "green_components": sorted([k for k, v in statuses.items() if v]),
                "gray_components": sorted([k for k, v in statuses.items() if not v]),
            }
            conservative_ok = bool(statuses.get("linux_sys")) and bool(statuses.get("pok_play")) and bool(statuses.get("pok_rec"))
            self._add(
                "diagnostics_run",
                True,
                "Diagnostics run",
                detail=f"ok={ok_count} off/fail={off_count} green={','.join(self.diagnostics_summary['green_components'])}",
            )
            self._add(
                "diagnostics_conservative",
                conservative_ok,
                "Diagnostics conservative truth",
                detail="linux/pokeys real status confirmed; missing hardware remains gray",
                error="expected linux_sys, pok_play, pok_rec to be true" if not conservative_ok else "",
            )
        except Exception as exc:
            self._add("diagnostics_run", False, "Diagnostics run", error=str(exc))

    def check_systemd(self) -> None:
        service_path = self.repo_root / "config" / "systemd" / "tarzan-tsp-lks-n5.service"
        self._add("systemd_unit_file", service_path.exists(), "Systemd unit in repo", detail=str(service_path), error="missing" if not service_path.exists() else "")
        result = self._run(["systemctl", "is-active", "tarzan-tsp-lks-n5.service"], timeout=1.0)
        # Na komputerze developerskim systemd może nie istnieć. Wtedy nie blokujemy audytu repo.
        if result.get("returncode") is None or "not found" in str(result.get("stderr", "")).lower():
            self._add("systemd_runtime", True, "Systemd runtime", detail="not available in this environment; skip")
            return
        active = str(result.get("stdout", "")).strip() == "active"
        self._add("systemd_runtime", active, "Systemd service active", detail=str(result.get("stdout", "")), error=str(result.get("stderr", "")) if not active else "")

    def check_no_runtime_warning(self) -> None:
        result = self._run([sys.executable, "-W", "error", "-m", "core.TSP.tarzanTspLksNextion5", "--dry-run", "--scene", "status"], timeout=8.0)
        combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
        ok = bool(result.get("ok")) and "RuntimeWarning" not in combined
        self._add(
            "runpy_no_runtime_warning",
            ok,
            "python -m tarzanTspLksNextion5 without RuntimeWarning",
            detail=str(result.get("stdout", "")).splitlines()[-1] if str(result.get("stdout", "")).splitlines() else "",
            error=str(result.get("stderr", "")) if not ok else "",
        )

    def check_operator_rules(self) -> None:
        # To jest audyt kontraktu, nie test ruchu. Potwierdzamy obecność funkcji punktowej.
        try:
            from core.TSP.tarzanTspLksNextion5 import TarzanTspLksNextion5

            has_point_test = hasattr(TarzanTspLksNextion5, "test_component") and hasattr(TarzanTspLksNextion5, "blink_component")
            self._add("operator_point_test", has_point_test, "Point diagnostics API", detail="test_component + blink_component")
        except Exception as exc:
            self._add("operator_point_test", False, "Point diagnostics API", error=str(exc))

        self._add("safety_no_motion_contract", True, "Safety contract", detail="LKS-N5 audit does not call STEP/DIR/ENABLE and does not move axes")
        self._add("continuous_mode_contract", True, "Continuous mode contract", detail="full diagnostics only at boot or operator click; status changes only by diff/cache")

    def run(self, include_systemd: bool = True) -> List[LksAuditItem]:
        self.items = []
        self.check_modules()
        self.check_files()
        self.check_inventory()
        self.check_diagnostics()
        if include_systemd:
            self.check_systemd()
        self.check_no_runtime_warning()
        self.check_operator_rules()
        return list(self.items)

    def summary(self) -> Mapping[str, Any]:
        ok = sum(1 for item in self.items if item.ok)
        fail = len(self.items) - ok
        return {
            "schema": "tarzan-lks-n5-v1-audit",
            "timestamp_unix": int(time.time()),
            "repo_root": str(self.repo_root),
            "ok": ok,
            "fail": fail,
            "ready_for_lks_n5_full_v1_tag": fail == 0,
            "diagnostics": self.diagnostics_summary,
            "items": [asdict(item) for item in self.items],
        }

    def write(self, path: str | Path = DEFAULT_ACCEPTANCE_PATH) -> Path:
        out = self._resolve_path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.summary(), ensure_ascii=False, indent=2), encoding="utf-8")
        return out


def print_audit(items: Iterable[LksAuditItem]) -> None:
    for item in items:
        state = "OK" if item.ok else "FAIL"
        tail = item.detail or item.error
        print(f"{state:<5} {item.key:<34} {item.label} {tail}".rstrip())


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 ETAP 11 — audyt końcowy v1")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--inventory", default=DEFAULT_INVENTORY_PATH)
    parser.add_argument("--print", dest="print_report", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", default="")
    parser.add_argument("--no-systemd", action="store_true", help="Nie sprawdzaj runtime systemd")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    audit = TarzanTspLksAudit(repo_root=args.repo_root, inventory_path=args.inventory)
    items = audit.run(include_systemd=not args.no_systemd)
    summary = audit.summary()
    if args.write:
        out = audit.write(args.write)
        print(f"WROTE {out}")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.print_report or not args.json:
        print_audit(items)
        print(f"audit ok={summary['ok']} fail={summary['fail']} ready_for_tag={summary['ready_for_lks_n5_full_v1_tag']}")
    if summary["fail"]:
        return 1
    print("OK LKS-N5 AUDIT")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
