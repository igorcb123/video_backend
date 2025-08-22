
import os
import tempfile
import sys
from pathlib import Path
# Add src a sys.path para imports absolutos
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.tts_service_elevenlabs import ElevenLabsTTSService

def test_elevenlabs_tts_with_debug():
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    
    if not api_key:
        print("❌ ERROR: Debes definir la variable de entorno ELEVENLABS_API_KEY")
        return
        
    print(f"🔑 Usando API Key: {api_key[:10]}...{api_key[-4:]}")  # Muestra solo parte de la key por seguridad
    
    voice_id = "ODrAZ5do9kWmKe8ZDNRB"  # Voz proporcionada por el usuario
    tts = ElevenLabsTTSService(api_key=api_key, voice_id=voice_id)
    
    # Primero, solo verificamos la información de la cuenta
    print("\n🔍 VERIFICANDO INFORMACIÓN DE CUENTA...")
    user_info = tts.get_user_info()
    subscription_info = tts.check_subscription_info()
    
    if not user_info or not subscription_info:
        print("❌ No se pudo obtener información de la cuenta. Verifica tu API key.")
        return
    
    # Texto más corto para la prueba
    text = "[curious] ¿Sabías que, aun en medio de la oscuridad, la voz de la fe sigue viva? [excited] La Palabra dice: *“Levántate y resplandece, porque ha venido tu luz, y la gloria de Jehová ha nacido sobre ti”* (Isaías 60:1)."
    print(f"\n📝 Texto a sintetizar: '{text}'")
    estimated_characters = tts.estimate_cost(text)
    
    # Verificar si tenemos suficientes créditos
    available_characters = subscription_info.get('character_limit', 0) - subscription_info.get('character_count', 0)
    print(f"💳 Caracteres disponibles: {available_characters}")
    print(f"💰 Caracteres necesarios: {estimated_characters}")
    
    if available_characters < estimated_characters:
        print(f"❌ ADVERTENCIA: No tienes suficientes caracteres disponibles")
        print(f"   Disponibles: {available_characters}")
        print(f"   Necesarios: {estimated_characters}")
        return
    
    # Si llegamos aquí, intentamos sintetizar
    print(f"\n🎵 INTENTANDO SINTETIZAR...")
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        output_path = tmp.name
    
    result = tts.synthesize(text, output_path, model_id="eleven_v3",
                            similarity_boost=0.8
                            )
    
    if result is not None:
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ ÉXITO: Audio generado en {output_path}")
            print(f"📁 Tamaño del archivo: {file_size} bytes")
        else:
            print(f"❌ ERROR: El archivo no fue creado aunque la API respondió OK")
    else:
        print(f"❌ ERROR: La síntesis falló")
def test_elevenlabs_synthesize_with_timestamps():
    import os
    import tempfile
    from services.tts_service_elevenlabs import ElevenLabsTTSService

    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("❌ ERROR: Debes definir la variable de entorno ELEVENLABS_API_KEY")
        return

    voice_id = "ODrAZ5do9kWmKe8ZDNRB"  # Cambia por una voz válida si es necesario
    tts = ElevenLabsTTSService(api_key=api_key, voice_id=voice_id)
    text = "Hola mundo, esto es una prueba de alineación de letras y palabras."

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        output_path = tmp.name

    result = tts.synthesize_with_timestamps(text, output_path, model_id="eleven_v3", similarity_boost=0.8)

    assert result["audio_path"] is not None and os.path.exists(result["audio_path"]), "No se generó el archivo de audio"
    assert len(result["letras"]) > 0, "No se obtuvieron letras"
    assert len(result["palabras"]) > 0, "No se obtuvieron palabras"
    print("✅ Prueba de synthesize_with_timestamps exitosa")

if __name__ == "__main__":
    test_elevenlabs_synthesize_with_timestamps()