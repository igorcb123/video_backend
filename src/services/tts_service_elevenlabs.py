from dataclasses import dataclass
import base64
from typing import List, Dict, Optional
from pathlib import Path
from .tts_cacher import TTSCacher

# Nuevas entidades para alineación
@dataclass
class Letra:
    orden: int
    letra: str
    timestamp_inicio: float
    timestamp_fin: float

@dataclass
class Palabra:
    orden: int
    palabra: str
    timestamp_inicio: float
    timestamp_fin: float

import requests
from typing import Optional
import json

class ElevenLabsTTSService:
    def __init__(self, api_key: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL", cache_dir: Optional[Path] = None):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1"
        # Usar caché configurable o por defecto en temp/tts_cache
        if cache_dir is None:
            cache_dir = Path("temp/tts_cache")
        self._cacher = TTSCacher(cache_dir)

    def synthesize_with_timestamps(self, text: str, output_path: Optional[str] = None, model_id: str = "eleven_v3",
                                   stability: float = 0.5, similarity_boost: float = 0.85, output_format: str = "mp3_44100_128",
                                   force_regenerate: bool = False) -> Dict[str, object]:
        """
        Sintetiza texto a voz usando el endpoint with-timestamps de ElevenLabs y retorna audio y alineación.
        Usa caché local si está disponible, permite forzar regeneración.
        Guarda y reutiliza alineación (letras y palabras) en caché junto con el audio.
        """
        import json as _json
        # Calcular ruta de caché para audio y para alineación
        cache_path = self._cacher.get_cache_path(text, "elevenlabs", self.voice_id, extra=model_id+output_format, ext=".mp3")
        align_path = self._cacher.get_cache_path(text, "elevenlabs", self.voice_id, extra=model_id+output_format+"_align", ext=".json")
        if output_path is None:
            output_path = str(cache_path)
        output_file = Path(output_path)
        align_file = Path(align_path)

        # Forzar regeneración si se solicita
        if force_regenerate:
            if output_file.exists():
                self._cacher.remove(output_file)
            if align_file.exists():
                self._cacher.remove(align_file)

        # Usar caché si existe
        if output_file.exists() and align_file.exists():
            with open(align_file, "r", encoding="utf-8") as f:
                align_data = _json.load(f)
            # Reconstruir objetos Letra y Palabra
            letras = [Letra(**d) for d in align_data.get("letras", [])]
            palabras = [Palabra(**d) for d in align_data.get("palabras", [])]
            return {"audio_path": output_path, "letras": letras, "palabras": palabras}

        url = f"{self.base_url}/text-to-speech/{self.voice_id}/with-timestamps"
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
            "output_format": output_format
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            # Decodificar audio base64
            audio_b64 = data.get("audio_base64")
            audio_bytes = base64.b64decode(audio_b64)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            # Procesar alineación carácter a carácter
            letras = []
            alignment = data.get("alignment") or {}
            chars = alignment.get("characters", [])
            start_times = alignment.get("character_start_times_seconds", [])
            end_times = alignment.get("character_end_times_seconds", [])
            for i, (c, t0, t1) in enumerate(zip(chars, start_times, end_times)):
                letras.append(Letra(orden=i, letra=c, timestamp_inicio=t0, timestamp_fin=t1))

            # Procesar palabras usando los caracteres y tiempos
            palabras = []
            palabra_actual = ""
            t0_palabra = None
            orden_palabra = 0
            for i, (c, t0, t1) in enumerate(zip(chars, start_times, end_times)):
                if c.strip() == "":
                    if palabra_actual:
                        palabras.append(Palabra(orden=orden_palabra, palabra=palabra_actual, timestamp_inicio=t0_palabra, timestamp_fin=prev_t1))
                        orden_palabra += 1
                        palabra_actual = ""
                        t0_palabra = None
                else:
                    if palabra_actual == "":
                        t0_palabra = t0
                    palabra_actual += c
                    prev_t1 = t1
            # Añadir última palabra si existe
            if palabra_actual:
                palabras.append(Palabra(orden=orden_palabra, palabra=palabra_actual, timestamp_inicio=t0_palabra, timestamp_fin=prev_t1))

            # Guardar alineación en caché
            with open(align_file, "w", encoding="utf-8") as f:
                _json.dump({
                    "letras": [l.__dict__ for l in letras],
                    "palabras": [p.__dict__ for p in palabras]
                }, f, ensure_ascii=False)

            return {"audio_path": output_path, "letras": letras, "palabras": palabras}
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return {"audio_path": None, "letras": [], "palabras": []}
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

    def estimate_cost(self, text: str, model_id: str = "eleven_v3"):
        """Estima el costo en caracteres del texto."""
        character_count = len(text)
        print(f"=== ESTIMACIÓN DE COSTO ===")
        print(f"Texto a sintetizar: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"Número de caracteres: {character_count}")
        print(f"Modelo: {model_id}")
        print("=" * 30)
        return character_count

    def synthesize(self, text: str, output_path: Optional[str] = None, model_id: str = "eleven_v3",
                  stability: float = 0.45, similarity_boost: float = 0.85, language: str = "es",
                  force_regenerate: bool = False) -> Optional[str]:
        """
        Sintetiza texto a voz usando ElevenLabs, con caché local y opción de forzar regeneración.
        """
        # Calcular ruta de caché
        cache_path = self._cacher.get_cache_path(text, "elevenlabs", self.voice_id, extra=model_id, ext=".mp3")
        if output_path is None:
            output_path = str(cache_path)
        output_file = Path(output_path)

        # Forzar regeneración si se solicita
        if force_regenerate and output_file.exists():
            self._cacher.remove(output_file)

        # Usar caché si existe
        if output_file.exists():
            return str(output_file)

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