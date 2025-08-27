#!/usr/bin/env python3
"""Quick test script for Coqui TTS service."""

import sys
from pathlib import Path

# Add src a sys.path para imports absolutos
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.tts_orchestrator import TTSService
from utils.audio import get_audio_info

def main():
    """Test TTS service with Coqui (XTTS v2, voice cloning)."""
    
    # Sample texts to test
    test_texts = [
        "El principio de la sabiduría es el temor de Jehová. (Proverbios 1:7)",
        "Hijo mío, no olvides mi ley, y tu corazón guarde mis mandamientos. (Proverbios 3:1)",
        "Sobre toda cosa guardada, guarda tu corazón; porque de él mana la vida. (Proverbios 4:23)"
    ]

    # Ruta al archivo de voz a clonar (puede ser mp3 o wav, debe existir)
    
    print("🎵 Initializing Coqui TTS service...")
    tts = TTSService(engine="coqui")

    for i, texto in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}: '{texto[:50]}...'")
        try:
            # Synthesize audio and get file path
            audio_path = tts.synthesize(texto)
            audio_info = get_audio_info(audio_path)
            print(f"✅ Success!")
            print(f"   📁 File: {audio_info.file_path}")
            print(f"   ⏱️  Duration: {audio_info.duration:.2f}s")
            print(f"   🔊 Sample Rate: {audio_info.sample_rate}Hz")
            print(f"   💾 Size: {audio_info.file_size / 1024:.1f}KB")
            # Optionally, test alignment info
            alignment = tts.synthesize_with_timestamps(texto,force_regenerate=True)
            print(f"   ⏲️ Alignment: {len(alignment.get('palabras', []))} palabras, {len(alignment.get('letras', []))} letras")
            import pathlib
            print("   🔗 Link to audio file:", pathlib.Path(audio_info.file_path).as_uri())
        except Exception as e:
            print(f"❌ Error: {e}")
    print("\n🎯 Coqui TTS testing complete!")
    print("💡 Next steps:")
    print("   1. Check generated audio files in temp/tts_cache/")
    print("   2. Play audio files to verify quality")
    print("   3. Test with longer texts")

if __name__ == "__main__":
    main()
