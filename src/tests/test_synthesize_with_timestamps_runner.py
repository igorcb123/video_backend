#!/usr/bin/env python3
"""
Test-style runner para ejecutar y debugear `synthesize_with_timestamps` sin usar pytest.

Colócalo en `src/tests` y ejecútalo directamente con Python.

Ejemplos:
  python src/tests/test_synthesize_with_timestamps_runner.py --text "Hola mundo" --engine piper --dry-run
  python src/tests/test_synthesize_with_timestamps_runner.py --text "Hola" --engine coqui

No está diseñado para ser descubierto por pytest; es un script ejecutable de depuración.
"""
import argparse
import sys
import traceback
from pathlib import Path
import os


def main(argv=None):
    parser = argparse.ArgumentParser(description="Runner (no-pytest) para synthesize_with_timestamps")
    parser.add_argument("--text", "-t", required=True, help="Texto a sintetizar")
    parser.add_argument("--engine", "-e", choices=["piper", "coqui"], default="piper", help="Motor TTS a usar")
    parser.add_argument("--output", "-o", default=None, help="Ruta de salida para el audio (opcional)")
    parser.add_argument("--force", "-f", action="store_true", help="Forzar regeneración")
    parser.add_argument("--attach", "-a", action="store_true", help="Pausar antes de la llamada para adjuntar el depurador")
    parser.add_argument("--dry-run", action="store_true", help="No ejecuta la síntesis, solo valida argumentos y entorno")
    parser.add_argument("--model-path", default=None, help="Ruta al modelo Piper (.onnx) si se usa engine=piper")
    parser.add_argument("--speaker-wav", default=None, help="Ruta al audio de referencia si se usa engine=coqui")
    parser.add_argument("--play", "-p", action="store_true", help="Reproducir el audio generado automáticamente")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar información detallada de timestamps")

    args = parser.parse_args(argv)

    # Garantizar que el paquete src esté en sys.path
    # __file__ = .../src/tests/test_... -> parents[2] es la raíz del repo (donde está la carpeta `src`)
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    print("[runner] repo root:", repo_root)
    print("[runner] using src path:", src_path)

    if args.dry_run:
        print("[runner] DRY RUN: argumentos recibidos:")
        print(f"  text={args.text!r}\n  engine={args.engine}\n  output={args.output}\n  force={args.force}")
        print(f"  model_path={args.model_path}\n  speaker_wav={args.speaker_wav}")
        return 0

    # Auto-detectar rutas si no se proporcionan
    repo_root = Path(__file__).resolve().parents[2]
    models_dir = repo_root / "models" / "tts"
    
    if args.engine == "piper" and args.model_path is None:
        # Usar el primer modelo .onnx disponible
        onnx_files = list(models_dir.glob("*.onnx"))
        if onnx_files:
            args.model_path = str(onnx_files[0])
            print(f"[runner] Auto-detectado model_path para Piper: {args.model_path}")
        else:
            print("[runner] ERROR: No se encontraron modelos .onnx para Piper en models/tts/")
            return 2
    
    if args.engine == "coqui" and args.speaker_wav is None:
        # Usar archivo de referencia por defecto
        default_ref = models_dir / "igor-neutral.wav"
        if default_ref.exists():
            args.speaker_wav = str(default_ref)
            print(f"[runner] Auto-detectado speaker_wav para Coqui: {args.speaker_wav}")
        else:
            print("[runner] WARNING: No se encontró igor-neutral.wav, continuando sin referencia específica")

    # Import tardío para evitar depender de paquetes en dry-run
    try:
        from services.tts_orchestrator import TTSService
    except Exception:
        print("[runner] ERROR: no se pudo importar TTSService (revisa sys.path y dependencias)")
        traceback.print_exc()
        return 2

    service = TTSService(engine=args.engine)

    if args.attach:
        pid = os.getpid()
        print(f"[runner] PID {pid}: espera para adjuntar depurador. Presiona Enter para continuar...")
        input()

    try:
        # Preparar kwargs para el motor
        synthesis_kwargs = {}
        if args.engine == "piper" and args.model_path:
            synthesis_kwargs["model_path"] = args.model_path
        elif args.engine == "coqui" and args.speaker_wav:
            synthesis_kwargs["speaker_wav"] = args.speaker_wav
        
        result = service.synthesize_with_timestamps(args.text, output_path=args.output, force_regenerate=args.force, **synthesis_kwargs)
        print("[runner] Resultado obtenido:")
        audio = result.get("audio_path")
        letras = result.get("letras", [])
        palabras = result.get("palabras", [])
        print(f"  audio_path={audio}")
        print(f"  letras={len(letras)} items, palabras={len(palabras)} items")
        
        # Mostrar información detallada si se solicita
        if args.verbose:
            if palabras:
                print("\n  Palabras con timestamps:")
                for p in palabras[:10]:  # Mostrar primeras 10
                    inicio = getattr(p, 'timestamp_inicio', 0)
                    fin = getattr(p, 'timestamp_fin', 0)
                    palabra = getattr(p, 'palabra', '')
                    print(f"    [{inicio:.2f}-{fin:.2f}s] '{palabra}'")
                if len(palabras) > 10:
                    print(f"    ... y {len(palabras) - 10} más")
            
            if letras:
                print("\n  Primeras letras con timestamps:")
                for l in letras[:15]:  # Mostrar primeras 15
                    inicio = getattr(l, 'timestamp_inicio', 0)
                    fin = getattr(l, 'timestamp_fin', 0)
                    letra = getattr(l, 'letra', '')
                    print(f"    [{inicio:.2f}-{fin:.2f}s] '{letra}'")
                if len(letras) > 15:
                    print(f"    ... y {len(letras) - 15} más")
        else:
            # Resumen compacto
            if letras:
                print("  primeras letras:", [ (getattr(l, 'orden', None), getattr(l, 'letra', None)) for l in letras[:10] ])
            if palabras:
                print("  primeras palabras:", [ (getattr(p, 'orden', None), getattr(p, 'palabra', None)) for p in palabras[:10] ])
        
        # Reproducir audio si se solicita
        if args.play and audio and Path(audio).exists():
            print(f"\n[runner] Reproduciendo audio: {audio}")
            try:
                import subprocess
                if sys.platform == "win32":
                    subprocess.run(["start", "", audio], shell=True)
                elif sys.platform == "darwin":
                    subprocess.run(["open", audio])
                else:
                    subprocess.run(["xdg-open", audio])
            except Exception as e:
                print(f"[runner] Error reproduciendo audio: {e}")
        
        # Mostrar información del archivo generado
        if audio and Path(audio).exists():
            file_size = Path(audio).stat().st_size
            print(f"\n[runner] Archivo generado: {audio} ({file_size:,} bytes)")
        
        return 0
    except Exception:
        print("[runner] EXCEPCIÓN durante synthesize_with_timestamps:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
