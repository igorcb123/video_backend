# Test Runner para synthesize_with_timestamps

El archivo `test_synthesize_with_timestamps_runner.py` es un runner independiente (no usa pytest) para probar la funcionalidad `synthesize_with_timestamps` del sistema TTS.

## Uso básico

```powershell
# Desde la raíz del proyecto
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Hola mundo" --engine coqui
```

## Opciones disponibles

- `--text, -t`: Texto a sintetizar (requerido)
- `--engine, -e`: Motor TTS (`piper` o `coqui`, default: `piper`)
- `--output, -o`: Ruta de salida personalizada (opcional)
- `--force, -f`: Forzar regeneración (ignora cache)
- `--verbose, -v`: Mostrar timestamps detallados
- `--play, -p`: Reproducir audio automáticamente
- `--attach, -a`: Pausar para adjuntar depurador
- `--dry-run`: Solo validar argumentos (no ejecuta síntesis)
- `--model-path`: Ruta al modelo Piper (.onnx)
- `--speaker-wav`: Audio de referencia para Coqui

## Ejemplos

```powershell
# Prueba básica con Coqui (recomendado)
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Hola mundo" --engine coqui

# Con información detallada de timestamps
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Texto largo para análisis" --engine coqui --verbose

# Con reproducción automática
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Reproducir inmediatamente" --engine coqui --play

# Forzar regeneración
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Regenerar cache" --engine coqui --force

# Solo validar configuración
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Test" --dry-run
```

## Notas

- **Coqui TTS** funciona mejor que Piper (que requiere instalación adicional)
- Los modelos y audios de referencia se auto-detectan desde `models/tts/`
- Los archivos generados se guardan en `temp/tts_cache/`
- El runner maneja automáticamente las rutas y dependencias del proyecto

## Debugging

Para debugear con VS Code:
1. Ejecuta con `--attach`
2. Cuando se pause, adjunta el depurador al PID mostrado
3. Presiona Enter para continuar

```powershell
python .\src\tests\test_synthesize_with_timestamps_runner.py --text "Debug test" --engine coqui --attach
```
