from pathlib import Path

path = Path('core/tarzanPoKeys.py')
s = path.read_text(encoding='utf-8')

old = '''    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:
        if not visible:
            return {"ok": self.test_board_once(board), "board": board}
        cols = self._matrix_text_columns("OK")
        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))
        time.sleep(0.20)
        self.matrix_write_frame(board, [0] * 8)
        return res

    def read_f_buttons_once(self) -> Dict[str, Any]:
'''
new = '''    def matrix_led_off_once(self, board: Any = "REC") -> Dict[str, Any]:
        """Twardo wygasza fizyczną matrycę LED.

        Sam zapis pustej ramki [0]*8 zostawia sterownik MatrixLED w stanie
        displayEnabled=1. Na realnym module może wtedy zostać pojedynczy
        ghost-pixel po multipleksowaniu. Dlatego po teście zerujemy dane i
        wyłączamy displayEnabled.
        """
        with self._lock:
            if self.logical_sleep:
                self.logical_wake()
            board, device = self._resolve_device_target(board, "REC")
            if device is None:
                return {"ok": False, "board": board, "error": f"{board} not connected"}
            try:
                matrix_ptr = device.device.contents.MatrixLED
                matrix = matrix_ptr[0]
                matrix.rows = 8
                matrix.columns = 8
                matrix.displayEnabled = 0
                matrix.RefreshFlag = 1
                for i in range(8):
                    matrix.data[i] = 0
                res = self._call_device(board, "PK_MatrixLEDConfigurationSet")
                if not res.get("ok"):
                    raise RuntimeError(f"PK_MatrixLEDConfigurationSet failed: {res.get('error')}")
                res = self._call_device(board, "PK_MatrixLEDUpdate")
                if not res.get("ok"):
                    raise RuntimeError(f"PK_MatrixLEDUpdate failed: {res.get('error')}")
                return {"ok": True, "board": board, "displayEnabled": 0}
            except Exception as exc:
                return {"ok": False, "board": board, "error": str(exc)}

    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:
        if not visible:
            ok = self.test_board_once(board)
            off = self.matrix_led_off_once(board)
            return {"ok": bool(ok and off.get("ok")), "board": board, "matrix_off": off}
        cols = self._matrix_text_columns("OK")
        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))
        time.sleep(0.20)
        off = self.matrix_led_off_once(board)
        if not off.get("ok"):
            return {"ok": False, "board": board, "write": res, "matrix_off": off}
        return {"ok": bool(res.get("ok")), "board": board, "write": res, "matrix_off": off}

    def read_f_buttons_once(self) -> Dict[str, Any]:
'''
if old not in s:
    raise SystemExit('ERROR: expected test_matrix_led_once block not found')
s = s.replace(old, new)
s = s.replace('"ui_hardware": ["lcd_write_lines", "matrix_write_frame", "read_f_buttons_once", "blink_f_led_once", "read_keypad_once"],',
              '"ui_hardware": ["lcd_write_lines", "matrix_write_frame", "matrix_led_off_once", "read_f_buttons_once", "blink_f_led_once", "read_keypad_once"],')
path.write_text(s, encoding='utf-8')
print('OK: Matrix LED test now disables display after test')
