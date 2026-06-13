from __future__ import annotations

"""TARZAN LKS-N5 — ETAP 13: realny postęp startu Linux/systemd.

Nextion 5 startuje wcześniej niż Linux, więc ``boot_loading`` pozostaje ekranem
oczekiwania w HMI. Od momentu startu usługi systemd miniPC przejmuje ekran i
pokazuje już realne kroki: system, repo, czas, sieć, usługi, porty, PoKeys,
magistrale i diagnostykę. Ten moduł nie rusza osi i nie wysyła STEP/DIR/ENABLE.
"""

import glob
import importlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from core.TSP.tarzanTspLksStatusMap import empty_statuses, bus_ok_from_statuses
from core.TSP.tarzanTspLksDiagnostics import TarzanTspLksDiagnostics
from core.TSP.tarzanTspLksHardwareTests import TarzanTspLksHardwareTests
from core.TSP.tarzanTspLksMessages import (
    SCENE_BOOT_LINUX,
    SCENE_BOOT_SERVICES,
    SCENE_BOOT_HARDWARE,
    SCENE_BOOT_TEST,
    SCENE_READY,
    SCENE_INTRO_STATUS,
    SCENE_STATUS,
)


@dataclass
class LksBootProgressResult:
    key: str
    component: str
    ok: bool
    label: str
    detail: str = ""
    error: str = ""
    progress: int = 0
    duration_ms: int = 0


class TarzanTspLksBootProgress:
    """Realny pasek przejścia z boot_loading do status_main.

    Zasada operatorska:
    - zanim Linux wystartuje, Nextion może tylko pokazywać ``boot_loading``;
    - po starcie systemd każdy kolejny procent wynika z realnego kroku;
    - brak testu albo brak urządzenia nie daje zielonego statusu.
    """

    def __init__(
        self,
        n5: object,
        repo_root: Optional[str] = None,
        pause_s: float = 0.18,
        nextion5_port: str = "",
        hardware_bridge: Optional[Any] = None,
    ) -> None:
        self.n5 = n5
        self.repo_root = Path(repo_root or self._detect_repo_root()).resolve()
        self.pause_s = max(0.0, float(pause_s))
        self.nextion5_port = str(nextion5_port or "")
        self.hardware_bridge = hardware_bridge
        self.results: List[LksBootProgressResult] = []
        self.statuses: Dict[str, bool] = empty_statuses(False)
        self._current_scene: str = ""
        self._global_progress: int = 0

    def _detect_repo_root(self) -> str:
        here = Path(__file__).resolve()
        try:
            return str(here.parents[2])
        except Exception:
            return os.getcwd()

    def _pause(self) -> None:
        if self.pause_s > 0:
            time.sleep(self.pause_s)

    def _run_cmd(self, args: List[str], timeout: float = 1.2) -> Tuple[int, str, str]:
        try:
            proc = subprocess.run(
                args,
                cwd=str(self.repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
            )
            return int(proc.returncode), proc.stdout.strip(), proc.stderr.strip()
        except Exception as exc:
            return 999, "", str(exc)

    def _systemctl_active(self, service: str) -> bool:
        rc, _, _ = self._run_cmd(["systemctl", "is-active", "--quiet", service], timeout=0.8)
        return rc == 0

    def _bridge_test(self, component: str, visible: bool = False) -> Optional[Tuple[bool, str, str]]:
        """Uruchamia test przez aktywny HardwareBridge, bez otwierania drugiej sesji PoKeys."""
        bridge = self.hardware_bridge
        if bridge is None or not hasattr(bridge, "test_lks_component"):
            return None
        try:
            result = bridge.test_lks_component(component, visible=visible)
            ok = bool(result.get("ok", False))
            detail = str(result.get("detail", "") or "")
            error = str(result.get("error", "") or "")
            return ok, detail[:180], error
        except Exception as exc:
            return False, "", str(exc)


    def _add_result(
        self,
        key: str,
        component: str,
        ok: bool,
        label: str,
        detail: str = "",
        error: str = "",
        progress: int = 0,
        start: Optional[float] = None,
    ) -> LksBootProgressResult:
        item = LksBootProgressResult(
            key=key,
            component=component,
            ok=bool(ok),
            label=label,
            detail=detail,
            error=error,
            progress=int(progress),
            duration_ms=int((time.time() - start) * 1000) if start is not None else 0,
        )
        self.results.append(item)
        if component:
            # Status zielony tylko dla konkretnego, potwierdzonego komponentu.
            # Późniejsze testy szczegółowe mogą nadpisać ten stan bardziej precyzyjnie.
            self.statuses[component] = bool(ok)
        return item

    def _show_step(self, scene: str, title: str, line1: str, line2: str, line3: str, status: str, code: str, progress: int) -> None:
        """Aktualizuje teksty i globalny postęp bez migania strony.

        Dla operatora pasek j_progress/n_progress oznacza postęp całego
        startu systemu, nie lokalny postęp pojedynczego testu. Dlatego:
        - strona Nextiona jest przełączana tylko przy zmianie sceny,
        - procent jest monotoniczny i nigdy się nie cofa,
        - wynik pojedynczego kroku zmienia tylko napisy, a nie restartuje strony.
        """
        if self._current_scene != scene:
            self.n5.page(scene)
            self._current_scene = scene

        safe_progress = max(self._global_progress, int(progress))
        self._global_progress = safe_progress

        self.n5.set_texts(
            {
                "t_title": title,
                "t_subtitle": title,
                "t_line1": line1,
                "t_line2": line2,
                "t_line3": line3,
                "t_status": status,
                "t_code": code,
            }
        )
        self.n5.set_numbers({"j_progress": safe_progress, "n_progress": safe_progress})

    def _mark_running(self, scene: str, progress: int, label: str, detail: str = "") -> None:
        if scene == SCENE_BOOT_LINUX:
            self._show_step(scene, "LINUX", label, detail, "", "checking", f"{progress}%", progress)
        elif scene == SCENE_BOOT_SERVICES:
            self._show_step(scene, "SERVICES", label, detail, "", "checking", f"{progress}%", progress)
        elif scene == SCENE_BOOT_HARDWARE:
            self._show_step(scene, "HARDWARE", label, detail, "", "checking", f"{progress}%", progress)
        elif scene == SCENE_INTRO_STATUS:
            self._show_step(scene, "INTRO STATUS", label, detail, "", "ready", f"{progress}%", progress)
        else:
            self._show_step(scene, "DEVICE TEST", label, detail, "", "checking", f"{progress}%", progress)


    def _show_ready_main(self) -> None:
        """Plansza gotowości po testach, przed intro_status i status_main.

        Kolejność operatorska po pełnym boot-checku:
        boot_test -> ready_main -> intro_status -> status_main.
        ready_main jest spokojnym ekranem GOTOWE po diagnostyce, jeszcze bez
        tablicy 30 kontrolek. Nie uruchamia żadnego testu i nie resetuje
        statusów.
        """
        green = sum(1 for value in self.statuses.values() if value)
        total = len(self.statuses)
        self.n5.page(SCENE_READY)
        self._current_scene = SCENE_READY
        self._global_progress = max(self._global_progress, 100)
        self.n5.set_texts(
            {
                "t_title": "SYSTEM READY",
                "t_subtitle": "LKS-N5 GOTOWE",
                "t_line1": "TESTY ZAKONCZONE",
                "t_line2": f"GOTOWE {green}/{total}",
                "t_line3": "PRZEJSCIE DO STATUSU",
                "t_status": "READY MAIN",
                "t_code": "100%",
            }
        )
        # ready_main ma własne pola liczbowe, nie ma klasycznego j_progress.
        # Nie wysyłamy tu j_progress/n_progress, żeby nie wywoływać Invalid Variable.
        self.n5.set_numbers({"n_test_idx": green, "n_level": 100})
        self._pause()

    def _show_status_intro(self) -> None:
        """Włącza fizyczną stronę intro_status i oddaje jej sterowanie.

        Aktualny HMI Nextion 5 ma na stronie intro_status tylko p_anim,
        va_anim i tm_anim. Nie ma tam pól t_title/t_line/j_progress.
        Dlatego Python NIE wysyła na tę stronę żadnych tekstów ani numerów.

        intro_status ma własny timer i na końcu sam wykonuje:
            page status_main

        Python ma tylko wejść na intro_status, poczekać aż animacja się
        zakończy, a potem wysłać wartości 30 kontrolek już na status_main.
        Nie wolno wymuszać page status_main z Pythona, bo to przerywa intro.
        """
        self.n5.page(SCENE_INTRO_STATUS)
        self._current_scene = SCENE_INTRO_STATUS
        self._global_progress = max(self._global_progress, 100)

        # FIZYCZNY KONTRAKT HMI:
        # intro_status ma tylko p_anim/va_anim/tm_anim i sam wykonuje
        # page status_main. W eksporcie Timer ma bazowo 250 ms, a PostInit
        # ustawia tm_anim.tim=150; przyjmujemy bezpieczny zapas 2.4 s.
        # Dzięki temu Python nie wysyła wartości status_main podczas intra,
        # co mogło dawać artefakty/ikony nakładające się w lewym górnym rogu.
        time.sleep(max(self.pause_s, 2.4))

    def _step(
        self,
        *,
        scene: str,
        progress: int,
        key: str,
        component: str,
        label: str,
        fn: Callable[[], Tuple[bool, str, str]],
    ) -> LksBootProgressResult:
        start = time.time()
        self._mark_running(scene, progress, label, "RUN")
        self._pause()
        ok, detail, error = fn()
        result = self._add_result(key, component, ok, label, detail=detail, error=error, progress=progress, start=start)
        state = "OK" if ok else "OFF"
        self._show_step(scene, label[:20], f"{label}: {state}"[:26], detail[:26], error[:26], "real boot step", f"{progress}%", progress)
        self._pause()
        return result

    # ------------------------------------------------------------------
    # Pojedyncze realne sprawdzenia
    # ------------------------------------------------------------------

    def _check_linux_alive(self) -> Tuple[bool, str, str]:
        return True, f"Python {sys.version.split()[0]} / {os.uname().nodename}", ""

    def _check_repo(self) -> Tuple[bool, str, str]:
        ok = (self.repo_root / "core" / "TSP").exists() and (self.repo_root / "hardware").exists()
        return ok, str(self.repo_root), "" if ok else "repo structure missing"

    def _check_time(self) -> Tuple[bool, str, str]:
        rc, out, err = self._run_cmd(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], timeout=0.8)
        if rc == 0:
            return bool(out.strip().lower() in {"yes", "true", "1"}), f"NTPSynchronized={out.strip()}", ""
        return True, time.strftime("%Y-%m-%d %H:%M:%S"), err

    def _check_network(self) -> Tuple[bool, str, str]:
        rc, out, err = self._run_cmd(["ip", "-o", "addr", "show", "scope", "global"], timeout=0.8)
        ok = rc == 0 and bool(out.strip())
        first = out.splitlines()[0].strip() if out.strip() else ""
        return ok, first[:120], "" if ok else (err or "no global network address")

    def _check_service_ssh(self) -> Tuple[bool, str, str]:
        ok = self._systemctl_active("ssh") or self._systemctl_active("sshd")
        return ok, "ssh/sshd active" if ok else "", "ssh not active" if not ok else ""

    def _check_tsp_module(self) -> Tuple[bool, str, str]:
        try:
            importlib.import_module("core.TSP.tarzanTsp")
            return True, "core.TSP.tarzanTsp import OK", ""
        except Exception as exc:
            return False, "", str(exc)

    def _check_lks_tty_module(self) -> Tuple[bool, str, str]:
        try:
            importlib.import_module("core.TSP.tarzanTspLks")
            return True, "LKS-TTY module OK", ""
        except Exception as exc:
            return False, "", str(exc)

    def _check_lks_n5_serial(self) -> Tuple[bool, str, str]:
        if self.nextion5_port:
            path = Path(self.nextion5_port)
            ok = path.exists()
            return ok, str(path), "" if ok else "configured port missing"
        links = sorted(glob.glob("/dev/serial/by-id/*CP210*") + glob.glob("/dev/serial/by-id/*Silicon_Labs*"))
        ok = bool(links)
        return ok, links[0] if links else "", "CP2102/Nextion5 not found" if not ok else ""

    def _check_pokeys_usb(self) -> Tuple[bool, str, str]:
        """Szybkie WYKRYCIE PoKeys PLAY/REC dla planszy boot_hardware.

        ETAP 2: boot_hardware nie uruchamia pelnego testu komponentow przez
        HardwareBridge.test_lks_component(). To miejsce tylko sprawdza, czy
        runtime widzi/utrzymuje uchwyty PLAY i REC albo czy urzadzenia PoKeys
        sa widoczne na USB. Pelny test pok_play/pok_rec zostaje dopiero w
        boot_test / LKS_TEST_MATRIX.
        """
        bridge = self.hardware_bridge
        if bridge is not None:
            try:
                if hasattr(bridge, "request_hardware_awake"):
                    bridge.request_hardware_awake(
                        source="LKS_BOOT_HARDWARE_DETECT_POKEYS",
                        grace_ms=4000,
                        ensure=True,
                        action_type="CONNECT_ONLY",
                    )
            except Exception:
                pass

            pokeys = getattr(bridge, "pokeys", None)
            if pokeys is not None:
                try:
                    play_ok = bool(pokeys.get_device("PLAY"))
                    rec_ok = bool(pokeys.get_device("REC"))
                    detail = f"detect-only PLAY={play_ok} REC={rec_ok}"
                    return play_ok and rec_ok, detail, "" if (play_ok and rec_ok) else "PoKeys detect-only did not confirm PLAY/REC"
                except Exception as exc:
                    return False, "detect-only via HardwareBridge", str(exc)

        rc, out, err = self._run_cmd(["lsusb"], timeout=1.2)
        if rc != 0:
            return False, "", err or "lsusb failed"
        has_polabs = "1dc3:1001" in out or "PoLabs" in out or "PoKeys" in out
        detail = "; ".join(line for line in out.splitlines() if "1dc3:1001" in line or "PoLabs" in line or "PoKeys" in line)
        return has_polabs, (detail or "PoKeys USB detect-only")[:180], "PoKeys USB not detected" if not has_polabs else ""

    def _check_nextion7(self) -> Tuple[bool, str, str]:
        """Sprawdza fizyczny port Nextion 7 na miniPC dla LKS-N5.

        Dwa identyczne konwertery UART nie muszą mieć czytelnego by-id z nazwą
        Nextion. Źródłem prawdy jest ustalony port by-path zapisany w
        data/lks_n5/lks_n5_hardware_requirements.json albo
        data/nextion/nextion_ports.json. Dopiero potem używamy globów jako
        awaryjnego rozpoznania.
        """
        candidates: List[str] = []
        try:
            req_path = self.repo_root / "data" / "lks_n5" / "lks_n5_hardware_requirements.json"
            if req_path.exists():
                req = json.loads(req_path.read_text(encoding="utf-8"))
                port = str(req.get("nextion7_port", "") or "")
                if port:
                    candidates.append(port)
        except Exception:
            pass
        try:
            ports_path = self.repo_root / "data" / "nextion" / "nextion_ports.json"
            if ports_path.exists():
                cfg = json.loads(ports_path.read_text(encoding="utf-8"))
                n7 = cfg.get("nextion_7", {}) if isinstance(cfg, dict) else {}
                port = str(n7.get("port", "") or "")
                enabled = bool(n7.get("enabled", True))
                if enabled and port:
                    candidates.append(port)
        except Exception:
            pass
        candidates.extend(sorted(glob.glob("/dev/serial/by-id/*Nextion*7*") + glob.glob("/dev/serial/by-id/*NX8048*")))
        candidates.extend(sorted(glob.glob("/dev/serial/by-path/*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")))
        seen = set()
        unique = []
        for item in candidates:
            if item and item not in seen:
                seen.add(item)
                unique.append(item)
        existing = [item for item in unique if Path(item).exists()]
        ok = bool(existing)
        detail = ", ".join(existing[:3] or unique[:3])
        return ok, detail, "Nextion 7 port not confirmed on miniPC" if not ok else ""

    def _check_i2c_nodes(self) -> Tuple[bool, str, str]:
        """Szybkie WYKRYCIE magistrali dla boot_hardware.

        ETAP 2: tu nie wolno wykonywac glebszych testow i2c_bus, BH1750 ani
        light_laser przez HardwareBridge.test_lks_component(), bo te same
        komponenty sa pelnie testowane pozniej w boot_test. Ten krok mowi
        tylko operatorowi: magistrala/tor bedzie testowany wlasciwie w pelnej
        macierzy.
        """
        nodes = sorted(glob.glob("/dev/i2c-*"))
        if nodes:
            return True, "detect-only linux nodes: " + ", ".join(nodes[:6]), ""

        bridge = self.hardware_bridge
        pokeys = getattr(bridge, "pokeys", None) if bridge is not None else None
        if pokeys is not None:
            try:
                connected = bool(pokeys.is_any_connected())
            except Exception:
                connected = False
            if connected:
                return True, "detect-only PoKeys connected; full BUS/I2C test in boot_test", ""

        return False, "detect-only no /dev/i2c-*; full BUS/I2C test deferred", "BUS/I2C not detected in quick stage"

    def _check_video_nodes(self) -> Tuple[bool, str, str]:
        nodes = sorted(glob.glob("/dev/video*"))
        ok = bool(nodes)
        return ok, ", ".join(nodes[:6]), "no /dev/video*" if not ok else ""

    def _check_diagnostics(self) -> Tuple[bool, str, str]:
        """Pełny test status_main przez jeden wspólny tor LKS_TEST_MATRIX.

        ETAP 3: ta metoda nie ma już własnej kopii pętli testów. Woła
        run_lks_full_matrix_via_bridge(), czyli ten sam tor, którego używa
        diagnostyka ręczna TSP. Dzięki temu boot_test i cmd_run_diagnostics
        nie rozjeżdżają kolejności, agregatu i2c_bus ani safe-state.
        """
        bridge = self.hardware_bridge
        if bridge is None or not hasattr(bridge, "test_lks_component"):
            self.statuses.update(empty_statuses(False))
            return False, "", "NO_HARDWAREBRIDGE_FOR_LKS_TEST_MATRIX"

        try:
            from core.TSP.tarzanTspLksHardwareTests import run_lks_full_matrix_via_bridge
        except Exception as exc:
            self.statuses.update(empty_statuses(False))
            return False, "", f"LKS_FULL_MATRIX_HELPER_IMPORT_FAILED: {exc}"

        def on_progress(component: str, idx: int, total: int, progress: int) -> None:
            self._mark_running(SCENE_BOOT_TEST, progress, f"MATRIX {component}", "REAL")

        def on_component_done(component: str, result: Dict[str, Any], ok: bool, progress: int) -> None:
            if component == "i2c_bus" and str(result.get("detail", "")) == "AGGREGATED_FROM_BUS_DEVICE":
                print("LKS-N5 FULL MATRIX TEST DONE component=i2c_bus ok=True AGGREGATED_FROM_BUS_DEVICE")
                return
            print(f"LKS-N5 FULL MATRIX TEST DONE component={component} ok={ok}")
            self.results.append(
                LksBootProgressResult(
                    key=f"matrix_{component}",
                    component=component,
                    ok=ok,
                    label=f"LKS matrix {component}",
                    detail=str(result.get("detail", "") or "")[:180],
                    error=str(result.get("error", "") or "")[:180],
                    progress=progress,
                )
            )

        try:
            run = run_lks_full_matrix_via_bridge(
                bridge,
                visible=True,
                batch_name="LKS_FULL_MATRIX_REAL_TESTS",
                safe_state_source="LKS_BOOT_FULL_MATRIX",
                progress_start=60,
                progress_span=30,
                on_progress=on_progress,
                on_component_done=on_component_done,
            )
        except Exception as exc:
            self.statuses.update(empty_statuses(False))
            return False, "", str(exc)

        self.statuses.update(run.statuses)
        fail_count = len([c for c in run.statuses if not self.statuses.get(c, False)])
        try:
            self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FULL MATRIX: DONE", f"OK {run.ok_count}/{run.total}", "", "real boot step", "90%", 90)
        except Exception:
            pass
        print(f"LKS-N5 FULL MATRIX TEST APPLIED statuses={run.total} ok={run.ok_count}")
        details = "; ".join(run.fail_details[:5])[:180]
        return True, f"LKS_TEST_MATRIX ok={run.ok_count}/{run.total} fail={fail_count}", details

    # ------------------------------------------------------------------    # ------------------------------------------------------------------

    def run(self) -> List[LksBootProgressResult]:
        self.results.clear()
        self.statuses = empty_statuses(False)
        self._current_scene = ""
        self._global_progress = 0
        self.n5.bkcmd(3)

        # Boot diagnostyka jest serią testów. Trzymamy hardware przez serię,
        # żeby Snajper nie robił reconnect-spinu PoKeys między komponentami.
        bridge_batch_started = False
        bridge = self.hardware_bridge
        if bridge is not None and hasattr(bridge, "begin_hardware_batch"):
            try:
                bridge.begin_hardware_batch("LKS_BOOT_DIAGNOSTICS", grace_ms=18000, ensure=False)
                bridge_batch_started = True
            except Exception:
                bridge_batch_started = False

        steps = [
            # ETAP 5: procenty odpowiadaja fazom pracy, nie sa juz jednym skokiem.
            # 0-50% = szybki start/detect, 60-90% = realny pelny test 30 komponentow,
            # 90-100% = safe/final-ready/ekrany koncowe.
            (SCENE_BOOT_LINUX, 6, "linux_alive", "linux_sys", "Linux alive", self._check_linux_alive),
            (SCENE_BOOT_LINUX, 14, "repo_structure", "linux_sys", "Repo OK", self._check_repo),
            (SCENE_BOOT_LINUX, 22, "system_time", "linux_sys", "Time OK", self._check_time),
            (SCENE_BOOT_SERVICES, 30, "network", "linux_sys", "Network OK", self._check_network),
            (SCENE_BOOT_SERVICES, 36, "ssh", "linux_sys", "SSH", self._check_service_ssh),
            (SCENE_BOOT_SERVICES, 42, "tsp_module", "take_sys", "TSP module", self._check_tsp_module),
            (SCENE_BOOT_SERVICES, 48, "lks_tty", "linux_sys", "LKS-TTY", self._check_lks_tty_module),
            # boot_hardware = szybkie wykrycie, bez ustawiania statusow ikon i bez pelnych testow komponentow.
            (SCENE_BOOT_HARDWARE, 50, "lks_n5_serial", "", "LKS-N5 serial", self._check_lks_n5_serial),
            (SCENE_BOOT_HARDWARE, 52, "pokeys_usb", "", "PoKeys USB detect", self._check_pokeys_usb),
            (SCENE_BOOT_HARDWARE, 54, "nextion7", "", "Nextion 7 detect", self._check_nextion7),
            (SCENE_BOOT_HARDWARE, 56, "pokeys_i2c_bus", "", "BUS/I2C detect", self._check_i2c_nodes),
            (SCENE_BOOT_HARDWARE, 58, "video_nodes", "", "Video detect", self._check_video_nodes),
            # boot_test = jedyny pelny test 30 komponentow LKS.
            (SCENE_BOOT_TEST, 60, "diagnostics", "linux_sys", "Full device tests", self._check_diagnostics),
        ]

        try:
            for scene, progress, key, component, label, fn in steps:
                self._step(scene=scene, progress=progress, key=key, component=component, label=label, fn=fn)
        finally:
            if bridge_batch_started and bridge is not None and hasattr(bridge, "end_hardware_batch"):
                try:
                    bridge.end_hardware_batch("LKS_BOOT_DIAGNOSTICS", grace_ms=2000)
                except Exception:
                    pass

        # ETAP 4/5: po testach i safe-state ustawiamy jeden końcowy stan
        # fizyczny. To jest ostatni zapis do LCD/Matrix/F-LED przed READY.
        self._mark_running(SCENE_BOOT_TEST, 94, "FINAL READY OUTPUTS", "LCD/MATRIX/F-LED")
        bridge = self.hardware_bridge
        if bridge is not None and hasattr(bridge, "apply_lks_final_ready_outputs"):
            try:
                final_ready = bridge.apply_lks_final_ready_outputs("LKS_BOOT_FINAL_READY")
                ok_final = bool(isinstance(final_ready, dict) and final_ready.get("ok"))
                print(f"LKS-N5 FINAL READY OUTPUTS ok={ok_final}")
                if isinstance(final_ready, dict):
                    matrix_ok = bool(final_ready.get("steps", {}).get("matrix_ready_heart", {}).get("ok"))
                    print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={matrix_ok}")
                self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FINAL READY OUTPUTS", f"OK {ok_final}", "", "ready", "98%", 98)
            except Exception as exc:
                print(f"LKS-N5 FINAL READY OUTPUTS ok=False error={exc}")
                self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FINAL READY OUTPUTS", "ERROR", str(exc)[:80], "warning", "98%", 98)
        else:
            self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FINAL READY OUTPUTS", "NO BRIDGE", "", "warning", "98%", 98)

        # Końcówka ma iść zgodnie z fizycznym układem stron operatora:
        # boot_test -> ready_main -> intro_status -> status_main.
        # Uwaga: intro_status sam przełącza na status_main timerem Nextiona.
        # Python nie robi tutaj page status_main, żeby nie przerywać animacji.
        self._show_ready_main()
        self._show_status_intro()

        # Po zakończeniu intro upewniamy się, że jesteśmy na status_main.
        # intro_status nadal ma czas skończyć animację samodzielnie, ale po
        # zapasie czasowym wolno jawnie ustawić status_main, żeby statusy ikon
        # nie trafiły w starą stronę boot/test.
        try:
            self.n5.page(SCENE_STATUS)
            self._current_scene = SCENE_STATUS
            time.sleep(max(0.15, min(0.4, self.pause_s)))
        except Exception:
            pass
        self.n5.set_many_statuses(self.statuses)
        self._apply_final_matrix_ready_heart()
        self._write_last_report()
        return list(self.results)


    def _apply_final_matrix_ready_heart(self) -> None:
        """Ostatni fizyczny zapis do Matrix LED po całym boot/status cache.

        Serce po teście matrix_led może zostać nadpisane przez późniejsze etapy
        bootu. Dlatego po ustawieniu status_main i statusów ikon wykonujemy
        ostatni zapis PoKeys w stanie POINT_TEST. Nie czyścimy i nie gasimy
        matrycy: ma zostać znak gotowości.
        """
        bridge = self.hardware_bridge
        if bridge is None:
            print("LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False detail=NO_HARDWAREBRIDGE")
            return
        pokeys = getattr(bridge, "pokeys", None)
        if pokeys is None or not hasattr(pokeys, "matrix_led_ready_heart_once"):
            print("LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False detail=NO_POKEYS_READY_HEART")
            return
        try:
            if hasattr(pokeys, "begin_point_test"):
                pokeys.begin_point_test("matrix_ready_heart_final")
            result = pokeys.matrix_led_ready_heart_once("REC")
            ok = bool(isinstance(result, dict) and result.get("ok"))
            detail = ""
            if isinstance(result, dict):
                detail = str(result.get("error") or result.get("reason") or result.get("pattern") or "")[:120]
            print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={ok} detail={detail}")
        except Exception as exc:
            print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False detail={exc}")
        finally:
            try:
                if pokeys is not None and hasattr(pokeys, "end_active_state"):
                    pokeys.end_active_state()
            except Exception:
                pass

    def _write_last_report(self) -> None:
        try:
            out_dir = self.repo_root / "data" / "lks_n5"
            out_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "ts": time.time(),
                "repo_root": str(self.repo_root),
                "statuses": self.statuses,
                "results": [asdict(item) for item in self.results],
            }
            (out_dir / "lks_n5_last_boot_progress.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass


def summarize_results(results: Iterable[LksBootProgressResult]) -> str:
    ok = sum(1 for item in results if item.ok)
    fail = sum(1 for item in results if not item.ok)
    return f"boot-progress ok={ok} off/fail={fail}"
