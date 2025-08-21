"""
Módulo de definición de la clase Proyecto.
"""
from datetime import datetime
from typing import List, Optional
from .palabra import Palabra
from .frase import Frase
from .escena import Escena
from .subtitulo import Subtitulo, EstiloSubtitulo

class ConfiguracionSubtitulos:
    """
    Configuración para la generación de subtítulos.
    """
    def __init__(
        self,
        duracion_maxima: float = 4.0,
        caracteres_maximos_linea: int = 42,
        lineas_maximas: int = 2,
        gap_minimo: float = 0.1,
        estilo_default: Optional[EstiloSubtitulo] = None
    ):
        self.duracion_maxima = duracion_maxima
        self.caracteres_maximos_linea = caracteres_maximos_linea
        self.lineas_maximas = lineas_maximas
        self.gap_minimo = gap_minimo
        self.estilo_default = estilo_default or EstiloSubtitulo()

class Proyecto:
    """
    Clase que representa un proyecto con sus atributos principales.
    Flujo: Texto → TTS (audio) → STT (timestamps) → Palabras → Frases → Escenas/Subtítulos → Video

    Atributos:
        id (int): Identificador único del proyecto.
        titulo (str): Título del proyecto.
        texto (str): Texto original del proyecto.
        etiquetas (List[str]): Lista de etiquetas asociadas al proyecto.
        descripcion (str): Descripción del proyecto.
        archivo_sonido (Optional[str]): Ruta o identificador del archivo de sonido.
        fecha_creacion (datetime): Fecha de creación del proyecto.
        fecha_produccion (Optional[datetime]): Fecha de producción del proyecto.
        fecha_publicacion (Optional[datetime]): Fecha de publicación del proyecto.
        palabras (List[Palabra]): Lista de palabras asociadas al proyecto.
        frases (List[Frase]): Lista de frases del proyecto.
        escenas (List[Escena]): Lista de escenas del proyecto.
        subtitulos (List[Subtitulo]): Lista de subtítulos del proyecto.
        config_subtitulos (ConfiguracionSubtitulos): Configuración para subtítulos.
    """
    def __init__(
        self,
        id: int,
        titulo: str,
        texto: str,
        etiquetas: Optional[List[str]] = None,
        descripcion: str = "",
        archivo_sonido: Optional[str] = None,
        fecha_creacion: Optional[datetime] = None,
        fecha_produccion: Optional[datetime] = None,
        fecha_publicacion: Optional[datetime] = None,
        palabras: Optional[List[Palabra]] = None,
        frases: Optional[List[Frase]] = None,
        escenas: Optional[List[Escena]] = None,
        subtitulos: Optional[List[Subtitulo]] = None,
        config_subtitulos: Optional[ConfiguracionSubtitulos] = None
    ):
        self.id = id
        self.titulo = titulo
        self.texto = texto
        self.etiquetas = etiquetas or []
        self.descripcion = descripcion
        self.archivo_sonido = archivo_sonido
        self.fecha_creacion = fecha_creacion or datetime.now()
        self.fecha_produccion = fecha_produccion
        self.fecha_publicacion = fecha_publicacion
        self.palabras = palabras or []
        self.frases = frases or []
        self.escenas = escenas or []
        self.subtitulos = subtitulos or []
        self.config_subtitulos = config_subtitulos or ConfiguracionSubtitulos()

    def __repr__(self) -> str:
        return (
            f"<Proyecto id={self.id} titulo='{self.titulo}' "
            f"etiquetas={self.etiquetas} fecha_creacion={self.fecha_creacion} "
            f"palabras={len(self.palabras)} frases={len(self.frases)} "
            f"escenas={len(self.escenas)} subtitulos={len(self.subtitulos)}>"
        )

    def duracion(self) -> float:
        """
        Calcula la duración total del proyecto usando los timestamps de las palabras.

        Returns:
            float: Duración total en segundos.
        """
        if not self.palabras:
            return 0.0
        inicio = self.palabras[0].timestamp_inicio
        fin = self.palabras[-1].timestamp_fin
        return fin - inicio

    def texto_procesado(self) -> str:
        """
        Regenera el texto a partir de las palabras procesadas.
        Útil para verificar consistencia con el texto original.

        Returns:
            str: Texto reconstruido desde las palabras.
        """
        if not self.palabras:
            return ""
        return ' '.join(palabra.palabra for palabra in self.palabras)

    def verificar_consistencia(self) -> bool:
        """
        Verifica si el texto original coincide básicamente con el texto procesado.
        (Ignorando espaciado múltiple y diferencias menores)

        Returns:
            bool: True si son consistentes.
        """
        texto_original = ' '.join(self.texto.split())
        texto_procesado = ' '.join(self.texto_procesado().split())
        return texto_original.lower() == texto_procesado.lower()

    def texto_frase(self, ordinal: int) -> str:
        """
        Devuelve el texto de la frase indicada por su ordinal.

        Args:
            ordinal (int): El orden de la frase (0-based).

        Returns:
            str: Texto de la frase.
        """
        if not self.frases or ordinal < 0 or ordinal >= len(self.frases):
            return ""
        frase = self.frases[ordinal]
        if frase.palabra_fin >= len(self.palabras):
            return ""
        return ' '.join(p.palabra for p in self.palabras[frase.palabra_inicio:frase.palabra_fin+1])

    def textos_frases(self) -> List[str]:
        """
        Devuelve una lista con el texto de todas las frases del proyecto.

        Returns:
            List[str]: Lista de textos de frases.
        """
        return [self.texto_frase(i) for i in range(len(self.frases))]

    def texto_escena(self, ordinal: int) -> str:
        """
        Devuelve el texto de la escena indicada por su ordinal.

        Args:
            ordinal (int): El orden de la escena (0-based).

        Returns:
            str: Texto de la escena.
        """
        if not self.escenas or ordinal < 0 or ordinal >= len(self.escenas):
            return ""
        escena = self.escenas[ordinal]
        if escena.palabra_fin >= len(self.palabras):
            return ""
        return ' '.join(p.palabra for p in self.palabras[escena.palabra_inicio:escena.palabra_fin+1])

    def textos_escenas(self) -> List[str]:
        """
        Devuelve una lista con el texto de todas las escenas del proyecto.

        Returns:
            List[str]: Lista de textos de escenas.
        """
        return [self.texto_escena(i) for i in range(len(self.escenas))]

    def duracion_escena(self, ordinal: int) -> float:
        """
        Devuelve la duración de la escena indicada por su ordinal.

        Args:
            ordinal (int): El orden de la escena (0-based).

        Returns:
            float: Duración en segundos.
        """
        if not self.escenas or ordinal < 0 or ordinal >= len(self.escenas):
            return 0.0
        escena = self.escenas[ordinal]
        if (not self.palabras or escena.palabra_inicio >= len(self.palabras) 
            or escena.palabra_fin >= len(self.palabras)):
            return 0.0
        inicio = self.palabras[escena.palabra_inicio].timestamp_inicio
        fin = self.palabras[escena.palabra_fin].timestamp_fin
        return fin - inicio

    def timestamp_inicio_escena(self, ordinal: int) -> float:
        """
        Devuelve el timestamp de inicio de la escena indicada por su ordinal.
        """
        if not self.escenas or ordinal < 0 or ordinal >= len(self.escenas):
            return 0.0
        escena = self.escenas[ordinal]
        if not self.palabras or escena.palabra_inicio >= len(self.palabras):
            return 0.0
        return self.palabras[escena.palabra_inicio].timestamp_inicio

    def timestamp_fin_escena(self, ordinal: int) -> float:
        """
        Devuelve el timestamp de fin de la escena indicada por su ordinal.
        """
        if not self.escenas or ordinal < 0 or ordinal >= len(self.escenas):
            return 0.0
        escena = self.escenas[ordinal]
        if not self.palabras or escena.palabra_fin >= len(self.palabras):
            return 0.0
        return self.palabras[escena.palabra_fin].timestamp_fin

    # Métodos para subtítulos
    def duracion_subtitulo(self, ordinal: int) -> float:
        """
        Devuelve la duración del subtítulo indicado por su ordinal.

        Args:
            ordinal (int): El orden del subtítulo (0-based).

        Returns:
            float: Duración en segundos.
        """
        if not self.subtitulos or ordinal < 0 or ordinal >= len(self.subtitulos):
            return 0.0
        subtitulo = self.subtitulos[ordinal]
        if (not self.palabras or subtitulo.palabra_inicio >= len(self.palabras) 
            or subtitulo.palabra_fin >= len(self.palabras)):
            return 0.0
        inicio = self.palabras[subtitulo.palabra_inicio].timestamp_inicio
        fin = self.palabras[subtitulo.palabra_fin].timestamp_fin
        return fin - inicio

    def timestamp_inicio_subtitulo(self, ordinal: int) -> float:
        """
        Devuelve el timestamp de inicio del subtítulo indicado por su ordinal.
        """
        if not self.subtitulos or ordinal < 0 or ordinal >= len(self.subtitulos):
            return 0.0
        subtitulo = self.subtitulos[ordinal]
        if not self.palabras or subtitulo.palabra_inicio >= len(self.palabras):
            return 0.0
        return self.palabras[subtitulo.palabra_inicio].timestamp_inicio

    def timestamp_fin_subtitulo(self, ordinal: int) -> float:
        """
        Devuelve el timestamp de fin del subtítulo indicado por su ordinal.
        """
        if not self.subtitulos or ordinal < 0 or ordinal >= len(self.subtitulos):
            return 0.0
        subtitulo = self.subtitulos[ordinal]
        if not self.palabras or subtitulo.palabra_fin >= len(self.palabras):
            return 0.0
        return self.palabras[subtitulo.palabra_fin].timestamp_fin

    def subtitulos_por_frase(self, orden_frase: int) -> List[Subtitulo]:
        """
        Devuelve todos los subtítulos que pertenecen a una frase específica.

        Args:
            orden_frase (int): Orden de la frase.

        Returns:
            List[Subtitulo]: Lista de subtítulos de la frase.
        """
        return [sub for sub in self.subtitulos if sub.frase_orden == orden_frase]

    def escenas_por_frase(self, orden_frase: int) -> List[Escena]:
        """
        Devuelve todas las escenas que pertenecen a una frase específica.

        Args:
            orden_frase (int): Orden de la frase.

        Returns:
            List[Escena]: Lista de escenas de la frase.
        """
        return [esc for esc in self.escenas if esc.frase_orden == orden_frase]