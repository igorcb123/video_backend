"""
Tests para el SentenceSplitterService.
"""
import sys
import os

# Añadir el directorio src al path
from pathlib import Path


# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.sentence_splitter_service import SentenceSplitterService


def test_basic_sentence_splitting():
    """Test básico de división de frases."""
    service = SentenceSplitterService()
    
    texto = "Hola mundo. ¿Cómo estás? ¡Muy bien! Esto es una prueba."
    frases = service.split_text_to_sentences(texto)
    
    expected = [
        "Hola mundo.",
        "¿Cómo estás?",
        "¡Muy bien!",
        "Esto es una prueba."
    ]
    
    print("=== Test Básico ===")
    print(f"Texto original: {texto}")
    print(f"Frases encontradas: {len(frases)}")
    for i, frase in enumerate(frases):
        print(f"  {i+1}: '{frase}'")
    
    assert len(frases) == len(expected), f"Expected {len(expected)} sentences, got {len(frases)}"
    print("✅ Test básico pasado\n")


def test_abbreviations():
    """Test con abreviaciones comunes."""
    service = SentenceSplitterService()
    
    texto = "El Dr. García vive en la calle Sr. López número 123. Estudió en la Universidad Nacional."
    frases = service.split_text_to_sentences(texto)
    
    print("=== Test Abreviaciones ===")
    print(f"Texto original: {texto}")
    print(f"Frases encontradas: {len(frases)}")
    for i, frase in enumerate(frases):
        print(f"  {i+1}: '{frase}'")
    
    # Debe dividir correctamente y no cortar en las abreviaciones
    assert len(frases) == 2, f"Expected 2 sentences, got {len(frases)}"
    print("✅ Test abreviaciones pasado\n")


def test_long_text():
    """Test con texto más largo y complejo."""
    service = SentenceSplitterService()
    
    texto = """
    La inteligencia artificial es una tecnología revolucionaria. Ha cambiado la forma en que trabajamos 
    y vivimos. ¿Pero qué impacto tendrá en el futuro? Nadie lo sabe con certeza. Sin embargo, 
    podemos estar seguros de que seguirá evolucionando. ¡Es emocionante pensar en las posibilidades!
    
    En el ámbito empresarial, la IA está transformando industrias completas. Las empresas que adopten 
    estas tecnologías temprano tendrán ventajas competitivas significativas.
    """
    
    frases = service.split_text_to_sentences(texto)
    
    print("=== Test Texto Largo ===")
    print(f"Texto original (primeros 100 chars): {texto[:100]}...")
    print(f"Frases encontradas: {len(frases)}")
    for i, frase in enumerate(frases):
        print(f"  {i+1}: '{frase}'")
    
    print("✅ Test texto largo pasado\n")


def test_frase_objects():
    """Test creación de objetos Frase."""
    service = SentenceSplitterService()
    
    texto = "Primera frase con tres palabras. Segunda frase con cuatro palabras aquí."
    frases_objetos = service.split_text_to_frase_objects(texto)
    
    print("=== Test Objetos Frase ===")
    print(f"Texto original: {texto}")
    print(f"Objetos Frase creados: {len(frases_objetos)}")
    for frase_obj in frases_objetos:
        print(f"  {frase_obj}")
    
    assert len(frases_objetos) == 2, f"Expected 2 Frase objects, got {len(frases_objetos)}"
    print("✅ Test objetos Frase pasado\n")


def test_max_length():
    """Test división con longitud máxima."""
    service = SentenceSplitterService()
    
    texto = ("Esta es una frase extremadamente larga que supera el límite de caracteres "
             "establecido y debe ser dividida en partes más pequeñas para facilitar "
             "el procesamiento y mejorar la legibilidad del contenido.")
    
    frases_cortas = service.split_with_max_length(texto, max_length=50)
    
    print("=== Test Longitud Máxima ===")
    print(f"Texto original: {texto}")
    print(f"Límite de caracteres: 50")
    print(f"Frases resultantes: {len(frases_cortas)}")
    for i, frase in enumerate(frases_cortas):
        print(f"  {i+1} ({len(frase)} chars): '{frase}'")
        assert len(frase) <= 50, f"Frase {i+1} excede el límite: {len(frase)} characters"
    
    print("✅ Test longitud máxima pasado\n")


def test_sentence_count():
    """Test conteo de frases."""
    service = SentenceSplitterService()
    
    texto = "Una frase. Otra frase más. ¿Una pregunta? ¡Una exclamación!"
    count = service.get_sentence_count(texto)
    
    print("=== Test Conteo ===")
    print(f"Texto: {texto}")
    print(f"Número de frases: {count}")
    
    assert count == 4, f"Expected 4 sentences, got {count}"
    print("✅ Test conteo pasado\n")


def test_edge_cases():
    """Test casos extremos."""
    service = SentenceSplitterService()
    
    # Texto vacío
    frases_empty = service.split_text_to_sentences("")
    assert len(frases_empty) == 0, "Empty text should return empty list"
    
    # Solo espacios
    frases_spaces = service.split_text_to_sentences("   \n\t   ")
    assert len(frases_spaces) == 0, "Whitespace-only text should return empty list"
    
    # Una sola palabra
    frases_word = service.split_text_to_sentences("Hola")
    assert len(frases_word) == 1, "Single word should return one sentence"
    assert frases_word[0] == "Hola"
    
    print("=== Test Casos Extremos ===")
    print("✅ Texto vacío pasado")
    print("✅ Solo espacios pasado") 
    print("✅ Una palabra pasado")
    print()


if __name__ == "__main__":
    print("🚀 Ejecutando tests del SentenceSplitterService...\n")
    
    test_basic_sentence_splitting()
    test_abbreviations()
    test_long_text()
    test_frase_objects()
    test_max_length()
    test_sentence_count()
    test_edge_cases()
    
    print("🎉 ¡Todos los tests pasaron exitosamente!")
