#!/usr/bin/env python3
"""Test script to verify multiple reference handling in Coqui TTS service."""

import sys
from pathlib import Path

# Add src to sys.path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.tts_service import TTSService

def main():
    """Test TTS service with different reference combinations."""
    
    test_text = "Hola, esta es una prueba de clonación de voz con múltiples referencias."
    
    print("🎵 Initializing Coqui TTS service...")
    tts = TTSService(engine="coqui")
    
    # Test 1: Default references only (no custom speaker_wav)
    print("\n📝 Test 1: Usando solo referencias por defecto")
    try:
        audio_path = tts.synthesize(test_text, output_path="temp/test_default_refs.wav", force_regenerate=True)
        audio_info = tts._get_audio_info(audio_path)
        print(f"✅ Success! Duration: {audio_info.duration:.2f}s, Size: {audio_info.file_size / 1024:.1f}KB")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Custom single reference (should combine with defaults)  
    print("\n📝 Test 2: Usando referencia personalizada (single file)")
    custom_ref = str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-sorpresa.wav")
    if Path(custom_ref).exists():
        try:
            audio_path = tts.synthesize(
                test_text, 
                output_path="temp/test_custom_single_ref.wav", 
                force_regenerate=True,
                coqui_voice_wav=custom_ref
            )
            audio_info = tts._get_audio_info(audio_path)
            print(f"✅ Success! Duration: {audio_info.duration:.2f}s, Size: {audio_info.file_size / 1024:.1f}KB")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"⚠️  Archivo de referencia no encontrado: {custom_ref}")
    
    # Test 3: Custom multiple references
    print("\n📝 Test 3: Usando múltiples referencias personalizadas")
    custom_refs = [
        str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-sorpresa.wav"),
        str(Path(__file__).parent.parent.parent / "models" / "tts" / "igor-tristeza.wav"),
    ]
    existing_refs = [ref for ref in custom_refs if Path(ref).exists()]
    
    if existing_refs:
        try:
            audio_path = tts.synthesize(
                test_text, 
                output_path="temp/test_custom_multi_refs.wav", 
                force_regenerate=True,
                coqui_voice_wav=existing_refs
            )
            audio_info = tts._get_audio_info(audio_path)
            print(f"✅ Success! Duration: {audio_info.duration:.2f}s, Size: {audio_info.file_size / 1024:.1f}KB")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⚠️  No se encontraron referencias personalizadas válidas")
    
    # Test 4: Non-existent reference (should fallback to defaults)
    print("\n📝 Test 4: Referencia inexistente (fallback a defaults)")
    try:
        audio_path = tts.synthesize(
            test_text, 
            output_path="temp/test_fallback_refs.wav", 
            force_regenerate=True,
            coqui_voice_wav="nonexistent_file.wav"
        )
        audio_info = tts._get_audio_info(audio_path)
        print(f"✅ Success! Duration: {audio_info.duration:.2f}s, Size: {audio_info.file_size / 1024:.1f}KB")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n🎯 Multiple references testing complete!")
    print("💡 Los archivos de audio generados están en temp/ para comparar calidad")

if __name__ == "__main__":
    main()
