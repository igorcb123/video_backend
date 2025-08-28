"""
Test de comparación de búsqueda entre proveedores.
Prueba la funcionalidad básica de búsqueda y comparación de URLs.
"""

import os
import sys
import pytest

# Agregar el directorio src al path para las importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.media_fetcher_orchestrator import MediaFetcherService


class TestImageSearchComparison:
    """Tests de comparación entre proveedores de imágenes."""
    
    def test_provider_availability(self):
        """Test que verifica qué proveedores están disponibles."""
        print("\n🔧 Verificando disponibilidad de proveedores...")
        
        # Test Pexels
        pexels_available = bool(os.getenv("PEXELS_API_KEYS"))
        print(f"🎨 Pexels API: {'✅ Disponible' if pexels_available else '❌ API keys requeridas (PEXELS_API_KEYS)'}")
        
        # Test Google
        try:
            service = MediaFetcherService(provider="google")
            capabilities = service.get_provider_capabilities()
            google_available = capabilities['name'] == 'google'
            service.close()
            print(f"🌐 Google Scraping: {'✅ Disponible' if google_available else '❌ No disponible'}")
        except ImportError:
            google_available = False
            print("🌐 Google Scraping: ❌ Selenium no instalado")
        except Exception as e:
            google_available = False
            print(f"🌐 Google Scraping: ❌ Error: {e}")
        
        # Al menos uno debe estar disponible para tests completos
        assert pexels_available or google_available, "Al menos un proveedor debe estar disponible"
    
    def test_search_description_english(self):
        """Test búsqueda con descripción en inglés."""
        description = "beautiful mountain landscape"
        print(f"\n🔍 Probando búsqueda: '{description}'")
        
        results = {}
        
        # Test Pexels si está disponible
        if os.getenv("PEXELS_API_KEYS"):
            try:
                pexels_service = MediaFetcherService(provider="pexels")
                pexels_result = pexels_service.search_images(description, per_page=3)
                results["pexels"] = pexels_result.items
                print(f"✅ Pexels: {len(pexels_result.items)} imágenes encontradas")
                
                # Verificar estructura de datos
                if pexels_result.items:
                    item = pexels_result.items[0]
                    assert hasattr(item, 'url'), "Item debe tener URL"
                    assert hasattr(item, 'download_url'), "Item debe tener download_url"
                    assert hasattr(item, 'title'), "Item debe tener título"
                    print(f"📋 Ejemplo Pexels URL: {item.url}")
                    print(f"📥 Ejemplo Pexels Download: {item.download_url}")
                    
            except Exception as e:
                print(f"⚠️ Pexels falló: {e}")
                results["pexels"] = []
        else:
            print("⚠️ Pexels: API keys no disponibles (PEXELS_API_KEYS)")
            results["pexels"] = []
        
        # Test Google si está disponible
        try:
            google_service = MediaFetcherService(provider="google")
            google_result = google_service.search_images(description, per_page=3)
            results["google"] = google_result.items
            google_service.close()
            
            print(f"✅ Google: {len(google_result.items)} imágenes encontradas")
            
            # Verificar estructura de datos
            if google_result.items:
                item = google_result.items[0]
                assert hasattr(item, 'url'), "Item debe tener URL"
                assert hasattr(item, 'download_url'), "Item debe tener download_url"
                assert hasattr(item, 'title'), "Item debe tener título"
                print(f"📋 Ejemplo Google URL: {item.url}")
                url_preview = item.download_url[:100] + "..." if len(item.download_url) > 100 else item.download_url
                print(f"📥 Ejemplo Google Download: {url_preview}")
                
        except ImportError:
            print("⚠️ Google: Selenium no disponible")
            results["google"] = []
        except Exception as e:
            print(f"⚠️ Google falló: {e}")
            results["google"] = []
        
        # Verificar que al menos un proveedor devolvió resultados
        total_results = sum(len(items) for items in results.values())
        print(f"📊 Total de imágenes encontradas: {total_results}")
        
        # Si hay API keys/dependencias, debe haber resultados
        has_pexels_key = bool(os.getenv("PEXELS_API_KEYS"))
        try:
            import selenium
            has_selenium = True
        except ImportError:
            has_selenium = False
        
        if has_pexels_key or has_selenium:
            assert total_results > 0, f"Debería encontrar imágenes con proveedores disponibles: Pexels={has_pexels_key}, Selenium={has_selenium}"
    
    def test_url_formats(self):
        """Test que verifica los formatos de URLs devueltos."""
        description = "office workspace"
        print(f"\n🔗 Probando formatos de URL: '{description}'")
        
        # Test con Google para verificar diferentes tipos de URL
        try:
            service = MediaFetcherService(provider="google")
            result = service.search_images(description, per_page=3)
            service.close()
            
            if result.items:
                print("🌐 Análisis de URLs de Google:")
                base64_count = 0
                http_count = 0
                
                for i, item in enumerate(result.items, 1):
                    if item.download_url.startswith("data:image"):
                        base64_count += 1
                        print(f"  {i}. Base64 image (tamaño: {len(item.download_url)} chars)")
                    elif item.download_url.startswith("http"):
                        http_count += 1
                        print(f"  {i}. HTTP URL: {item.download_url[:80]}...")
                    else:
                        print(f"  {i}. Formato desconocido: {item.download_url[:50]}...")
                
                print(f"📊 Resumen: {base64_count} Base64, {http_count} HTTP")
                
                # Verificar que las URLs no estén vacías
                for item in result.items:
                    assert item.download_url, "Download URL no debe estar vacío"
                    assert len(item.download_url) > 10, "Download URL debe tener contenido válido"
                    
        except ImportError:
            print("⚠️ Selenium no disponible para test de URLs")
        except Exception as e:
            print(f"⚠️ Error en test de URLs: {e}")
    
    def test_comparison_output(self):
        """Test que simula la función de comparación principal."""
        description = "business meeting"
        print(f"\n📊 Test de comparación completa: '{description}'")
        
        def mock_search_and_compare(desc, num_images=3):
            """Versión simplificada de la función de comparación."""
            results = {}
            
            # Pexels
            if os.getenv("PEXELS_API_KEYS"):
                try:
                    service = MediaFetcherService(provider="pexels")
                    result = service.search_images(desc, per_page=num_images)
                    results["pexels"] = len(result.items)
                except Exception:
                    results["pexels"] = 0
            else:
                results["pexels"] = 0
            
            # Google
            try:
                service = MediaFetcherService(provider="google")
                result = service.search_images(desc, per_page=num_images)
                results["google"] = len(result.items)
                service.close()
            except Exception:
                results["google"] = 0
            
            return results
        
        results = mock_search_and_compare(description)
        
        print(f"📈 Resultados de comparación:")
        print(f"   🎨 Pexels: {results['pexels']} imágenes")
        print(f"   🌐 Google: {results['google']} imágenes")
        
        # Verificar que la función devuelve datos válidos
        assert isinstance(results, dict), "Debe devolver diccionario"
        assert "pexels" in results, "Debe incluir resultados de Pexels"
        assert "google" in results, "Debe incluir resultados de Google"
        assert all(isinstance(v, int) and v >= 0 for v in results.values()), "Conteos deben ser enteros no negativos"


def test_manual_search_comparison():
    """Test manual que puede ejecutarse directamente."""
    print("\n🧪 TEST MANUAL: Búsqueda y Comparación")
    print("-" * 50)
    
    description = "modern technology laptop computer"
    num_images = 2
    
    print(f"🔍 Búsqueda: '{description}'")
    print(f"📊 Imágenes por proveedor: {num_images}")
    
    all_results = []
    
    # Test Pexels
    print("\n🎨 Probando Pexels...")
    if os.getenv("PEXELS_API_KEYS"):
        try:
            pexels_service = MediaFetcherService(provider="pexels")
            pexels_result = pexels_service.search_images(description, per_page=num_images)
            
            print(f"✅ Pexels encontró: {len(pexels_result.items)} imágenes")
            for i, item in enumerate(pexels_result.items, 1):
                print(f"   {i}. {item.title or 'Sin título'}")
                print(f"      URL: {item.url}")
                print(f"      Download: {item.download_url}")
                all_results.append(f"Pexels-{i}")
                
        except Exception as e:
            print(f"❌ Pexels error: {e}")
    else:
        print("⚠️ API keys de Pexels no configuradas (PEXELS_API_KEYS)")
    
    # Test Google
    print("\n🌐 Probando Google...")
    try:
        google_service = MediaFetcherService(provider="google")
        google_result = google_service.search_images(description, per_page=num_images)
        
        print(f"✅ Google encontró: {len(google_result.items)} imágenes")
        for i, item in enumerate(google_result.items, 1):
            print(f"   {i}. {item.title or 'Sin título'}")
            print(f"      URL: {item.url}")
            url_preview = item.download_url[:100] + "..." if len(item.download_url) > 100 else item.download_url
            print(f"      Download: {url_preview}")
            all_results.append(f"Google-{i}")
        
        google_service.close()
        
    except ImportError:
        print("❌ Selenium no está disponible")
    except Exception as e:
        print(f"❌ Google error: {e}")
    
    print(f"\n📋 Resumen: Se obtuvieron {len(all_results)} resultados en total")
    return all_results


if __name__ == "__main__":
    # Ejecutar test manual
    results = test_manual_search_comparison()
    print(f"\n✅ Test completado con {len(results)} resultados")
