"""
Redis Cache sistemi - Production-ready
In-memory fallback ile çalışır
"""
import json
import time
from typing import Any, Optional, Callable, Awaitable
from src.config import settings
import structlog

logger = structlog.get_logger()

# In-memory fallback: {key: (value, expiry_timestamp)}
_memory_cache: dict[str, tuple[Any, float]] = {}
_DEFAULT_TTL = settings.redis_cache_ttl


async def _get_redis_client():
    """Redis client - lazy init. Redis yoksa None döner."""
    try:
        url = (settings.redis_url or "").strip()
        if not url:
            logger.warning("redis_disabled", reason="REDIS_URL not set")
            return None
        
        try:
            import redis.asyncio as redis  # type: ignore
        except (ImportError, AttributeError):
            # Eski redis versiyonları için fallback
            try:
                import redis  # type: ignore
            except ImportError:
                logger.warning("redis_unavailable", reason="redis package not installed")
                return None
        
        client = redis.from_url(url, decode_responses=True)
        await client.ping()  # Connection test
        return client
    except ImportError:
        logger.warning("redis_unavailable", reason="redis package not installed")
        return None
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return None


async def get_cached(
    key: str,
    fetch_fn: Optional[Callable[[], Awaitable[Any]]] = None,
    ttl: int = _DEFAULT_TTL
) -> Optional[Any]:
    """
    Cache'den veri al. Yoksa fetch_fn çağır ve cache'e yaz.
    
    Args:
        key: Cache anahtarı
        fetch_fn: async callable, cache miss durumunda çağrılır
        ttl: Time to live (saniye)
    
    Returns:
        Cached veya fetch edilmiş değer
    """
    client = None
    try:
        # Redis'ten dene
        client = await _get_redis_client()
        if client:
            raw = await client.get(key)
            if raw:
                try:
                    value = json.loads(raw)
                    logger.debug("cache_hit", key=key, source="redis")
                    return value
                except json.JSONDecodeError:
                    # Raw string
                    logger.debug("cache_hit", key=key, source="redis")
                    return raw
        
        # In-memory fallback
        now = time.time()
        if key in _memory_cache:
            value, expiry = _memory_cache[key]
            if now < expiry:
                logger.debug("cache_hit", key=key, source="memory")
                return value
        
        # Cache miss
        _memory_cache.pop(key, None)
        logger.debug("cache_miss", key=key)
        
        # Fetch fonksiyonu varsa çağır
        if fetch_fn:
            value = await fetch_fn() if callable(fetch_fn) else fetch_fn
            await set_cached(key, value, ttl)
            return value
        
        return None
    
    except Exception as e:
        logger.error("cache_get_error", key=key, error=str(e))
        # Fetch fn varsa direkt çağır (cache bypass)
        if fetch_fn:
            return await fetch_fn() if callable(fetch_fn) else fetch_fn
        return None
    
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


async def set_cached(key: str, value: Any, ttl: int = _DEFAULT_TTL) -> bool:
    """
    Cache'e veri yaz.
    
    Args:
        key: Cache anahtarı
        value: Kaydedilecek değer
        ttl: Time to live (saniye)
    
    Returns:
        Başarılı ise True
    """
    client = None
    try:
        # JSON serialize et
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value, ensure_ascii=False)
        else:
            serialized = str(value)
        
        # Redis'e yaz
        client = await _get_redis_client()
        if client:
            await client.set(key, serialized, ex=ttl)
            logger.debug("cache_set", key=key, ttl=ttl, target="redis")
        
        # In-memory'ye de yaz
        _memory_cache[key] = (value, time.time() + ttl)
        logger.debug("cache_set", key=key, ttl=ttl, target="memory")
        
        return True
    
    except Exception as e:
        logger.error("cache_set_error", key=key, error=str(e))
        # En azından memory'ye yaz
        try:
            _memory_cache[key] = (value, time.time() + ttl)
            return True
        except Exception:
            return False
    
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


async def delete_cached(key: str) -> bool:
    """
    Cache'den sil.
    
    Args:
        key: Cache anahtarı
    
    Returns:
        Başarılı ise True
    """
    client = None
    try:
        # Memory'den sil
        _memory_cache.pop(key, None)
        
        # Redis'ten sil
        client = await _get_redis_client()
        if client:
            await client.delete(key)
        
        logger.debug("cache_deleted", key=key)
        return True
    
    except Exception as e:
        logger.error("cache_delete_error", key=key, error=str(e))
        return False
    
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


async def delete_pattern(pattern: str) -> int:
    """
    Pattern'e uyan tüm anahtarları sil.
    
    Args:
        pattern: Redis pattern (örn: "node:*")
    
    Returns:
        Silinen anahtar sayısı
    """
    client = None
    count = 0
    
    try:
        # Memory'den sil (basit string match)
        deleted_keys = [k for k in _memory_cache.keys() if pattern.replace("*", "") in k]
        for k in deleted_keys:
            _memory_cache.pop(k, None)
        count += len(deleted_keys)
        
        # Redis'ten sil
        client = await _get_redis_client()
        if client:
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
        
        logger.info("cache_pattern_deleted", pattern=pattern, count=count)
        return count
    
    except Exception as e:
        logger.error("cache_pattern_delete_error", pattern=pattern, error=str(e))
        return count
    
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


async def clear_all() -> bool:
    """Tüm cache'i temizle (dikkatli kullan!)"""
    client = None
    try:
        # Memory'yi temizle
        _memory_cache.clear()
        
        # Redis'i temizle
        client = await _get_redis_client()
        if client:
            await client.flushdb()
        
        logger.warning("cache_cleared")
        return True
    
    except Exception as e:
        logger.error("cache_clear_error", error=str(e))
        return False
    
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


# Helper fonksiyonlar

async def cache_node_stats(node_address: str, stats: dict, ttl: int = 60) -> bool:
    """Düğüm istatistiklerini cache'le"""
    return await set_cached(f"node:stats:{node_address}", stats, ttl)


async def get_node_stats(node_address: str) -> Optional[dict]:
    """Düğüm istatistiklerini cache'den al"""
    return await get_cached(f"node:stats:{node_address}")


async def invalidate_node_cache(node_address: str) -> int:
    """Düğümle ilgili tüm cache'i temizle"""
    return await delete_pattern(f"node:*:{node_address}*")


async def cache_task_result(task_uid: str, result: Any, ttl: int = 3600) -> bool:
    """Görev sonucunu cache'le"""
    return await set_cached(f"task:result:{task_uid}", result, ttl)


async def get_task_result(task_uid: str) -> Optional[Any]:
    """Görev sonucunu cache'den al"""
    return await get_cached(f"task:result:{task_uid}")
