"""
Ejemplo de búsqueda comparativa entre Google Images y Pexels
Busca imágenes basadas en descripciones en inglés y muestra URLs de resultados
"""

import os
from pathlib import Path
from services.media_fetcher_orchestrator import MediaFetcherService


def search_comparison_demo(description: str, num_results: int = 5):
    """
    Compara resultados de búsqueda entre Google Images y Pexels
    
    Args:
        description: Descripción en inglés de la imagen a buscar
        num_results: Número de resultados a mostrar por proveedor
    """
    print("🔍 DEMO: Búsqueda Comparativa Google vs Pexels")
    print("=" * 60)
    print(f"Descripción: '{description}'")
    print(f"Resultados por proveedor: {num_results}")
    print()
    
    results = {}
    
    # ========================================
    # BÚSQUEDA EN PEXELS
    # ========================================
    print("📸 BUSCANDO EN PEXELS...")
    print("-" * 30)
    
    pexels_available = bool(os.getenv("PEXELS_API_KEY"))
    
    if pexels_available:
        try:
            pexels_service = MediaFetcherService(provider="pexels")
            print("✅ Servicio Pexels inicializado")
            
            pexels_result = pexels_service.search_images(description, per_page=num_results)
            results["pexels"] = pexels_result.items
            
            print(f"🎯 Pexels encontró: {len(pexels_result.items)} imágenes")
            print(f"📊 Total disponible: {pexels_result.total_results}")
            print()
            
            if pexels_result.items:
                print("🔗 URLs de Pexels:")
                for i, item in enumerate(pexels_result.items, 1):
                    print(f"  {i}. {item.title or 'Sin título'}")
                    print(f"     📏 Tamaño: {item.width}x{item.height}")
                    print(f"     👤 Fotógrafo: {item.photographer or 'Desconocido'}")
                    print(f"     🌐 Página: {item.url}")
                    print(f"     ⬇️ Descarga: {item.download_url}")
                    print(f"     🏷️ Tags: {', '.join(item.tags) if item.tags else 'Sin tags'}")
                    print()
            else:
                print("❌ No se encontraron imágenes en Pexels")
                
        except Exception as e:
            print(f"❌ Error en Pexels: {e}")
            results["pexels"] = []
    else:
        print("⚠️ API key de Pexels no disponible")
        print("💡 Set PEXELS_API_KEY environment variable")
        results["pexels"] = []
    
    print()
    
    # ========================================
    # BÚSQUEDA EN GOOGLE IMAGES
    # ========================================
    print("🌐 BUSCANDO EN GOOGLE IMAGES...")
    print("-" * 30)
    
    try:
        google_service = MediaFetcherService(provider="google")
        print("✅ Servicio Google inicializado")
        
        # Búsqueda con filtros para mejores resultados
        google_result = google_service.search_images(
            description, 
            per_page=num_results,
            size="large",  # Preferir imágenes grandes
            image_type="photo"  # Preferir fotos
        )
        results["google"] = google_result.items
        
        print(f"🎯 Google encontró: {len(google_result.items)} imágenes")
        print()
        
        if google_result.items:
            print("🔗 URLs de Google:")
            for i, item in enumerate(google_result.items, 1):
                # Determinar tipo de URL
                url_type = "🔗 HTTP" if not item.download_url.startswith("data:") else "📊 Base64"
                url_preview = item.download_url[:80] + "..." if len(item.download_url) > 80 else item.download_url
                
                print(f"  {i}. {item.title or 'Sin título'}")
                print(f"     📏 Tamaño: {item.width}x{item.height}")
                print(f"     🌐 Fuente: {item.photographer}")
                print(f"     📄 Página: {item.url}")
                print(f"     {url_type}: {url_preview}")
                print(f"     🏷️ Tags: {', '.join(item.tags) if item.tags else description.split()}")
                print()
        else:
            print("❌ No se encontraron imágenes en Google")
        
        # Cerrar recursos de Google (WebDriver)
        google_service.close()
        
    except ImportError as e:
        print(f"❌ Selenium no disponible: {e}")
        print("💡 Install with: pip install selenium webdriver-manager")
        results["google"] = []
    except Exception as e:
        print(f"❌ Error en Google: {e}")
        results["google"] = []
    
    # ========================================
    # COMPARACIÓN DE RESULTADOS
    # ========================================
    print("📊 COMPARACIÓN DE RESULTADOS")
    print("=" * 60)
    
    pexels_count = len(results.get("pexels", []))
    google_count = len(results.get("google", []))
    
    print(f"📸 Pexels: {pexels_count} imágenes")
    print(f"🌐 Google: {google_count} imágenes")
    print(f"📈 Total: {pexels_count + google_count} imágenes")
    print()
    
    # Mostrar características de cada proveedor
    print("🔍 ANÁLISIS COMPARATIVO:")
    print("-" * 30)
    
    if pexels_count > 0:
        pexels_items = results["pexels"]
        avg_pexels_size = sum(item.width * item.height for item in pexels_items) / len(pexels_items)
        print(f"📸 Pexels:")
        print(f"   • Calidad: Curada profesionalmente")
        print(f"   • Licencia: Libre para uso comercial")
        print(f"   • Tamaño promedio: {avg_pexels_size:,.0f} píxeles")
        print(f"   • Tipo URLs: HTTP directas")
        print()
    
    if google_count > 0:
        google_items = results["google"]
        google_base64 = sum(1 for item in google_items if item.download_url.startswith("data:"))
        google_http = google_count - google_base64
        
        print(f"🌐 Google:")
        print(f"   • Calidad: Variada (depende de fuente)")
        print(f"   • Licencia: Variable (verificar individualmente)")
        print(f"   • URLs HTTP: {google_http}")
        print(f"   • URLs Base64: {google_base64}")
        print(f"   • Fuentes diversas: {len(set(item.photographer for item in google_items))}")
        print()
    
    # Recomendaciones
    print("💡 RECOMENDACIONES:")
    print("-" * 20)
    if pexels_count > 0:
        print("✅ Usa Pexels para: Contenido comercial, calidad garantizada")
    if google_count > 0:
        print("✅ Usa Google para: Mayor variedad, búsquedas específicas")
    
    return results


def multi_description_demo():
    """Demo con múltiples descripciones para mostrar versatilidad"""
    descriptions = [
        "beautiful sunset over mountains",
        "modern office workspace with laptop",
        "happy children playing in park",
        "delicious italian pasta with tomatoes",
        "professional businesswoman presentation"
    ]
    
    print("🎯 DEMO: Múltiples Descripciones")
    print("=" * 50)
    print()
    
    all_results = {}
    
    for i, desc in enumerate(descriptions, 1):
        print(f"🔍 BÚSQUEDA {i}/5: {desc}")
        print("=" * 50)
        
        try:
            results = search_comparison_demo(desc, num_results=3)
            all_results[desc] = results
            
        except KeyboardInterrupt:
            print("⏹️ Búsqueda interrumpida por el usuario")
            break
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            all_results[desc] = {"pexels": [], "google": []}
        
        print("\n" + "="*50 + "\n")
    
    # Resumen final
    print("📈 RESUMEN FINAL")
    print("=" * 30)
    
    total_pexels = 0
    total_google = 0
    
    for desc, results in all_results.items():
        pexels_count = len(results.get("pexels", []))
        google_count = len(results.get("google", []))
        
        total_pexels += pexels_count
        total_google += google_count
        
        print(f"'{desc[:30]}...'")
        print(f"  📸 Pexels: {pexels_count} | 🌐 Google: {google_count}")
    
    print(f"\n📊 TOTALES:")
    print(f"   📸 Pexels: {total_pexels} imágenes")
    print(f"   🌐 Google: {total_google} imágenes")
    print(f"   📈 Total: {total_pexels + total_google} imágenes")


def focused_search_demo():
    """Demo con una búsqueda específica y análisis detallado"""
    description = "professional woman working on laptop in modern office"
    
    print("🎯 BÚSQUEDA ENFOCADA: Análisis Detallado")
    print("=" * 60)
    
    results = search_comparison_demo(description, num_results=5)
    
    # Análisis detallado
    print("🔬 ANÁLISIS DETALLADO DE URLs")
    print("-" * 40)
    
    for provider, items in results.items():
        if not items:
            continue
            
        print(f"\n{provider.upper()}:")
        print("-" * 20)
        
        for i, item in enumerate(items, 1):
            print(f"\n🖼️ Imagen {i}:")
            print(f"   📝 Título: {item.title}")
            print(f"   📏 Dimensiones: {item.width} x {item.height} px")
            print(f"   📊 Área: {item.width * item.height:,} píxeles")
            
            if provider == "pexels":
                print(f"   👤 Fotógrafo: {item.photographer}")
                print(f"   🔗 Portfolio: {item.photographer_url}")
                print(f"   🌐 Página Pexels: {item.url}")
                print(f"   ⬇️ URL Descarga: {item.download_url}")
            
            elif provider == "google":
                url_type = "Base64" if item.download_url.startswith("data:") else "HTTP"
                print(f"   🌐 Fuente: {item.photographer}")
                print(f"   📄 Página origen: {item.url}")
                print(f"   🔗 Tipo URL: {url_type}")
                
                if url_type == "HTTP":
                    print(f"   ⬇️ URL Descarga: {item.download_url}")
                else:
                    print(f"   📊 Base64 Data: {len(item.download_url)} caracteres")


def main():
    """Función principal que ejecuta todos los demos"""
    print("🚀 DEMO COMPLETO: Búsqueda Comparativa de Imágenes")
    print("🔍 Google Images vs Pexels")
    print("=" * 60)
    print()
    
    print("💡 INFORMACIÓN:")
    print("   • Este demo compara resultados de Google Images y Pexels")
    print("   • Se mostrarán las URLs de descarga de todas las imágenes")
    print("   • Google usa Selenium (puede ser más lento)")
    print("   • Pexels requiere API key para funcionar")
    print()
    
    # Verificar disponibilidad de servicios
    pexels_available = bool(os.getenv("PEXELS_API_KEY"))
    selenium_available = True
    
    try:
        import selenium
    except ImportError:
        selenium_available = False
    
    print("🔧 ESTADO DE SERVICIOS:")
    print(f"   📸 Pexels API: {'✅ Disponible' if pexels_available else '❌ Falta API key'}")
    print(f"   🌐 Google Selenium: {'✅ Disponible' if selenium_available else '❌ Falta Selenium'}")
    print()
    
    if not pexels_available and not selenium_available:
        print("❌ Ningún servicio está disponible. Configurar al menos uno:")
        print("   • Pexels: export PEXELS_API_KEY=tu_api_key")
        print("   • Google: pip install selenium webdriver-manager")
        return
    
    try:
        # Demo principal con una descripción específica
        print("1️⃣ BÚSQUEDA SIMPLE")
        search_comparison_demo("beautiful landscape with mountains and lake", num_results=3)
        print("\n" + "="*60 + "\n")
        
        # Demo enfocado con análisis detallado
        print("2️⃣ ANÁLISIS DETALLADO")
        focused_search_demo()
        print("\n" + "="*60 + "\n")
        
        # Preguntar si quiere hacer múltiples búsquedas
        print("3️⃣ ¿MÚLTIPLES BÚSQUEDAS?")
        response = input("¿Ejecutar demo con 5 descripciones diferentes? (y/N): ").strip().lower()
        
        if response in ['y', 'yes', 'sí', 's']:
            multi_description_demo()
        else:
            print("⏩ Saltando demo múltiple")
        
        print("\n🎉 DEMO COMPLETADO!")
        print("✅ Todas las URLs han sido mostradas para comparación")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
