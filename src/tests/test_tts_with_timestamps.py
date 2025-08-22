
import sys
from pathlib import Path
import pytest
# Añadir el directorio raíz del proyecto al sys.path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.services.tts_service import TTSService


import time

def main():
    """
    Ejecuta synthesize_with_timestamps y muestra resultados relevantes, tiempos y paths de caché.
    """
    texto = "This is a test sentence.\nHere is another line for alignment."
    print("Texto a sintetizar:", texto)

    # Crear el servicio TTS usando el motor piper y la voz disponible
    tts = TTSService(engine="piper")
    tts.voice = "es_ES-davefx-medium"  # Aseguramos que el modelo existe
    # Usar alineación avanzada con aeneas
    from src.services.forced_alignment import ForcedAlignmentProcessor
    tts.alignment_method = "aeneas"
    tts.alignment_processor = ForcedAlignmentProcessor()

    # Carpeta de caché
    cache_dir = tts._cacher.cache_dir
    print(f"Directorio de caché: {cache_dir}")

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
    print(f"\nRuta del audio generado: {resultado.get('audio_path')}")

    # Buscar archivo de alineación en caché
    align_path = tts._cacher.get_cache_path(texto, tts.engine, tts.voice, extra="align", ext=".json")
    print(f"Ruta del archivo de alineación (timestamps): {align_path}")

    # Mostrar resumen de palabras y letras
    palabras = resultado.get("palabras", [])
    letras = resultado.get("letras", [])
    print(f"\nPalabras detectadas: {len(palabras)}")
    if palabras:
        print("Primera palabra:", vars(palabras[0]))
    print(f"Letras detectadas: {len(letras)}")
    if letras:
        print("Primera letra:", vars(letras[0]))

if __name__ == "__main__":
    main()
