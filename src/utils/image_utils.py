"""
Utility functions for image downloading and processing.
"""
import time
import io
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from PIL import Image


class ImageDownloader:
    """Utility class for downloading images concurrently."""
    
    def __init__(self, timeout: int = 10, max_retries: int = 2, max_workers: int = 8):
        """
        Initialize image downloader.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            max_workers: Maximum number of concurrent workers
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_workers = max_workers
    
    def download_single_image(self, url: str, image_size: tuple = (224, 224)) -> Optional[Image.Image]:
        """
        Download a single image from URL with retries and error handling.
        
        Args:
            url: Image URL
            image_size: Target size for resizing
            
        Returns:
            PIL Image or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers=headers,
                    stream=True
                )
                response.raise_for_status()
                
                # Verify content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'webp']):
                    raise ValueError(f"Content type not supported: {content_type}")
                
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                image = image.resize(image_size, Image.LANCZOS)
                
                return image
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Failed to download {url} after {self.max_retries} attempts: {str(e)}")
                    return None
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return None
    
    def download_images_concurrent(self, urls: List[str], image_size: tuple = (224, 224)) -> Dict[str, Optional[Image.Image]]:
        """
        Download multiple images concurrently.
        
        Args:
            urls: List of image URLs
            image_size: Target size for resizing
            
        Returns:
            Dictionary with URL -> Image or None
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.download_single_image, url, image_size): url 
                for url in urls
            }
            
            # Collect results
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    results[url] = None
        
        return results


class ImageProcessor:
    """Utility class for image processing operations."""
    
    @staticmethod
    def validate_images(downloaded_images: Dict[str, Optional[Image.Image]], 
                       original_urls: List[str]) -> tuple:
        """
        Separate valid images from failed downloads.
        
        Args:
            downloaded_images: Dict with URL -> Image or None
            original_urls: Original list of URLs in order
            
        Returns:
            Tuple of (valid_images, valid_urls, failed_urls)
        """
        valid_images = []
        valid_urls = []
        failed_urls = []
        
        for url in original_urls:
            img = downloaded_images.get(url)
            if img is not None:
                valid_images.append(img)
                valid_urls.append(url)
            else:
                failed_urls.append(url)
        
        return valid_images, valid_urls, failed_urls
    
    @staticmethod
    def create_error_result(url: str, error_message: str = "Failed to download image") -> Dict:
        """
        Create error result structure for failed downloads.
        
        Args:
            url: Image URL that failed
            error_message: Error description
            
        Returns:
            Error result dictionary
        """
        return {
            "image": url,
            "error": error_message,
            "state": "error",
            "score_positive_raw": 0.0,
            "score_positive_pct": 0.0,
            "score_negative_raw": 0.0,
            "score_negative_pct": 0.0,
            "negatives_triggered": [],
            "time_ms": 0.0
        }
