from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from core.tarzanAssets import axis_icon, take_icon, BASE_DIR

try:
    from PIL import Image, ImageTk, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

class AssetManager:
    """
    Centralny manager assetów graficznych (ikony) dla edytorów Tarzana.
    Zapewnia cache'owanie obiektów ImageTk.PhotoImage, co zapobiega ich 
    odśmiecaniu przez GC i zapewnia spójność wizualną.
    """
    _instance: Optional[AssetManager] = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.photo_cache: Dict[Tuple[Any, ...], ImageTk.PhotoImage] = {}
        self.image_cache: Dict[Tuple[Any, ...], Image.Image] = {}
        self._initialized = True

    def get_axis_photo(self, axis_name: str, size: int = 64, state: str = "active") -> Optional[ImageTk.PhotoImage]:
        """Zwraca PhotoImage dla ikony osi."""
        if not PILLOW_AVAILABLE:
            return None
            
        key = ("axis", axis_name, size, state)
        if key in self.photo_cache:
            return self.photo_cache[key]
            
        try:
            path = axis_icon(axis_name, size=size, state=state)
            if not Path(path).exists():
                # Próba fallbacku na 64 jeśli inny rozmiar nie istnieje
                if size != 64:
                    return self.get_axis_photo(axis_name, size=64, state=state)
                return None
                
            img = Image.open(path).convert("RGBA")
            # Jeśli potrzebujemy dokładnego rozmiaru a plik ma inny
            if img.size != (size, size):
                img = img.resize((size, size), Image.LANCZOS)
                
            photo = ImageTk.PhotoImage(img)
            self.photo_cache[key] = photo
            self.image_cache[key] = img
            return photo
        except Exception:
            return None

    def get_take_photo(self, state: str = "closed", size: int = 64) -> Optional[ImageTk.PhotoImage]:
        """Zwraca PhotoImage dla ikony TAKE."""
        if not PILLOW_AVAILABLE:
            return None
            
        key = ("take", state, size)
        if key in self.photo_cache:
            return self.photo_cache[key]
            
        try:
            path = take_icon(size=size, state=state)
            if not Path(path).exists():
                return None
                
            img = Image.open(path).convert("RGBA")
            if img.size != (size, size):
                img = img.resize((size, size), Image.LANCZOS)
                
            photo = ImageTk.PhotoImage(img)
            self.photo_cache[key] = photo
            self.image_cache[key] = img
            return photo
        except Exception:
            return None

    def get_ui_icon(self, name: str, size: int = 24, fill: str = "#D5DCE7") -> Optional[ImageTk.PhotoImage]:
        """
        Zwraca ikonę UI (gear, wave itp.).
        Jeśli brak pliku, generuje ikonę zastępczą (kształt geometryczny).
        """
        if not PILLOW_AVAILABLE:
            return None
            
        key = ("ui", name, size, fill)
        if key in self.photo_cache:
            return self.photo_cache[key]
            
        try:
            path = Path(BASE_DIR) / "img" / "ui" / f"{name}_{size}.png"
            if path.exists():
                img = Image.open(path).convert("RGBA")
                if img.size != (size, size):
                    img = img.resize((size, size), Image.LANCZOS)
            else:
                # Generujemy ikonę zastępczą
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                if name == "gear":
                    # Kółko z ząbkami (uproszczone)
                    draw.ellipse([2, 2, size-3, size-3], outline=fill, width=2)
                    for i in range(8):
                        import math
                        angle = i * (math.pi / 4)
                        x1 = size/2 + math.cos(angle) * (size/2 - 5)
                        y1 = size/2 + math.sin(angle) * (size/2 - 5)
                        x2 = size/2 + math.cos(angle) * (size/2 - 1)
                        y2 = size/2 + math.sin(angle) * (size/2 - 1)
                        draw.line([x1, y1, x2, y2], fill=fill, width=2)
                elif name == "wave":
                    # Sinusoida
                    points = []
                    import math
                    for x in range(2, size-2):
                        y = size/2 + math.sin((x/size) * 2 * math.pi) * (size/4)
                        points.append((x, y))
                    draw.line(points, fill=fill, width=2)
                else:
                    # Kwadrat dla nieznanych
                    draw.rectangle([4, 4, size-5, size-5], outline=fill, width=1)
            
            photo = ImageTk.PhotoImage(img)
            self.photo_cache[key] = photo
            return photo
        except Exception:
            return None

    def clear_cache(self):
        self.photo_cache.clear()
        self.image_cache.clear()
