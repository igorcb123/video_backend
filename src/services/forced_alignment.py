"""
Módulo para forced alignment usando Aeneas.
Extrae timestamps de palabras y caracteres desde audio y texto.
"""

import tempfile
import json
from pathlib import Path
from typing import List, Tuple, Optional
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

class ForcedAlignmentProcessor:
    """Procesa forced alignment usando Aeneas."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "tts_alignment"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def align_text_audio(self, text: str, audio_path: str, language: str = "es") -> Tuple[List[WordAlignment], List[CharAlignment]]:
        """
        Realiza forced alignment entre texto y audio.
        Retorna alineación de palabras y caracteres.
        """
        try:
            from aeneas.executetask import ExecuteTask
            from aeneas.task import Task
            import uuid
            
            # Generar archivos temporales únicos
            task_id = str(uuid.uuid4())[:8]
            text_file = self.temp_dir / f"text_{task_id}.txt"
            config_file = self.temp_dir / f"config_{task_id}.json"
            map_file = self.temp_dir / f"map_{task_id}.json"
            

            # Escribir texto: una sola línea (alineación por frase)
            with open(text_file, "w", encoding="utf-8") as f:
                for word in text.strip().split():
                    f.write(word + "\n")
            # Verificar existencia y contenido del archivo antes de ejecutar aeneas
            if text_file.exists():
                print(f"[Aeneas DEBUG] El archivo de texto existe: {text_file}")
                with open(text_file, "r", encoding="utf-8") as f:
                    print(f"[Aeneas DEBUG] Contenido real: '{f.read()}'")
            else:
                print(f"[Aeneas DEBUG] El archivo de texto NO existe: {text_file}")
            # Verificar existencia y contenido del archivo antes de ejecutar aeneas
            if text_file.exists():
                print(f"[Aeneas DEBUG] El archivo de texto existe: {text_file}")
                with open(text_file, "r", encoding="utf-8") as f:
                    print(f"[Aeneas DEBUG] Contenido real: '{f.read()}'")
            else:
                print(f"[Aeneas DEBUG] El archivo de texto NO existe: {text_file}")
            # Depuración: imprimir el contenido del archivo de texto
            with open(text_file, "r", encoding="utf-8") as f:
                print(f"[Aeneas DEBUG] Contenido archivo texto: '{f.read()}'")

            # Configuración de Aeneas como string
            # Usar 'spa' como código de idioma para español (ISO 639-2)
            lang_code = 'spa' if language in ('es', 'spa', 'es-ES') else language
            config_string = f"task_language={lang_code}|os_task_file_format=json|task_text_file_format=plain"

            # Ejecutar alineación
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = audio_path
            task.text_file_path_absolute = str(text_file)
            task.sync_map_file_path_absolute = str(map_file)

            ExecuteTask(task).execute()
            
            # Leer resultados
            with open(map_file, "r", encoding="utf-8") as f:
                alignment_data = json.load(f)
            
            # Procesar palabras
            word_alignments = []
            for fragment in alignment_data["fragments"]:
                word = fragment["lines"][0].strip()
                start_time = float(fragment["begin"])
                end_time = float(fragment["end"])
                if word:  # Ignorar fragmentos vacíos
                    word_alignments.append(WordAlignment(word, start_time, end_time))
            
            # Generar alineación de caracteres interpolando desde palabras
            char_alignments = self._interpolate_char_alignment(text, word_alignments)
            
            # Limpiar archivos temporales
            for temp_file in [text_file, config_file, map_file]:
                if temp_file.exists():
                    temp_file.unlink()
            
            return word_alignments, char_alignments
            
        except ImportError:
            raise RuntimeError("Aeneas no está instalado. Instala con: pip install aeneas")
        except Exception as e:
            raise RuntimeError(f"Error en forced alignment: {e}")
    
    def _interpolate_char_alignment(self, text: str, word_alignments: List[WordAlignment]) -> List[CharAlignment]:
        """
        Interpola timestamps de caracteres basándose en la alineación de palabras.
        """
        char_alignments = []
        text_pos = 0
        
        for word_align in word_alignments:
            word = word_align.word
            word_duration = word_align.end_time - word_align.start_time
            
            # Encontrar la palabra en el texto original
            word_start_pos = text.find(word, text_pos)
            if word_start_pos == -1:
                continue  # Palabra no encontrada, saltar
            
            # Procesar caracteres antes de la palabra (espacios, puntuación)
            for i in range(text_pos, word_start_pos):
                char = text[i]
                # Asignar timestamp del inicio de la palabra
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
    Procesador de alineación simple como fallback cuando Aeneas no está disponible.
    Distribuye uniformemente el tiempo basándose en la duración del audio.
    """
    
    def align_text_audio(self, text: str, audio_path: str, language: str = "es") -> Tuple[List[WordAlignment], List[CharAlignment]]:
        """Alineación simple basada en duración uniforme."""
        try:
            import librosa
            
            # Obtener duración del audio
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Dividir texto en palabras
            words = text.split()
            word_alignments = []
            
            if words:
                time_per_word = duration / len(words)
                for i, word in enumerate(words):
                    start_time = i * time_per_word
                    end_time = (i + 1) * time_per_word
                    word_alignments.append(WordAlignment(word, start_time, end_time))
            
            # Generar alineación de caracteres
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