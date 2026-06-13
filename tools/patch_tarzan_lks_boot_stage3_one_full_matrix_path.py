from pathlib import Path

HW = Path('core/TSP/tarzanTspLksHardwareTests.py')
BOOT = Path('core/TSP/tarzanTspLksBootProgress.py')
SERVER = Path('core/TSP/tarzanTspServer.py')


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f'Nie znaleziono start_marker: {start_marker!r}')
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f'Nie znaleziono end_marker po {start_marker!r}: {end_marker!r}')
    return text[:start] + replacement + text[end:]

helper = '''

@dataclass
class LksFullMatrixRunResult:
    """Wynik jednego, wspólnego toru pełnego testu LKS_TEST_MATRIX."""

    statuses: Dict[str, bool]
    ok_count: int
    total: int
    fail_details: list[str]
    ordered_components: list[str]
    aggregated_i2c: bool = False


def run_lks_full_matrix_via_bridge(
    bridge: object,
    *,
    visible: bool = True,
    batch_name: str = "LKS_FULL_MATRIX_REAL_TESTS",
    safe_state_source: str = "LKS_FULL_MATRIX_REAL_TESTS",
    progress_start: int = 50,
    progress_span: int = 40,
    on_progress: Optional[object] = None,
    on_component_done: Optional[object] = None,
) -> LksFullMatrixRunResult:
    """JEDYNY wspólny tor pełnego testu 30 komponentów LKS w runtime.

    ETAP 3:
    - BootProgress i TspServer nie mają już własnych kopii pętli pełnych testów.
    - Oba wołają tę funkcję i dostają ten sam porządek komponentów, ten sam
      agregat i2c_bus oraz ten sam safe-state po testach.
    - Funkcja nie tworzy własnego TarzanPoKeys i nie otwiera drugiej sesji USB.
    """
    from core.TSP.tarzanTspLksStatusMap import empty_statuses, bus_ok_from_statuses
    from core.TSP.tarzanTspLksTestMatrix import MATRIX_ERRORS, components

    if bridge is None or not hasattr(bridge, "test_lks_component"):
        raise RuntimeError("NO_HARDWAREBRIDGE_FOR_LKS_TEST_MATRIX")
    if MATRIX_ERRORS:
        raise RuntimeError("BAD_TEST_MATRIX: " + "; ".join(MATRIX_ERRORS[:6]))

    statuses: Dict[str, bool] = empty_statuses(False)
    all_components = tuple(components())
    ordered_components = list(all_components)

    # light_laser musi byc przed i2c_bus, bo i2c_bus moze byc agregowany
    # z realnego ACK urzadzenia magistrali.
    for name in ("light_laser", "light_bh1750", "i2c_bus"):
        if name in ordered_components:
            ordered_components.remove(name)
    insert_at = ordered_components.index("level_xyz") + 1 if "level_xyz" in ordered_components else 0
    ordered_components[insert_at:insert_at] = [c for c in ("light_laser", "light_bh1750", "i2c_bus") if c in all_components]

    batch_started = False
    if hasattr(bridge, "begin_hardware_batch"):
        try:
            bridge.begin_hardware_batch(batch_name, grace_ms=18000, ensure=False)
            batch_started = True
        except Exception:
            batch_started = False

    ok_count = 0
    fail_details: list[str] = []
    aggregated_i2c = False
    total_ordered = max(1, len(ordered_components))

    try:
        for idx, component in enumerate(ordered_components, start=1):
            progress = int(progress_start) + int((idx / total_ordered) * int(progress_span))
            if on_progress is not None:
                on_progress(component, idx, total_ordered, progress)

            result = bridge.test_lks_component(component, visible=visible)
            ok = bool(result.get("ok", False))
            statuses[component] = ok
            if component == "light_laser" and ok:
                statuses["i2c_bus"] = True
            if ok:
                ok_count += 1
            else:
                err = str(result.get("error", "") or result.get("detail", "") or "FAIL")
                fail_details.append(f"{component}:{err[:40]}")

            if on_component_done is not None:
                on_component_done(component, result, ok, progress)

        if bus_ok_from_statuses(statuses) and not statuses.get("i2c_bus", False):
            statuses["i2c_bus"] = True
            ok_count += 1
            aggregated_i2c = True
            if on_component_done is not None:
                on_component_done("i2c_bus", {"ok": True, "detail": "AGGREGATED_FROM_BUS_DEVICE"}, True, int(progress_start) + int(progress_span))

        return LksFullMatrixRunResult(
            statuses=statuses,
            ok_count=ok_count,
            total=len(all_components),
            fail_details=fail_details,
            ordered_components=ordered_components,
            aggregated_i2c=aggregated_i2c,
        )
    finally:
        if batch_started and hasattr(bridge, "end_hardware_batch"):
            try:
                bridge.end_hardware_batch(batch_name, grace_ms=2000)
            except Exception:
                pass
        if safe_state_source and hasattr(bridge, "apply_lks_test_safe_state"):
            try:
                bridge.apply_lks_test_safe_state(safe_state_source)
            except Exception:
                pass
'''

new_boot_check = '''    def _check_diagnostics(self) -> Tuple[bool, str, str]:
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
                progress_start=50,
                progress_span=40,
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

'''

new_server_matrix = '''    def _run_lks_n5_full_test_matrix(self, *, visible: bool = True) -> Dict[str, bool]:
        """Uruchamia pełny test 30 ikon LKS-N5 przez wspólny tor ETAPU 3."""
        try:
            from core.TSP.tarzanTspLksHardwareTests import run_lks_full_matrix_via_bridge
        except Exception as exc:
            raise RuntimeError(f"LKS_FULL_MATRIX_HELPER_IMPORT_FAILED: {exc}") from exc

        hw_bridge = getattr(self, "hw_bridge", None)
        if hw_bridge is None or not hasattr(hw_bridge, "test_lks_component"):
            raise RuntimeError("NO_HARDWAREBRIDGE_FOR_LKS_TEST_MATRIX")

        def on_component_done(component: str, result: Dict[str, Any], ok: bool, progress: int) -> None:
            detail = str(result.get("detail", "") or result.get("error", "") or "")
            if component == "i2c_bus" and detail == "AGGREGATED_FROM_BUS_DEVICE":
                self.logger.info("LKS-N5 FULL MATRIX TEST DONE component=i2c_bus ok=True AGGREGATED_FROM_BUS_DEVICE")
            else:
                self.logger.info("LKS-N5 FULL MATRIX TEST DONE component=%s ok=%s %s", component, ok, detail[:220])

        run = run_lks_full_matrix_via_bridge(
            hw_bridge,
            visible=visible,
            batch_name="LKS_FULL_MATRIX_REAL_TESTS",
            safe_state_source="LKS_FULL_MATRIX_REAL_TESTS",
            progress_start=50,
            progress_span=40,
            on_component_done=on_component_done,
        )
        self.logger.info("LKS-N5 FULL MATRIX TEST APPLIED statuses=%d ok=%d", run.total, run.ok_count)
        return run.statuses

'''


def patch_hw():
    text = HW.read_text(encoding='utf-8')
    if 'class LksFullMatrixRunResult' in text and 'def run_lks_full_matrix_via_bridge' in text:
        return False
    marker = '\n\nclass TarzanTspLksHardwareTests:'
    if marker not in text:
        raise SystemExit('Nie znaleziono klasy TarzanTspLksHardwareTests')
    text = text.replace(marker, helper + marker, 1)
    HW.write_text(text, encoding='utf-8')
    return True


def patch_boot():
    text = BOOT.read_text(encoding='utf-8')
    if 'run_lks_full_matrix_via_bridge(' in text and 'ETAP 3: ta metoda nie ma już własnej kopii' in text:
        return False
    text = replace_between(text, '    def _check_diagnostics', '    # ------------------------------------------------------------------', new_boot_check + '    # ------------------------------------------------------------------')
    BOOT.write_text(text, encoding='utf-8')
    return True


def patch_server():
    text = SERVER.read_text(encoding='utf-8')
    if 'wspólny tor ETAPU 3' in text and 'run_lks_full_matrix_via_bridge' in text:
        return False
    text = replace_between(text, '    def _run_lks_n5_full_test_matrix', '    def _run_diagnostics', new_server_matrix)
    SERVER.write_text(text, encoding='utf-8')
    return True

changed = []
if patch_hw(): changed.append(str(HW))
if patch_boot(): changed.append(str(BOOT))
if patch_server(): changed.append(str(SERVER))
print('OK: ETAP 3 jeden wspolny tor pelnego testu LKS; changed=' + ', '.join(changed))
