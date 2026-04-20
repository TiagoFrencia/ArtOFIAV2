"""
Redis Client - Cliente async para operaciones de caché.

Proporciona:
- Conexión async a Redis
- Operaciones CRUD
- Gestión de TTL
- Serialización de datos
"""

import logging
import json
from typing import Any, Optional
from datetime import timedelta

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError as e:
    REDIS_AVAILABLE = False
    REDIS_ERROR = str(e)


class RedisClient:
    """Cliente async para Redis con soporte de TTL y serialización."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600
    ) -> None:
        """
        Inicializa cliente Redis.

        Args:
            host: Host de Redis (default: localhost)
            port: Puerto de Redis (default: 6379)
            db: Base de datos (default: 0)
            password: Contraseña de Redis (optional)
            default_ttl: TTL por defecto en segundos (default: 3600 = 1 hora)

        Raises:
            ImportError: Si redis package no está instalado
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package required for caching. "
                "Install with: pip install redis"
            ) from None

        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.redis: Optional[Redis] = None

        self.logger.info(
            f"RedisClient configured: {host}:{port}/db:{db}"
        )

    async def connect(self) -> None:
        """Establece conexión a Redis."""
        try:
            self.redis = await redis.from_url(
                f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
                if self.password
                else f"redis://{self.host}:{self.port}/{self.db}",
                decode_responses=False,
                encoding="utf-8"
            )
            # Verificar conexión
            await self.redis.ping()
            self.logger.info("✓ Redis connection established")
        except Exception as e:
            self.logger.error(f"✗ Redis connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Cierra conexión a Redis."""
        if self.redis:
            await self.redis.close()
            self.logger.info("✓ Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene valor de cache.

        Args:
            key: Clave de cache

        Returns:
            Valor deserializado o None si no existe
        """
        if not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"✗ Cache get error for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Almacena valor en cache.

        Args:
            key: Clave de cache
            value: Valor a almacenar
            ttl: Time-to-live en segundos (default: self.default_ttl)

        Returns:
            True si se almacenó, False si falló
        """
        if not self.redis:
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            self.logger.debug(f"✓ Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            self.logger.error(f"✗ Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Elimina valor del cache.

        Args:
            key: Clave de cache

        Returns:
            True si se eliminó, False si no existía
        """
        if not self.redis:
            return False

        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"✗ Cache delete error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Verifica si existe clave en cache.

        Args:
            key: Clave de cache

        Returns:
            True si existe, False si no
        """
        if not self.redis:
            return False

        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"✗ Cache exists error for key '{key}': {e}")
            return False

    async def flush(self) -> bool:
        """
        Limpia toda la base de datos de cache.

        Returns:
            True si se limpió, False si falló
        """
        if not self.redis:
            return False

        try:
            await self.redis.flushdb()
            self.logger.info("✓ Cache flushed")
            return True
        except Exception as e:
            self.logger.error(f"✗ Cache flush error: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        Obtiene estadísticas del cache.

        Returns:
            Dict con info de cache
        """
        if not self.redis:
            return {}

        try:
            info = await self.redis.info()
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace": info.get("keyspace", {})
            }
        except Exception as e:
            self.logger.error(f"✗ Cache stats error: {e}")
            return {}

    def generate_key(
        self,
        function_name: str,
        args: tuple = (),
        kwargs: dict = None
    ) -> str:
        """
        Genera clave de cache a partir de función y argumentos.

        Args:
            function_name: Nombre de función
            args: Argumentos posicionales
            kwargs: Argumentos nombrados

        Returns:
            Clave de cache (string)
        """
        kwargs = kwargs or {}
        
        # Serializar argumentos
        args_str = "|".join(str(arg) for arg in args)
        kwargs_str = "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        params = "|".join(filter(None, [args_str, kwargs_str]))
        
        if params:
            return f"cache:{function_name}:{params}"
        else:
            return f"cache:{function_name}"
