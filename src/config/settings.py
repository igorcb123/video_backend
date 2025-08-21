"""Configuration settings for video generation system."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # TTS Configuration
    tts_engine: Literal["piper", "coqui"] = Field(default="piper", description="TTS engine")
    tts_model_path: Path = Field(default=Path("./models/tts/"), description="TTS models directory")
    tts_voice: str = Field(default="es_ES-davefx-medium", description="Default TTS voice")
    
    # STT Configuration  
    stt_engine: Literal["whisper_cpp", "vosk"] = Field(default="whisper_cpp", description="STT engine")
    stt_model: Literal["tiny", "base", "small", "medium"] = Field(default="small", description="Whisper model size")
    stt_model_path: Path = Field(default=Path("./models/stt/"), description="STT models directory")
    
    # Processing Configuration
    max_workers: int = Field(default=4, description="Max parallel workers")
    cache_enabled: bool = Field(default=True, description="Enable result caching")
    temp_dir: Path = Field(default=Path("./temp/"), description="Temporary files directory")
    
    # Audio Configuration
    sample_rate: int = Field(default=22050, description="Audio sample rate")
    audio_format: Literal["wav", "mp3"] = Field(default="wav", description="Audio format")
    
    # LLM Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="llama3.1", description="Default LLM model")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")

    def __post_init__(self):
        """Create required directories."""
        for path in [self.tts_model_path, self.stt_model_path, self.temp_dir]:
            path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()