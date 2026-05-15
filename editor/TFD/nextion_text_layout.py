import re
import os
from pathlib import Path

class NextionLayoutParser:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.components = []
        self.page_name = ""

    def parse(self):
        if not self.file_path.exists():
            return []
        
        try:
            content = self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = self.file_path.read_text(encoding="iso-8859-1")
            except:
                return []

        self.page_name = self.file_path.stem
        
        current_comp = None
        
        for line in content.splitlines():
            comp_match = re.match(r"^(\w+)\s+([\w\.]+)", line)
            if comp_match:
                comp_type = comp_match.group(1)
                comp_name = comp_match.group(2)
                current_comp = {"type": comp_type, "name": comp_name, "attrs": {}}
                self.components.append(current_comp)
                continue
            
            if ":" in line and current_comp:
                parts = line.split(":", 1)
                attr_name = parts[0].strip()
                attr_val = parts[1].strip()
                current_comp["attrs"][attr_name] = attr_val

        return self.components

_layout_cache = {}

def get_layout(page_name):
    if page_name.lower().endswith(".txt"):
        base_name = page_name[:-4]
    else:
        base_name = page_name
        
    if base_name in _layout_cache:
        return _layout_cache[base_name]

    # Dynamiczne szukanie korzenia projektu
    current_file = Path(__file__).resolve()
    root = current_file.parents[2] # Fallback (editor/TFD/nextion_text_layout.py)
    
    # Szukamy folderu hardware idąc w górę
    p = current_file
    for _ in range(5):
        if (p / "hardware").exists():
            root = p
            break
        if p.parent == p: break
        p = p.parent

    file_path = root / "hardware" / "Nextion_structure" / f'{base_name}.txt'
    
    # Maksymalna odporność: jeśli nie ma w domyślnym miejscu, szukaj w hardware
    if not file_path.exists():
        try:
            for p in (root / "hardware").rglob(f"{base_name}.txt"):
                file_path = p
                break
        except: pass

    parser = NextionLayoutParser(file_path)
    layout = parser.parse()
    if layout:
        _layout_cache[base_name] = layout
    return layout

if __name__ == "__main__":
    layout = get_layout("take_main.txt")
    print(f"File: {__file__}")
    print(f"Resolved: {Path(__file__).resolve()}")
    print(f"Root: {Path(__file__).resolve().parents[2]}")
    print(f"Layout components: {len(layout)}")
    for i, comp in enumerate(layout[:5]):
        print(f" {i}. {comp['type']}: {comp['name']}")