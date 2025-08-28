"""Test script to check if Google video search is feasible."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def test_google_video_search():
    """Test if Google video search is technically feasible."""
    
    print("🎬 Testing Google Video Search Feasibility")
    print("=" * 50)
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Test 1: Basic video search
        video_url = 'https://www.google.com/search?q=ocean+waves&tbm=vid'
        print(f"🔍 Testing video search URL: {video_url}")
        driver.get(video_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Check page title
        title = driver.title
        print(f"📄 Page title: {title}")
        
        # Test 2: Look for video result containers
        video_selectors = [
            'div[data-ved]',  # General Google result containers
            '.g',             # Google result class
            '.rc',            # Google result content
            'a[href*="youtube.com"]',  # YouTube links
            'a[href*="vimeo.com"]',    # Vimeo links
            'a[href*="dailymotion.com"]',  # Dailymotion links
            '[data-ved][href*="watch"]'  # Video watch links
        ]
        
        total_elements = 0
        for selector in video_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"   📊 {selector}: {len(elements)} elements")
            total_elements += len(elements)
        
        # Test 3: Look for video-specific elements
        video_indicators = driver.find_elements(By.CSS_SELECTOR, '[aria-label*="video"], [title*="video"], .video, [data-ved*="video"]')
        print(f"🎥 Video indicators found: {len(video_indicators)}")
        
        # Test 4: Check for thumbnail images (videos usually have thumbnails)
        thumbnails = driver.find_elements(By.CSS_SELECTOR, 'img[src*="i.ytimg.com"], img[src*="vimeocdn.com"]')
        print(f"🖼️ Video thumbnails found: {len(thumbnails)}")
        
        # Test 5: Look for duration indicators
        durations = driver.find_elements(By.CSS_SELECTOR, '[aria-label*="duration"], .duration, [title*="duration"]')
        print(f"⏱️ Duration indicators: {len(durations)}")
        
        # Test 6: Check for video platform links
        youtube_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="youtube.com"]')
        vimeo_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="vimeo.com"]')
        
        print(f"🔗 Platform links found:")
        print(f"   📺 YouTube: {len(youtube_links)}")
        print(f"   🎬 Vimeo: {len(vimeo_links)}")
        
        # Analysis
        print(f"\n📈 Analysis:")
        print(f"   Total result elements: {total_elements}")
        
        if total_elements > 5 and (youtube_links or vimeo_links or video_indicators):
            print("   ✅ Google video search appears FEASIBLE")
            print("   ✅ Video results are being returned")
            print("   ✅ Platform links are available")
            
            # Check if we can extract video URLs
            if youtube_links:
                first_youtube = youtube_links[0]
                href = first_youtube.get_attribute('href')
                print(f"   🔗 Sample YouTube URL: {href[:80]}...")
            
            return True
        else:
            print("   ❌ Google video search may NOT be feasible")
            print("   ❌ Insufficient video results or indicators found")
            return False
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    finally:
        driver.quit()

def analyze_video_download_feasibility():
    """Analyze if video downloads are possible."""
    print(f"\n🔄 Video Download Feasibility Analysis:")
    print("=" * 50)
    
    print("📋 Considerations for video downloads:")
    print("   ✅ YouTube videos: Possible with yt-dlp library")
    print("   ✅ Vimeo videos: Possible with yt-dlp library")
    print("   ✅ Direct MP4 links: Directly downloadable")
    print("   ⚠️ Embedded videos: May require special handling")
    print("   ❌ DRM-protected content: Not downloadable")
    
    print(f"\n💡 Recommended approach:")
    print("   1. Extract video URLs from Google search results")
    print("   2. Use yt-dlp for YouTube/Vimeo downloads")
    print("   3. Use requests for direct video file links")
    print("   4. Filter for short videos suitable as B-rolls")
    
    # Check if yt-dlp is available
    try:
        import yt_dlp
        print("   ✅ yt-dlp library is available")
        return True
    except ImportError:
        print("   ⚠️ yt-dlp library not installed (pip install yt-dlp)")
        return False

if __name__ == "__main__":
    search_feasible = test_google_video_search()
    download_feasible = analyze_video_download_feasibility()
    
    print(f"\n🎯 Final Assessment:")
    if search_feasible and download_feasible:
        print("   ✅ Google video search with download capability is FEASIBLE")
        print("   🚀 Can proceed with implementation")
    elif search_feasible:
        print("   ⚠️ Google video search is feasible but downloads need yt-dlp")
        print("   📦 Install yt-dlp to enable video downloads")
    else:
        print("   ❌ Google video search implementation may be challenging")
        print("   🔄 Consider alternative approaches or video sources")
