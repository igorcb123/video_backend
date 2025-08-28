"""Media cache service for storing and retrieving media metadata and files."""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from services.fetchers.base_fetcher import MediaItem, SearchResult


class MediaCache:
    """Cache service for media items and search results."""
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24, max_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.max_size_mb = max_size_mb
        
        # Create cache directories
        self.metadata_dir = self.cache_dir / "metadata"
        self.files_dir = self.cache_dir / "files"
        self.search_dir = self.cache_dir / "searches"
        
        for dir_path in [self.metadata_dir, self.files_dir, self.search_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, data: str) -> str:
        """Generate cache key from string data."""
        return hashlib.md5(data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid based on TTL."""
        if not cache_file.exists():
            return False
        
        file_age = time.time() - cache_file.stat().st_mtime
        max_age = self.ttl_hours * 3600  # Convert to seconds
        return file_age < max_age
    
    def cache_search_result(self, query: str, page: int, per_page: int, filters: Dict[str, Any], result: SearchResult, provider: str = None) -> None:
        """Cache search results."""
        provider_prefix = f"{provider}_" if provider else ""
        search_key = f"{provider_prefix}{query}_{page}_{per_page}_{json.dumps(filters, sort_keys=True)}"
        cache_key = self._generate_cache_key(search_key)
        cache_file = self.search_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                "timestamp": time.time(),
                "query": query,
                "page": page,
                "per_page": per_page,
                "filters": filters,
                "result": {
                    "items": [asdict(item) for item in result.items],
                    "total_results": result.total_results,
                    "page": result.page,
                    "per_page": result.per_page,
                    "has_next": result.has_next
                }
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to cache search result: {e}")
    
    def get_cached_search_result(self, query: str, page: int, per_page: int, filters: Dict[str, Any], provider: str = None) -> Optional[SearchResult]:
        """Retrieve cached search results if valid."""
        provider_prefix = f"{provider}_" if provider else ""
        search_key = f"{provider_prefix}{query}_{page}_{per_page}_{json.dumps(filters, sort_keys=True)}"
        cache_key = self._generate_cache_key(search_key)
        cache_file = self.search_dir / f"{cache_key}.json"
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            result_data = cache_data["result"]
            items = [MediaItem(**item_data) for item_data in result_data["items"]]
            
            return SearchResult(
                items=items,
                total_results=result_data["total_results"],
                page=result_data["page"],
                per_page=result_data["per_page"],
                has_next=result_data["has_next"]
            )
            
        except Exception as e:
            print(f"Warning: Failed to load cached search result: {e}")
            return None
    
    def cache_media_item(self, item: MediaItem) -> None:
        """Cache media item metadata."""
        cache_key = self._generate_cache_key(f"{item.provider}_{item.id}")
        cache_file = self.metadata_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                "timestamp": time.time(),
                "item": asdict(item)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Warning: Failed to cache media item: {e}")
    
    def get_cached_media_item(self, provider: str, item_id: str) -> Optional[MediaItem]:
        """Retrieve cached media item if valid."""
        cache_key = self._generate_cache_key(f"{provider}_{item_id}")
        cache_file = self.metadata_dir / f"{cache_key}.json"
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            return MediaItem(**cache_data["item"])
            
        except Exception as e:
            print(f"Warning: Failed to load cached media item: {e}")
            return None
    
    def get_cached_file_path(self, item: MediaItem, size: str = "medium") -> Optional[str]:
        """Get path to cached file if it exists and is valid."""
        filename = f"{item.provider}_{item.id}_{size}.jpg"
        file_path = self.files_dir / filename
        
        if self._is_cache_valid(file_path):
            return str(file_path)
        return None
    
    def cache_file_path(self, item: MediaItem, size: str = "medium") -> str:
        """Get path where file should be cached."""
        filename = f"{item.provider}_{item.id}_{size}.jpg"
        return str(self.files_dir / filename)
    
    def cleanup_old_cache(self) -> None:
        """Remove expired cache files."""
        current_time = time.time()
        max_age = self.ttl_hours * 3600
        
        for cache_dir in [self.metadata_dir, self.files_dir, self.search_dir]:
            for cache_file in cache_dir.glob("*"):
                if cache_file.is_file():
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > max_age:
                        try:
                            cache_file.unlink()
                        except Exception as e:
                            print(f"Warning: Failed to delete expired cache file {cache_file}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "metadata_files": len(list(self.metadata_dir.glob("*.json"))),
            "cached_files": len(list(self.files_dir.glob("*"))),
            "search_cache_files": len(list(self.search_dir.glob("*.json"))),
            "total_size_mb": 0
        }
        
        # Calculate total cache size
        total_size = 0
        for cache_dir in [self.metadata_dir, self.files_dir, self.search_dir]:
            for file_path in cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        
        stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        return stats
