"""Text-to-Speech service implementation with timestamp alignment."""

import subprocess
import json
from pathlib import Path
from typing import Literal, Optional, Dict, List
from pydantic import BaseModel
from dataclasses import dataclass

try:
    from ..config.settings import settings
except ImportError:
    from config.settings import settings
from .tts_cacher import TTSCacher

try:
    from .forced_alignment import WhisperAlignmentProcessor, SimpleAlignmentProcessor
except ImportError:
    WhisperAlignmentProcessor = None
    SimpleAlignmentProcessor = None

# Entidades para alineación (compatibles con ElevenLabs)
@dataclass
class Letra:
    orden: int
    letra: str
    timestamp_inicio: float
    timestamp_fin: float

@dataclass
class Palabra:
    orden: int
    palabra: str
    timestamp_inicio: float
    timestamp_fin: float

class AudioInfo(BaseModel):
    """Audio file information."""
    
    file_path: str
    duration: float
    sample_rate: int
    channels: int
    file_size: int

class TTSService:
    """Local Text-to-Speech service con forced alignment, API compatible con ElevenLabsTTSService."""
    
    def __init__(self, engine: Literal["piper", "coqui"] = "piper"):
        self.engine = engine
        self.model_path = settings.tts_model_path
        self.cache_enabled = settings.cache_enabled
        self.voice = getattr(settings, "tts_voice", "default")
        self._cacher = TTSCacher(settings.temp_dir / "tts_cache")
        
        # Inicializar procesador de alineación
        self._init_alignment_processor()

    def _init_alignment_processor(self):
        """Inicializa el procesador de alineación forzada."""
        try:
            if WhisperAlignmentProcessor:
                self.alignment_processor = WhisperAlignmentProcessor(model_name="base", device="cpu")
                self.alignment_method = "whisper"
            else:
                self.alignment_processor = self._create_simple_processor()
                self.alignment_method = "simple"
        except Exception:
            self.alignment_processor = self._create_simple_processor()
            self.alignment_method = "simple"

    def _create_simple_processor(self):
        """Crea un procesador simple de alineación como fallback."""
        class SimpleProcessor:
            def align_text_audio(self, text: str, audio_path: str, language: str = "es"):
                import librosa
                y, sr = librosa.load(audio_path, sr=None)
                duration = librosa.get_duration(y=y, sr=sr)
                
                words = text.split()
                word_alignments = []
                if words:
                    time_per_word = duration / len(words)
                    for i, word in enumerate(words):
                        start_time = i * time_per_word
                        end_time = (i + 1) * time_per_word
                        word_alignments.append((word, start_time, end_time))
                
                char_alignments = []
                if text:
                    time_per_char = duration / len(text)
                    for i, char in enumerate(text):
                        start_time = i * time_per_char
                        end_time = (i + 1) * time_per_char
                        char_alignments.append((char, start_time, end_time))
                
                return word_alignments, char_alignments
        
        return SimpleProcessor()

    def synthesize(self, text: str, output_path: Optional[str] = None, force_regenerate: bool = False, **kwargs) -> Optional[str]:
        """
        Sintetiza texto a voz localmente, con caché y opción de forzar regeneración.
        Devuelve la ruta al archivo generado.
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        cache_path = self._cacher.get_cache_path(text, self.engine, self.voice, ext=".wav")
        if output_path is None:
            output_path = str(cache_path)
        output_file = Path(output_path)

        if force_regenerate and output_file.exists():
            self._cacher.remove(output_file)

        if self.cache_enabled and output_file.exists():
            return str(output_file)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        if self.engine == "piper":
            self._synthesize_with_piper(text, str(output_file))
        elif self.engine == "coqui":
            self._synthesize_with_coqui(text, str(output_file))
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")

        if not output_file.exists():
            raise RuntimeError(f"TTS synthesis failed: {output_file} not created")
        return str(output_file)

    def synthesize_with_timestamps(self, text: str, output_path: Optional[str] = None, 
                                 force_regenerate: bool = False, **kwargs) -> Dict[str, object]:
        """
        Sintetiza texto a voz con alineación temporal, compatible con ElevenLabsTTSService.
        Retorna diccionario con audio_path, letras y palabras con timestamps.
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Calcular rutas de caché
        cache_path = self._cacher.get_cache_path(text, self.engine, self.voice, ext=".wav")
        align_path = self._cacher.get_cache_path(text, self.engine, self.voice, extra="align", ext=".json")
        
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
        print(f"🎵 Generando audio con {self.engine}...")
        audio_path = self.synthesize(text, str(output_file), force_regenerate)
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
    
    def _synthesize_with_piper(self, text: str, output_path: str) -> None:
        """Synthesize using Piper TTS."""
        model_file = self.model_path / f"{self.voice}.onnx"
        if not model_file.exists():
            raise FileNotFoundError(f"Piper model not found: {model_file}")
        cmd = [
            "piper",
            "--model", str(model_file),
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
            raise RuntimeError(f"Piper synthesis failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Piper not found. Install with: pip install piper-tts")
    
    def _synthesize_with_coqui(self, text: str, output_path: str) -> None:
        """Synthesize using Coqui TTS."""
        try:
            raise NotImplementedError("Coqui TTS integration pending")
        except Exception as e:
            raise RuntimeError(f"Coqui synthesis failed: {e}")
    
    def _get_audio_info(self, file_path: str) -> AudioInfo:
        """Extract audio file information."""
        import librosa
        import soundfile as sf
        
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