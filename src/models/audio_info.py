from pydantic import BaseModel

class AudioInfo(BaseModel):
    """Audio file information."""
    file_path: str
    duration: float
    sample_rate: int
    channels: int
    file_size: int
