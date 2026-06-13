from pathlib import Path

TARGET = Path('core/TSP/tarzanTspLksBootProgress.py')


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f'Nie znaleziono start_marker: {start_marker!r}')
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f'Nie znaleziono end_marker po {start_marker!r}: {end_marker!r}')
    return text[:start] + replacement + text[end:]


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f'Brak pliku: {TARGET}')
    text = TARGET.read_text(encoding='utf-8')
    original = text

    new_pokeys = '''    def _check_pokeys_usb(self) -> Tuple[bool, str, str]:
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

'''
    text = replace_between(text, '    def _check_pokeys_usb', '    def _check_nextion7', new_pokeys)

    new_i2c = '''    def _check_i2c_nodes(self) -> Tuple[bool, str, str]:
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

'''
    text = replace_between(text, '    def _check_i2c_nodes', '    def _check_video_nodes', new_i2c)

    text = text.replace(
        '                progress = 88 + int((idx / total) * 10)',
        '                progress = 50 + int((idx / total) * 40)',
    )
    text = text.replace(
        'self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FULL MATRIX: DONE", f"OK {ok_count}/{len(all_components)}", "", "real boot step", "100%", 100)',
        'self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FULL MATRIX: DONE", f"OK {ok_count}/{len(all_components)}", "", "real boot step", "90%", 90)',
    )

    old_steps = '''        steps = [
            (SCENE_BOOT_LINUX, 10, "linux_alive", "linux_sys", "Linux alive", self._check_linux_alive),
            (SCENE_BOOT_LINUX, 20, "repo_structure", "linux_sys", "Repo OK", self._check_repo),
            (SCENE_BOOT_LINUX, 30, "system_time", "linux_sys", "Time OK", self._check_time),
            (SCENE_BOOT_SERVICES, 40, "network", "linux_sys", "Network OK", self._check_network),
            (SCENE_BOOT_SERVICES, 50, "ssh", "linux_sys", "SSH", self._check_service_ssh),
            (SCENE_BOOT_SERVICES, 58, "tsp_module", "take_sys", "TSP module", self._check_tsp_module),
            (SCENE_BOOT_SERVICES, 62, "lks_tty", "linux_sys", "LKS-TTY", self._check_lks_tty_module),
            (SCENE_BOOT_HARDWARE, 68, "lks_n5_serial", "linux_sys", "LKS-N5 serial", self._check_lks_n5_serial),
            (SCENE_BOOT_HARDWARE, 74, "pokeys_usb", "pok_play", "PoKeys USB", self._check_pokeys_usb),
            (SCENE_BOOT_HARDWARE, 78, "nextion7", "next_7", "Nextion 7", self._check_nextion7),
            (SCENE_BOOT_HARDWARE, 82, "pokeys_i2c_bus", "i2c_bus", "PoKeys BUS/I2C", self._check_i2c_nodes),
            (SCENE_BOOT_HARDWARE, 86, "video_nodes", "cam_main", "Video nodes", self._check_video_nodes),
            (SCENE_BOOT_TEST, 94, "diagnostics", "linux_sys", "Real diagnostics", self._check_diagnostics),
        ]'''
    new_steps = '''        steps = [
            (SCENE_BOOT_LINUX, 8, "linux_alive", "linux_sys", "Linux alive", self._check_linux_alive),
            (SCENE_BOOT_LINUX, 16, "repo_structure", "linux_sys", "Repo OK", self._check_repo),
            (SCENE_BOOT_LINUX, 24, "system_time", "linux_sys", "Time OK", self._check_time),
            (SCENE_BOOT_SERVICES, 32, "network", "linux_sys", "Network OK", self._check_network),
            (SCENE_BOOT_SERVICES, 38, "ssh", "linux_sys", "SSH", self._check_service_ssh),
            (SCENE_BOOT_SERVICES, 44, "tsp_module", "take_sys", "TSP module", self._check_tsp_module),
            (SCENE_BOOT_SERVICES, 48, "lks_tty", "linux_sys", "LKS-TTY", self._check_lks_tty_module),
            # boot_hardware = szybkie wykrycie, bez ustawiania statusow ikon i bez pelnych testow komponentow.
            (SCENE_BOOT_HARDWARE, 50, "lks_n5_serial", "", "LKS-N5 serial", self._check_lks_n5_serial),
            (SCENE_BOOT_HARDWARE, 50, "pokeys_usb", "", "PoKeys USB detect", self._check_pokeys_usb),
            (SCENE_BOOT_HARDWARE, 50, "nextion7", "", "Nextion 7 detect", self._check_nextion7),
            (SCENE_BOOT_HARDWARE, 50, "pokeys_i2c_bus", "", "BUS/I2C detect", self._check_i2c_nodes),
            (SCENE_BOOT_HARDWARE, 50, "video_nodes", "", "Video detect", self._check_video_nodes),
            # boot_test = jedyny pelny test 30 komponentow LKS.
            (SCENE_BOOT_TEST, 50, "diagnostics", "linux_sys", "Full device tests", self._check_diagnostics),
        ]'''
    if old_steps not in text and new_steps not in text:
        raise SystemExit('Nie znaleziono oczekiwanego bloku steps do podmiany')
    text = text.replace(old_steps, new_steps)

    if text == original:
        print('OK: patch juz byl zastosowany albo brak zmian')
    else:
        TARGET.write_text(text, encoding='utf-8')
        print('OK: boot_hardware rozdzielony od boot_test; pelne testy zostaja w boot_test')


if __name__ == '__main__':
    main()
