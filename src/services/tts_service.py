"""Text-to-Speech service implementation with timestamp alignment."""

import subprocess
import json
from pathlib import Path
from typing import Literal, Optional, Dict, List, Union
from services.tts_cacher import TTSCacher
# Shared models for TTS alignment and audio info
import torch  # GPU availability
from models.letra import Letra
from models.palabra import Palabra
from models.audio_info import AudioInfo

from config.settings import settings
# TTSCacher already imported above

try:
    from services.forced_alignment import WhisperAlignmentProcessor, SimpleAlignmentProcessor
except ImportError:
    WhisperAlignmentProcessor = None
    SimpleAlignmentProcessor = None


class TTSService:
    """Local Text-to-Speech service con forced alignment, API compatible con ElevenLabsTTSService."""
    
    def __init__(self, engine: Literal["piper", "coqui"] = "piper"):
        # Para cachear el último speaker_wav procesado
        self._last_speaker_wav_path = None
        self._last_speaker_wav_src = None
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

        # Extraer parámetro para Coqui si se proporciona
        coqui_voice_wav = kwargs.get("coqui_voice_wav")
        if self.engine == "piper":
            self._synthesize_with_piper(text, str(output_file))
        elif self.engine == "coqui":
            self._synthesize_with_coqui(text, str(output_file), coqui_voice_wav)
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
    
    def _synthesize_with_coqui(
        self,
        text: str,
        output_path: str,
        speaker_wav: Union[str, List[str], None] = None,
        speaker_id: Optional[str] = "igor_cache",
        temperature: float = 0.85,
        repetition_penalty: float = 1.1,
        speed: float = 1.0,
        split_sentences: Optional[bool] = None,
        language: str = "es",
    ) -> None:
        """Synthesize using Coqui TTS (XTTS v2, voice cloning). Soporta múltiples referencias para mejor clonación de voz."""
        
        try:
            from TTS.api import TTS
        except ImportError:
            raise RuntimeError("TTS library not found. Install with: pip install TTS")
        try:
            import librosa
            import soundfile as sf
        except ImportError:
            raise RuntimeError("Se requiere librosa y soundfile para procesar el audio. Instala con: pip install librosa soundfile")
        import tempfile
        
        # Configurar torch para permitir carga de modelos Coqui TTS (PyTorch 2.6+)
        import os
        # Temporal fix para PyTorch 2.6: deshabilitar weights_only por defecto para TTS
        os.environ.setdefault('TORCH_SERIALIZATION_WEIGHTS_ONLY', 'False')

        # Modelo multilingüe con voice cloning
        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"

        # Helper function to prepare speaker wav files for optimal voice cloning
        def prepare_speaker_wav(input_path: str) -> str:
            """Prepara un archivo de audio para voice cloning optimizado: 24kHz, mono, PCM_16, max 6s."""
            y, sr = librosa.load(input_path, sr=24000, mono=True)
            max_sec = 6.0
            # Usar los últimos 6 segundos para mejor calidad
            if librosa.get_duration(y=y, sr=sr) > max_sec:
                start_sample = int((librosa.get_duration(y=y, sr=sr) - max_sec) * sr)
                y = y[start_sample:]
            
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(tmp_wav.name, y, sr, subtype="PCM_16")
            tmp_wav.close()
            return tmp_wav.name

        # Helper function to build and process reference list
        def build_reference_list(speaker_wav: Union[str, List[str], None]) -> List[str]:
            """Construye y procesa la lista de archivos de referencia para voice cloning."""
            # Archivos de referencia por defecto (voces de Igor con diferentes emociones)
            default_references = [
                str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-neutral.wav"),
                str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-calma.wav"),
                str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-alegria.wav"),
                str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-pensativo.wav"),
                str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-enojo.wav"),
            ]
            
            # Filtrar referencias por defecto que existen
            existing_defaults = [p for p in default_references if Path(p).exists()]
            
            # Si no se proporciona speaker_wav, usar referencias por defecto
            if speaker_wav is None:
                return existing_defaults
            
            # Procesar speaker_wav proporcionado
            if isinstance(speaker_wav, str):
                # Un solo archivo de referencia
                if Path(speaker_wav).exists():
                    processed_wav = prepare_speaker_wav(speaker_wav)
                    # Combinar con las referencias por defecto para mejor clonación
                    return [processed_wav] + existing_defaults[:2]  # Archivo principal + 2 refs por defecto
                else:
                    print(f"⚠️  Archivo de referencia no encontrado: {speaker_wav}, usando referencias por defecto")
                    return existing_defaults
            elif isinstance(speaker_wav, list):
                # Múltiples archivos de referencia
                processed_wavs = []
                for wav_path in speaker_wav:
                    if Path(wav_path).exists():
                        processed_wavs.append(prepare_speaker_wav(wav_path))
                    else:
                        print(f"⚠️  Archivo de referencia no encontrado: {wav_path}")
                
                if processed_wavs:
                    # Combinar archivos procesados con algunas referencias por defecto
                    return processed_wavs + existing_defaults[:2]
                else:
                    print("⚠️  Ningún archivo de referencia válido encontrado, usando referencias por defecto")
                    return existing_defaults
            
            return existing_defaults

        # Construir lista de referencias optimizada
        reference_files = build_reference_list(speaker_wav)
        
        print(f"🎙️  Usando {len(reference_files)} archivos de referencia para voice cloning")
        for i, ref_file in enumerate(reference_files[:3], 1):  # Mostrar solo los primeros 3
            print(f"   {i}. {Path(ref_file).name}")
        if len(reference_files) > 3:
            print(f"   ... y {len(reference_files) - 3} más")

        use_gpu = torch.cuda.is_available()
        tts = TTS(model_name=model_name, progress_bar=False, gpu=use_gpu)
        try:
            # Usar múltiples referencias para mejor voice cloning
            tts.tts_to_file(
                text=text,
                speaker_wav=reference_files,  # Lista de múltiples referencias
                file_path=output_path,
                language=language,
                speed=speed,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                split_sentences=split_sentences,
            )
        except Exception as e:
            raise RuntimeError(f"Coqui synthesis failed: {e}")
        
        # Cleanup temporal files if any were created
        for ref_file in reference_files:
            if "tmp" in ref_file and Path(ref_file).exists():
                try:
                    Path(ref_file).unlink()
                except Exception:
                    pass
    
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