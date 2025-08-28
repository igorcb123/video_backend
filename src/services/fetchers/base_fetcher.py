"""Base fetcher interface for media providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MediaItem:
    """Represents a media item from any provider."""
    id: str
    url: str
    download_url: str
    title: str
    description: Optional[str] = None
    tags: List[str] = None
    width: int = 0
    height: int = 0
    file_size: Optional[int] = None
    photographer: Optional[str] = None
    photographer_url: Optional[str] = None
    provider: str = ""
    
    # Video-specific fields
    media_type: str = "photo"  # "photo" or "video"
    duration: Optional[int] = None  # Duration in seconds for videos
    video_files: Optional[List[Dict[str, Any]]] = None  # Different video qualities/formats
    preview_images: Optional[List[str]] = None  # Video thumbnail images
    thumbnail_url: Optional[str] = None  # Main thumbnail/preview image
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.video_files is None:
            self.video_files = []
        if self.preview_images is None:
            self.preview_images = []


@dataclass
class SearchResult:
    """Represents search results from a media provider."""
    items: List[MediaItem]
    total_results: int
    page: int
    per_page: int
    total_pages: int = 0
    has_next: bool = False


class BaseMediaFetcher(ABC):
    """Base interface for media fetchers."""
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 15,
        **filters: Any
    ) -> SearchResult:
        """
        Search for media items.
        
        Args:
            query: Search query string
            page: Page number (1-based)
            per_page: Number of results per page
            **filters: Additional filters (orientation, size, color, etc.)
            
        Returns:
            SearchResult object with media items
            
        Raises:
            RuntimeError: If search fails
        """
        pass
    
    @abstractmethod
    def get_item(self, item_id: str) -> MediaItem:
        """
        Get a specific media item by ID.
        
        Args:
            item_id: The item ID
            
        Returns:
            MediaItem object
            
        Raises:
            RuntimeError: If item not found or fetch fails
        """
        pass
    
    @abstractmethod
    def download_item(self, item: MediaItem, output_path: str, size: str = "medium") -> str:
        """
        Download a media item to local storage.
        
        Args:
            item: MediaItem to download
            output_path: Local path to save the file
            size: Size variant to download (small, medium, large, original)
            
        Returns:
            Path to the downloaded file
            
        Raises:
            RuntimeError: If download fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the media provider."""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """List of supported file formats."""
        pass
