"""
Cache Decorator - Decoradores para memoización automática.

Proporciona:
- @cached: Para funciones síncronas
- @async_cached: Para funciones asíncronas
"""

import functools
import logging
import asyncio
from typing import Any, Callable, Optional, TypeVar
from concurrent.futures import ThreadPoolExecutor
from .redis_client import RedisClient

logger = logging.getLogger(__name__)

# Instancia global de Redis (inicializada por CacheManager)
_redis_client: Optional[RedisClient] = None
_thread_executor: Optional[ThreadPoolExecutor] = None

F = TypeVar('F', bound=Callable[..., Any])
AF = TypeVar('AF', bound=Callable[..., Any])


def set_redis_client(client: RedisClient) -> None:
    """Register Redis client globally for cache decorators.
    
    Called by CacheManager to provide Redis instance to decorators.
    Also initializes ThreadPoolExecutor for safe event loop operations.
    
    Args:
        client: RedisClient instance to use for caching.
    """
    global _redis_client, _thread_executor
    _redis_client = client
    # Initialize thread pool for async-safe Redis operations
    if _thread_executor is None:
        _thread_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cache_")


def cached(ttl: Optional[int] = None) -> Callable[[F], F]:
    """Decorator for caching synchronous function results.
    
    Automatically caches function results in Redis with optional TTL.
    Gracefully degrades if Redis unavailable (executes function normally).
    Thread-safe: Can be called from both sync and async contexts.
    
    Args:
        ttl: Time-to-live in seconds (default: use RedisClient default)
        
    Returns:
        Decorated function that caches results.
        
    Example:
        @cached(ttl=3600)
        def expensive_operation(x, y):
            return x + y
            
    Note:
        - Cache keys are deterministic based on function name and args
        - Logs cache hits for monitoring
        - Fails gracefully if Redis connection fails
        - Uses ThreadPoolExecutor for safe event loop handling
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _redis_client:
                logger.debug(f"Redis not available, executing {func.__name__} directly")
                return func(*args, **kwargs)

            try:
                cache_key = _redis_client.generate_key(func.__name__, args, kwargs)
                
                # Check if we're in an async context
                try:
                    asyncio.get_running_loop()
                    in_async_context = True
                except RuntimeError:
                    in_async_context = False
                
                # If in async context, delegate to thread pool to avoid deadlock
                if in_async_context:
                    loop = asyncio.get_running_loop()
                    cached_value = loop.run_in_executor(
                        _thread_executor,
                        _redis_sync_get,
                        cache_key
                    )
                    # Can't await in sync decorator, so return function result
                    result = func(*args, **kwargs)
                    try:
                        loop.run_in_executor(_thread_executor, _redis_sync_set, cache_key, result, ttl)
                    except Exception as e:
                        logger.warning(f"Failed to cache result: {e}")
                    return result
                
                # Safe path for non-async context: use new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    cached_value = loop.run_until_complete(_redis_client.get(cache_key))
                    if cached_value is not None:
                        logger.info(f"⚡ Cache hit: {func.__name__}")
                        return cached_value

                    result = func(*args, **kwargs)
                    loop.run_until_complete(_redis_client.set(cache_key, result, ttl))
                    return result
                finally:
                    loop.close()

            except Exception as e:
                logger.error(f"✗ Cache error in {func.__name__}: {e}")
                return func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator


def _redis_sync_get(key: str) -> Any:
    """Helper function to get from Redis in thread pool (sync wrapper)."""
    # This runs in a thread, so we can create our own event loop safely
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_redis_client.get(key))
    finally:
        loop.close()


def _redis_sync_set(key: str, value: Any, ttl: Optional[int]) -> None:
    """Helper function to set in Redis in thread pool (sync wrapper)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_redis_client.set(key, value, ttl))
    finally:
        loop.close()


def async_cached(ttl: Optional[int] = None) -> Callable[[AF], AF]:
    """Decorator for caching asynchronous function results.
    
    Automatically caches async function results in Redis with optional TTL.
    Gracefully degrades if Redis unavailable (executes function normally).
    
    Args:
        ttl: Time-to-live in seconds (default: use RedisClient default)
        
    Returns:
        Decorated async function that caches results.
        
    Example:
        @async_cached(ttl=3600)
        async def fetch_endpoints(url):
            return await http.get(url)
            
    Note:
        - Cache keys are deterministic based on function name and args
        - Logs cache hits for monitoring
        - Fails gracefully if Redis connection fails
        - Recommended for network I/O and expensive operations
    """
    def decorator(func: AF) -> AF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _redis_client:
                # Si Redis no está disponible, ejecutar función normal
                logger.debug(f"Redis not available, executing {func.__name__} directly")
                return await func(*args, **kwargs)

            try:
                # Generar clave de cache
                cache_key = _redis_client.generate_key(func.__name__, args, kwargs)

                # Intentar obtener del cache
                cached_value = await _redis_client.get(cache_key)
                if cached_value is not None:
                    logger.info(f"⚡ Cache hit: {func.__name__}")
                    return cached_value

                # Ejecutar función asincrónica
                result = await func(*args, **kwargs)

                # Almacenar en cache
                await _redis_client.set(cache_key, result, ttl)

                return result

            except Exception as e:
                logger.error(f"✗ Cache error in {func.__name__}: {e}")
                # Si falla cache, ejecutar función normalmente
                return await func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator
