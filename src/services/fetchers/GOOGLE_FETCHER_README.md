# Google Images Fetcher - Selenium Based

Este módulo implementa un fetcher de imágenes de Google usando Selenium WebDriver para hacer scraping de Google Images, replicando la funcionalidad del fetcher original pero adaptado a la arquitectura del proyecto.

## Características Principales

### ✅ Funcionalidades Implementadas

1. **Scraping Directo de Google Images**
   - Usa Selenium WebDriver para navegar y extraer imágenes
   - Maneja automáticamente formularios de consentimiento
   - Soporte para modo headless y con interfaz gráfica

2. **Filtros Avanzados de Búsqueda**
   - **Tamaño**: small, medium, large, xlarge, xxlarge, huge
   - **Color**: red, orange, yellow, green, teal, blue, purple, pink, white, gray, black, brown
   - **Tipo de Imagen**: face, photo, clipart, lineart, animated
   - **Formato de Archivo**: jpg, png, gif, bmp, webp
   - **Derechos de Uso**: cc_publicdomain, cc_attribute, cc_sharealike, cc_noncommercial, cc_nonderived
   - **Sitio Específico**: Búsqueda en sitios específicos

3. **Descarga de Imágenes**
   - Soporte para imágenes HTTP regulares
   - Manejo de imágenes base64 embebidas
   - Conversión automática de formatos (RGBA a RGB para JPEG)
   - Validación de integridad de archivos descargados

4. **Integración con Arquitectura del Proyecto**
   - Compatible con el sistema de caché existente
   - Implementa la interfaz `BaseMediaFetcher`
   - Gestión automática de recursos (WebDriver cleanup)
   - Configuración centralizada en `settings.py`

## Instalación de Dependencias

```bash
pip install selenium webdriver-manager Pillow
```

## Configuración

### Variables de Entorno (Opcionales)

```bash
# Configuración de Selenium (opcional)
SELENIUM_HEADLESS=true
WEBDRIVER_PATH=/path/to/chromedriver  # Auto-descarga si está vacío
```

### Configuración en settings.py

```python
# Media Fetcher Configuration
media_provider: Literal["pexels", "google"] = "google"
selenium_headless: bool = True
webdriver_path: str = ""  # Auto-descarga ChromeDriver si está vacío
```

## Uso Básico

### 1. Búsqueda Simple

```python
from services.media_fetcher_orchestrator import MediaFetcherService

# Inicializar servicio
service = MediaFetcherService(provider="google")

# Búsqueda básica
result = service.search_images("mountain landscape", per_page=5)

print(f"Encontradas {len(result.items)} imágenes")
for item in result.items:
    print(f"- {item.title} ({item.width}x{item.height})")

# Importante: Cerrar recursos
service.close()
```

### 2. Búsqueda con Filtros

```python
service = MediaFetcherService(provider="google")

# Búsqueda con filtros avanzados
result = service.search_images(
    "sunset photography",
    per_page=5,
    size="large",
    color="orange",
    image_type="photo",
    license="cc_publicdomain"
)

service.close()
```

### 3. Descarga de Imágenes

```python
service = MediaFetcherService(provider="google")

# Buscar y descargar
result = service.search_images("nature", per_page=3)

if result.items:
    # Descargar primera imagen
    output_path = "./downloads/nature_image.jpg"
    downloaded_path = service.download_image(result.items[0], custom_path=output_path)
    print(f"Imagen descargada en: {downloaded_path}")

service.close()
```

### 4. Descarga en Lote

```python
service = MediaFetcherService(provider="google")

# Buscar imágenes
result = service.search_images("workspace office", per_page=5)

# Descargar todas
download_dir = "./downloads/office_images"
downloaded_files = service.bulk_download_images(
    result.items,
    download_dir,
    size="medium"
)

print(f"Descargadas {len(downloaded_files)} imágenes")
service.close()
```

## Características Técnicas

### Selectores CSS Dinámicos

El fetcher utiliza múltiples estrategias para encontrar elementos:

```python
selectors = [
    "img.YQ4gaf",         # Selector principal actualizado
    "div[data-ri] img",   # Contenedor con data-ri
    ".eA0Zlc img",        # Contenedor de miniaturas
    "img[data-src]",      # Imágenes con data-src
    ".islrc img",         # Otro contenedor posible
    "img.rg_i",           # Selector clásico
]
```

### Estrategias de Click Robustas

```python
# Múltiples métodos de click para mayor confiabilidad
1. ActionChains().move_to_element().click()
2. JavaScript: driver.execute_script("arguments[0].click();", element)
3. ActionChains con offset al centro del elemento
```

### Manejo de Formularios de Consentimiento

```python
consent_buttons = [
    ("W0wltc", "Accept"),
    ("L2AGLb", "Reject all"), 
    ("VtwTSb", "Accept all"),
    # ... más variantes
]
```

## Tipos de Datos

### MediaItem
```python
@dataclass
class MediaItem:
    id: str                    # Hash único generado
    url: str                   # URL de la página de Google
    download_url: str          # URL directa de la imagen o base64
    title: str                 # Título/descripción alt
    description: str           # Descripción extendida
    tags: List[str]           # Tags extraídos del query
    width: int                # Ancho en píxeles
    height: int               # Alto en píxeles
    photographer: str         # Dominio de origen
    photographer_url: str     # URL del sitio origen
    provider: str = "google"  # Proveedor
```

## Ventajas vs API de Google

### ✅ Ventajas del Scraping
- **Sin límites de cuota**: No hay restricciones de API
- **Sin costo**: Completamente gratuito
- **Más resultados**: Acceso a todo el índice de Google Images
- **Filtros completos**: Todos los filtros de la interfaz web

### ⚠️ Consideraciones
- **Dependiente de Selenium**: Requiere Chrome instalado
- **Más lento**: Navegador web vs API directa
- **Frágil**: Cambios en Google pueden romper selectores
- **Recursos**: Consume más memoria y CPU

## Manejo de Errores

```python
try:
    service = MediaFetcherService(provider="google")
    result = service.search_images("query")
    # ... procesamiento
except ImportError:
    print("Selenium no disponible")
except RuntimeError as e:
    print(f"Error de scraping: {e}")
finally:
    service.close()  # Siempre cerrar recursos
```

## Comparación con Pexels

| Característica | Google (Scraping) | Pexels (API) |
|---------------|------------------|--------------|
| Costo | Gratuito | Gratuito con límites |
| Velocidad | Lenta | Rápida |
| Variedad | Muy alta | Alta, curada |
| Calidad | Variable | Consistentemente alta |
| Licencias | Variables | Claramente definidas |
| Mantenimiento | Alto | Bajo |

## Ejemplos de Uso Avanzado

### Búsqueda en Sitio Específico
```python
result = service.search_images(
    "logo design",
    site="dribbble.com",
    image_type="clipart",
    per_page=10
)
```

### Combinación de Filtros
```python
result = service.search_images(
    "business meeting",
    size="xlarge",
    color="blue",
    image_type="photo",
    license="cc_publicdomain",
    per_page=5
)
```

## Solución de Problemas

### Chrome no encontrado
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# Windows: Instalar Chrome desde https://chrome.google.com
```

### WebDriver desactualizado
```python
# El WebDriver se actualiza automáticamente con webdriver-manager
# Si hay problemas, eliminar cache:
rm -rf ~/.wdm  # Linux/Mac
# o eliminar carpeta equivalente en Windows
```

### Elementos no encontrados
- Los selectores CSS pueden cambiar con actualizaciones de Google
- El fetcher usa múltiples selectores de respaldo
- Considera ejecutar con `headless=False` para debugging

## Integración con Proyecto

Este Google Images Fetcher está completamente integrado con:

- ✅ Sistema de caché (`MediaCache`)
- ✅ Configuración centralizada (`settings.py`)
- ✅ Interface unificada (`BaseMediaFetcher`)
- ✅ Orquestador principal (`MediaFetcherService`)
- ✅ Tests y ejemplos

¡El fetcher mantiene toda la funcionalidad original pero con mejor arquitectura y mantenibilidad!
