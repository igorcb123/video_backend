#!/usr/bin/env python3
"""Test script for utils integration."""

import sys
from pathlib import Path

# Add src to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.text_cleaner import TextCleaner
from utils.audio_processor import AudioProcessor
from services.tts_service import TTSService


def test_text_cleaner_integration():
    """Test text cleaner with real examples."""
    print("🧹 Testing TextCleaner...")
    
    cleaner = TextCleaner()
    
    test_cases = [
        "Hola, tengo 25 años y nací en 2024.",
        "El Dr. García dice que son las 3:30 PM.",
        "<p>Texto con **HTML** y markdown</p>",
        "¡¿Esto funciona bien??? ¡Increíble!",
        "   Texto   con    espacios    múltiples   ",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}:")
        print(f"   Input:  '{text}'")
        
        result = cleaner.clean_for_tts(text)
        print(f"   Output: '{result}'")
        
        # Basic validation
        assert isinstance(result, str)
        assert len(result.strip()) > 0 or len(text.strip()) == 0
    
    print("\n✅ TextCleaner tests passed!")


def test_audio_processor_integration():
    """Test audio processor configuration."""
    print("\n🎵 Testing AudioProcessor...")
    
    # Test processor initialization
    processor = AudioProcessor(target_sample_rate=16000)
    print(f"   ✓ Initialized with target sample rate: {processor.target_sample_rate}Hz")
    
    # Test temp directory creation
    assert processor.temp_dir.exists()
    print(f"   ✓ Temp directory created: {processor.temp_dir}")
    
    # Test different sample rates
    processor_22k = AudioProcessor(target_sample_rate=22050)
    assert processor_22k.target_sample_rate == 22050
    print(f"   ✓ Custom sample rate: {processor_22k.target_sample_rate}Hz")
    
    print("✅ AudioProcessor tests passed!")


def test_pipeline_integration():
    """Test text and audio processing pipeline simulation."""
    print("\n🔗 Testing Pipeline Integration...")
    
    # Simulate the TTS pipeline
    raw_text = """
    <h1>Bienvenido al sistema</h1>
    
    El Dr. López tiene 35 años.
    Nació en 1988 y trabaja desde las 9:00 AM.
    
    **¡Excelente trabajo!** ¿No te parece increíble???
    """
    
    # Step 1: Clean text for TTS
    cleaner = TextCleaner()
    clean_text = cleaner.clean_for_tts(raw_text)
    
    print("📝 Text Processing:")
    print(f"   Raw text length: {len(raw_text)} chars")
    print(f"   Clean text length: {len(clean_text)} chars")
    print(f"   Cleaned: '{clean_text[:100]}...' ")
    
    # Verify cleaning worked
    assert "<h1>" not in clean_text
    assert "Dr." in clean_text
    
    # Step 2: Prepare audio processor (for future TTS output)
    processor = AudioProcessor(target_sample_rate=16000)
    print(f"\n🎵 Audio Processing Ready:")
    print(f"   Target sample rate: {processor.target_sample_rate}Hz")
    print(f"   Temp directory: {processor.temp_dir}")
    
    # Step 3: Synthesize audio using Piper TTS
    tts_service = TTSService(engine="piper")
    audio_info = tts_service.synthesize_audio(clean_text)

    print("\n🔊 TTS Synthesis:")
    print(f"   File: {audio_info.file_path}")
    print(f"   Duration: {audio_info.duration:.2f}s")
    print(f"   Sample Rate: {audio_info.sample_rate}Hz")
    print(f"   Size: {audio_info.file_size / 1024:.1f}KB")

    # Verify audio details
    assert audio_info.duration > 0, "Audio duration should be greater than 0"
    assert audio_info.sample_rate == processor.target_sample_rate, "Sample rate mismatch"
    assert audio_info.file_size > 0, "Audio file size should be greater than 0"

    # Ensure audio file exists
    audio_file = Path(audio_info.file_path)
    assert audio_file.exists(), f"Audio file not found: {audio_info.file_path}"
    assert audio_file.is_file(), f"Expected a file but found something else: {audio_info.file_path}"

    print("   ✓ Audio file verified successfully")

    print("\n✅ Pipeline integration test passed!")
    
    return clean_text, processor


def main():
    """Run all integration tests."""
    print("🚀 Starting Utils Integration Tests...\n")
    
    try:
        # Test individual components
        test_text_cleaner_integration()
        test_audio_processor_integration()
        
        # Test integrated pipeline
        clean_text, processor = test_pipeline_integration()
        
        print("\n🎉 All integration tests passed!")
        print("\n📋 Summary:")
        print(f"   ✅ TextCleaner: Ready for TTS optimization")
        print(f"   ✅ AudioProcessor: Ready for STT preprocessing")
        print(f"   ✅ Pipeline: Text → TTS → STT flow ready")
        
        print("\n🔮 Next Steps:")
        print("   1. Implement STTService with Whisper.cpp")
        print("   2. Create TextProcessingService orchestrator")
        print("   3. Build end-to-end pipeline tests")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
