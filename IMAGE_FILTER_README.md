# ImageFilterCLIP Service

A performant image filtering service using OpenAI's CLIP model to filter images based on text descriptions while minimizing false positives.

## Features

- **Batch Processing**: Optimized for processing multiple images efficiently
- **Concurrent Downloads**: Downloads images in parallel for better performance  
- **Smart Caching**: Caches text embeddings to improve repeated filtering operations
- **Configurable Thresholds**: Adjustable positive/negative thresholds for fine-tuning
- **False Positive Reduction**: Adaptive logic to minimize incorrect classifications
- **Error Handling**: Robust error handling for failed downloads and processing
- **Modular Design**: Clean separation of concerns with utility classes

## Architecture

The service is structured following the project's service patterns:

```
services/
├── image_filter_class.py       # Main service class
utils/
├── image_utils.py             # Image download and processing utilities
tests/
├── test_image_filter.py       # Comprehensive tests
examples/
├── image_filter_demo.py       # Usage demonstration
```

## Usage

### Basic Usage

```python
from services.image_filter_class import ImageFilterCLIP

# Initialize with default configuration
filter_service = ImageFilterCLIP()

# Filter images
results = filter_service.filter_images(
    description="A small dog with a ball",
    image_urls=[
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ]
)

# Access results
print(f"Found {results['statistics']['valid']} matching images")
```

### Custom Configuration

```python
# Custom configuration for specific needs
custom_config = {
    "positive_threshold": 0.30,     # Higher threshold = more strict matching
    "negative_threshold": 0.22,     # Lower threshold = more sensitive censoring
    "batch_size": 16,               # Larger batches = better GPU utilization
    "max_workers": 10,              # More workers = faster downloads
    "timeout": 15,                  # Longer timeout for slow connections
    "max_retries": 3                # More retries for reliability
}

filter_service = ImageFilterCLIP(custom_config)
```

### Advanced Usage with Custom Negative Prompts

```python
# Use custom negative prompts for specific filtering needs
custom_negatives = [
    "inappropriate content",
    "violence",
    "adult content"
]

results = filter_service.filter_images(
    description="family photo",
    image_urls=urls,
    negative_prompts=custom_negatives
)
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `"openai/clip-vit-base-patch32"` | CLIP model to use |
| `positive_threshold` | `0.28` | Minimum similarity for positive matches |
| `negative_threshold` | `0.25` | Minimum similarity for negative content detection |
| `batch_size` | `12` | Number of images processed per batch |
| `max_workers` | `8` | Maximum concurrent download threads |
| `image_size` | `(224, 224)` | Target image size for processing |
| `timeout` | `10` | Request timeout in seconds |
| `max_retries` | `2` | Maximum retry attempts for failed downloads |
| `device` | `None` | Device for model (auto-detects CUDA/CPU) |
| `use_cache` | `True` | Enable text embedding caching |
| `negative_prompts` | `[predefined list]` | Default negative content patterns |

## Response Format

```python
{
    "model": "openai/clip-vit-base-patch32",
    "description": "search description",
    "positive_threshold": 0.28,
    "negative_threshold": 0.25,
    "negative_prompts": [...],
    "processing_time_seconds": 2.34,
    "download_time_seconds": 1.15,
    "statistics": {
        "total": 10,
        "valid": 7,
        "no_match": 2,
        "censored": 0,
        "errors": 1
    },
    "results": [
        {
            "image": "https://example.com/image1.jpg",
            "state": "valid",
            "score_positive_raw": 0.85,
            "score_positive_pct": 85.0,
            "score_negative_raw": 0.12,
            "score_negative_pct": 12.0,
            "negatives_triggered": [],
            "time_ms": 234.5
        },
        // ... more results
    ]
}
```

### Result States

- `"valid"`: Image matches the description and passes content filters
- `"no_match"`: Image doesn't match the description sufficiently
- `"censored"`: Image contains inappropriate content based on negative prompts
- `"error"`: Failed to download or process the image

## Performance Optimization

### GPU Usage
- Automatically detects and uses CUDA if available
- Optimized batch sizes for GPU memory efficiency
- Model inference runs entirely on GPU when available

### Memory Management
- Configurable batch sizes to control memory usage
- Automatic cleanup of processed image batches
- Text embedding caching reduces repeated computations

### Network Optimization
- Concurrent image downloads with configurable worker count
- Retry logic with exponential backoff
- Request timeouts to prevent hanging operations

## Error Handling

The service handles various error conditions gracefully:

- **Network errors**: Retries with exponential backoff
- **Invalid images**: Skips and reports as errors
- **Model errors**: Graceful fallback and error reporting
- **Memory errors**: Automatic batch size adjustment (future enhancement)

## Testing

Run the comprehensive test suite:

```bash
python src/tests/test_image_filter.py
```

Test coverage includes:
- Configuration validation
- Service initialization
- Error handling
- Edge cases (empty inputs, invalid configs)
- Performance verification

## Examples

See `src/examples/image_filter_demo.py` for a complete usage example.

## Dependencies

- `torch`: PyTorch for model inference
- `transformers`: Hugging Face transformers (CLIP model)
- `PIL`: Image processing
- `requests`: HTTP requests for image downloads

## Future Enhancements

- [ ] Adaptive batch sizing based on available memory
- [ ] Support for local image files
- [ ] Custom model fine-tuning capabilities
- [ ] Performance metrics and monitoring
- [ ] Image preprocessing pipelines
- [ ] Multi-language support for descriptions
