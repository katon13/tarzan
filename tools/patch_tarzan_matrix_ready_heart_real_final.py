from pathlib import Path
import re

ROOT = Path.cwd()
po = ROOT / "core" / "tarzanPoKeys.py"
bp = ROOT / "core" / "TSP" / "tarzanTspLksBootProgress.py"

s = po.read_text(encoding="utf-8")

heart_method = '\n    def matrix_led_ready_heart_once(self, board: Any = "REC") -> Dict[str, Any]:\n        """Pokazuje stałe serce READY na Matrix LED.\n\n        Orientacja B została potwierdzona na fizycznej matrycy TARZAN:\n        heart_columns -> _matrix_rows_from_columns(heart_columns).\n        Nie wyłączamy displayEnabled i nie czyścimy ramki po teście.\n        """\n        heart_columns = [0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00]\n        rows = self._matrix_rows_from_columns(heart_columns)\n        res = self.matrix_write_frame(board, rows)\n        if isinstance(res, dict):\n            res["pattern"] = "READY_HEART_B"\n            res["rows"] = rows\n        return res\n'

if "def matrix_led_ready_heart_once" not in s:
    marker = "    def test_matrix_led_once("
    idx = s.find(marker)
    if idx < 0:
        raise SystemExit("Nie znaleziono test_matrix_led_once w core/tarzanPoKeys.py")
    s = s[:idx] + heart_method + "\n" + s[idx:]

def repl_test(match: re.Match) -> str:
    return '    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:\n        """Test Matrix LED kończy się stałym sercem READY.\n\n        Ważne: nie zostawiamy pustej ramki ani nie wyłączamy displayEnabled,\n        bo matryca pełni funkcję gotowości systemu. Serce jest ustawiane także\n        później jako finalny stan bootu w tarzanTspLksBootProgress.py.\n        """\n        if not visible:\n            ok = self.test_board_once(board)\n            ready = self.matrix_led_ready_heart_once(board)\n            return {"ok": bool(ok and ready.get("ok")), "board": board, "ready_heart": ready, "mode": "board_ack_plus_ready_heart"}\n        cols = self._matrix_text_columns("OK")\n        write = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))\n        time.sleep(0.20)\n        ready = self.matrix_led_ready_heart_once(board)\n        return {"ok": bool(write.get("ok") and ready.get("ok")), "board": board, "write": write, "ready_heart": ready}\n\n'

pattern = r"    def test_matrix_led_once\(self, visible: bool = False, board: str = \"REC\"\) -> Dict\[str, Any\]:\n.*?\n(?=    def read_f_buttons_once\()"
s2, n = re.subn(pattern, repl_test, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit("Nie udało się podmienić test_matrix_led_once w core/tarzanPoKeys.py")
po.write_text(s2, encoding="utf-8")

b = bp.read_text(encoding="utf-8")
method = '\n    def _apply_final_matrix_ready_heart(self) -> None:\n        """Ostatni fizyczny zapis do Matrix LED po całym boot/status cache.\n\n        Serce po teście matrix_led może zostać nadpisane przez późniejsze etapy\n        bootu. Dlatego po ustawieniu status_main i statusów ikon wykonujemy\n        ostatni zapis PoKeys w stanie POINT_TEST. Nie czyścimy i nie gasimy\n        matrycy: ma zostać znak gotowości.\n        """\n        bridge = self.hardware_bridge\n        if bridge is None:\n            print("LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False detail=NO_HARDWAREBRIDGE")\n            return\n        pokeys = getattr(bridge, "pokeys", None)\n        if pokeys is None or not hasattr(pokeys, "matrix_led_ready_heart_once"):\n            print("LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False detail=NO_POKEYS_READY_HEART")\n            return\n        try:\n            if hasattr(pokeys, "begin_point_test"):\n                pokeys.begin_point_test("matrix_ready_heart_final")\n            result = pokeys.matrix_led_ready_heart_once("REC")\n            ok = bool(isinstance(result, dict) and result.get("ok"))\n            detail = ""\n            if isinstance(result, dict):\n                detail = str(result.get("error") or result.get("reason") or result.get("pattern") or "")[:120]\n            print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok={ok} detail={detail}")\n        except Exception as exc:\n            print(f"LKS-N5 FINAL MATRIX READY HEART component=matrix_led ok=False detail={exc}")\n        finally:\n            try:\n                if pokeys is not None and hasattr(pokeys, "end_active_state"):\n                    pokeys.end_active_state()\n            except Exception:\n                pass\n\n'
if "def _apply_final_matrix_ready_heart" not in b:
    marker = "    def _write_last_report(self) -> None:"
    idx = b.find(marker)
    if idx < 0:
        raise SystemExit("Nie znaleziono _write_last_report w tarzanTspLksBootProgress.py")
    b = b[:idx] + method + b[idx:]

old = "        self.n5.set_many_statuses(self.statuses)\n        self._write_last_report()"
new = "        self.n5.set_many_statuses(self.statuses)\n        self._apply_final_matrix_ready_heart()\n        self._write_last_report()"
if old in b and "self._apply_final_matrix_ready_heart()" not in b[b.find("self.n5.set_many_statuses(self.statuses)"):b.find("self.n5.set_many_statuses(self.statuses)")+200]:
    b = b.replace(old, new, 1)
elif "self._apply_final_matrix_ready_heart()" not in b:
    raise SystemExit("Nie udało się dopiąć finalnego serca po set_many_statuses")

bp.write_text(b, encoding="utf-8")
print("OK: Matrix LED READY HEART is set as the final physical boot state")
