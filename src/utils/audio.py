from pathlib import Path
from models.audio_info import AudioInfo
import librosa
import soundfile as sf

def get_audio_info(file_path: str) -> AudioInfo:
    """
    Extrae información de un archivo de audio.

    Args:
        file_path (str): Ruta del archivo de audio.

    Returns:
        AudioInfo: Información del archivo de audio.
    """
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
