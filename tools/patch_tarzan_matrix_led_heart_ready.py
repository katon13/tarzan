from pathlib import Path

p = Path('core/tarzanPoKeys.py')
s = p.read_text(encoding='utf-8')

# 1) Add heart helper once, directly before matrix_write_frame.
if 'def matrix_show_heart_once' not in s:
    marker = '    def matrix_write_frame(self, board: Any = "REC", rows: Iterable[int] = ()) -> Dict[str, Any]:\n'
    if marker not in s:
        raise SystemExit('ERROR: matrix_write_frame marker not found')
    insert = '''    _MATRIX_HEART_8X8: List[int] = [\n        0x66,  # 01100110\n        0xFF,  # 11111111\n        0xFF,  # 11111111\n        0xFF,  # 11111111\n        0x7E,  # 01111110\n        0x3C,  # 00111100\n        0x18,  # 00011000\n        0x00,  # 00000000\n    ]\n\n    def matrix_show_heart_once(self, board: Any = "REC") -> Dict[str, Any]:\n        """Pokazuje serce gotowości na Matrix LED.\n\n        Zasada TARZAN: po poprawnym teście nie wyłączamy sterownika matrycy,\n        tylko zostawiamy jasny znak gotowości.\n        """\n        return self.matrix_write_frame(board, self._MATRIX_HEART_8X8)\n\n'''
    s = s.replace(marker, insert + marker)

# 2) Replace test_matrix_led_once so it ends with a heart, not blank/off.
start = s.find('    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:\n')
end = s.find('    def read_f_buttons_once(self) -> Dict[str, Any]:\n', start)
if start == -1 or end == -1:
    raise SystemExit('ERROR: test_matrix_led_once block markers not found')
new_block = '''    def test_matrix_led_once(self, visible: bool = False, board: str = "REC") -> Dict[str, Any]:\n        if not visible:\n            ok = self.test_board_once(board)\n            if ok:\n                return self.matrix_show_heart_once(board)\n            return {"ok": False, "board": board, "error": "matrix board test failed"}\n\n        cols = self._matrix_text_columns("OK")\n        res = self.matrix_write_frame(board, self._matrix_rows_from_columns(cols[:8]))\n        time.sleep(0.20)\n\n        if not res.get("ok"):\n            return res\n\n        heart = self.matrix_show_heart_once(board)\n        if heart.get("ok"):\n            return {"ok": True, "board": board, "display": "HEART_READY"}\n        return heart\n\n'''
s = s[:start] + new_block + s[end:]

# 3) Expose helper in ui_hardware list without breaking old actions.
old = '"ui_hardware": ["lcd_write_lines", "matrix_write_frame", "read_f_buttons_once", "blink_f_led_once", "read_keypad_once"],'
new = '"ui_hardware": ["lcd_write_lines", "matrix_write_frame", "matrix_show_heart_once", "test_matrix_led_once", "read_f_buttons_once", "blink_f_led_once", "read_keypad_once"],'
if old in s:
    s = s.replace(old, new)
elif 'matrix_show_heart_once' not in s[s.find('"ui_hardware"'):s.find('"ui_hardware"')+250]:
    raise SystemExit('ERROR: ui_hardware list format changed; update manually')

p.write_text(s, encoding='utf-8')
print('OK: Matrix LED leaves HEART_READY after successful test')
