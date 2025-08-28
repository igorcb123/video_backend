"""
Image filtering service using CLIP model.

Service for filtering images based on text descriptions, optimized for performance
and minimizing false positives.
"""

import torch
import time
import warnings
from typing import List, Dict, Optional
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import hashlib
from utils.image_utils import ImageDownloader, ImageProcessor


class ImageFilterConfig:
    """Configuration class for ImageFilterCLIP service."""
    
    def __init__(self):
        """Initialize default configuration."""
        self.model_name = "openai/clip-vit-base-patch32"
        self.positive_threshold = 0.28  # More strict to reduce false positives
        self.negative_threshold = 0.25  # More conservative for problematic content
        self.batch_size = 12  # Optimized for GPU memory
        self.max_workers = 8  # For concurrent download
        self.image_size = (224, 224)
        self.timeout = 10  # Timeout for image download
        self.max_retries = 2
        self.device = None  # Auto-detect
        self.use_cache = True
        self.negative_prompts = [
            "nudity", "naked person", "sexual content",
            "violence", "blood", "gore", "graphic injury",
            "weapons", "guns", "knives",
            "adult content", "pornography",
            "drug use", "drugs", "smoking",
            "hate symbols", "inappropriate content"
        ]
    
    def update(self, **kwargs):
        """Update configuration with provided values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {key: getattr(self, key) for key in dir(self) 
                if not key.startswith('_') and not callable(getattr(self, key))}


class ImageFilterCLIP:
    """
    Service for filtering images using CLIP model.
    
    Features:
    - Batch processing for maximum performance
    - Concurrent image downloading
    - Text embedding caching
    - Flexible threshold configuration
    - Minimization of false positives with adaptive thresholds
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the image filter.
        
        Args:
            config: Dictionary with custom configuration
        """
        self.config = ImageFilterConfig()
        if config:
            self.config.update(**config)
        
        self.model = None
        self.processor = None
        self.device = None
        self._text_embeddings_cache = {}
        self._image_downloader = ImageDownloader(
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            max_workers=self.config.max_workers
        )
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize CLIP model and configure device."""
        print(f"Loading model: {self.config.model_name}")
        start_time = time.time()
        
        self.model = CLIPModel.from_pretrained(self.config.model_name)
        self.processor = CLIPProcessor.from_pretrained(self.config.model_name)
        self.model.eval()
        
        # Configure device
        if self.config.device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device_str = self.config.device.lower()
            if device_str == "cuda" and not torch.cuda.is_available():
                warnings.warn("CUDA not available - using CPU")
                self.device = torch.device("cpu")
            else:
                self.device = torch.device(device_str)
        
        self.model.to(self.device)
        print(f"Model loaded in {time.time() - start_time:.2f}s on {self.device}")
    
    def _get_text_embeddings(self, texts: List[str]) -> torch.Tensor:
        """
        Obtiene embeddings de texto con cache para mejorar performance.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Tensor normalizado con embeddings
        """
        if not texts:
            return None
        
        # Crear clave de cache
        cache_key = hashlib.md5('|'.join(texts).encode()).hexdigest()
        
        if self.config.use_cache and cache_key in self._text_embeddings_cache:
            return self._text_embeddings_cache[cache_key]
        
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        
        # Mover inputs al dispositivo
        for k, v in inputs.items():
            inputs[k] = v.to(self.device)
        
        with torch.no_grad():
            text_embs = self.model.get_text_features(**inputs)
        
        # Normalizar
        text_embs = text_embs / text_embs.norm(dim=-1, keepdim=True)
        
        if self.config.use_cache:
            self._text_embeddings_cache[cache_key] = text_embs
        
        return text_embs
    
    def _compute_image_embeddings_batch(self, images: List[Image.Image]) -> torch.Tensor:
        """
        Calcula embeddings para un batch de imágenes.
        
        Args:
            images: Lista de imágenes PIL
            
        Returns:
            Tensor normalizado con embeddings
        """
        if not images:
            return torch.empty(0, 512, device=self.device)  # 512 es la dimensión de CLIP
        
        inputs = self.processor(images=images, return_tensors="pt")
        
        # Mover al dispositivo
        for k, v in inputs.items():
            inputs[k] = v.to(self.device)
        
        with torch.no_grad():
            img_embs = self.model.get_image_features(**inputs)
        
        # Normalizar
        img_embs = img_embs / img_embs.norm(dim=-1, keepdim=True)
        
        return img_embs
    
    def _compute_similarities(self, img_embedding: torch.Tensor, text_embeddings: torch.Tensor) -> torch.Tensor:
        """
        Calcula similitudes coseno entre imagen y textos.
        
        Args:
            img_embedding: Embedding de imagen (D,)
            text_embeddings: Embeddings de texto (N, D)
            
        Returns:
            Tensor con similitudes (N,)
        """
        if text_embeddings is None or text_embeddings.shape[0] == 0:
            return torch.tensor([], device=self.device)
        
        return torch.nn.functional.cosine_similarity(
            img_embedding.unsqueeze(0), 
            text_embeddings, 
            dim=1
        )
    
    def _classify_image(
        self, 
        img_emb: torch.Tensor, 
        pos_emb: torch.Tensor, 
        neg_emb: Optional[torch.Tensor],
        negative_prompts: List[str]
    ) -> Dict:
        """
        Clasifica una imagen basada en sus similitudes.
        
        Args:
            img_emb: Embedding de la imagen
            pos_emb: Embeddings positivos
            neg_emb: Embeddings negativos
            negative_prompts: Lista de prompts negativos
            
        Returns:
            Diccionario con clasificación y scores
        """
        # Calcular similitudes positivas
        sim_pos = self._compute_similarities(img_emb, pos_emb)
        max_pos = float(sim_pos.max().item()) if sim_pos.numel() > 0 else 0.0
        
        # Calcular similitudes negativas
        max_neg = 0.0
        negatives_triggered = []
        
        if neg_emb is not None and neg_emb.numel() > 0:
            sim_neg = self._compute_similarities(img_emb, neg_emb)
            sim_neg_list = sim_neg.cpu().tolist()
            max_neg = max(sim_neg_list) if sim_neg_list else 0.0
            
            # Identify triggered negative prompts
            for i, score in enumerate(sim_neg_list):
                if score >= self.config.negative_threshold:
                    if i < len(negative_prompts):
                        negatives_triggered.append({
                            "prompt": negative_prompts[i],
                            "score_raw": round(score, 4),
                            "score_pct": round(score * 100, 2)
                        })
        
        # Determine state with optimized logic to reduce false positives
        if max_neg >= self.config.negative_threshold:
            state = "censored"
        elif max_pos >= self.config.positive_threshold:
            # Additional check: if there's negative content near threshold, be more strict
            if max_neg > (self.config.negative_threshold * 0.8):
                # Require higher positive confidence if there are negative signals
                required_pos_threshold = self.config.positive_threshold * 1.2
                state = "valid" if max_pos >= required_pos_threshold else "no_match"
            else:
                state = "valid"
        else:
            state = "no_match"
        
        return {
            "state": state,
            "score_positive_raw": round(max_pos, 4),
            "score_positive_pct": round(max_pos * 100, 2),
            "score_negative_raw": round(max_neg, 4),
            "score_negative_pct": round(max_neg * 100, 2),
            "negatives_triggered": negatives_triggered
        }
    
    def filter_images(
        self, 
        description: str, 
        image_urls: List[str],
        negative_prompts: Optional[List[str]] = None
    ) -> Dict:
        """
        Filtra un array de URLs de imágenes basado en la descripción.
        
        Args:
            description: Descripción positiva a buscar
            image_urls: Lista de URLs de imágenes
            negative_prompts: Prompts negativos opcionales (usa defaults si no se especifica)
            
        Returns:
            Diccionario con resultados similar al código original
        """
        if not image_urls:
            return {
                "model": self.config.model_name,
                "description": description,
                "positive_threshold": self.config.positive_threshold,
                "negative_threshold": self.config.negative_threshold,
                "negative_prompts": negative_prompts or self.config.negative_prompts,
                "results": []
            }
        
        start_time = time.time()
        
        # Use default negative prompts if not specified
        neg_prompts = negative_prompts or self.config.negative_prompts
        
        print(f"Processing {len(image_urls)} images...")
        
        # Calculate text embeddings (with cache)
        pos_emb = self._get_text_embeddings([description])
        neg_emb = self._get_text_embeddings(neg_prompts) if neg_prompts else None
        
        # Download images concurrently using utility class
        print("Downloading images...")
        download_start = time.time()
        downloaded_images = self._image_downloader.download_images_concurrent(
            image_urls, self.config.image_size
        )
        download_time = time.time() - download_start
        print(f"Downloaded images in {download_time:.2f}s")
        
        # Separate valid images from failed downloads using utility
        valid_images, valid_urls, failed_urls = ImageProcessor.validate_images(
            downloaded_images, image_urls
        )
        
        results = []
        
        # Process failed downloads
        for url in failed_urls:
            results.append(ImageProcessor.create_error_result(url))
        
        # Process valid images in batches
        batch_size = self.config.batch_size
        
        for i in range(0, len(valid_images), batch_size):
            batch_start = time.time()
            
            batch_images = valid_images[i:i + batch_size]
            batch_urls = valid_urls[i:i + batch_size]
            
            try:
                # Calcular embeddings del batch
                img_embeddings = self._compute_image_embeddings_batch(batch_images)
                
                # Clasificar cada imagen del batch
                for j, url in enumerate(batch_urls):
                    img_emb = img_embeddings[j]
                    
                    classification = self._classify_image(
                        img_emb, pos_emb, neg_emb, neg_prompts
                    )
                    
                    batch_time = (time.time() - batch_start) * 1000 / len(batch_images)
                    
                    result = {
                        "image": url,
                        "time_ms": round(batch_time, 2),
                        **classification
                    }
                    
                    results.append(result)
                    
            except Exception as e:
                # Si falla el batch completo, marcar todas las imágenes como error
                for url in batch_urls:
                    results.append({
                        "image": url,
                        "error": str(e),
                        "state": "error",
                        "score_positive_raw": 0.0,
                        "score_positive_pct": 0.0,
                        "score_negative_raw": 0.0,
                        "score_negative_pct": 0.0,
                        "negatives_triggered": [],
                        "time_ms": 0.0
                    })
        
        total_time = time.time() - start_time
        
        # Estadísticas finales
        states = [r.get('state', 'error') for r in results]
        stats = {
            'total': len(results),
            'valid': states.count('valid'),
            'censored': states.count('censored'),
            'no_match': states.count('no_match'),
            'errors': states.count('error')
        }
        
        print(f"Processing completed in {total_time:.2f}s")
        print(f"Results: {stats}")
        
        return {
            "model": self.config.model_name,
            "description": description,
            "positive_threshold": self.config.positive_threshold,
            "negative_threshold": self.config.negative_threshold,
            "negative_prompts": neg_prompts,
            "processing_time_seconds": round(total_time, 2),
            "download_time_seconds": round(download_time, 2),
            "statistics": stats,
            "results": results
        }
    
    def update_config(self, **kwargs):
        """
        Update service configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        old_config = self.config.to_dict()
        self.config.update(**kwargs)
        
        # If model changed, reinitialize
        if 'model_name' in kwargs:
            self._initialize_model()
        
        # If download-related config changed, reinitialize downloader
        download_params = {'timeout', 'max_retries', 'max_workers'}
        if download_params.intersection(kwargs.keys()):
            self._image_downloader = ImageDownloader(
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                max_workers=self.config.max_workers
            )
    
    def clear_cache(self):
        """Clear text embeddings cache."""
        self._text_embeddings_cache.clear()
    
    def get_config(self) -> Dict:
        """Return current configuration."""
        return self.config.to_dict()


