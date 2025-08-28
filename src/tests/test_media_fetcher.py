"""Tests for MediaFetcherService functionality."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.media_fetcher_orchestrator import MediaFetcherService
from services.fetchers.base_fetcher import MediaItem, SearchResult
from services.media_cache import MediaCache


class TestMediaFetcherService:
    """Test cases for MediaFetcherService."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test service initialization with different providers."""
        # Test default provider
        service = MediaFetcherService()
        assert service.provider_name == "pexels"
        assert service.fetcher.name == "pexels"
        
        # Test explicit provider
        service = MediaFetcherService(provider="pexels")
        assert service.provider_name == "pexels"
    
    def test_service_initialization_invalid_provider(self):
        """Test service initialization with invalid provider."""
        with pytest.raises(ValueError, match="Proveedor de medios no soportado"):
            MediaFetcherService(provider="invalid")
    
    @patch.dict(os.environ, {"PEXELS_API_KEY": "test_key"})
    def test_search_images_with_mock(self):
        """Test image search with mocked API response."""
        # Mock search result
        mock_item = MediaItem(
            id="123",
            url="https://example.com/photo",
            download_url="https://example.com/download",
            title="Test Photo",
            provider="pexels"
        )
        mock_result = SearchResult(
            items=[mock_item],
            total_results=1,
            page=1,
            per_page=15,
            has_next=False
        )
        
        # Create service with mocked fetcher
        service = MediaFetcherService()
        
        with patch.object(service.fetcher, 'search', return_value=mock_result):
            result = service.search_images("test query")
            
            assert len(result.items) == 1
            assert result.items[0].id == "123"
            assert result.items[0].title == "Test Photo"
    
    @patch.dict(os.environ, {"PEXELS_API_KEY": "test_key"})
    def test_get_image_with_mock(self):
        """Test get specific image with mocked API response."""
        mock_item = MediaItem(
            id="456",
            url="https://example.com/photo/456",
            download_url="https://example.com/download/456",
            title="Specific Photo",
            provider="pexels"
        )
        
        service = MediaFetcherService()
        
        with patch.object(service.fetcher, 'get_item', return_value=mock_item):
            result = service.get_image("456")
            
            assert result.id == "456"
            assert result.title == "Specific Photo"
    
    @patch.dict(os.environ, {"PEXELS_API_KEY": "test_key"})
    def test_download_image_with_mock(self):
        """Test image download with mocked implementation."""
        mock_item = MediaItem(
            id="789",
            url="https://example.com/photo/789",
            download_url="https://example.com/download/789",
            title="Download Test",
            provider="pexels"
        )
        
        service = MediaFetcherService()
        expected_path = str(self.temp_dir / "test_image.jpg")
        
        with patch.object(service.fetcher, 'download_item', return_value=expected_path):
            result = service.download_image(mock_item, custom_path=expected_path)
            
            assert result == expected_path
    
    def test_cache_functionality(self):
        """Test cache functionality."""
        cache = MediaCache(self.temp_dir, ttl_hours=1)
        
        # Test cache stats
        stats = cache.get_cache_stats()
        assert "metadata_files" in stats
        assert "cached_files" in stats
        assert "search_cache_files" in stats
        assert "total_size_mb" in stats
    
    @patch.dict(os.environ, {"PEXELS_API_KEY": "test_key"})
    def test_get_provider_info(self):
        """Test provider information."""
        service = MediaFetcherService()
        info = service.get_provider_info()
        
        assert info["name"] == "pexels"
        assert "supported_formats" in info
        assert "cache_enabled" in info
    
    @patch.dict(os.environ, {"PEXELS_API_KEY": "test_key"})
    def test_search_and_download_workflow(self):
        """Test complete search and download workflow."""
        mock_items = [
            MediaItem(
                id=str(i),
                url=f"https://example.com/photo/{i}",
                download_url=f"https://example.com/download/{i}",
                title=f"Photo {i}",
                provider="pexels"
            ) for i in range(3)
        ]
        
        mock_result = SearchResult(
            items=mock_items,
            total_results=3,
            page=1,
            per_page=15,
            has_next=False
        )
        
        service = MediaFetcherService()
        
        # Mock both search and download
        with patch.object(service.fetcher, 'search', return_value=mock_result), \
             patch.object(service.fetcher, 'download_item', side_effect=lambda item, path, size: path):
            
            download_dir = str(self.temp_dir)
            result = service.search_and_download("test", count=2, download_dir=download_dir)
            
            assert len(result) == 2  # Only download 2 even though 3 available


def test_media_item_creation():
    """Test MediaItem creation and validation."""
    item = MediaItem(
        id="test123",
        url="https://example.com/test",
        download_url="https://example.com/download/test",
        title="Test Item"
    )
    
    assert item.id == "test123"
    assert item.tags == []  # Should initialize empty list
    assert item.provider == ""


def test_search_result_creation():
    """Test SearchResult creation."""
    items = [
        MediaItem(
            id="1",
            url="https://example.com/1",
            download_url="https://example.com/download/1",
            title="Item 1"
        )
    ]
    
    result = SearchResult(
        items=items,
        total_results=100,
        page=1,
        per_page=15,
        has_next=True
    )
    
    assert len(result.items) == 1
    assert result.total_results == 100
    assert result.has_next is True


if __name__ == "__main__":
    # Quick manual test
    print("🧪 Running manual tests...")
    
    # Test basic functionality
    try:
        service = MediaFetcherService()
        info = service.get_provider_info()
        print(f"✓ Service initialized: {info}")
        
        cache_stats = service.get_cache_stats()
        print(f"✓ Cache stats: {cache_stats}")
        
        print("✅ Basic tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    print("🏁 Manual test completed")
