"""
Ejemplo de uso del SentenceSplitterService.

Este script demuestra cómo usar el servicio para dividir texto largo
en frases individuales en español.
"""
import sys
import os

# Añadir el directorio padre al path para poder importar desde src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sentence_splitter_service import SentenceSplitterService


def ejemplo_basico():
    """Ejemplo básico de uso del servicio."""
    print("=" * 60)
    print("EJEMPLO BÁSICO - División de Frases")
    print("=" * 60)
    
    service = SentenceSplitterService()
    
    texto_ejemplo = """
    Buenos días, mi nombre es Juan Pérez. Soy desarrollador de software con 5 años de experiencia. 
    ¿Te gustaría conocer más sobre mi trabajo? He trabajado en proyectos de inteligencia artificial, 
    desarrollo web y aplicaciones móviles. ¡Es muy emocionante! 
    
    Además, tengo experiencia con Python, JavaScript, y bases de datos. Mi objetivo es seguir 
    aprendiendo nuevas tecnologías. ¿Qué opinas de la programación funcional?
    """
    
    frases = service.split_text_to_sentences(texto_ejemplo)
    
    print(f"📝 Texto original ({len(texto_ejemplo)} caracteres):")
    print(texto_ejemplo.strip())
    print(f"\n🔍 Resultado: {len(frases)} frases encontradas:")
    print("-" * 40)
    
    for i, frase in enumerate(frases, 1):
        print(f"{i:2}. {frase}")


def ejemplo_con_objetos_frase():
    """Ejemplo usando objetos Frase."""
    print("\n" + "=" * 60)
    print("EJEMPLO - Objetos Frase")
    print("=" * 60)
    
    service = SentenceSplitterService()
    
    texto = "La tecnología avanza rápidamente. Los desarrolladores deben adaptarse constantemente. ¿Estás preparado para el cambio?"
    
    frases_objetos = service.split_text_to_frase_objects(texto)
    
    print(f"📝 Texto: {texto}")
    print(f"\n🎯 Objetos Frase creados:")
    print("-" * 40)
    
    for frase_obj in frases_objetos:
        print(f"Orden: {frase_obj.orden}, Palabras: {frase_obj.palabra_inicio}-{frase_obj.palabra_fin}")


def ejemplo_longitud_controlada():
    """Ejemplo con control de longitud máxima."""
    print("\n" + "=" * 60)
    print("EJEMPLO - Longitud Controlada")
    print("=" * 60)
    
    service = SentenceSplitterService()
    
    texto_largo = """
    La inteligencia artificial ha revolucionado completamente la forma en que las empresas 
    procesan información, analizan datos, toman decisiones estratégicas y optimizan sus 
    operaciones diarias para mejorar la eficiencia, reducir costos y aumentar la 
    productividad en todos los departamentos de la organización.
    """
    
    # División normal
    frases_normales = service.split_text_to_sentences(texto_largo)
    
    # División con longitud máxima
    frases_cortas = service.split_with_max_length(texto_largo, max_length=80)
    
    print(f"📝 Texto original:")
    print(texto_largo.strip())
    
    print(f"\n📊 División normal ({len(frases_normales)} frases):")
    print("-" * 40)
    for i, frase in enumerate(frases_normales, 1):
        print(f"{i}. ({len(frase)} chars) {frase}")
    
    print(f"\n✂️ División con máximo 80 caracteres ({len(frases_cortas)} frases):")
    print("-" * 40)
    for i, frase in enumerate(frases_cortas, 1):
        print(f"{i}. ({len(frase)} chars) {frase}")


def ejemplo_con_abreviaciones():
    """Ejemplo manejando abreviaciones."""
    print("\n" + "=" * 60)
    print("EJEMPLO - Manejo de Abreviaciones")
    print("=" * 60)
    
    service = SentenceSplitterService()
    
    texto_abrev = """
    El Dr. Martínez trabaja en el Hospital Gral. San Juan ubicado en la Av. Libertador no. 456. 
    La Dra. López es especialista en cardiología, etc. Su consulta está abierta de lunes a viernes.
    Para más información puede llamar al tel. 555-1234 o visitar la pág. web oficial.
    """
    
    frases = service.split_text_to_sentences(texto_abrev)
    
    print(f"📝 Texto con abreviaciones:")
    print(texto_abrev.strip())
    
    print(f"\n🔍 Frases identificadas ({len(frases)} total):")
    print("-" * 40)
    for i, frase in enumerate(frases, 1):
        print(f"{i}. {frase}")


def estadisticas_texto():
    """Ejemplo mostrando estadísticas del texto."""
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS DE TEXTO")
    print("=" * 60)
    
    service = SentenceSplitterService()
    
    texto = """
    Python es un lenguaje de programación muy popular. Es fácil de aprender y muy versátil. 
    ¿Sabías que fue creado por Guido van Rossum? Se usa en desarrollo web, ciencia de datos, 
    inteligencia artificial y muchas otras áreas. ¡Es realmente increíble!
    
    Muchas empresas grandes como Google, Netflix y Instagram lo utilizan. Si quieres 
    aprender programación, Python es una excelente opción para empezar.
    """
    
    # Obtener estadísticas
    num_frases = service.get_sentence_count(texto)
    frases = service.split_text_to_sentences(texto)
    num_caracteres = len(texto.strip())
    num_palabras = len(texto.split())
    
    # Calcular longitudes
    longitudes = [len(frase) for frase in frases]
    longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
    frase_mas_larga = max(frases, key=len) if frases else ""
    frase_mas_corta = min(frases, key=len) if frases else ""
    
    print(f"📊 ESTADÍSTICAS:")
    print("-" * 30)
    print(f"Total de caracteres: {num_caracteres}")
    print(f"Total de palabras: {num_palabras}")
    print(f"Total de frases: {num_frases}")
    print(f"Longitud promedio por frase: {longitud_promedio:.1f} caracteres")
    print(f"Frase más larga: {len(frase_mas_larga)} caracteres")
    print(f"Frase más corta: {len(frase_mas_corta)} caracteres")
    
    print(f"\n📝 Frase más larga:")
    print(f"'{frase_mas_larga}'")
    
    print(f"\n📝 Frase más corta:")
    print(f"'{frase_mas_corta}'")


if __name__ == "__main__":
    print("🚀 EJEMPLOS DE USO - SentenceSplitterService")
    print("👉 Servicio para dividir texto largo en frases individuales\n")
    
    # Ejecutar todos los ejemplos
    ejemplo_basico()
    ejemplo_con_objetos_frase()
    ejemplo_longitud_controlada()
    ejemplo_con_abreviaciones()
    estadisticas_texto()
    
    print("\n" + "🎉" * 20)
    print("¡Ejemplos completados! El SentenceSplitterService está listo para usar.")
    print("🎉" * 20)
