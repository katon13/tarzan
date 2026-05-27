from __future__ import annotations

import tkinter as tk
from typing import Optional

from editor.KRO.tarzanKroTypes import KroPluginType, KroRelationSpec


class KroConnectorUi:
    def __init__(self, adapter) -> None:
        self.adapter = adapter
        self.drag_source_axis_index: int | None = None
        self.drag_current_xy: tuple[int, int] | None = None

    @property
    def window(self):
        return self.adapter.window

    def get_anchor_point(self, axis_index: int) -> tuple[int, int]:
        rect = self.window.axis_rects.get(axis_index)
        if rect is None:
            return (0, 0)
        return (int(rect.left - 130), int((rect.top + rect.bottom) / 2) - 15)

    def draw(self, canvas: tk.Canvas) -> None:
        # Anchory
        for axis_index, rect in self.window.axis_rects.items():
            model = self.window.axis_models[axis_index]
            if getattr(model, "is_release_axis", False):
                continue

            x, y = self.get_anchor_point(axis_index)
            canvas.create_oval(
                x - 5,
                y - 5,
                x + 5,
                y + 5,
                fill="#FFCC00",
                outline="",
                width=0,
                tags=("kro", "kro_anchor", f"kro_anchor_{axis_index}"),
            )

        # Linia tymczasowa drag
        if self.drag_source_axis_index is not None and self.drag_current_xy is not None:
            sx, sy = self.get_anchor_point(self.drag_source_axis_index)
            cx, cy = self.drag_current_xy
            canvas.create_line(
                sx,
                sy,
                cx,
                cy,
                fill="#FFCC00",
                dash=(3, 2),
                width=2,
                arrow="last",
                arrowshape=(10, 12, 4),
                tags=("kro", "kro_drag"),
            )

        # Relacje
        for relation in self.adapter.session.relations:
            src_idx = self.adapter.axis_index_by_id(relation.source_axis_id)
            tgt_idx = self.adapter.axis_index_by_id(relation.target_axis_id)
            if src_idx is None or tgt_idx is None:
                continue

            sx, sy = self.get_anchor_point(src_idx)
            tx, ty = self.get_anchor_point(tgt_idx)

            color = "#FFCC00" if relation.enabled else "#555555"
            canvas.create_line(
                sx,
                sy,
                tx,
                ty,
                fill=color,
                width=2,
                dash=(3, 2),
                arrow="last",
                arrowshape=(10, 12, 4),
                tags=("kro", "kro_relation", relation.relation_id),
            )

            label = f"[{relation.normalized_plugin_type().value}]"
            canvas.create_text(
                (sx + tx) / 2 - 35,
                (sy + ty) / 2,
                text=label,
                fill="#FFFFFF",
                font=("Segoe UI", 8, "bold"),
                anchor="e",
                tags=("kro", "kro_badge", relation.relation_id),
            )

    def handle_press(self, x: int, y: int, x_root: int, y_root: int) -> bool:
        axis_idx = self.hit_anchor(x, y)
        if axis_idx is not None:
            self.drag_source_axis_index = axis_idx
            self.drag_current_xy = (x, y)
            return True

        relation = self.hit_relation(x, y)
        if relation is not None:
            self.show_relation_menu(relation, x_root, y_root)
            return True

        return False

    def handle_drag(self, x: int, y: int) -> bool:
        if self.drag_source_axis_index is None:
            return False
        self.drag_current_xy = (x, y)
        return True

    def handle_release(self, x: int, y: int) -> bool:
        if self.drag_source_axis_index is None:
            return False

        source_idx = self.drag_source_axis_index
        target_idx = self.hit_anchor(x, y)

        self.drag_source_axis_index = None
        self.drag_current_xy = None

        if target_idx is None or target_idx == source_idx:
            return True

        self.adapter.create_relation_by_indices(source_idx, target_idx)
        return True

    def handle_right_click(self, x: int, y: int) -> bool:
        relation = self.hit_relation(x, y)
        if relation is None:
            return False
        self.adapter.remove_relation(relation.relation_id, restore_backup=True)
        return True

    def hit_anchor(self, x: int, y: int) -> int | None:
        for axis_index, _rect in self.window.axis_rects.items():
            model = self.window.axis_models[axis_index]
            if getattr(model, "is_release_axis", False):
                continue
            ax, ay = self.get_anchor_point(axis_index)
            if (x - ax) ** 2 + (y - ay) ** 2 <= 10 ** 2:
                return axis_index
        return None

    def hit_relation(self, x: int, y: int) -> KroRelationSpec | None:
        for relation in self.adapter.session.relations:
            src_idx = self.adapter.axis_index_by_id(relation.source_axis_id)
            tgt_idx = self.adapter.axis_index_by_id(relation.target_axis_id)
            if src_idx is None or tgt_idx is None:
                continue

            sx, sy = self.get_anchor_point(src_idx)
            tx, ty = self.get_anchor_point(tgt_idx)

            # Badge hit
            bx = (sx + tx) / 2 - 35
            by = (sy + ty) / 2
            if abs(x - (bx - 30)) <= 34 and abs(y - by) <= 14:
                return relation

            # Line hit
            if self._dist_point_segment(x, y, sx, sy, tx, ty) <= 14:
                return relation

        return None

    @staticmethod
    def _dist_point_segment(px, py, x1, y1, x2, y2) -> float:
        line_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_len <= 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len ** 2)
        t = max(0.0, min(1.0, t))
        xx = x1 + t * (x2 - x1)
        yy = y1 + t * (y2 - y1)
        return ((px - xx) ** 2 + (py - yy) ** 2) ** 0.5

    def show_relation_menu(self, relation: KroRelationSpec, x_root: int, y_root: int) -> None:
        menu = tk.Menu(self.window, tearoff=0)

        for plugin_type in KroPluginType:
            menu.add_command(
                label=plugin_type.value,
                command=lambda p=plugin_type: self.adapter.change_relation_plugin(relation.relation_id, p),
            )

        menu.add_separator()
        menu.add_command(
            label="KRO OFF / PRZYWRÓĆ TARGET",
            command=lambda: self.adapter.disable_relation(relation.relation_id, restore_backup=True),
        )
        menu.add_command(
            label="ZASTOSUJ I ZOSTAW LINIĘ",
            command=lambda: self.adapter.accept_relation_result(relation.relation_id),
        )
        menu.add_command(
            label="USUŃ RELACJĘ",
            command=lambda: self.adapter.remove_relation(relation.relation_id, restore_backup=True),
            foreground="red",
        )

        menu.post(x_root, y_root)
