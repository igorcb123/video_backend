
"""
Módulo para forced alignment usando Whisper.
Extrae timestamps de palabras y caracteres desde audio y texto.
"""

import json
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class WordAlignment:
    word: str
    start_time: float
    end_time: float

@dataclass
class CharAlignment:
    char: str
    start_time: float
    end_time: float

class WhisperAlignmentProcessor:
    """Procesa forced alignment usando Whisper."""
    def __init__(self, model_name: str = "base", device: str = "cpu"):
        import whisper
        self.model = whisper.load_model(model_name, device=device)

    def align_text_audio(self, text: str, audio_path: str, language: str = "es") -> Tuple[List[WordAlignment], List[CharAlignment]]:
        """
        Realiza forced alignment entre texto y audio usando Whisper.
        Retorna alineación de palabras y caracteres.
        """
        import whisper
        # Transcribir el audio
        result = self.model.transcribe(audio_path, language=language, word_timestamps=True, verbose=False)
        # Extraer alineación de palabras
        word_alignments = []
        for segment in result["segments"]:
            for word_info in segment.get("words", []):
                word = word_info["word"].strip()
                start_time = float(word_info["start"])
                end_time = float(word_info["end"])
                word_alignments.append(WordAlignment(word, start_time, end_time))
        # Extraer alineación de caracteres interpolando desde palabras
        char_alignments = self._interpolate_char_alignment(text, word_alignments)
        return word_alignments, char_alignments

    def _interpolate_char_alignment(self, text: str, word_alignments: List[WordAlignment]) -> List[CharAlignment]:
        char_alignments = []
        text_pos = 0
        for word_align in word_alignments:
            word = word_align.word
            word_duration = word_align.end_time - word_align.start_time
            word_start_pos = text.find(word, text_pos)
            if word_start_pos == -1:
                continue
            # Procesar caracteres antes de la palabra (espacios, puntuación)
            for i in range(text_pos, word_start_pos):
                char = text[i]
                char_alignments.append(CharAlignment(char, word_align.start_time, word_align.start_time))
            # Procesar caracteres de la palabra
            for i, char in enumerate(word):
                char_progress = i / len(word) if len(word) > 1 else 0
                char_start = word_align.start_time + (char_progress * word_duration)
                char_end = word_align.start_time + ((i + 1) / len(word) * word_duration)
                char_alignments.append(CharAlignment(char, char_start, char_end))
            text_pos = word_start_pos + len(word)
        # Procesar caracteres restantes
        if text_pos < len(text):
            last_time = word_alignments[-1].end_time if word_alignments else 0.0
            for i in range(text_pos, len(text)):
                char = text[i]
                char_alignments.append(CharAlignment(char, last_time, last_time))
        return char_alignments

class SimpleAlignmentProcessor:
    """
    Procesador de alineación simple como fallback cuando Whisper no está disponible.
    Distribuye uniformemente el tiempo basándose en la duración del audio.
    """
    def align_text_audio(self, text: str, audio_path: str, language: str = "es") -> Tuple[List[WordAlignment], List[CharAlignment]]:
        try:
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
                    word_alignments.append(WordAlignment(word, start_time, end_time))
            char_alignments = []
            if text:
                time_per_char = duration / len(text)
                for i, char in enumerate(text):
                    start_time = i * time_per_char
                    end_time = (i + 1) * time_per_char
                    char_alignments.append(CharAlignment(char, start_time, end_time))
            return word_alignments, char_alignments
        except Exception as e:
            raise RuntimeError(f"Error en alineación simple: {e}")