"""
Módulo que gestiona la rotación de claves de API de Pexels,
asegurando no exceder el límite de llamadas por periodo.
"""
from collections import deque
from datetime import datetime, timedelta


class PexelsAPIKeyManager:
    """Gestor de claves API con rotación automática y control de rate limiting."""
    
    def __init__(self, keys, max_calls=200, period_seconds=3600):
        """
        Inicializa el gestor con una lista de claves, límite de llamadas y periodo.
        
        Args:
            keys: Lista de claves API de Pexels
            max_calls: Máximo número de llamadas por periodo (default 200)
            period_seconds: Duración del periodo en segundos (default 3600 = 1 hora)
        """
        if not keys:
            raise ValueError("Se requiere al menos una clave API")
            
        self.keys = deque(keys)
        self.usage = {k: {'count': 0, 'start': datetime.utcnow()} for k in keys}
        self.max_calls = max_calls
        self.period = timedelta(seconds=period_seconds)

    def get_next_key(self):
        """
        Devuelve la siguiente clave disponible dentro del rate limit.
        
        Returns:
            str: Clave API disponible
            
        Raises:
            RuntimeError: Si todas las claves están agotadas
        """
        for _ in range(len(self.keys)):
            key = self.keys[0]
            rec = self.usage[key]
            now = datetime.utcnow()
            
            # Reinicia conteo si pasó el periodo
            if now - rec['start'] >= self.period:
                rec['count'], rec['start'] = 0, now
                
            # Si aún hay llamadas disponibles, usa esta clave
            if rec['count'] < self.max_calls:
                rec['count'] += 1
                self.keys.rotate(-1)
                return key
                
            # Si no, rota y prueba siguiente
            self.keys.rotate(-1)
            
        raise RuntimeError("Todas las claves API están agotadas.")
    
    def get_usage_stats(self):
        """
        Devuelve estadísticas de uso de las claves.
        
        Returns:
            dict: Estadísticas de uso por clave
        """
        stats = {}
        now = datetime.utcnow()
        
        for key, rec in self.usage.items():
            time_since_start = now - rec['start']
            remaining_calls = max(0, self.max_calls - rec['count'])
            
            # Si el periodo ha expirado, las llamadas se resetean
            if time_since_start >= self.period:
                remaining_calls = self.max_calls
                
            stats[key[-10:]] = {  # Solo mostrar últimos 10 caracteres de la clave
                'used_calls': rec['count'] if time_since_start < self.period else 0,
                'remaining_calls': remaining_calls,
                'period_remaining': max(0, (self.period - time_since_start).total_seconds()) if time_since_start < self.period else 0
            }
            
        return stats
    
    def reset_usage(self, key=None):
        """
        Resetea el uso de una clave específica o todas las claves.
        
        Args:
            key: Clave específica a resetear (None para resetear todas)
        """
        if key and key in self.usage:
            self.usage[key] = {'count': 0, 'start': datetime.utcnow()}
        elif key is None:
            for k in self.usage:
                self.usage[k] = {'count': 0, 'start': datetime.utcnow()}
