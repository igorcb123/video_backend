"""
Google Images scraper implementation using Selenium.
Robust version that avoids base64 images and uses JavaScript to extract URLs.
Based on the robust GoogleImageScraper implementation.
"""

import os
import re
import time
import base64
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urlencode, quote_plus
import urllib.parse
from PIL import Image
import io
from shutil import which

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException, ElementClickInterceptedException,
        StaleElementReferenceException
    )
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

from .base_fetcher import BaseMediaFetcher, MediaItem, SearchResult


class GoogleImagesFetcher(BaseMediaFetcher):
    """Robust Google scraper for images and videos that uses JavaScript for URL extraction."""
    
    def __init__(self, webdriver_path: Optional[str] = None, headless: bool = True):
        """
        Initialize Google scraper for images and videos.
        
        Args:
            webdriver_path: Path to Chrome WebDriver executable
            headless: Whether to run browser in headless mode
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError(
                "Selenium is required for Google scraper. "
                "Install with: pip install selenium webdriver-manager"
            )
        
        self.webdriver_path = webdriver_path
        self.headless = headless
        self.driver = None
        
        # Watermarked domains to avoid
        self.watermark_domains = {
            'media.gettyimages.com', 'shutterstock.com', 'istockphoto.com',
            'dreamstime.com', 'depositphotos.com', 'alamy.com', '123rf.com',
            'bigstockphoto.com', 'fotolia.com', 'canstockphoto.com',
            'vectorstock.com', 'freepik.com', 'adobe.com', 'envato.com',
        }
    
    def _init_driver(self, user_agent=None, chrome_binary=None):
        """Initialize Chrome WebDriver with robust settings."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        if user_agent:
            options.add_argument(f"--user-agent={user_agent}")
        else:
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        
        if chrome_binary:
            options.binary_location = chrome_binary

        # Resolve chromedriver path
        exe_path = None
        if self.webdriver_path:
            cand = self.webdriver_path
            if not os.path.isabs(cand):
                cand = os.path.abspath(cand)
            if os.path.isfile(cand):
                exe_path = cand
            else:
                found = which(self.webdriver_path)
                if found and os.path.isfile(found):
                    exe_path = found

        # Try webdriver_manager if no valid path
        if not exe_path:
            try:
                exe_path = ChromeDriverManager().install()
            except Exception:
                exe_path = None  # Let Selenium Manager handle it

        # Create the driver
        if exe_path:
            driver = webdriver.Chrome(service=Service(exe_path), options=options)
        else:
            driver = webdriver.Chrome(options=options)

        driver.set_window_size(1400, 1050)

        # Handle cookies banner
        try:
            driver.get("https://www.google.com")
            for selector in [
                (By.ID, "W0wltc"),
                (By.CSS_SELECTOR, "button[aria-label*='Aceptar']"),
                (By.CSS_SELECTOR, "button[aria-label*='Acepto']"),
                (By.CSS_SELECTOR, "button[aria-label*='Agree']"),
            ]:
                try:
                    WebDriverWait(driver, 3).until(EC.element_to_be_clickable(selector)).click()
                    break
                except Exception:
                    pass
        except Exception:
            pass

        return driver
    
    @staticmethod
    def _build_google_image_search_url(
        query: str,
        size: str = 'l',
        color: str = None,
        license: str = None
    ) -> str:
        """Build Google Images search URL with filters (simplified)."""
        # Construct tbs parameter
        tbs_parts = []
        if size:
            tbs_parts.append(f"isz:{size}")
        if color:
            tbs_parts.append(f"ic:{color}")
        if license:
            tbs_parts.append(f"sur:{license}")
        tbs_param = ",".join(tbs_parts)

        # URL de Google Imágenes (minimalista)
        base_url = (
            "https://www.google.com/search?"
            f"q={query}&"
            "tbm=isch&source=lnms&"
        )
        if tbs_param:
            base_url += f"tbs={tbs_param}&"
        base_url += "sa=X"
        
        return base_url
    
    @staticmethod
    def _build_google_video_search_url(
        query: str,
        duration: str = None,
        quality: str = None,
        recent: bool = False
    ) -> str:
        """Build Google Videos search URL with filters."""
        # Construct tbs parameter for videos
        tbs_parts = []
        if duration:
            # Video duration filters: short (<4min), medium (4-20min), long (>20min)
            duration_map = {
                'short': 'dur:s',    # < 4 minutes
                'medium': 'dur:m',   # 4-20 minutes  
                'long': 'dur:l'      # > 20 minutes
            }
            if duration in duration_map:
                tbs_parts.append(duration_map[duration])
        
        if quality:
            # Video quality filters
            quality_map = {
                'high': 'hd:1',     # High definition
                'any': ''           # Any quality
            }
            if quality in quality_map and quality_map[quality]:
                tbs_parts.append(quality_map[quality])
        
        if recent:
            tbs_parts.append('qdr:m')  # Recent (past month)
        
        tbs_param = ",".join(tbs_parts)

        # URL de Google Videos
        base_url = (
            "https://www.google.com/search?"
            f"q={query}&"
            "tbm=vid&source=lnms&"
        )
        if tbs_param:
            base_url += f"tbs={tbs_param}&"
        base_url += "sa=X"
        
        return base_url
    
    def _is_watermarked(self, url):
        """Check if URL is from a watermarked domain."""
        if not isinstance(url, str):
            return False
        return any(domain in url for domain in self.watermark_domains)

    def _wait_for_preview_images(self, timeout=10):
        """
        Espera que el panel de previsualización tenga al menos una <img> con src cargado.
        Retorna lista de WebElements (no se usa directamente para leer atributos).
        """
        wait = WebDriverWait(self.driver, timeout)
        CSS = "img.n3VNCb, img.iPVvYb, img.r48jcc, img.pT0Scc, img.H8Rx8c, img.sFlh5c"
        return wait.until(
            lambda d: [e for e in d.find_elements(By.CSS_SELECTOR, CSS) if e.get_attribute("src")]
        )

    def _collect_preview_srcs(self):
        """
        Lee las URLs de las imágenes del panel usando JS (evita StaleElementReference).
        Devuelve lista de strings (o None en posiciones sin URL válida).
        """
        CSS = "img.n3VNCb, img.iPVvYb, img.r48jcc, img.pT0Scc, img.H8Rx8c, img.sFlh5c"
        script = r"""
            const sel = arguments[0];
            const imgs = Array.from(document.querySelectorAll(sel));
            const urls = [];
            for (const img of imgs) {
                let u = null;
                for (const a of ['src','data-src','data-iurl']) {
                    const v = img.getAttribute(a);
                    if (v && v.startsWith('http')) { u = v; break; }
                }
                if (!u) {
                    const ss = img.getAttribute('srcset') || '';
                    for (const part of ss.split(',')) {
                        const uu = part.trim().split(' ')[0];
                        if (uu && uu.startsWith('http')) { u = uu; break; }
                    }
                }
                urls.push(u);
            }
            return urls;
        """
        try:
            return self.driver.execute_script(script, CSS) or []
        except Exception:
            return []

    def _safe_click(self, element):
        """Click con fallback a JS por problemas de interceptación."""
        try:
            element.click()
        except (ElementClickInterceptedException, Exception):
            self.driver.execute_script("arguments[0].click();", element)

    def search(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 10,
        **filters: Any
    ) -> SearchResult:
        """
        Search for images or videos using Google search with robust extraction.
        
        Args:
            query: Search query string
            page: Page number (not directly supported by scraping)
            per_page: Number of items to fetch
            **filters: Search filters including media_type, size, color, duration, etc.
        """
        media_type = filters.get("media_type", "photo")  # "photo", "video", or "both"
        
        if media_type == "both":
            # Search both images and videos and combine results
            photo_results = self._search_images(query, page, per_page // 2, **filters)
            video_results = self._search_videos(query, page, per_page // 2, **filters)
            
            # Combine results
            combined_items = photo_results.items + video_results.items
            total_results = photo_results.total_results + video_results.total_results
            
            return SearchResult(
                items=combined_items[:per_page],
                total_results=total_results,
                page=page,
                per_page=per_page,
                total_pages=1,  # We don't have reliable pagination info
                has_next=len(combined_items) >= per_page
            )
        elif media_type == "video":
            return self._search_videos(query, page, per_page, **filters)
        else:
            return self._search_images(query, page, per_page, **filters)
    
    def _search_images(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 10,
        **filters: Any
    ) -> SearchResult:
        """Search for images using Google Images scraping with robust extraction."""
        if self.driver is None:
            self.driver = self._init_driver()
        
        # Build search URL with filters
        url = self._build_google_image_search_url(
            query=query,
            size=filters.get('size', 'l'),
            color=filters.get('color'),
            license=filters.get('license')
        )
        
        print(f"[INFO] Opening Google Images search: {url}")
        self.driver.get(url)
        
        # Wait for thumbnails to appear
        thumb_css = "img.Q4LuWd, img.YQ4gaf, img.rg_i, img.MiYDnb"
        try:
            WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, thumb_css)))
        except TimeoutException:
            print("[ERR] No thumbnails found. Check your query or selectors.")
            return SearchResult(items=[], total_results=0, page=page, per_page=per_page, has_next=False)

        items = []
        count = 0
        missed_in_row = 0
        thumb_index = 0
        max_missed = 10

        while count < per_page and missed_in_row < max_missed:
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, thumb_css)
            # Filter valid thumbnails by size (discard small toolbar images)
            thumbnails = [thumb for thumb in thumbnails if thumb.size['width'] > 50 and thumb.size['height'] > 50]

            if thumb_index >= len(thumbnails):
                # No more thumbnails visible: scroll and/or try 'Load more'
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.0)

                try:
                    more_btn = self.driver.find_element(By.CLASS_NAME, "mye4qd")
                    self._safe_click(more_btn)
                    print("[INFO] Loading more results...")
                    time.sleep(1.5)
                except Exception:
                    # No 'more results' button; extra scroll
                    self.driver.execute_script("window.scrollBy(0, 600);")
                    time.sleep(0.8)

                thumbnails = self.driver.find_elements(By.CSS_SELECTOR, thumb_css)
                if thumb_index >= len(thumbnails):
                    print("[INFO] No more thumbnails available.")
                    break

            thumb = thumbnails[thumb_index]
            thumb_index += 1

            # Try to open thumbnail preview
            try:
                self._safe_click(thumb)
            except Exception as e:
                print(f"[DEBUG] Thumbnail click failed: {repr(e)}")
                missed_in_row += 1
                continue

            # Retry getting images from the panel using JS
            got_valid = False
            for attempt in range(3):
                try:
                    _ = self._wait_for_preview_images(timeout=6)  # ensure panel has images
                    srcs = self._collect_preview_srcs()
                    print(f"[DEBUG] Preview srcs found: {len(srcs)} (attempt {attempt+1})")

                    for src_link in srcs:
                        if not src_link:
                            continue
                        if not src_link.startswith("http"):
                            continue
                        if "encrypted" in src_link:
                            continue
                        if self._is_watermarked(src_link):
                            continue
                        
                        print(f"[INFO] {query}\t#{count+1}\t{src_link}")
                        
                        # Create MediaItem
                        item_id = str(abs(hash(f"{query}_{count}_{src_link}")))
                        
                        # Extract domain for photographer field
                        parsed = urlparse(src_link)
                        photographer = parsed.netloc
                        photographer_url = f"{parsed.scheme}://{parsed.netloc}"
                        
                        item = MediaItem(
                            id=item_id,
                            url=self.driver.current_url,  # Current Google search URL
                            download_url=src_link,
                            title=f"Image {count+1} from search: {query}",
                            description=f"Image from Google Images search: {query}",
                            tags=query.split(),
                            width=0,  # We don't have dimensions from JS extraction
                            height=0,
                            photographer=photographer,
                            photographer_url=photographer_url,
                            provider="google",
                            media_type="photo"
                        )
                        
                        items.append(item)
                        count += 1
                        got_valid = True
                        break

                    if got_valid:
                        break

                    # Small scroll and retry if no valid found
                    self.driver.execute_script("window.scrollBy(0, 250);")
                    time.sleep(0.6)

                except TimeoutException:
                    time.sleep(0.8)

            if got_valid:
                missed_in_row = 0
            else:
                missed_in_row += 1
                print("[INFO] No valid image from this thumbnail.")
        
        print(f"[INFO] Google search ended. Found {len(items)} images.")
        
        return SearchResult(
            items=items,
            total_results=len(items),  # We don't know the actual total
            page=page,
            per_page=per_page,
            has_next=len(items) == per_page  # Estimate based on results
        )
    
    def _search_videos(
        self, 
        query: str, 
        page: int = 1, 
        per_page: int = 10,
        **filters: Any
    ) -> SearchResult:
        """Search for videos using Google Videos scraping."""
        if self.driver is None:
            self.driver = self._init_driver()
        
        # Build search URL with filters
        url = self._build_google_video_search_url(
            query=query,
            duration=filters.get('duration', 'short'),  # Default to short videos for B-rolls
            quality=filters.get('quality'),
            recent=filters.get('recent', False)
        )
        
        print(f"[INFO] Opening Google Videos search: {url}")
        self.driver.get(url)
        
        # Wait for video results to appear
        video_selectors = [
            'a[href*="youtube.com"]',
            'a[href*="vimeo.com"]',
            'a[href*="dailymotion.com"]',
            'a[href*="watch"]',
            'div[data-ved]'
        ]
        
        try:
            # Wait for any of the video selectors to appear
            for selector in video_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            else:
                print("[ERR] No video results found. Check your query or connection.")
                return SearchResult(items=[], total_results=0, page=page, per_page=per_page, has_next=False)
        except TimeoutException:
            print("[ERR] No video results found. Check your query or connection.")
            return SearchResult(items=[], total_results=0, page=page, per_page=per_page, has_next=False)

        items = []
        count = 0
        
        # Extract video links
        video_links = []
        
        # Get YouTube links
        youtube_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="youtube.com"]')
        for link in youtube_links[:per_page]:
            href = link.get_attribute('href')
            if href and 'watch?v=' in href:
                video_links.append(('youtube', href, link))
        
        # Get Vimeo links
        vimeo_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="vimeo.com"]')
        for link in vimeo_links[:per_page]:
            href = link.get_attribute('href')
            if href and ('vimeo.com/' in href):
                video_links.append(('vimeo', href, link))
        
        # Process video links
        for platform, video_url, element in video_links[:per_page]:
            if count >= per_page:
                break
                
            try:
                # Get video metadata if available
                title_element = element.find_element(By.XPATH, ".//h3 | .//span | .//div[contains(@class, 'title')]")
                title = title_element.text.strip() if title_element else f"{platform.title()} video from search: {query}"
            except:
                title = f"{platform.title()} video from search: {query}"
            
            # Try to get duration from yt-dlp (quick info extraction)
            duration = None
            thumbnail_url = None
            
            if YT_DLP_AVAILABLE:
                try:
                    # Quick metadata extraction without downloading
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                        'skip_download': True
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=False)
                        duration = info.get('duration', 0)
                        thumbnail_url = info.get('thumbnail')
                        
                        # Filter by duration if specified (for B-rolls, prefer short videos)
                        max_duration = filters.get('max_duration', 300)  # 5 minutes default
                        if duration and duration > max_duration:
                            print(f"[INFO] Skipping video {video_url} - too long ({duration}s)")
                            continue
                            
                except Exception as e:
                    print(f"[DEBUG] Could not extract metadata for {video_url}: {e}")
                    # Continue anyway, we can still include the video
            
            # Create MediaItem for video
            item_id = str(abs(hash(f"{query}_{count}_{video_url}")))
            
            # Extract channel/creator info
            parsed = urlparse(video_url)
            photographer = f"{platform.title()} Creator"
            photographer_url = f"{parsed.scheme}://{parsed.netloc}"
            
            item = MediaItem(
                id=item_id,
                url=self.driver.current_url,  # Current Google search URL
                download_url=video_url,
                title=title,
                description=f"Video from Google {platform.title()} search: {query}",
                tags=query.split(),
                width=0,  # Video dimensions not extracted from search
                height=0,
                photographer=photographer,
                photographer_url=photographer_url,
                provider="google",
                media_type="video",
                duration=duration,
                thumbnail_url=thumbnail_url,
                video_files=[{
                    "platform": platform,
                    "url": video_url,
                    "quality": "original"
                }]
            )
            
            items.append(item)
            count += 1
            print(f"[INFO] {query}\t#{count}\t{platform}\t{video_url}")
        
        print(f"[INFO] Google video search ended. Found {len(items)} videos.")
        
        return SearchResult(
            items=items,
            total_results=len(items),  # We don't know the actual total
            page=page,
            per_page=per_page,
            has_next=len(items) == per_page  # Estimate based on results
        )
    
    def get_item(self, item_id: str, media_type: str = "photo") -> MediaItem:
        """Get item by ID - not supported for scraping."""
        raise NotImplementedError(
            "Google scraper doesn't support fetching individual items by ID. "
            "Use search() method instead."
        )
    
    def download_item(self, item: MediaItem, output_path: str, quality: str = "best") -> str:
        """Download image or video from URL."""
        if item.media_type == "video":
            return self._download_video(item, output_path, quality)
        else:
            return self._download_image(item, output_path)
    
    def _download_image(self, item: MediaItem, output_path: str) -> str:
        """Download image from URL."""
        download_url = item.download_url
        
        if not download_url:
            raise RuntimeError("No download URL available")
        
        try:
            # Create output directory
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(download_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save image using PIL to handle format conversion
            with Image.open(io.BytesIO(response.content)) as img:
                # Ensure output path has correct extension
                path_obj = Path(output_path)
                if not path_obj.suffix:
                    format_ext = img.format.lower() if img.format else 'jpg'
                    output_path = str(path_obj.with_suffix(f".{format_ext}"))
                
                # Convert RGBA to RGB if saving as JPEG
                if path_obj.suffix.lower() in ['.jpg', '.jpeg'] and img.mode in ['RGBA', 'P']:
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                img.save(output_path)
                print(f"[INFO] Image downloaded to {output_path}")
            
            # Verify file was created and has content
            if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
                raise RuntimeError("Downloaded file is empty or wasn't created")
            
            return output_path
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download image: {str(e)}")
        except IOError as e:
            raise RuntimeError(f"Failed to save image: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during download: {str(e)}")
    
    def _download_video(self, item: MediaItem, output_path: str, quality: str = "best") -> str:
        """Download video using yt-dlp."""
        if not YT_DLP_AVAILABLE:
            raise RuntimeError(
                "yt-dlp is required for video downloads. Install with: pip install yt-dlp"
            )
        
        download_url = item.download_url
        
        if not download_url:
            raise RuntimeError("No download URL available")
        
        try:
            # Create output directory
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': self._get_video_format_selector(quality),
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                # Prefer MP4 format for compatibility
                'format_selector': 'best[ext=mp4]/best',
                # Limit video duration for B-rolls (optional)
                'match_filter': self._duration_filter(max_duration=600)  # 10 minutes max
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"[INFO] Downloading video from {download_url}")
                ydl.download([download_url])
            
            # Verify file was created
            if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
                # yt-dlp might have changed the filename, look for similar files
                output_dir = Path(output_path).parent
                stem = Path(output_path).stem
                
                for file in output_dir.glob(f"{stem}*"):
                    if file.is_file() and file.stat().st_size > 0:
                        # Rename to expected output path
                        file.rename(output_path)
                        print(f"[INFO] Video downloaded to {output_path}")
                        return output_path
                
                raise RuntimeError("Downloaded file not found or is empty")
            
            print(f"[INFO] Video downloaded to {output_path}")
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to download video: {str(e)}")
    
    def _get_video_format_selector(self, quality: str) -> str:
        """Get yt-dlp format selector based on quality preference."""
        quality_map = {
            "best": "best[height<=1080]",          # Best quality up to 1080p
            "high": "best[height<=1080]",          # 1080p max
            "medium": "best[height<=720]",         # 720p max
            "low": "worst[height>=360]",           # 360p min
            "worst": "worst"                       # Smallest file
        }
        return quality_map.get(quality, "best[height<=720]")  # Default to 720p for B-rolls
    
    def _duration_filter(self, max_duration: int = 600):
        """Create a filter function for video duration (for B-rolls)."""
        def filter_func(info_dict):
            duration = info_dict.get('duration')
            if duration and duration > max_duration:
                return f"Video too long: {duration}s > {max_duration}s"
            return None
        return filter_func
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup WebDriver on object destruction."""
        self.close()
    
    @property
    def name(self) -> str:
        return "google"
    
    @property
    def supported_formats(self) -> List[str]:
        base_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
        if YT_DLP_AVAILABLE:
            return base_formats + ["mp4", "webm", "avi", "mov"]
        return base_formats
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get fetcher capabilities."""
        base_capabilities = {
            "name": self.name,
            "supported_formats": self.supported_formats,
            "supported_media_types": ["photo"],
            "supports_pagination": False,
            "supports_filters": True,
            "available_filters": {
                "photo": {
                    "size": self.supported_sizes,
                    "color": self.supported_colors,
                    "license": ["commercial", "noncommercial"]
                }
            }
        }
        
        if YT_DLP_AVAILABLE:
            base_capabilities["supported_media_types"].extend(["video", "both"])
            base_capabilities["available_filters"]["video"] = {
                "duration": ["short", "medium", "long"],  # <4min, 4-20min, >20min
                "quality": ["high", "any"],
                "recent": [True, False],
                "max_duration": "seconds (for B-roll filtering)"
            }
            base_capabilities["video_platforms"] = ["youtube", "vimeo", "dailymotion"]
            base_capabilities["video_qualities"] = ["best", "high", "medium", "low", "worst"]
        
        return base_capabilities
    
    @property
    def supported_sizes(self) -> List[str]:
        return ["s", "m", "l", "x", "xx", "h"]  # Google's size codes
    
    @property
    def supported_colors(self) -> List[str]:
        return ["red", "orange", "yellow", "green", "teal", "blue", 
                "purple", "pink", "white", "gray", "black", "brown"]
    
    # Convenience methods for specific media types
    def search_images(self, query: str, page: int = 1, per_page: int = 10, **filters: Any) -> SearchResult:
        """Search specifically for images."""
        filters["media_type"] = "photo"
        return self.search(query, page, per_page, **filters)
    
    def search_videos(self, query: str, page: int = 1, per_page: int = 10, **filters: Any) -> SearchResult:
        """Search specifically for videos (B-rolls)."""
        filters["media_type"] = "video"
        # Default settings optimized for B-rolls
        if "duration" not in filters:
            filters["duration"] = "short"  # Prefer short videos for B-rolls
        if "max_duration" not in filters:
            filters["max_duration"] = 300  # 5 minutes max for B-rolls
        return self.search(query, page, per_page, **filters)
    
    def search_brolls(self, query: str, max_duration: int = 180, per_page: int = 5, **filters: Any) -> SearchResult:
        """Search specifically for B-roll videos (short clips)."""
        filters.update({
            "media_type": "video",
            "duration": "short",
            "max_duration": max_duration,  # Default 3 minutes for B-rolls
            "quality": "high"
        })
        return self.search(query, page=1, per_page=per_page, **filters)
