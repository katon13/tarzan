from __future__ import annotations

import time
import tkinter as tk
from typing import Optional

try:
    from hardware.tarzanNextion.device import TarzanNextionDevice
    from hardware.tarzanNextion.protocol import command_bytes
except ModuleNotFoundError:
    from device import TarzanNextionDevice
    from protocol import command_bytes


TERMINATOR = b"\xff\xff\xff"


def _decode_packet(raw: bytes) -> str:
    if not raw:
        return "<empty>"
    if raw.startswith(b"comok"):
        try:
            return raw.decode("ascii", errors="replace")
        except Exception:
            return repr(raw)
    code = raw[0]
    if code == 0x00:
        return "Invalid instruction"
    if code == 0x01:
        return "Command executed successfully"
    if code == 0x65 and len(raw) >= 4:
        return f"Touch event: page={raw[1]} component={raw[2]} event={raw[3]}"
    if code == 0x66 and len(raw) >= 2:
        return f"Current page id: {raw[1]}"
    if code == 0x70:
        try:
            return f"String return: {raw[1:].decode('latin1', errors='replace')}"
        except Exception:
            return repr(raw)
    if code == 0x71 and len(raw) >= 5:
        value = int.from_bytes(raw[1:5], "little", signed=False)
        return f"Numeric return: {value}"
    return repr(raw)


class TarzanNextionSandbox(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TARZAN NEXTION SANDBOX SIMPLE")
        self.geometry("1060x760")
        self.minsize(920, 640)
        self.configure(bg="#0b1116")

        self.device: Optional[TarzanNextionDevice] = None
        self.online = False
        self.sent_count = 0
        self.recv_count = 0

        self.port_var = tk.StringVar(value="COM7")
        self.baud_var = tk.StringVar(value="9600")
        self.page_var = tk.StringVar(value="boot")
        self.text_component_var = tk.StringVar(value="t0")
        self.text_value_var = tk.StringVar(value="HELLO TARZAN")
        self.raw_cmd_var = tk.StringVar(value="connect")
        self.status_var = tk.StringVar(value="OFF")
        self.error_var = tk.StringVar(value="-")
        self.sent_var = tk.StringVar(value="0")
        self.recv_var = tk.StringVar(value="0")

        self._build_ui()
        self.after(50, self._tick)

    def _build_ui(self) -> None:
        top = tk.Frame(self, bg="#101820")
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="PORT", bg="#101820", fg="#dbe6ee", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(8, 4), pady=8)
        tk.Entry(top, textvariable=self.port_var, bg="#071015", fg="#dbe6ee", insertbackground="#dbe6ee", width=10).grid(row=0, column=1, sticky="w", padx=(0, 10))
        tk.Label(top, text="BAUD", bg="#101820", fg="#dbe6ee", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(8, 4))
        tk.Entry(top, textvariable=self.baud_var, bg="#071015", fg="#dbe6ee", insertbackground="#dbe6ee", width=10).grid(row=0, column=3, sticky="w", padx=(0, 10))
        tk.Button(top, text="POŁĄCZ", command=self.connect_auto, bg="#193246", fg="#ffffff", relief="flat", padx=18).grid(row=0, column=4, padx=6)
        tk.Button(top, text="ROZŁĄCZ", command=self.disconnect, bg="#3b2226", fg="#ffffff", relief="flat", padx=18).grid(row=0, column=5, padx=6)

        status = tk.Frame(self, bg="#101820")
        status.pack(fill="x", padx=10)
        for i in range(4):
            status.grid_columnconfigure(i, weight=1)

        def stat(title: str, var: tk.StringVar, col: int):
            box = tk.Frame(status, bg="#16222c", highlightbackground="#27404f", highlightthickness=1)
            box.grid(row=0, column=col, sticky="ew", padx=4, pady=6)
            tk.Label(box, text=title, bg="#16222c", fg="#8fa6b5", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
            tk.Label(box, textvariable=var, bg="#16222c", fg="#30ef42", font=("Consolas", 12, "bold")).pack(anchor="w", padx=8, pady=(0, 6))

        stat("STATUS", self.status_var, 0)
        stat("BŁĄD", self.error_var, 1)
        stat("WYSŁANE", self.sent_var, 2)
        stat("ODEBRANE", self.recv_var, 3)

        actions = tk.Frame(self, bg="#0b1116")
        actions.pack(fill="x", padx=10, pady=(6, 8))
        actions.grid_columnconfigure(1, weight=1)
        actions.grid_columnconfigure(2, weight=1)

        tk.Label(actions, text="PAGE", bg="#0b1116", fg="#dbe6ee").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        tk.Entry(actions, textvariable=self.page_var, bg="#071015", fg="#dbe6ee", insertbackground="#dbe6ee", width=16).grid(row=0, column=1, sticky="w", pady=4)
        tk.Button(actions, text="SEND page", command=self.send_page, bg="#263741", fg="#ffffff", relief="flat", padx=14).grid(row=0, column=2, padx=8, pady=4, sticky="w")

        tk.Label(actions, text="TEXT COMP", bg="#0b1116", fg="#dbe6ee").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        tk.Entry(actions, textvariable=self.text_component_var, bg="#071015", fg="#dbe6ee", insertbackground="#dbe6ee", width=16).grid(row=1, column=1, sticky="w", pady=4)
        tk.Entry(actions, textvariable=self.text_value_var, bg="#071015", fg="#dbe6ee", insertbackground="#dbe6ee").grid(row=1, column=2, sticky="ew", padx=(8, 8), pady=4)
        tk.Button(actions, text="SEND text", command=self.send_text, bg="#263741", fg="#ffffff", relief="flat", padx=14).grid(row=1, column=3, padx=8, pady=4)

        tk.Label(actions, text="RAW CMD", bg="#0b1116", fg="#dbe6ee").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        tk.Entry(actions, textvariable=self.raw_cmd_var, bg="#071015", fg="#dbe6ee", insertbackground="#dbe6ee").grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        tk.Button(actions, text="SEND raw", command=self.send_raw_command, bg="#263741", fg="#ffffff", relief="flat", padx=14).grid(row=2, column=3, padx=8, pady=4)

        log_box = tk.Frame(self, bg="#101820", highlightbackground="#27404f", highlightthickness=1)
        log_box.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        tk.Label(log_box, text="LOG UART", bg="#101820", fg="#dbe6ee", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=8)

        self.log = tk.Text(log_box, bg="#05090d", fg="#dbe6ee", insertbackground="#dbe6ee", relief="flat", wrap="word")
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log.tag_configure("tx", foreground="#61c9ff")
        self.log.tag_configure("rx", foreground="#24e22d")
        self.log.tag_configure("err", foreground="#ff6a6a")
        self.log.tag_configure("info", foreground="#f0a622")

    def _append_log(self, text: str, tag: str = "info") -> None:
        ts = time.strftime("%H:%M:%S")
        self.log.insert("end", f"[{ts}] {text}\n", tag)
        self.log.see("end")

    def _update_status(self) -> None:
        if self.online:
            self.status_var.set("ONLINE")
        elif self.device and self.device.connected:
            self.status_var.set("PORT OPEN")
        else:
            self.status_var.set("OFF")
        err = "-"
        if self.device and self.device.last_error:
            err = self.device.last_error
        self.error_var.set(err)
        self.sent_var.set(str(self.sent_count))
        self.recv_var.set(str(self.recv_count))

    def _open_device(self, baud: int) -> bool:
        self.disconnect(silent=True)
        self.device = TarzanNextionDevice("nextion_7_sandbox", self.port_var.get().strip(), baud)
        ok = self.device.open()
        self.online = False
        self._update_status()
        if ok:
            self._append_log(f"OPEN {self.device.port} @ {self.device.baudrate}", "info")
            self.clear_rx(log_it=False)
            return True
        self._append_log(f"OPEN ERROR: {self.device.last_error or '-'}", "err")
        return False

    def _handshake(self, wait_ms: int = 100) -> bool:
        if self.device is None or not self.device.connected:
            return False
        self._send_payload("connect", command_bytes("connect"), auto_log=True)
        end = time.time() + (wait_ms / 1000.0)
        while time.time() < end:
            events = self.device.poll()
            if events:
                for ev in events:
                    self.recv_count += 1
                    self._append_log(f"RX {ev.raw!r} | {_decode_packet(ev.raw)}", "rx")
                    if ev.raw.startswith(b"comok"):
                        self.online = True
                        self._update_status()
                        self._append_log("HANDSHAKE OK", "info")
                        self.baud_var.set(str(self.device.baudrate))
                        return True
            time.sleep(0.01)
        self.online = False
        self._update_status()
        self._append_log(f"HANDSHAKE FAIL (brak odpowiedzi w {wait_ms} ms)", "err")
        return False

    def connect_auto(self) -> None:
        preferred = int((self.baud_var.get() or "9600").strip())
        bauds = [preferred] + [b for b in (9600, 115200, 57600, 38400, 19200) if b != preferred]
        for baud in bauds:
            if not self._open_device(baud):
                return
            if self._handshake(100):
                self._append_log(f"CONNECTED AT {baud}", "info")
                return
        self._append_log("AUTO CONNECT FAIL", "err")

    def disconnect(self, silent: bool = False) -> None:
        if self.device is not None:
            port = self.device.port
            self.device.close()
            self.online = False
            self._update_status()
            if not silent:
                self._append_log(f"CLOSE {port}", "info")

    def clear_rx(self, log_it: bool = True) -> None:
        if self.device is not None:
            try:
                self.device.read_buffer.clear()
                if self.device.serial_port is not None:
                    self.device.serial_port.reset_input_buffer()
            except Exception:
                pass
        if log_it:
            self._append_log("RX BUFFER CLEARED", "info")

    def _send_payload(self, label: str, payload: bytes, auto_log: bool = False) -> None:
        if self.device is None or not self.device.connected:
            self.connect_auto()
        if self.device is None:
            return
        ok = self.device.send_raw(payload)
        if ok:
            self.sent_count += 1
            self._append_log(f"TX {label}: {payload!r}", "tx")
        else:
            self._append_log(f"TX ERROR {label}: {self.device.last_error or '-'}", "err")
        self._update_status()

    def send_page(self) -> None:
        page = self.page_var.get().strip()
        self._send_payload(f"page {page}", command_bytes(f"page {page}"))

    def send_text(self) -> None:
        comp = self.text_component_var.get().strip() or "t0"
        value = self.text_value_var.get()
        safe = value.replace('"', r'\"')
        self._send_payload(f"{comp}.txt", command_bytes(f'{comp}.txt="{safe}"'))

    def send_raw_command(self) -> None:
        real_cmd = self.raw_cmd_var.get().strip()
        if not real_cmd:
            return
        self._send_payload(real_cmd, command_bytes(real_cmd))

    def _tick(self) -> None:
        if self.device is not None and self.device.connected:
            events = self.device.poll()
            for ev in events:
                self.recv_count += 1
                self._append_log(f"RX {ev.raw!r} | {_decode_packet(ev.raw)}", "rx")
        self._update_status()
        self.after(50, self._tick)


if __name__ == "__main__":
    TarzanNextionSandbox().mainloop()
