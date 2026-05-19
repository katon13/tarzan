from __future__ import annotations

"""
TARZAN Nextion monitor panel.

Ten moduł nie renderuje już graficznej kopii ekranów Nextiona.
Fizyczny Nextion jest jedynym ekranem operatorskim, a PAR pokazuje tylko:
- stan połączenia,
- aktualną stronę fizycznego Nextiona,
- UI CUT jako stan diagnostyczny,
- log transportu TX/RX/SET/SYS/PAGE/ERR.

Kontrakt:
    SignalBus / TFDState -> Snajper -> physical_nextion -> fizyczny Nextion

Ten panel nie jest adapterem HMI i nie tworzy drugiego systemu odświeżania.
canvas_preview zostaje neutralny/no-op, aby nie zrywać integracji ze Snajperem.
"""

import json
import tkinter as tk
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from editor.PAR.tarzanParWidgets import COLORS, Panel
except ModuleNotFoundError:
    from tarzanParWidgets import COLORS, Panel


class TarzanNextionPreviewPanel(tk.Frame):
    """
    Lekki monitor fizycznego Nextiona.

    Historycznie ten panel rysował lokalną kopię stron HMI na Canvasie.
    Po integracji fizycznego Nextiona i Snajpera nie dublujemy już ekranów.
    Panel zostaje jako diagnostyka łączności i logów.
    """

    LOG_LIMIT = 300

    def __init__(self, parent: Any, bridge: Any, screen_key: str, title: str) -> None:
        super().__init__(parent, bg=COLORS["panel"])
        self.bridge = bridge
        self.screen_key = screen_key
        self.title = title
        self.state: Dict[str, Any] = {}
        self.current_page_id: Optional[str] = None
        self.ui_cut: bool = False
        self._snajper_canvas_items: Dict[str, int] = {}
        self._last_log_lines: List[str] = []
        self._last_log_signature: str = ""
        self._manual_log_lines: List[str] = []
        self._refresh_after_id: Optional[str] = None
        self._refresh_interval_ms = 200

        self.settings = self._load_settings()
        self.ports_cfg = self._load_ports_cfg()

        self.panel = Panel(self, title=title)
        self.panel.pack(fill="both", expand=True)
        self._build_shell()
        self.refresh()
        self._schedule_refresh()

    # ---------------------------------------------------------------------
    # Public compatibility API used by PAR/Snajper integration
    # ---------------------------------------------------------------------

    def ensure_snajper_items(self) -> None:
        """Compatibility no-op: graficzny canvas_preview został odłączony."""
        return

    def register_snajper_canvas_item(self, page: str, component: str, prop: str, item_id: int) -> None:
        """Compatibility no-op, zostawione aby adapter Snajpera nie zgłaszał błędów."""
        self._snajper_canvas_items[f"{page}.{component}.{prop}"] = item_id

    def update_component(self, page: str, component: str, prop: str, value: Any) -> None:
        """
        Snajper może nadal wysłać update do canvas_preview.
        Panel nie renderuje HMI, więc nie aktualizuje elementów graficznych.
        Zachowujemy tylko istotne stany diagnostyczne.
        """
        if component == "b_ui_cut" and prop == "val":
            self.set_ui_cut(self._as_bool(value))
        if page:
            self.current_page_id = str(page)
            self._update_page_label()

    def set_ui_cut(self, enabled: bool) -> None:
        """
        UI CUT jest teraz statusem diagnostycznym lokalnego podglądu.
        Nie zatrzymuje Snajpera, Bridge ani physical_nextion.
        """
        self.ui_cut = bool(enabled)
        if hasattr(self, "ui_cut_value"):
            self.ui_cut_value.configure(
                text="ON" if self.ui_cut else "OFF",
                fg=COLORS["red"] if self.ui_cut else COLORS["green"],
            )
        if hasattr(self, "status"):
            self._update_status_line()

    def refresh(self) -> None:
        """Odświeża tylko status, aktualną stronę i log transportu."""
        self._poll_bridge_once()
        self.state = self._snapshot()
        self.current_page_id = self._bridge_page_id() or self.current_page_id or "-"
        self._update_ui_cut_from_state()

        self._update_connection_labels()
        self._update_page_label()
        self._refresh_transport_log()
        self._update_status_line()

    def destroy(self) -> None:
        if self._refresh_after_id:
            try:
                self.after_cancel(self._refresh_after_id)
            except Exception:
                pass
            self._refresh_after_id = None
        super().destroy()

    def _schedule_refresh(self) -> None:
        if self._refresh_after_id:
            try:
                self.after_cancel(self._refresh_after_id)
            except Exception:
                pass
        self._refresh_after_id = self.after(self._refresh_interval_ms, self._refresh_tick)

    def _refresh_tick(self) -> None:
        self._refresh_after_id = None
        try:
            self.refresh()
        finally:
            try:
                self._schedule_refresh()
            except Exception:
                pass

    def _poll_bridge_once(self) -> None:
        """
        Monitor sam lekko pobiera zdarzenia z Bridge, żeby panel odświeżał
        stronę/logi nawet wtedy, gdy zewnętrzny refresh PAR nie wywołał panel.refresh().
        """
        if not hasattr(self.bridge, "poll"):
            return
        try:
            logs = self.bridge.poll()
            if logs:
                self._manual_log_lines.extend([str(x) for x in logs])
                if len(self._manual_log_lines) > self.LOG_LIMIT:
                    self._manual_log_lines = self._manual_log_lines[-self.LOG_LIMIT:]
        except Exception as exc:
            self._manual_log_lines.append(f"ERR: bridge.poll failed: {exc}")
            self._manual_log_lines = self._manual_log_lines[-self.LOG_LIMIT:]

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------

    def _build_shell(self) -> None:
        toolbar = tk.Frame(self.panel.body, bg=COLORS["panel"])
        toolbar.pack(fill="x", pady=(0, 6))

        tk.Button(
            toolbar,
            text="SYNC",
            bg=COLORS["button"],
            fg=COLORS["text"],
            relief="flat",
            command=self._sync,
        ).pack(side="left", padx=4)
        tk.Button(
            toolbar,
            text="POŁĄCZ",
            bg=COLORS["button"],
            fg=COLORS["text"],
            relief="flat",
            command=self._connect,
        ).pack(side="left", padx=4)
        tk.Button(
            toolbar,
            text="ROZŁĄCZ",
            bg=COLORS["button"],
            fg=COLORS["text"],
            relief="flat",
            command=self._disconnect,
        ).pack(side="left", padx=2)
        tk.Button(
            toolbar,
            text="CLEAR LOG",
            bg=COLORS["button"],
            fg=COLORS["text"],
            relief="flat",
            command=self._clear_log_view,
        ).pack(side="left", padx=8)

        self.page_label = tk.Label(
            toolbar,
            text="PAGE: -",
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 10, "bold"),
        )
        self.page_label.pack(side="right")

        summary = tk.Frame(self.panel.body, bg="#0a0d10", highlightbackground="#4b5660", highlightthickness=1)
        summary.pack(fill="x", pady=(0, 8), ipady=6)

        self._summary_row(summary, 0, "SCREEN", self.screen_key.upper(), "screen_value")
        self._summary_row(summary, 1, "PORT", "-", "port_value")
        self._summary_row(summary, 2, "BAUD", "-", "baud_value")
        self._summary_row(summary, 3, "CONNECTED", "NO", "connected_value")
        self._summary_row(summary, 4, "CURRENT PAGE", "-", "current_page_value")
        self._summary_row(summary, 5, "UI CUT", "OFF", "ui_cut_value")
        self._summary_row(summary, 6, "LAST ERROR", "-", "error_value")

        log_header = tk.Frame(self.panel.body, bg=COLORS["panel"])
        log_header.pack(fill="x")
        tk.Label(
            log_header,
            text="LOGI FIZYCZNEGO NEXTIONA — TX/RX/PAGE/SET/SYS/ERR",
            bg=COLORS["panel"],
            fg=COLORS["green"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        log_frame = tk.Frame(self.panel.body, bg="#050708", highlightbackground="#4b5660", highlightthickness=1)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            bg="#050708",
            fg="#d0d7de",
            insertbackground="#d0d7de",
            relief="flat",
            wrap="none",
            height=12,
            font=("Consolas", 9),
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.status = tk.Label(
            self.panel.body,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            anchor="w",
            justify="left",
        )
        self.status.pack(fill="x", pady=(6, 0))

    def _summary_row(self, parent: tk.Widget, row: int, label: str, value: str, attr_name: str) -> None:
        tk.Label(
            parent,
            text=f"{label}:",
            bg="#0a0d10",
            fg="#7a838a",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            width=16,
        ).grid(row=row, column=0, sticky="w", padx=(10, 6), pady=2)
        value_label = tk.Label(
            parent,
            text=value,
            bg="#0a0d10",
            fg="#ffffff",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        )
        value_label.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=2)
        parent.grid_columnconfigure(1, weight=1)
        setattr(self, attr_name, value_label)

    # ---------------------------------------------------------------------
    # Bridge actions
    # ---------------------------------------------------------------------

    def _sync(self) -> None:
        try:
            if hasattr(self.bridge, "sync"):
                self.bridge.sync(force=True)
        except TypeError:
            try:
                self.bridge.sync()
            except Exception:
                pass
        except Exception:
            pass
        self.refresh()

    def _connect(self) -> None:
        try:
            if hasattr(self.bridge, "connect_screen"):
                self.bridge.connect_screen(self.screen_key)
            elif hasattr(self.bridge, "nextion_connect_screen"):
                self.bridge.nextion_connect_screen(self.screen_key)
            elif hasattr(self.bridge, "nextion_connect"):
                self.bridge.nextion_connect()
        except Exception:
            pass
        self.refresh()

    def _disconnect(self) -> None:
        try:
            if hasattr(self.bridge, "disconnect_screen"):
                self.bridge.disconnect_screen(self.screen_key)
            elif hasattr(self.bridge, "nextion_disconnect_screen"):
                self.bridge.nextion_disconnect_screen(self.screen_key)
            elif hasattr(self.bridge, "nextion_disconnect_all"):
                self.bridge.nextion_disconnect_all()
        except Exception:
            pass
        self.refresh()

    # ---------------------------------------------------------------------
    # Status/log helpers
    # ---------------------------------------------------------------------

    def _snapshot(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        try:
            if hasattr(self.bridge, "snapshot"):
                snap = self.bridge.snapshot()
                if isinstance(snap, dict):
                    data.update(snap)
        except Exception:
            pass
        try:
            if hasattr(self.bridge, "get_nextion_monitor_state"):
                monitor = self.bridge.get_nextion_monitor_state(self.screen_key)
                if isinstance(monitor, dict):
                    data[f"{self.screen_key}.connected"] = monitor.get("connected", data.get(f"{self.screen_key}.connected"))
                    data[f"{self.screen_key}.port"] = monitor.get("port", data.get(f"{self.screen_key}.port"))
                    data[f"{self.screen_key}.baudrate"] = monitor.get("baudrate", data.get(f"{self.screen_key}.baudrate"))
                    data[f"{self.screen_key}.last_error"] = monitor.get("last_error", data.get(f"{self.screen_key}.last_error"))
                    data[f"{self.screen_key}.page"] = monitor.get("page", data.get(f"{self.screen_key}.page"))
                    data[f"{self.screen_key}.ui_cut"] = monitor.get("ui_cut", data.get(f"{self.screen_key}.ui_cut"))
                    data[f"{self.screen_key}.snajper_pending"] = monitor.get("pending", data.get(f"{self.screen_key}.snajper_pending"))
        except Exception:
            pass
        return data

    def _bridge_page_id(self) -> str:
        try:
            if hasattr(self.bridge, "get_page"):
                page = self.bridge.get_page(self.screen_key)
                if isinstance(page, dict):
                    return str(page.get("id", "") or "")
                return str(page or "")
        except Exception:
            pass
        return str(self.state.get(f"{self.screen_key}.page", "") or self.state.get("page", "") or "")

    def _device(self) -> Any:
        try:
            return getattr(self.bridge, "devices", {}).get(self.screen_key)
        except Exception:
            return None

    def _is_connected(self) -> bool:
        device = self._device()
        if device is not None and hasattr(device, "connected"):
            return bool(getattr(device, "connected", False))
        for key in (f"{self.screen_key}.connected", "connected"):
            if key in self.state:
                return self._as_bool(self.state.get(key))
        return False

    def _port(self) -> str:
        device = self._device()
        if device is not None and hasattr(device, "port"):
            port = getattr(device, "port", "")
            if port:
                return str(port)
        port = self.state.get(f"{self.screen_key}.port") or self.state.get("port")
        if port:
            return str(port)
        cfg = self.ports_cfg.get(self.screen_key, {}) if isinstance(self.ports_cfg, dict) else {}
        return str(cfg.get("port", "-"))

    def _baudrate(self) -> str:
        device = self._device()
        if device is not None and hasattr(device, "baudrate"):
            baud = getattr(device, "baudrate", "")
            if baud:
                return str(baud)
        cfg = self.ports_cfg.get(self.screen_key, {}) if isinstance(self.ports_cfg, dict) else {}
        return str(cfg.get("baudrate", "-"))

    def _last_error(self) -> str:
        device = self._device()
        if device is not None:
            err = getattr(device, "last_error", None)
            if err:
                return str(err)
        return str(self.state.get(f"{self.screen_key}.last_error", "") or self.state.get("last_error", "") or "-")

    def _recent_logs(self, limit: int = 120) -> List[str]:
        collected: List[str] = []

        if hasattr(self.bridge, "get_recent_transport_log"):
            try:
                logs = self.bridge.get_recent_transport_log(self.screen_key, limit=limit)
                if logs:
                    collected.extend([self._format_log_line(line) for line in logs])
            except TypeError:
                try:
                    logs = self.bridge.get_recent_transport_log(limit=limit)
                    if logs:
                        collected.extend([self._format_log_line(line) for line in logs])
                except Exception:
                    pass
            except Exception:
                pass

        if not collected and hasattr(self.bridge, "last_commands"):
            try:
                collected.extend([f"TX: {line}" for line in list(self.bridge.last_commands)[-limit:]])
            except Exception:
                pass

        if self._manual_log_lines:
            collected.extend([self._format_log_line(line) for line in self._manual_log_lines[-limit:]])

        # usunięcie prostych duplikatów przy zachowaniu kolejności
        deduped: List[str] = []
        seen = set()
        for line in collected:
            key = str(line)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(key)

        return deduped[-limit:]

    def _format_log_line(self, line: Any) -> str:
        if isinstance(line, dict):
            direction = str(line.get("direction") or line.get("dir") or line.get("type") or "LOG").upper()
            payload = line.get("payload") or line.get("message") or line.get("text") or line
            return f"{direction}: {payload}"
        text = str(line)
        if "sys:ui_cut=" in text or "set:ui_cut=" in text:
            self._update_ui_cut_from_text(text)
        return text

    def _refresh_transport_log(self) -> None:
        logs = self._recent_logs(limit=self.LOG_LIMIT)
        if not logs:
            logs = ["Brak logów transportu z Bridge."]
        signature = "\n".join(logs[-self.LOG_LIMIT:])
        if signature == self._last_log_signature:
            return
        self._last_log_signature = signature
        self._last_log_lines = logs[-self.LOG_LIMIT:]

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self._last_log_lines))
        self.log_text.insert("end", "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log_view(self) -> None:
        self._last_log_signature = ""
        self._last_log_lines = []
        self._manual_log_lines = []
        if hasattr(self.bridge, "clear_transport_log"):
            try:
                self.bridge.clear_transport_log(self.screen_key)
            except TypeError:
                try:
                    self.bridge.clear_transport_log()
                except Exception:
                    pass
            except Exception:
                pass
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _update_ui_cut_from_state(self) -> None:
        value = None
        for key in (
            f"{self.screen_key}.ui_cut",
            "nextion_ui_cut",
            "par_nextion_ui_cut",
        ):
            if key in self.state:
                value = self.state.get(key)
                break
        if value is not None:
            self.set_ui_cut(self._as_bool(value))

    def _update_connection_labels(self) -> None:
        connected = self._is_connected()
        self.port_value.configure(text=self._port())
        self.baud_value.configure(text=self._baudrate())
        self.connected_value.configure(
            text="YES" if connected else "NO",
            fg=COLORS["green"] if connected else COLORS["red"],
        )
        self.error_value.configure(text="-" if connected else self._last_error())

    def _update_page_label(self) -> None:
        page = self.current_page_id or "-"
        self.current_page_value.configure(text=page)
        self.page_label.configure(text=f"PAGE: {page.upper()}")

    def _update_status_line(self) -> None:
        self.status.configure(
            text=(
                f"PORT: {self._port()}   "
                f"BAUD: {self._baudrate()}   "
                f"COM: {'OK' if self._is_connected() else 'OFF'}   "
                f"PAGE: {self.current_page_id or '-'}   "
                f"UI CUT: {'ON' if self.ui_cut else 'OFF'}   "
                f"PENDING: {self.state.get(f'{self.screen_key}.snajper_pending', '-')}"
            )
        )

    def _update_ui_cut_from_text(self, text: str) -> None:
        lower = text.lower()
        if "sys:ui_cut=1" in lower or "set:ui_cut=1" in lower:
            self.set_ui_cut(True)
        elif "sys:ui_cut=0" in lower or "set:ui_cut=0" in lower:
            self.set_ui_cut(False)

    # ---------------------------------------------------------------------
    # Config helpers
    # ---------------------------------------------------------------------

    def _load_settings(self) -> Dict[str, Any]:
        root = Path(__file__).resolve().parents[2]
        settings_path = root / "data" / "nextion" / f"{self.screen_key}_settings.json"
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _load_ports_cfg(self) -> Dict[str, Any]:
        root = Path(__file__).resolve().parents[2]
        ports_path = root / "data" / "nextion" / "nextion_ports.json"
        try:
            data = json.loads(ports_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "on", "ui_cut", "cut"}


# Backward-compatible alias used by older imports/tests.
NextionPreviewPanel = TarzanNextionPreviewPanel
