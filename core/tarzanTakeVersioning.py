from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


class TarzanTakeVersioning:
    """
    Obsługa wersjonowania TAKE.

    Tworzy nową wersję pliku:
    TAKE_001_v01.json -> TAKE_001_v02.json
    """

    VERSION_PATTERN = re.compile(r"_v(\d+)\.json$", re.IGNORECASE)

    def get_next_version_path(self, take_path: Path) -> Path:
        """
        Oblicza nazwę kolejnej wersji TAKE.
        """
        name = take_path.name
        match = self.VERSION_PATTERN.search(name)

        if not match:
            raise ValueError(f"Nie można rozpoznać wersji w nazwie pliku: {name}")

        version_number = int(match.group(1))
        next_version = version_number + 1

        next_name = name.replace(
            f"_v{version_number:02d}.json",
            f"_v{next_version:02d}.json",
        )

        return take_path.parent / next_name

    def save_new_take(
        self,
        original_take_path: Path,
        take_dict: dict,
    ) -> Path:
        """
        Zapisuje nową wersję TAKE.
        """
        new_path = self.get_next_version_path(original_take_path)

        now = datetime.now().isoformat(timespec="seconds")

        if "metadata" in take_dict:
            take_dict["metadata"]["version"] = self._extract_version(new_path.name)
            take_dict["metadata"]["edited_at"] = now

        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(take_dict, f, indent=2, ensure_ascii=False)

        return new_path

    def _extract_version(self, filename: str) -> str:
        match = self.VERSION_PATTERN.search(filename)
        if not match:
            return "v??"
        return f"v{int(match.group(1)):02d}"