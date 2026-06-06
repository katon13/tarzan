from __future__ import annotations

"""Globalny strażnik dostępu do fizycznego hardware TARZAN.

Jeden właściciel sprzętu naraz. Runtime HardwareBridge trzyma blokadę,
a diagnostyka/testery mają dostać BUSY zamiast równolegle otwierać/zamykać
PoKeys i ryzykować crash libusb/hid_close.
"""

import os
import threading
from pathlib import Path

try:
    import fcntl  # type: ignore
except Exception:  # Windows fallback
    fcntl = None  # type: ignore


class TarzanHardwareAccessBusy(RuntimeError):
    pass


class TarzanHardwareAccessGuard:
    _process_lock = threading.RLock()

    def __init__(self, owner: str, blocking: bool = True) -> None:
        self.owner = str(owner or "UNKNOWN")
        self.blocking = bool(blocking)
        self._fh = None
        self.acquired = False

    @staticmethod
    def lock_path() -> Path:
        return Path(os.environ.get("TARZAN_HW_LOCK_FILE", "/tmp/tarzan_hardware_access.lock"))

    def acquire(self) -> bool:
        if self.acquired:
            return True
        got_thread_lock = TarzanHardwareAccessGuard._process_lock.acquire(blocking=self.blocking)
        if not got_thread_lock:
            return False
        try:
            path = self.lock_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(path, "a+", encoding="utf-8")
            if fcntl is not None:
                flags = fcntl.LOCK_EX
                if not self.blocking:
                    flags |= fcntl.LOCK_NB
                try:
                    fcntl.flock(self._fh.fileno(), flags)
                except BlockingIOError:
                    self._fh.close()
                    self._fh = None
                    TarzanHardwareAccessGuard._process_lock.release()
                    return False
            self._fh.seek(0)
            self._fh.truncate()
            self._fh.write(f"{os.getpid()} {self.owner}\n")
            self._fh.flush()
            self.acquired = True
            return True
        except Exception:
            if self._fh is not None:
                try:
                    self._fh.close()
                except Exception:
                    pass
                self._fh = None
            TarzanHardwareAccessGuard._process_lock.release()
            raise

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            if self._fh is not None and fcntl is not None:
                try:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
            if self._fh is not None:
                try:
                    self._fh.close()
                except Exception:
                    pass
        finally:
            self._fh = None
            self.acquired = False
            try:
                TarzanHardwareAccessGuard._process_lock.release()
            except RuntimeError:
                pass

    def __enter__(self) -> "TarzanHardwareAccessGuard":
        if not self.acquire():
            raise TarzanHardwareAccessBusy(f"hardware access busy; owner={self.current_owner()}")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    @classmethod
    def current_owner(cls) -> str:
        try:
            path = cls.lock_path()
            if path.exists():
                return path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            pass
        return "UNKNOWN"
