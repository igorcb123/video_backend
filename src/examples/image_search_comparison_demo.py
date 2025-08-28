"""
Ejemplo de comparación entre Google Images y Pexels        except Exception as e:
            print(f"❌ Error con Pexels API: {e}")
            results["pexels"] = []
    else:
        print("⚠️  API keys de Pexels no configuradas (PEXELS_API_KEYS)")
        print("💡 Configúralas para probar Pexels API")
        results["pexels"] = []usca imágenes basadas en una descripción en inglés y muestra las URLs de los resultados.
"""

import os
import sys

# Agregar el directorio src al path para las importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.media_fetcher_orchestrator import MediaFetcherService


def search_and_compare_providers(description: str, num_images: int = 5):
    """
    Busca imágenes en Google y Pexels usando la misma descripción y compara resultados.
    
    Args:
        description: Descripción en inglés para buscar imágenes
        num_images: Número de imágenes a buscar por proveedor
    """
    print("🔍 COMPARACIÓN DE PROVEEDORES DE IMÁGENES")
    print("=" * 60)
    print(f"Búsqueda: '{description}'")
    print(f"Imágenes solicitadas: {num_images} por proveedor")
    print("-" * 60)
    
    results = {}
    
    # 1. BUSCAR EN PEXELS
    print("\n🎨 BUSCANDO EN PEXELS API...")
    print("-" * 30)
    
    if os.getenv("PEXELS_API_KEYS"):
        try:
            pexels_service = MediaFetcherService(provider="pexels")
            pexels_result = pexels_service.search_images(description, per_page=num_images)
            results["pexels"] = pexels_result.items
            
            print(f"✅ Pexels encontró: {len(pexels_result.items)} imágenes")
            print(f"📊 Total disponible: {pexels_result.total_results}")
            
            if pexels_result.items:
                print("\n📋 RESULTADOS DE PEXELS:")
                for i, item in enumerate(pexels_result.items, 1):
                    print(f"  {i}. {item.title or 'Sin título'}")
                    print(f"     🖼️  Tamaño: {item.width}x{item.height}")
                    print(f"     👤 Fotógrafo: {item.photographer}")
                    print(f"     🔗 URL Página: {item.url}")
                    print(f"     📥 URL Descarga: {item.download_url}")
                    print(f"     🏷️  Tags: {', '.join(item.tags) if item.tags else 'Sin tags'}")
                    print()
            else:
                print("     ❌ No se encontraron imágenes")
            
        except Exception as e:
            print(f"❌ Error en Pexels: {e}")
            results["pexels"] = []
    else:
        print("⚠️  API key de Pexels no configurada (PEXELS_API_KEY)")
        print("💡 Configúrala para probar Pexels API")
        results["pexels"] = []
    
    # 2. BUSCAR EN GOOGLE IMAGES
    print("\n🌐 BUSCANDO EN GOOGLE IMAGES (Scraping)...")
    print("-" * 30)
    
    try:
        google_service = MediaFetcherService(provider="google")
        google_result = google_service.search_images(description, per_page=num_images)
        results["google"] = google_result.items
        
        print(f"✅ Google encontró: {len(google_result.items)} imágenes")
        print(f"📊 Total estimado: {google_result.total_results}")
        
        if google_result.items:
            print("\n📋 RESULTADOS DE GOOGLE:")
            for i, item in enumerate(google_result.items, 1):
                url_type = "Base64" if item.download_url.startswith("data:image") else "HTTP"
                print(f"  {i}. {item.title or 'Sin título'}")
                print(f"     🖼️  Tamaño: {item.width}x{item.height}")
                print(f"     🌍 Fuente: {item.photographer}")
                print(f"     🔗 URL Página: {item.url}")
                print(f"     📥 URL Descarga: {item.download_url[:100]}{'...' if len(item.download_url) > 100 else ''}")
                print(f"     📊 Tipo URL: {url_type}")
                print(f"     🏷️  Tags: {', '.join(item.tags) if item.tags else 'Sin tags'}")
                print()
        else:
            print("     ❌ No se encontraron imágenes")
            
        # Importante: Cerrar WebDriver
        google_service.close()
        
    except ImportError:
        print("❌ Selenium no está disponible")
        print("💡 Instala con: pip install selenium webdriver-manager")
        results["google"] = []
    except Exception as e:
        print(f"❌ Error en Google: {e}")
        results["google"] = []
    
    # 3. COMPARACIÓN DE RESULTADOS
    print("\n📊 ANÁLISIS COMPARATIVO")
    print("=" * 60)
    
    pexels_count = len(results.get("pexels", []))
    google_count = len(results.get("google", []))
    
    print(f"📈 Resultados obtenidos:")
    print(f"   🎨 Pexels API: {pexels_count} imágenes")
    print(f"   🌐 Google Scraping: {google_count} imágenes")
    
    print(f"\n🔍 Análisis de URLs:")
    
    # Analizar tipos de URLs en Google
    if results.get("google"):
        base64_count = sum(1 for item in results["google"] if item.download_url.startswith("data:image"))
        http_count = google_count - base64_count
        print(f"   Google - Base64: {base64_count}, HTTP: {http_count}")
    
    # Analizar fuentes en Google
    if results.get("google"):
        sources = {}
        for item in results["google"]:
            source = item.photographer or "Desconocido"
            sources[source] = sources.get(source, 0) + 1
        print(f"   Google - Fuentes únicas: {len(sources)}")
        if len(sources) <= 5:  # Mostrar si hay pocas fuentes
            for source, count in sources.items():
                print(f"     • {source}: {count} imagen(es)")
    
    print(f"\n💡 Observaciones:")
    
    if pexels_count > 0:
        print(f"   ✅ Pexels: URLs directas, alta calidad, metadatos completos")
        print(f"   ✅ Pexels: Licencias claras, fotógrafos identificados")
    else:
        print(f"   ⚠️  Pexels: Requiere API key para funcionar")
    
    if google_count > 0:
        print(f"   ✅ Google: Mayor variedad de fuentes")
        print(f"   ✅ Google: Sin límites de API")
        if any(item.download_url.startswith("data:image") for item in results.get("google", [])):
            print(f"   ⚠️  Google: Algunas imágenes en formato Base64")
    else:
        print(f"   ⚠️  Google: Scraping puede fallar por cambios en el sitio")
    
    return results


def demo_multiple_descriptions():
    """Prueba varias descripciones diferentes."""
    descriptions = [
        # Genéricos
        "happy family having dinner",
        "person reading a book",
        
        # Abstractos  
        "flowing liquid metal texture",
        "ethereal light particles floating in space",
        
        # Muy específicos
        "red 2019 Tesla Model S parked in front of glass office building",
        "elderly woman wearing blue cardigan knitting wool scarf by window",
        
        # Educativos
        "human heart anatomy cross section medical illustration", 
        "solar system planets educational diagram with labels"
    ]
    
    print("🚀 DEMO: BÚSQUEDAS MÚLTIPLES")
    print("=" * 60)
    
    for i, description in enumerate(descriptions, 1):
        print(f"\n🔍 BÚSQUEDA {i}/8: '{description}'")
        print("-" * 50)
        
        try:
            results = search_and_compare_providers(description, num_images=3)
            
            # Resumen rápido
            pexels_count = len(results.get("pexels", []))
            google_count = len(results.get("google", []))
            
            print(f"📋 Resumen: Pexels={pexels_count}, Google={google_count}")
            
            if i < len(descriptions):
                print("\n⏳ Esperando antes de la siguiente búsqueda...")
                import time
                time.sleep(2)  # Pausa entre búsquedas
                
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            continue
    
    print(f"\n✅ Demo de búsquedas múltiples completado!")


def demo_detailed_search():
    """Demo detallado con una sola búsqueda."""
    description = "professional business meeting in modern conference room"
    
    print("🔎 DEMO: BÚSQUEDA DETALLADA")
    print("=" * 60)
    print(f"Descripción: '{description}'")
    print()
    
    results = search_and_compare_providers(description, num_images=5)
    
    # Mostrar detalles adicionales
    print("\n🔍 DETALLES ADICIONALES")
    print("-" * 30)
    
    for provider, items in results.items():
        if items:
            print(f"\n📊 Análisis de {provider.upper()}:")
            
            # Estadísticas de tamaños
            sizes = [(item.width, item.height) for item in items if item.width and item.height]
            if sizes:
                avg_width = sum(w for w, h in sizes) / len(sizes)
                avg_height = sum(h for w, h in sizes) / len(sizes)
                print(f"   📐 Tamaño promedio: {avg_width:.0f}x{avg_height:.0f}")
                
                max_size = max(sizes, key=lambda x: x[0] * x[1])
                min_size = min(sizes, key=lambda x: x[0] * x[1])
                print(f"   📏 Rango de tamaños: {min_size[0]}x{min_size[1]} a {max_size[0]}x{max_size[1]}")
            
            # Análisis de títulos
            titles = [item.title for item in items if item.title]
            if titles:
                avg_title_length = sum(len(title) for title in titles) / len(titles)
                print(f"   📝 Longitud promedio de título: {avg_title_length:.1f} caracteres")


def main():
    """Función principal del demo."""
    print("🎯 DEMO DE COMPARACIÓN: GOOGLE vs PEXELS")
    print("=" * 60)
    print()
    
    print("💡 INFORMACIÓN IMPORTANTE:")
    print("   • Para Pexels: Configura PEXELS_API_KEYS")
    print("   • Para Google: Asegúrate de tener Chrome instalado")
    print("   • Google usa scraping, Pexels usa API oficial")
    print()
    
    # Verificar disponibilidad
    pexels_available = bool(os.getenv("PEXELS_API_KEYS"))
    
    try:
        from selenium import webdriver
        google_available = True
    except ImportError:
        google_available = False
    
    print("🔧 ESTADO DE PROVEEDORES:")
    print(f"   🎨 Pexels API: {'✅ Disponible' if pexels_available else '❌ API keys requeridas'}")
    print(f"   🌐 Google Scraping: {'✅ Disponible' if google_available else '❌ Selenium requerido'}")
    print()
    
    if not pexels_available and not google_available:
        print("⚠️ Ningún proveedor está disponible completamente.")
        print("   El demo continuará pero con funcionalidad limitada.")
        print()
    
    # Ejecutar demos
    print("🚀 INICIANDO DEMOS...")
    print()
    
    # Demo 1: Búsqueda detallada
    demo_detailed_search()
    
    print("\n" + "="*80 + "\n")
    
    # Demo 2: Búsquedas múltiples
    demo_multiple_descriptions()
    
    print("\n✅ TODOS LOS DEMOS COMPLETADOS!")
    print("🎉 Comparación entre Google Images y Pexels finalizada.")


if __name__ == "__main__":
    main()
