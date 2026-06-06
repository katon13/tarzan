from __future__ import annotations

"""TARZAN LKS-N5 — warstwa scen Nextion 5.

Ten moduł mapuje znaczenia LKS na strony i pola Nextion 5.
Nie diagnozuje sprzętu, nie steruje ruchem, nie wysyła STEP/DIR/ENABLE.
Diagnostyka będzie w osobnym etapie. Tu jest tylko wyświetlanie.
"""

import argparse
import sys
import time
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

try:
    from hardware.tarzanNextion.lks_n5_device import TarzanLksN5Device
except Exception as exc:  # pragma: no cover
    TarzanLksN5Device = None  # type: ignore
    _DEVICE_IMPORT_ERROR = exc
else:
    _DEVICE_IMPORT_ERROR = None

from core.TSP.tarzanTspLksMessages import (
    BOOT_PROGRESS_HARDWARE,
    BOOT_PROGRESS_LINUX,
    BOOT_PROGRESS_READY,
    BOOT_PROGRESS_SERVICES,
    BOOT_PROGRESS_TEST,
    CODE_ERROR,
    CODE_READY,
    CODE_TAKE,
    CODE_WARN,
    ERR_UNKNOWN,
    LEVEL_ERROR,
    LEVEL_OK,
    LEVEL_WARN,
    SCENE_BOOT_HARDWARE,
    SCENE_BOOT_LINUX,
    SCENE_BOOT_SERVICES,
    SCENE_BOOT_TEST,
    SCENE_ERROR,
    SCENE_INTRO_STATUS,
    SCENE_READY,
    SCENE_STATUS,
    SCENE_TAKE,
    SCENE_WARN,
)

from core.TSP.tarzanTspLksStatusMap import all_components, validate_component
from core.TSP.tarzanTspLksDiagnostics import TarzanTspLksDiagnostics


class TarzanTspLksNextion5:
    """Warstwa wizualna LKS-N5.

    Przyjmuje gotowe znaczenia: strona, tekst, status kontrolki.
    Nie sprawdza realnego hardware i nie podejmuje decyzji diagnostycznych.
    """

    def __init__(
        self,
        device: Optional[object] = None,
        port: str = "",
        baudrate: int = 9600,
        timeout: float = 0.2,
        dry_run: bool = False,
        command_delay_s: float = 0.03,
    ) -> None:
        if device is None:
            if TarzanLksN5Device is None:
                raise RuntimeError(f"Brak TarzanLksN5Device: {_DEVICE_IMPORT_ERROR}")
            device = TarzanLksN5Device(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                dry_run=dry_run,
            )
        self.device = device
        self.command_delay_s = float(command_delay_s)
        self.last_scene: str = ""
        self.last_status: Dict[str, bool] = {}
        self.last_error: str = ""

    def connect(self) -> None:
        connect = getattr(self.device, "connect", None)
        if callable(connect):
            connect()

    def close(self) -> None:
        close = getattr(self.device, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> "TarzanTspLksNextion5":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _sleep(self) -> None:
        if self.command_delay_s > 0:
            time.sleep(self.command_delay_s)

    def page(self, name: str) -> None:
        getattr(self.device, "page")(name)
        self.last_scene = name
        self._sleep()

    def txt(self, component: str, value: str) -> None:
        getattr(self.device, "txt")(component, value)
        self._sleep()

    def val(self, component: str, value: int) -> None:
        getattr(self.device, "val")(component, int(value))
        self._sleep()

    def set_texts(self, values: Mapping[str, str]) -> None:
        for component, value in values.items():
            self.txt(component, str(value))

    def set_numbers(self, values: Mapping[str, int]) -> None:
        for component, value in values.items():
            self.val(component, int(value))

    def bkcmd(self, level: int = 3) -> None:
        getattr(self.device, "bkcmd")(int(level))
        self._sleep()


    def read_events(self) -> List[object]:
        """Odczytuje dostępne eventy z Nextiona bez blokowania pętli TSP."""
        poll = getattr(self.device, "poll_events", None)
        if callable(poll):
            return list(poll())
        return []

    def blink_component(self, component: str, base_value: Optional[bool] = None, cycles: int = 3, delay_s: float = 0.12) -> None:
        """Krótko mruga jednym elementem podczas testu punktowego operatora."""
        name = validate_component(component)
        if base_value is None:
            base_value = bool(self.last_status.get(name, False))
        for _ in range(max(1, int(cycles))):
            self.val(name, 0 if base_value else 1)
            time.sleep(max(0.02, float(delay_s)))
            self.val(name, 1 if base_value else 0)
            time.sleep(max(0.02, float(delay_s)))

    def test_component(self, component: str, diagnostics: Optional[TarzanTspLksDiagnostics] = None) -> bool:
        """Testuje jedno ogniwo po kliknięciu przycisku na status_main.

        W czasie testu mruga tylko kliknięty element. Po teście wraca:
        - ``.val=1`` gdy test OK,
        - ``.val=0`` gdy test niepotwierdzony albo FAIL.
        """
        name = validate_component(component)
        base = bool(self.last_status.get(name, False))
        self.blink_component(name, base_value=base)
        diag = diagnostics or TarzanTspLksDiagnostics()
        diag.run_component(name, operator_visible=True)
        ok = bool(diag.status_map().get(name, False))
        self.set_status(name, ok)
        return ok

    def show_boot_linux(self) -> None:
        self.page(SCENE_BOOT_LINUX)
        self.set_texts(
            {
                "t_title": "LINUX OK",
                "t_subtitle": "LINUX OK",
                "t_line1": "SYSTEM STARTED",
                "t_line2": "STARTING SERVICES",
                "t_line3": "",
                "t_status": "LKS-N5 ONLINE",
                "t_code": "",
            }
        )
        self.set_numbers({"j_progress": BOOT_PROGRESS_LINUX, "n_progress": BOOT_PROGRESS_LINUX})

    def show_services(
        self,
        ssh: str = "SSH: OK",
        tsp: str = "TSP: STARTING",
        lks: str = "LKS: OK",
        status: str = "checking...",
    ) -> None:
        self.page(SCENE_BOOT_SERVICES)
        self.set_texts(
            {
                "t_title": "SERVICES",
                "t_subtitle": "SERVICES",
                "t_line1": ssh,
                "t_line2": tsp,
                "t_line3": lks,
                "t_status": status,
                "t_code": "",
            }
        )
        self.set_numbers({"j_progress": BOOT_PROGRESS_SERVICES, "n_progress": BOOT_PROGRESS_SERVICES})

    def show_hardware(
        self,
        line1: str = "PLAY: SCAN...",
        line2: str = "REC: SCAN...",
        line3: str = "PoKeysLib: OK",
        status: str = "checking bus...",
    ) -> None:
        self.page(SCENE_BOOT_HARDWARE)
        self.set_texts(
            {
                "t_title": "HARDWARE CHECK",
                "t_subtitle": "POKEYS CHECK",
                "t_line1": line1,
                "t_line2": line2,
                "t_line3": line3,
                "t_status": status,
                "t_code": "",
            }
        )
        self.set_numbers({"j_progress": BOOT_PROGRESS_HARDWARE, "n_progress": BOOT_PROGRESS_HARDWARE})

    def show_test(
        self,
        code: str = "TEST 01/08",
        line1: str = "LCD: TEST",
        line2: str = "MATRIX: WAIT",
        line3: str = "F1 LED: WAIT",
        status: str = "running whitelist tests",
    ) -> None:
        self.page(SCENE_BOOT_TEST)
        self.set_texts(
            {
                "t_title": "DEVICE TEST",
                "t_subtitle": "DEVICE TEST",
                "t_line1": line1,
                "t_line2": line2,
                "t_line3": line3,
                "t_status": status,
                "t_code": code,
            }
        )
        self.set_numbers({"j_progress": BOOT_PROGRESS_TEST, "n_progress": BOOT_PROGRESS_TEST})

    def show_intro_status(self) -> None:
        self.page(SCENE_INTRO_STATUS)

    def show_ready(self) -> None:
        self.page(SCENE_READY)
        self.set_texts(
            {
                "t_title": "SYSTEM READY",
                "t_subtitle": "TARZAN NODE",
                "t_line1": "SYSTEM READY",
                "t_line2": "TSP: OK   PAR: WAIT",
                "t_line3": "PLAY: OK  REC: OK",
                "t_status": "LKS-N5 READY",
                "t_code": CODE_READY,
            }
        )
        self.set_numbers({"n_level": LEVEL_OK, "n_test_idx": 0})

    def show_status(self, reset: bool = False) -> None:
        self.page(SCENE_STATUS)
        if reset:
            self.reset_status_main()

    def show_warn(
        self,
        title: str = "WARNING",
        line1: str = "NEXTION 7 LOST",
        line2: str = "CHECK USB PORT",
        code: str = "N7_OFFLINE",
        status: str = "system still running",
        line3: str = "",
    ) -> None:
        self.page(SCENE_WARN)
        self.set_texts(
            {
                "t_title": title,
                "t_subtitle": "WARNING",
                "t_line1": line1,
                "t_line2": line2,
                "t_line3": line3 or code,
                "t_status": status,
                "t_code": code or CODE_WARN,
            }
        )
        self.set_numbers({"n_level": LEVEL_WARN})

    def show_error(
        self,
        title: str = "ERROR",
        line1: str = "HARDWARE ERROR",
        line2: str = "CHECK SYSTEM",
        code: str = ERR_UNKNOWN,
        status: str = "operator action required",
        line3: str = "",
    ) -> None:
        self.page(SCENE_ERROR)
        self.set_texts(
            {
                "t_title": title,
                "t_subtitle": "ERROR",
                "t_line1": line1,
                "t_line2": line2,
                "t_line3": line3 or code,
                "t_status": status,
                "t_code": code or CODE_ERROR,
            }
        )
        self.set_numbers({"n_level": LEVEL_ERROR})

    def show_take(
        self,
        take: str = "TAKE: WAIT",
        tc: str = "TC: 00:00:00:00",
        clap: str = "CLAP: WAIT",
        status: str = "marker standby",
    ) -> None:
        self.page(SCENE_TAKE)
        self.set_texts(
            {
                "t_title": "TAKE",
                "t_subtitle": "TARZAN NODE",
                "t_line1": take,
                "t_line2": tc,
                "t_line3": clap,
                "t_status": status,
                "t_code": CODE_TAKE,
            }
        )

    def set_status(self, component: str, ok: bool) -> None:
        name = validate_component(str(component or "").strip())
        self.val(name, 1 if ok else 0)
        self.last_status[name] = bool(ok)

    def set_many_statuses(self, statuses: Mapping[str, bool]) -> None:
        for component, ok in statuses.items():
            self.set_status(component, bool(ok))


    def set_poksyg_last_forced_status(self, signal: str, value: object, ack_ok: bool, message: str = "") -> None:
        """Pokazuje trwały status ostatniego wymuszonego sygnału POKSYG na istniejącej kontrolce.

        Aktualny eksport Nextion 5 status_main ma wyłącznie 30 dual-state buttonów,
        bez osobnego dolnego pola tekstowego. Nie wysyłamy więc komend do
        nieistniejących komponentów. Używamy istniejącej kontrolki pok_play:
        - .val pokazuje OK/ERROR,
        - .txt trzyma krótki opis ostatniego ACK.
        Po dodaniu pola tekstowego w HMI można rozszerzyć tę metodę bez zmiany toru.
        """
        sig = str(signal or "").strip()
        val = str(value)
        ok_txt = "OK" if bool(ack_ok) else "ERR"
        if sig == "play_p37_step_disconnect_manual":
            short = f"P37={val} {ok_txt}"
        else:
            short = f"{sig[:8]}={val} {ok_txt}"
        try:
            self.set_status("pok_play", bool(ack_ok))
        except Exception:
            pass
        try:
            self.txt("pok_play", short[:20])
        except Exception:
            pass

    def reset_status_main(self, components: Optional[Iterable[str]] = None) -> None:
        for component in components or all_components():
            self.set_status(str(component), False)

    def run_scene_demo(self, include_status: bool = True) -> None:
        """Test ETAPU 3: przejście po scenach i zapalenie kilku kontrolek."""
        self.bkcmd(3)
        self.show_boot_linux()
        self.show_services(tsp="TSP: OK", status="services OK")
        self.show_hardware(line1="PLAY: OK", line2="REC: OK", status="hardware OK")
        self.show_test(
            code="TEST 08/08",
            line1="LCD: OK",
            line2="MATRIX: OK",
            line3="F1-F4 LED: OK",
            status="safe tests OK",
        )
        self.show_ready()
        if include_status:
            self.show_status(reset=True)
            self.set_many_statuses(
                {
                    "linux_sys": True,
                    "pok_play": True,
                    "pok_rec": True,
                    "i2c_bus": True,
                    "take_sys": True,
                }
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARZAN LKS-N5 / Nextion 5 scene layer")
    parser.add_argument("--port", default="", help="Port Nextion 5, najlepiej /dev/serial/by-id/...")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delay", type=float, default=0.03, help="Opóźnienie między komendami")
    parser.add_argument("--test-scenes", action="store_true", help="Demo ETAPU 3 po scenach")
    parser.add_argument("--boot-check", action="store_true", help="ETAP 5: realny, bezpieczny boot-check miniPC")
    parser.add_argument("--diagnostics", action="store_true", help="ETAP 6: diagnostyka podzespołów status_main")
    parser.add_argument("--print-results", action="store_true", help="Wypisz wyniki diagnostyki ETAPU 6")
    parser.add_argument(
        "--scene",
        choices=["linux", "services", "hardware", "test", "ready", "status", "warn", "error", "take"],
    )
    parser.add_argument("--set", action="append", default=[], help="Status kontrolki: nazwa=0/1, można podać wiele razy")
    parser.add_argument("--reset-status", action="store_true")
    return parser


def _parse_status_assignments(values: Iterable[str]) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Status wymaga formatu nazwa=0/1: {item}")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip().lower()
        out[key] = raw_value in {"1", "true", "yes", "on", "ok"}
    return out


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not args.dry_run and not args.port:
        print("BŁĄD: podaj --port albo użyj --dry-run", file=sys.stderr)
        return 2

    try:
        with TarzanTspLksNextion5(
            port=args.port,
            baudrate=args.baudrate,
            timeout=args.timeout,
            dry_run=args.dry_run,
            command_delay_s=args.delay,
        ) as n5:
            if args.boot_check:
                from core.TSP.tarzanTspLksBootCheck import TarzanTspLksBootCheck

                TarzanTspLksBootCheck(n5).run()
            elif args.diagnostics:
                from core.TSP.tarzanTspLksDiagnostics import (
                    TarzanTspLksDiagnostics,
                    apply_diagnostics_to_n5,
                    summarize_results,
                    _print_results,
                )

                diagnostics = TarzanTspLksDiagnostics()
                results = apply_diagnostics_to_n5(n5, diagnostics)
                if args.print_results:
                    _print_results(results)
                print(summarize_results(results))
            elif args.test_scenes:
                n5.run_scene_demo()
            elif args.scene == "linux":
                n5.show_boot_linux()
            elif args.scene == "services":
                n5.show_services()
            elif args.scene == "hardware":
                n5.show_hardware()
            elif args.scene == "test":
                n5.show_test()
            elif args.scene == "ready":
                n5.show_ready()
            elif args.scene == "status":
                n5.show_status(reset=args.reset_status)
            elif args.scene == "warn":
                n5.show_warn()
            elif args.scene == "error":
                n5.show_error()
            elif args.scene == "take":
                n5.show_take()

            statuses = _parse_status_assignments(args.set)
            if statuses:
                n5.set_many_statuses(statuses)
    except Exception as exc:
        print(f"BŁĄD LKS-N5 SCENES: {exc}", file=sys.stderr)
        return 1

    print("OK LKS-N5 SCENES")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
