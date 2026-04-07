from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class TarzanProtocolRow:
    sample_index: int
    time_ms: int
    dir: int
    step: int
    ev: int
    enable: int
    amp: float
    count: int

    def to_dict(self) -> dict[str, int | float]:
        sample = int(self.sample_index)
        time_ms = int(self.time_ms)
        dir_value = int(self.dir)
        step_value = int(self.step)
        ev_value = int(self.ev)
        enable_value = int(self.enable)
        amp_value = float(self.amp)
        count_value = int(self.count)
        return {
            "SAMPLE": sample,
            "TIME_MS": time_ms,
            "DIR": dir_value,
            "STEP": step_value,
            "EV": ev_value,
            "ENABLE": enable_value,
            "AMP": amp_value,
            "COUNT": count_value,
            "sample": sample,
            "time_ms": time_ms,
            "dir": dir_value,
            "step": step_value,
            "ev": ev_value,
            "step_events": ev_value,
            "enable": enable_value,
            "amp": amp_value,
            "count": count_value,
        }


class TarzanStepGenerator:
    """
    Centralny generator STEP dla projektu TARZAN.

    Założenia klasy:
    - pracuje wyłącznie w globalnym kroku czasu systemu,
    - buduje pełny timeline osi od początku do końca TAKE,
    - zapisuje STEP jako stan logiczny obecności impulsu w próbce,
    - EV oznacza liczbę impulsów przypadających na próbkę,
    - COUNT rośnie o pełne EV, nie tylko o 0/1,
    - DIR i ENABLE są stanami próbek, nie osobnym preview,
    - preview ma czytać wynik tej klasy, a nie liczyć po swojemu.

    Klasa zachowuje kompatybilność z dwiema ścieżkami użycia istniejącymi
    w projekcie:
    1. generate_step_times() – używane przez starszą symulację z main.py
    2. generate_axis_protocol(...) – używane przez edytor choreografii.
    """

    def __init__(
        self,
        sample_ms: int = 10,
        time_ms: Sequence[float] | None = None,
        pulse_density: Sequence[float] | None = None,
    ) -> None:
        self.sample_ms = max(1, int(sample_ms))
        self.time_ms = list(time_ms) if time_ms is not None else []
        self.pulse_density = list(pulse_density) if pulse_density is not None else []

    # ------------------------------------------------------------------
    # Public API used by main.py
    # ------------------------------------------------------------------

    def generate_step_times(self) -> list[int]:
        """
        Starsze API projektu.

        Zwraca chwile czasowe próbek, w których został wygenerowany STEP = 1.
        Wejściem są tablice time_ms i pulse_density przekazane w __init__.
        """
        if not self.time_ms or not self.pulse_density:
            return []

        rows = self._generate_rows_from_density(
            times_ms=self._normalize_times(self.time_ms),
            density=self._normalize_density(self.pulse_density),
            direction_hint=1,
            enable=1,
            start_count=0,
        )
        return [int(row.time_ms) for row in rows if row.step == 1]

    # ------------------------------------------------------------------
    # Public API used by editor
    # ------------------------------------------------------------------

    def generate_axis_protocol(self, axis_take, line=None, timeline=None) -> dict[str, Any]:
        """
        Buduje pełny generated_protocol dla jednej osi TAKE.

        Wynik zawiera:
        - pełne rows dla całego TAKE,
        - uproszczone listy STEP/DIR/ENABLE/AMP/COUNT,
        - step_count_total,
        - validated + messages.
        """
        sample_ms = self._resolve_sample_ms(timeline)
        take_start, take_end = self._resolve_timeline_bounds(axis_take=axis_take, line=line, timeline=timeline)
        times_ms = list(range(take_start, take_end + sample_ms, sample_ms))
        if not times_ms:
            times_ms = [0]

        amps = self._sample_axis_amplitudes(axis_take=axis_take, line=line, times_ms=times_ms)
        direction = self._build_direction_samples(amps)
        target_pulses = self._resolve_target_pulses(axis_take, len(times_ms))
        density = self._build_segment_aware_density(
            axis_take=axis_take,
            times_ms=times_ms,
            amps=amps,
            target_pulses=target_pulses,
            sample_ms=sample_ms,
        )

        rows = self._generate_rows_from_density(
            times_ms=times_ms,
            density=density,
            direction_hint=1,
            enable=1 if getattr(axis_take, "axis_enabled", True) else 0,
            start_count=0,
            dir_samples=direction,
            amp_samples=amps,
        )
        rows = self._ensure_exact_total(rows=rows, requested_pulses=int(target_pulses))

        messages = self._build_messages(axis_take=axis_take, rows=rows, requested_pulses=target_pulses)
        validated = len(messages) == 0

        step_samples = [int(row.step) for row in rows]
        dir_samples = [int(row.dir) for row in rows]
        enable_samples = [int(row.enable) for row in rows]
        amp_samples = [float(row.amp) for row in rows]
        count_samples = [int(row.count) for row in rows]

        serialized_rows = [row.to_dict() for row in rows]
        protocol = {
            "sample_ms": int(sample_ms),
            "take_start": int(times_ms[0]),
            "take_end": int(times_ms[-1]),
            "rows": serialized_rows,
            "protocol_rows": serialized_rows,
            "step_samples": step_samples,
            "dir_samples": dir_samples,
            "enable_samples": enable_samples,
            "amp_samples": amp_samples,
            "count_samples": count_samples,
            "step_count_total": int(count_samples[-1] if count_samples else 0),
            "requested_step_count_total": int(target_pulses),
            "validated": bool(validated),
            "messages": messages,
        }
        return protocol

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def _generate_rows_from_density(
        self,
        times_ms: Sequence[int],
        density: Sequence[float],
        direction_hint: int,
        enable: int,
        start_count: int,
        dir_samples: Sequence[int] | None = None,
        amp_samples: Sequence[float] | None = None,
    ) -> list[TarzanProtocolRow]:
        rows: list[TarzanProtocolRow] = []
        accumulator = 0.0
        count = int(start_count)

        for index, time_ms in enumerate(times_ms):
            d = float(density[index]) if index < len(density) else 0.0
            accumulator += max(0.0, d)

            ev = int(accumulator)
            if ev > 0:
                accumulator -= float(ev)
                count += ev
            step = 1 if ev > 0 else 0

            dir_value = (
                int(dir_samples[index])
                if dir_samples is not None and index < len(dir_samples)
                else int(direction_hint)
            )
            amp = (
                float(amp_samples[index])
                if amp_samples is not None and index < len(amp_samples)
                else 0.0
            )

            rows.append(
                TarzanProtocolRow(
                    sample_index=index,
                    time_ms=int(time_ms),
                    dir=dir_value,
                    step=int(step),
                    ev=int(ev),
                    enable=int(enable),
                    amp=float(amp),
                    count=int(count),
                )
            )

        return rows

    def _build_density_from_amplitudes(
        self,
        amps: Sequence[float],
        axis_take,
        target_pulses: int,
        sample_ms: int,
    ) -> list[float]:
        # Uproszczony rozkład impulsów z krzywej
        n=len(amps)
        density=[0.0]*n
        high=list(range(1,n,2))
        if not high:
            return density
        max_p=len(high)
        target_pulses=min(int(target_pulses),max_p)
        weights=[]
        for hi in high:
            lo=hi-1
            w=(abs(amps[lo])+abs(amps[hi]))*0.5
            weights.append(w)
        total=sum(weights) or len(weights)
        cumulative=0.0
        emitted=0
        pulses=[0]*len(high)
        for i,w in enumerate(weights):
            cumulative+=target_pulses*(w/total)
            if cumulative>=emitted+1:
                pulses[i]=1
                emitted+=1
        for idx,hi in enumerate(high):
            density[hi]=float(pulses[idx])
        return density

    def _build_segment_aware_density(
        self,
        axis_take,
        times_ms: Sequence[int],
        amps: Sequence[float],
        target_pulses: int,
        sample_ms: int,
    ) -> list[float]:
        if not amps:
            return []
        density = [0.0 for _ in amps]
        segments = self._find_active_segments(amps)
        if not segments:
            return density

        declared = [seg for seg in getattr(axis_take, "segments", []) or [] if not getattr(seg, "is_pause", False) and int(getattr(seg, "pulse_count", 0) or 0) > 0]
        areas = [sum(abs(float(amps[i])) for i in range(start, end + 1)) for start, end, _ in segments]
        total_area = sum(areas)
        targets: list[int] = []
        if len(declared) == len(segments):
            targets = [max(0, int(getattr(seg, "pulse_count", 0) or 0)) for seg in declared]
        else:
            allocated = 0
            for idx, area in enumerate(areas):
                if idx == len(areas) - 1:
                    seg_target = max(0, int(target_pulses) - allocated)
                elif total_area > 0:
                    seg_target = max(0, int(round(float(target_pulses) * (area / total_area))))
                    allocated += seg_target
                else:
                    seg_target = 0
                    allocated += seg_target
                targets.append(seg_target)

        for (start, end, sign), seg_target in zip(segments, targets):
            local_amps = [abs(float(v)) for v in amps[start:end + 1]]
            local_density = self._build_density_from_amplitudes(
                amps=local_amps,
                axis_take=axis_take,
                target_pulses=seg_target,
                sample_ms=sample_ms,
            )
            for offset, value in enumerate(local_density):
                density[start + offset] = float(value)
        return density

    def _find_active_segments(self, amps: Sequence[float], eps: float = 1e-9) -> list[tuple[int, int, int]]:
        segments: list[tuple[int, int, int]] = []
        idx = 0
        while idx < len(amps):
            while idx < len(amps) and abs(float(amps[idx])) <= eps:
                idx += 1
            if idx >= len(amps):
                break
            sign = 1 if float(amps[idx]) > 0 else -1
            start = idx
            end = idx
            while end + 1 < len(amps) and abs(float(amps[end + 1])) > eps and (1 if float(amps[end + 1]) > 0 else -1) == sign:
                end += 1
            segments.append((start, end, sign))
            idx = end + 1
        return segments

    def _redistribute_density(
        self,
        density: Sequence[float],
        weights: Sequence[float],
        target_total: float,
        per_sample_cap: float,
        max_iterations: int = 12,
    ) -> list[float]:
        out = [float(v) for v in density]
        target_total = max(0.0, float(target_total))
        per_sample_cap = max(0.0, float(per_sample_cap))

        for _ in range(max_iterations):
            missing = target_total - sum(out)
            if missing <= 1e-9:
                break

            free = [max(0.0, per_sample_cap - v) for v in out]
            weighted_free = [free_i * max(0.0, w) for free_i, w in zip(free, weights)]
            denom = sum(weighted_free)
            if denom <= 1e-12:
                break

            for idx, capacity in enumerate(free):
                if capacity <= 0.0:
                    continue
                share = missing * (weighted_free[idx] / denom)
                out[idx] += min(capacity, share)

        residual = target_total - sum(out)
        if residual > 1e-9:
            free = [max(0.0, per_sample_cap - v) for v in out]
            for idx in sorted(range(len(out)), key=lambda i: (max(0.0, weights[i]), free[i]), reverse=True):
                if residual <= 1e-9:
                    break
                capacity = free[idx]
                if capacity <= 0.0:
                    continue
                delta = min(capacity, residual)
                out[idx] += delta
                residual -= delta

        return out


    def _ensure_exact_total(self, rows: list[TarzanProtocolRow], requested_pulses: int) -> list[TarzanProtocolRow]:
        if not rows:
            return rows
        requested_pulses = max(0, int(requested_pulses))
        current_total = int(rows[-1].count)
        if current_total == requested_pulses:
            return rows

        adjusted = list(rows)
        target_index = None
        for idx in range(len(adjusted) - 1, -1, -1):
            if abs(float(adjusted[idx].amp)) > 1e-12:
                target_index = idx
                break
        if target_index is None:
            target_index = len(adjusted) - 1

        delta = requested_pulses - current_total
        row = adjusted[target_index]
        new_ev = max(0, int(row.ev) + delta)
        new_step = 1 if new_ev > 0 else 0
        adjusted[target_index] = TarzanProtocolRow(
            sample_index=row.sample_index,
            time_ms=row.time_ms,
            dir=row.dir,
            step=new_step,
            ev=new_ev,
            enable=row.enable,
            amp=row.amp,
            count=0,
        )

        cumulative = 0
        rebuilt: list[TarzanProtocolRow] = []
        for row in adjusted:
            cumulative += int(row.ev)
            rebuilt.append(TarzanProtocolRow(
                sample_index=row.sample_index,
                time_ms=row.time_ms,
                dir=row.dir,
                step=row.step,
                ev=row.ev,
                enable=row.enable,
                amp=row.amp,
                count=cumulative,
            ))
        return rebuilt

    # ------------------------------------------------------------------
    # Timeline / sampling helpers
    # ------------------------------------------------------------------

    def _resolve_sample_ms(self, timeline) -> int:
        timeline_step = int(getattr(timeline, "sample_step", self.sample_ms) or self.sample_ms)
        return max(1, timeline_step)

    def _resolve_timeline_bounds(self, axis_take, line, timeline) -> tuple[int, int]:
        start = int(getattr(timeline, "take_start", 0) or 0)
        end = int(getattr(timeline, "take_end", 0) or 0)

        point_times = [time_ms for time_ms, _ in self._collect_points(axis_take=axis_take, line=line)]
        if point_times:
            start = min(start, min(point_times))
            end = max(end, max(point_times))

        if end <= start:
            sample_ms = self._resolve_sample_ms(timeline)
            end = start + sample_ms

        return int(start), int(end)

    def _sample_axis_amplitudes(self, axis_take, line, times_ms: Sequence[int]) -> list[float]:
        points = self._collect_points(axis_take=axis_take, line=line)
        if not points:
            return [0.0 for _ in times_ms]
        if len(points) == 1:
            return [float(points[0][1]) for _ in times_ms]

        result: list[float] = []
        segment_index = 0

        for t in times_ms:
            while segment_index < len(points) - 2 and t > points[segment_index + 1][0]:
                segment_index += 1

            left_time, left_amp = points[segment_index]
            right_time, right_amp = points[min(segment_index + 1, len(points) - 1)]

            if right_time <= left_time:
                result.append(float(right_amp))
                continue

            if t <= left_time:
                result.append(float(left_amp))
                continue
            if t >= right_time and segment_index == len(points) - 2:
                result.append(float(right_amp))
                continue

            ratio = (float(t) - float(left_time)) / (float(right_time) - float(left_time))
            amp = float(left_amp) + ratio * (float(right_amp) - float(left_amp))
            result.append(float(amp))

        return result

    def _collect_points(self, axis_take, line) -> list[tuple[int, float]]:
        points: list[tuple[int, float]] = []

        if line is not None and getattr(line, "nodes", None):
            for node in getattr(line, "nodes", []):
                points.append((int(getattr(node, "time_ms", 0)), float(getattr(node, "value", 0.0))))
        else:
            curve = getattr(axis_take, "curve", None)
            for cp in getattr(curve, "control_points", []) or []:
                points.append((int(getattr(cp, "time", 0)), float(getattr(cp, "amplitude", 0.0))))

        points.sort(key=lambda item: item[0])

        normalized: list[tuple[int, float]] = []
        for time_ms, amp in points:
            if normalized and normalized[-1][0] == time_ms:
                normalized[-1] = (time_ms, amp)
            else:
                normalized.append((time_ms, amp))
        return normalized

    def _build_direction_samples(self, amps: Sequence[float]) -> list[int]:
        result: list[int] = []
        last_dir = 0
        for amp in amps:
            if amp > 0:
                last_dir = 1
            elif amp < 0:
                last_dir = 0
            result.append(last_dir)
        return result

    # ------------------------------------------------------------------
    # Pulse budgets and limits
    # ------------------------------------------------------------------

    def _resolve_target_pulses(self, axis_take, sample_count: int) -> int:
        requested = 0

        # 1. jawna liczba impulsów z segmentów TAKE jest nadrzędna
        requested = int(sum(int(getattr(seg, "pulse_count", 0) or 0) for seg in getattr(axis_take, "segments", []) or []))

        # 2. jeśli brak segmentów, sprawdzamy sygnał źródłowy
        if requested <= 0:
            raw_signal = getattr(axis_take, "raw_signal", {}) or {}
            if isinstance(raw_signal, dict):
                requested = int(raw_signal.get("step_count_total", 0) or 0)

        # 3. dopiero na końcu używamy mechaniki osi jako źródła prawdy dla pełnego ruchu generatora
        if requested <= 0:
            requested = int(getattr(axis_take, "full_cycle_pulses", 0) or 0)

        # 4. fallback do poprzedniego protokołu tylko gdy nie ma nic lepszego
        if requested <= 0:
            generated = getattr(axis_take, "generated_protocol", {}) or {}
            if isinstance(generated, dict):
                requested = int(generated.get("requested_step_count_total", 0) or generated.get("step_count_total", 0) or 0)

        return max(0, int(requested))

    def _resolve_max_steps_per_sample(self, axis_take, sample_ms: int) -> float:
        max_rate = float(getattr(axis_take, "max_pulse_rate", 0) or 0)
        if max_rate <= 0.0:
            return float(1_000_000)
        mechanical_cap = max_rate * (float(sample_ms) / 1000.0)
        return max(0.0, mechanical_cap)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def _build_messages(self, axis_take, rows: Sequence[TarzanProtocolRow], requested_pulses: int) -> list[str]:
        messages: list[str] = []
        generated = int(rows[-1].count if rows else 0)

        if generated != int(requested_pulses):
            messages.append(
                f"{getattr(axis_take, 'axis_name', 'oś')}: generated step_count_total={generated} != requested={int(requested_pulses)}"
            )

        if rows and getattr(axis_take, "start_must_be_zero", True) and rows[0].step != 0:
            messages.append(f"{getattr(axis_take, 'axis_name', 'oś')}: start STEP musi być 0")

        if rows and getattr(axis_take, "end_must_be_zero", True) and rows[-1].step != 0:
            messages.append(f"{getattr(axis_take, 'axis_name', 'oś')}: end STEP musi być 0")

        return messages

    # ------------------------------------------------------------------
    # Utility helpers for legacy API
    # ------------------------------------------------------------------

    def _normalize_times(self, values: Iterable[float]) -> list[int]:
        return [int(round(float(v))) for v in values]

    def _normalize_density(self, values: Iterable[float]) -> list[float]:
        normalized = [max(0.0, float(v) * (self.sample_ms / 1000.0)) for v in values]
        return normalized
