"""
Redis Adapter com Fallback In-Memory
Usado quando Redis não está disponível em DEV/TEST
"""
import json
import time
import logging
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class RedisAdapter(ABC):
    """Interface para adapter Redis"""
    
    @abstractmethod
    def ping(self) -> bool:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> int:
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

class RedisClient(RedisAdapter):
    """Adapter Redis real"""
    
    def __init__(self, redis_url: str):
        import redis
        self.client = redis.from_url(redis_url)
    
    def ping(self) -> bool:
        try:
            return self.client.ping()
        except Exception:
            return False
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        try:
            result = self.client.get(key)
            return result.decode('utf-8') if result else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def delete(self, key: str) -> int:
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

class InMemoryRedis(RedisAdapter):
    """Adapter Redis in-memory para DEV/TEST"""
    
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        logger.info("🧠 Redis in-memory adapter ativado")
    
    def ping(self) -> bool:
        return True
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            entry = {
                "value": value,
                "expires": time.time() + ex if ex else None
            }
            self._data[key] = entry
            return True
        except Exception as e:
            logger.error(f"InMemory SET error: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        try:
            if key not in self._data:
                return None
            
            entry = self._data[key]
            
            # Verificar expiração
            if entry["expires"] and time.time() > entry["expires"]:
                del self._data[key]
                return None
            
            return entry["value"]
        except Exception as e:
            logger.error(f"InMemory GET error: {e}")
            return None
    
    def delete(self, key: str) -> int:
        try:
            if key in self._data:
                del self._data[key]
                return 1
            return 0
        except Exception as e:
            logger.error(f"InMemory DELETE error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        try:
            if key not in self._data:
                return False
            
            entry = self._data[key]
            
            # Verificar expiração
            if entry["expires"] and time.time() > entry["expires"]:
                del self._data[key]
                return False
            
            return True
        except Exception as e:
            logger.error(f"InMemory EXISTS error: {e}")
            return False

def get_redis_adapter() -> RedisAdapter:
    """Factory para obter adapter Redis"""
    from app.settings import settings
    
    # Se REDIS_URL vazio ou None, usar in-memory
    if not settings.REDIS_URL:
        logger.info("{"evt":"redis_fallback", "mode":"inmemory"}")
        return InMemoryRedis()
    
    # Tentar Redis real
    try:
        adapter = RedisClient(settings.REDIS_URL)
        if adapter.ping():
            logger.info("{"evt":"redis_connected", "mode":"real"}")
            return adapter
        else:
            logger.warning("Redis PING falhou, usando in-memory")
            logger.info("{"evt":"redis_fallback", "mode":"inmemory"}")
            return InMemoryRedis()
    except Exception as e:
        logger.warning(f"Redis não disponível: {e}, usando in-memory")
        logger.info("{"evt":"redis_fallback", "mode":"inmemory"}")
        return InMemoryRedis()

# Instância global
_redis_adapter: Optional[RedisAdapter] = None

def get_redis() -> RedisAdapter:
    """Obter instância global do Redis adapter"""
    global _redis_adapter
    if _redis_adapter is None:
        _redis_adapter = get_redis_adapter()
    return _redis_adapter
