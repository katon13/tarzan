from __future__ import annotations

import time
from typing import Any, Dict, List

from .config import load_ports
from .device import TarzanNextionDevice
from .protocol import cmd_page, cmd_text, cmd_value, cmd_visible, command_bytes
from .screen_model import ScreenDefinition, load_screen_definition
from .state_mapper import TarzanNextionStateMapper


class TarzanNextionBridge:
    def __init__(self, bus) -> None:
        self.bus = bus
        self.state_mapper = TarzanNextionStateMapper(bus)
        self.ports_cfg = load_ports()
        self.screen_defs: Dict[str, ScreenDefinition] = {
            "nextion_5": load_screen_definition("nextion_5"),
            "nextion_7": load_screen_definition("nextion_7"),
        }
        self.active_pages: Dict[str, str] = {
            key: (screen.settings.get("startup_page") or (screen.pages[0]["id"] if screen.pages else "main"))
            for key, screen in self.screen_defs.items()
        }
        self.devices: Dict[str, TarzanNextionDevice] = {}
        for key in ("nextion_5", "nextion_7"):
            cfg = self.ports_cfg.get(key, {})
            self.devices[key] = TarzanNextionDevice(key, cfg.get("port", "COM1"), int(cfg.get("baudrate", 115200)))
        self.last_sync = 0.0
        self.last_sent_snapshot: Dict[str, Any] = {}
        self.last_commands: List[str] = []

    def _enabled(self, screen_key: str) -> bool:
        return bool(self.ports_cfg.get(screen_key, {}).get("enabled", False))

    def _page_ids(self, screen_key: str) -> List[str]:
        screen = self.screen_defs[screen_key]
        return [str(p.get("id", "")) for p in screen.pages if p.get("id")]

    def _page_id_from_index(self, screen_key: str, page_index: int) -> str:
        page_ids = self._page_ids(screen_key)
        if 0 <= page_index < len(page_ids):
            return page_ids[page_index]
        return self.active_pages.get(screen_key, page_ids[0] if page_ids else "main")

    def _request_current_page(self, device: TarzanNextionDevice) -> None:
        if device.connected:
            device.send_raw(command_bytes("sendme"))

    def connect_enabled(self) -> None:
        for key in self.devices:
            if self._enabled(key):
                self.connect_screen(key)

    def connect_screen(self, screen_key: str) -> bool:
        device = self.devices.get(screen_key)
        if device is None:
            return False
        ok = device.handshake(wait_ms=100)
        if ok:
            page_id = self.active_pages.get(screen_key, "")
            if page_id:
                device.send_raw(cmd_page(page_id))
            self._request_current_page(device)
        return ok

    def disconnect_screen(self, screen_key: str) -> None:
        device = self.devices.get(screen_key)
        if device is not None:
            device.close()

    def disconnect_all(self) -> None:
        for device in self.devices.values():
            device.close()

    def snapshot(self) -> Dict[str, Any]:
        base = self.state_mapper.snapshot()
        for key, device in self.devices.items():
            base[f"{key}.connected"] = bool(device.connected)
            base[f"{key}.port"] = device.port
            base[f"{key}.baudrate"] = int(device.baudrate)
            base[f"{key}.last_error"] = device.last_error or ""
            base[f"{key}.page"] = self.active_pages.get(key, "")
        return base

    def set_page(self, screen_key: str, page_id: str) -> None:
        self.active_pages[screen_key] = page_id
        device = self.devices.get(screen_key)
        if device is not None and device.connected:
            device.send_raw(cmd_page(page_id))
            self._request_current_page(device)

    def next_page(self, screen_key: str) -> None:
        screen = self.screen_defs[screen_key]
        pages = [p.get("id") for p in screen.pages]
        if not pages:
            return
        cur = self.active_pages.get(screen_key, pages[0])
        idx = pages.index(cur) if cur in pages else 0
        self.set_page(screen_key, pages[(idx + 1) % len(pages)])

    def prev_page(self, screen_key: str) -> None:
        screen = self.screen_defs[screen_key]
        pages = [p.get("id") for p in screen.pages]
        if not pages:
            return
        cur = self.active_pages.get(screen_key, pages[0])
        idx = pages.index(cur) if cur in pages else 0
        self.set_page(screen_key, pages[(idx - 1) % len(pages)])

    def get_page(self, screen_key: str) -> Dict[str, Any]:
        screen = self.screen_defs[screen_key]
        page_id = self.active_pages.get(screen_key)
        for page in screen.pages:
            if page.get("id") == page_id:
                return page
        return screen.pages[0] if screen.pages else {"id": "empty", "components": []}

    def build_commands(self, screen_key: str, state: Dict[str, Any]) -> List[bytes]:
        page = self.get_page(screen_key)
        commands: List[bytes] = []
        for comp in page.get("components", []):
            nxt = comp.get("nextion") or {}
            component = nxt.get("component")
            prop = nxt.get("property", "txt")
            if not component:
                continue
            visible_if = comp.get("visible_if")
            if visible_if:
                commands.append(cmd_visible(component, bool(state.get(visible_if))))
            bind = comp.get("bind")
            if bind:
                value = state.get(bind, comp.get("text", ""))
            else:
                value = comp.get("text", "")
            if prop == "val":
                commands.append(cmd_value(component, value))
            else:
                commands.append(cmd_text(component, value))
        return commands

    def _level_xyz_commands(self, screen_key: str, state: Dict[str, Any]) -> List[bytes]:
        if screen_key != "nextion_7":
            return []
        if self.active_pages.get(screen_key) != "level_xyz":
            return []

        try:
            x = int(float(self.bus.get("par_level_x", 0) or 0))
        except Exception:
            x = 0

        try:
            y = int(float(self.bus.get("par_level_y", 0) or 0))
        except Exception:
            y = 0

        x = max(-30, min(30, x))
        y = max(-30, min(30, y))

        return [
            command_bytes(f"va0.val={x}"),
            command_bytes(f"va1.val={y}"),
        ]

    def sync(self, force: bool = False) -> None:
        snapshot = self.snapshot()
        now = time.time()
        interval = max(0.1, float(self.ports_cfg.get("sync_interval_ms", 100)) / 1000.0)
        if not force and snapshot == self.last_sent_snapshot and (now - self.last_sync) < interval:
            return
        self.last_sync = now
        self.last_commands = []
        for key, device in self.devices.items():
            if not self._enabled(key) or not device.connected:
                continue
            commands = self.build_commands(key, snapshot)
            commands.extend(self._level_xyz_commands(key, snapshot))
            for payload in commands:
                self.last_commands.append(f"{key}: {payload!r}")
                device.send_raw(payload)
        self.last_sent_snapshot = dict(snapshot)

    def poll(self) -> List[str]:
        logs: List[str] = []
        for key, device in self.devices.items():
            for event in device.poll():
                raw = event.raw
                logs.append(f"{key} EVENT {raw!r}")

                if len(raw) >= 2 and raw[0] == 0x66:
                    page_id = self._page_id_from_index(key, int(raw[1]))
                    self.active_pages[key] = page_id
                    logs.append(f"{key} PAGE {page_id}")
                    continue

                if len(raw) >= 4 and raw[0] == 0x65:
                    self._request_current_page(device)
                    logs.append(f"{key} TOUCH page={int(raw[1])} comp={int(raw[2])} event={int(raw[3])}")
        return logs
