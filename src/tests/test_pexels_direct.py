"""
Test rápido sin caché para verificar Pexels API keys.
"""

import os
import sys

# Agregar el directorio src al path para las importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.fetchers.pexels_fetcher import PexelsFetcher
from services.fetchers.key_manager import PexelsAPIKeyManager

def test_pexels_direct():
    """Test directo de Pexels sin orchestrador."""
    print("🧪 TEST DIRECTO DE PEXELS API")
    print("=" * 50)
    
    # Check API keys
    api_keys = os.getenv("PEXELS_API_KEYS", "")
    
    if not api_keys:
        print("❌ PEXELS_API_KEYS no está configurada")
        print("💡 Configura esta variable de entorno con tus API keys separadas por comas")
        return False
    
    print(f"🔑 API Keys encontradas: {len(api_keys.split(','))} claves")
    
    try:
        # Test key manager
        keys = [k.strip() for k in api_keys.split(",") if k.strip()]
        key_manager = PexelsAPIKeyManager(keys)
        
        print(f"✅ Key Manager inicializado con {len(keys)} claves")
        
        # Get usage stats
        stats = key_manager.get_usage_stats()
        print("📊 Estado inicial de las claves:")
        for key_id, stat in stats.items():
            print(f"   🔑 ...{key_id}: {stat['remaining_calls']} llamadas disponibles")
        
        # Test fetcher
        fetcher = PexelsFetcher(api_keys)
        print("✅ PexelsFetcher inicializado correctamente")
        
        # Test search
        print("\n🔍 Probando búsqueda: 'coffee cup morning'")
        result = fetcher.search("coffee cup morning", per_page=3)
        
        print(f"✅ Búsqueda exitosa: {len(result.items)} resultados")
        print(f"📊 Total disponible: {result.total_results}")
        
        if result.items:
            print("\n📋 RESULTADOS:")
            for i, item in enumerate(result.items, 1):
                print(f"  {i}. {item.title}")
                print(f"     📐 Tamaño: {item.width}x{item.height}")
                print(f"     🔗 URL: {item.url}")
                print(f"     📥 Download: {item.download_url[:80]}...")
                print(f"     👨‍💼 Fotógrafo: {item.photographer}")
                print()
        
        # Test get usage after request
        stats_after = fetcher.get_usage_stats()
        print("📊 Estado después de la búsqueda:")
        for key_id, stat in stats_after.items():
            print(f"   🔑 ...{key_id}: {stat['remaining_calls']} llamadas restantes")
        
        fetcher.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_pexels_direct()
    print(f"\n{'✅ Test exitoso' if success else '❌ Test fallido'}")
