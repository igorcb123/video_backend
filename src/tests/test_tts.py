#!/usr/bin/env python3
"""Quick test script for TTS service."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.tts_service import TTSService


def main():
    """Test TTS service with sample text."""
    
    # Sample texts to test
    test_texts = [
        "Hola, este es un test del sistema de síntesis de voz.",
        "Los números 123 y fechas como 2024 deberían pronunciarse correctamente.",
        "¿Funciona bien la pronunciación de signos de interrogación?"
    ]
    
    # Initialize TTS service
    print("🎵 Initializing TTS service...")
    tts = TTSService(engine="piper")
    
    # Test each text
    for i, texto in enumerate(test_texts, 1):
        print(f"\n📝 Test {i}: '{texto[:50]}...'")
        
        try:
            # Synthesize audio
            audio_info = tts.synthesize_audio(texto)
            
            print(f"✅ Success!")
            print(f"   📁 File: {audio_info.file_path}")
            print(f"   ⏱️  Duration: {audio_info.duration:.2f}s")
            print(f"   🔊 Sample Rate: {audio_info.sample_rate}Hz")
            print(f"   💾 Size: {audio_info.file_size / 1024:.1f}KB")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎯 TTS testing complete!")
    print("💡 Next steps:")
    print("   1. Check generated audio files in temp/tts_cache/")
    print("   2. Play audio files to verify quality")
    print("   3. Test with longer texts")


if __name__ == "__main__":
    main()