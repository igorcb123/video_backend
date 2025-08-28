"""Example usage of MediaFetcherService with multiple providers."""

import os
from pathlib import Path
from services.media_fetcher_orchestrator import MediaFetcherService


def demo_provider_comparison():
    """Demo comparing different providers."""
    print("⚖️ Demo: Provider Comparison")
    print("-" * 40)
    
    providers = ["pexels", "google"]
    
    for provider in providers:
        try:
            print(f"\n📊 Testing {provider.upper()} provider:")
            
            # Check if API keys are available
            api_key_available = False
            if provider == "pexels":
                api_key_available = bool(os.getenv("PEXELS_API_KEY"))
            elif provider == "google":
                api_key_available = bool(os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY") and 
                                       os.getenv("GOOGLE_SEARCH_ENGINE_ID"))
            
            if not api_key_available:
                print(f"⚠️ API key not available for {provider}")
                continue
            
            service = MediaFetcherService(provider=provider)
            capabilities = service.get_provider_capabilities()
            
            print(f"Provider: {capabilities['name']}")
            print(f"Supported formats: {capabilities['supported_formats']}")
            print(f"Bulk download: {capabilities['bulk_download']}")
            print(f"Async download: {capabilities['async_download']}")
            print(f"Quota tracking: {capabilities['quota_tracking']}")
            
            if "supported_sizes" in capabilities:
                print(f"Supported sizes: {capabilities['supported_sizes']}")
            
            if "supported_colors" in capabilities:
                print(f"Supported colors: {capabilities['supported_colors']}")
            
            # Test quota info for Google
            if provider == "google":
                quota_info = service.get_quota_info()
                if quota_info:
                    print(f"Quota used: {quota_info['daily_used']}/{quota_info['daily_limit']}")
            
        except Exception as e:
            print(f"❌ Error with {provider}: {e}")


def demo_google_advanced_search():
    """Demo Google Images advanced search features."""
    print("🎯 Demo: Google Images Advanced Search")
    print("-" * 40)
    
    if not (os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID")):
        print("⚠️ Google API keys not set - skipping Google demo")
        return
    
    try:
        service = MediaFetcherService(provider="google")
        
        # Test various search filters
        search_configs = [
            {
                "query": "sunset landscape",
                "filters": {"size": "large", "image_type": "photo", "color": "orange"},
                "description": "Large orange sunset photos"
            },
            {
                "query": "business meeting",
                "filters": {"usage_rights": "cc_publicdomain", "file_type": "jpg"},
                "description": "Business meeting images with public domain rights"
            },
            {
                "query": "logo design",
                "filters": {"image_type": "lineart", "site_search": "dribbble.com"},
                "description": "Line art logos from Dribbble"
            }
        ]
        
        for config in search_configs:
            print(f"\n🔍 Searching: {config['description']}")
            print(f"Query: '{config['query']}'")
            print(f"Filters: {config['filters']}")
            
            result = service.search_images(
                config["query"], 
                per_page=3, 
                **config["filters"]
            )
            
            print(f"Found {len(result.items)} images (Total: {result.total_results})")
            
            for i, item in enumerate(result.items, 1):
                print(f"  {i}. {item.title[:50]}...")
                print(f"     Size: {item.width}x{item.height}")
                print(f"     Source: {item.photographer}")
        
        # Show quota usage
        quota_info = service.get_quota_info()
        if quota_info:
            print(f"\n📊 API Usage: {quota_info['daily_used']}/{quota_info['daily_limit']} "
                  f"({quota_info['percentage_used']:.1f}%)")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_bulk_download_google():
    """Demo Google Images bulk download."""
    print("🚀 Demo: Google Bulk Download")
    print("-" * 40)
    
    if not (os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID")):
        print("⚠️ Google API keys not set - skipping bulk download demo")
        return
    
    try:
        service = MediaFetcherService(provider="google")
        
        # Search for images
        query = "nature photography"
        print(f"Searching for: '{query}'")
        
        result = service.search_images(query, per_page=5, size="medium", image_type="photo")
        
        if result.items:
            # Create download directory
            download_dir = Path("./temp/google_bulk_download")
            download_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"Found {len(result.items)} images")
            print(f"Bulk downloading to: {download_dir}")
            
            # Use bulk download (Google-specific feature)
            downloaded_files = service.bulk_download_images(
                result.items[:3],  # Download first 3
                str(download_dir),
                size="medium",
                max_concurrent=2
            )
            
            print(f"Successfully downloaded {len(downloaded_files)} images:")
            for file_path in downloaded_files:
                file_size = Path(file_path).stat().st_size / 1024  # KB
                print(f"- {Path(file_path).name} ({file_size:.1f} KB)")
        else:
            print("No images found")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_mixed_provider_workflow():
    """Demo using different providers in the same workflow."""
    print("🔄 Demo: Mixed Provider Workflow")
    print("-" * 40)
    
    try:
        # Try Pexels first
        pexels_available = bool(os.getenv("PEXELS_API_KEY"))
        google_available = bool(os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY") and 
                              os.getenv("GOOGLE_SEARCH_ENGINE_ID"))
        
        query = "workspace office"
        results = {}
        
        if pexels_available:
            print("🔍 Searching Pexels...")
            pexels_service = MediaFetcherService(provider="pexels")
            pexels_result = pexels_service.search_images(query, per_page=3)
            results["pexels"] = pexels_result
            print(f"Pexels found: {len(pexels_result.items)} images")
        
        if google_available:
            print("🔍 Searching Google...")
            google_service = MediaFetcherService(provider="google")
            google_result = google_service.search_images(
                query, 
                per_page=3,
                image_type="photo",
                usage_rights="cc_publicdomain"
            )
            results["google"] = google_result
            print(f"Google found: {len(google_result.items)} images")
        
        # Compare results
        print("\n📊 Results Comparison:")
        for provider, result in results.items():
            print(f"\n{provider.upper()}:")
            for i, item in enumerate(result.items, 1):
                print(f"  {i}. {item.title[:40]}...")
                print(f"     {item.width}x{item.height} - {item.photographer}")
        
        if not results:
            print("⚠️ No API keys available for demonstration")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_basic_search():
    """Demo basic search functionality."""
    print("🔍 Demo: Basic Image Search")
    print("-" * 40)
    
    try:
        # Try to use the best available provider
        provider = "pexels"  # Default
        
        if os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY") and os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
            provider = "google"
        elif not os.getenv("PEXELS_API_KEY"):
            print("⚠️ No API keys available - using mock demonstration")
            return
        
        # Initialize service
        service = MediaFetcherService(provider=provider)
        
        # Get provider info
        capabilities = service.get_provider_capabilities()
        print(f"Using provider: {capabilities['name']}")
        print(f"Supported formats: {capabilities['supported_formats']}")
        print(f"Cache enabled: {capabilities['cache_enabled']}")
        print()
        
        # Search for images
        query = "mountain landscape"
        print(f"Searching for: '{query}'")
        
        result = service.search_images(query, per_page=5)
        
        print(f"Found {len(result.items)} images (Total: {result.total_results})")
        print()
        
        # Display results
        for i, item in enumerate(result.items, 1):
            print(f"{i}. {item.title or 'Untitled'}")
            print(f"   ID: {item.id}")
            print(f"   Size: {item.width}x{item.height}")
            print(f"   Photographer: {item.photographer or 'Unknown'}")
            print(f"   URL: {item.url}")
            print()
        
        return result.items
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def demo_search_with_filters():
    """Demo search with filters."""
    print("🎯 Demo: Search with Filters")
    print("-" * 40)
    
    try:
        service = MediaFetcherService()
        
        # Search with filters
        query = "city"
        filters = {
            "orientation": "landscape",
            "size": "large",
            "color": "blue"
        }
        
        print(f"Searching for: '{query}' with filters: {filters}")
        
        if os.getenv("PEXELS_API_KEY"):
            result = service.search_images(query, per_page=3, **filters)
            print(f"Found {len(result.items)} filtered images")
            
            for item in result.items:
                print(f"- {item.title or 'Untitled'} ({item.width}x{item.height})")
        else:
            print("⚠️ PEXELS_API_KEY not set - skipping API call")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_download_functionality():
    """Demo download functionality."""
    print("⬇️ Demo: Download Images")
    print("-" * 40)
    
    try:
        service = MediaFetcherService()
        
        # Create temp download directory
        download_dir = Path("./temp/demo_downloads")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        if os.getenv("PEXELS_API_KEY"):
            # Search and download in one step
            query = "mountain"
            print(f"Searching and downloading images for: '{query}'")
            
            downloaded_files = service.search_and_download(
                query=query,
                count=2,
                size="medium",
                download_dir=str(download_dir)
            )
            
            print(f"Downloaded {len(downloaded_files)} images:")
            for file_path in downloaded_files:
                file_size = Path(file_path).stat().st_size / 1024  # KB
                print(f"- {Path(file_path).name} ({file_size:.1f} KB)")
        else:
            print("⚠️ PEXELS_API_KEY not set - cannot download real images")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_cache_functionality():
    """Demo cache functionality."""
    print("💾 Demo: Cache Functionality")
    print("-" * 40)
    
    try:
        service = MediaFetcherService()
        
        # Get cache stats
        stats = service.get_cache_stats()
        print("Cache Statistics:")
        for key, value in stats.items():
            print(f"- {key}: {value}")
        print()
        
        # Clean up cache
        service.cleanup_cache()
        
        # Get updated stats
        stats = service.get_cache_stats()
        print("Cache Statistics After Cleanup:")
        for key, value in stats.items():
            print(f"- {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_integration_with_image_filter():
    """Demo integration with existing image filter service."""
    print("🔗 Demo: Integration with Image Filter")
    print("-" * 40)
    
    try:
        from services.image_filter_class import ImageFilterCLIP
        
        # Initialize services
        media_service = MediaFetcherService()
        
        if os.getenv("PEXELS_API_KEY"):
            # Search for images
            query = "dog playing"
            result = media_service.search_images(query, per_page=5)
            
            if result.items:
                # Get image URLs for filtering
                image_urls = [item.download_url for item in result.items[:3]]
                
                print(f"Found {len(image_urls)} images to filter")
                print("Image URLs:")
                for url in image_urls:
                    print(f"- {url}")
                
                print("\n🔍 This is where you could use ImageFilterCLIP")
                print("   to filter these images based on specific criteria")
                
                # Example of how you might integrate:
                # filter_service = ImageFilterCLIP()
                # positive_prompts = ["happy dog", "playing"]
                # negative_prompts = ["aggressive", "sad"]
                # filtered_results = filter_service.filter_images(
                #     image_urls, positive_prompts, negative_prompts
                # )
        else:
            print("⚠️ PEXELS_API_KEY not set - cannot fetch real images for filtering")
            
    except ImportError:
        print("⚠️ ImageFilterCLIP not available - skipping integration demo")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all demos."""
    print("🚀 MediaFetcher Service Demo (Multi-Provider)")
    print("=" * 60)
    print()
    
    # Check API keys
    pexels_available = bool(os.getenv("PEXELS_API_KEY"))
    google_available = bool(os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY") and 
                           os.getenv("GOOGLE_SEARCH_ENGINE_ID"))
    
    print("� API Key Status:")
    print(f"   Pexels: {'✅ Available' if pexels_available else '❌ Missing PEXELS_API_KEY'}")
    print(f"   Google: {'✅ Available' if google_available else '❌ Missing GOOGLE_CUSTOM_SEARCH_API_KEY or GOOGLE_SEARCH_ENGINE_ID'}")
    print()
    
    if not pexels_available and not google_available:
        print("💡 Tip: Set API keys to test with real providers:")
        print("   - PEXELS_API_KEY for Pexels provider")
        print("   - GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID for Google provider")
        print()
    
    # Run demos
    demo_provider_comparison()
    print()
    
    demo_basic_search()
    print()
    
    if google_available:
        demo_google_advanced_search()
        print()
        
        demo_bulk_download_google()
        print()
    
    demo_search_with_filters()
    print()
    
    demo_download_functionality()
    print()
    
    demo_mixed_provider_workflow()
    print()
    
    demo_cache_functionality()
    print()
    
    demo_integration_with_image_filter()
    print()
    
    print("✅ Multi-provider demo completed!")
    print("🎉 Google Images fetcher successfully integrated!")


if __name__ == "__main__":
    main()
