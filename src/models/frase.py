"""
Módulo de definición de la clase Frase.
"""
from typing import List

class Frase:
    """
    Clase que representa una frase dentro de un proyecto.

    Atributos:
        orden (int): Orden de aparición de la frase.
        palabra_inicio (int): Índice de la palabra inicial en la lista de palabras.
        palabra_fin (int): Índice de la palabra final en la lista de palabras.
    """
    def __init__(
        self,
        orden: int,
        palabra_inicio: int,
        palabra_fin: int
    ):
        self.orden = orden
        self.palabra_inicio = palabra_inicio
        self.palabra_fin = palabra_fin
        
        # Validación básica
        if palabra_fin < palabra_inicio:
            raise ValueError(f"palabra_fin ({palabra_fin}) debe ser >= palabra_inicio ({palabra_inicio})")

    def __repr__(self) -> str:
        return (
            f"<Frase orden={self.orden} palabras={self.palabra_inicio}-{self.palabra_fin}>"
        )