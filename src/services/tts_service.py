"""Text-to-Speech service implementation."""

import hashlib
import subprocess
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel

try:
    from ..config.settings import settings
except ImportError:
    from config.settings import settings


class AudioInfo(BaseModel):
    """Audio file information."""
    
    file_path: str
    duration: float
    sample_rate: int
    channels: int
    file_size: int


class TTSService:
    """Local Text-to-Speech service using Piper."""
    
    def __init__(self, engine: Literal["piper", "coqui"] = "piper"):
        """Initialize TTS service.
        
        Args:
            engine: TTS engine to use
        """
        self.engine = engine
        self.model_path = settings.tts_model_path
        self.cache_enabled = settings.cache_enabled
        self._cache_dir = settings.temp_dir / "tts_cache"
        self._cache_dir.mkdir(exist_ok=True)
    
    def synthesize_audio(self, texto: str, output_path: Optional[str] = None) -> AudioInfo:
        """Synthesize text to audio.
        
        Args:
            texto: Text to synthesize
            output_path: Output file path (optional)
            
        Returns:
            AudioInfo with synthesis results
            
        Raises:
            RuntimeError: If synthesis fails
        """
        if not texto.strip():
            raise ValueError("Text cannot be empty")
            
        # Generate output path if not provided
        if output_path is None:
            text_hash = self._get_text_hash(texto)
            output_path = str(self._cache_dir / f"tts_{text_hash}.wav")
        
        output_file = Path(output_path)
        
        # Check cache first
        if self.cache_enabled and output_file.exists():
            return self._get_audio_info(str(output_file))
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Synthesize audio based on engine
        if self.engine == "piper":
            self._synthesize_with_piper(texto, str(output_file))
        elif self.engine == "coqui":
            self._synthesize_with_coqui(texto, str(output_file))
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")
        
        # Verify output file was created
        if not output_file.exists():
            raise RuntimeError(f"TTS synthesis failed: {output_file} not created")
            
        return self._get_audio_info(str(output_file))
    
    def _synthesize_with_piper(self, texto: str, output_path: str) -> None:
        """Synthesize using Piper TTS.
        
        Args:
            texto: Text to synthesize
            output_path: Output WAV file path
            
        Raises:
            RuntimeError: If Piper command fails
        """
        # Piper command: echo "text" | piper --model model.onnx --output_file output.wav
        model_file = self.model_path / f"{settings.tts_voice}.onnx"
        
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
                input=texto,
                text=True,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Piper synthesis failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("Piper not found. Install with: pip install piper-tts")
    
    def _synthesize_with_coqui(self, texto: str, output_path: str) -> None:
        """Synthesize using Coqui TTS.
        
        Args:
            texto: Text to synthesize  
            output_path: Output WAV file path
            
        Raises:
            RuntimeError: If Coqui synthesis fails
        """
        try:
            # This would use Coqui TTS library
            # Implementation depends on specific Coqui setup
            raise NotImplementedError("Coqui TTS integration pending")
        except Exception as e:
            raise RuntimeError(f"Coqui synthesis failed: {e}")
    
    def _get_text_hash(self, texto: str) -> str:
        """Generate hash for text caching.
        
        Args:
            texto: Input text
            
        Returns:
            MD5 hash string
        """
        content = f"{texto}_{self.engine}_{settings.tts_voice}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_audio_info(self, file_path: str) -> AudioInfo:
        """Extract audio file information.
        
        Args:
            file_path: Audio file path
            
        Returns:
            AudioInfo object
        """
        import librosa
        import soundfile as sf
        
        file_path_obj = Path(file_path)
        
        # Load audio to get duration and sample rate
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Get file info
        info = sf.info(file_path)
        
        return AudioInfo(
            file_path=file_path,
            duration=duration,
            sample_rate=int(sr),
            channels=info.channels,
            file_size=file_path_obj.stat().st_size
        )