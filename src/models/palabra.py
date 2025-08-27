"""
Módulo de definición de la clase Palabra.
"""
from dataclasses import dataclass

@dataclass
class Palabra:
    """
    Clase que representa una palabra dentro de un proyecto, con información de tiempo.

    Atributos:
        orden (int): Orden de aparición de la palabra.
        palabra (str): La palabra en sí.
        timestamp_inicio (float): Momento de inicio (en segundos).
        timestamp_fin (float): Momento de fin (en segundos).
    """
    orden: int
    palabra: str
    timestamp_inicio: float
    timestamp_fin: float

    def __post_init__(self):
        # Validación básica
        if self.timestamp_fin < self.timestamp_inicio:
            raise ValueError(f"timestamp_fin ({self.timestamp_fin}) debe ser >= timestamp_inicio ({self.timestamp_inicio})")

    def duracion(self) -> float:
        """
        Calcula la duración de la palabra basada en los timestamps.

        Returns:
            float: Duración en segundos.
        """
        return self.timestamp_fin - self.timestamp_inicio

    def __repr__(self) -> str:
        return (
            f"<Palabra orden={self.orden} palabra='{self.palabra}' "
            f"inicio={self.timestamp_inicio} fin={self.timestamp_fin} "
            f"duracion={self.duracion():.2f}s>"
        )