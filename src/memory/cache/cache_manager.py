"""
Cache Manager - Gestor centralizado del sistema de caching.

Proporciona:
- Inicialización y gestión del ciclo de vida de Redis
- Gestión de políticas de TTL
- Estadísticas de caché
"""

import logging
from typing import Optional, Dict, Any
from .redis_client import RedisClient
from .cache_decorator import set_redis_client


class CacheManager:
    """Centralized cache management system (Singleton pattern).
    
    Manages Redis connection lifecycle, TTL policies, and cache operations.
    Implements singleton pattern to ensure single instance across application.
    
    Provides:
        - Redis connection management
        - Per-tool TTL policy configuration
        - Cache statistics and health checks
        - Pattern-based cache invalidation
        
    Example:
        manager = CacheManager()
        await manager.initialize(host='localhost', port=6379)
        manager.set_ttl_policy('my_tool', 3600)
        stats = await manager.get_stats()
        await manager.shutdown()
    """

    _instance: Optional['CacheManager'] = None
    _initialized = False

    def __new__(cls) -> 'CacheManager':
        """Create or return singleton instance.
        
        Returns:
            Singleton CacheManager instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize CacheManager (singleton pattern).
        
        Sets up logging, Redis client reference, and default TTL policies.
        Subsequent calls return without reinitializing.
        """
        if self._initialized:
            return

        self.logger = logging.getLogger(__name__)
        self.redis_client: Optional[RedisClient] = None
        self.policies: Dict[str, int] = {}

        self.default_policies = {
            "extract_javascript_files": 3600,
            "discover_graphql_endpoints": 7200,
            "introspect_graphql_schema": 7200,
            "dns_enumeration": 86400,
            "analyze_http_headers": 3600,
            "tls_certificate_analysis": 86400,
            "port_scan_passive": 43200,
            "extract_shadow_apis": 3600,
        }

        self.policies = self.default_policies.copy()
        self._initialized = True

        self.logger.info("✓ CacheManager initialized")

    async def initialize(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ) -> bool:
        """Initialize Redis connection.
        
        Establishes async connection to Redis and registers client
        with decorators for caching support.
        
        Args:
            host: Redis host address (default: localhost)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
            password: Redis authentication password (optional)
            
        Returns:
            True if initialization successful, False if failed.
            
        Raises:
            Exception: If connection fails (caught and logged).
        """
        try:
            self.redis_client = RedisClient(
                host=host,
                port=port,
                db=db,
                password=password,
                default_ttl=3600
            )
            await self.redis_client.connect()

            # Registrar cliente en decoradores
            set_redis_client(self.redis_client)

            self.logger.info("✓ CacheManager Redis initialized")
            return True

        except Exception as e:
            self.logger.error(f"✗ CacheManager initialization failed: {e}")
            return False

    async def shutdown(self) -> None:
        """Disconnect from Redis and cleanup resources.
        
        Safely closes Redis connection and logs shutdown.
        """
        if self.redis_client:
            await self.redis_client.disconnect()
            self.logger.info("✓ CacheManager shutdown")

    def set_ttl_policy(self, function_name: str, ttl: int) -> None:
        """Set TTL policy for a specific function.
        
        Args:
            function_name: Name of function to set policy for
            ttl: Time-to-live in seconds
            
        Example:
            manager.set_ttl_policy("discover_graphql", 7200)
        """
        self.policies[function_name] = ttl
        self.logger.debug(f"TTL policy set: {function_name} -> {ttl}s")

    def get_ttl_policy(self, function_name: str) -> int:
        """Get TTL policy for a function.
        
        Args:
            function_name: Name of function
            
        Returns:
            TTL in seconds (default: 3600 if not configured)
        """
        return self.policies.get(function_name, 3600)

    async def clear_cache(self) -> bool:
        """Clear all cached data.
        
        Returns:
            True if cache cleared successfully, False if failed.
        """
        if not self.redis_client:
            self.logger.warning("Redis client not initialized")
            return False

        return await self.redis_client.flush()

    async def clear_by_pattern(self, pattern: str) -> int:
        """Clear cache entries matching a glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., 'cache:discover_graphql*')
            
        Returns:
            Number of cache keys deleted.
            
        Example:
            # Clear all GraphQL discovery cache
            await manager.clear_by_pattern('cache:discover_graphql*')
        """
        if not self.redis_client or not self.redis_client.redis:
            return 0

        try:
            keys = await self.redis_client.redis.keys(pattern)
            if keys:
                count = await self.redis_client.redis.delete(*keys)
                self.logger.info(f"✓ Cleared {count} cache entries matching {pattern}")
                return count
            return 0
        except Exception as e:
            self.logger.error(f"✗ Cache clear error: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and information.
        
        Returns:
            Dictionary with memory usage, client count, policies, etc.
        """
        if not self.redis_client:
            return {"status": "not_initialized"}

        stats = await self.redis_client.get_stats()
        stats["policies"] = self.policies
        return stats

    async def health_check(self) -> bool:
        """Check Redis connection health.
        
        Returns:
            True if Redis is healthy and responsive, False if unavailable.
        """
        if not self.redis_client or not self.redis_client.redis:
            return False

        try:
            await self.redis_client.redis.ping()
            return True
        except Exception:
            return False


def get_cache_manager() -> CacheManager:
    """Get global CacheManager singleton instance.
    
    Returns:
        CacheManager singleton instance.
    """
    return CacheManager()
