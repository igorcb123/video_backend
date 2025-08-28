"""
Example usage of the ImageFilterCLIP service.
"""
import sys
from pathlib import Path
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.image_filter_class import ImageFilterCLIP


def main():
    """Demonstrate ImageFilterCLIP usage."""
    print("🖼️  ImageFilterCLIP Service Demo")
    print("=" * 50)
    
    # Custom configuration for better performance
    custom_config = {
        "positive_threshold": 0.30,
        "negative_threshold": 0.22,
        "batch_size": 16,
        "max_workers": 10,
        "timeout": 15,  # Longer timeout for real usage
        "max_retries": 2
    }
    
    # Initialize filter
    print("Initializing ImageFilterCLIP service...")
    filter_service = ImageFilterCLIP(custom_config)
    
    # Example URLs (replace with real URLs for actual testing)
    image_urls = [
        "https://images.pexels.com/photos/7210673/pexels-photo-7210673.jpeg",
        "https://images.pexels.com/photos/17507248/pexels-photo-17507248.jpeg",
        "https://images.pexels.com/photos/16549837/pexels-photo-16549837.jpeg",
        "https://images.pexels.com/photos/15356250/pexels-photo-15356250.jpeg"
    ]
    
    description = "A small dog with a ball"
    
    print(f"\nFiltering {len(image_urls)} images with description: '{description}'")
    print("This is a demo - uncomment the next lines for actual processing:")
    
    # Uncomment these lines to actually process images:
    # results = filter_service.filter_images(
    #     description=description,
    #     image_urls=image_urls
    # )
    # 
    # # Display results
    # print("\n📊 Results Summary:")
    # stats = results.get("statistics", {})
    # print(f"Total images: {stats.get('total', 0)}")
    # print(f"Valid matches: {stats.get('valid', 0)}")
    # print(f"No matches: {stats.get('no_match', 0)}")
    # print(f"Censored: {stats.get('censored', 0)}")
    # print(f"Errors: {stats.get('errors', 0)}")
    # 
    # print(f"\n⏱️ Performance:")
    # print(f"Processing time: {results.get('processing_time_seconds', 0):.2f}s")
    # print(f"Download time: {results.get('download_time_seconds', 0):.2f}s")
    # 
    # # Print full results (formatted)
    # print("\n📋 Full Results:")
    # print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # Display current configuration
    print("\n⚙️ Current Configuration:")
    config = filter_service.get_config()
    for key, value in config.items():
        if isinstance(value, list) and len(value) > 3:
            print(f"  {key}: [{len(value)} items]")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Demo completed!")
    print("💡 Tip: Uncomment the processing lines above to test with real images.")


if __name__ == "__main__":
    main()
