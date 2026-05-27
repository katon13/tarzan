from typing import List, Tuple, Optional
import numpy as np

class KroEngine:
    @staticmethod
    def calculate_target_line(
        source_curve: List[Tuple[int, float]], 
        target_base_curve: List[Tuple[int, float]], 
        relation_type: str, 
        strength: float,
        enabled: bool = True,
        y_limit: Optional[float] = None
    ) -> List[Tuple[int, float]]:
        if not enabled or not source_curve or not target_base_curve:
            return target_base_curve
        
        # Dispatch types
        if relation_type in ["DIAGNOSTYKA", "ADRR GUIDE", "SYNC"]:
            return target_base_curve

        # Ensure we can interpolate source values at target times
        src_times = np.array([p[0] for p in source_curve])
        src_vals = np.array([p[1] for p in source_curve])
        
        # Source reference is 0.0 in EHR models
        source_reference = 0.0
        
        result_vals = []
        target_times = [p[0] for p in target_base_curve]
        target_base_vals = [p[1] for p in target_base_curve]
        
        # Interpolate source values at target times
        interpolated_src_vals = np.interp(target_times, src_times, src_vals)
        
        for i in range(len(target_times)):
            t_val = target_base_vals[i]
            source_delta = interpolated_src_vals[i] - source_reference
            
            if relation_type == 'KONTRA':
                res_val = t_val - source_delta * strength
            elif relation_type == 'FOLLOW':
                res_val = t_val + source_delta * strength
            elif relation_type == 'COMP':
                # COMP is 50% strength contra
                res_val = t_val - source_delta * (strength * 0.5)
            else:
                res_val = t_val
            
            result_vals.append(res_val)

        # Soft-fit / auto-scale if limit provided
        if y_limit is not None and len(result_vals) > 0:
            max_abs = max(abs(v) for v in result_vals)
            if max_abs > y_limit:
                scale = y_limit / max_abs
                result_vals = [v * scale for v in result_vals]
            
            # Final safety clamp
            result_vals = [max(-y_limit, min(y_limit, v)) for v in result_vals]
                
        return list(zip(target_times, result_vals))

    @staticmethod
    def topological_sort(relations: List['KroLine'], axis_ids: List[str]) -> List[str]:
        """
        Sortuje osie tak, aby SOURCE zawsze był przed TARGET.
        Zwraca listę axis_id.
        """
        from collections import defaultdict, deque
        
        adj = defaultdict(list)
        in_degree = {aid: 0 for aid in axis_ids}
        
        for rel in relations:
            if rel.enabled:
                adj[rel.source_axis_id].append(rel.target_axis_id)
                in_degree[rel.target_axis_id] += 1
                
        queue = deque([aid for aid in axis_ids if in_degree[aid] == 0])
        sorted_ids = []
        
        while queue:
            u = queue.popleft()
            sorted_ids.append(u)
            
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        # Jeśli nie wszystkie osie są w sorted_ids, mamy cykl.
        # W takim przypadku zwracamy oryginalną listę lub zgłaszamy błąd, 
        # ale dla stabilności zwrócimy co się udało.
        if len(sorted_ids) < len(axis_ids):
            # Doklejamy brakujące osie (te w cyklu) na koniec, żeby nie zniknęły
            missing = set(axis_ids) - set(sorted_ids)
            sorted_ids.extend(list(missing))
            
        return sorted_ids
