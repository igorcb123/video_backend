from typing import List, Tuple
import librosa

class SimpleProcessor:
    """
    Procesador simple de alineación como fallback.
    """

    def align_text_audio(self, text: str, audio_path: str, language: str = "es") -> Tuple[List[Tuple[str, float, float]], List[Tuple[str, float, float]]]:
        """
        Realiza una alineación simple entre texto y audio.

        Args:
            text (str): Texto a alinear.
            audio_path (str): Ruta del archivo de audio.
            language (str): Idioma del texto (no utilizado en este procesador).

        Returns:
            Tuple[List[Tuple[str, float, float]], List[Tuple[str, float, float]]]:
                Alineaciones de palabras y caracteres.
        """
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
