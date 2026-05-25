from __future__ import annotations

"""
TARZAN KRO — Kontrapunkt Ruchu Osi.

KRO jest odpinaną warstwą relacji między osiami TARZANA.
Nie rysuje UI, nie zna Tkintera, nie steruje Snajperem i nie wysyła nic na Nextion.

Kontrakt:
- source_axis wpływa na target_axis przez relację, np. KONTRA,
- KRO nie zmienia nodes operatora,
- KRO nie miesza STEP osi,
- KRO nie odwraca gotowego DIR na wyjściu,
- KRO przygotowuje runtime overlay przebiegu targetu,
- generator STEP/DIR targetu ma użyć overlay, a ADRR łagodzi wynik po KRO.

Pełne typy relacji:
- KONTRA: target dostaje odwrócony wpływ ruchu source,
- FOLLOW: target podąża za ruchem source,
- COMP: target kompensuje source zgodnie ze znakiem/invert,
- SYNC: target zachowuje własną bazę, ale jest prowadzony do wspólnej frazy/akcentu source,
- FREE: brak relacji.
"""

from bisect import bisect_left
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple
import copy


class KroRelationType(str, Enum):
    FREE = "FREE"
    KONTRA = "KONTRA"
    SYNC = "SYNC"
    FOLLOW = "FOLLOW"
    COMP = "COMP"


@dataclass
class KroRelation:
    relation_id: str
    source_axis_id: str
    target_axis_id: str
    relation_type: KroRelationType | str
    strength: float = 0.35
    enabled: bool = False
    lag_ms: int = 0
    softness: float = 0.50
    invert: bool = False
    name: str = ""

    def normalized_type(self) -> KroRelationType:
        """Zwraca typ relacji odporny na Enum, string i zapis z TAKE TXT."""
        if isinstance(self.relation_type, KroRelationType):
            return self.relation_type
        try:
            text = str(self.relation_type or "FREE").strip()
            if "." in text:
                text = text.rsplit(".", 1)[-1]
            return KroRelationType(text.upper())
        except Exception:
            return KroRelationType.FREE

    def clamp(self) -> None:
        self.relation_id = str(self.relation_id or "").strip()
        self.source_axis_id = str(self.source_axis_id or "").strip()
        self.target_axis_id = str(self.target_axis_id or "").strip()
        self.strength = max(0.0, min(1.0, float(self.strength)))
        self.enabled = bool(self.enabled)
        self.lag_ms = int(round(float(self.lag_ms or 0)))
        # 0.98 zamiast 1.0, aby relacja zawsze minimalnie reagowała.
        self.softness = max(0.0, min(0.98, float(self.softness)))
        self.invert = bool(self.invert)
        self.relation_type = self.normalized_type()

    def effective_gain(self) -> float:
        """Znak i siła relacji displacementowej.

        KONTRA zawsze ma znak ujemny. FOLLOW dodatni. COMP zależy od invert.
        SYNC nie używa tego bezpośrednio do kopiowania ruchu; ma osobny algorytm
        wyrównania frazy, ale gain zostaje dodatni/ujemny dla diagnostyki i opcji invert.
        """
        self.clamp()
        rel_type = self.normalized_type()
        sign = 1.0
        if rel_type == KroRelationType.KONTRA:
            sign = -1.0
        elif rel_type == KroRelationType.COMP:
            sign = -1.0 if self.invert else 1.0
        elif rel_type == KroRelationType.SYNC:
            sign = -1.0 if self.invert else 1.0
        elif rel_type == KroRelationType.FOLLOW:
            sign = 1.0
        if self.invert and rel_type == KroRelationType.FOLLOW:
            sign *= -1.0
        return sign * self.strength

    def to_signature(self) -> Tuple[object, ...]:
        self.clamp()
        return (
            self.relation_id,
            self.source_axis_id,
            self.target_axis_id,
            self.normalized_type().value,
            round(self.strength, 6),
            bool(self.enabled),
            int(self.lag_ms),
            round(self.softness, 6),
            bool(self.invert),
            self.name,
        )


@dataclass
class KroAxisSample:
    time_ms: int
    y: float
    dir: int = 0
    step: int = 0
    rate: float = 0.0


@dataclass
class KroAxisMotion:
    axis_id: str
    samples: List[KroAxisSample]
    y_limit: float = 100.0


@dataclass
class KroHint:
    target_axis_id: str
    relation_id: str
    time_ms: int
    influence_y: float
    source_y: float
    reason: str


@dataclass
class KroAxisResult:
    axis_id: str
    base_samples: List[KroAxisSample]
    influenced_samples: List[KroAxisSample]
    hints: List[KroHint] = field(default_factory=list)
    relation_ids: List[str] = field(default_factory=list)
    active: bool = False


@dataclass
class KroRelationStats:
    relation_id: str
    relation_type: str
    source_axis_id: str
    target_axis_id: str
    gain: float
    max_abs_influence: float
    avg_abs_influence: float
    active_samples: int


@dataclass
class KroPacketResult:
    axes: Dict[str, KroAxisResult]
    relations: List[KroRelation]
    active_relation_ids: List[str]
    status: str
    stats: List[KroRelationStats] = field(default_factory=list)


def _clamp(value: float, limit: float) -> float:
    limit = max(1.0, float(limit or 100.0))
    return max(-limit, min(limit, float(value)))


def _ordered(samples: Sequence[KroAxisSample]) -> List[KroAxisSample]:
    return sorted(
        (KroAxisSample(int(s.time_ms), float(s.y), int(s.dir), int(s.step), float(s.rate)) for s in samples),
        key=lambda s: s.time_ms,
    )


def _sample_y_at(samples: Sequence[KroAxisSample], time_ms: int) -> float:
    if not samples:
        return 0.0
    ordered = samples if all(samples[i].time_ms <= samples[i + 1].time_ms for i in range(len(samples) - 1)) else _ordered(samples)
    t = int(time_ms)
    if t <= ordered[0].time_ms:
        return float(ordered[0].y)
    if t >= ordered[-1].time_ms:
        return float(ordered[-1].y)
    times = [s.time_ms for s in ordered]
    idx = bisect_left(times, t)
    if idx <= 0:
        return float(ordered[0].y)
    left = ordered[idx - 1]
    right = ordered[idx]
    span = max(1, int(right.time_ms - left.time_ms))
    rel = (t - left.time_ms) / float(span)
    return float(left.y) + (float(right.y) - float(left.y)) * max(0.0, min(1.0, rel))


def _motion_signature(motion: KroAxisMotion) -> Tuple[object, ...]:
    ordered = _ordered(motion.samples)
    if not ordered:
        return (str(motion.axis_id), round(float(motion.y_limit or 0.0), 6), 0, ())

    # Pełny podpis próbek. KRO cache nie może opierać się tylko o końce
    # i częściowy checksum, bo zmiana punktu w środku frazy source/target
    # musi zawsze wymusić przeliczenie relacji. 800 próbek na oś jest tu
    # bezpieczne kosztowo, a daje deterministyczną zgodność z ruchem.
    samples_sig = tuple(
        (
            int(sample.time_ms),
            round(float(sample.y), 6),
            int(sample.dir),
            int(sample.step),
            round(float(sample.rate), 6),
        )
        for sample in ordered
    )
    return (
        str(motion.axis_id),
        round(float(motion.y_limit or 0.0), 6),
        len(ordered),
        samples_sig,
    )


def _copy_result(result: KroPacketResult) -> KroPacketResult:
    return copy.deepcopy(result)


class TarzanKroEngine:
    """Pakietowy silnik KRO — relacje osi bez UI i bez Snajpera."""

    def __init__(self, relations: Iterable[KroRelation] | None = None) -> None:
        self.relations: List[KroRelation] = list(relations or [])
        for relation in self.relations:
            relation.clamp()
        self._cache_signature: Tuple[object, ...] | None = None
        self._cache_result: KroPacketResult | None = None

    def clear_cache(self) -> None:
        self._cache_signature = None
        self._cache_result = None

    def set_relations(self, relations: Iterable[KroRelation]) -> None:
        self.relations = list(relations or [])
        for relation in self.relations:
            relation.clamp()
        self.clear_cache()

    def enable_relation(self, relation_id: str) -> KroRelation | None:
        relation = self.find_relation(relation_id)
        if relation is not None:
            relation.enabled = True
            relation.clamp()
            self.clear_cache()
        return relation

    def disable_relation(self, relation_id: str) -> KroRelation | None:
        relation = self.find_relation(relation_id)
        if relation is not None:
            relation.enabled = False
            relation.clamp()
            self.clear_cache()
        return relation

    def find_relation(self, relation_id: str) -> KroRelation | None:
        rid = str(relation_id or "").strip()
        for relation in self.relations:
            if relation.relation_id == rid:
                return relation
        return None

    def active_relations_for_target(self, axis_id: str) -> List[KroRelation]:
        aid = str(axis_id or "").strip()
        return [r for r in self.relations if r.enabled and r.target_axis_id == aid]

    def active_relations_for_source(self, axis_id: str) -> List[KroRelation]:
        aid = str(axis_id or "").strip()
        return [r for r in self.relations if r.enabled and r.source_axis_id == aid]

    def affected_axis_ids(self, axis_id: str) -> List[str]:
        aid = str(axis_id or "").strip()
        affected = {aid}
        for relation in self.relations:
            if not relation.enabled:
                continue
            if relation.source_axis_id == aid or relation.target_axis_id == aid:
                affected.add(relation.source_axis_id)
                affected.add(relation.target_axis_id)
        return [axis for axis in affected if axis]

    def _signature(self, motions: Mapping[str, KroAxisMotion], relations: Sequence[KroRelation]) -> Tuple[object, ...]:
        return (
            tuple(sorted((axis_id, _motion_signature(motion)) for axis_id, motion in motions.items())),
            tuple(r.to_signature() for r in relations),
        )

    def apply(self, motions: Mapping[str, KroAxisMotion], relations: Iterable[KroRelation] | None = None) -> KroPacketResult:
        relation_list = list(relations if relations is not None else self.relations)
        for relation in relation_list:
            relation.clamp()

        signature = self._signature(motions, relation_list)
        if signature == self._cache_signature and self._cache_result is not None:
            return _copy_result(self._cache_result)

        results: Dict[str, KroAxisResult] = {}
        for axis_id, motion in motions.items():
            base = _ordered(motion.samples)
            results[axis_id] = KroAxisResult(axis_id=axis_id, base_samples=base, influenced_samples=list(base))

        active_ids: List[str] = []
        stats: List[KroRelationStats] = []
        for relation in relation_list:
            if not relation.enabled or relation.normalized_type() == KroRelationType.FREE:
                continue
            source = motions.get(relation.source_axis_id)
            target = results.get(relation.target_axis_id)
            target_motion = motions.get(relation.target_axis_id)
            if source is None or target is None or target_motion is None:
                continue
            active_ids.append(relation.relation_id)
            stats.append(self._apply_relation(relation, source, target, float(target_motion.y_limit or 100.0)))

        status = "KRO: OFF"
        if active_ids:
            details = []
            for stat in stats:
                details.append(
                    f"{stat.relation_type} {stat.source_axis_id}→{stat.target_axis_id} "
                    f"{stat.gain:+.2f} max={stat.max_abs_influence:.1f}"
                )
            status = "KRO: ON " + "; ".join(details)

        packet = KroPacketResult(axes=results, relations=relation_list, active_relation_ids=active_ids, status=status, stats=stats)
        self._cache_signature = signature
        self._cache_result = _copy_result(packet)
        return packet

    def _relation_raw_influence(
        self,
        relation: KroRelation,
        *,
        source_samples: Sequence[KroAxisSample],
        source_y: float,
        source_reference_y: float,
        base_y: float,
        target_reference_y: float,
        source_limit: float,
        target_limit: float,
    ) -> float:
        rel_type = relation.normalized_type()
        gain = relation.effective_gain()
        source_delta = float(source_y) - float(source_reference_y)

        if rel_type == KroRelationType.SYNC:
            # SYNC nie kopiuje source 1:1. Czyta frazę source jako znormalizowany
            # akcent i delikatnie prowadzi target w stronę podobnej frazy,
            # zachowując jego bazową krzywą operatora.
            source_norm = source_delta / max(1.0, abs(float(source_limit or 100.0)))
            target_delta = float(base_y) - float(target_reference_y)
            target_norm = target_delta / max(1.0, abs(float(target_limit or 100.0)))
            sync_error = source_norm - target_norm
            sign = -1.0 if relation.invert else 1.0
            return sync_error * float(target_limit) * abs(float(relation.strength)) * sign

        # KONTRA / FOLLOW / COMP działają jako relacja displacementowa.
        return source_delta * gain

    def _apply_relation(self, relation: KroRelation, source: KroAxisMotion, target: KroAxisResult, target_limit: float) -> KroRelationStats:
        source_samples = _ordered(source.samples)
        if not source_samples or not target.influenced_samples:
            return KroRelationStats(relation.relation_id, relation.normalized_type().value, relation.source_axis_id, relation.target_axis_id, 0.0, 0.0, 0.0, 0)

        source_reference_y = float(source_samples[0].y)
        target_reference_y = float(target.influenced_samples[0].y)
        source_limit = float(source.y_limit or 100.0)
        gain = relation.effective_gain()
        softness = max(0.0, min(0.98, float(relation.softness)))
        previous_influence = 0.0
        influenced: List[KroAxisSample] = []
        hints: List[KroHint] = []
        abs_sum = 0.0
        max_abs = 0.0
        active_samples = 0

        for base in target.influenced_samples:
            source_time = int(base.time_ms) - int(relation.lag_ms)
            source_y = _sample_y_at(source_samples, source_time)
            raw_influence = self._relation_raw_influence(
                relation,
                source_samples=source_samples,
                source_y=source_y,
                source_reference_y=source_reference_y,
                base_y=float(base.y),
                target_reference_y=target_reference_y,
                source_limit=source_limit,
                target_limit=float(target_limit),
            )
            influence = previous_influence * softness + raw_influence * (1.0 - softness)
            previous_influence = influence
            new_y = _clamp(float(base.y) + influence, target_limit)
            influenced.append(KroAxisSample(time_ms=int(base.time_ms), y=new_y, dir=int(base.dir), step=int(base.step), rate=float(base.rate)))
            abs_inf = abs(float(influence))
            abs_sum += abs_inf
            max_abs = max(max_abs, abs_inf)
            if abs_inf > 1e-6:
                active_samples += 1
                hints.append(KroHint(
                    target_axis_id=relation.target_axis_id,
                    relation_id=relation.relation_id,
                    time_ms=int(base.time_ms),
                    influence_y=float(influence),
                    source_y=float(source_y),
                    reason=str(relation.normalized_type().value),
                ))

        target.influenced_samples = influenced
        target.hints.extend(hints)
        if relation.relation_id not in target.relation_ids:
            target.relation_ids.append(relation.relation_id)
        target.active = True
        avg_abs = abs_sum / max(1, len(target.influenced_samples))
        return KroRelationStats(
            relation_id=relation.relation_id,
            relation_type=relation.normalized_type().value,
            source_axis_id=relation.source_axis_id,
            target_axis_id=relation.target_axis_id,
            gain=float(gain),
            max_abs_influence=float(max_abs),
            avg_abs_influence=float(avg_abs),
            active_samples=int(active_samples),
        )


def build_default_kro_relations() -> List[KroRelation]:
    """Domyślne relacje KRO dla TARZANA. Startowo są OFF, operator podpina je w EHR."""
    return [
        KroRelation(
            relation_id="kro_arm_h_to_cam_h_counter",
            source_axis_id="arm_h",
            target_axis_id="cam_h",
            relation_type=KroRelationType.KONTRA,
            strength=0.35,
            enabled=False,
            lag_ms=0,
            softness=0.50,
            invert=True,
            name="KONTRA: oś pozioma ramienia → oś pozioma kamery",
        ),
        KroRelation(
            relation_id="kro_arm_v_to_cam_v_comp",
            source_axis_id="arm_v",
            target_axis_id="cam_v",
            relation_type=KroRelationType.COMP,
            strength=0.25,
            enabled=False,
            lag_ms=0,
            softness=0.55,
            invert=True,
            name="COMP: oś pionowa ramienia → oś pionowa kamery",
        ),
        KroRelation(
            relation_id="kro_arm_h_to_arm_t_comp",
            source_axis_id="arm_h",
            target_axis_id="arm_t",
            relation_type=KroRelationType.COMP,
            strength=0.18,
            enabled=False,
            lag_ms=0,
            softness=0.60,
            invert=False,
            name="COMP: oś pozioma ramienia → oś pochyłu kamery",
        ),
        KroRelation(
            relation_id="kro_cam_h_to_cam_f_follow",
            source_axis_id="cam_h",
            target_axis_id="cam_f",
            relation_type=KroRelationType.FOLLOW,
            strength=0.12,
            enabled=False,
            lag_ms=0,
            softness=0.70,
            invert=False,
            name="FOLLOW: oś pozioma kamery → oś ostrości kamery",
        ),
        KroRelation(
            relation_id="kro_arm_v_to_arm_t_follow",
            source_axis_id="arm_v",
            target_axis_id="arm_t",
            relation_type=KroRelationType.FOLLOW,
            strength=0.16,
            enabled=False,
            lag_ms=0,
            softness=0.60,
            invert=False,
            name="FOLLOW: oś pionowa ramienia → oś pochyłu kamery",
        ),
        KroRelation(
            relation_id="kro_cam_v_to_arm_t_sync",
            source_axis_id="cam_v",
            target_axis_id="arm_t",
            relation_type=KroRelationType.SYNC,
            strength=0.10,
            enabled=False,
            lag_ms=0,
            softness=0.65,
            invert=False,
            name="SYNC: oś pionowa kamery → oś pochyłu kamery",
        ),
    ]
