import subprocess
from pathlib import Path
from services.engines.base_engine import BaseTTSEngine

class PiperEngine(BaseTTSEngine):
    """
    Implementación del motor TTS para Piper.
    """

    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """
        Genera un archivo de audio usando Piper.

        Args:
            text (str): Texto a sintetizar.
            output_path (str): Ruta donde se guardará el archivo generado.
            **kwargs: Debe incluir 'model_path' con la ruta al modelo .onnx.

        Raises:
            RuntimeError: Si ocurre un error durante la síntesis.
            FileNotFoundError: Si el modelo Piper no se encuentra.
        """
        model_path = kwargs.get("model_path")
        if not model_path:
            raise FileNotFoundError("Piper model path not provided in kwargs (expected key: 'model_path')")

        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(
                f"Piper model not found at: {model_path_obj.resolve()}\n"
                "Asegúrate de que el archivo .onnx exista y que 'tts_model_path' en config.settings apunte al directorio correcto."
            )

        cmd = [
            "piper",
            "--model", str(model_path),
            "--output_file", output_path
        ]

        try:
            process = subprocess.run(
                cmd,
                input=text.encode("utf-8"),  # Codifica el texto explícitamente
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper synthesis failed: {e.stderr.decode('utf-8') if e.stderr else 'Unknown error'}")
        except FileNotFoundError:
            raise RuntimeError("Piper not found. Install with: pip install piper-tts")

    @property
    def name(self) -> str:
        return "piper"
