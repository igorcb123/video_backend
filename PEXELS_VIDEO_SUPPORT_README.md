# Pexels Fetcher - Soporte para Videos

## Resumen de Nuevas Funcionalidades

El `PexelsFetcher` ha sido extendido para soportar tanto **fotos** como **videos**, manteniendo toda la funcionalidad original intacta.

## Características Principales

### 🎬 Soporte de Videos
- ✅ Búsqueda de videos en Pexels
- ✅ Múltiples calidades disponibles (HD, SD, HLS)
- ✅ Información detallada de videos (duración, FPS, dimensiones)
- ✅ URLs de descarga para diferentes resoluciones
- ✅ Imágenes de previsualización/thumbnails

### 📸 Funcionalidad Original Preservada
- ✅ Búsqueda de fotos (sin cambios)
- ✅ Misma API y métodos existentes
- ✅ Rotación de API keys
- ✅ Filtros y parámetros de búsqueda

## Uso Básico

### Búsqueda Combinada (Fotos y Videos)
```python
from services.fetchers.pexels_fetcher import PexelsFetcher

fetcher = PexelsFetcher()

# Buscar solo fotos (comportamiento original)
photos = fetcher.search("nature", media_type="photo")

# Buscar solo videos
videos = fetcher.search("ocean", media_type="video") 

# Buscar ambos (fotos y videos)
mixed = fetcher.search("sunset", media_type="both")
```

### Métodos de Conveniencia
```python
# Búsqueda específica por tipo de media
photo_results = fetcher.search_photos("landscape", per_page=10)
video_results = fetcher.search_videos("waves", per_page=5)

# Obtener información específica de un video
video_item = fetcher.get_item("1918465", media_type="video")
```

## Información Adicional de Videos

### Campos Añadidos a `MediaItem`
```python
# Campos específicos para videos
media_type: str = "photo"  # "photo" o "video"
duration: Optional[int] = None  # Duración en segundos
video_files: Optional[List[Dict]] = None  # Diferentes calidades
preview_images: Optional[List[str]] = None  # URLs de thumbnails
thumbnail_url: Optional[str] = None  # Imagen principal de previsualización
```

### Estructura de `video_files`
Cada elemento contiene:
```python
{
    "id": 125004,
    "quality": "hd",  # "hd", "sd", "hls"
    "file_type": "video/mp4",
    "width": 1920,
    "height": 1080,
    "fps": 24.0,
    "link": "https://player.vimeo.com/external/..."
}
```

## Filtros Específicos para Videos

### Filtros Disponibles
```python
video_results = fetcher.search_videos("nature", 
    orientation="landscape",     # landscape, portrait, square
    size="large",               # large (4K), medium (Full HD), small (HD)
    min_duration=10,            # duración mínima en segundos
    max_duration=60,            # duración máxima en segundos
    min_width=1920,             # ancho mínimo en píxeles
    min_height=1080,            # alto mínimo en píxeles
    locale="en-US"              # localización
)
```

## Descarga de Videos

### Selección de Calidad
```python
# Descargar con calidad específica
fetcher.download_item(video_item, "video.mp4", quality="hd")

# Opciones de calidad disponibles:
# - "best": Mejor calidad disponible (por defecto)
# - "hd": Alta definición
# - "sd": Definición estándar  
# - "worst": Menor calidad (para tests/previews)
```

### Obtener URLs Específicas
```python
# Obtener URL de mejor calidad HD
hd_url = fetcher.get_best_video_url(video_item, "hd")

# Obtener todas las calidades disponibles
qualities = fetcher.get_video_qualities(video_item)
for q in qualities:
    print(f"{q['quality']}: {q['width']}x{q['height']}px - {q['link']}")
```

## Capacidades del Fetcher

```python
capabilities = fetcher.get_capabilities()
print(capabilities)

# Resultado:
{
    "name": "pexels",
    "supported_formats": ["jpg", "jpeg", "mp4", "mov"],
    "supported_media_types": ["photo", "video", "both"],
    "video_qualities": ["hd", "sd", "hls"],
    "available_filters": {
        "photo": ["orientation", "size", "color", "locale"],
        "video": ["orientation", "size", "locale", "min_width", 
                 "min_height", "min_duration", "max_duration"]
    }
}
```

## Ejemplos Prácticos

### Ejemplo 1: Buscar Videos de Naturaleza
```python
nature_videos = fetcher.search_videos("forest", 
    size="large",
    min_duration=15,
    max_duration=45,
    orientation="landscape"
)

for video in nature_videos.items:
    print(f"🎥 {video.title}")
    print(f"   📐 {video.width}x{video.height}px")
    print(f"   ⏱️ {video.duration}s")
    print(f"   🔗 {video.url}")
    print(f"   🖼️ Thumbnail: {video.thumbnail_url}")
    
    # Mostrar calidades disponibles
    for quality in video.video_files[:3]:
        print(f"   📹 {quality['quality'].upper()}: {quality['width']}x{quality['height']}px")
```

### Ejemplo 2: Descargar Video en Diferentes Calidades
```python
video = fetcher.get_item("1918465", media_type="video")

# Descargar en HD
fetcher.download_item(video, "ocean_hd.mp4", quality="hd")

# Descargar en SD para preview
fetcher.download_item(video, "ocean_preview.mp4", quality="sd")
```

## Compatibilidad y Migración

### ✅ Código Existente Sigue Funcionando
```python
# Este código existente NO requiere cambios
fetcher = PexelsFetcher()
results = fetcher.search("nature")  # Sigue devolviendo solo fotos
photo = fetcher.get_item("12345")   # Sigue funcionando para fotos
```

### 🔄 Para Aprovechar las Nuevas Funcionalidades
```python
# Simplemente añadir parámetros opcionales
results = fetcher.search("nature", media_type="video")  # Ahora busca videos
video = fetcher.get_item("12345", media_type="video")   # Para obtener videos
```

## Notas Importantes

1. **API Keys**: Usa las mismas claves de API de Pexels
2. **Rate Limits**: Se aplican los mismos límites para fotos y videos
3. **Endpoints**: Videos usan `https://api.pexels.com/videos/` automáticamente
4. **Formatos**: Videos principalmente en MP4, fotos en JPG/JPEG
5. **Compatibilidad**: 100% compatible con código existente

## Testing

Ejecuta el script de demostración:
```bash
python src/examples/pexels_video_demo.py
```

Este script demuestra todas las nuevas funcionalidades y verifica que todo funcione correctamente.
