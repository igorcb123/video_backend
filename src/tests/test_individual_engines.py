"""
Script simple para probar engines TTS individuales.
Permite probar rápidamente un engine específico con diferentes configuraciones.
"""

import os
import sys
import time
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_piper_engine():
    """Prueba específica del PiperEngine factorizado."""
    print("🔧 PROBANDO PIPER ENGINE FACTORIZADO")
    print("=" * 40)
    
    try:
        from services.engines.piper_engine import PiperEngine
        from config.settings import settings
        
        engine = PiperEngine()
        print(f"✅ PiperEngine inicializado: {engine.name}")
        
        # Configurar ruta del modelo
        model_file = settings.tts_model_path / f"{getattr(settings, 'tts_voice', 'default')}.onnx"
        output_path = Path(__file__).parent / "temp" / "test_piper_engine.wav"
        output_path.parent.mkdir(exist_ok=True)
        
        test_text = "Hola, este es un test del motor Piper factorizado."
        
        print(f"📝 Texto: {test_text}")
        print(f"🎯 Modelo: {model_file}")
        print(f"💾 Salida: {output_path}")
        
        if not model_file.exists():
            print(f"⚠️  Modelo no encontrado: {model_file}")
            print("   Configura el modelo en settings o coloca un archivo .onnx válido")
            return
        
        start_time = time.time()
        engine.synthesize(
            text=test_text,
            output_path=str(output_path),
            model_path=str(model_file)
        )
        end_time = time.time()
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"✅ Síntesis completada en {end_time - start_time:.2f}s")
            print(f"📄 Archivo generado: {file_size} bytes")
        else:
            print("❌ No se generó el archivo de audio")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_coqui_engine():
    """Prueba específica del CoquiEngine factorizado."""
    print("🎙️  PROBANDO COQUI ENGINE FACTORIZADO")
    print("=" * 40)
    
    try:
        from services.engines.coqui_engine import CoquiEngine
        
        engine = CoquiEngine()
        print(f"✅ CoquiEngine inicializado: {engine.name}")
        print(f"🔊 Voice cloning: {engine.supports_voice_cloning()}")
        
        output_path = Path(__file__).parent / "temp" / "test_coqui_engine.wav"
        output_path.parent.mkdir(exist_ok=True)
        
        test_text = "Hola, este es un test del motor Coqui con clonación de voz."
        
        print(f"📝 Texto: {test_text}")
        print(f"💾 Salida: {output_path}")
        
        start_time = time.time()
        engine.synthesize(
            text=test_text,
            output_path=str(output_path),
            language="es"
        )
        end_time = time.time()
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"✅ Síntesis completada en {end_time - start_time:.2f}s")
            print(f"📄 Archivo generado: {file_size} bytes")
        else:
            print("❌ No se generó el archivo de audio")
            
    except ImportError as e:
        print(f"❌ Dependencias faltantes: {e}")
        print("   Instala: pip install TTS torch librosa soundfile")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_orchestrator():
    """Prueba del TTSService orquestador."""
    print("🎭 PROBANDO TTS ORCHESTRATOR")
    print("=" * 40)
    
    try:
        from services.tts_orchestrator import TTSService
        
        # Probar con diferentes engines
        engines = ["piper", "coqui"]
        
        for engine_name in engines:
            print(f"\n🔧 Probando con engine: {engine_name}")
            try:
                service = TTSService(engine=engine_name)
                print(f"✅ TTSService inicializado con {engine_name}")
                
                output_path = Path(__file__).parent / "temp" / f"test_orchestrator_{engine_name}.wav"
                output_path.parent.mkdir(exist_ok=True)
                
                test_text = f"Test del orquestador TTS usando {engine_name}."
                
                # Prueba síntesis básica
                print(f"   🎵 Probando síntesis básica...")
                start_time = time.time()
                result = service.synthesize(
                    text=test_text,
                    output_path=str(output_path),
                    force_regenerate=True
                )
                end_time = time.time()
                
                if result and Path(result).exists():
                    file_size = Path(result).stat().st_size
                    print(f"   ✅ Básica OK: {end_time - start_time:.2f}s, {file_size} bytes")
                
                # Prueba síntesis con timestamps
                print(f"   ⏱️  Probando síntesis con timestamps...")
                start_time = time.time()
                result_ts = service.synthesize_with_timestamps(
                    text=test_text,
                    output_path=str(output_path).replace(".wav", "_ts.wav"),
                    force_regenerate=True
                )
                end_time = time.time()
                
                audio_path = result_ts.get("audio_path")
                palabras = len(result_ts.get("palabras", []))
                letras = len(result_ts.get("letras", []))
                
                if audio_path and Path(audio_path).exists():
                    print(f"   ✅ Timestamps OK: {end_time - start_time:.2f}s")
                    print(f"      Palabras: {palabras}, Letras: {letras}")
                
            except Exception as e:
                print(f"   ❌ Error con {engine_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Función principal del script de pruebas."""
    print("🧪 TEST DE ENGINES TTS FACTORIZADOS")
    print("=" * 50)
    
    # Crear directorio temporal
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    print("Selecciona qué probar:")
    print("1. PiperEngine (factorizado)")
    print("2. CoquiEngine (factorizado)")  
    print("3. TTSService Orchestrator")
    print("4. Todo lo anterior")
    print("0. Salir")
    
    try:
        choice = input("\nOpción (0-4): ").strip()
        
        if choice == "1":
            test_piper_engine()
        elif choice == "2":
            test_coqui_engine()
        elif choice == "3":
            test_orchestrator()
        elif choice == "4":
            test_piper_engine()
            print("\n" + "="*50)
            test_coqui_engine()
            print("\n" + "="*50)
            test_orchestrator()
        elif choice == "0":
            print("👋 ¡Hasta luego!")
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n👋 Cancelado por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
