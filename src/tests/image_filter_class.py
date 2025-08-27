"""
image_filter_class.py

Clase optimizada para filtrar imágenes basada en CLIP que recibe una descripción
y un array de URLs de imágenes, devolviendo un objeto con los mismos resultados
que el código original pero de forma más performante y minimizando falsos positivos.

Uso:
    filter = ImageFilterCLIP()
    results = filter.filter_images("A small dog with a ball", image_urls)
"""

import torch
import time
import warnings
import json
import io
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Union, Tuple
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from urllib.parse import urlparse
import hashlib


class ImageFilterCLIP:
    """
    Clase optimizada para filtrar imágenes usando CLIP.
    
    Características:
    - Procesamiento en batch para máxima performance
    - Descarga concurrente de imágenes
    - Cache de embeddings de texto
    - Configuración flexible de umbrales
    - Minimización de falsos positivos con umbrales adaptativos
    """
    
    # Configuración por defecto optimizada para minimizar falsos positivos
    DEFAULT_CONFIG = {
        "model_name": "openai/clip-vit-base-patch32",
        "positive_threshold": 0.28,  # Más estricto para reducir falsos positivos
        "negative_threshold": 0.25,  # Más conservador para detectar contenido problemático
        "batch_size": 12,  # Optimizado para memoria GPU
        "max_workers": 8,  # Para descarga concurrente
        "image_size": (224, 224),
        "timeout": 10,  # Timeout para descarga de imágenes
        "max_retries": 2,
        "device": None,  # Auto-detect
        "use_cache": True,
        "negative_prompts": [
            "nudity", "naked person", "sexual content",
            "violence", "blood", "gore", "graphic injury",
            "weapons", "guns", "knives",
            "adult content", "pornography",
            "drug use", "drugs", "smoking",
            "hate symbols", "inappropriate content"
        ]
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el filtro de imágenes.
        
        Args:
            config: Diccionario con configuración personalizada
        """
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)
        
        self.model = None
        self.processor = None
        self.device = None
        self._text_embeddings_cache = {}
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializa el modelo CLIP y configura el dispositivo."""
        print(f"Loading model: {self.config['model_name']}")
        start_time = time.time()
        
        self.model = CLIPModel.from_pretrained(self.config['model_name'])
        self.processor = CLIPProcessor.from_pretrained(self.config['model_name'])
        self.model.eval()
        
        # Configurar dispositivo
        if self.config['device'] is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device_str = self.config['device'].lower()
            if device_str == "cuda" and not torch.cuda.is_available():
                warnings.warn("CUDA no disponible - usando CPU")
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
        
        if self.config['use_cache'] and cache_key in self._text_embeddings_cache:
            return self._text_embeddings_cache[cache_key]
        
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        
        # Mover inputs al dispositivo
        for k, v in inputs.items():
            inputs[k] = v.to(self.device)
        
        with torch.no_grad():
            text_embs = self.model.get_text_features(**inputs)
        
        # Normalizar
        text_embs = text_embs / text_embs.norm(dim=-1, keepdim=True)
        
        if self.config['use_cache']:
            self._text_embeddings_cache[cache_key] = text_embs
        
        return text_embs
    
    def _download_image(self, url: str) -> Optional[Image.Image]:
        """
        Descarga una imagen desde URL con reintentos y manejo de errores.
        
        Args:
            url: URL de la imagen
            
        Returns:
            Imagen PIL o None si falla
        """
        for attempt in range(self.config['max_retries']):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(
                    url,
                    timeout=self.config['timeout'],
                    headers=headers,
                    stream=True
                )
                response.raise_for_status()
                
                # Verificar que es una imagen
                content_type = response.headers.get('content-type', '').lower()
                if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'webp']):
                    raise ValueError(f"Content type not supported: {content_type}")
                
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                image = image.resize(self.config['image_size'], Image.LANCZOS)
                
                return image
                
            except Exception as e:
                if attempt == self.config['max_retries'] - 1:
                    print(f"Failed to download {url} after {self.config['max_retries']} attempts: {str(e)}")
                    return None
                time.sleep(0.5 * (attempt + 1))  # Backoff exponencial
        
        return None
    
    def _download_images_concurrent(self, urls: List[str]) -> Dict[str, Optional[Image.Image]]:
        """
        Descarga múltiples imágenes de forma concurrente.
        
        Args:
            urls: Lista de URLs
            
        Returns:
            Diccionario con URL -> Image o None
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
            # Enviar todas las tareas
            future_to_url = {executor.submit(self._download_image, url): url for url in urls}
            
            # Recoger resultados
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    results[url] = None
        
        return results
    
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
            
            # Identificar prompts negativos activados
            for i, score in enumerate(sim_neg_list):
                if score >= self.config['negative_threshold']:
                    if i < len(negative_prompts):
                        negatives_triggered.append({
                            "prompt": negative_prompts[i],
                            "score_raw": round(score, 4),
                            "score_pct": round(score * 100, 2)
                        })
        
        # Determinar estado con lógica optimizada para reducir falsos positivos
        if max_neg >= self.config['negative_threshold']:
            state = "censored"
        elif max_pos >= self.config['positive_threshold']:
            # Verificación adicional: si hay contenido negativo cerca del umbral, ser más estricto
            if max_neg > (self.config['negative_threshold'] * 0.8):
                # Requerir mayor confianza positiva si hay señales negativas
                required_pos_threshold = self.config['positive_threshold'] * 1.2
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
                "model": self.config['model_name'],
                "description": description,
                "positive_threshold": self.config['positive_threshold'],
                "negative_threshold": self.config['negative_threshold'],
                "negative_prompts": negative_prompts or self.config['negative_prompts'],
                "results": []
            }
        
        start_time = time.time()
        
        # Usar prompts negativos por defecto si no se especifican
        neg_prompts = negative_prompts or self.config['negative_prompts']
        
        print(f"Processing {len(image_urls)} images...")
        
        # Calcular embeddings de texto (con cache)
        pos_emb = self._get_text_embeddings([description])
        neg_emb = self._get_text_embeddings(neg_prompts) if neg_prompts else None
        
        # Descargar imágenes concurrentemente
        print("Downloading images...")
        download_start = time.time()
        downloaded_images = self._download_images_concurrent(image_urls)
        download_time = time.time() - download_start
        print(f"Downloaded images in {download_time:.2f}s")
        
        # Separar imágenes válidas de las que fallaron
        valid_images = []
        valid_urls = []
        failed_urls = []
        
        for url in image_urls:
            img = downloaded_images.get(url)
            if img is not None:
                valid_images.append(img)
                valid_urls.append(url)
            else:
                failed_urls.append(url)
        
        results = []
        
        # Procesar imágenes que fallaron en descarga
        for url in failed_urls:
            results.append({
                "image": url,
                "error": "Failed to download image",
                "state": "error",
                "score_positive_raw": 0.0,
                "score_positive_pct": 0.0,
                "score_negative_raw": 0.0,
                "score_negative_pct": 0.0,
                "negatives_triggered": [],
                "time_ms": 0.0
            })
        
        # Procesar imágenes válidas en batches
        batch_size = self.config['batch_size']
        
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
            "model": self.config['model_name'],
            "description": description,
            "positive_threshold": self.config['positive_threshold'],
            "negative_threshold": self.config['negative_threshold'],
            "negative_prompts": neg_prompts,
            "processing_time_seconds": round(total_time, 2),
            "download_time_seconds": round(download_time, 2),
            "statistics": stats,
            "results": results
        }
    
    def update_config(self, **kwargs):
        """
        Actualiza la configuración de la clase.
        
        Args:
            **kwargs: Parámetros de configuración a actualizar
        """
        self.config.update(kwargs)
        
        # Si se cambió el modelo, reinicializar
        if 'model_name' in kwargs:
            self._initialize_model()
    
    def clear_cache(self):
        """Limpia el cache de embeddings de texto."""
        self._text_embeddings_cache.clear()
    
    def get_config(self) -> Dict:
        """Retorna la configuración actual."""
        return self.config.copy()


# Ejemplo de uso
if __name__ == "__main__":
    # Configuración personalizada para mayor performance
    custom_config = {
        "positive_threshold": 0.30,
        "negative_threshold": 0.22,
        "batch_size": 16,
        "max_workers": 10
    }
    
    # Inicializar filtro
    filter_instance = ImageFilterCLIP(custom_config)
    
    # URLs de ejemplo (reemplazar con URLs reales)
    image_urls = [
        "https://images.pexels.com/photos/7210673/pexels-photo-7210673.jpeg",
        "https://images.pexels.com/photos/17507248/pexels-photo-17507248.jpeg",
        "https://images.pexels.com/photos/16549837/pexels-photo-16549837.jpeg",
        "https://images.pexels.com/photos/15356250/pexels-photo-15356250.jpeg"
    ]
    
    # Filtrar imágenes
    results = filter_instance.filter_images(
        description="A small dog with a ball",
        image_urls=image_urls
    )
    
    # Mostrar resultados
    print(json.dumps(results, indent=2, ensure_ascii=False))
