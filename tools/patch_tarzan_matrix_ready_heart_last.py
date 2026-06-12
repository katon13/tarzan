from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
po = ROOT / "core" / "tarzanPoKeys.py"
bp = ROOT / "core" / "TSP" / "tarzanTspLksBootProgress.py"

s = po.read_text(encoding="utf-8")

heart_helper = '    def matrix_led_ready_heart_once(self, board: Any = "REC") -> Dict[str, Any]:\n        """Zostawia na Matrix LED znak gotowości: serce READY.\n\n        Orientacja B potwierdzona fizycznie:\n        heart_columns -> _matrix_rows_from_columns(heart_columns).\n        Sterownik zostaje aktywny, bo matryca ma pokazywać gotowość.\n        """\n        heart_columns = [0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00]\n        return self.matrix_write_frame(board, self._matrix_rows_from_columns(heart_columns))\n\n'

s = re.sub(
    r"\n    def matrix_led_ready_heart_once\(self, board: Any = \"REC\"\) -> Dict\[str, Any\]:\n(?:        .*\n)+?(?=\n    def )",
    "\n",
    s,
)
s = re.sub(
    r"\n    def matrix_show_heart_once\(self, board: Any = \"REC\"\) -> Dict\[str, Any\]:\n(?:        .*\n)+?(?=\n    def )",
    "\n",
    s,
)

marker = '    def matrix_write_frame(self, board: Any = "REC", rows: Iterable[int] = ()) -> Dict[str, Any]:\n'
if marker not in s:
    raise SystemExit("ERROR: matrix_write_frame marker not found")
s = s.replace(marker, heart_helper + marker, 1)

start = s.find('    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:\n')
if start < 0:
    raise SystemExit("ERROR: test_matrix_led_once not found")
end = s.find('\n    def read_f_buttons_once', start)
if end < 0:
    raise SystemExit("ERROR: read_f_buttons_once marker not found")

new_test = '    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:\n        if not visible:\n            ok = self.test_board_once(board)\n            ready = self.matrix_led_ready_heart_once(board)\n            return {"ok": bool(ok and ready.get("ok")), "board": board, "matrix_ready": ready}\n\n        cols = self._matrix_text_columns("OK")\n        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))\n        time.sleep(0.20)\n        ready = self.matrix_led_ready_heart_once(board)\n        if not ready.get("ok"):\n            return {"ok": False, "board": board, "write": res, "matrix_ready": ready}\n        return {"ok": bool(res.get("ok") and ready.get("ok")), "board": board, "write": res, "matrix_ready": ready}\n\n'
s = s[:start] + new_test + s[end+1:]
po.write_text(s, encoding="utf-8")

b = bp.read_text(encoding="utf-8")
if "LKS-N5 FINAL MATRIX READY HEART" not in b:
    lcd_block_end_marker = '            except Exception as exc:\n                print(f"LKS-N5 FINAL LCD VISIBLE REFRESH component=lcd_1602 ok=False error={exc}")\n\n        # Po pełnej serii przeliczamy agregat i2c_bus z wyników peryferiów.\n'
    insert = '            except Exception as exc:\n                print(f"LKS-N5 FINAL LCD VISIBLE REFRESH component=lcd_1602 ok=False error={exc}")\n\n            # OSTATNI FIZYCZNY ZNAK GOTOWOŚCI NA MATRIX LED:\n            # test Matrix LED pokazuje serce, ale późniejsze testy/refresh mogą nadpisać\n            # rejestry matrycy. Dlatego po LCD refresh zostawiamy serce jako ostatni\n            # widoczny stan gotowości. Nie rusza LCD, keypad, F-LED ani ABC.\n            try:\n                pokeys = getattr(bridge, "pokeys", None)\n                if pokeys is not None and hasattr(pokeys, "matrix_led_ready_heart_once"):\n                    heart_result = pokeys.matrix_led_ready_heart_once("REC")\n                    print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={bool(isinstance(heart_result, dict) and heart_result.get(\'ok\'))} detail={str(heart_result)[:120]}")\n            except Exception as exc:\n                print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False error={exc}")\n\n        # Po pełnej serii przeliczamy agregat i2c_bus z wyników peryferiów.\n'
    if lcd_block_end_marker not in b:
        raise SystemExit("ERROR: FINAL LCD refresh block marker not found in tarzanTspLksBootProgress.py")
    b = b.replace(lcd_block_end_marker, insert, 1)
    bp.write_text(b, encoding="utf-8")

print("OK: Matrix LED READY heart is now final physical state after LKS boot tests")
