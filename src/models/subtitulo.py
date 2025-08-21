"""
Módulo de definición de la clase Subtitulo.
"""
from typing import Optional
from enum import Enum

class PosicionVertical(Enum):
    """Posiciones verticales para subtítulos."""
    ARRIBA = "arriba"
    CENTRO = "centro"
    ABAJO = "abajo"

class Justificacion(Enum):
    """Justificación del texto del subtítulo."""
    IZQUIERDA = "izquierda"
    CENTRO = "centro"
    DERECHA = "derecha"

class EstiloSubtitulo:
    """
    Clase para configurar el estilo de los subtítulos.
    """
    def __init__(
        self,
        fuente: str = "Arial",
        tamaño_fuente: int = 24,
        color_texto: str = "#FFFFFF",
        color_borde: str = "#000000",
        grosor_borde: int = 2,
        sombra: bool = True,
        color_sombra: str = "#000000",
        opacidad: float = 1.0
    ):
        self.fuente = fuente
        self.tamaño_fuente = tamaño_fuente
        self.color_texto = color_texto
        self.color_borde = color_borde
        self.grosor_borde = grosor_borde
        self.sombra = sombra
        self.color_sombra = color_sombra
        self.opacidad = opacidad

class Subtitulo:
    """
    Clase que representa un subtítulo dentro de un proyecto.
    Los subtítulos son subdivisiones de frases que incluyen puntuación.

    Atributos:
        orden (int): Orden de aparición del subtítulo.
        frase_orden (int): Orden de la frase a la que pertenece este subtítulo.
        palabra_inicio (int): Índice de la palabra inicial en la lista de palabras.
        palabra_fin (int): Índice de la palabra final en la lista de palabras.
        texto (str): Texto del subtítulo con puntuación incluida.
        posicion_vertical (PosicionVertical): Posición vertical del subtítulo.
        justificacion (Justificacion): Justificación del texto.
        estilo (EstiloSubtitulo): Configuración de estilo del subtítulo.
    """
    def __init__(
        self,
        orden: int,
        frase_orden: int,
        palabra_inicio: int,
        palabra_fin: int,
        texto: str,
        posicion_vertical: PosicionVertical = PosicionVertical.ABAJO,
        justificacion: Justificacion = Justificacion.CENTRO,
        estilo: Optional[EstiloSubtitulo] = None
    ):
        self.orden = orden
        self.frase_orden = frase_orden
        self.palabra_inicio = palabra_inicio
        self.palabra_fin = palabra_fin
        self.texto = texto
        self.posicion_vertical = posicion_vertical
        self.justificacion = justificacion
        self.estilo = estilo or EstiloSubtitulo()
        
        # Validación básica
        if palabra_fin < palabra_inicio:
            raise ValueError(f"palabra_fin ({palabra_fin}) debe ser >= palabra_inicio ({palabra_inicio})")
        if not texto.strip():
            raise ValueError("El texto del subtítulo no puede estar vacío")

    def __repr__(self) -> str:
        return (
            f"<Subtitulo orden={self.orden} frase={self.frase_orden} "
            f"palabras={self.palabra_inicio}-{self.palabra_fin} "
            f"texto='{self.texto[:30]}{'...' if len(self.texto) > 30 else ''}'>"
        )
