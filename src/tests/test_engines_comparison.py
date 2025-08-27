"""
Script para probar y comparar los dos engines TTS:
- tts_service.py (implementación original)
- tts_orchestrator.py (implementación factorizada)

Compara funcionalidad, rendimiento y compatibilidad de API.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_basic_synthesis(service_class, engine_name: str, test_text: str, output_dir: Path) -> Dict[str, Any]:
    """Prueba básica de síntesis de texto a voz."""
    print(f"\n🔧 Probando síntesis básica con {engine_name}...")
    
    try:
        # Inicializar servicio
        if engine_name in ["piper", "coqui"]:
            service = service_class(engine=engine_name)
        else:
            service = service_class()
        
        output_path = output_dir / f"test_basic_{engine_name}.wav"
        
        # Medir tiempo
        start_time = time.time()
        result = service.synthesize(
            text=test_text,
            output_path=str(output_path),
            force_regenerate=True
        )
        end_time = time.time()
        
        duration = end_time - start_time
        file_exists = Path(result).exists() if result else False
        file_size = Path(result).stat().st_size if file_exists else 0
        
        print(f"✅ Síntesis básica completada en {duration:.2f}s")
        print(f"   Archivo: {result}")
        print(f"   Tamaño: {file_size} bytes")
        
        return {
            "success": True,
            "duration": duration,
            "file_path": result,
            "file_size": file_size,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ Error en síntesis básica: {e}")
        return {
            "success": False,
            "duration": 0,
            "file_path": None,
            "file_size": 0,
            "error": str(e)
        }

def test_synthesis_with_timestamps(service_class, engine_name: str, test_text: str, output_dir: Path) -> Dict[str, Any]:
    """Prueba síntesis con alineación temporal."""
    print(f"\n⏱️  Probando síntesis con timestamps con {engine_name}...")
    
    try:
        # Inicializar servicio
        if engine_name in ["piper", "coqui"]:
            service = service_class(engine=engine_name)
        else:
            service = service_class()
        
        output_path = output_dir / f"test_timestamps_{engine_name}.wav"
        
        # Medir tiempo
        start_time = time.time()
        result = service.synthesize_with_timestamps(
            text=test_text,
            output_path=str(output_path),
            force_regenerate=True
        )
        end_time = time.time()
        
        duration = end_time - start_time
        audio_path = result.get("audio_path")
        letras = result.get("letras", [])
        palabras = result.get("palabras", [])
        
        file_exists = Path(audio_path).exists() if audio_path else False
        file_size = Path(audio_path).stat().st_size if file_exists else 0
        
        print(f"✅ Síntesis con timestamps completada en {duration:.2f}s")
        print(f"   Archivo: {audio_path}")
        print(f"   Tamaño: {file_size} bytes")
        print(f"   Palabras alineadas: {len(palabras)}")
        print(f"   Letras alineadas: {len(letras)}")
        
        return {
            "success": True,
            "duration": duration,
            "file_path": audio_path,
            "file_size": file_size,
            "words_count": len(palabras),
            "chars_count": len(letras),
            "error": None
        }
        
    except Exception as e:
        print(f"❌ Error en síntesis con timestamps: {e}")
        return {
            "success": False,
            "duration": 0,
            "file_path": None,
            "file_size": 0,
            "words_count": 0,
            "chars_count": 0,
            "error": str(e)
        }

def test_caching(service_class, engine_name: str, test_text: str, output_dir: Path) -> Dict[str, Any]:
    """Prueba funcionalidad de caché."""
    print(f"\n💾 Probando funcionalidad de caché con {engine_name}...")
    
    try:
        # Inicializar servicio
        if engine_name in ["piper", "coqui"]:
            service = service_class(engine=engine_name)
        else:
            service = service_class()
        
        output_path = output_dir / f"test_cache_{engine_name}.wav"
        
        # Primera síntesis (sin caché)
        start_time1 = time.time()
        result1 = service.synthesize(
            text=test_text,
            output_path=str(output_path),
            force_regenerate=True
        )
        end_time1 = time.time()
        duration1 = end_time1 - start_time1
        
        # Segunda síntesis (con caché)
        start_time2 = time.time()
        result2 = service.synthesize(
            text=test_text,
            output_path=str(output_path),
            force_regenerate=False
        )
        end_time2 = time.time()
        duration2 = end_time2 - start_time2
        
        cache_speedup = duration1 / duration2 if duration2 > 0 else 0
        
        print(f"✅ Prueba de caché completada")
        print(f"   Primera síntesis: {duration1:.2f}s")
        print(f"   Segunda síntesis (caché): {duration2:.2f}s")
        print(f"   Aceleración por caché: {cache_speedup:.1f}x")
        
        return {
            "success": True,
            "first_duration": duration1,
            "cached_duration": duration2,
            "speedup": cache_speedup,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ Error en prueba de caché: {e}")
        return {
            "success": False,
            "first_duration": 0,
            "cached_duration": 0,
            "speedup": 0,
            "error": str(e)
        }

def compare_engines():
    """Función principal de comparación de engines."""
    print("🔬 COMPARACIÓN DE ENGINES TTS")
    print("=" * 50)
    
    # Configuración de prueba
    test_text = "Hola, este es un texto de prueba para comparar los engines de síntesis de voz."
    output_dir = Path(__file__).parent / "temp_comparison"
    output_dir.mkdir(exist_ok=True)
    
    # Resultados
    results = {}
    
    try:
        # Importar servicios
        print("📦 Importando servicios...")
        from services.tts_service import TTSService as OriginalTTSService
        from services.tts_orchestrator import TTSService as OrchestratorTTSService
        print("✅ Servicios importados correctamente")
        
        # Motores a probar
        engines_to_test = []
        
        # Verificar qué motores están disponibles
        try:
            # Probar Piper
            service_piper = OriginalTTSService(engine="piper")
            engines_to_test.append(("piper", "Piper TTS"))
            print("✅ Piper TTS disponible")
        except Exception as e:
            print(f"⚠️  Piper TTS no disponible: {e}")
        
        try:
            # Probar Coqui (solo si torch está instalado)
            import torch
            service_coqui = OriginalTTSService(engine="coqui")
            engines_to_test.append(("coqui", "Coqui TTS"))
            print("✅ Coqui TTS disponible")
        except Exception as e:
            print(f"⚠️  Coqui TTS no disponible: {e}")
        
        if not engines_to_test:
            print("❌ No hay motores TTS disponibles para probar")
            return
        
        # Probar cada motor con ambas implementaciones
        for engine_name, engine_display in engines_to_test:
            print(f"\n🚀 PROBANDO {engine_display.upper()}")
            print("-" * 40)
            
            # Pruebas con implementación original
            print(f"📊 Implementación Original (tts_service.py)")
            original_results = {}
            original_results["basic"] = test_basic_synthesis(
                OriginalTTSService, engine_name, test_text, output_dir
            )
            original_results["timestamps"] = test_synthesis_with_timestamps(
                OriginalTTSService, engine_name, test_text, output_dir
            )
            original_results["caching"] = test_caching(
                OriginalTTSService, engine_name, test_text, output_dir
            )
            
            # Pruebas con implementación factorizada
            print(f"\n📊 Implementación Factorizada (tts_orchestrator.py)")
            orchestrator_results = {}
            orchestrator_results["basic"] = test_basic_synthesis(
                OrchestratorTTSService, engine_name, test_text, output_dir
            )
            orchestrator_results["timestamps"] = test_synthesis_with_timestamps(
                OrchestratorTTSService, engine_name, test_text, output_dir
            )
            orchestrator_results["caching"] = test_caching(
                OrchestratorTTSService, engine_name, test_text, output_dir
            )
            
            results[engine_name] = {
                "original": original_results,
                "orchestrator": orchestrator_results
            }
        
        # Generar reporte de comparación
        print("\n📋 REPORTE DE COMPARACIÓN")
        print("=" * 50)
        
        for engine_name, engine_results in results.items():
            print(f"\n🔧 {engine_name.upper()}")
            print("-" * 20)
            
            original = engine_results["original"]
            orchestrator = engine_results["orchestrator"]
            
            # Comparar síntesis básica
            if original["basic"]["success"] and orchestrator["basic"]["success"]:
                orig_time = original["basic"]["duration"]
                orch_time = orchestrator["basic"]["duration"]
                time_diff = ((orch_time - orig_time) / orig_time * 100) if orig_time > 0 else 0
                
                print(f"  Síntesis Básica:")
                print(f"    Original: {orig_time:.2f}s")
                print(f"    Factorizada: {orch_time:.2f}s")
                print(f"    Diferencia: {time_diff:+.1f}%")
            
            # Comparar síntesis con timestamps
            if original["timestamps"]["success"] and orchestrator["timestamps"]["success"]:
                orig_time = original["timestamps"]["duration"]
                orch_time = orchestrator["timestamps"]["duration"]
                time_diff = ((orch_time - orig_time) / orig_time * 100) if orig_time > 0 else 0
                
                orig_words = original["timestamps"]["words_count"]
                orch_words = orchestrator["timestamps"]["words_count"]
                
                print(f"  Síntesis con Timestamps:")
                print(f"    Original: {orig_time:.2f}s ({orig_words} palabras)")
                print(f"    Factorizada: {orch_time:.2f}s ({orch_words} palabras)")
                print(f"    Diferencia: {time_diff:+.1f}%")
            
            # Comparar caché
            if original["caching"]["success"] and orchestrator["caching"]["success"]:
                orig_speedup = original["caching"]["speedup"]
                orch_speedup = orchestrator["caching"]["speedup"]
                
                print(f"  Funcionalidad de Caché:")
                print(f"    Original: {orig_speedup:.1f}x aceleración")
                print(f"    Factorizada: {orch_speedup:.1f}x aceleración")
        
        # Guardar resultados detallados
        results_file = output_dir / "comparison_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 Resultados detallados guardados en: {results_file}")
        print("\n✅ Comparación completada exitosamente")
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Asegúrate de que los servicios estén disponibles")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_engines()
