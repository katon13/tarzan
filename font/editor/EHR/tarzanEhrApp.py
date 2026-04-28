from __future__ import annotations

# Shim zgodności importów. UI Tkinter EHR jest teraz w editor/tarzanEHR.py.

from editor.EHR.tarzanEhrUi import AxisSettingsDialog, TarzanEhrMultiAxisWindow, main

__all__ = ["AxisSettingsDialog", "TarzanEhrMultiAxisWindow", "main"]
