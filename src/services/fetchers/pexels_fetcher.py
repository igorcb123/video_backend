"""Pexels API media fetcher implementation."""

import requests
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_fetcher import BaseMediaFetcher, MediaItem, SearchResult
from .key_manager import PexelsAPIKeyManager


class PexelsFetcher(BaseMediaFetcher):
    """Pexels API implementation for media fetching with multiple API key rotation."""
    
    def __init__(self, api_keys: Optional[str] = None):
        """
        Initialize Pexels fetcher with API key management.
        
        Args:
            api_keys: Comma-separated API keys or single key. 
                     If None, reads from PEXELS_API_KEYS environment variable.
        """
        # Get API keys from parameter or environment
        keys_string = api_keys or os.getenv("PEXELS_API_KEYS", "")
        
        if not keys_string:
            raise ValueError(
                "Pexels API keys are required. "
                "Set PEXELS_API_KEYS environment variable with comma-separated keys."
            )
        
        # Parse and clean keys
        keys = [k.strip() for k in keys_string.split(",") if k.strip()]
        if not keys:
            raise ValueError("No valid Pexels API keys found.")
            
        self.key_manager = PexelsAPIKeyManager(keys)
        self.base_url_photos = "https://api.pexels.com/v1"
        self.base_url_videos = "https://api.pexels.com/videos"
        self.session = requests.Session()
        
        # Request configuration
        self.per_page = 80
        self.max_retries = 3
        self.request_delay = 1.5
    
    def search(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 15,
        **filters: Any
    ) -> SearchResult:
        """Search for media on Pexels (photos and videos) with automatic API key rotation."""
        media_type = filters.get("media_type", "photo")  # "photo", "video", or "both"
        
        if media_type == "both":
            # Search both photos and videos and combine results
            photo_results = self._search_photos(query, page, per_page // 2, **filters)
            video_results = self._search_videos(query, page, per_page // 2, **filters)
            
            # Combine results
            combined_items = photo_results.items + video_results.items
            total_results = photo_results.total_results + video_results.total_results
            
            return SearchResult(
                items=combined_items[:per_page],
                total_results=total_results,
                page=page,
                per_page=per_page,
                total_pages=total_results // per_page + 1,
                has_next=page < (total_results // per_page + 1)
            )
        elif media_type == "video":
            return self._search_videos(query, page, per_page, **filters)
        else:
            return self._search_photos(query, page, per_page, **filters)
    
    def _search_photos(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 15,
        **filters: Any
    ) -> SearchResult:
        """Search for photos on Pexels with automatic API key rotation."""
        params = {
            "query": query,
            "page": page,
            "per_page": min(per_page, self.per_page)  # Pexels max is 80
        }
        
        # Add supported filters for photos
        if "orientation" in filters:
            params["orientation"] = filters["orientation"]  # landscape, portrait, square
        if "size" in filters:
            params["size"] = filters["size"]  # large, medium, small
        if "color" in filters:
            params["color"] = filters["color"]  # red, orange, yellow, green, etc.
        if "locale" in filters:
            params["locale"] = filters["locale"]  # en-US, pt-BR, es-ES, etc.
        
        url = f"{self.base_url_photos}/search"
        
        # Retry logic with API key rotation
        for attempt in range(1, self.max_retries + 1):
            try:
                # Get next available API key
                api_key = self.key_manager.get_next_key()
                headers = {"Authorization": api_key}
                
                # Add request delay to avoid rate limiting
                time.sleep(self.request_delay)
                
                response = self.session.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # Convert Pexels response to our format
                items = []
                for photo in data.get("photos", []):
                    # Get the best quality image URL
                    src = photo.get("src", {})
                    download_url = (
                        src.get("original") or 
                        src.get("large2x") or 
                        src.get("large") or 
                        src.get("medium")
                    )
                    
                    item = MediaItem(
                        id=str(photo.get("id", "")),
                        url=photo.get("url", ""),
                        download_url=download_url,
                        title=f"Photo by {photo.get('photographer', 'Unknown')}",
                        description=photo.get("alt", ""),
                        tags=[query],  # Pexels doesn't provide tags, use search query
                        width=photo.get("width", 0),
                        height=photo.get("height", 0),
                        photographer=photo.get("photographer"),
                        photographer_url=photo.get("photographer_url"),
                        provider="Pexels",
                        media_type="photo"
                    )
                    items.append(item)
                
                return SearchResult(
                    items=items,
                    total_results=data.get("total_results", len(items)),
                    page=page,
                    per_page=per_page,
                    total_pages=data.get("total_results", len(items)) // per_page + 1,
                    has_next=page < (data.get("total_results", len(items)) // per_page + 1)
                )
                
            except requests.RequestException as e:
                logging.warning(f"[Attempt {attempt}] Pexels Photos API error for '{query}': {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logging.error(f"All {self.max_retries} attempts failed for Pexels photos query '{query}'")
                    
            except RuntimeError as e:
                # All API keys exhausted
                logging.error(f"All Pexels API keys exhausted: {e}")
                break
        
        # Return empty result if all attempts failed
        return SearchResult(items=[], total_results=0, page=page, per_page=per_page, total_pages=0, has_next=False)
    
    def _search_videos(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 15,
        **filters: Any
    ) -> SearchResult:
        """Search for videos on Pexels with automatic API key rotation."""
        params = {
            "query": query,
            "page": page,
            "per_page": min(per_page, self.per_page)  # Pexels max is 80
        }
        
        # Add supported filters for videos
        if "orientation" in filters:
            params["orientation"] = filters["orientation"]  # landscape, portrait, square
        if "size" in filters:
            params["size"] = filters["size"]  # large (4K), medium (Full HD), small (HD)
        if "locale" in filters:
            params["locale"] = filters["locale"]  # en-US, pt-BR, es-ES, etc.
        if "min_width" in filters:
            params["min_width"] = filters["min_width"]
        if "min_height" in filters:
            params["min_height"] = filters["min_height"]
        if "min_duration" in filters:
            params["min_duration"] = filters["min_duration"]
        if "max_duration" in filters:
            params["max_duration"] = filters["max_duration"]
        
        url = f"{self.base_url_videos}/search"
        
        # Retry logic with API key rotation
        for attempt in range(1, self.max_retries + 1):
            try:
                # Get next available API key
                api_key = self.key_manager.get_next_key()
                headers = {"Authorization": api_key}
                
                # Add request delay to avoid rate limiting
                time.sleep(self.request_delay)
                
                response = self.session.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # Convert Pexels video response to our format
                items = []
                for video in data.get("videos", []):
                    # Get video files with different qualities
                    video_files = []
                    best_quality_url = ""
                    
                    for vf in video.get("video_files", []):
                        video_file_info = {
                            "id": vf.get("id"),
                            "quality": vf.get("quality"),  # hd, sd, hls
                            "file_type": vf.get("file_type", "video/mp4"),
                            "width": vf.get("width"),
                            "height": vf.get("height"),
                            "fps": vf.get("fps"),
                            "link": vf.get("link")
                        }
                        video_files.append(video_file_info)
                        
                        # Select best quality for main download URL
                        if vf.get("quality") == "hd" and not best_quality_url:
                            best_quality_url = vf.get("link", "")
                        elif not best_quality_url and vf.get("link"):
                            best_quality_url = vf.get("link", "")
                    
                    # Get preview images/thumbnails
                    preview_images = []
                    for vp in video.get("video_pictures", []):
                        preview_images.append(vp.get("picture", ""))
                    
                    # Get user/creator info
                    user = video.get("user", {})
                    photographer = user.get("name", "Unknown")
                    photographer_url = user.get("url", "")
                    
                    item = MediaItem(
                        id=str(video.get("id", "")),
                        url=video.get("url", ""),
                        download_url=best_quality_url,
                        title=f"Video by {photographer}",
                        description=f"Duration: {video.get('duration', 0)}s",
                        tags=video.get("tags", [query]),  # Use tags if available, otherwise query
                        width=video.get("width", 0),
                        height=video.get("height", 0),
                        photographer=photographer,
                        photographer_url=photographer_url,
                        provider="Pexels",
                        media_type="video",
                        duration=video.get("duration", 0),
                        video_files=video_files,
                        preview_images=preview_images,
                        thumbnail_url=video.get("image", "")  # Main thumbnail
                    )
                    items.append(item)
                
                return SearchResult(
                    items=items,
                    total_results=data.get("total_results", len(items)),
                    page=page,
                    per_page=per_page,
                    total_pages=data.get("total_results", len(items)) // per_page + 1,
                    has_next=page < (data.get("total_results", len(items)) // per_page + 1)
                )
                
            except requests.RequestException as e:
                logging.warning(f"[Attempt {attempt}] Pexels Videos API error for '{query}': {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logging.error(f"All {self.max_retries} attempts failed for Pexels videos query '{query}'")
                    
            except RuntimeError as e:
                # All API keys exhausted
                logging.error(f"All Pexels API keys exhausted: {e}")
                break
        
        # Return empty result if all attempts failed
        return SearchResult(items=[], total_results=0, page=page, per_page=per_page, total_pages=0, has_next=False)
    
    def get_item(self, item_id: str, media_type: str = "photo") -> MediaItem:
        """Get a specific photo or video by ID from Pexels."""
        if media_type == "video":
            return self._get_video(item_id)
        else:
            return self._get_photo(item_id)
    
    def _get_photo(self, item_id: str) -> MediaItem:
        """Get a specific photo by ID from Pexels."""
        try:
            # Get next available API key
            api_key = self.key_manager.get_next_key()
            headers = {"Authorization": api_key}
            
            response = self.session.get(f"{self.base_url_photos}/photos/{item_id}", headers=headers)
            response.raise_for_status()
            photo = response.json()
            
            # Convert to MediaItem format
            src = photo.get("src", {})
            download_url = (
                src.get("original") or 
                src.get("large2x") or 
                src.get("large") or 
                src.get("medium")
            )
            
            return MediaItem(
                id=str(photo.get("id", "")),
                url=photo.get("url", ""),
                download_url=download_url,
                title=f"Photo by {photo.get('photographer', 'Unknown')}",
                description=photo.get("alt", ""),
                tags=[],
                width=photo.get("width", 0),
                height=photo.get("height", 0),
                photographer=photo.get("photographer"),
                photographer_url=photo.get("photographer_url"),
                provider="Pexels",
                media_type="photo"
            )
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get Pexels photo {item_id}: {str(e)}")
        except RuntimeError as e:
            raise RuntimeError(f"API keys exhausted while getting photo {item_id}: {str(e)}")
    
    def _get_video(self, item_id: str) -> MediaItem:
        """Get a specific video by ID from Pexels."""
        try:
            # Get next available API key
            api_key = self.key_manager.get_next_key()
            headers = {"Authorization": api_key}
            
            response = self.session.get(f"{self.base_url_videos}/videos/{item_id}", headers=headers)
            response.raise_for_status()
            video = response.json()
            
            # Process video files
            video_files = []
            best_quality_url = ""
            
            for vf in video.get("video_files", []):
                video_file_info = {
                    "id": vf.get("id"),
                    "quality": vf.get("quality"),
                    "file_type": vf.get("file_type", "video/mp4"),
                    "width": vf.get("width"),
                    "height": vf.get("height"),
                    "fps": vf.get("fps"),
                    "link": vf.get("link")
                }
                video_files.append(video_file_info)
                
                if vf.get("quality") == "hd" and not best_quality_url:
                    best_quality_url = vf.get("link", "")
                elif not best_quality_url and vf.get("link"):
                    best_quality_url = vf.get("link", "")
            
            # Get preview images
            preview_images = []
            for vp in video.get("video_pictures", []):
                preview_images.append(vp.get("picture", ""))
            
            # Get user info
            user = video.get("user", {})
            photographer = user.get("name", "Unknown")
            photographer_url = user.get("url", "")
            
            return MediaItem(
                id=str(video.get("id", "")),
                url=video.get("url", ""),
                download_url=best_quality_url,
                title=f"Video by {photographer}",
                description=f"Duration: {video.get('duration', 0)}s",
                tags=video.get("tags", []),
                width=video.get("width", 0),
                height=video.get("height", 0),
                photographer=photographer,
                photographer_url=photographer_url,
                provider="Pexels",
                media_type="video",
                duration=video.get("duration", 0),
                video_files=video_files,
                preview_images=preview_images,
                thumbnail_url=video.get("image", "")
            )
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get Pexels video {item_id}: {str(e)}")
        except RuntimeError as e:
            raise RuntimeError(f"API keys exhausted while getting video {item_id}: {str(e)}")
    
    def download_item(self, item: MediaItem, output_path: str, quality: str = "best") -> str:
        """Download a photo or video from Pexels."""
        try:
            # Create output directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            download_url = item.download_url
            
            # For videos, allow quality selection
            if item.media_type == "video" and item.video_files:
                download_url = self._select_video_quality(item.video_files, quality)
                if not download_url:
                    download_url = item.download_url  # Fallback to default
            
            # Download the media
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return output_path
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download {item.media_type}: {str(e)}")
        except IOError as e:
            raise RuntimeError(f"Failed to save {item.media_type} to {output_path}: {str(e)}")
    
    def _select_video_quality(self, video_files: List[Dict[str, Any]], quality: str) -> str:
        """Select the appropriate video quality URL based on preference."""
        if not video_files:
            return ""
        
        # Define quality preference order
        quality_preferences = {
            "best": ["hd", "sd", "hls"],
            "hd": ["hd"],
            "sd": ["sd"],
            "worst": ["sd", "hd", "hls"]
        }
        
        preferences = quality_preferences.get(quality, ["hd", "sd", "hls"])
        
        # Find the best matching quality
        for pref in preferences:
            for vf in video_files:
                if vf.get("quality") == pref and vf.get("link"):
                    return vf.get("link")
        
        # Fallback to first available
        for vf in video_files:
            if vf.get("link"):
                return vf.get("link")
        
        return ""
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API key usage statistics."""
        return self.key_manager.get_usage_stats()
    
    def close(self):
        """Close the fetcher and clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()
    
    @property
    def name(self) -> str:
        return "pexels"
    
    @property
    def supported_formats(self) -> List[str]:
        """List of supported file formats."""
        return ["jpg", "jpeg", "mp4", "mov"]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get fetcher capabilities."""
        return {
            "name": self.name,
            "supported_formats": ["jpg", "jpeg", "mp4", "mov"],
            "supported_media_types": ["photo", "video", "both"],
            "max_per_page": self.per_page,
            "supports_filters": True,
            "available_filters": {
                "photo": [
                    "orientation",  # landscape, portrait, square
                    "size",        # large (24MP), medium (12MP), small (4MP)
                    "color",       # red, orange, yellow, green, etc.
                    "locale"       # en-US, pt-BR, es-ES, etc.
                ],
                "video": [
                    "orientation",     # landscape, portrait, square
                    "size",           # large (4K), medium (Full HD), small (HD)
                    "locale",         # en-US, pt-BR, es-ES, etc.
                    "min_width",      # minimum width in pixels
                    "min_height",     # minimum height in pixels
                    "min_duration",   # minimum duration in seconds
                    "max_duration"    # maximum duration in seconds
                ]
            },
            "video_qualities": ["hd", "sd", "hls"],
            "api_keys_count": len(self.key_manager.keys),
            "rate_limit": f"{self.key_manager.max_calls} calls per {self.key_manager.period.total_seconds()} seconds"
        }
    
    # Convenience methods for specific media types
    def search_photos(self, query: str, page: int = 1, per_page: int = 15, **filters: Any) -> SearchResult:
        """Search specifically for photos."""
        filters["media_type"] = "photo"
        return self.search(query, page, per_page, **filters)
    
    def search_videos(self, query: str, page: int = 1, per_page: int = 15, **filters: Any) -> SearchResult:
        """Search specifically for videos."""
        filters["media_type"] = "video"
        return self.search(query, page, per_page, **filters)
    
    def get_video_qualities(self, item: MediaItem) -> List[Dict[str, Any]]:
        """Get available video qualities for a video item."""
        if item.media_type != "video" or not item.video_files:
            return []
        return item.video_files
    
    def get_best_video_url(self, item: MediaItem, preferred_quality: str = "hd") -> str:
        """Get the best video URL for a specific quality preference."""
        if item.media_type != "video" or not item.video_files:
            return item.download_url
        return self._select_video_quality(item.video_files, preferred_quality) or item.download_url
