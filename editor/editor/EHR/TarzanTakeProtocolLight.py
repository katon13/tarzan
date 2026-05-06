from __future__ import annotations

# Shim zgodności importów. UI TAKE PROTOCOL LIGHT jest teraz w editor/tarzanEHR.py.

from editor.EHR.tarzanEhrUi import (
    UiSettings, SlotRecord, SlotStore, SlotState, SlotVM, IconRenderer,
    SlotWidget, TarzanTakeProtocolLightWidget, ensure_dirs, take_path_from_record,
    extract_number_from_take_id, extract_number_from_filename, extract_version_from_filename,
    read_take_number, read_take_version, copy_take_into_project, project_take_icon_path,
    chalk_font_candidates, normal_font_candidates, fit_font,
)

__all__ = [
    "UiSettings", "SlotRecord", "SlotStore", "SlotState", "SlotVM", "IconRenderer",
    "SlotWidget", "TarzanTakeProtocolLightWidget", "ensure_dirs", "take_path_from_record",
    "extract_number_from_take_id", "extract_number_from_filename", "extract_version_from_filename",
    "read_take_number", "read_take_version", "copy_take_into_project", "project_take_icon_path",
    "chalk_font_candidates", "normal_font_candidates", "fit_font",
]
