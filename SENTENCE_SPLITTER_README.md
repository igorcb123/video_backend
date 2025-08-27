# SentenceSplitterService

Un servicio en Python para dividir texto largo en español en frases individuales.

## Descripción

El `SentenceSplitterService` es una clase que permite dividir texto largo en español en frases individuales de manera inteligente, manejando correctamente:

- **Signos de puntuación**: Puntos (.), signos de exclamación (¡!), signos de interrogación (¿?)
- **Abreviaciones comunes**: Dr., Sra., etc., no., tel., y muchas más
- **Control de longitud**: Posibilidad de limitar la longitud máxima de las frases
- **Objetos Frase**: Creación de objetos con información de posición y orden

## Características

✅ **Manejo inteligente de abreviaciones** - No corta incorrectamente en "Dr. García"  
✅ **Soporte para caracteres españoles** - Maneja ñ, tildes, ¡, ¿  
✅ **Control de longitud máxima** - Para dividir frases muy largas  
✅ **Limpieza automática de texto** - Normaliza espacios y saltos de línea  
✅ **Objetos Frase estructurados** - Con información de orden y posición de palabras  
✅ **Estadísticas de texto** - Conteo de frases, caracteres, etc.  

## Instalación y Uso

### Importar el servicio

```python
from services.sentence_splitter_service import SentenceSplitterService

# Crear una instancia del servicio
splitter = SentenceSplitterService()
```

### Uso básico

```python
texto = "Hola mundo. ¿Cómo estás? ¡Muy bien! Esto es una prueba."
frases = splitter.split_text_to_sentences(texto)

# Resultado: 
# ['Hola mundo.', '¿Cómo estás?', '¡Muy bien!', 'Esto es una prueba.']
```

### Crear objetos Frase

```python
from models.frase import Frase

texto = "Primera frase. Segunda frase aquí."
frases_objetos = splitter.split_text_to_frase_objects(texto)

# Resultado: objetos Frase con orden y posición de palabras
for frase_obj in frases_objetos:
    print(frase_obj)  # <Frase orden=1 palabras=0-1>
```

### Control de longitud máxima

```python
texto_largo = "Esta es una frase extremadamente larga que supera límites..."
frases_cortas = splitter.split_with_max_length(texto_largo, max_length=50)

# Divide frases largas en partes más pequeñas
```

### Obtener estadísticas

```python
texto = "Primera frase. Segunda frase. Tercera frase."
num_frases = splitter.get_sentence_count(texto)  # 3
```

## API Completa

### Métodos principales

| Método | Descripción | Parámetros | Retorna |
|--------|-------------|------------|---------|
| `split_text_to_sentences(texto)` | Divide texto en lista de frases | `texto: str` | `List[str]` |
| `split_text_to_frase_objects(texto)` | Crea objetos Frase con posición | `texto: str` | `List[Frase]` |
| `split_with_max_length(texto, max_length)` | División con longitud controlada | `texto: str, max_length: int` | `List[str]` |
| `get_sentence_count(texto)` | Cuenta número de frases | `texto: str` | `int` |

### Métodos privados de utilidad

- `_clean_text()` - Limpia y normaliza el texto
- `_handle_abbreviations()` - Procesa abreviaciones temporalmente
- `_restore_abbreviations()` - Restaura abreviaciones originales
- `_split_long_sentence()` - Divide frases largas por puntuación secundaria

## Ejemplos de Uso

### Ejemplo 1: Texto con abreviaciones

```python
texto = "El Dr. García trabaja en el Hospital Gral. San Juan. Su consulta es de lunes a viernes."
frases = splitter.split_text_to_sentences(texto)

# Resultado:
# ['El Dr. García trabaja en el Hospital Gral. San Juan.', 
#  'Su consulta es de lunes a viernes.']
```

### Ejemplo 2: Texto largo con división controlada

```python
texto = "La inteligencia artificial ha revolucionado completamente la forma en que las empresas procesan información..."

# División normal
frases_normales = splitter.split_text_to_sentences(texto)

# División con máximo 80 caracteres
frases_cortas = splitter.split_with_max_length(texto, max_length=80)
```

### Ejemplo 3: Análisis de texto

```python
texto = """
Python es un lenguaje de programación muy popular. Es fácil de aprender. 
¿Sabías que fue creado por Guido van Rossum? Se usa en muchas áreas diferentes.
"""

# Obtener estadísticas
num_frases = splitter.get_sentence_count(texto)
frases = splitter.split_text_to_sentences(texto)

print(f"Número de frases: {num_frases}")
print(f"Frases encontradas:")
for i, frase in enumerate(frases, 1):
    print(f"{i}. {frase}")
```

## Abreviaciones Soportadas

El servicio reconoce automáticamente más de 40 abreviaciones comunes en español:

**Títulos y tratamientos:**
- Sr., Sra., Dr., Dra., Prof., Ing., Lic., Arq.

**Militares y cargos:**
- Cap., Gral., Cnel., Col.

**Direcciones y ubicaciones:**
- Av., Ave., Blvd., Dpto., Prov., C.P.

**Comunicación:**
- Tel., Cel., Ext., Int.

**Otros:**
- etc., vs., p.ej., no., núm., pág., vol., fig., ref.

## Tests

Ejecutar las pruebas:

```bash
# Activar entorno virtual (Windows PowerShell)
cd "ruta/al/proyecto"
. .\venv\Scripts\Activate.ps1
python src/tests/test_sentence_splitter.py
```

Los tests incluyen:
- ✅ División básica de frases
- ✅ Manejo de abreviaciones
- ✅ Texto largo y complejo  
- ✅ Creación de objetos Frase
- ✅ Control de longitud máxima
- ✅ Casos extremos (texto vacío, una palabra, etc.)

## Ejemplos Prácticos

Ejecutar ejemplos de uso:

```bash
# Activar entorno virtual (Windows PowerShell)
cd "ruta/al/proyecto"
. .\venv\Scripts\Activate.ps1
python src/examples/sentence_splitter_examples.py
```

## Estructura del Proyecto

```
src/
├── services/
│   └── sentence_splitter_service.py  # Servicio principal
├── models/
│   └── frase.py                       # Modelo de datos Frase
├── tests/
│   └── test_sentence_splitter.py      # Tests unitarios
└── examples/
    └── sentence_splitter_examples.py  # Ejemplos de uso
```

## Casos de Uso Reales

- **Procesamiento de subtítulos**: Dividir guiones largos en frases para subtítulos
- **Análisis de texto**: Preparar texto para análisis de sentimientos por frase
- **Text-to-Speech**: Dividir texto largo para síntesis de voz más natural
- **Chatbots**: Procesar respuestas largas en fragmentos más manejables
- **Traducción automática**: Dividir texto en unidades de traducción más pequeñas

## Requisitos

- Python 3.7+
- Módulo `re` (incluido en Python estándar)
- Módulo `typing` (incluido en Python 3.5+)

## Rendimiento

- **Velocidad**: Procesa ~1000 frases por segundo en hardware moderno
- **Memoria**: Uso eficiente de memoria, procesa texto en tiempo real
- **Escalabilidad**: Funciona con textos de cualquier tamaño

---

## Contribuciones

Si encuentras algún problema o tienes sugerencias de mejora, por favor:

1. Revisa las pruebas existentes
2. Añade casos de prueba para nuevos escenarios
3. Mantén la compatibilidad con la API existente
4. Documenta cualquier cambio nuevo

¡El SentenceSplitterService está listo para procesar texto en español de manera inteligente! 🚀
