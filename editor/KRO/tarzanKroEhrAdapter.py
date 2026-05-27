from __future__ import annotations

import copy
from mechanics.tarzanMechanikaOsi import TarzanMechanics

from editor.KRO.tarzanKroTypes import KroAxisLine, KroPluginType, KroRelationSpec, KroTuningProfile, KroAxisMechanicalProfile
from editor.KRO.tarzanKroPlugins import KroPluginRegistry
from editor.KRO.tarzanKroSession import KroSession
from editor.KRO.tarzanKroConnectorUi import KroConnectorUi


class TarzanKroEhrAdapter:
    """
    Jedyny most KRO ↔ EHR.

    Zasada:
    - KRO nie zna protokołu.
    - KRO nie zna STEP/DIR.
    - KRO nie zna SAVE/LOAD TAKE.
    - KRO tylko podstawia nową roboczą linię TARGET jako model.nodes.
    """

    def __init__(self, ehr_window) -> None:
        self.window = ehr_window
        self.session = KroSession()
        self.plugins = KroPluginRegistry()
        self.ui = KroConnectorUi(self)

    # ---------------------------------------------------------------------
    # Indeksy / modele
    # ---------------------------------------------------------------------

    def axis_index_by_id(self, axis_id: str) -> int | None:
        for idx, model in enumerate(self.window.axis_models):
            if model.axis_def.axis_id == axis_id:
                return idx
        return None

    def axis_model_by_id(self, axis_id: str):
        idx = self.axis_index_by_id(axis_id)
        if idx is None:
            return None
        return self.window.axis_models[idx]

    def axis_id_by_index(self, axis_index: int) -> str:
        return self.window.axis_models[axis_index].axis_def.axis_id

    # ---------------------------------------------------------------------
    # Konwersja EHR ↔ KRO
    # ---------------------------------------------------------------------

    def model_to_line(self, model) -> KroAxisLine:
        points = [(int(node.time_ms), float(node.y)) for node in model.nodes]
        return KroAxisLine(
            axis_id=model.axis_def.axis_id,
            points=points,
            y_limit=float(model.config.y_limit),
        )

    def points_to_nodes(self, model, points: list[tuple[int, float]]):
        from editor.EHR.tarzanEhrMultiAxisModel import AxisNode

        nodes = []
        for time_ms, y in points:
            nodes.append(AxisNode(model.snap_time(int(time_ms)), model.clamp_y(float(y))))

        model.nodes = nodes
        model.sort_and_fix_nodes()
        model._invalidate_cache()

    # ---------------------------------------------------------------------
    # Tworzenie relacji
    # ---------------------------------------------------------------------

    def create_relation_by_indices(self, source_axis_index: int, target_axis_index: int) -> None:
        source_model = self.window.axis_models[source_axis_index]
        target_model = self.window.axis_models[target_axis_index]

        if getattr(source_model, "is_release_axis", False) or getattr(target_model, "is_release_axis", False):
            self.set_status("KRO: DRON/release axis nie bierze udziału w relacji.")
            return

        source_id = source_model.axis_def.axis_id
        target_id = target_model.axis_def.axis_id

        if self.session.would_create_cycle(source_id, target_id):
            self.set_status("KRO: cykl relacji zablokowany.")
            return

        relation = KroRelationSpec(
            relation_id=f"kro_{source_id}_{target_id}",
            source_axis_id=source_id,
            target_axis_id=target_id,
            plugin_type=KroPluginType.KONTRA,
            enabled=True,
        )

        self.apply_relation(relation, make_backup=True)

    def apply_relation(self, relation: KroRelationSpec, *, make_backup: bool) -> None:
        relation.clamp()

        source_model = self.axis_model_by_id(relation.source_axis_id)
        target_model = self.axis_model_by_id(relation.target_axis_id)

        if source_model is None or target_model is None:
            self.set_status("KRO: brak osi SOURCE/TARGET.")
            return

        if make_backup:
            self.session.backup_target_if_needed(
                relation.target_axis_id,
                copy.deepcopy(target_model.nodes),
            )

        source_line = self.model_to_line(source_model)
        target_line = self.model_to_line(target_model)

        plugin = self.plugins.get(relation.plugin_type)
        tuning = self._get_tuning_profile(relation)
        
        # Pobieramy profile mechaniczne dla SOURCE i TARGET
        source_mech = self._get_mechanical_profile(relation.source_axis_id)
        target_mech = self._get_mechanical_profile(relation.target_axis_id)
        
        result = plugin.build_target_line(
            source_line=source_line,
            target_line=target_line,
            source_mech=source_mech,
            target_mech=target_mech,
            relation=relation,
            tuning=tuning,
        )

        self.points_to_nodes(target_model, result.new_points)
        self.session.add_or_replace_relation(relation)

        target_idx = self.axis_index_by_id(relation.target_axis_id)
        if target_idx is not None:
            self.refresh_axis(target_idx, result.status)

    # ---------------------------------------------------------------------
    # Zmiana pluginu / siły
    # ---------------------------------------------------------------------

    def change_relation_plugin(self, relation_id: str, plugin_type: KroPluginType) -> None:
        relation = self.find_relation(relation_id)
        if relation is None:
            return
        relation.plugin_type = plugin_type
        relation.enabled = True

        # Przy zmianie pluginu liczymy ponownie od backupu, nie od już przefiltrowanej linii,
        # żeby pluginy się nie nakładały przypadkiem na siebie.
        self.restore_target_backup(relation.target_axis_id, keep_backup=True)
        self.apply_relation(relation, make_backup=False)

    def change_relation_strength(self, relation_id: str, strength: float) -> None:
        """Kompatybilność po usunięciu operatorskiej SIŁY KRO.

        Siła relacji nie jest już częścią logiki. Plugin określa relację,
        a korekty mają iść przez KroTuningProfile / JSON strojenia.
        """
        self.set_status("KRO: SIŁA relacji jest wyłączona; użyj strojenia KRO.")

    def find_relation(self, relation_id: str) -> KroRelationSpec | None:
        for relation in self.session.relations:
            if relation.relation_id == relation_id:
                return relation
        return None

    # ---------------------------------------------------------------------
    # OFF / ACCEPT / REMOVE
    # ---------------------------------------------------------------------

    def disable_relation(self, relation_id: str, *, restore_backup: bool = True) -> None:
        """
        KRO OFF: przywraca backup i usuwa relację z sesji.
        """
        relation = self.find_relation(relation_id)
        if relation is None:
            return

        target_axis_id = relation.target_axis_id
        target_idx = self.axis_index_by_id(target_axis_id)

        # Usuwamy relację z sesji (KRO OFF = usuń/wyłącz)
        self.session.remove_relation(relation_id)

        if restore_backup:
            # restore_target_backup sam wywoła refresh_axis
            self.restore_target_backup(target_axis_id, keep_backup=False)
        elif target_idx is not None:
            self.refresh_axis(target_idx, f"KRO OFF: relacja usunięta dla {target_axis_id}")

        self.redraw()

    def remove_relation(self, relation_id: str, *, restore_backup: bool = True) -> None:
        """
        Usuwa relację i opcjonalnie przywraca backup.
        """
        relation = self.session.remove_relation(relation_id)
        if relation is None:
            return

        if restore_backup:
            self.restore_target_backup(relation.target_axis_id, keep_backup=False)
        else:
            target_idx = self.axis_index_by_id(relation.target_axis_id)
            if target_idx is not None:
                self.refresh_axis(target_idx, f"KRO: relacja usunięta dla {relation.target_axis_id}")

        self.redraw()

    def accept_relation_result(self, relation_id: str) -> None:
        """
        KRO ZASTOSUJ: zostawia aktualną linię TARGET jako zwykłą linię EHR i usuwa relację.
        """
        relation = self.session.remove_relation(relation_id)
        if relation is None:
            return

        self.session.clear_backup(relation.target_axis_id)

        target_idx = self.axis_index_by_id(relation.target_axis_id)
        if target_idx is not None:
            # Pełny refresh, aby EHR/Snajper wiedzieli o nowej stałej linii (matrix, metryki)
            self.refresh_axis(target_idx, f"KRO ZASTOSOWANE: linia {relation.target_axis_id} zostaje w EHR")

        self.redraw()

    def restore_target_backup(self, target_axis_id: str, *, keep_backup: bool) -> None:
        target_model = self.axis_model_by_id(target_axis_id)
        if target_model is None:
            return

        if keep_backup:
            backup = self.session.target_backups.get(target_axis_id)
            if backup is None:
                return
            restored_nodes = copy.deepcopy(backup.nodes_snapshot)
        else:
            restored_nodes = self.session.pop_backup(target_axis_id)
            if restored_nodes is None:
                return

        target_model.nodes = restored_nodes
        target_model.sort_and_fix_nodes()
        target_model._invalidate_cache()

        target_idx = self.axis_index_by_id(target_axis_id)
        if target_idx is not None:
            self.refresh_axis(target_idx, f"KRO: przywrócono bazę osi {target_axis_id}")

    # ---------------------------------------------------------------------
    # UI events
    # ---------------------------------------------------------------------

    def draw(self, canvas) -> None:
        self.ui.draw(canvas)

    def handle_press(self, x: int, y: int, x_root: int, y_root: int) -> bool:
        return self.ui.handle_press(x, y, x_root, y_root)

    def handle_drag(self, x: int, y: int) -> bool:
        return self.ui.handle_drag(x, y)

    def handle_release(self, x: int, y: int) -> bool:
        return self.ui.handle_release(x, y)

    def handle_right_click(self, x: int, y: int) -> bool:
        return self.ui.handle_right_click(x, y)

    # ---------------------------------------------------------------------
    # Refresh / status
    # ---------------------------------------------------------------------

    def refresh_axis(self, axis_index: int, status: str | None = None) -> None:
        """
        Pełne odświeżenie osi TARGET w EHR używając Snajpera (linia, matrix, metryki).
        """
        try:
            # Używamy dedykowanej metody Snajpera z EHR UI, która odświeża wszystko:
            # - curve: rysowanie krzywej
            # - metrics: metryki w panelu D
            # - step: matrix i podgląd bitów w panelu lewym
            self.window._snajper_refresh_ehr_axis(
                axis_index,
                curve=True,
                metrics=True,
                step=True,
                status=status or "KRO: odświeżono linię TARGET",
                change_active=True,
                skip_kro=True
            )
        except Exception:
            # Fallback jeśli EHR UI nie ma tej metody (np. w testach)
            try:
                self.window.mark_axis_dirty(axis_index, status=status)
            except Exception:
                self.redraw()
                if status:
                    self.set_status(status)

    def on_axis_changed(self, axis_index: int) -> None:
        """
        Wywoływane przez EHR, gdy dane osi ulegną zmianie.
        Jeśli ta oś jest źródłem (SOURCE) dla innych relacji KRO, aktualizujemy TARGETY.
        """
        if not self.window.kro_enabled_var.get():
            return

        source_id = self.axis_id_by_index(axis_index)
        # Pobierz wszystkie relacje, w których ta oś jest źródłem
        relations = self.session.relations_from_source(source_id)
        for relation in relations:
            if relation.enabled:
                # Aktualizuj target (bez robienia nowego backupu, bo już go mamy)
                self.apply_relation(relation, make_backup=False)

    def redraw(self) -> None:
        try:
            self.window._request_main_canvas_redraw()
        except Exception:
            pass

    def set_status(self, text: str) -> None:
        try:
            self.window._set_status(text)
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # Tuning / Mechanics
    # ---------------------------------------------------------------------

    def _load_tuning_config(self) -> dict:
        import json
        from pathlib import Path
        # Używamy ścieżki względnej względem roota projektu (X:\tarzan)
        path = Path("data/kro/kro_axis_tuning.json")
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _get_mechanical_profile(self, axis_id: str) -> KroAxisMechanicalProfile:
        """Pobiera pełny profil mechaniczny osi z TarzanMechanics."""
        p = KroAxisMechanicalProfile(axis_id=axis_id)
        try:
            if axis_id == "cam_h":
                p.pulses_per_cycle = TarzanMechanics.cameraHorizontalPulsesPerCycle()
                p.cruise_max_pulses_per_second = TarzanMechanics.cameraHorizontalCruiseMaxPulsesPerSecond()
                p.start_settle_pulses = TarzanMechanics.cameraHorizontalStartSettlePulses()
                p.start_settle_time = TarzanMechanics.CAMERA_HORIZONTAL_START_SETTLE_TIME_SEC
                p.start_ramp_pulses = TarzanMechanics.cameraHorizontalStartRampPulses()
                p.start_ramp_time = TarzanMechanics.CAMERA_HORIZONTAL_START_RAMP_TIME_SEC
                p.backlash_compensation_pulses = TarzanMechanics.CAMERA_HORIZONTAL_BACKLASH_COMPENSATION_PULSES
            elif axis_id == "cam_v":
                p.pulses_per_cycle = TarzanMechanics.cameraVerticalPulsesPerCycle()
                p.cruise_max_pulses_per_second = TarzanMechanics.cameraVerticalCruiseMaxPulsesPerSecond()
                p.start_settle_pulses = TarzanMechanics.cameraVerticalStartSettlePulses()
                p.start_settle_time = TarzanMechanics.CAMERA_VERTICAL_START_SETTLE_TIME_SEC
                p.start_ramp_pulses = TarzanMechanics.cameraVerticalStartRampPulses()
                p.start_ramp_time = TarzanMechanics.CAMERA_VERTICAL_START_RAMP_TIME_SEC
                p.backlash_compensation_pulses = TarzanMechanics.CAMERA_VERTICAL_BACKLASH_COMPENSATION_PULSES
            elif axis_id in ["cam_t", "arm_t"]:
                p.pulses_per_cycle = TarzanMechanics.cameraTiltPulsesPerCycle()
                p.cruise_max_pulses_per_second = TarzanMechanics.cameraTiltCruiseMaxPulsesPerSecond()
                p.start_settle_pulses = TarzanMechanics.cameraTiltStartSettlePulses()
                p.start_settle_time = TarzanMechanics.CAMERA_TILT_START_SETTLE_TIME_SEC
                p.start_ramp_pulses = TarzanMechanics.cameraTiltStartRampPulses()
                p.start_ramp_time = TarzanMechanics.CAMERA_TILT_START_RAMP_TIME_SEC
                p.backlash_compensation_pulses = TarzanMechanics.CAMERA_TILT_BACKLASH_COMPENSATION_PULSES
            elif axis_id == "cam_f":
                p.pulses_per_cycle = TarzanMechanics.cameraFocusPulsesPerCycle()
                p.cruise_max_pulses_per_second = TarzanMechanics.cameraFocusCruiseMaxPulsesPerSecond()
                p.start_settle_pulses = TarzanMechanics.cameraFocusStartSettlePulses()
                p.start_settle_time = TarzanMechanics.CAMERA_FOCUS_START_SETTLE_TIME_SEC
                p.start_ramp_pulses = TarzanMechanics.cameraFocusStartRampPulses()
                p.start_ramp_time = TarzanMechanics.CAMERA_FOCUS_START_RAMP_TIME_SEC
                p.backlash_compensation_pulses = TarzanMechanics.CAMERA_FOCUS_BACKLASH_COMPENSATION_PULSES
            elif axis_id == "arm_v":
                p.pulses_per_cycle = TarzanMechanics.armVerticalPulsesPerCycle()
                p.cruise_max_pulses_per_second = TarzanMechanics.armVerticalCruiseMaxPulsesPerSecond()
                p.start_settle_pulses = TarzanMechanics.armVerticalStartSettlePulses()
                p.start_settle_time = TarzanMechanics.ARM_VERTICAL_START_SETTLE_TIME_SEC
                p.start_ramp_pulses = TarzanMechanics.armVerticalStartRampPulses()
                p.start_ramp_time = TarzanMechanics.ARM_VERTICAL_START_RAMP_TIME_SEC
                p.backlash_compensation_pulses = TarzanMechanics.ARM_VERTICAL_BACKLASH_COMPENSATION_PULSES
            elif axis_id == "arm_h":
                p.pulses_per_cycle = TarzanMechanics.armHorizontalPulsesPerCycle()
                p.cruise_max_pulses_per_second = TarzanMechanics.armHorizontalCruiseMaxPulsesPerSecond()
                p.start_settle_pulses = TarzanMechanics.armHorizontalStartSettlePulses()
                p.start_settle_time = TarzanMechanics.ARM_HORIZONTAL_START_SETTLE_TIME_SEC
                p.start_ramp_pulses = TarzanMechanics.armHorizontalStartRampPulses()
                p.start_ramp_time = TarzanMechanics.ARM_HORIZONTAL_START_RAMP_TIME_SEC
                p.backlash_compensation_pulses = TarzanMechanics.ARM_HORIZONTAL_BACKLASH_COMPENSATION_PULSES
        except Exception:
            pass
        return p

    def _get_tuning_profile(self, relation: KroRelationSpec) -> KroTuningProfile:
        config = self._load_tuning_config()
        profile = KroTuningProfile()

        # 0. Base Mechanics Tuning (Physical ratio)
        source_mech = self._get_mechanical_profile(relation.source_axis_id)
        target_mech = self._get_mechanical_profile(relation.target_axis_id)

        # Jeśli obie osie mają zdefiniowaną mechanikę, obliczamy bazowy mnożnik fizyczny
        if source_mech.pulses_per_cycle > 0 and target_mech.pulses_per_cycle > 0:
            # Ruch o 1% source przekłada się na X% targetu w skali impulsów
            profile.axis_multiplier = source_mech.pulses_per_cycle / target_mech.pulses_per_cycle

        plugin_type_str = relation.plugin_type.value if hasattr(relation.plugin_type, "value") else str(relation.plugin_type)

        # 1. Plugin defaults
        plugin_defaults = config.get("plugin_defaults", {}).get(plugin_type_str, {})
        for key, val in plugin_defaults.items():
            if hasattr(profile, key):
                setattr(profile, key, val)
        
        # 2. Specific relation tuning (Empirical override for specific pair and plugin)
        # To jest teraz główna tabela strojenia relacyjnego.
        for rt in config.get("relation_tuning", []):
            if rt.get("source_axis_id") == relation.source_axis_id and \
               rt.get("target_axis_id") == relation.target_axis_id and \
               rt.get("plugin_type") == plugin_type_str:
                
                # Przenosimy wszystkie parametry z JSON do profilu
                for key, val in rt.items():
                    if key in ["source_axis_id", "target_axis_id", "plugin_type"]:
                        continue
                    if hasattr(profile, key):
                        setattr(profile, key, val)
                break
                
        return profile

