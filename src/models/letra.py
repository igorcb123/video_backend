from dataclasses import dataclass

@dataclass
class Letra:
    orden: int
    letra: str
    timestamp_inicio: float
    timestamp_fin: float
