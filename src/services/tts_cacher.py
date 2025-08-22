import hashlib
from pathlib import Path
from typing import Optional

class TTSCacher:
    """
    Utilidad para gestionar caché de archivos de audio TTS.
    """
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, text: str, engine: str, voice: str, extra: Optional[str] = None, ext: str = ".wav") -> Path:
        """
        Calcula la ruta de caché para un texto y parámetros dados.
        """
        key = f"{text}_{engine}_{voice}"
        if extra:
            key += f"_{extra}"
        hash_str = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"tts_{hash_str}{ext}"

    def exists(self, cache_path: Path) -> bool:
        return cache_path.exists()

    def remove(self, cache_path: Path):
        if cache_path.exists():
            cache_path.unlink()

    def ensure_dir(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
