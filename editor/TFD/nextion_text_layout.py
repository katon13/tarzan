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
            content = self.file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = self.file_path.read_text(encoding='iso-8859-1')
            except:
                return []

        self.page_name = self.file_path.stem
        
        current_obj = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                if current_obj:
                    self.components.append(current_obj)
                    current_obj = {}
                continue
            
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip().lower()
                val = parts[1].strip()
                
                if key == "type": current_obj["type"] = val
                elif key == "obj": current_obj["name"] = val
                elif key == "x": 
                    try: current_obj["x"] = int(val)
                    except: current_obj["x"] = 0
                elif key == "y": 
                    try: current_obj["y"] = int(val)
                    except: current_obj["y"] = 0
                elif key == "w": 
                    try: current_obj["w"] = int(val)
                    except: current_obj["w"] = 0
                elif key == "h": 
                    try: current_obj["h"] = int(val)
                    except: current_obj["h"] = 0
                elif key == "txt": current_obj["text"] = val
                elif key == "pco": current_obj["color"] = val
                elif key == "bco": current_obj["bgcolor"] = val
                elif key == "pic": current_obj["pic"] = val

        if current_obj:
            self.components.append(current_obj)
            
        return self.components

def get_layout(page_name):
    # Szukamy pliku .txt w hardware/Nextion_stucture/
    root = Path(__file__).resolve().parents[2]
    file_path = root / "hardware" / "Nextion_stucture" / f"{page_name}.txt"
    parser = NextionLayoutParser(file_path)
    return parser.parse()
