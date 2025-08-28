"""Demo script to test Pexels fetcher with video support."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from services.fetchers.pexels_fetcher import PexelsFetcher


def demo_pexels_videos():
    """Demonstrate Pexels video fetching capabilities."""
    
    # Check if API key is available
    api_key = os.getenv("PEXELS_API_KEYS")
    if not api_key:
        print("❌ PEXELS_API_KEYS environment variable not set")
        print("Please set your Pexels API key to test video functionality")
        return
    
    print("🎬 Testing Pexels Fetcher with Video Support")
    print("=" * 50)
    
    try:
        # Initialize fetcher
        fetcher = PexelsFetcher()
        
        # Test 1: Get capabilities
        print("\n1️⃣ Fetcher Capabilities:")
        capabilities = fetcher.get_capabilities()
        print(f"   📋 Supported formats: {capabilities['supported_formats']}")
        print(f"   📋 Media types: {capabilities['supported_media_types']}")
        print(f"   📋 Video qualities: {capabilities['video_qualities']}")
        
        # Test 2: Search for photos only
        print("\n2️⃣ Searching for photos only (query: 'nature'):")
        photo_results = fetcher.search_photos("nature", per_page=3)
        print(f"   📸 Found {photo_results.total_results} photos")
        for i, item in enumerate(photo_results.items[:2]):
            print(f"   [{i+1}] {item.title} - {item.width}x{item.height}px")
            print(f"       🔗 {item.url}")
        
        # Test 3: Search for videos only
        print("\n3️⃣ Searching for videos only (query: 'ocean'):")
        video_results = fetcher.search_videos("ocean", per_page=3)
        print(f"   🎥 Found {video_results.total_results} videos")
        for i, item in enumerate(video_results.items[:2]):
            print(f"   [{i+1}] {item.title} - {item.width}x{item.height}px - {item.duration}s")
            print(f"       🔗 {item.url}")
            print(f"       🖼️ Thumbnail: {item.thumbnail_url}")
            
            # Show video qualities
            qualities = fetcher.get_video_qualities(item)
            print(f"       📹 Available qualities:")
            for q in qualities[:3]:  # Show first 3 qualities
                print(f"          - {q['quality'].upper()}: {q['width']}x{q['height']}px")
        
        # Test 4: Search both photos and videos
        print("\n4️⃣ Searching for both photos and videos (query: 'sunset'):")
        mixed_results = fetcher.search("sunset", per_page=4, media_type="both")
        print(f"   🎯 Found {mixed_results.total_results} total items")
        for i, item in enumerate(mixed_results.items):
            media_icon = "📸" if item.media_type == "photo" else "🎥"
            duration_info = f" - {item.duration}s" if item.media_type == "video" else ""
            print(f"   [{i+1}] {media_icon} {item.title} - {item.width}x{item.height}px{duration_info}")
        
        # Test 5: Get specific video item
        if video_results.items:
            print("\n5️⃣ Getting specific video details:")
            first_video = video_results.items[0]
            video_detail = fetcher.get_item(first_video.id, media_type="video")
            print(f"   🎥 Video ID: {video_detail.id}")
            print(f"   ⏱️ Duration: {video_detail.duration}s")
            print(f"   📹 Available qualities: {len(video_detail.video_files)}")
            print(f"   🖼️ Preview images: {len(video_detail.preview_images)}")
            
            # Show best quality URL
            best_hd_url = fetcher.get_best_video_url(video_detail, "hd")
            print(f"   🎬 Best HD URL: {best_hd_url[:80]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        fetcher.close()


if __name__ == "__main__":
    demo_pexels_videos()
