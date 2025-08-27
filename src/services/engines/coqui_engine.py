import os
import tempfile
import torch
from pathlib import Path
from typing import Union, List, Optional
from services.engines.base_engine import BaseTTSEngine

class CoquiEngine(BaseTTSEngine):
    """
    Implementación del motor TTS para Coqui con voice cloning avanzado.
    """

    def synthesize(self, text: str, output_path: str, **kwargs) -> None:
        """
        Genera un archivo de audio usando Coqui TTS (XTTS v2, voice cloning).
        Soporta múltiples referencias para mejor clonación de voz.

        Args:
            text (str): Texto a sintetizar.
            output_path (str): Ruta donde se guardará el archivo generado.
            **kwargs: Parámetros específicos de Coqui.

        Raises:
            RuntimeError: Si ocurre un error durante la síntesis.
        """
        try:
            from TTS.api import TTS
        except ImportError:
            raise RuntimeError("TTS library not found. Install with: pip install TTS")
        try:
            import librosa
            import soundfile as sf
        except ImportError:
            raise RuntimeError("Se requiere librosa y soundfile para procesar el audio. Instala con: pip install librosa soundfile")

        # Configurar torch para permitir carga de modelos Coqui TTS (PyTorch 2.6+)
        os.environ.setdefault('TORCH_SERIALIZATION_WEIGHTS_ONLY', 'False')

        # Configurar modelo y parámetros
        model_name = kwargs.get("model_name", "tts_models/multilingual/multi-dataset/xtts_v2")
        speaker_wav = kwargs.get("speaker_wav")
        language = kwargs.get("language", "es")
        speed = kwargs.get("speed", 1.0)
        temperature = kwargs.get("temperature", 0.85)
        repetition_penalty = kwargs.get("repetition_penalty", 1.1)

        # Construir lista de referencias optimizada
        reference_files = self._build_reference_list(speaker_wav)
        
        print(f"🎙️  Usando {len(reference_files)} archivos de referencia para voice cloning")
        for i, ref_file in enumerate(reference_files[:3], 1):
            print(f"    {i}. {Path(ref_file).name}")
        if len(reference_files) > 3:
            print(f"    ... y {len(reference_files) - 3} más")

        use_gpu = torch.cuda.is_available()
        tts = TTS(model_name=model_name, progress_bar=False, gpu=use_gpu)

        try:
            tts.tts_to_file(
                text=text,
                speaker_wav=reference_files,
                file_path=output_path,
                language=language,
                speed=speed,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
            )
        except Exception as e:
            raise RuntimeError(f"Coqui synthesis failed: {e}")
        
        # Cleanup temporal files if any were created
        for ref_file in reference_files:
            if ref_file.startswith(tempfile.gettempdir()) and Path(ref_file).exists():
                try:
                    os.unlink(ref_file)
                except OSError:
                    pass

    def _prepare_speaker_wav(self, input_path: str) -> str:
        """Prepara un archivo de audio para voice cloning optimizado: 24kHz, mono, PCM_16, max 6s."""
        import librosa
        import soundfile as sf
        
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

    def _build_reference_list(self, speaker_wav: Union[str, List[str], None]) -> List[str]:
        """Construye y procesa la lista de archivos de referencia para voice cloning."""
        # Archivos de referencia por defecto (voces de Igor con diferentes emociones)
        default_references = [
            str(Path(__file__).parent.parent.parent.parent / "models" / "tts" / "igor-neutral.wav"),
            str(Path(__file__).parent.parent.parent.parent / "models" / "tts" / "igor-calma.wav"),
            str(Path(__file__).parent.parent.parent.parent / "models" / "tts" / "igor-alegria.wav"),
            str(Path(__file__).parent.parent.parent.parent / "models" / "tts" / "igor-pensativo.wav"),
            str(Path(__file__).parent.parent.parent.parent / "models" / "tts" / "igor-enojo.wav"),
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
                processed_wav = self._prepare_speaker_wav(speaker_wav)
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
                    processed_wav = self._prepare_speaker_wav(wav_path)
                    processed_wavs.append(processed_wav)
                else:
                    print(f"⚠️  Archivo de referencia no encontrado: {wav_path}, omitiendo")
            
            # Combinar archivos procesados con algunos por defecto
            if processed_wavs:
                return processed_wavs + existing_defaults[:max(0, 3 - len(processed_wavs))]
            else:
                print("⚠️  Ningún archivo de referencia válido encontrado, usando referencias por defecto")
                return existing_defaults
        
        return existing_defaults

    @property
    def name(self) -> str:
        return "coqui"

    def supports_voice_cloning(self) -> bool:
        """Coqui soporta clonación de voz."""
        return True
