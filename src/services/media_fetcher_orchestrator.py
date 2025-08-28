"""Media fetcher orchestrator service."""

from pathlib import Path
from typing import Literal, Optional, Dict, List, Any

from services.media_cache import MediaCache
from services.fetchers.pexels_fetcher import PexelsFetcher
from services.fetchers.google_fetcher import GoogleImagesFetcher
from services.fetchers.base_fetcher import BaseMediaFetcher, MediaItem, SearchResult
from config.settings import settings


class MediaFetcherService:
    """
    Orquestador principal para obtención de medios con soporte para múltiples proveedores y caché.
    """
    
    def __init__(self, provider: Literal["pexels", "google"] = "pexels"):
        self.provider_name = provider
        self.cache_enabled = settings.cache_enabled
        self._cache = MediaCache(
            cache_dir=settings.temp_dir / "media_cache",
            ttl_hours=24,
            max_size_mb=500
        )
        self.fetcher = self._initialize_fetcher()
    
    def _initialize_fetcher(self) -> BaseMediaFetcher:
        """Initialize the media fetcher based on provider."""
        if self.provider_name == "pexels":
            # Use the new settings field for multiple API keys
            api_keys = getattr(settings, 'pexels_api_keys', '')
            return PexelsFetcher(api_keys=api_keys)
        elif self.provider_name == "google":
            webdriver_path = getattr(settings, 'webdriver_path', '') or None
            headless = getattr(settings, 'selenium_headless', True)
            return GoogleImagesFetcher(webdriver_path=webdriver_path, headless=headless)
        else:
            raise ValueError(f"Proveedor de medios no soportado: {self.provider_name}")
    
    def search_images(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 15,
        use_cache: bool = True,
        **filters: Any
    ) -> SearchResult:
        """
        Search for images using the configured provider.
        
        Args:
            query: Search query string
            page: Page number (1-based)
            per_page: Number of results per page
            use_cache: Whether to use cached results
            **filters: Additional filters (orientation, size, color, etc.)
            
        Returns:
            SearchResult object with media items
        """
        # Try cache first if enabled
        if self.cache_enabled and use_cache:
            cached_result = self._cache.get_cached_search_result(query, page, per_page, filters, provider=self.provider_name)
            if cached_result:
                print(f"✓ Using cached search results for: {query}")
                return cached_result
        
        # Fetch from provider
        try:
            print(f"🔍 Searching {self.provider_name} for: {query}")
            result = self.fetcher.search(query, page, per_page, **filters)
            
            # Cache the result
            if self.cache_enabled:
                self._cache.cache_search_result(query, page, per_page, filters, result, provider=self.provider_name)
                # Also cache individual items
                for item in result.items:
                    self._cache.cache_media_item(item)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Error searching images: {str(e)}")
        finally:
            # Clean up WebDriver for Google fetcher
            if hasattr(self.fetcher, 'close'):
                self.fetcher.close()
    
    def get_image(self, item_id: str, use_cache: bool = True) -> MediaItem:
        """
        Get a specific image by ID.
        
        Args:
            item_id: The image ID
            use_cache: Whether to use cached data
            
        Returns:
            MediaItem object
        """
        # Try cache first if enabled
        if self.cache_enabled and use_cache:
            cached_item = self._cache.get_cached_media_item(self.provider_name, item_id)
            if cached_item:
                print(f"✓ Using cached item: {item_id}")
                return cached_item
        
        # Fetch from provider
        try:
            print(f"📥 Fetching {self.provider_name} item: {item_id}")
            item = self.fetcher.get_item(item_id)
            
            # Cache the item
            if self.cache_enabled:
                self._cache.cache_media_item(item)
            
            return item
            
        except Exception as e:
            raise RuntimeError(f"Error fetching image {item_id}: {str(e)}")
    
    def download_image(
        self, 
        item: MediaItem, 
        size: str = "medium", 
        custom_path: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Download an image to local storage.
        
        Args:
            item: MediaItem to download
            size: Size variant to download (small, medium, large, original)
            custom_path: Custom output path (optional)
            use_cache: Whether to use cached files
            
        Returns:
            Path to the downloaded file
        """
        # Check cache first if enabled
        if self.cache_enabled and use_cache:
            cached_path = self._cache.get_cached_file_path(item, size)
            if cached_path:
                print(f"✓ Using cached file: {cached_path}")
                return cached_path
        
        # Determine output path
        if custom_path:
            output_path = custom_path
        else:
            output_path = self._cache.cache_file_path(item, size)
        
        # Download from provider
        try:
            print(f"⬇️ Downloading {item.provider} image: {item.id} ({size})")
            downloaded_path = self.fetcher.download_item(item, output_path, size)
            print(f"✓ Downloaded to: {downloaded_path}")
            return downloaded_path
            
        except Exception as e:
            raise RuntimeError(f"Error downloading image: {str(e)}")
    
    def search_and_download(
        self, 
        query: str, 
        count: int = 5, 
        size: str = "medium",
        download_dir: Optional[str] = None,
        **filters: Any
    ) -> List[str]:
        """
        Search for images and download them in one operation.
        
        Args:
            query: Search query string
            count: Number of images to download
            size: Size variant to download
            download_dir: Directory to save images (optional)
            **filters: Additional search filters
            
        Returns:
            List of paths to downloaded files
        """
        # Search for images
        search_result = self.search_images(query, per_page=count, **filters)
        
        if not search_result.items:
            raise RuntimeError(f"No images found for query: {query}")
        
        # Download images
        downloaded_paths = []
        items_to_download = search_result.items[:count]
        
        for i, item in enumerate(items_to_download, 1):
            try:
                if download_dir:
                    filename = f"{query.replace(' ', '_')}_{i}_{item.id}.jpg"
                    custom_path = str(Path(download_dir) / filename)
                else:
                    custom_path = None
                
                path = self.download_image(item, size, custom_path)
                downloaded_paths.append(path)
                
            except Exception as e:
                print(f"⚠️ Failed to download image {item.id}: {e}")
                continue
        
        return downloaded_paths
    
    def bulk_download_images(
        self, 
        items: List[MediaItem], 
        output_dir: str, 
        size: str = "medium",
        max_concurrent: int = 3
    ) -> List[str]:
        """
        Download multiple images (sequential for Google scraper).
        
        Args:
            items: List of MediaItems to download
            output_dir: Directory to save images
            size: Size preference
            max_concurrent: Maximum concurrent downloads (ignored for Google scraper)
            
        Returns:
            List of paths to downloaded files
        """
        print(f"� Downloading {len(items)} images to {output_dir}")
        downloaded_paths = []
        
        for i, item in enumerate(items, 1):
            try:
                # Generate filename
                import re
                safe_title = re.sub(r'[^\w\-_\.]', '_', item.title or f"image_{item.id}")[:50]
                filename = f"{i:03d}_{safe_title}.jpg"
                output_path = str(Path(output_dir) / filename)
                
                path = self.download_image(item, size, output_path)
                downloaded_paths.append(path)
                print(f"Downloaded {i}/{len(items)}: {filename}")
                
            except Exception as e:
                print(f"⚠️ Failed to download image {i}: {e}")
                continue
        
        print(f"✓ Successfully downloaded {len(downloaded_paths)} images")
        return downloaded_paths
    
    def get_quota_info(self) -> Optional[Dict[str, Any]]:
        """Get quota information for providers that support it."""
        # Google scraper doesn't have quota limits like API
        return None
    
    def get_provider_capabilities(self) -> Dict[str, Any]:
        """Get detailed capabilities of the current provider."""
        capabilities = {
            "name": self.fetcher.name,
            "supported_formats": self.fetcher.supported_formats,
            "cache_enabled": self.cache_enabled,
            "bulk_download": True,  # Our orchestrator always supports this
            "async_download": False,  # Selenium is synchronous
            "quota_tracking": False   # Scraping doesn't have quotas
        }
        
        # Add provider-specific capabilities
        if hasattr(self.fetcher, 'supported_sizes'):
            capabilities["supported_sizes"] = self.fetcher.supported_sizes
        
        if hasattr(self.fetcher, 'supported_image_types'):
            capabilities["supported_image_types"] = self.fetcher.supported_image_types
        
        if hasattr(self.fetcher, 'supported_colors'):
            capabilities["supported_colors"] = self.fetcher.supported_colors
        
        return capabilities
    
    def close(self) -> None:
        """Close resources (WebDriver for Google fetcher)."""
        if hasattr(self, 'fetcher') and hasattr(self.fetcher, 'close'):
            self.fetcher.close()
    
    def __del__(self):
        """Cleanup resources on object destruction."""
        try:
            self.close()
        except Exception:
            pass  # Ignore cleanup errors during destruction

    def cleanup_cache(self) -> None:
        """Clean up expired cache files."""
        if self.cache_enabled:
            print("🧹 Cleaning up expired cache files...")
            self._cache.cleanup_old_cache()
            print("✓ Cache cleanup completed")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache_enabled:
            return self._cache.get_cache_stats()
        return {"cache_enabled": False}
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        return {
            "name": self.fetcher.name,
            "supported_formats": self.fetcher.supported_formats,
            "cache_enabled": self.cache_enabled
        }
