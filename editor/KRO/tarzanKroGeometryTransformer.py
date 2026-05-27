from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from editor.KRO.tarzanKroTypes import KroAxisLine, KroAxisMechanicalProfile, KroTuningProfile, KroPluginType

class KroGeometryTransformer:
    """
    Zaawansowany transformator geometrii linii KRO.
    Zamiast prostego mnożenia, analizuje dynamikę SOURCE i nakłada ograniczenia fizyczne TARGET.
    """

    def __init__(
        self,
        *,
        source_line: KroAxisLine,
        target_line: KroAxisLine,
        source_mech: KroAxisMechanicalProfile,
        target_mech: KroAxisMechanicalProfile,
        tuning: KroTuningProfile,
        plugin_base_multiplier: float, # np. -1.0 dla KONTRY
        sampling_ms: int = 10,
        is_sync: bool = False
    ):
        self.source_line = source_line
        self.target_line = target_line
        self.source_mech = source_mech
        self.target_mech = target_mech
        self.tuning = tuning
        self.plugin_base_multiplier = plugin_base_multiplier
        self.sampling_ms = sampling_ms
        self.is_sync = is_sync

    def transform(self) -> list[tuple[int, float]]:
        from editor.KRO.tarzanKroLineTools import sorted_points, value_at

        src_pts = sorted_points(self.source_line.points)
        tgt_pts = sorted_points(self.target_line.points)

        if not src_pts or not tgt_pts:
            return tgt_pts

        t_start = tgt_pts[0][0]
        t_end = tgt_pts[-1][0]
        
        if t_end <= t_start:
            return tgt_pts

        # 1. Resampling i analiza dynamiki
        # Obliczamy roboczy gain uwzględniający wszystko poza wagami dynamicznymi
        effective_gain = (
            self.plugin_base_multiplier *
            self.tuning.axis_multiplier *
            self.tuning.empirical_gain *
            self.tuning.damping *
            self.tuning.direction_correction
        )

        source_ref_y = float(src_pts[0][1])
        target_ref_y = float(tgt_pts[0][1])

        # Stan transformatora (do efektów histerezy/inercji)
        prev_target_y = target_ref_y
        prev_velocity_pps = 0.0
        
        # Filtry i stany
        inertia_y = target_ref_y
        last_dir = 0 # 1: up, -1: down, 0: none

        result_points: list[tuple[int, float]] = []
        
        # Przygotowanie stałych mechanicznych
        pulses_per_y = self.target_mech.pulses_per_cycle / 100.0
        max_pps = self.target_mech.cruise_max_pulses_per_second * (2.0 - self.tuning.cruise_limit_weight)
        
        # Akceleracja (proste przybliżenie z rampy)
        # Jeśli start_ramp_time to 0.5s do pełnej prędkości, to a = max_pps / 0.5
        accel_pps2 = 1000000.0 # domyślnie "nieskończona"
        if self.target_mech.start_ramp_time > 0:
            accel_pps2 = self.target_mech.cruise_max_pulses_per_second / self.target_mech.start_ramp_time
            # Modulujemy wagą (im większa waga, tym mniejsza akceleracja = dłuższa rampa)
            accel_pps2 /= (1.0 + self.tuning.start_ramp_weight * 3.0)

        # 4. Przygotowanie gęstej siatki czasu z uwzględnieniem punktów TARGET
        target_times_list = sorted(set(int(t) for t, _ in tgt_pts))
        all_times_set = set()
        for i in range(len(target_times_list) - 1):
            t_curr = target_times_list[i]
            t_next = target_times_list[i+1]
            t = t_curr
            while t < t_next:
                all_times_set.add(t)
                t += self.sampling_ms
        all_times_set.add(target_times_list[-1])
        sorted_times = sorted(list(all_times_set))

        for i, current_t in enumerate(sorted_times):
            if i == 0:
                dt_sec = self.sampling_ms / 1000.0
            else:
                dt_sec = (current_t - sorted_times[i-1]) / 1000.0
            
            if dt_sec <= 0:
                dt_sec = 0.001 # fallback

            # Aktualne wartości z wejścia
            curr_src_y = value_at(src_pts, current_t)
            curr_tgt_base_y = value_at(tgt_pts, current_t)
            
            # 2. Obliczanie wpływu KRO (surowy delta lub sync error)
            source_delta = curr_src_y - source_ref_y
            
            if self.is_sync:
                target_delta = curr_tgt_base_y - target_ref_y
                sync_error = source_delta - target_delta
                raw_kro_effect = sync_error * effective_gain
            else:
                raw_kro_effect = source_delta * effective_gain
            
            # Limitowanie surowego wpływu
            if self.tuning.max_effect_limit < 100.0:
                raw_kro_effect = max(-self.tuning.max_effect_limit, min(self.tuning.max_effect_limit, raw_kro_effect))
            
            # Docelowy punkt przed filtrami (bazowy target + wpływ KRO)
            target_goal_y = curr_tgt_base_y + raw_kro_effect
            
            # 3. Analiza dy/dt i ograniczenia mechaniczne TARGET
            
            # a) Bezwładność (Inertia) - prosty filtr dolnoprzepustowy (EMA)
            alpha = 1.0 / (1.0 + self.tuning.inertia_weight * 5.0) 
            inertia_y = inertia_y + alpha * (target_goal_y - inertia_y)
            
            # b) Backlash (Luz)
            current_move_dir = 1 if (inertia_y > prev_target_y + 0.0001) else (-1 if inertia_y < prev_target_y - 0.0001 else 0)
            if current_move_dir != 0 and current_move_dir != last_dir and last_dir != 0:
                if pulses_per_y > 0:
                    # Chwilowe zatrzymanie przy zmianie kierunku
                    inertia_y = prev_target_y
            
            if current_move_dir != 0:
                last_dir = current_move_dir

            # c) Ograniczenia dynamiki (Prędkość i Akceleracja)
            if pulses_per_y > 0:
                target_dy = inertia_y - prev_target_y
                target_dpulses = target_dy * pulses_per_y
                target_velocity_pps = target_dpulses / dt_sec
                
                # Ograniczenie akceleracji
                dv_max = accel_pps2 * dt_sec
                actual_velocity_pps = max(prev_velocity_pps - dv_max, min(prev_velocity_pps + dv_max, target_velocity_pps))
                
                # Ograniczenie prędkości (Cruise)
                if max_pps > 0:
                    actual_velocity_pps = max(-max_pps, min(max_pps, actual_velocity_pps))
                
                # Przeliczamy z powrotem na y
                actual_dpulses = actual_velocity_pps * dt_sec
                final_y = prev_target_y + (actual_dpulses / pulses_per_y)
                prev_velocity_pps = actual_velocity_pps
            else:
                final_y = inertia_y
            
            # d) Start Settle - dodatkowe tłumienie na małych prędkościach
            if self.tuning.start_settle_weight > 0 and abs(prev_velocity_pps) < (max_pps * 0.1):
                 # TODO: implementation of settle damping
                 pass

            # Dodajemy punkt do wyniku
            result_points.append((int(current_t), float(final_y)))
            
            # Update stanu
            prev_target_y = final_y
            
        # 5. Upraszczanie wyniku
        return self._simplify_points(result_points)

    def _simplify_points(self, points: list[tuple[int, float]]) -> list[tuple[int, float]]:
        """
        Zwraca rzadką linię operatorską zgodną z filozofią EHR.
        
        Zasada:
        1. Zachowaj start, koniec i wszystkie oryginalne punkty TARGET.
        2. Użyj Douglas-Peucker z limitem punktów, aby dodać tylko kluczowe punkty przełamania.
        3. Cel: ok. 4-6 punktów (max 10), aby linia była czytelna dla operatora.
        """
        if not points:
            return []

        # 1. Zidentyfikuj indeksy punktów TARGET (kotwice)
        target_times = sorted(set(int(t) for t, _ in self.target_line.points))
        anchor_indices = []
        p_idx = 0
        for t in target_times:
            while p_idx < len(points) and points[p_idx][0] < t:
                p_idx += 1
            if p_idx < len(points) and points[p_idx][0] == t:
                anchor_indices.append(p_idx)
                p_idx += 1
        
        if not anchor_indices:
            anchor_indices = [0, len(points) - 1]
        elif 0 not in anchor_indices:
            anchor_indices.insert(0, 0)
        elif len(points)-1 not in anchor_indices:
            anchor_indices.append(len(points)-1)
            
        final_indices = set(anchor_indices)
        
        # 2. Rekurencyjne upraszczanie (Douglas-Peucker) z kolejką priorytetową
        import heapq
        
        # Próg istotności (ok. 8-10% zakresu 100)
        threshold = 12.0
        max_total_points = 10
        
        def get_best_split(idx1, idx2):
            if idx2 - idx1 <= 2:
                return None, 0.0
            
            p1 = points[idx1]
            p2 = points[idx2]
            dt = float(p2[0] - p1[0]) if p2[0] > p1[0] else 1.0
            
            best_k = -1
            max_d = 0.0
            
            # Normalizacja czasu segmentu do 100 dla sprawiedliwej odległości
            for k in range(idx1 + 1, idx2):
                pk = points[k]
                nx = (pk[0] - p1[0]) / dt * 100.0
                ny = pk[1]
                
                dist = self._perpendicular_distance_norm((nx, ny), (0.0, p1[1]), (100.0, p2[1]))
                if dist > max_d:
                    max_d = dist
                    best_k = k
            return best_k, max_d

        # Kolejka segmentów: (-odległość, start, end, best_split_idx)
        segments = []
        sorted_anchors = sorted(list(final_indices))
        for i in range(len(sorted_anchors) - 1):
            k, d = get_best_split(sorted_anchors[i], sorted_anchors[i+1])
            if k is not None and d > threshold:
                heapq.heappush(segments, (-d, sorted_anchors[i], sorted_anchors[i+1], k))

        # Dodajemy punkty aż do limitu lub wyczerpania istotnych odchyleń
        while segments and len(final_indices) < max_total_points:
            neg_d, s_idx, e_idx, k_idx = heapq.heappop(segments)
            
            if k_idx in final_indices:
                continue
                
            final_indices.add(k_idx)
            
            # Nowe segmenty po podziale
            k1, d1 = get_best_split(s_idx, k_idx)
            if k1 is not None and d1 > threshold:
                heapq.heappush(segments, (-d1, s_idx, k_idx, k1))
                
            k2, d2 = get_best_split(k_idx, e_idx)
            if k2 is not None and d2 > threshold:
                heapq.heappush(segments, (-d2, k_idx, e_idx, k2))

        # 3. Zwróć posortowaną listę punktów
        return [points[i] for i in sorted(list(final_indices))]

    @staticmethod
    def _perpendicular_distance_norm(p: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Odległość punktu od prostej."""
        x, y = p
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((x - x1)**2 + (y - y1)**2)
        return abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.sqrt(dx**2 + dy**2)
