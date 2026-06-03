from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 9: realna inwentaryzacja miniPC/hardware.

Ten moduł NIE steruje sprzętem. Nie wysyła STEP/DIR/ENABLE. Nie porusza osi.
Jego zadaniem jest zebrać prawdę o środowisku miniPC: usługi, porty,
magistrale, urządzenia w /dev, ślady repo i kandydatów pod status_main.

Wynik jest zapisywany do JSON i ma być podstawą ETAPU 10 — realnych testerów.
Jeżeli czegoś nie da się potwierdzić, zapisujemy ``unknown`` albo ``missing``.
Nie udajemy zielonego statusu.
"""

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from core.TSP.tarzanTspLksStatusMap import all_components

DEFAULT_OUTPUT = "data/lks_n5/lks_n5_hardware_inventory.json"
DEFAULT_NEXTION5_PORT_HINT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"


@dataclass
class InventoryItem:
    key: str
    status: str  # present / missing / unknown / error
    label: str
    detail: str = ""
    error: str = ""
    values: Dict[str, Any] = field(default_factory=dict)


class TarzanTspLksInventory:
    """Read-only inventory of TARZAN miniPC for LKS-N5.

    ``collect()`` returns JSON-safe data. The inventory may be run on a dev
    station too, but the meaningful result is from the real miniPC.
    """

    def __init__(self, repo_root: Optional[str] = None) -> None:
        self.repo_root = Path(repo_root or self._detect_repo_root()).resolve()
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        self.items: List[InventoryItem] = []

    def _detect_repo_root(self) -> str:
        here = Path(__file__).resolve()
        try:
            return str(here.parents[2])
        except Exception:
            return os.getcwd()

    def _item(self, key: str, status: str, label: str, detail: str = "", error: str = "", values: Optional[Mapping[str, Any]] = None) -> InventoryItem:
        item = InventoryItem(
            key=str(key),
            status=str(status),
            label=str(label),
            detail=str(detail or ""),
            error=str(error or ""),
            values=dict(values or {}),
        )
        self.items.append(item)
        return item

    def _glob(self, patterns: Iterable[str]) -> List[str]:
        import glob

        found: List[str] = []
        for pattern in patterns:
            found.extend(glob.glob(pattern))
        return sorted(set(found))

    def _run(self, command: Sequence[str], timeout: float = 1.5) -> Dict[str, Any]:
        if not command or shutil.which(command[0]) is None:
            return {"ok": False, "returncode": None, "stdout": "", "stderr": f"command not found: {command[0] if command else ''}"}
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

    def _systemctl_state(self, unit: str) -> Dict[str, Any]:
        result = self._run(["systemctl", "is-active", unit], timeout=1.0)
        state = (result.get("stdout") or result.get("stderr") or "unknown").strip()
        return {"unit": unit, "state": state, "ok": state == "active", "raw": result}

    def collect_system(self) -> None:
        values = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "repo_root": str(self.repo_root),
            "cwd": os.getcwd(),
        }
        self._item("system_identity", "present", "Linux/Python identity", detail=values["hostname"], values=values)

        checks = {
            "repo_root_exists": self.repo_root.exists(),
            "core_tsp_exists": (self.repo_root / "core" / "TSP").exists(),
            "lks_tty_file": (self.repo_root / "core" / "TSP" / "tarzanTspLks.py").exists(),
            "lks_n5_file": (self.repo_root / "core" / "TSP" / "tarzanTspLksNextion5.py").exists(),
        }
        self._item(
            "repo_structure",
            "present" if all(checks.values()) else "missing",
            "TARZAN repo structure",
            detail=str(self.repo_root),
            values=checks,
        )

    def collect_services(self) -> None:
        units = [
            "ssh.service",
            "sshd.service",
            "tarzan-tsp-lks-n5.service",
        ]
        states = {unit: self._systemctl_state(unit) for unit in units}
        ssh_ok = states["ssh.service"]["ok"] or states["sshd.service"]["ok"]
        lks_service_ok = states["tarzan-tsp-lks-n5.service"]["ok"]
        self._item("service_ssh", "present" if ssh_ok else "missing", "SSH service", detail="active" if ssh_ok else "not active", values=states)
        self._item("service_lks_n5", "present" if lks_service_ok else "missing", "systemd LKS-N5 service", detail=states["tarzan-tsp-lks-n5.service"]["state"], values=states["tarzan-tsp-lks-n5.service"])

        proc = self._run(["pgrep", "-af", "tarzanTsp"], timeout=1.0)
        tsp_seen = bool(proc.get("ok") and proc.get("stdout"))
        self._item("process_tsp", "present" if tsp_seen else "missing", "TSP process", detail=(proc.get("stdout") or "")[:500], error="no tarzanTsp process" if not tsp_seen else "")

        ip = self._run(["ip", "-brief", "addr"], timeout=1.0)
        network_seen = bool(ip.get("ok") and ip.get("stdout"))
        self._item("network_links", "present" if network_seen else "unknown", "Network interfaces", detail=(ip.get("stdout") or ip.get("stderr") or "")[:900], values=ip)

        timedatectl = self._run(["timedatectl", "show", "-p", "SystemClockSynchronized", "-p", "NTPSynchronized"], timeout=1.0)
        self._item("system_time", "present" if timedatectl.get("ok") else "unknown", "System time state", detail=(timedatectl.get("stdout") or timedatectl.get("stderr") or ""), values=timedatectl)

    def collect_serial(self) -> None:
        by_id = self._glob(["/dev/serial/by-id/*"])
        tty = self._glob(["/dev/ttyUSB*", "/dev/ttyACM*"])
        resolved = {}
        for path in by_id:
            try:
                resolved[path] = str(Path(path).resolve())
            except Exception as exc:
                resolved[path] = f"ERROR: {exc}"

        self._item("serial_by_id", "present" if by_id else "missing", "Serial by-id devices", detail=", ".join(by_id), values={"paths": by_id, "resolved": resolved})
        self._item("serial_tty", "present" if tty else "missing", "TTY USB/ACM devices", detail=", ".join(tty), values={"paths": tty})

        n5_hint_exists = Path(DEFAULT_NEXTION5_PORT_HINT).exists()
        cp2102 = [p for p in by_id if "CP210" in p or "Silicon_Labs" in p]
        self._item(
            "nextion5_port",
            "present" if n5_hint_exists or cp2102 else "missing",
            "Nextion 5 serial candidate",
            detail=DEFAULT_NEXTION5_PORT_HINT if n5_hint_exists else ", ".join(cp2102),
            error="no CP2102/Nextion5 candidate" if not (n5_hint_exists or cp2102) else "",
            values={"hint": DEFAULT_NEXTION5_PORT_HINT, "hint_exists": n5_hint_exists, "cp2102_candidates": cp2102},
        )

        # Nextion 7 nie ma tu stałego portu w dokumentacji. Zbieramy kandydatów,
        # ale nie zapalamy statusu na zielono bez ręcznej konfiguracji ETAPU 10.
        n7_candidates = [p for p in by_id if p not in cp2102]
        self._item(
            "nextion7_candidates",
            "unknown" if n7_candidates else "missing",
            "Nextion 7 serial candidates",
            detail=", ".join(n7_candidates),
            error="needs explicit mapping" if n7_candidates else "no additional serial candidate",
            values={"candidates": n7_candidates},
        )

    def collect_usb(self) -> None:
        lsusb = self._run(["lsusb"], timeout=1.5)
        text = lsusb.get("stdout") or ""
        pokeys_hint = "PoKeys" in text or "PoLabs" in text
        cp2102_hint = "CP210" in text or "Silicon Labs" in text
        self._item("usb_lsusb", "present" if lsusb.get("ok") else "unknown", "USB inventory", detail=text[:1200] or lsusb.get("stderr", ""), values=lsusb)
        self._item("usb_pokeys_hint", "present" if pokeys_hint else "unknown", "PoKeys USB hint", detail="PoKeys/PoLabs found in lsusb" if pokeys_hint else "not identified by lsusb text")
        self._item("usb_cp2102_hint", "present" if cp2102_hint else "unknown", "CP2102 USB hint", detail="CP2102/Silicon Labs found" if cp2102_hint else "not identified by lsusb text")

    def collect_i2c(self) -> None:
        nodes = self._glob(["/dev/i2c-*"])
        self._item("i2c_nodes", "present" if nodes else "missing", "I2C device nodes", detail=", ".join(nodes), values={"nodes": nodes})

        scans: Dict[str, Any] = {}
        if shutil.which("i2cdetect"):
            for node in nodes[:4]:
                bus = node.rsplit("-", 1)[-1]
                scans[node] = self._run(["i2cdetect", "-y", bus], timeout=2.0)
        status = "present" if scans else ("unknown" if nodes else "missing")
        detail = "i2cdetect scan collected" if scans else ("i2cdetect unavailable" if nodes else "no i2c nodes")
        self._item("i2c_scan", status, "I2C address scan", detail=detail, values=scans)

    def collect_video(self) -> None:
        nodes = self._glob(["/dev/video*"])
        details: Dict[str, Any] = {"nodes": nodes}
        if shutil.which("v4l2-ctl"):
            details["v4l2_list_devices"] = self._run(["v4l2-ctl", "--list-devices"], timeout=2.0)
        self._item("video_nodes", "present" if nodes else "missing", "Camera/video devices", detail=", ".join(nodes), values=details)

    def collect_repo_markers(self) -> None:
        def rels(paths: Iterable[Path], limit: int = 12) -> List[str]:
            out = []
            for path in paths:
                try:
                    out.append(str(path.relative_to(self.repo_root)))
                except Exception:
                    out.append(str(path))
            return out[:limit]

        markers = {
            "take": rels((self.repo_root / "data" / "take").glob("*")) if (self.repo_root / "data" / "take").exists() else [],
            "par": rels(self.repo_root.glob("**/*par*")),
            "ehr": rels(self.repo_root.glob("**/*ehr*")),
            "rrp": rels(self.repo_root.glob("**/*rrp*")),
            "sok": rels(self.repo_root.glob("**/*sok*")),
            "axis": rels(list(self.repo_root.glob("**/*axis*")) + list(self.repo_root.glob("**/*step*"))),
            "pokeys_lib": rels(list(self.repo_root.glob("**/libPoKeys.so*")) + list(self.repo_root.glob("**/PoKeyslib.dll"))),
        }
        for key, values in markers.items():
            self._item(f"repo_marker_{key}", "present" if values else "missing", f"Repo marker {key}", detail=", ".join(values), values={"paths": values})

    def collect_component_truth_table(self) -> None:
        """Creates a conservative table: component -> unknown/missing/present hint.

        This is not the final green/red status. It is input for ETAP 10.
        """
        by_key = {item.key: item for item in self.items}
        component_state: Dict[str, Dict[str, Any]] = {name: {"inventory": "unknown", "reason": "not mapped yet"} for name in all_components()}

        def set_state(component: str, state: str, reason: str) -> None:
            if component in component_state:
                component_state[component] = {"inventory": state, "reason": reason}

        if by_key.get("repo_structure") and by_key["repo_structure"].status == "present":
            set_state("linux_sys", "present", "repo and runtime found")
        if by_key.get("process_tsp") and by_key["process_tsp"].status == "present":
            set_state("take_sys", "present", "TSP process/module present")
        if by_key.get("repo_marker_par") and by_key["repo_marker_par"].status == "present":
            set_state("par_sys", "present", "repo marker only, heartbeat required in ETAP 10")
        if by_key.get("repo_marker_ehr") and by_key["repo_marker_ehr"].status == "present":
            set_state("ehr_sys", "present", "repo marker only, heartbeat required in ETAP 10")
        if by_key.get("repo_marker_pokeys_lib") and by_key["repo_marker_pokeys_lib"].status == "present":
            set_state("pok_play", "unknown", "PoKeys library present, device identity required")
            set_state("pok_rec", "unknown", "PoKeys library present, device identity required")
        if by_key.get("i2c_nodes") and by_key["i2c_nodes"].status == "present":
            set_state("i2c_bus", "unknown", "I2C node exists, individual devices required")
            for c in ("lcd_1602", "matrix_led", "keypad", "light_bh1750", "level_xyz", "shock_alarm", "light_laser"):
                set_state(c, "unknown", "bus exists, address/test required")
        if by_key.get("video_nodes") and by_key["video_nodes"].status == "present":
            set_state("cam_main", "unknown", "video device exists, role mapping required")
            set_state("cam_track", "unknown", "video device exists, role mapping required")
        if by_key.get("nextion7_candidates") and by_key["nextion7_candidates"].values.get("candidates"):
            set_state("next_7", "unknown", "serial candidate exists, explicit mapping required")
        if by_key.get("repo_marker_axis") and by_key["repo_marker_axis"].status == "present":
            for c in ("kam_poz", "kam_pion", "kam_ostr", "kam_poch", "ram_poziom", "ram_pion"):
                set_state(c, "unknown", "axis config marker only, read-only driver status required")
        if by_key.get("repo_marker_sok") and by_key["repo_marker_sok"].status == "present":
            set_state("sok_poz", "unknown", "SOK marker only, real module mapping required")
            set_state("sok_pion", "unknown", "SOK marker only, real module mapping required")
        if by_key.get("repo_marker_rrp") and by_key["repo_marker_rrp"].status == "present":
            set_state("rrp", "unknown", "RRP marker only, runtime heartbeat required")

        self._item("component_truth_table", "present", "Conservative component inventory table", values=component_state)

    def collect(self) -> Dict[str, Any]:
        self.items.clear()
        self.collect_system()
        self.collect_services()
        self.collect_serial()
        self.collect_usb()
        self.collect_i2c()
        self.collect_video()
        self.collect_repo_markers()
        self.collect_component_truth_table()
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "tarzan-lks-n5-inventory-v1",
            "stage": "ETAP 9 — realna inwentaryzacja sprzętu",
            "generated_at": self.started_at,
            "repo_root": str(self.repo_root),
            "safety": {
                "step": "forbidden",
                "dir": "forbidden",
                "enable": "forbidden",
                "axis_motion": "forbidden",
                "outputs": "read-only inventory only",
            },
            "items": [asdict(item) for item in self.items],
        }

    def write(self, output_path: str | Path, data: Optional[Mapping[str, Any]] = None) -> Path:
        path = Path(output_path)
        if not path.is_absolute():
            path = self.repo_root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(data or self.to_dict())
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path


def summarize_inventory(data: Mapping[str, Any]) -> str:
    items = list(data.get("items", []))
    counts: Dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    parts = [f"{key}={counts[key]}" for key in sorted(counts)]
    return "inventory " + " ".join(parts)


def _print_table(data: Mapping[str, Any]) -> None:
    for item in data.get("items", []):
        key = str(item.get("key", ""))
        status = str(item.get("status", ""))
        label = str(item.get("label", ""))
        detail = str(item.get("detail", ""))
        print(f"{status.upper():8} {key:24} {label} {detail}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 ETAP 9 real hardware inventory")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--write", default="", help=f"Write JSON inventory, e.g. {DEFAULT_OUTPUT}")
    parser.add_argument("--print", dest="print_table", action="store_true", help="Print human-readable table")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--self-test", action="store_true", help="Collect inventory and verify JSON shape")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        inventory = TarzanTspLksInventory(repo_root=args.repo_root or None)
        data = inventory.collect()
        if args.self_test:
            if data.get("schema") != "tarzan-lks-n5-inventory-v1":
                raise RuntimeError("bad inventory schema")
            if not data.get("items"):
                raise RuntimeError("empty inventory")
        if args.write:
            path = inventory.write(args.write, data)
            print(f"WROTE {path}")
        if args.print_table:
            _print_table(data)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        print(summarize_inventory(data))
    except Exception as exc:
        print(f"BŁĄD LKS-N5 INVENTORY: {exc}", file=sys.stderr)
        return 1
    print("OK LKS-N5 INVENTORY")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
