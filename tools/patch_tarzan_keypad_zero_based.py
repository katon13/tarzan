from pathlib import Path

path = Path('core/tarzanPoKeys.py')
s = path.read_text(encoding='utf-8')

repls = {
    'kb.matrixKBcolumnsPins[0] = int(self.PLAY_KEYPAD_4X3_COLUMNS["A"])': 'kb.matrixKBcolumnsPins[0] = int(self.PLAY_KEYPAD_4X3_COLUMNS["A"]) - 1',
    'kb.matrixKBcolumnsPins[1] = int(self.PLAY_KEYPAD_4X3_COLUMNS["B"])': 'kb.matrixKBcolumnsPins[1] = int(self.PLAY_KEYPAD_4X3_COLUMNS["B"]) - 1',
    'kb.matrixKBcolumnsPins[2] = int(self.PLAY_KEYPAD_4X3_COLUMNS["C"])': 'kb.matrixKBcolumnsPins[2] = int(self.PLAY_KEYPAD_4X3_COLUMNS["C"]) - 1',
    'kb.matrixKBrowsPins[0] = int(self.PLAY_KEYPAD_4X3_ROWS[1])': 'kb.matrixKBrowsPins[0] = int(self.PLAY_KEYPAD_4X3_ROWS[1]) - 1',
    'kb.matrixKBrowsPins[1] = int(self.PLAY_KEYPAD_4X3_ROWS[2])': 'kb.matrixKBrowsPins[1] = int(self.PLAY_KEYPAD_4X3_ROWS[2]) - 1',
    'kb.matrixKBrowsPins[2] = int(self.PLAY_KEYPAD_4X3_ROWS[3])': 'kb.matrixKBrowsPins[2] = int(self.PLAY_KEYPAD_4X3_ROWS[3]) - 1',
    'kb.matrixKBrowsPins[3] = int(self.PLAY_KEYPAD_4X3_ROWS[4])': 'kb.matrixKBrowsPins[3] = int(self.PLAY_KEYPAD_4X3_ROWS[4]) - 1',
}
missing = []
for old, new in repls.items():
    if old not in s and new not in s:
        missing.append(old)
    s = s.replace(old, new)

comment_old = '# PoKeys arrays are zero-based: columnsPins[0] = A, rowsPins[0] = row 1.'
comment_new = '# PoKeys MatrixKB stores pin indexes as ZERO-BASED values: physical P27 => 26. columnsPins[0] = A, rowsPins[0] = row 1.'
s = s.replace(comment_old, comment_new)

old_ok = 'ok = bool(set_res.get("ok") and get_res.get("ok") and save_res.get("ok"))\n            return {'
new_ok = '''expected_rows_api = [
                int(self.PLAY_KEYPAD_4X3_ROWS[1]) - 1,
                int(self.PLAY_KEYPAD_4X3_ROWS[2]) - 1,
                int(self.PLAY_KEYPAD_4X3_ROWS[3]) - 1,
                int(self.PLAY_KEYPAD_4X3_ROWS[4]) - 1,
            ]
            expected_columns_api = [
                int(self.PLAY_KEYPAD_4X3_COLUMNS["A"]) - 1,
                int(self.PLAY_KEYPAD_4X3_COLUMNS["B"]) - 1,
                int(self.PLAY_KEYPAD_4X3_COLUMNS["C"]) - 1,
            ]
            actual_rows_api = [int(kb.matrixKBrowsPins[i]) for i in range(4)]
            actual_columns_api = [int(kb.matrixKBcolumnsPins[i]) for i in range(3)]
            mapping_ok = actual_rows_api == expected_rows_api and actual_columns_api == expected_columns_api
            ok = bool(set_res.get("ok") and get_res.get("ok") and save_res.get("ok") and mapping_ok)
            return {'''
if old_ok in s:
    s = s.replace(old_ok, new_ok)
else:
    if 'expected_rows_api' not in s:
        missing.append('ok block for matrix mapping readback')

old_return = '"columns": dict(self.PLAY_KEYPAD_4X3_COLUMNS),\n                "set": set_res,'
new_return = '"columns": dict(self.PLAY_KEYPAD_4X3_COLUMNS),\n                "expected_rows_api": expected_rows_api,\n                "expected_columns_api": expected_columns_api,\n                "actual_rows_api": actual_rows_api,\n                "actual_columns_api": actual_columns_api,\n                "mapping_ok": mapping_ok,\n                "set": set_res,'
s = s.replace(old_return, new_return)

if missing:
    raise SystemExit('Nie znaleziono wzorców do patcha:\n' + '\n'.join(missing))

path.write_text(s, encoding='utf-8')
print('OK: patched MatrixKB physical pins to zero-based API indexes')
