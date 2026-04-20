"""
Tiered Cache System - L1 Local + L2 Redis + L3 Database caching.

Proporciona:
- L1 Cache: Local in-memory LRU (rápido, pequeño)
- L2 Cache: Redis (rápido, mediano)
- L3 Cache: Database (lento, grande)
- Cache warming (precarga de datos frecuentes)
- Smart invalidation (invalida todos los niveles)
"""

import logging
import json
from typing import Any, Callable, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio

logger = logging.getLogger(__name__)


class LRUCache:
    """Local LRU (Least Recently Used) in-memory cache.
    
    Primer nivel de caché: rápido, pequeño, boundado.
    Evita viajes a Redis para datos calientes.
    
    Features:
    - O(1) get/set
    - Automatic eviction when maxsize exceeded
    - TTL support per entry
    - Statistics tracking
    """
    
    def __init__(self, maxsize: int = 1000, default_ttl: int = 300):
        """
        Inicializa LRU cache.
        
        Args:
            maxsize: Máximo número de entradas
            default_ttl: TTL por defecto en segundos
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Tuple[Any, datetime]] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_puts": 0
        }
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache (L1).
        
        Args:
            key: Cache key
            
        Returns:
            Valor cacheado o None si no existe/expiró
        """
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        value, expiry = self.cache[key]
        
        # Verificar si expiró
        if datetime.now() > expiry:
            del self.cache[key]
            self.stats["misses"] += 1
            return None
        
        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.stats["hits"] += 1
        return value
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Almacena valor en cache (L1).
        
        Args:
            key: Cache key
            value: Valor a cachear
            ttl: Time-to-live en segundos (default: default_ttl)
        """
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        # Si la key ya existe, removerla primero
        if key in self.cache:
            del self.cache[key]
        
        # Si alcanzamos maxsize, evict oldest entry (FIFO)
        if len(self.cache) >= self.maxsize:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
            self.logger.debug(f"Evicted {oldest_key} from L1 cache")
        
        # Add new entry at end
        self.cache[key] = (value, expiry)
        self.stats["total_puts"] += 1
    
    def delete(self, key: str) -> bool:
        """Elimina entrada del cache.
        
        Args:
            key: Cache key
            
        Returns:
            True si se eliminou, False si no existía
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Limpia todo el cache L1."""
        self.cache.clear()
        logger.info("L1 cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "level": "L1_LOCAL",
            **self.stats,
            "hit_ratio": f"{hit_ratio:.2%}",
            "current_size": len(self.cache),
            "max_size": self.maxsize
        }


class TieredCacheManager:
    """Gestor de caché en 3 niveles.
    
    L1: Local LRU (rápido, pequeño - 1000 entries)
    L2: Redis (rápido, mediano - GB)
    L3: Database (lento, grande - TB)
    
    Estrategia:
    - Siempre checkear L1 primero
    - Si miss, checkear L2
    - Si miss, checkear L3
    - Si hit, llenar niveles superiores
    """
    
    def __init__(self, redis_client=None, l1_maxsize: int = 1000):
        """
        Inicializa gestor de caché en 3 niveles.
        
        Args:
            redis_client: Cliente Redis para L2
            l1_maxsize: Tamaño máximo del LRU local
        """
        self.l1 = LRUCache(maxsize=l1_maxsize)
        self.l2_client = redis_client  # Redis
        self.l3_query_fn = None  # Database query function
        self.logger = logging.getLogger(__name__)
    
    def set_database_query_function(self, fn: Callable) -> None:
        """Registra función para queries a la base de datos (L3).
        
        Args:
            fn: Async function que toma clave y retorna valor
        """
        self.l3_query_fn = fn
    
    async def get(self, key: str, fetch_fn: Optional[Callable] = None) -> Optional[Any]:
        """Obtiene valor usando estrategia tiered (L1 → L2 → L3 → fetch_fn).
        
        Args:
            key: Cache key
            fetch_fn: Función para obtener valor si no está en ningún nivel
            
        Returns:
            Valor cacheado o None
        """
        # L1: Local cache (rápido)
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # L2: Redis cache (si disponible)
        if self.l2_client:
            try:
                value = await self.l2_client.get(key)
                if value is not None:
                    # Llenar L1 con el valor de L2
                    self.l1.put(key, value, ttl=300)  # 5min TTL en L1
                    return value
            except Exception as e:
                self.logger.warning(f"L2 cache error: {e}")
        
        # L3: Database (si hay función registrada)
        if self.l3_query_fn:
            try:
                value = await self.l3_query_fn(key)
                if value is not None:
                    # Llenar L1 y L2 con el valor de L3
                    self.l1.put(key, value, ttl=300)
                    if self.l2_client:
                        await self.l2_client.set(key, value, 3600)  # 1h TTL en L2
                    return value
            except Exception as e:
                self.logger.warning(f"L3 query error: {e}")
        
        # Custom fetch function (si se proporciona)
        if fetch_fn:
            try:
                value = await fetch_fn() if asyncio.iscoroutinefunction(fetch_fn) else fetch_fn()
                if value is not None:
                    # Llenar todos los niveles
                    self.l1.put(key, value, ttl=300)
                    if self.l2_client:
                        await self.l2_client.set(key, value, 3600)
                    return value
            except Exception as e:
                self.logger.error(f"Fetch function error: {e}")
        
        return None
    
    async def put(self, key: str, value: Any, ttl_l1: int = 300, ttl_l2: int = 3600) -> None:
        """Almacena valor en todos los niveles.
        
        Args:
            key: Cache key
            value: Valor a cachear
            ttl_l1: TTL para L1 (seconds)
            ttl_l2: TTL para L2 (seconds)
        """
        # L1: Always
        self.l1.put(key, value, ttl=ttl_l1)
        
        # L2: If Redis available
        if self.l2_client:
            try:
                await self.l2_client.set(key, value, ttl_l2)
            except Exception as e:
                self.logger.warning(f"Failed to put in L2: {e}")
    
    async def delete(self, key: str) -> None:
        """Elimina entrada de todos los niveles.
        
        Args:
            key: Cache key
        """
        self.l1.delete(key)
        
        if self.l2_client:
            try:
                await self.l2_client.delete(key)
            except Exception as e:
                self.logger.warning(f"Failed to delete from L2: {e}")
    
    async def clear_by_pattern(self, pattern: str) -> int:
        """Elimina todas las claves que coincidan con patrón.
        
        Args:
            pattern: Patrón glob (ej: "cache:graphql:*")
            
        Returns:
            Número de claves eliminadas
        """
        deleted = 0
        
        # L1: Manual pattern matching (no pattern matching native)
        keys_to_delete = [k for k in self.l1.cache.keys() if pattern.replace("*", "") in k]
        for key in keys_to_delete:
            self.l1.delete(key)
            deleted += 1
        
        # L2: Pattern deletion
        if self.l2_client:
            try:
                deleted += await self.l2_client.delete_pattern(pattern)
            except Exception as e:
                self.logger.warning(f"Failed to clear L2 pattern: {e}")
        
        return deleted
    
    def get_tiered_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas consolidadas de todos los niveles.
        
        Returns:
            Dict con stats de L1, L2, etc
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "l1": self.l1.get_stats(),
            "l2": "redis_client available" if self.l2_client else "not_available",
            "l3": "database_function available" if self.l3_query_fn else "not_available"
        }
        
        # Intentar stats de L2
        if self.l2_client and hasattr(self.l2_client, 'get_stats'):
            try:
                # Aquí iría stats de Redis si lo implementamos
                stats["l2"] = "available"
            except:
                pass
        
        return stats


class CacheWarmer:
    """Precarga datos frecuentes en cache.
    
    Mejora performance al:
    - Llenar cache durante off-peak hours
    - Precargar datos que se usan en primera request
    - Mantener "hot data" siempre disponible
    """
    
    def __init__(self, tiered_cache: TieredCacheManager):
        """
        Inicializa cache warmer.
        
        Args:
            tiered_cache: TieredCacheManager instance
        """
        self.cache = tiered_cache
        self.warming_tasks: Set[asyncio.Task] = set()
        self.logger = logging.getLogger(__name__)
    
    async def warm_cache(
        self,
        keys: Dict[str, Callable],
        batch_size: int = 10
    ) -> Dict[str, bool]:
        """Precarga múltiples claves en cache.
        
        Args:
            keys: Dict mapping {key: fetch_function}
            batch_size: Número de fetches concurrentes
            
        Returns:
            Dict mapping {key: success}
        """
        results = {}
        
        # Procesar en batches para no sobrecargar
        key_list = list(keys.items())
        for i in range(0, len(key_list), batch_size):
            batch = key_list[i:i+batch_size]
            
            tasks = [
                self._warm_single_key(key, fetch_fn)
                for key, fetch_fn in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for (key, _), result in zip(batch, batch_results):
                results[key] = isinstance(result, bool) and result
        
        self.logger.info(f"Cache warming completed: {sum(results.values())}/{len(results)} succeeded")
        return results
    
    async def _warm_single_key(self, key: str, fetch_fn: Callable) -> bool:
        """Precarga una única clave.
        
        Args:
            key: Cache key
            fetch_fn: Función para obtener valor
            
        Returns:
            True si fue exitoso
        """
        try:
            if asyncio.iscoroutinefunction(fetch_fn):
                value = await fetch_fn()
            else:
                value = fetch_fn()
            
            if value is not None:
                await self.cache.put(key, value)
                return True
        except Exception as e:
            self.logger.error(f"Failed to warm key {key}: {e}")
        
        return False
