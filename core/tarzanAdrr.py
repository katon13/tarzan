from __future__ import annotations

"""
TARZAN ADRR — Automatyczne Dostrojenie Rytmu Ruchu.

ADRR jest pakietowym filtrem HARMONII RUCHU dla STEP 0/1.
Nie zna osi, kierunku DIR, EHR, PAR ani Snajpera.

Zasada algorytmiczna v6:
- traktuje STEP matrix jak rytmiczno-melodyczną partyturę ruchu,
- najpierw „słucha” całego utworu ruchu osi i buduje mapę globalnej harmonii oraz obwiedni gęstości,
- dopiero na tle całego utworu dzieli matrix na frazy i stroi lokalne rytmy,
- buduje rytmiczne sloty i dopasowuje impulsy do slotów,
- usuwa lub oznacza śmieci między slotami, klastry i fałszywe piki,
- dostraja rytm bez zmiany krzywej, DIR, czasu TAKE ani kolejności próbek.

Modyfikowane pola w rows:
- step
- count

Pozostałe pola, np. time_ms, dir, y, rate, acc, przechodzą bez zmian.
"""

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from math import ceil, floor
from statistics import median
from typing import Any, Callable, Mapping, MutableMapping, Sequence, TypeVar

Row = MutableMapping[str, Any]
T = TypeVar("T")


@dataclass(frozen=True)
class AdrrDirt:
    """Pojedyncza interwencja diagnostyczna ADRR.

    time_ms:
        Czas oryginalnego impulsu albo miejsca, gdzie wykryto dziurę harmonii.

    corrected_time_ms:
        Czas po dostrojeniu. Jeśli filtr tylko wykrył brud, ale nie przesunął
        impulsu, wartość może być równa time_ms.

    reason:
        Etykieta diagnostyczna dla STEP preview:
        harmony, jitter, too_close, cluster, late, early, collision, rejected,
        phrase_noise, off_grid, hole.
    """

    time_ms: int
    corrected_time_ms: int
    original_index: int
    corrected_index: int
    shift_samples: int
    reason: str


@dataclass(frozen=True)
class AdrrChaos:
    """Liczbowa diagnostyka harmonii matrixa STEP przed i po ADRR.

    Wartości są tylko diagnostyką dla panelu/operatora. Nie wpływają na ruch.
    chaos_before / chaos_after:
        0.0 = czysty, harmonijny matrix
        100.0 = bardzo chaotyczny matrix

    improvement_percent:
        Dodatnia wartość oznacza poprawę harmonii po ADRR.
    """

    chaos_before: float
    chaos_after: float
    improvement_percent: float
    dirt_count: int
    moved_count: int
    removed_count: int
    added_count: int
    pulse_count_before: int
    pulse_count_after: int


@dataclass
class AdrrResult:
    """Wynik filtra ADRR: przebieg, brudy oraz Chaos Index."""

    rows: list[dict[str, Any]]
    dirt: list[AdrrDirt]
    chaos: AdrrChaos | None = None


@dataclass
class AdrrSettings:
    """Ustawienia filtra ADRR / HARMONIA RUCHU.

    strength:
        Główna siła dostrojenia rytmu ruchu.
        0.00 = wyłączone.
        0.25 = lekka korekta i diagnostyka brudów.
        0.50 = normalne dostrojenie do lokalnej harmonii.
        0.75 = mocne porządkowanie klastrów i pików.
        1.00 = najczytelniejsza harmonia w granicach max_shift_samples.

    sample_ms:
        Czas próbki protokołu. W TARZANIE standardowo 10 ms.

    local_window:
        Zachowane dla kompatybilności z poprzednią wersją. W v4 oznacza
        czułość ucha frazy, ale harmonia jest liczona raz na frazę, nie dla
        każdego impulsu.

    max_shift_samples:
        Maksymalne przesunięcie impulsu w próbkach. To hamulec przed zmianą
        tempa/melodii ruchu.

    min_interval_samples:
        Minimalna odległość między impulsami. Przy 10 ms i limicie 50 Hz wartość
        bazowa to 2, czyli rytm 101010 bez 11.

    dirt_threshold:
        Czułość wykrywania fałszu względem lokalnej harmonii. Niżej = więcej
        brudów, wyżej = tylko największe odchyłki.

    preserve_pulse_count:
        True = zachowuj liczbę impulsów, o ile da się je rozstawić bez kolizji.

    hard_cleanup:
        True = przy wysokiej sile może odrzucić ewidentny pik, którego nie da się
        umieścić harmonijnie bez kolizji.
    """

    strength: float = 0.0
    sample_ms: int = 10
    local_window: int = 13
    max_shift_samples: int = 8
    min_interval_samples: int = 2
    dirt_threshold: float = 0.16
    preserve_pulse_count: bool = True
    hard_cleanup: bool = False

    def clamp(self) -> None:
        self.strength = max(0.0, min(1.0, float(self.strength)))
        self.sample_ms = max(1, int(round(float(self.sample_ms))))
        self.local_window = max(5, min(61, int(round(float(self.local_window)))))
        if self.local_window % 2 == 0:
            self.local_window += 1
        self.max_shift_samples = max(0, min(50, int(round(float(self.max_shift_samples)))))
        self.min_interval_samples = max(1, min(50, int(round(float(self.min_interval_samples)))))
        self.dirt_threshold = max(0.04, min(0.80, float(self.dirt_threshold)))
        self.preserve_pulse_count = bool(self.preserve_pulse_count)
        self.hard_cleanup = bool(self.hard_cleanup)


@dataclass(frozen=True)
class _Phrase:
    start_pulse: int
    end_pulse: int  # inclusive


@dataclass(frozen=True)
class _HarmonyModel:
    interval: float
    phase: float
    score: float
    density: float
    positions: tuple[int, ...]


@dataclass(frozen=True)
class _EnvelopeBand:
    start: int
    end: int
    pulse_count: int
    density: float
    interval_hint: float


@dataclass(frozen=True)
class _SongMap:
    """Globalny obraz utworu ruchu dla jednej osi.

    ADRR nie stroi lokalnej frazy w próżni. Najpierw słucha całej osi,
    rozpoznaje globalny puls, typowe przerwy i charakter zagęszczeń, a dopiero
    potem dostraja lokalne fragmenty.
    """

    base_interval: float
    phrase_gap: int
    confidence: float
    global_model: _HarmonyModel | None
    pulse_count: int
    span: int
    envelope: tuple[_EnvelopeBand, ...]


@dataclass(frozen=True)
class _GridSlot:
    index: int
    order: int


@dataclass(frozen=True)
class _PulseCandidate:
    old_index: int
    slot_index: int
    error: float
    reason: str


DEFAULT_ADRR_SETTINGS = AdrrSettings()


def _copy_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _step_indices(rows: Sequence[Mapping[str, Any]]) -> list[int]:
    """Szybkie wyciąganie indeksów impulsów."""
    return [i for i, r in enumerate(rows) if r.get("step") == 1]


def _clamp_percent(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _chaos_score_for_positions(step_positions: Sequence[int], settings: AdrrSettings) -> float:
    """Szacuje Chaos Index dla samego matrixa STEP.

    To jest odczyt diagnostyczny, nie element decydujący o korekcie ruchu.
    Wynik 0..100 opisuje, jak bardzo rytm wygląda jak szum zamiast harmonii.

    Składniki:
    - jitter odstępów,
    - klastry / za bliskie impulsy,
    - dziury względem lokalnego rytmu,
    - błąd fazy względem szybkiego modelu harmonii,
    - kolizje wielu impulsów w tym samym slocie rytmu.
    """
    if len(step_positions) < 3:
        return 0.0

    intervals = [float(v) for v in _intervals(step_positions) if v > 0]
    if not intervals:
        return 0.0

    clean_intervals = [v for v in intervals if v >= settings.min_interval_samples]
    base = _robust_median(clean_intervals or intervals, fallback=max(settings.min_interval_samples, 4))
    base = max(float(settings.min_interval_samples), float(base))

    normalized_errors = [abs(v - base) / max(1.0, base) for v in intervals]
    jitter = _robust_median(normalized_errors, fallback=0.0)

    cluster_limit = max(float(settings.min_interval_samples), base * 0.55)
    cluster_ratio = sum(1 for v in intervals if v < cluster_limit) / max(1, len(intervals))

    hole_limit = base * (1.0 + max(settings.dirt_threshold, 0.28))
    hole_ratio = sum(1 for v in intervals if v > hole_limit) / max(1, len(intervals))

    phase_ratio = 0.0
    collision_ratio = 0.0
    sample_positions = _subsample_positions(step_positions, limit=220)
    model = _infer_harmony_fast(sample_positions, settings, guide_intervals=[base])
    if model is not None and model.interval > 0:
        phase_errors = _phase_error_values(sample_positions, model.interval, model.phase)
        phase_ratio = _robust_median(
            [err / max(1.0, model.interval) for err in phase_errors],
            fallback=0.0,
        )

        slot_counts: dict[int, int] = {}
        for pos in sample_positions:
            k = round((float(pos) - model.phase) / model.interval)
            slot_counts[k] = slot_counts.get(k, 0) + 1
        collisions = sum(count - 1 for count in slot_counts.values() if count > 1)
        collision_ratio = collisions / max(1, len(sample_positions))

    raw_score = (
        jitter * 38.0
        + cluster_ratio * 32.0
        + hole_ratio * 26.0
        + phase_ratio * 34.0
        + collision_ratio * 22.0
    )
    return round(_clamp_percent(raw_score), 2)


def _make_chaos_metrics(
    source_rows: Sequence[Mapping[str, Any]],
    result_rows: Sequence[Mapping[str, Any]],
    dirt: Sequence[AdrrDirt],
    settings: AdrrSettings,
) -> AdrrChaos:
    """Buduje diagnostykę Chaos Index dla panelu ADRR.

    Funkcja nie zmienia danych. Porównuje STEP przed i po filtrze.
    """
    before = _step_indices(source_rows)
    after = _step_indices(result_rows)
    before_set = set(before)
    after_set = set(after)

    chaos_before = _chaos_score_for_positions(before, settings)
    chaos_after = _chaos_score_for_positions(after, settings)
    if chaos_before <= 0.001:
        improvement = 0.0 if chaos_after <= 0.001 else -100.0
    else:
        improvement = (chaos_before - chaos_after) / chaos_before * 100.0

    moved_count = sum(1 for item in dirt if getattr(item, "shift_samples", 0) != 0)
    removed_count = len(before_set - after_set)
    added_count = len(after_set - before_set)

    return AdrrChaos(
        chaos_before=round(chaos_before, 2),
        chaos_after=round(chaos_after, 2),
        improvement_percent=round(float(improvement), 2),
        dirt_count=len(dirt),
        moved_count=moved_count,
        removed_count=removed_count,
        added_count=added_count,
        pulse_count_before=len(before),
        pulse_count_after=len(after),
    )


def _recount_steps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Przelicza pole count na podstawie pola step."""
    count = 0
    for row in rows:
        step = 1 if row.get("step") == 1 else 0
        if step:
            count += 1
        row["step"] = step
        row["count"] = count
    return rows


def _intervals(step_positions: Sequence[int]) -> list[int]:
    return [step_positions[i + 1] - step_positions[i] for i in range(len(step_positions) - 1)]


def _trimmed(values: Sequence[float], trim_ratio: float = 0.18) -> list[float]:
    if not values:
        return []
    ordered = sorted(float(v) for v in values)
    cut = int(len(ordered) * trim_ratio)
    if cut <= 0 or len(ordered) <= 2 * cut:
        return ordered
    return ordered[cut:-cut]


def _robust_median(values: Sequence[float], fallback: float) -> float:
    trimmed = _trimmed(values)
    if not trimmed:
        return float(fallback)
    return float(median(trimmed))


def _row_time_ms(rows: Sequence[Mapping[str, Any]], index: int, settings: AdrrSettings) -> int:
    index = max(0, min(len(rows) - 1, index)) if rows else 0
    try:
        return int(rows[index].get("time_ms", index * settings.sample_ms))
    except Exception:
        return int(index * settings.sample_ms)


def _floor(value: float) -> int:
    integer = int(value)
    return integer if value >= integer else integer - 1


def _ceil(value: float) -> int:
    integer = int(value)
    return integer if value == integer or value < integer else integer + 1


def _split_phrases(step_positions: Sequence[int], settings: AdrrSettings, song: _SongMap | None = None) -> list[_Phrase]:
    """Dzieli matrix na frazy ruchu.

    Duże przerwy są traktowane jako pauzy/oddechy ruchu. Dzięki temu ADRR nie
    przeciąga rytmu przez ciszę, tylko słucha osobnych fraz.
    """
    if not step_positions:
        return []
    if len(step_positions) < 2:
        return [_Phrase(0, len(step_positions) - 1)]

    intervals = _intervals(step_positions)
    clean = [iv for iv in intervals if iv >= settings.min_interval_samples]
    if song is not None:
        base = max(float(settings.min_interval_samples), song.base_interval)
        phrase_gap = song.phrase_gap
    else:
        base = _robust_median(clean, fallback=max(settings.min_interval_samples, 4))
        phrase_gap = max(settings.min_interval_samples * 4, int(round(base * 3.8)))

    phrases: list[_Phrase] = []
    start = 0
    for i, gap in enumerate(intervals):
        if gap > phrase_gap:
            phrases.append(_Phrase(start, i))
            start = i + 1
    phrases.append(_Phrase(start, len(step_positions) - 1))
    return [p for p in phrases if p.end_pulse >= p.start_pulse]



def _phrase_chunks(phrase: _Phrase, max_pulses: int = 160) -> list[_Phrase]:
    """Tnie bardzo długą frazę na słyszalne odcinki robocze.

    To nie zmienia logiki ruchu. To tylko optymalizacja i lepsze słuchanie
    matrixa: ADRR liczy harmonię dla lokalnych fragmentów, a nie dla tysięcy
    impulsów naraz.
    """
    total = phrase.end_pulse - phrase.start_pulse + 1
    if total <= max_pulses:
        return [phrase]
    chunks: list[_Phrase] = []
    start = phrase.start_pulse
    while start <= phrase.end_pulse:
        end = min(phrase.end_pulse, start + max_pulses - 1)
        chunks.append(_Phrase(start, end))
        start = end + 1
    return chunks

def _candidate_intervals(positions: Sequence[int], settings: AdrrSettings, guide_intervals: Sequence[float] | None = None) -> list[float]:
    if len(positions) < 2:
        return []
    intervals = [float(v) for v in _intervals(positions) if v >= settings.min_interval_samples]
    if not intervals:
        return []

    med = _robust_median(intervals, fallback=max(settings.min_interval_samples, 2))
    span = float(positions[-1] - positions[0])
    density = span / max(1, (len(positions) - 1))

    buckets: dict[int, float] = {}
    for iv in intervals:
        rounded = max(settings.min_interval_samples, int(round(iv)))
        # Bardzo krótkie odstępy z klastra są podejrzane; zmniejszamy ich wpływ.
        weight = 0.35 if iv < med * 0.55 else 1.0
        buckets[rounded] = buckets.get(rounded, 0.0) + weight
    mode = float(max(buckets.items(), key=lambda item: (item[1], -abs(item[0] - med)))[0])

    # Warianty harmoniczne: czasem brudne piki dzielą właściwy takt na pół.
    candidates = [med, density, mode]
    if guide_intervals:
        for guide in guide_intervals:
            if guide > 0:
                candidates.extend([guide, guide / 2.0, guide * 2.0, guide * 1.5, guide / 1.5])
    for value in (med, density, mode):
        if value >= settings.min_interval_samples * 2:
            candidates.append(value / 2.0)
        candidates.append(value * 2.0)
    candidates.extend([(med * 0.70 + density * 0.30), (mode * 0.62 + med * 0.38)])

    out: list[float] = []
    for value in candidates:
        value = max(float(settings.min_interval_samples), float(value))
        if value <= 0:
            continue
        if not any(abs(value - existing) < 0.35 for existing in out):
            out.append(value)
    return out


def _phase_error_values(positions: Sequence[int], interval: float, phase: float) -> list[float]:
    if interval <= 0:
        return [1_000_000.0]
    errors: list[float] = []
    for pos in positions:
        k = round((float(pos) - phase) / interval)
        grid = phase + k * interval
        errors.append(abs(float(pos) - grid))
    return errors


def _harmony_score(positions: Sequence[int], interval: float, phase: float, settings: AdrrSettings) -> float:
    """Ocena dopasowania rytmu do modelu harmonii.

    Zoptymalizowana wersja z jedną pętlą i precyzyjnymi karami.
    """
    if interval <= 0:
        return 1_000_000.0

    errors: list[float] = []
    slot_counts: dict[int, int] = {}
    f_interval = float(interval)
    f_phase = float(phase)

    for pos in positions:
        f_pos = float(pos)
        k = round((f_pos - f_phase) / f_interval)
        grid = f_phase + k * f_interval
        errors.append(abs(f_pos - grid))
        slot_counts[k] = slot_counts.get(k, 0) + 1

    median_error = median(sorted(errors)) if errors else 0.0
    collisions = sum(count - 1 for count in slot_counts.values() if count > 1)
    collision_penalty = collisions * max(1.0, f_interval * 0.25)

    # Kara za zbyt rzadką/za gęstą siatkę względem liczby impulsów frazy.
    span = max(1.0, float(positions[-1] - positions[0]))
    expected_slots = max(1.0, span / max(float(settings.min_interval_samples), f_interval))
    density_penalty = abs(expected_slots - max(1, len(positions) - 1)) * 0.08

    return float(median_error + collision_penalty + density_penalty)


def _infer_harmony(positions: Sequence[int], settings: AdrrSettings, guide_intervals: Sequence[float] | None = None) -> _HarmonyModel | None:
    """Rozpoznaje lokalną harmonię całej frazy matrixa.

    V4 liczy model raz na frazę, a nie dla każdego impulsu. To jest szybsze i
    bardziej muzyczne: najpierw słyszymy frazę, potem stroimy jej wykonanie.
    """
    if len(positions) < 3:
        return None

    candidates = _candidate_intervals(positions, settings, guide_intervals=guide_intervals)
    if not candidates:
        return None

    best: _HarmonyModel | None = None
    span_density = float(positions[-1] - positions[0]) / max(1, len(positions) - 1)

    for interval in candidates:
        # Fazy z realnych impulsów oraz z kilku przesunięć. Nie kotwiczymy się
        # tylko na pierwszym impulsie, bo on sam może być brudem.
        seeds: list[float] = []
        edge_positions = list(positions[:3]) + list(positions[-3:])
        center_positions = list(positions[:: max(1, len(positions) // 5)])
        for seed in edge_positions + center_positions:
            for shift in (-0.5, 0.0, 0.5):
                seeds.append(float(seed) + interval * shift)

        for phase in seeds:
            score = _harmony_score(positions, interval, phase, settings)
            model = _HarmonyModel(
                interval=float(interval),
                phase=float(phase),
                score=float(score),
                density=float(span_density),
                positions=tuple(int(v) for v in positions),
            )
            key = (model.score, abs(model.interval - span_density), model.interval)
            if best is None:
                best = model
            else:
                best_key = (best.score, abs(best.interval - span_density), best.interval)
                if key < best_key:
                    best = model
    return best


def _nearest_grid_index(index: int, model: _HarmonyModel) -> int:
    k = round((float(index) - model.phase) / model.interval)
    return int(round(model.phase + k * model.interval))


def _grid_slots_for_phrase(positions: Sequence[int], model: _HarmonyModel, settings: AdrrSettings) -> list[_GridSlot]:
    if not positions or model.interval <= 0:
        return []
    start = min(positions) - settings.max_shift_samples
    end = max(positions) + settings.max_shift_samples
    k0 = _floor((float(start) - model.phase) / model.interval) - 1
    k1 = _ceil((float(end) - model.phase) / model.interval) + 1
    slots: list[_GridSlot] = []
    for k in range(k0, k1 + 1):
        idx = int(round(model.phase + k * model.interval))
        if start <= idx <= end:
            slots.append(_GridSlot(index=idx, order=k))
    # Usuwamy duplikaty wynikające z zaokrągleń przy małym interwale.
    unique: dict[int, _GridSlot] = {}
    for slot in slots:
        unique.setdefault(slot.index, slot)
    return [unique[index] for index in sorted(unique)]


def _pulse_reason(old_index: int, slot_index: int, positions: Sequence[int], model: _HarmonyModel, settings: AdrrSettings) -> str:
    target_error = abs(old_index - slot_index)
    interval = max(float(settings.min_interval_samples), model.interval)
    phase_limit = max(1.0, interval * settings.dirt_threshold)

    pos_list = list(positions)
    try:
        i = pos_list.index(old_index)
    except ValueError:
        i = -1
    prev_gap = old_index - pos_list[i - 1] if i > 0 else None
    next_gap = pos_list[i + 1] - old_index if 0 <= i < len(pos_list) - 1 else None

    hard_short = max(float(settings.min_interval_samples), interval * 0.42)
    soft_short = max(float(settings.min_interval_samples), interval * 0.62)
    long_limit = interval * (1.0 + max(settings.dirt_threshold, 0.22))

    if (prev_gap is not None and prev_gap < hard_short) or (next_gap is not None and next_gap < hard_short):
        return "cluster"
    if (prev_gap is not None and prev_gap < soft_short) or (next_gap is not None and next_gap < soft_short):
        return "too_close"
    if prev_gap is not None and next_gap is not None and prev_gap > long_limit and next_gap > long_limit:
        return "phrase_noise"
    if prev_gap is not None and prev_gap > long_limit:
        return "late"
    if next_gap is not None and next_gap > long_limit:
        return "early"
    if target_error >= phase_limit:
        return "harmony"
    if target_error >= max(1.0, phase_limit * 0.58) and settings.strength >= 0.25:
        return "jitter"
    return "clean"


def _assign_phrase_to_harmony(
    positions: Sequence[int],
    model: _HarmonyModel,
    row_count: int,
    occupied_global: set[int],
    settings: AdrrSettings,
) -> tuple[list[tuple[int, int, str]], list[tuple[int, str]]]:
    """Dopasowuje impulsy frazy do slotów harmonii.

    Zwraca:
    - assigned: (old_index, harmonic_slot_index, reason)
    - rejected: (old_index, reason)
    """
    slots = _grid_slots_for_phrase(positions, model, settings)
    if not slots:
        return [(p, p, "clean") for p in positions], []

    # Kandydaci: impuls może trafić do najbliższego slotu w zasięgu ruchu.
    max_reach = max(settings.max_shift_samples, int(round(model.interval * (0.42 + settings.strength * 0.25))))
    candidates: list[_PulseCandidate] = []
    for old in positions:
        nearest = min(slots, key=lambda slot: abs(slot.index - old))
        error = abs(nearest.index - old)
        reason = _pulse_reason(old, nearest.index, positions, model, settings)
        if error <= max_reach or reason in {"cluster", "too_close", "phrase_noise"}:
            candidates.append(_PulseCandidate(old_index=old, slot_index=nearest.index, error=float(error), reason=reason))
        else:
            candidates.append(_PulseCandidate(old_index=old, slot_index=old, error=float(error), reason="off_grid"))

    # Jeden slot = jeden główny impuls. Klastry/śmieci konkurujące o ten sam slot
    # są odkładane do rejected albo zachowywane jako nieharmoniczne przy słabszym ADRR.
    candidates_sorted = sorted(
        candidates,
        key=lambda c: (
            c.error,
            0 if c.reason == "clean" else 1,
            abs(c.old_index - int(round(model.phase))),
        ),
    )
    used_slots: set[int] = set()
    assigned_by_old: dict[int, tuple[int, str]] = {}
    rejected: list[tuple[int, str]] = []

    for cand in candidates_sorted:
        slot_taken = cand.slot_index in used_slots
        global_taken = cand.slot_index in occupied_global
        if cand.reason == "off_grid" and settings.strength >= 0.55:
            rejected.append((cand.old_index, "off_grid"))
            continue
        if not slot_taken and not global_taken:
            used_slots.add(cand.slot_index)
            assigned_by_old[cand.old_index] = (cand.slot_index, cand.reason)
            continue

        # Konflikt slotu: to jest typowy śmieć między rytmem. Przy mocniejszym
        # ADRR odrzucamy, przy słabszym próbujemy zachować blisko starego miejsca.
        if settings.hard_cleanup or settings.strength >= 0.68:
            rejected.append((cand.old_index, "cluster" if cand.reason in {"clean", "jitter"} else cand.reason))
        else:
            assigned_by_old[cand.old_index] = (cand.old_index, "collision")

    assigned: list[tuple[int, int, str]] = []
    for old in positions:
        if old in assigned_by_old:
            slot, reason = assigned_by_old[old]
            assigned.append((old, slot, reason))
        elif not any(old == rej_old for rej_old, _ in rejected):
            assigned.append((old, old, "clean"))
    return assigned, rejected


def _nearest_free_index(
    desired: int,
    old_index: int,
    occupied: set[int],
    row_count: int,
    settings: AdrrSettings,
) -> int | None:
    lo = max(0, old_index - settings.max_shift_samples)
    hi = min(row_count - 1, old_index + settings.max_shift_samples)
    desired = max(lo, min(hi, desired))

    def allowed(index: int) -> bool:
        if index < lo or index > hi or index in occupied:
            return False
        # Szybka kontrola lokalna zamiast skanowania całego occupied.
        # Przy min_interval_samples=2 wystarczy sprawdzić najbliższe indeksy.
        radius = max(0, settings.min_interval_samples - 1)
        for other in range(index - radius, index + radius + 1):
            if other != index and other in occupied:
                return False
        return True

    if allowed(desired):
        return desired

    best: int | None = None
    best_distance: tuple[int, int] | None = None
    for index in range(lo, hi + 1):
        if not allowed(index):
            continue
        distance = (abs(index - desired), abs(index - old_index))
        if best_distance is None or distance < best_distance:
            best = index
            best_distance = distance
    return best


def _hole_markers_for_phrase(
    rows: Sequence[Mapping[str, Any]],
    positions: Sequence[int],
    model: _HarmonyModel,
    settings: AdrrSettings,
) -> list[AdrrDirt]:
    """Wykrywa dziury w harmonii matrixa.

    Dziury są tylko diagnostyką markerów — nie dodajemy impulsów, bo ADRR nie ma
    zmieniać prędkości ani melodii ruchu.
    """
    if settings.strength < 0.18 or len(positions) < 5:
        return []
    interval = max(float(settings.min_interval_samples), model.interval)
    gap_limit = interval * (1.0 + max(settings.dirt_threshold, 0.25))
    pulse_set = set(positions)
    dirt: list[AdrrDirt] = []
    max_markers = 12

    for left, right in zip(positions, positions[1:]):
        if right - left <= gap_limit:
            continue
        k = _floor((float(left) - model.phase) / interval) + 1
        while True:
            grid = int(round(model.phase + k * interval))
            if grid >= right:
                break
            if grid > left and all(abs(grid - p) >= settings.min_interval_samples for p in pulse_set):
                dirt.append(
                    AdrrDirt(
                        time_ms=_row_time_ms(rows, grid, settings),
                        corrected_time_ms=_row_time_ms(rows, grid, settings),
                        original_index=grid,
                        corrected_index=grid,
                        shift_samples=0,
                        reason="hole",
                    )
                )
                if len(dirt) >= max_markers:
                    return dirt
            k += 1
    return dirt



def _subsample_positions(positions: Sequence[int], limit: int = 720) -> tuple[int, ...]:
    if len(positions) <= limit:
        return tuple(int(v) for v in positions)
    step = max(1, len(positions) // limit)
    sampled = [int(v) for v in positions[::step]]
    if sampled[-1] != positions[-1]:
        sampled.append(int(positions[-1]))
    return tuple(sampled)


def _infer_envelope_bands(step_positions: Sequence[int], settings: AdrrSettings, span: int) -> tuple[_EnvelopeBand, ...]:
    """Buduje globalną obwiednię gęstości matrixa STEP.

    To jest wizualno-rytmiczna warstwa ADRR v6: filtr nie patrzy tylko na
    najbliższe impulsy, ale widzi, gdzie w całym utworze ruchu rośnie i opada
    zagęszczenie. Dzięki temu śmieć w spokojnym fragmencie jest traktowany
    ostrzej niż impuls w prawdziwym akcentowanym paśmie.
    """
    if not step_positions:
        return ()
    first = int(step_positions[0])
    last = int(step_positions[-1])
    # Około 0.5 s przy 10 ms, ale skalowane ostrożnie dla innych próbek.
    band_width = max(settings.local_window * 3, int(round(520 / max(1, settings.sample_ms))))
    band_width = max(24, min(120, band_width))
    bands: list[_EnvelopeBand] = []
    cursor = first
    pos_i = 0
    total = len(step_positions)
    global_interval = max(float(settings.min_interval_samples), float(span) / max(1, total - 1))
    while cursor <= last:
        end = min(last, cursor + band_width - 1)
        while pos_i < total and step_positions[pos_i] < cursor:
            pos_i += 1
        j = pos_i
        while j < total and step_positions[j] <= end:
            j += 1
        count = j - pos_i
        density = count / max(1, end - cursor + 1)
        interval_hint = (end - cursor + 1) / max(1, count - 1) if count >= 2 else global_interval
        bands.append(_EnvelopeBand(cursor, end, count, float(density), float(max(settings.min_interval_samples, interval_hint))))
        cursor = end + 1
    return tuple(bands)


def _envelope_at(song: _SongMap, index: int) -> _EnvelopeBand | None:
    if not song.envelope:
        return None
    # Liczba pasm jest mała, liniowe wyszukanie jest wystarczająco tanie.
    for band in song.envelope:
        if band.start <= index <= band.end:
            return band
    if index < song.envelope[0].start:
        return song.envelope[0]
    return song.envelope[-1]


def _visual_cleanup_power(settings: AdrrSettings) -> float:
    """Ile wolno czyścić obraz matrixa, bez zmiany melodii przy niskim ADRR."""
    if settings.strength <= 0.22:
        return 0.0
    return max(0.0, min(1.0, (settings.strength - 0.22) / 0.78))


def _phrase_density_kind(positions: Sequence[int], model: _HarmonyModel, song: _SongMap, settings: AdrrSettings) -> str:
    if len(positions) < 2:
        return "single"
    center = positions[len(positions) // 2]
    band = _envelope_at(song, center)
    local_span = max(1, positions[-1] - positions[0])
    local_density = len(positions) / local_span
    song_density = song.pulse_count / max(1, song.span)
    band_density = band.density if band is not None else song_density
    if local_density > max(song_density, band_density) * 1.75 and settings.strength >= 0.45:
        return "overdense"
    if local_density < max(song_density, band_density) * 0.42:
        return "sparse"
    return "balanced"


def _build_visual_slots(
    positions: Sequence[int],
    model: _HarmonyModel,
    song: _SongMap,
    settings: AdrrSettings,
) -> list[int]:
    """Buduje harmonijne sloty dla całej frazy, z uwzględnieniem obwiedni utworu.

    W v6 to jest serce HARMONII RUCHU: zamiast poprawiać pojedyncze impulsy,
    rozkładamy frazę na czytelne miejsca rytmiczne. Przy niskim ADRR slotów jest
    tyle co impulsów, więc tempo zostaje praktycznie nienaruszone. Przy wysokim
    ADRR nadmiarowe śmieci między pasmami nie dostają własnego slotu.
    """
    if not positions:
        return []
    if len(positions) == 1:
        return [positions[0]]

    first = int(positions[0])
    last = int(positions[-1])
    span = max(1, last - first)
    pulse_count = len(positions)
    interval = max(float(settings.min_interval_samples), float(model.interval))
    band = _envelope_at(song, (first + last) // 2)
    if band is not None and band.pulse_count >= 2:
        # Delikatnie mieszamy lokalny rytm z obwiednią, bo obraz matrixa ma mieć
        # falę gęstości, a nie mechaniczne sloty oderwane od całości.
        envelope_blend = min(0.38, _visual_cleanup_power(settings) * 0.38)
        interval = interval * (1.0 - envelope_blend) + band.interval_hint * envelope_blend

    grid_count = max(1, int(round(span / interval)) + 1)
    cleanup = _visual_cleanup_power(settings)
    kind = _phrase_density_kind(positions, model, song, settings)

    if settings.preserve_pulse_count and settings.strength < 0.58:
        target_count = pulse_count
    else:
        # Nie dodajemy nowego ruchu. Co najwyżej odbieramy sloty oczywistym
        # śmieciom, szczególnie w nadgęstych fragmentach.
        if kind == "overdense":
            target_count = int(round(pulse_count * (1.0 - 0.42 * cleanup) + grid_count * (0.42 * cleanup)))
        elif kind == "sparse":
            target_count = pulse_count
        else:
            target_count = int(round(pulse_count * (1.0 - 0.25 * cleanup) + grid_count * (0.25 * cleanup)))
        target_count = max(1, min(pulse_count, target_count))

    if target_count <= 1:
        return [int(round((first + last) * 0.5))]

    # Sloty są równomierne w ramach frazy, ale fazę bierzemy z modelu harmonii.
    # Następnie wybieramy te, które pokrywają całą frazę.
    raw_slots: list[int] = []
    k0 = _floor((first - model.phase) / interval) - 2
    k1 = _ceil((last - model.phase) / interval) + 2
    for k in range(k0, k1 + 1):
        idx = int(round(model.phase + k * interval))
        if first - settings.max_shift_samples <= idx <= last + settings.max_shift_samples:
            raw_slots.append(max(0, idx))
    raw_slots = sorted(set(raw_slots))
    if not raw_slots:
        raw_slots = [int(round(first + i * span / max(1, target_count - 1))) for i in range(target_count)]

    # Jeżeli siatka ma zbyt wiele slotów, wybieramy reprezentatywne. To usuwa
    # wizualny szum między pasmami, zachowując obwiednię frazy.
    if len(raw_slots) > target_count:
        selected: list[int] = []
        for i in range(target_count):
            pos = i * (len(raw_slots) - 1) / max(1, target_count - 1)
            selected.append(raw_slots[int(round(pos))])
        raw_slots = sorted(set(selected))
    if len(raw_slots) < target_count:
        # Uzupełnij brakujące sloty równomiernie, ale bez ryzyka pętli na duplikatach.
        even_slots = [int(round(first + i * span / max(1, target_count - 1))) for i in range(target_count)]
        raw_slots = sorted(set(raw_slots + even_slots))
    if len(raw_slots) > target_count:
        selected = []
        for i in range(target_count):
            pos = i * (len(raw_slots) - 1) / max(1, target_count - 1)
            selected.append(raw_slots[int(round(pos))])
        raw_slots = sorted(set(selected))
    return raw_slots[:target_count]


def _phrase_already_harmonic(positions: Sequence[int], model: _HarmonyModel, settings: AdrrSettings) -> bool:
    """Rozpoznaje frazę, która już jest harmonijna i nie wymaga dotykania.

    To chroni melodię/tempo: ADRR ma czyścić fałsz, a nie przerabiać dobry rytm.
    Zoptymalizowane dla rytmów 101010 i 10001000.
    """
    if len(positions) < 2:
        return True
    iv = _intervals(positions)
    if not iv:
        return True
    min_iv = min(iv)
    max_iv = max(iv)

    # Idealnie równy rytm zostawiamy bezwzględnie.
    if min_iv == max_iv:
        return True

    # Bardzo równe 1010, 10001000 itd. (jitter max 1) zostawiamy bez zmian.
    if max_iv - min_iv <= 1:
        if min_iv >= settings.min_interval_samples:
            return True

    # Lekko zaokrąglone rytmy też zostawiamy, jeśli faza modelu je potwierdza.
    # Przy niskim strength pozwalamy na większy 'naturalny' błąd.
    errors = _phase_error_values(positions, model.interval, model.phase)
    if not errors:
        return False

    med_err = median(sorted(errors))
    max_err = max(errors)

    # Dynamiczne progi akceptacji harmonii
    threshold_med = 0.25 + (1.0 - settings.strength) * 0.30
    threshold_max = 0.90 + (1.0 - settings.strength) * 0.60

    if med_err <= threshold_med and max_err <= threshold_max:
        return True

    return False


def _assign_to_visual_slots(
    positions: Sequence[int],
    slots: Sequence[int],
    occupied_global: set[int],
    row_count: int,
    settings: AdrrSettings,
    model: _HarmonyModel,
) -> tuple[list[tuple[int, int, str]], list[tuple[int, str]]]:
    """Przypisuje impulsy frazy do wizualno-harmonicznych slotów.

    Zoptymalizowane pod kątem wydajności przy użyciu bisect dla dużych fraz.
    """
    if not positions:
        return [], []
    if not slots:
        return [(p, p, "clean") for p in positions], []

    max_reach = max(settings.max_shift_samples, int(round(model.interval * (0.45 + settings.strength * 0.28))))
    pairs: list[tuple[float, int, int]] = []

    # Zoptymalizowane wyszukiwanie par w zasięgu max_reach
    for old in positions:
        idx_start = bisect_left(slots, old - max_reach)
        idx_end = bisect_right(slots, old + max_reach)
        for i in range(idx_start, idx_end):
            slot = slots[i]
            dist = abs(old - slot)
            pairs.append((float(dist), old, slot))

    pairs.sort(key=lambda item: item[0])

    used_old: set[int] = set()
    used_slot: set[int] = set()
    assigned: list[tuple[int, int, str]] = []
    for _dist, old, slot in pairs:
        if old in used_old or slot in used_slot or slot in occupied_global:
            continue
        reason = _pulse_reason(old, slot, positions, model, settings)
        used_old.add(old)
        used_slot.add(slot)
        assigned.append((old, slot, reason))

    rejected: list[tuple[int, str]] = []
    for old in positions:
        if old in used_old:
            continue
        # nearest_slot z bisect
        idx = bisect_left(slots, old)
        if idx == 0:
            nearest_slot = slots[0]
        elif idx == len(slots):
            nearest_slot = slots[-1]
        else:
            s1, s2 = slots[idx - 1], slots[idx]
            nearest_slot = s1 if abs(s1 - old) <= abs(s2 - old) else s2

        reason = _pulse_reason(old, nearest_slot, positions, model, settings)
        if settings.hard_cleanup or settings.strength >= 0.58:
            rejected.append((old, reason if reason != "clean" else "phrase_noise"))
        else:
            assigned.append((old, old, "collision" if reason == "clean" else reason))

    assigned.sort(key=lambda item: item[0])
    return assigned, rejected


def _infer_song_map(step_positions: Sequence[int], settings: AdrrSettings) -> _SongMap:
    """Słucha całego utworu ruchu osi i buduje globalną mapę harmonii.

    To jest nadrzędne ucho ADRR. Lokalna fraza nie wybiera rytmu wyłącznie z
    własnego krótkiego okna, tylko dostaje kontekst: globalny puls, typową
    przerwę frazy i ogólną gęstość partytury STEP.
    """
    if len(step_positions) < 3:
        fallback = float(max(settings.min_interval_samples, 4))
        return _SongMap(
            base_interval=fallback,
            phrase_gap=int(round(fallback * 4.0)),
            confidence=0.0,
            global_model=None,
            pulse_count=len(step_positions),
            span=0,
            envelope=(),
        )

    span = max(1, int(step_positions[-1] - step_positions[0]))
    intervals = [iv for iv in _intervals(step_positions) if iv >= settings.min_interval_samples]
    local_base = _robust_median(intervals, fallback=max(settings.min_interval_samples, 4))

    # Globalny model liczony na podpróbce, żeby nie obciążać UI przy 3-minutowym TAKE.
    sample_positions = _subsample_positions(step_positions, limit=220)
    global_model = _infer_harmony_fast(sample_positions, settings, guide_intervals=[local_base])
    if global_model is not None:
        base = max(float(settings.min_interval_samples), global_model.interval)
        score_norm = global_model.score / max(1.0, base)
        confidence = max(0.0, min(1.0, 1.0 - score_norm))
    else:
        base = max(float(settings.min_interval_samples), local_base)
        confidence = 0.0

    # Duża pauza rozdziela frazy. Przy niskiej pewności dajemy szerszy oddech,
    # żeby nie ciągnąć rytmu przez chaos.
    phrase_gap = max(
        settings.min_interval_samples * 5,
        int(round(base * (4.2 + (1.0 - confidence) * 1.3))),
    )
    return _SongMap(
        base_interval=base,
        phrase_gap=phrase_gap,
        confidence=confidence,
        global_model=global_model,
        pulse_count=len(step_positions),
        span=span,
        envelope=_infer_envelope_bands(step_positions, settings, span),
    )


def _guide_intervals_for_phrase(positions: Sequence[int], song: _SongMap, settings: AdrrSettings) -> list[float]:
    """Zwraca globalno-lokalne podpowiedzi rytmu dla frazy."""
    guide = [song.base_interval]
    if song.global_model is not None:
        guide.append(song.global_model.interval)
    if len(positions) >= 2:
        local_density = float(positions[-1] - positions[0]) / max(1, len(positions) - 1)
        guide.extend([local_density, (local_density + song.base_interval) * 0.5])

    # Harmoniczne związki są celowe: czasem lokalna fraza gra dwa razy gęściej
    # lub dwa razy rzadziej niż globalny puls, ale nadal należy do tego samego utworu.
    enriched: list[float] = []
    for value in guide:
        if value <= 0:
            continue
        enriched.extend([value, value / 2.0, value * 2.0])
    out: list[float] = []
    for value in enriched:
        value = max(float(settings.min_interval_samples), float(value))
        if not any(abs(value - existing) < 0.25 for existing in out):
            out.append(value)
    return out



def _infer_harmony_fast(
    positions: Sequence[int],
    settings: AdrrSettings,
    guide_intervals: Sequence[float] | None = None,
) -> _HarmonyModel | None:
    """Szybkie słuchanie harmonii frazy.

    Pełne _infer_harmony jest dokładniejsze, ale za ciężkie dla żywego EHR.
    Ten wariant bierze globalno-lokalne kandydaty pulsu i małą liczbę faz,
    dzięki czemu cała 3-minutowa oś może być analizowana w czasie roboczym.
    """
    if len(positions) < 3:
        return None
    intervals = [float(v) for v in _intervals(positions) if v >= settings.min_interval_samples]
    if not intervals:
        return None
    med = _robust_median(intervals, fallback=max(settings.min_interval_samples, 4))
    density = float(positions[-1] - positions[0]) / max(1, len(positions) - 1)
    candidates: list[float] = [med, density]
    if guide_intervals:
        candidates.extend(float(v) for v in guide_intervals if v > 0)
    # Dodaj harmoniczne, ale bez eksplozji kandydatów.
    enriched: list[float] = []
    for value in candidates:
        if value <= 0:
            continue
        enriched.extend([value, value / 2.0, value * 2.0])
    unique: list[float] = []
    for value in enriched:
        value = max(float(settings.min_interval_samples), float(value))
        if not any(abs(value - existing) < 0.35 for existing in unique):
            unique.append(value)
    # Najbardziej prawdopodobne kandydaty najpierw.
    unique = sorted(unique, key=lambda v: (abs(v - density), abs(v - med)))[:10]

    seed_step = max(1, len(positions) // 6)
    seed_positions = list(positions[::seed_step])[:6]
    if positions[-1] not in seed_positions:
        seed_positions.append(positions[-1])

    best: _HarmonyModel | None = None
    for interval in unique:
        phases: list[float] = []
        for seed in seed_positions:
            k = round(float(seed) / interval)
            base_phase = float(seed) - k * interval
            phases.extend([base_phase, base_phase - interval * 0.5, base_phase + interval * 0.5])
        # deduplikacja faz
        phase_unique: list[float] = []
        for phase in phases:
            if not any(abs(phase - old) < 0.25 for old in phase_unique):
                phase_unique.append(phase)
        for phase in phase_unique[:12]:
            score = _harmony_score(positions, interval, phase, settings)
            model = _HarmonyModel(
                interval=float(interval),
                phase=float(phase),
                score=float(score),
                density=float(density),
                positions=tuple(int(v) for v in positions),
            )
            key = (model.score, abs(model.interval - density), model.interval)
            if best is None:
                best = model
            else:
                best_key = (best.score, abs(best.interval - density), best.interval)
                if key < best_key:
                    best = model
    return best

def _stabilize_model_with_song(local: _HarmonyModel, song: _SongMap, settings: AdrrSettings) -> _HarmonyModel:
    """Delikatnie wiąże lokalny rytm z globalnym utworem ruchu.

    Zoptymalizowana i wzmocniona stabilizacja względem globalnej mapy.
    """
    if song.confidence <= 0.10:
        return local

    base = max(float(settings.min_interval_samples), song.base_interval)
    interval = local.interval

    # Harmoniczne opcje dociągania
    harmonic_options = [base / 2.0, base, base * 2.0, base * 1.5, base / 1.5, base * 3.0, base / 3.0]
    harmonic_options = [v for v in harmonic_options if v >= settings.min_interval_samples]

    nearest = min(harmonic_options, key=lambda v: abs(v - interval))

    # Jeśli lokalny rytm jest blisko globalnej harmonicznej, dociągamy go.
    if abs(nearest - interval) <= max(1.8, nearest * 0.36):
        # Blend rośnie wraz ze strength i confidence.
        blend = min(0.60, song.confidence * (0.22 + settings.strength * 0.40))
        new_interval = interval * (1.0 - blend) + nearest * blend
        return _HarmonyModel(
            interval=new_interval,
            phase=local.phase,
            score=local.score,
            density=local.density,
            positions=local.positions,
        )
    return local


def _target_slot_count(positions: Sequence[int], model: _HarmonyModel, settings: AdrrSettings) -> int:
    """Ile harmonijnych miejsc rytmicznych ma sens w tej frazie.

    Dla umiarkowanego ADRR zachowujemy liczbę impulsów. Dla mocnego ADRR
    odrzucamy ewidentne nadmiary z klastrów, więc liczba slotów może być mniejsza.
    """
    if not positions:
        return 0
    pulse_count = len(positions)
    if settings.preserve_pulse_count and settings.strength < 0.62:
        return pulse_count
    span = max(1, positions[-1] - positions[0])
    interval = max(float(settings.min_interval_samples), model.interval)
    grid_count = max(1, int(round(span / interval)) + 1)
    if settings.strength < 0.78:
        # Jeszcze nie tnij agresywnie; ogranicz tylko skrajne klastry.
        return max(1, min(pulse_count, int(round(pulse_count * 0.92 + grid_count * 0.08))))
    return max(1, min(pulse_count, grid_count))

def filter_axis_rows_with_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    settings: AdrrSettings | None = None,
) -> AdrrResult:
    """Filtruje rytm STEP jednej osi i zwraca diagnostykę ADRR.

    Algorytm v6: HARMONIA RUCHU — cały utwór + obwiednia obrazu + frazy.

    Warstwy:
    1. GLOBAL SONG LISTENING — słuchanie całej osi i budowa mapy utworu,
    2. VISUAL ENVELOPE — analiza fali/gęstości matrixa STEP,
    3. PHRASE HARMONY — lokalna siatka rytmu na tle całości,
    4. SLOT PERFORMANCE — rozmieszczenie impulsów w harmonijnych slotach,
    5. DIRT DIAGNOSTICS — markery fałszu/brudu dla STEP preview.

    Kontrakt pozostaje twardy: nie ruszamy time_ms, dir, y, rate ani kolejności
    próbek. Zmieniamy tylko step i count.
    """
    settings = settings or DEFAULT_ADRR_SETTINGS
    settings = AdrrSettings(**settings.__dict__)
    settings.clamp()

    if settings.strength <= 0.0 or settings.max_shift_samples <= 0:
        out_rows = _recount_steps(_copy_rows(rows))
        return AdrrResult(rows=out_rows, dirt=[], chaos=_make_chaos_metrics(rows, out_rows, [], settings))

    pulses = _step_indices(rows)
    if len(pulses) < 3:
        out_rows = _recount_steps(_copy_rows(rows))
        return AdrrResult(rows=out_rows, dirt=[], chaos=_make_chaos_metrics(rows, out_rows, [], settings))

    song = _infer_song_map(pulses, settings)
    phrases = _split_phrases(pulses, settings, song)
    row_count = len(rows)
    occupied: set[int] = set()
    final_positions: list[int] = []
    dirt: list[AdrrDirt] = []

    # Suwak nie jest progiem detekcji. Detekcja działa wcześnie, a siła suwaka
    # steruje tym, jak mocno dostrajamy do slotów harmonii.
    correction_power = 0.16 + 0.84 * settings.strength
    allow_reject = settings.hard_cleanup or settings.strength >= 0.58

    for source_phrase in phrases:
        # Większe kawałki niż w v5: chcemy widzieć falę/motyw, ale nie blokować UI.
        for phrase in _phrase_chunks(source_phrase, max_pulses=220):
            positions = tuple(int(v) for v in pulses[phrase.start_pulse : phrase.end_pulse + 1])
            if not positions:
                continue
            if len(positions) < 3:
                for old in positions:
                    chosen = _nearest_free_index(old, old, occupied, row_count, settings)
                    if chosen is not None:
                        occupied.add(chosen)
                        final_positions.append(chosen)
                continue

            guide = _guide_intervals_for_phrase(positions, song, settings)
            model = _infer_harmony_fast(positions, settings, guide_intervals=guide)
            if model is not None:
                model = _stabilize_model_with_song(model, song, settings)

            if model is None:
                for old in positions:
                    chosen = _nearest_free_index(old, old, occupied, row_count, settings)
                    if chosen is not None:
                        occupied.add(chosen)
                        final_positions.append(chosen)
                continue

            if _phrase_already_harmonic(positions, model, settings):
                for old in positions:
                    chosen = _nearest_free_index(old, old, occupied, row_count, settings)
                    if chosen is not None:
                        occupied.add(chosen)
                        final_positions.append(chosen)
                continue

            slots = _build_visual_slots(positions, model, song, settings)
            assigned, rejected = _assign_to_visual_slots(positions, slots, occupied, row_count, settings, model)

            for old_index, slot_index, reason in assigned:
                if reason == "clean" and settings.strength < 0.35:
                    desired = old_index
                else:
                    raw_new = old_index + (float(slot_index) - float(old_index)) * correction_power
                    shift = int(round(raw_new - old_index))
                    shift = max(-settings.max_shift_samples, min(settings.max_shift_samples, shift))
                    desired = old_index + shift

                chosen = _nearest_free_index(desired, old_index, occupied, row_count, settings)
                if chosen is None:
                    if settings.preserve_pulse_count or not allow_reject:
                        chosen = _nearest_free_index(old_index, old_index, occupied, row_count, settings)
                        if chosen is not None and reason == "clean":
                            reason = "collision"
                    if chosen is None:
                        rejected.append((old_index, "rejected" if reason == "clean" else reason))
                        continue

                occupied.add(chosen)
                final_positions.append(chosen)

                if reason != "clean" or chosen != old_index:
                    dirt.append(
                        AdrrDirt(
                            time_ms=_row_time_ms(rows, old_index, settings),
                            corrected_time_ms=_row_time_ms(rows, chosen, settings),
                            original_index=old_index,
                            corrected_index=chosen,
                            shift_samples=chosen - old_index,
                            reason=reason if reason != "clean" else "harmony",
                        )
                    )

            for old_index, reason in rejected:
                if settings.preserve_pulse_count and not allow_reject:
                    chosen = _nearest_free_index(old_index, old_index, occupied, row_count, settings)
                    if chosen is not None:
                        occupied.add(chosen)
                        final_positions.append(chosen)
                        dirt.append(
                            AdrrDirt(
                                time_ms=_row_time_ms(rows, old_index, settings),
                                corrected_time_ms=_row_time_ms(rows, chosen, settings),
                                original_index=old_index,
                                corrected_index=chosen,
                                shift_samples=chosen - old_index,
                                reason="collision",
                            )
                        )
                        continue
                dirt.append(
                    AdrrDirt(
                        time_ms=_row_time_ms(rows, old_index, settings),
                        corrected_time_ms=_row_time_ms(rows, old_index, settings),
                        original_index=old_index,
                        corrected_index=old_index,
                        shift_samples=0,
                        reason=reason,
                    )
                )

            # Dziury harmonii
            dirt.extend(_hole_markers_for_phrase(rows, positions, model, settings))

    # FINALNA REKONSTRUKCJA: jedna pętla kopiująca i przeliczająca count
    final_rows: list[dict[str, Any]] = []
    final_pos_set = set(final_positions)
    count = 0
    for i, row in enumerate(rows):
        # Kopiujemy tylko te pola, których nie zmieniamy (zabezpieczenie kontraktu)
        new_row = dict(row)
        is_step = 1 if i in final_pos_set else 0
        if is_step:
            count += 1
        new_row["step"] = is_step
        new_row["count"] = count
        final_rows.append(new_row)

    return AdrrResult(rows=final_rows, dirt=dirt, chaos=_make_chaos_metrics(rows, final_rows, dirt, settings))

def filter_axis_rows(rows: Sequence[Mapping[str, Any]], settings: AdrrSettings | None = None) -> list[dict[str, Any]]:
    """Filtruje rytm STEP jednej osi bez zwracania diagnostyki."""
    return filter_axis_rows_with_diagnostics(rows, settings).rows


def filter_axes_packet(
    packet: Mapping[T, Sequence[Mapping[str, Any]]],
    settings: AdrrSettings | Mapping[T, AdrrSettings] | Callable[[T], AdrrSettings] | None = None,
) -> dict[T, list[dict[str, Any]]]:
    """Filtruje pakiet osi bez zmiany kluczy i bez zmiany kolejności wejścia."""
    result: dict[T, list[dict[str, Any]]] = {}
    for key, axis_rows in packet.items():
        if callable(settings):
            axis_settings = settings(key)
        elif isinstance(settings, Mapping):
            axis_settings = settings.get(key, DEFAULT_ADRR_SETTINGS)  # type: ignore[arg-type]
        else:
            axis_settings = settings
        result[key] = filter_axis_rows(axis_rows, axis_settings)
    return result
