from dataclasses import dataclass

@dataclass
class KroLine:
    line_id: str
    source_axis_id: str
    target_axis_id: str
    relation_type: str = 'KONTRA' # KONTRA, FOLLOW, COMP, SYNC
    strength: float = 1.0
    enabled: bool = True
