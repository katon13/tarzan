"""Most PAR ↔ SignalBus ↔ TAKE."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional

from core.tarzanSignalBus import TarzanSignalBus, get_signal_bus
try:
    from editor.PAR.tarzanParProtocolMapper import TarzanParProtocolMapper
except ModuleNotFoundError:
    from tarzanParProtocolMapper import TarzanParProtocolMapper
try:
    from editor.PAR.tarzanParTakePlayer import TarzanParTakePlayer, TarzanTakeData
except ModuleNotFoundError:
    from tarzanParTakePlayer import TarzanParTakePlayer, TarzanTakeData


class TarzanParBridge:
    def __init__(
        self,
        bus: Optional[TarzanSignalBus] = None,
        after: Optional[Callable[..., Any]] = None,
        after_cancel: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.bus = bus or get_signal_bus("TEST")
        self.mapper = TarzanParProtocolMapper(self.bus.names())
        self.take_player = TarzanParTakePlayer(self.bus, self.mapper)
        if after is not None and after_cancel is not None:
            self.take_player.set_scheduler(after, after_cancel)
        
        # NEXTION SNAJPER: fizyczny most Nextiona jako pod-komponent
        from hardware.tarzanNextion.bridge import TarzanNextionBridge
        self.nextion = TarzanNextionBridge(self.bus)

    def nextion_connect(self):
        return self.nextion.connect_enabled()

    def nextion_sync(self, force: bool = False):
        return self.nextion.sync(force=force)

    def poll(self):
        return self.nextion.poll()

    def flush_snajper_commands(self):
        if hasattr(self.nextion, "flush_snajper_commands"):
            return self.nextion.flush_snajper_commands()

    def queue_snajper_command(self, scope: str, component: str, prop: str, value):
        if hasattr(self.nextion, "queue_snajper_command"):
            return self.nextion.queue_snajper_command(scope, component, prop, value)

    def set_mode(self, mode: str) -> None:
        self.bus.set_mode(mode)

    def read_input(self, name: str, default: Any = 0) -> Any:
        return self.bus.read_input(name, default)

    def set_input(self, name: str, value: Any, source: str = "PAR") -> bool:
        return self.bus.set_input(name, value, source=source)

    def write_output(self, name: str, value: Any, source: str = "PAR") -> bool:
        return self.bus.write_output(name, value, source=source)

    def force_signal(self, name: str, value: Any, source: str = "PAR_FORCE") -> bool:
        return self.bus.force_signal(name, value, source=source)

    def snapshot(self, include_meta: bool = False) -> Dict[str, Any]:
        return self.bus.snapshot(include_meta=include_meta)

    def load_take(self, path: str | Path) -> TarzanTakeData:
        return self.take_player.load(path)

    def play_take(self) -> None:
        self.take_player.play()

    def pause_take(self) -> None:
        self.take_player.pause()

    def stop_take(self) -> None:
        self.take_player.stop()

    def step_take_index(self, index: int):
        return self.take_player.step_to_index(index)

    def step_take_time(self, time_ms: int):
        return self.take_player.step_time(time_ms)

    def take_column_map(self):
        return self.mapper.map_take_columns()
