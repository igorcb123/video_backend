"""
Módulo de definición de la clase Escena.
"""
from typing import List

class Escena:
    """
    Clase que representa una escena generada a partir de una frase.
    Una escena siempre es parte de una sola frase.

    Atributos:
        orden (int): Orden de aparición de la escena en el proyecto.
        frase_orden (int): Orden de la frase a la que pertenece esta escena.
        palabra_inicio (int): Índice de la palabra inicial en la lista de palabras.
        palabra_fin (int): Índice de la palabra final en la lista de palabras.
        visual_focus (str): Descripción del foco visual de la escena.
    """
    def __init__(
        self,
        orden: int,
        frase_orden: int,
        palabra_inicio: int,
        palabra_fin: int,
        visual_focus: str
    ):
        self.orden = orden
        self.frase_orden = frase_orden
        self.palabra_inicio = palabra_inicio
        self.palabra_fin = palabra_fin
        self.visual_focus = visual_focus
        
        # Validación básica
        if palabra_fin < palabra_inicio:
            raise ValueError(f"palabra_fin ({palabra_fin}) debe ser >= palabra_inicio ({palabra_inicio})")

    def __repr__(self) -> str:
        return (
            f"<Escena orden={self.orden} frase={self.frase_orden} "
            f"palabras={self.palabra_inicio}-{self.palabra_fin} "
            f"visual_focus='{self.visual_focus}'>"
        )