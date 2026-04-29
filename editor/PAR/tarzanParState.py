from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List
from editor.PAR.tarzanParSignalsAdapter import ParSignal


@dataclass
class ParSignalState:
    signal: ParSignal
    value: Any
    forced: bool = False
    source: str = "TEST"
    last_change: float = field(default_factory=time.time)


class TarzanParState:
    def __init__(self, signals: List[ParSignal]) -> None:
        self.mode = "TEST"
        self.signals = signals
        self.states: Dict[str, ParSignalState] = {}
        self.subscribers: List[Callable[[str, ParSignalState], None]] = []
        self.log_lines: List[str] = []

        for signal in signals:
            self.states[signal.nazwa] = ParSignalState(signal=signal, value=self._default(signal))

        self.log("PAR", "Start pulpitu anatomii ruchu")

    def _default(self, signal: ParSignal):
        if signal.typ == "ANALOG":
            return 50
        if signal.typ in {"F", "RESERVED"}:
            return None
        return 1 if str(signal.default).strip() == "1" else 0

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def notify(self, name: str):
        state = self.states[name]
        for callback in self.subscribers:
            callback(name, state)

    def set_mode(self, mode: str):
        self.mode = mode
        self.log("MODE", f"Tryb PAR: {mode}")
        for name in list(self.states):
            self.states[name].source = mode
            self.notify(name)

    def set_value(self, name: str, value, origin: str = "UI", forced: bool = True):
        if name not in self.states:
            return
        state = self.states[name]
        state.value = value
        state.forced = forced
        state.last_change = time.time()
        self.log(origin, f"{name} = {value}")
        self.notify(name)

    def toggle(self, name: str):
        if name not in self.states:
            return
        current = self.states[name].value
        self.set_value(name, 0 if current else 1)

    def get(self, name: str):
        return self.states[name].value if name in self.states else 0

    def log(self, source: str, message: str):
        self.log_lines.append(f"{time.strftime('%H:%M:%S')} [{source}] {message}")
        self.log_lines = self.log_lines[-500:]
