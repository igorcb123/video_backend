import sys
from pathlib import Path
# Añadir el directorio raíz del proyecto al sys.path
import os
# Ensure the project's `src` directory is on sys.path so imports like
# `from services...` inside modules resolve correctly when running this script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Provide a minimal dummy `torch` module when running tests locally where torch
# may not be installed. The real code only checks `torch.cuda.is_available()`.
try:
    import torch  # type: ignore
except Exception:
    import types as _types
    import sys as _sys
    torch = _types.ModuleType("torch")
    cuda_mod = _types.ModuleType("torch.cuda")
    def _is_available():
        return False
    cuda_mod.is_available = _is_available
    torch.cuda = cuda_mod
    _sys.modules["torch"] = torch
# Create a minimal fake `config.settings` module so we don't need pydantic
# or other heavy dependencies when running this lightweight test locally.
import types as _types
from pathlib import Path as _Path

_config_mod = _types.ModuleType("config.settings")

class _DummySettings:
    def __init__(self):
        self.tts_model_path = _Path("./models/tts/")
        self.cache_enabled = True
        self.tts_voice = "es_MX-ald-medium"
        self.temp_dir = _Path("./temp/")

_config_mod.settings = _DummySettings()
import sys as _sys
_sys.modules["config.settings"] = _config_mod
_sys.modules["config"] = _types.ModuleType("config")
_sys.modules["config"].settings = _config_mod.settings

from services.tts_service import TTSService
from services.forced_alignment import WhisperAlignmentProcessor

import time

def main():
    """
    Ejecuta synthesize_with_timestamps y muestra resultados relevantes, tiempos y paths de caché.
    """
    texto = "Porque de tal manera amo Dios al mundo, que ha dado a su Hijo unigenito, para que todo aquel que en el cree, no se pierda, mas tenga vida eterna."
    print("🎵 Test de TTS con timestamps")
    print("=" * 50)
    print("Texto a sintetizar:", texto)
    print("=" * 50)

    try:
        # Crear el servicio TTS usando el motor piper y la voz disponible
        tts = TTSService(engine="piper")
        tts.voice = "es_MX-ald-medium"  # Usar modelo disponible
        
        # El alignment processor se inicializa automáticamente en TTSService
        print(f"🔧 Método de alineación: {tts.alignment_method}")
        print(f"🎯 Motor TTS: {tts.engine}")
        print(f"🎤 Voz: {tts.voice}")

        # Carpeta de caché
        cache_dir = tts._cacher.cache_dir
        print(f"📁 Directorio de caché: {cache_dir}")

        # Definir la ruta de salida para el audio
        ruta_audio = Path(cache_dir) / "demo_tts.wav"

        # Medir tiempo de ejecución
        inicio = time.time()
        resultado = tts.synthesize_with_timestamps(
            texto,
            output_path=str(ruta_audio),
            force_regenerate=True
        )
        fin = time.time()

        print(f"\nTiempo total de ejecución: {fin-inicio:.2f} segundos")
        
        audio_path = resultado.get('audio_path')
        print(f"\nRuta del audio generado: {audio_path}")
        
        # Verificar que el archivo de audio existe
        if audio_path and Path(audio_path).exists():
            audio_size = Path(audio_path).stat().st_size
            print(f"✅ Archivo de audio creado exitosamente ({audio_size / 1024:.1f}KB)")
        else:
            print("❌ Error: No se pudo crear el archivo de audio")

        # Buscar archivo de alineación en caché
        align_path = tts._cacher.get_cache_path(texto, tts.engine, tts.voice, extra="align", ext=".json")
        print(f"Ruta del archivo de alineación (timestamps): {align_path}")
        
        # Verificar que el archivo de alineación existe
        if Path(align_path).exists():
            align_size = Path(align_path).stat().st_size
            print(f"✅ Archivo de alineación creado exitosamente ({align_size / 1024:.1f}KB)")
        else:
            print("❌ Archivo de alineación no encontrado")

        # Mostrar resumen de palabras y letras
        palabras = resultado.get("palabras", [])
        letras = resultado.get("letras", [])
        print(f"\n📊 Resultados de alineación:")
        print(f"   Palabras detectadas: {len(palabras)}")
        print(f"   Letras detectadas: {len(letras)}")
        
        if palabras:
            print(f"\n🔤 Primeras 3 palabras:")
            for i, palabra in enumerate(palabras[:3], 1):
                print(f"   {i}. '{palabra.palabra}' [{palabra.timestamp_inicio:.3f}s - {palabra.timestamp_fin:.3f}s]")
        
        if letras:
            print(f"\n🔠 Primeras 5 letras:")
            for i, letra in enumerate(letras[:5], 1):
                print(f"   {i}. '{letra.letra}' [{letra.timestamp_inicio:.3f}s - {letra.timestamp_fin:.3f}s]")
    
        print(f"\n🎉 Test completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
