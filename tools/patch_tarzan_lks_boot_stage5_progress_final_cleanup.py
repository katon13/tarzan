from pathlib import Path


def patch_boot_progress(root: Path) -> bool:
    path = root / "core" / "TSP" / "tarzanTspLksBootProgress.py"
    text = path.read_text(encoding="utf-8")
    changed = False

    old_steps = '        steps = [\n            (SCENE_BOOT_LINUX, 8, "linux_alive", "linux_sys", "Linux alive", self._check_linux_alive),\n            (SCENE_BOOT_LINUX, 16, "repo_structure", "linux_sys", "Repo OK", self._check_repo),\n            (SCENE_BOOT_LINUX, 24, "system_time", "linux_sys", "Time OK", self._check_time),\n            (SCENE_BOOT_SERVICES, 32, "network", "linux_sys", "Network OK", self._check_network),\n            (SCENE_BOOT_SERVICES, 38, "ssh", "linux_sys", "SSH", self._check_service_ssh),\n            (SCENE_BOOT_SERVICES, 44, "tsp_module", "take_sys", "TSP module", self._check_tsp_module),\n            (SCENE_BOOT_SERVICES, 48, "lks_tty", "linux_sys", "LKS-TTY", self._check_lks_tty_module),\n            # boot_hardware = szybkie wykrycie, bez ustawiania statusow ikon i bez pelnych testow komponentow.\n            (SCENE_BOOT_HARDWARE, 50, "lks_n5_serial", "", "LKS-N5 serial", self._check_lks_n5_serial),\n            (SCENE_BOOT_HARDWARE, 50, "pokeys_usb", "", "PoKeys USB detect", self._check_pokeys_usb),\n            (SCENE_BOOT_HARDWARE, 50, "nextion7", "", "Nextion 7 detect", self._check_nextion7),\n            (SCENE_BOOT_HARDWARE, 50, "pokeys_i2c_bus", "", "BUS/I2C detect", self._check_i2c_nodes),\n            (SCENE_BOOT_HARDWARE, 50, "video_nodes", "", "Video detect", self._check_video_nodes),\n            # boot_test = jedyny pelny test 30 komponentow LKS.\n            (SCENE_BOOT_TEST, 50, "diagnostics", "linux_sys", "Full device tests", self._check_diagnostics),\n        ]\n'
    new_steps = '        steps = [\n            # ETAP 5: procenty odpowiadaja fazom pracy, nie sa juz jednym skokiem.\n            # 0-50% = szybki start/detect, 60-90% = realny pelny test 30 komponentow,\n            # 90-100% = safe/final-ready/ekrany koncowe.\n            (SCENE_BOOT_LINUX, 6, "linux_alive", "linux_sys", "Linux alive", self._check_linux_alive),\n            (SCENE_BOOT_LINUX, 14, "repo_structure", "linux_sys", "Repo OK", self._check_repo),\n            (SCENE_BOOT_LINUX, 22, "system_time", "linux_sys", "Time OK", self._check_time),\n            (SCENE_BOOT_SERVICES, 30, "network", "linux_sys", "Network OK", self._check_network),\n            (SCENE_BOOT_SERVICES, 36, "ssh", "linux_sys", "SSH", self._check_service_ssh),\n            (SCENE_BOOT_SERVICES, 42, "tsp_module", "take_sys", "TSP module", self._check_tsp_module),\n            (SCENE_BOOT_SERVICES, 48, "lks_tty", "linux_sys", "LKS-TTY", self._check_lks_tty_module),\n            # boot_hardware = szybkie wykrycie, bez ustawiania statusow ikon i bez pelnych testow komponentow.\n            (SCENE_BOOT_HARDWARE, 50, "lks_n5_serial", "", "LKS-N5 serial", self._check_lks_n5_serial),\n            (SCENE_BOOT_HARDWARE, 52, "pokeys_usb", "", "PoKeys USB detect", self._check_pokeys_usb),\n            (SCENE_BOOT_HARDWARE, 54, "nextion7", "", "Nextion 7 detect", self._check_nextion7),\n            (SCENE_BOOT_HARDWARE, 56, "pokeys_i2c_bus", "", "BUS/I2C detect", self._check_i2c_nodes),\n            (SCENE_BOOT_HARDWARE, 58, "video_nodes", "", "Video detect", self._check_video_nodes),\n            # boot_test = jedyny pelny test 30 komponentow LKS.\n            (SCENE_BOOT_TEST, 60, "diagnostics", "linux_sys", "Full device tests", self._check_diagnostics),\n        ]\n'
    if old_steps in text:
        text = text.replace(old_steps, new_steps, 1)
        changed = True

    old_progress = """                progress_start=50,\n                progress_span=40,\n"""
    new_progress = """                progress_start=60,\n                progress_span=30,\n"""
    if old_progress in text:
        text = text.replace(old_progress, new_progress, 1)
        changed = True

    old_final = '        # ETAP 4: po testach i safe-state ustawiamy jeden końcowy stan\n        # fizyczny. To jest ostatni zapis do LCD/Matrix/F-LED przed READY.\n        bridge = self.hardware_bridge\n        if bridge is not None and hasattr(bridge, "apply_lks_final_ready_outputs"):\n            try:\n                final_ready = bridge.apply_lks_final_ready_outputs("LKS_BOOT_FINAL_READY")\n                ok_final = bool(isinstance(final_ready, dict) and final_ready.get("ok"))\n                print(f"LKS-N5 FINAL READY OUTPUTS ok={ok_final}")\n                if isinstance(final_ready, dict):\n                    matrix_ok = bool(final_ready.get("steps", {}).get("matrix_ready_heart", {}).get("ok"))\n                    print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={matrix_ok}")\n            except Exception as exc:\n                print(f"LKS-N5 FINAL READY OUTPUTS ok=False error={exc}")\n\n        # Końcówka ma iść zgodnie z fizycznym układem stron operatora:\n'
    new_final = '        # ETAP 4/5: po testach i safe-state ustawiamy jeden końcowy stan\n        # fizyczny. To jest ostatni zapis do LCD/Matrix/F-LED przed READY.\n        self._mark_running(SCENE_BOOT_TEST, 94, "FINAL READY OUTPUTS", "LCD/MATRIX/F-LED")\n        bridge = self.hardware_bridge\n        if bridge is not None and hasattr(bridge, "apply_lks_final_ready_outputs"):\n            try:\n                final_ready = bridge.apply_lks_final_ready_outputs("LKS_BOOT_FINAL_READY")\n                ok_final = bool(isinstance(final_ready, dict) and final_ready.get("ok"))\n                print(f"LKS-N5 FINAL READY OUTPUTS ok={ok_final}")\n                if isinstance(final_ready, dict):\n                    matrix_ok = bool(final_ready.get("steps", {}).get("matrix_ready_heart", {}).get("ok"))\n                    print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={matrix_ok}")\n                self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FINAL READY OUTPUTS", f"OK {ok_final}", "", "ready", "98%", 98)\n            except Exception as exc:\n                print(f"LKS-N5 FINAL READY OUTPUTS ok=False error={exc}")\n                self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FINAL READY OUTPUTS", "ERROR", str(exc)[:80], "warning", "98%", 98)\n        else:\n            self._show_step(SCENE_BOOT_TEST, "DEVICE TEST", "FINAL READY OUTPUTS", "NO BRIDGE", "", "warning", "98%", 98)\n\n        # Końcówka ma iść zgodnie z fizycznym układem stron operatora:\n'
    if old_final in text:
        text = text.replace(old_final, new_final, 1)
        changed = True

    if not changed:
        if "ETAP 5: procenty odpowiadaja fazom pracy" in text and "98%" in text:
            return False
        raise SystemExit("PATCH FAILED: no Stage 5 markers matched in tarzanTspLksBootProgress.py")
    path.write_text(text, encoding="utf-8")
    return True


def patch_tsp_server_progress_defaults(root: Path) -> bool:
    path = root / "core" / "TSP" / "tarzanTspServer.py"
    text = path.read_text(encoding="utf-8")
    old = """            progress_start=50,\n            progress_span=40,\n"""
    new = """            progress_start=60,\n            progress_span=30,\n"""
    if old not in text:
        return False
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    root = Path.cwd()
    changed = []
    if patch_boot_progress(root):
        changed.append("core/TSP/tarzanTspLksBootProgress.py")
    if patch_tsp_server_progress_defaults(root):
        changed.append("core/TSP/tarzanTspServer.py")
    print("OK: ETAP 5 progress/final-ready uporzadkowany; changed=" + (", ".join(changed) if changed else "none"))


if __name__ == "__main__":
    main()
