import json
from pathlib import Path
from typing import Literal, Optional, Dict, List
from services.tts_cacher import TTSCacher
from services.engines.piper_engine import PiperEngine
from services.engines.coqui_engine import CoquiEngine
from services.alignment.simple_processor import SimpleProcessor
from models.letra import Letra
from models.palabra import Palabra
from config.settings import settings

try:
    from services.forced_alignment import WhisperAlignmentProcessor
except ImportError:
    WhisperAlignmentProcessor = None

class TTSService:
    """
    Orquestador principal para TTS con soporte para múltiples motores y alineación.
    API compatible con ElevenLabsTTSService.
    """

    def __init__(self, engine: Literal["piper", "coqui"] = "piper"):
        self.engine_name = engine
        # Asegurar que model_path sea absoluto para evitar problemas con cwd
        self.model_path = settings.tts_model_path.resolve()
        self.cache_enabled = settings.cache_enabled
        self.voice = getattr(settings, "tts_voice", "default")
        self._cacher = TTSCacher(settings.temp_dir / "tts_cache")
        self.engine = self._initialize_engine()
        self.alignment_processor, self.alignment_method = self._initialize_alignment_processor()

    def _initialize_engine(self):
        if self.engine_name == "piper":
            return PiperEngine()
        elif self.engine_name == "coqui":
            return CoquiEngine()
        else:
            raise ValueError(f"Motor TTS no soportado: {self.engine_name}")

    def _initialize_alignment_processor(self):
        """Inicializa el procesador de alineación forzada."""
        try:
            if WhisperAlignmentProcessor:
                return WhisperAlignmentProcessor(model_name="base", device="cpu"), "whisper"
            else:
                return SimpleProcessor(), "simple"
        except Exception:
            return SimpleProcessor(), "simple"

    def synthesize(self, text: str, output_path: Optional[str] = None, force_regenerate: bool = False, **kwargs) -> Optional[str]:
        """
        Sintetiza texto a voz localmente, con caché y opción de forzar regeneración.
        Devuelve la ruta al archivo generado.
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        cache_path = self._cacher.get_cache_path(text, self.engine.name, self.voice, ext=".wav")
        if output_path is None:
            output_path = str(cache_path)
        output_file = Path(output_path)

        if force_regenerate and output_file.exists():
            self._cacher.remove(output_file)

        if self.cache_enabled and output_file.exists():
            return str(output_file)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Preparar kwargs específicos para cada motor
        if self.engine_name == "piper":
            model_file = self.model_path / f"{self.voice}.onnx"
            # Si no existe en la ruta configurada, intentar buscar en el workspace (fallback)
            if not model_file.exists():
                print(f"⚠️  Piper model no encontrado en {model_file}, buscando en el workspace...")
                candidates = list(Path.cwd().rglob(f"{self.voice}.onnx"))
                if candidates:
                    model_file = candidates[0]
                    print(f"ℹ️  Piper model encontrado en: {model_file}")
                else:
                    print(f"⚠️  No se encontró {self.voice}.onnx al hacer rglob desde {Path.cwd()}")
            kwargs["model_path"] = str(model_file)
        elif self.engine_name == "coqui":
            kwargs["speaker_wav"] = kwargs.get("coqui_voice_wav") or kwargs.get("speaker_wav")

        try:
            self.engine.synthesize(text, str(output_file), **kwargs)
        except Exception as e:
            raise RuntimeError(f"TTS synthesis failed: {e}")

        if not output_file.exists():
            raise RuntimeError(f"TTS synthesis failed: {output_file} not created")
        return str(output_file)

    def synthesize_with_timestamps(self, text: str, output_path: Optional[str] = None, force_regenerate: bool = False, **kwargs) -> Dict[str, object]:
        """
        Sintetiza texto a voz con alineación temporal, compatible con ElevenLabsTTSService.
        Retorna diccionario con audio_path, letras y palabras con timestamps.
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Calcular rutas de caché
        cache_path = self._cacher.get_cache_path(text, self.engine.name, self.voice, ext=".wav")
        align_path = self._cacher.get_cache_path(text, self.engine.name, self.voice, extra="align", ext=".json")
        
        if output_path is None:
            output_path = str(cache_path)
        output_file = Path(output_path)
        align_file = Path(align_path)

        # Forzar regeneración si se solicita
        if force_regenerate:
            if output_file.exists():
                self._cacher.remove(output_file)
            if align_file.exists():
                self._cacher.remove(align_file)

        # Usar caché si existe
        if output_file.exists() and align_file.exists():
            try:
                with open(align_file, "r", encoding="utf-8") as f:
                    align_data = json.load(f)
                letras = [Letra(**d) for d in align_data.get("letras", [])]
                palabras = [Palabra(**d) for d in align_data.get("palabras", [])]
                return {"audio_path": str(output_file), "letras": letras, "palabras": palabras}
            except Exception:
                # Si hay error leyendo caché, regenerar
                pass

        # Generar audio
        print(f"🎵 Generando audio con {self.engine_name}...")
        audio_path = self.synthesize(text, str(output_file), force_regenerate, **kwargs)
        if not audio_path:
            return {"audio_path": None, "letras": [], "palabras": []}

        # Realizar alineación forzada
        print(f"⏱️ Realizando forced alignment con método {self.alignment_method}...")
        try:
            word_alignments, char_alignments = self.alignment_processor.align_text_audio(text, audio_path)
            if self.alignment_method == "whisper":
                palabras = [
                    Palabra(orden=i, palabra=w.word, timestamp_inicio=w.start_time, timestamp_fin=w.end_time)
                    for i, w in enumerate(word_alignments)
                ]
                letras = [
                    Letra(orden=i, letra=c.char, timestamp_inicio=c.start_time, timestamp_fin=c.end_time)
                    for i, c in enumerate(char_alignments)
                ]
            else:
                palabras = [
                    Palabra(orden=i, palabra=w[0], timestamp_inicio=w[1], timestamp_fin=w[2])
                    for i, w in enumerate(word_alignments)
                ]
                letras = [
                    Letra(orden=i, letra=c[0], timestamp_inicio=c[1], timestamp_fin=c[2])
                    for i, c in enumerate(char_alignments)
                ]

            # Guardar alineación en caché
            align_data = {
                "letras": [{"orden": l.orden, "letra": l.letra, "timestamp_inicio": l.timestamp_inicio, "timestamp_fin": l.timestamp_fin} for l in letras],
                "palabras": [{"orden": p.orden, "palabra": p.palabra, "timestamp_inicio": p.timestamp_inicio, "timestamp_fin": p.timestamp_fin} for p in palabras],
                "method": self.alignment_method
            }
            with open(align_file, "w", encoding="utf-8") as f:
                json.dump(align_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Alineación completada: {len(palabras)} palabras, {len(letras)} letras")
            return {"audio_path": audio_path, "letras": letras, "palabras": palabras}
        except Exception as e:
            print(f"❌ Error en alineación: {e}")
            # Fallback: retornar solo audio sin alineación
            return {"audio_path": audio_path, "letras": [], "palabras": []}

    def _get_audio_info(self, file_path: str):
        """Extract audio file information."""
        try:
            import librosa
            import soundfile as sf
        except ImportError:
            raise RuntimeError("Se requiere librosa y soundfile para obtener información del audio")
        
        from models.audio_info import AudioInfo
        
        file_path_obj = Path(file_path)
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        info = sf.info(file_path)
        
        return AudioInfo(
            file_path=file_path,
            duration=duration,
            sample_rate=int(sr),
            channels=info.channels,
            file_size=file_path_obj.stat().st_size
        )
