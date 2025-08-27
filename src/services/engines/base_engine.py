from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseTTSEngine(ABC):
    """
    Interfaz base para motores TTS.
    """

    @abstractmethod
    def synthesize(self, text: str, output_path: str, **kwargs: Any) -> None:
        """
        Genera un archivo de audio a partir de texto.

        Args:
            text (str): Texto a sintetizar.
            output_path (str): Ruta donde se guardará el archivo generado.
            **kwargs (Any): Parámetros adicionales específicos del motor.

        Raises:
            RuntimeError: Si ocurre un error durante la síntesis.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nombre del motor TTS.

        Returns:
            str: Nombre del motor.
        """
        pass

    def supports_voice_cloning(self) -> bool:
        """
        Indica si el motor soporta clonación de voz.

        Returns:
            bool: True si soporta clonación de voz.
        """
        return False
