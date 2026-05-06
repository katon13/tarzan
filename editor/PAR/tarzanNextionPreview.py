from __future__ import annotations

import tkinter as tk
from typing import Any, Dict, Optional

try:
    from editor.PAR.tarzanParWidgets import COLORS, Panel, Led
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, Panel, Led


class TarzanNextionPreviewPanel(tk.Frame):
    def __init__(self, parent, bridge, screen_key: str, title: str) -> None:
        super().__init__(parent, bg=COLORS["panel"])
        self.bridge = bridge
        self.screen_key = screen_key
        self.title = title
        self.state: Dict[str, Any] = {}
        self.component_widgets: Dict[str, Any] = {}
        self.component_meta: Dict[str, Dict[str, Any]] = {}
        self.current_page_id: Optional[str] = None
        self.panel = Panel(self, title=title)
        self.panel.pack(fill="both", expand=True)
        self._build_shell()
        self.refresh()

    def _build_shell(self) -> None:
        toolbar = tk.Frame(self.panel.body, bg=COLORS["panel"])
        toolbar.pack(fill="x", pady=(0, 6))
        tk.Button(toolbar, text="◀", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self._switch(-1)).pack(side="left", padx=2)
        tk.Button(toolbar, text="▶", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self._switch(1)).pack(side="left", padx=2)
        tk.Button(toolbar, text="SYNC", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=lambda: self.bridge.sync(force=True)).pack(side="left", padx=4)
        tk.Button(toolbar, text="POŁĄCZ", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=self._connect).pack(side="left", padx=4)
        tk.Button(toolbar, text="ROZŁĄCZ", bg=COLORS["button"], fg=COLORS["text"], relief="flat", command=self._disconnect).pack(side="left", padx=2)
        self.page_label = tk.Label(toolbar, text="PAGE", bg=COLORS["panel"], fg=COLORS["green"], font=("Segoe UI", 10, "bold"))
        self.page_label.pack(side="right")

        self.screen_frame = tk.Frame(self.panel.body, bg="#0a0d10", highlightbackground="#4b5660", highlightthickness=2)
        self.screen_frame.pack(fill="both", expand=True)
        self.screen_frame.grid_rowconfigure(0, weight=1)
        self.screen_frame.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Frame(self.screen_frame, bg="#13181d")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.status = tk.Label(self.panel.body, text="", bg=COLORS["panel"], fg=COLORS["muted"], anchor="w", justify="left")
        self.status.pack(fill="x", pady=(6, 0))

    def _switch(self, step: int) -> None:
        if step > 0:
            self.bridge.next_page(self.screen_key)
        else:
            self.bridge.prev_page(self.screen_key)
        self.refresh()

    def _connect(self) -> None:
        if hasattr(self.bridge, "connect_screen"):
            self.bridge.connect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_connect_screen"):
            self.bridge.nextion_connect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_connect"):
            self.bridge.nextion_connect()
        self.refresh()

    def _disconnect(self) -> None:
        if hasattr(self.bridge, "disconnect_screen"):
            self.bridge.disconnect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_disconnect_screen"):
            self.bridge.nextion_disconnect_screen(self.screen_key)
        elif hasattr(self.bridge, "nextion_disconnect_all"):
            self.bridge.nextion_disconnect_all()
        self.refresh()

    def refresh(self) -> None:
        self.state = self.bridge.snapshot()
        page = self.bridge.get_page(self.screen_key)
        page_id = page.get("id", "")
        self.page_label.configure(text=f"{self.screen_key.upper()} | {page.get('title', page_id or 'PAGE')}")

        if self.current_page_id != page_id:
            self._rebuild_page(page)
            self.current_page_id = page_id
        else:
            self._update_page_values(page)

        device = getattr(self.bridge, "devices", {}).get(self.screen_key)
        port = getattr(device, "port", self.state.get(f'{self.screen_key}.port', ''))
        connected = bool(getattr(device, "connected", False))
        err = getattr(device, "last_error", None) or self.state.get(f'{self.screen_key}.last_error', '') or '-'
        if connected:
            err = '-'
        status = [
            f"PORT: {port}",
            f"COM: {'OK' if connected else 'OFF'}",
            f"ERR: {err}",
        ]
        self.status.configure(text="   ".join(status))

    def _rebuild_page(self, page: Dict[str, Any]) -> None:
        for child in self.canvas.winfo_children():
            child.destroy()
        self.component_widgets.clear()
        self.component_meta.clear()
        self._render_page(page)

    def _render_page(self, page: Dict[str, Any]) -> None:
        components = list(page.get("components", []))
        for i, comp in enumerate(components):
            frame = tk.Frame(self.canvas, bg=comp.get("bg_color", COLORS["panel3"]), highlightbackground=COLORS["border"], highlightthickness=1)
            frame.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)
            self.canvas.grid_columnconfigure(i % 2, weight=1)
            bind = comp.get("bind")
            value = self.state.get(bind, comp.get("text", "")) if bind else comp.get("text", "")
            tk.Label(frame, text=comp.get("label", comp.get("id", "")), bg=frame.cget("bg"), fg=COLORS["muted"], anchor="w", font=("Segoe UI", 8, "bold")).pack(fill="x", padx=8, pady=(6, 2))
            ctype = comp.get("type", "text")
            cid = comp.get("id", f"comp_{i}")
            self.component_meta[cid] = {"type": ctype, "bind": bind, "text": comp.get("text", "")}
            if ctype in {"led", "indicator"}:
                led = Led(frame, size=26, bg=frame.cget("bg"))
                led.pack(padx=8, pady=8)
                led.set(value)
                self.component_widgets[cid] = led
            else:
                fg = comp.get("color", COLORS["text"])
                font_size = int(comp.get("font_size", 14))
                justify = comp.get("align", "left")
                lbl = tk.Label(frame, text=str(value), bg=frame.cget("bg"), fg=fg, justify=justify, anchor="w", wraplength=300, font=("Segoe UI", font_size, "bold" if ctype in {"button", "title"} else "normal"))
                lbl.pack(fill="both", expand=True, padx=8, pady=(0, 8))
                self.component_widgets[cid] = lbl

    def _update_page_values(self, page: Dict[str, Any]) -> None:
        for i, comp in enumerate(list(page.get("components", []))):
            cid = comp.get("id", f"comp_{i}")
            widget = self.component_widgets.get(cid)
            if widget is None:
                continue
            bind = comp.get("bind")
            value = self.state.get(bind, comp.get("text", "")) if bind else comp.get("text", "")
            ctype = comp.get("type", "text")
            if ctype in {"led", "indicator"}:
                try:
                    widget.set(value)
                except Exception:
                    pass
            else:
                try:
                    widget.configure(text=str(value))
                except Exception:
                    pass
