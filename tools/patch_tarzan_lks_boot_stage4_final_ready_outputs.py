from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"PATCH FAILED: marker not found: {label}")
    return text.replace(old, new, 1)


def ensure_matrix_ready_method(root: Path) -> bool:
    path = root / "core" / "tarzanPoKeys.py"
    text = path.read_text(encoding="utf-8")
    if "def matrix_led_ready_heart_once" in text:
        return False
    marker = '''    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:\n        if not visible:\n            return {"ok": self.test_board_once(board), "board": board}\n        cols = self._matrix_text_columns("OK")\n        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))\n        time.sleep(0.20)\n        self.matrix_write_frame(board, [0] * 8)\n        return res\n'''
    addition = marker + '''\n    def matrix_led_ready_heart_once(self, board: Any = "REC") -> Dict[str, Any]:\n        # Koncowy stan READY dla Matrix LED; wariant B potwierdzony fizycznie.\n        heart_columns = [0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00]\n        return self.matrix_write_frame(board, self._matrix_rows_from_columns(heart_columns))\n'''
    text = replace_once(text, marker, addition, "tarzanPoKeys.test_matrix_led_once")
    path.write_text(text, encoding="utf-8")
    return True


def ensure_hardwarebridge_final_outputs(root: Path) -> bool:
    path = root / "core" / "tarzanHardwareBridge.py"
    text = path.read_text(encoding="utf-8")
    if "def apply_lks_final_ready_outputs" in text:
        return False
    marker = '''    def apply_lks_test_safe_state(self, source: str = "LKS_TEST") -> Dict[str, Any]:\n        """Przywraca bezpieczny stan wyjść po testach LKS/ABC, bez ruchu osi.\n\n        Testy LKS mogą chwilowo mignąć LED/wyjściami. Po zakończeniu serii\n        wracamy do naturalnego stanu OFF/LOW zapisanego w tarzanPoKeys.\n        Nie zapisujemy konfiguracji i nie uruchamiamy STEP/DIR/ENABLE.\n        """\n        try:\n            if hasattr(self.pokeys, "apply_default_safe_state_once"):\n                result = self.pokeys.apply_default_safe_state_once()\n                self.logger.info(\n                    "POKEYS ABC SAFE STATE AFTER %s ok=%s",\n                    source,\n                    bool(isinstance(result, dict) and result.get("ok")),\n                )\n                return result if isinstance(result, dict) else {"ok": False, "raw": result}\n        except Exception as exc:\n            self.logger.warning("POKEYS ABC SAFE STATE AFTER %s failed: %s", source, exc)\n            return {"ok": False, "error": str(exc)}\n        return {"ok": False, "error": "NO_SAFE_STATE_METHOD"}\n'''
    addition = marker + '''\n    def apply_lks_final_ready_outputs(self, source: str = "LKS_BOOT_FINAL_READY") -> Dict[str, Any]:\n        """Ostatni fizyczny stan po boot LKS: F-LED OFF, LCD READY, Matrix HEART."""\n        out: Dict[str, Any] = {"ok": True, "source": source, "steps": {}, "errors": []}\n        batch_started = False\n        try:\n            if hasattr(self, "begin_hardware_batch"):\n                self.begin_hardware_batch(source, grace_ms=4000, ensure=False, action_type="POINT_TEST")\n                batch_started = True\n\n            try:\n                if hasattr(self.pokeys, "set_f_leds_off_once"):\n                    res = self.pokeys.set_f_leds_off_once()\n                else:\n                    dev = self.pokeys.get_device("REC") if hasattr(self.pokeys, "get_device") else None\n                    pins = getattr(self.pokeys, "F_LED_PINS", {})\n                    res = {"ok": bool(dev), "pins": dict(pins)}\n                    if dev is not None and hasattr(self.pokeys, "set_digital_output"):\n                        for pin in pins.values():\n                            self.pokeys.set_digital_output(dev, int(pin), 1)\n                out["steps"]["f_led_off"] = res\n                if not bool(isinstance(res, dict) and res.get("ok", True)):\n                    out["errors"].append("f_led_off")\n            except Exception as exc:\n                out["steps"]["f_led_off"] = {"ok": False, "error": str(exc)}\n                out["errors"].append("f_led_off")\n\n            lcd_ok = True\n            lcd_steps: Dict[str, Any] = {}\n            for board in ("PLAY", "REC"):\n                try:\n                    init = self.pokeys.lcd_init(board) if hasattr(self.pokeys, "lcd_init") else {"ok": False, "error": "NO_LCD_INIT"}\n                    write = self.pokeys.lcd_write_lines(board, "BEZ BLEDOW", "GOTOWE") if hasattr(self.pokeys, "lcd_write_lines") else {"ok": False, "error": "NO_LCD_WRITE"}\n                    lcd_steps[board] = {"init": init, "write": write, "ok": bool(write.get("ok"))}\n                    lcd_ok = lcd_ok and bool(write.get("ok"))\n                except Exception as exc:\n                    lcd_steps[board] = {"ok": False, "error": str(exc)}\n                    lcd_ok = False\n            out["steps"]["lcd_ready"] = {"ok": lcd_ok, "boards": lcd_steps}\n            if not lcd_ok:\n                out["errors"].append("lcd_ready")\n\n            try:\n                if hasattr(self.pokeys, "matrix_led_ready_heart_once"):\n                    matrix = self.pokeys.matrix_led_ready_heart_once("REC")\n                else:\n                    heart_columns = [0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00]\n                    rows = self.pokeys._matrix_rows_from_columns(heart_columns)\n                    matrix = self.pokeys.matrix_write_frame("REC", rows)\n                out["steps"]["matrix_ready_heart"] = matrix\n                if not bool(isinstance(matrix, dict) and matrix.get("ok")):\n                    out["errors"].append("matrix_ready_heart")\n            except Exception as exc:\n                out["steps"]["matrix_ready_heart"] = {"ok": False, "error": str(exc)}\n                out["errors"].append("matrix_ready_heart")\n\n            out["ok"] = not out["errors"]\n            self.logger.info(\n                "LKS-N5 FINAL READY OUTPUTS ok=%s lcd=%s matrix=%s f_led_off=%s",\n                out["ok"],\n                bool(out["steps"].get("lcd_ready", {}).get("ok")),\n                bool(out["steps"].get("matrix_ready_heart", {}).get("ok")),\n                bool(out["steps"].get("f_led_off", {}).get("ok", True)),\n            )\n            return out\n        except Exception as exc:\n            self.logger.warning("LKS-N5 FINAL READY OUTPUTS failed: %s", exc)\n            return {"ok": False, "source": source, "error": str(exc), "steps": out.get("steps", {})}\n        finally:\n            if batch_started and hasattr(self, "end_hardware_batch"):\n                try:\n                    self.end_hardware_batch(source, grace_ms=2000)\n                except Exception:\n                    pass\n'''
    text = replace_once(text, marker, addition, "tarzanHardwareBridge.apply_lks_test_safe_state")
    path.write_text(text, encoding="utf-8")
    return True


def ensure_bootprogress_call(root: Path) -> bool:
    path = root / "core" / "TSP" / "tarzanTspLksBootProgress.py"
    text = path.read_text(encoding="utf-8")
    if "FINAL READY OUTPUTS" in text and "apply_lks_final_ready_outputs" in text:
        return False
    marker = '''        # Końcówka ma iść zgodnie z fizycznym układem stron operatora:\n        # boot_test -> ready_main -> intro_status -> status_main.\n'''
    addition = '''        # ETAP 4: po testach i safe-state ustawiamy jeden końcowy stan\n        # fizyczny. To jest ostatni zapis do LCD/Matrix/F-LED przed READY.\n        bridge = self.hardware_bridge\n        if bridge is not None and hasattr(bridge, "apply_lks_final_ready_outputs"):\n            try:\n                final_ready = bridge.apply_lks_final_ready_outputs("LKS_BOOT_FINAL_READY")\n                ok_final = bool(isinstance(final_ready, dict) and final_ready.get("ok"))\n                print(f"LKS-N5 FINAL READY OUTPUTS ok={ok_final}")\n                if isinstance(final_ready, dict):\n                    matrix_ok = bool(final_ready.get("steps", {}).get("matrix_ready_heart", {}).get("ok"))\n                    print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={matrix_ok}")\n            except Exception as exc:\n                print(f"LKS-N5 FINAL READY OUTPUTS ok=False error={exc}")\n\n''' + marker
    text = replace_once(text, marker, addition, "tarzanTspLksBootProgress final ready marker")
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    root = Path.cwd()
    changed = []
    if ensure_matrix_ready_method(root):
        changed.append("core/tarzanPoKeys.py")
    if ensure_hardwarebridge_final_outputs(root):
        changed.append("core/tarzanHardwareBridge.py")
    if ensure_bootprogress_call(root):
        changed.append("core/TSP/tarzanTspLksBootProgress.py")
    print("OK: ETAP 4 final-ready outputs uporządkowane; changed=" + (", ".join(changed) if changed else "none"))


if __name__ == "__main__":
    main()
