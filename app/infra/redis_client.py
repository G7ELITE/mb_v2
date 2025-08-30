import redis
from typing import Optional
from app.settings import settings


class RedisClient:
    """Cliente Redis para cache e filas leves."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    def get_client(self) -> Optional[redis.Redis]:
        """Retorna cliente Redis se configurado."""
        if not settings.REDIS_URL:
            return None
            
        if self._client is None:
            self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        return self._client
    
    def set_cache(self, key: str, value: str, expire_seconds: int = 3600) -> bool:
        """Armazena valor no cache com expiração."""
        client = self.get_client()
        if not client:
            return False
        
        try:
            client.setex(key, expire_seconds, value)
            return True
        except Exception:
            return False
    
    def get_cache(self, key: str) -> Optional[str]:
        """Recupera valor do cache."""
        client = self.get_client()
        if not client:
            return None
        
        try:
            return client.get(key)
        except Exception:
            return None


# Instância global do cliente Redis
redis_client = RedisClient()
