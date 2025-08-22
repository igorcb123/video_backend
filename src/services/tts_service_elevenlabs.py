import requests
from typing import Optional
import json

class ElevenLabsTTSService:
    """
    Servicio TTS usando la API de ElevenLabs con debugging mejorado.
    """
    def __init__(self, api_key: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1"

    def check_subscription_info(self):
        """Verifica información de la suscripción y créditos disponibles."""
        url = f"{self.base_url}/user/subscription"
        headers = {
            "xi-api-key": self.api_key,
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("=== INFORMACIÓN DE SUSCRIPCIÓN ===")
            print(f"Tier: {data.get('tier', 'N/A')}")
            print(f"Character count: {data.get('character_count', 0)}")
            print(f"Character limit: {data.get('character_limit', 0)}")
            print(f"Can extend character limit: {data.get('can_extend_character_limit', False)}")
            print(f"Allowed to extend character limit: {data.get('allowed_to_extend_character_limit', False)}")
            print(f"Next character count reset unix: {data.get('next_character_count_reset_unix', 'N/A')}")
            print("=" * 40)
            return data
        else:
            print(f"Error obteniendo info de suscripción: {response.status_code} - {response.text}")
            return None

    def get_user_info(self):
        """Obtiene información del usuario."""
        url = f"{self.base_url}/user"
        headers = {
            "xi-api-key": self.api_key,
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("=== INFORMACIÓN DE USUARIO ===")
            print(f"User ID: {data.get('user_id', 'N/A')}")
            
            subscription = data.get('subscription', {})
            print(f"Tier: {subscription.get('tier', 'N/A')}")
            print(f"Character count: {subscription.get('character_count', 0)}")
            print(f"Character limit: {subscription.get('character_limit', 0)}")
            print(f"Status: {subscription.get('status', 'N/A')}")
            print("=" * 35)
            return data
        else:
            print(f"Error obteniendo info de usuario: {response.status_code} - {response.text}")
            return None

    def estimate_cost(self, text: str, model_id: str = "eleven_monolingual_v1"):
        """Estima el costo en caracteres del texto."""
        character_count = len(text)
        print(f"=== ESTIMACIÓN DE COSTO ===")
        print(f"Texto a sintetizar: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"Número de caracteres: {character_count}")
        print(f"Modelo: {model_id}")
        print("=" * 30)
        return character_count

    def synthesize(self, text: str, output_path: str, model_id: str = "eleven_monolingual_v1",
                  stability: float = 0.5, similarity_boost: float = 0.5, language: str = "es") -> Optional[str]:
        
        # Debug: Verificar información antes de sintetizar
        print("Verificando información de cuenta antes de sintetizar...")
        self.get_user_info()
        self.check_subscription_info()
        self.estimate_cost(text, model_id)
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            },
            "output_format": "mp3",
            "response_format": "audio",
            # Nota: 'lang' podría no ser un parámetro válido para todos los modelos
        }
        
        print(f"=== REQUEST INFO ===")
        print(f"URL: {url}")
        print(f"Voice ID: {self.voice_id}")
        print(f"Model ID: {model_id}")
        print("=" * 20)
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"=== RESPONSE INFO ===")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Audio generado exitosamente: {output_path}")
            return output_path
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
            # Intenta parsear el error como JSON para más detalles
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    detail = error_data['detail']
                    print(f"Detalles del error:")
                    print(f"  - Status: {detail.get('status', 'N/A')}")
                    print(f"  - Message: {detail.get('message', 'N/A')}")
            except:
                print("No se pudo parsear el error como JSON")
            
            return None