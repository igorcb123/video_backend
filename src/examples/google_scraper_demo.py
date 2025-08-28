"""Specific demo for Google Images scraper functionality."""

import os
from pathlib import Path
from services.media_fetcher_orchestrator import MediaFetcherService


def demo_google_scraper_basic():
    """Demo basic Google Images scraping."""
    print("🌐 Demo: Google Images Scraper (Selenium)")
    print("-" * 50)
    
    try:
        # Initialize Google scraper (headless by default)
        service = MediaFetcherService(provider="google")
        
        print("Provider capabilities:")
        capabilities = service.get_provider_capabilities()
        for key, value in capabilities.items():
            print(f"  {key}: {value}")
        print()
        
        # Test search with basic query
        query = "python programming"
        print(f"Searching for: '{query}' (first 3 results)")
        
        try:
            result = service.search_images(query, per_page=3)
            
            print(f"Found {len(result.items)} images:")
            print()
            
            for i, item in enumerate(result.items, 1):
                print(f"{i}. {item.title[:60]}...")
                print(f"   Size: {item.width}x{item.height}")
                print(f"   Source: {item.photographer}")
                print(f"   URL type: {'Base64' if item.download_url.startswith('data:') else 'HTTP'}")
                print()
            
            return result.items
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
        finally:
            # Always close the service to clean up WebDriver
            service.close()
            
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install selenium webdriver-manager")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def demo_google_advanced_filters():
    """Demo Google Images with advanced filters."""
    print("🎯 Demo: Google Images Advanced Filters")
    print("-" * 50)
    
    try:
        service = MediaFetcherService(provider="google")
        
        # Test different filter combinations
        filter_tests = [
            {
                "query": "sunset",
                "filters": {"size": "large", "color": "orange"},
                "description": "Large orange sunset images"
            },
            {
                "query": "business",
                "filters": {"image_type": "photo", "size": "medium"},
                "description": "Medium business photos"
            },
            {
                "query": "logo",
                "filters": {"image_type": "clipart", "color": "blue"},
                "description": "Blue clipart logos"
            }
        ]
        
        all_results = []
        
        for test in filter_tests:
            print(f"🔍 {test['description']}")
            print(f"Query: '{test['query']}', Filters: {test['filters']}")
            
            try:
                result = service.search_images(
                    test["query"], 
                    per_page=2,  # Just 2 for demo
                    **test["filters"]
                )
                
                print(f"Results: {len(result.items)} images")
                for item in result.items:
                    print(f"  - {item.title[:40]}... ({item.width}x{item.height})")
                
                all_results.extend(result.items)
                print()
                
            except Exception as e:
                print(f"❌ Filter test failed: {e}")
                print()
        
        service.close()
        return all_results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def demo_google_download():
    """Demo downloading images from Google Images."""
    print("⬇️ Demo: Download Google Images")
    print("-" * 50)
    
    try:
        service = MediaFetcherService(provider="google")
        
        # Search for images
        query = "nature landscape"
        print(f"Searching and downloading: '{query}'")
        
        result = service.search_images(query, per_page=2)
        
        if result.items:
            # Create download directory
            download_dir = Path("./temp/google_downloads")
            download_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"Found {len(result.items)} images")
            print(f"Downloading to: {download_dir}")
            print()
            
            downloaded_files = []
            
            for i, item in enumerate(result.items, 1):
                try:
                    # Generate safe filename
                    safe_title = "".join(c for c in item.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title[:30] if safe_title else f"image_{item.id}"
                    
                    filename = f"{i:03d}_{safe_title.replace(' ', '_')}.jpg"
                    output_path = download_dir / filename
                    
                    print(f"Downloading image {i}: {item.title[:40]}...")
                    
                    downloaded_path = service.download_image(item, custom_path=str(output_path))
                    
                    # Check file size
                    file_size = Path(downloaded_path).stat().st_size / 1024  # KB
                    print(f"✓ Downloaded: {Path(downloaded_path).name} ({file_size:.1f} KB)")
                    
                    downloaded_files.append(downloaded_path)
                    
                except Exception as e:
                    print(f"⚠️ Failed to download image {i}: {e}")
            
            print(f"\n✅ Successfully downloaded {len(downloaded_files)} images")
            
            # Show total size
            total_size = sum(Path(f).stat().st_size for f in downloaded_files) / 1024  # KB
            print(f"Total download size: {total_size:.1f} KB")
            
        else:
            print("No images found to download")
        
        service.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def demo_google_vs_pexels():
    """Compare Google scraper vs Pexels API."""
    print("⚖️ Demo: Google vs Pexels Comparison")
    print("-" * 50)
    
    query = "mountain landscape"
    print(f"Comparing results for: '{query}'")
    print()
    
    results = {}
    
    # Test Pexels (if API key available)
    if os.getenv("PEXELS_API_KEY"):
        try:
            print("🔍 Testing Pexels API...")
            pexels_service = MediaFetcherService(provider="pexels")
            pexels_result = pexels_service.search_images(query, per_page=3)
            results["pexels"] = pexels_result.items
            print(f"Pexels found: {len(pexels_result.items)} images")
        except Exception as e:
            print(f"Pexels failed: {e}")
            results["pexels"] = []
    else:
        print("⚠️ Pexels API key not available")
        results["pexels"] = []
    
    # Test Google scraper
    try:
        print("🔍 Testing Google scraper...")
        google_service = MediaFetcherService(provider="google")
        google_result = google_service.search_images(query, per_page=3)
        results["google"] = google_result.items
        print(f"Google found: {len(google_result.items)} images")
        google_service.close()
    except Exception as e:
        print(f"Google failed: {e}")
        results["google"] = []
    
    # Compare results
    print("\n📊 Comparison Results:")
    print("-" * 30)
    
    for provider, items in results.items():
        print(f"\n{provider.upper()} ({len(items)} images):")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item.title[:50]}...")
            print(f"     Size: {item.width}x{item.height}")
            print(f"     Source: {item.photographer}")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   Pexels (API): {len(results['pexels'])} images - High quality, curated")
    print(f"   Google (Scraping): {len(results['google'])} images - Diverse sources, more variety")


def main():
    """Run Google Images scraper demos."""
    print("🚀 Google Images Scraper Demo")
    print("=" * 60)
    print()
    
    print("💡 Note: This uses Selenium to scrape Google Images")
    print("   Make sure Chrome browser is installed on your system")
    print("   WebDriver will be downloaded automatically")
    print()
    
    # Run demos
    demo_google_scraper_basic()
    print()
    
    demo_google_advanced_filters()
    print()
    
    demo_google_download()
    print()
    
    demo_google_vs_pexels()
    print()
    
    print("✅ Google Images scraper demo completed!")
    print("🎉 Successfully integrated Selenium-based Google Images scraper!")


if __name__ == "__main__":
    main()
