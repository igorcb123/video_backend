from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
from services.tts_orchestrator import TTSService
from utils.audio import get_audio_info

try:
    tts = TTSService(engine='coqui')
    refs = 'models/tts/igor.wav'
    texts = [
        "El principio de la sabiduría es el temor de Jehová. (Proverbios 1:7)",
        "Hijo mío, no olvides mi ley, y tu corazón guarde mis mandamientos. (Proverbios 3:1)"
    ]
    for t in texts:
        print('\n--- Synthesizing:', t[:60], '...')
        audio_path = tts.synthesize(t, force_regenerate=True, speaker_wav=refs)
        info = get_audio_info(audio_path)
        print('Generated:', info.file_path)
        print('Duration:', f"{info.duration:.2f}s")
        print('Sample rate:', info.sample_rate)
        print('Size:', f"{info.file_size/1024:.1f}KB")
except Exception as e:
    print('Error during test:', e)
