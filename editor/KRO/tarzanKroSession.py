from __future__ import annotations

import copy
from dataclasses import dataclass, field

from editor.KRO.tarzanKroTypes import KroRelationSpec


@dataclass
class KroTargetBackup:
    target_axis_id: str
    nodes_snapshot: list[object]


@dataclass
class KroSession:
    relations: list[KroRelationSpec] = field(default_factory=list)
    target_backups: dict[str, KroTargetBackup] = field(default_factory=dict)

    def relation_for_target(self, target_axis_id: str) -> KroRelationSpec | None:
        for relation in self.relations:
            if relation.target_axis_id == target_axis_id:
                return relation
        return None

    def relations_from_source(self, source_axis_id: str) -> list[KroRelationSpec]:
        return [r for r in self.relations if r.source_axis_id == source_axis_id]

    def add_or_replace_relation(self, relation: KroRelationSpec) -> None:
        relation.clamp()

        # Jeden TARGET ma jedną relację wejściową.
        self.relations = [r for r in self.relations if r.target_axis_id != relation.target_axis_id]
        self.relations.append(relation)

    def remove_relation(self, relation_id: str) -> KroRelationSpec | None:
        found = None
        kept: list[KroRelationSpec] = []
        for relation in self.relations:
            if relation.relation_id == relation_id:
                found = relation
            else:
                kept.append(relation)
        self.relations = kept
        return found

    def backup_target_if_needed(self, target_axis_id: str, nodes: list[object]) -> None:
        if target_axis_id not in self.target_backups:
            self.target_backups[target_axis_id] = KroTargetBackup(
                target_axis_id=target_axis_id,
                nodes_snapshot=copy.deepcopy(nodes),
            )

    def pop_backup(self, target_axis_id: str) -> list[object] | None:
        backup = self.target_backups.pop(target_axis_id, None)
        if backup is None:
            return None
        return copy.deepcopy(backup.nodes_snapshot)

    def clear_backup(self, target_axis_id: str) -> None:
        self.target_backups.pop(target_axis_id, None)

    def would_create_cycle(self, source_axis_id: str, target_axis_id: str) -> bool:
        """
        Blokada cyklu:
        jeżeli target może dojść po relacjach do source, to source→target robi cykl.
        """
        visited: set[str] = set()
        stack = [target_axis_id]

        while stack:
            current = stack.pop()
            if current == source_axis_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            for relation in self.relations:
                if relation.source_axis_id == current:
                    stack.append(relation.target_axis_id)

        return False
