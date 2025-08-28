"""
Tests for the ImageFilterCLIP service.
"""
import sys
from pathlib import Path
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.image_filter_class import ImageFilterCLIP, ImageFilterConfig


def test_config_initialization():
    """Test configuration initialization and updates."""
    print("=== Test Config Initialization ===")
    
    # Test default config
    config = ImageFilterConfig()
    assert config.model_name == "openai/clip-vit-base-patch32"
    assert config.positive_threshold == 0.28
    assert config.negative_threshold == 0.25
    print("✅ Default config initialized correctly")
    
    # Test config update
    config.update(positive_threshold=0.35, batch_size=8)
    assert config.positive_threshold == 0.35
    assert config.batch_size == 8
    print("✅ Config update working correctly")
    
    # Test invalid config key
    try:
        config.update(invalid_key="value")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✅ Config validation working: {e}")
    
    print()


def test_service_initialization():
    """Test service initialization with different configurations."""
    print("=== Test Service Initialization ===")
    
    # Test default initialization
    service = ImageFilterCLIP()
    assert service.config.model_name == "openai/clip-vit-base-patch32"
    print("✅ Default service initialization working")
    
    # Test custom configuration
    custom_config = {
        "positive_threshold": 0.30,
        "negative_threshold": 0.22,
        "batch_size": 16,
        "max_workers": 4
    }
    service_custom = ImageFilterCLIP(custom_config)
    assert service_custom.config.positive_threshold == 0.30
    assert service_custom.config.batch_size == 16
    print("✅ Custom config initialization working")
    
    print()


def test_config_methods():
    """Test configuration utility methods."""
    print("=== Test Config Methods ===")
    
    service = ImageFilterCLIP()
    
    # Test get_config
    config_dict = service.get_config()
    assert isinstance(config_dict, dict)
    assert "model_name" in config_dict
    print("✅ get_config working")
    
    # Test update_config
    original_threshold = service.config.positive_threshold
    service.update_config(positive_threshold=0.35)
    assert service.config.positive_threshold == 0.35
    assert service.config.positive_threshold != original_threshold
    print("✅ update_config working")
    
    # Test clear_cache
    service.clear_cache()
    assert len(service._text_embeddings_cache) == 0
    print("✅ clear_cache working")
    
    print()


def test_empty_image_urls():
    """Test filter with empty image URLs list."""
    print("=== Test Empty Image URLs ===")
    
    service = ImageFilterCLIP()
    results = service.filter_images("test description", [])
    
    assert results["description"] == "test description"
    assert results["results"] == []
    assert "model" in results
    assert "positive_threshold" in results
    assert "negative_threshold" in results
    print("✅ Empty URLs handling working")
    
    print()


def test_performance_example():
    """Test with example URLs (demonstration only - won't actually download in CI)."""
    print("=== Test Performance Example ===")
    
    # Custom config for better performance
    custom_config = {
        "positive_threshold": 0.30,
        "negative_threshold": 0.22,
        "batch_size": 16,
        "max_workers": 10,
        "timeout": 5,  # Shorter timeout for tests
        "max_retries": 1  # Fewer retries for tests
    }
    
    # Initialize filter
    filter_instance = ImageFilterCLIP(custom_config)
    
    # Example URLs (these are real URLs but we won't actually download them in tests)
    image_urls = [
        "https://images.pexels.com/photos/7210673/pexels-photo-7210673.jpeg",
        "https://images.pexels.com/photos/17507248/pexels-photo-17507248.jpeg",
        "https://images.pexels.com/photos/16549837/pexels-photo-16549837.jpeg",
        "https://images.pexels.com/photos/15356250/pexels-photo-15356250.jpeg"
    ]
    
    print(f"Example configuration: {filter_instance.get_config()}")
    print(f"Would process {len(image_urls)} images with description 'A small dog with a ball'")
    
    # In a real test, you would call:
    # results = filter_instance.filter_images(
    #     description="A small dog with a ball",
    #     image_urls=image_urls
    # )
    # print(json.dumps(results, indent=2, ensure_ascii=False))
    
    print("✅ Example setup working (actual processing skipped for CI)")
    print()


def run_all_tests():
    """Run all test functions."""
    print("🧪 Running ImageFilterCLIP Service Tests\n")
    
    test_config_initialization()
    test_service_initialization()
    test_config_methods()
    test_empty_image_urls()
    test_performance_example()
    
    print("🎉 All tests completed successfully!")


if __name__ == "__main__":
    run_all_tests()
