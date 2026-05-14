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

    root = Path(__file__).resolve().parents[2]
    file_path = root / "hardware" / "Nextion_stucture" / f'{base_name}.txt'
    
    parser = NextionLayoutParser(file_path)
    layout = parser.parse()
    _layout_cache[base_name] = layout
    return layout