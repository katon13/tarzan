from __future__ import annotations

from abc import ABC, abstractmethod

from editor.KRO.tarzanKroTypes import KroAxisLine, KroBuildResult, KroPluginType, KroRelationSpec, KroTuningProfile, KroAxisMechanicalProfile
from editor.KRO.tarzanKroLineTools import clamp_y, sorted_points, value_at
from editor.KRO.tarzanKroGeometryTransformer import KroGeometryTransformer


class KroPlugin(ABC):
    plugin_type: KroPluginType

    @abstractmethod
    def build_target_line(
        self,
        *,
        source_line: KroAxisLine,
        target_line: KroAxisLine,
        source_mech: KroAxisMechanicalProfile | None = None,
        target_mech: KroAxisMechanicalProfile | None = None,
        relation: KroRelationSpec,
        tuning: KroTuningProfile | None = None,
    ) -> KroBuildResult:
        raise NotImplementedError


class KroKontraPlugin(KroPlugin):
    plugin_type = KroPluginType.KONTRA

    def build_target_line(
        self,
        *,
        source_line: KroAxisLine,
        target_line: KroAxisLine,
        source_mech: KroAxisMechanicalProfile | None = None,
        target_mech: KroAxisMechanicalProfile | None = None,
        relation: KroRelationSpec,
        tuning: KroTuningProfile | None = None,
    ) -> KroBuildResult:
        relation.clamp()
        # Interpretacja pluginu: KONTRA to odwrócenie kierunku
        base_multiplier = -1.0
        
        tuning = tuning or KroTuningProfile()
        source_mech = source_mech or KroAxisMechanicalProfile(axis_id=source_line.axis_id)
        target_mech = target_mech or KroAxisMechanicalProfile(axis_id=target_line.axis_id)

        # Używamy zaawansowanego transformatora geometrii
        transformer = KroGeometryTransformer(
            source_line=source_line,
            target_line=target_line,
            source_mech=source_mech,
            target_mech=target_mech,
            tuning=tuning,
            plugin_base_multiplier=base_multiplier
        )
        
        new_points = transformer.transform()

        return KroBuildResult(
            target_axis_id=target_line.axis_id,
            plugin_type=self.plugin_type,
            new_points=new_points,
            status=f"KRO KONTRA: {source_line.axis_id} → {target_line.axis_id} (geometry transformer)",
        )


class KroFollowPlugin(KroPlugin):
    plugin_type = KroPluginType.FOLLOW

    def build_target_line(
        self,
        *,
        source_line: KroAxisLine,
        target_line: KroAxisLine,
        source_mech: KroAxisMechanicalProfile | None = None,
        target_mech: KroAxisMechanicalProfile | None = None,
        relation: KroRelationSpec,
        tuning: KroTuningProfile | None = None,
    ) -> KroBuildResult:
        relation.clamp()
        # Interpretacja pluginu: FOLLOW to śledzenie 1:1
        base_multiplier = 1.0
        
        tuning = tuning or KroTuningProfile()
        source_mech = source_mech or KroAxisMechanicalProfile(axis_id=source_line.axis_id)
        target_mech = target_mech or KroAxisMechanicalProfile(axis_id=target_line.axis_id)

        # Używamy zaawansowanego transformatora geometrii
        transformer = KroGeometryTransformer(
            source_line=source_line,
            target_line=target_line,
            source_mech=source_mech,
            target_mech=target_mech,
            tuning=tuning,
            plugin_base_multiplier=base_multiplier
        )
        
        new_points = transformer.transform()

        return KroBuildResult(
            target_axis_id=target_line.axis_id,
            plugin_type=self.plugin_type,
            new_points=new_points,
            status=f"KRO FOLLOW: {source_line.axis_id} → {target_line.axis_id} (geometry transformer)",
        )


class KroCompPlugin(KroPlugin):
    plugin_type = KroPluginType.COMP

    def build_target_line(
        self,
        *,
        source_line: KroAxisLine,
        target_line: KroAxisLine,
        source_mech: KroAxisMechanicalProfile | None = None,
        target_mech: KroAxisMechanicalProfile | None = None,
        relation: KroRelationSpec,
        tuning: KroTuningProfile | None = None,
    ) -> KroBuildResult:
        relation.clamp()
        # Interpretacja pluginu: COMP to odwrócenie o połowę
        base_multiplier = -0.5
        
        tuning = tuning or KroTuningProfile()
        source_mech = source_mech or KroAxisMechanicalProfile(axis_id=source_line.axis_id)
        target_mech = target_mech or KroAxisMechanicalProfile(axis_id=target_line.axis_id)

        # Używamy zaawansowanego transformatora geometrii
        transformer = KroGeometryTransformer(
            source_line=source_line,
            target_line=target_line,
            source_mech=source_mech,
            target_mech=target_mech,
            tuning=tuning,
            plugin_base_multiplier=base_multiplier
        )
        
        new_points = transformer.transform()

        return KroBuildResult(
            target_axis_id=target_line.axis_id,
            plugin_type=self.plugin_type,
            new_points=new_points,
            status=f"KRO COMP: {source_line.axis_id} → {target_line.axis_id} (geometry transformer)",
        )


class KroSyncPlugin(KroPlugin):
    plugin_type = KroPluginType.SYNC

    def build_target_line(
        self,
        *,
        source_line: KroAxisLine,
        target_line: KroAxisLine,
        source_mech: KroAxisMechanicalProfile | None = None,
        target_mech: KroAxisMechanicalProfile | None = None,
        relation: KroRelationSpec,
        tuning: KroTuningProfile | None = None,
    ) -> KroBuildResult:
        relation.clamp()
        # Interpretacja pluginu: SYNC to śledzenie błędów
        base_multiplier = 1.0
        
        tuning = tuning or KroTuningProfile(damping=0.25)
        source_mech = source_mech or KroAxisMechanicalProfile(axis_id=source_line.axis_id)
        target_mech = target_mech or KroAxisMechanicalProfile(axis_id=target_line.axis_id)

        # Używamy zaawansowanego transformatora geometrii w trybie SYNC
        transformer = KroGeometryTransformer(
            source_line=source_line,
            target_line=target_line,
            source_mech=source_mech,
            target_mech=target_mech,
            tuning=tuning,
            plugin_base_multiplier=base_multiplier,
            is_sync=True
        )
        
        new_points = transformer.transform()

        return KroBuildResult(
            target_axis_id=target_line.axis_id,
            plugin_type=self.plugin_type,
            new_points=new_points,
            status=f"KRO SYNC: {source_line.axis_id} → {target_line.axis_id} (geometry transformer)",
        )


class KroPluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[KroPluginType, KroPlugin] = {
            KroPluginType.KONTRA: KroKontraPlugin(),
            KroPluginType.FOLLOW: KroFollowPlugin(),
            KroPluginType.COMP: KroCompPlugin(),
            KroPluginType.SYNC: KroSyncPlugin(),
        }

    def get(self, plugin_type: KroPluginType | str) -> KroPlugin:
        try:
            normalized = plugin_type if isinstance(plugin_type, KroPluginType) else KroPluginType(str(plugin_type).strip().upper())
        except Exception:
            normalized = KroPluginType.KONTRA
        return self._plugins[normalized]

    def names(self) -> list[str]:
        return [item.value for item in self._plugins.keys()]
