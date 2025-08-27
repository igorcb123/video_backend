"""
Servicio para dividir texto largo en frases individuales.
"""
import re
from typing import List, Optional
from models.frase import Frase


class SentenceSplitterService:
    """
    Servicio que divide texto largo en español en frases individuales.
    
    Utiliza patrones de expresiones regulares optimizados para el español
    para identificar límites de frases de manera precisa.
    """
    
    def __init__(self):
        """Inicializa el servicio con los patrones de división de frases."""
        # Patrón principal para dividir frases
        # Busca puntos, signos de exclamación, interrogación seguidos de espacio y mayúscula
        # o al final del texto
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])|(?<=[.!?])$',
            re.MULTILINE | re.UNICODE
        )
        
        # Patrón para limpiar espacios múltiples y saltos de línea
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Patrones de abreviaciones comunes en español que NO terminan frase
        self.abbreviations = {
            'Sr.', 'Sra.', 'Dr.', 'Dra.', 'Prof.', 'Ing.', 'Lic.', 
            'Arq.', 'Cap.', 'Gral.', 'Cnel.', 'etc.', 'vs.', 'p.ej.',
            'a.C.', 'd.C.', 'n.º', 'núm.', 'pág.', 'tel.', 'vol.',
            'art.', 'inc.', 'párr.', 'ej.', 'fig.', 'ref.', 'cf.',
            'V.', 'Ud.', 'Vd.', 'Uds.', 'Vds.', 'Av.', 'Ave.', 'no.',
            'nro.', 'núm.', 'Blvd.', 'Dpto.', 'Depto.', 'Prov.',
            'Col.', 'Frag.', 'Edo.', 'Mpio.', 'C.P.', 'Tel.', 'Cel.',
            'Ext.', 'Int.', 'Apt.', 'Ste.', 'Fte.', 'Pte.', 'Nte.',
            'Ote.', 'Sur.', 'Norte.', 'Este.', 'Oeste.'
        }

    def split_text_to_sentences(self, texto: str) -> List[str]:
        """
        Divide un texto largo en una lista de frases individuales.
        
        Args:
            texto (str): El texto a dividir en frases.
            
        Returns:
            List[str]: Lista de frases individuales.
        """
        if not texto or not texto.strip():
            return []
            
        # Limpiar y normalizar el texto
        texto_limpio = self._clean_text(texto)
        
        # Procesar abreviaciones para evitar falsos positivos
        texto_procesado = self._handle_abbreviations(texto_limpio)
        
        # Dividir en frases usando un enfoque más simple y robusto
        frases = []
        frase_actual = ""
        
        i = 0
        while i < len(texto_procesado):
            char = texto_procesado[i]
            frase_actual += char
            
            # Verificar si hemos llegado a un final de frase
            if char in '.!?':
                # Verificar que no sea parte de una abreviación ya procesada
                if '◊' not in frase_actual[-10:]:  # Buscar el marcador en los últimos caracteres
                    # Verificar si es el final del texto o si lo que sigue es espacio + mayúscula
                    if i == len(texto_procesado) - 1:  # Final del texto
                        frase_final = self._restore_abbreviations(frase_actual.strip())
                        if frase_final:
                            frases.append(frase_final)
                        frase_actual = ""
                    elif i < len(texto_procesado) - 1:
                        # Buscar el próximo carácter que no sea espacio
                        j = i + 1
                        while j < len(texto_procesado) and texto_procesado[j].isspace():
                            frase_actual += texto_procesado[j]
                            j += 1
                        
                        # Si encontramos una mayúscula o símbolo de inicio de frase
                        if j < len(texto_procesado) and (
                            texto_procesado[j].isupper() or 
                            texto_procesado[j] in '¿¡'
                        ):
                            frase_final = self._restore_abbreviations(frase_actual.strip())
                            if frase_final:
                                frases.append(frase_final)
                            frase_actual = ""
                            i = j - 1  # Ajustar índice
                        
            i += 1
        
        # Agregar la última frase si queda algo
        if frase_actual.strip():
            frase_final = self._restore_abbreviations(frase_actual.strip())
            if frase_final:
                frases.append(frase_final)
        
        return frases

    def split_text_to_frase_objects(self, texto: str) -> List[Frase]:
        """
        Divide un texto en frases y retorna objetos Frase con información de posición.
        
        Args:
            texto (str): El texto a dividir en frases.
            
        Returns:
            List[Frase]: Lista de objetos Frase con información de orden y posición.
        """
        frases_texto = self.split_text_to_sentences(texto)
        frases_objetos = []
        
        # Para este método simple, asumimos que cada frase es una "palabra"
        # En un sistema más complejo, se integraría con un tokenizador de palabras
        for i, frase_texto in enumerate(frases_texto):
            # Contar palabras aproximadamente (dividir por espacios)
            palabras_en_frase = len(frase_texto.split())
            
            # Calcular posición aproximada de palabras
            if i == 0:
                palabra_inicio = 0
            else:
                # Sumar palabras de frases anteriores
                palabras_anteriores = sum(
                    len(f.split()) for f in frases_texto[:i]
                )
                palabra_inicio = palabras_anteriores
            
            palabra_fin = palabra_inicio + palabras_en_frase - 1
            
            frase_obj = Frase(
                orden=i + 1,
                palabra_inicio=palabra_inicio,
                palabra_fin=palabra_fin
            )
            frases_objetos.append(frase_obj)
        
        return frases_objetos

    def get_sentence_count(self, texto: str) -> int:
        """
        Cuenta el número de frases en un texto.
        
        Args:
            texto (str): El texto a analizar.
            
        Returns:
            int: Número de frases encontradas.
        """
        return len(self.split_text_to_sentences(texto))

    def _clean_text(self, texto: str) -> str:
        """Limpia y normaliza el texto."""
        # Reemplazar múltiples espacios y saltos de línea con un espacio
        texto_limpio = self.whitespace_pattern.sub(' ', texto)
        # Quitar espacios al inicio y final
        return texto_limpio.strip()

    def _handle_abbreviations(self, texto: str) -> str:
        """
        Reemplaza temporalmente las abreviaciones para evitar falsos cortes.
        """
        texto_procesado = texto
        for abbr in self.abbreviations:
            # Reemplazar el punto de la abreviación con un marcador temporal
            placeholder = abbr.replace('.', '◊')
            texto_procesado = texto_procesado.replace(abbr, placeholder)
        return texto_procesado

    def _restore_abbreviations(self, texto: str) -> str:
        """
        Restaura las abreviaciones originales.
        """
        texto_restaurado = texto
        for abbr in self.abbreviations:
            placeholder = abbr.replace('.', '◊')
            texto_restaurado = texto_restaurado.replace(placeholder, abbr)
        return texto_restaurado

    def split_with_max_length(self, texto: str, max_length: int = 200) -> List[str]:
        """
        Divide el texto en frases respetando una longitud máxima.
        
        Si una frase supera la longitud máxima, intenta dividirla en sub-frases
        usando puntos y comas, puntos y comas, o dos puntos.
        
        Args:
            texto (str): El texto a dividir.
            max_length (int): Longitud máxima por frase.
            
        Returns:
            List[str]: Lista de frases con longitud controlada.
        """
        frases_base = self.split_text_to_sentences(texto)
        frases_finales = []
        
        for frase in frases_base:
            if len(frase) <= max_length:
                frases_finales.append(frase)
            else:
                # Intentar subdividir frases largas
                sub_frases = self._split_long_sentence(frase, max_length)
                frases_finales.extend(sub_frases)
        
        return frases_finales

    def _split_long_sentence(self, frase: str, max_length: int) -> List[str]:
        """
        Divide una frase larga en sub-frases más pequeñas.
        """
        # Intentar dividir por signos de puntuación secundarios
        separadores = [';', ':', ',']
        
        for sep in separadores:
            if sep in frase:
                partes = frase.split(sep)
                if len(partes) > 1:
                    sub_frases = []
                    for i, parte in enumerate(partes):
                        parte = parte.strip()
                        if parte:
                            # Añadir el separador de vuelta excepto en la última parte
                            if i < len(partes) - 1:
                                parte += sep
                            
                            if len(parte) <= max_length:
                                sub_frases.append(parte)
                            else:
                                # Si aún es muy larga, dividir por espacios
                                palabras = parte.split()
                                sub_frase_actual = ""
                                
                                for palabra in palabras:
                                    if len(sub_frase_actual + " " + palabra) <= max_length:
                                        if sub_frase_actual:
                                            sub_frase_actual += " " + palabra
                                        else:
                                            sub_frase_actual = palabra
                                    else:
                                        if sub_frase_actual:
                                            sub_frases.append(sub_frase_actual)
                                        sub_frase_actual = palabra
                                
                                if sub_frase_actual:
                                    sub_frases.append(sub_frase_actual)
                    
                    return sub_frases
        
        # Si no se puede dividir con puntuación, dividir por espacios
        palabras = frase.split()
        sub_frases = []
        sub_frase_actual = ""
        
        for palabra in palabras:
            if len(sub_frase_actual + " " + palabra) <= max_length:
                if sub_frase_actual:
                    sub_frase_actual += " " + palabra
                else:
                    sub_frase_actual = palabra
            else:
                if sub_frase_actual:
                    sub_frases.append(sub_frase_actual)
                sub_frase_actual = palabra
        
        if sub_frase_actual:
            sub_frases.append(sub_frase_actual)
        
        return sub_frases if sub_frases else [frase]
