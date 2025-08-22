---
applyTo: "**"
---
# Python Backend - Video Generation System

## Code Standards
- Files: snake_case.py ≤250 lines
- Classes: PascalCase, Functions: snake_case, Constants: UPPER_SNAKE_CASE
- Type hints + Google docstrings mandatory
- Use: black, isort, flake8, mypy

## Directory Structure
src/
├── api/         # REST endpoints
├── config/      # Settings (pydantic-settings)
├── llm/         # Ollama integration
├── models/      # Domain entities (@dataclass)
├── repositories/# Data persistence
├── schemas/     # Pydantic models
├── services/    # Business logic
├── utils/       # Specialized processors
└── tests/       # pytest tests

## Video Generation Pipeline
Text → TTS_Local → STT_Local → Words+Timestamps → Sentences/Scenes/Subtitles → Video

## Core Models (src/models/)
@dataclass
class Palabra:
   orden: int; palabra: str; timestamp_inicio: float; timestamp_fin: float

@dataclass  
class Frase:
   orden: int; palabra_inicio: int; palabra_fin: int

@dataclass
class Escena:
   orden: int; frase_orden: int; palabra_inicio: int; palabra_fin: int; visual_focus: str

@dataclass
class Subtitulo:
   orden: int; frase_orden: int; palabra_inicio: int; palabra_fin: int; texto: str

class Proyecto:
   # Main container with palabras[], frases[], escenas[], subtitulos[]

## Services (src/services/) - Business Logic
# text_processing_service.py
class TextProcessingService:
   def process_text_to_words(texto: str) -> List[Palabra]  # Text→TTS→STT→Words
   def generate_sentences(palabras: List[Palabra]) -> List[Frase]
   def generate_scenes(frases: List[Frase]) -> List[Escena]  # Uses LLM
   def generate_subtitles(frases: List[Frase]) -> List[Subtitulo]

# tts_service.py - Local Text-to-Speech
class TTSService:
   def __init__(engine: "piper"|"coqui" = "piper")
   def synthesize_audio(texto: str, output_path: str) -> AudioInfo

# stt_service.py - Local Speech-to-Text  
class STTService:
   def __init__(engine: "whisper_cpp"|"vosk" = "whisper_cpp")
   def extract_word_timestamps(audio_path: str) -> List[WordTimestamp]
   def align_text_with_audio(texto: str, audio_path: str) -> List[Palabra]

# scene_generation_service.py
class SceneGenerationService:
   def generate_visual_descriptions(frases: List[Frase]) -> List[str]  # Uses Ollama

# subtitle_service.py
class SubtitleService:
   def generate_optimal_subtitles(frases, config) -> List[Subtitulo]
   def export_subtitles(subtitulos, format: "srt"|"vtt") -> str

# project_service.py
class ProjectService:
   def create_project_from_text(texto: str) -> Proyecto  # Full pipeline

## Utils (src/utils/) - Specialized Processors
# text_cleaner.py
class TextCleaner:
   def clean_for_tts(texto: str) -> str  # Numbers→words, optimize for TTS
   def normalize_punctuation(texto: str) -> str
   def remove_markup(texto: str) -> str

# sentence_splitter.py  
class SentenceSplitter:
   def split_by_punctuation(texto: str) -> List[str]  # Basic rules
   def split_by_semantic_breaks(texto: str) -> List[str]  # Uses spaCy
   def merge_short_sentences(frases: List[str]) -> List[str]

# timestamp_aligner.py
class TimestampAligner:
   def align_words_with_timestamps(palabras_texto, timestamps) -> List[Palabra]
   def smooth_timestamps(palabras: List[Palabra]) -> List[Palabra]
   def validate_timestamp_consistency(palabras) -> List[ValidationError]

# audio_processor.py
class AudioProcessor:
   def normalize_audio(audio_path: str) -> str  # Volume/quality for STT
   def extract_audio_info(audio_path: str) -> AudioInfo
   def trim_silence(audio_path: str) -> str

# subtitle_formatter.py
class SubtitleFormatter:
   def format_srt(subtitulos: List[Subtitulo]) -> str
   def format_vtt(subtitulos: List[Subtitulo]) -> str
   def optimize_line_breaks(texto: str, max_chars=42) -> str

# file_manager.py
class FileManager:
   def create_project_directory(project_id: int) -> Path
   def cleanup_temp_files(project_id: int) -> None
   def get_file_hash(file_path: str) -> str

## LLM Integration (src/llm/)
# scene_prompt_builder.py
class ScenePromptBuilder:
   def build_scene_description_prompt(frase_texto: str) -> str
   def build_scene_transition_prompt(escena_actual, escena_siguiente) -> str

# text_analyzer.py  
class TextAnalyzer:
   def extract_visual_elements(texto: str) -> List[str]  # Uses Ollama
   def determine_scene_mood(frase: str) -> str
   def suggest_scene_breaks(texto: str) -> List[int]

## Tech Stack (Local, No GPU)
# TTS: Piper (fast) - CONFIRMED STRATEGY
pip install piper-tts

# STT: Whisper.cpp (CPU optimized) - CONFIRMED STRATEGY
# Using small model (244MB) for optimal balance of speed/accuracy
# Provides word-level timestamps essential for video sync
pip install whisper-cpp-python
# Model auto-download: whisper-small.bin (~244MB)

# Text: spaCy small models, NLTK, regex
pip install spacy && python -m spacy download es_core_news_sm

# Audio: librosa, soundfile, pydub
pip install librosa soundfile pydub

## Environment Variables
TTS_ENGINE=piper          # CONFIRMED: piper only
TTS_MODEL_PATH=./models/tts/
STT_ENGINE=whisper_cpp    # CONFIRMED: whisper_cpp only
STT_MODEL=small           # CONFIRMED: small model (244MB, optimal balance)
STT_LANGUAGE=es           # Spanish language code
MAX_WORKERS=4             # Parallel processing
CACHE_ENABLED=true        # Reuse TTS/STT results

## Performance Optimizations
- Cache identical TTS/STT results using content hash
- Lazy load Whisper model (load once, reuse)
- Parallel processing for multiple audio files
- Use Whisper small model: fast + accurate + word timestamps
- Audio preprocessing: normalize volume/sample rate for STT
- Smart caching: same text = reuse previous TTS+STT results