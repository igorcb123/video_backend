from TTS.api import TTS

# Cargar el modelo multilingüe que soporta voice cloning
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True, gpu=False)

# Texto a sintetizar
texto = "Por qué las personas dudan?"

# Ruta al archivo WAV del hablante (voz a clonar)
sp = "igor.wav"  # Asegúrate de que exista y tenga el formato correcto

# Ruta de salida del audio generado
salida = "output.wav"

# Ejecutar TTS con voice cloning
tts.tts_to_file(
    text=texto,
    speaker_wav=sp,
    file_path=salida,
    language="es"
)


print("✅ Audio generado en:", salida)
