"""
Recon Cache Layer - Capa de caching para herramientas del ReconAgent.

Proporciona wrappers con caching para todas las herramientas de reconocimiento
que implican requests de red o análisis pesado.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from src.memory.cache import CacheManager, async_cached
from src.memory.cache.cache_decorator import get_redis_client

logger = logging.getLogger(__name__)


class ReconCacheLayer:
    """Capa de caching para operaciones del ReconAgent."""

    def __init__(self, cache_manager: Optional[CacheManager] = None) -> None:
        """
        Inicializa la capa de caching.

        Args:
            cache_manager: Instancia de CacheManager (si None, usa singleton)
        """
        self.cache_manager = cache_manager or CacheManager()
        self.logger = logging.getLogger(__name__)

    async def get_cached_result(
        self,
        tool_name: str,
        *args: Any,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene resultado cacheado de una herramienta.

        Args:
            tool_name: Nombre de la herramienta
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre

        Returns:
            Resultado cacheado o None
        """
        if not self.cache_manager.redis_client:
            return None

        redis_client = self.cache_manager.redis_client
        cache_key = redis_client.generate_key(tool_name, args, kwargs)

        cached_value = await redis_client.get(cache_key)
        if cached_value:
            self.logger.info(f"⚡ Cache hit: {tool_name}")
            return cached_value

        return None

    async def cache_result(
        self,
        tool_name: str,
        result: Dict[str, Any],
        *args: Any,
        **kwargs: Any
    ) -> bool:
        """
        Cachea resultado de una herramienta.

        Args:
            tool_name: Nombre de la herramienta
            result: Resultado a cachear
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre

        Returns:
            True si se cacheó correctamente
        """
        if not self.cache_manager.redis_client:
            return False

        redis_client = self.cache_manager.redis_client
        cache_key = redis_client.generate_key(tool_name, args, kwargs)
        ttl = self.cache_manager.get_ttl_policy(tool_name)

        return await redis_client.set(cache_key, result, ttl)

    async def invalidate_tool_cache(self, tool_name: str) -> int:
        """
        Invalida todo el cache de una herramienta.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Cantidad de claves eliminadas
        """
        pattern = f"cache:{tool_name}:*"
        return await self.cache_manager.clear_by_pattern(pattern)

    def get_cache_info(self) -> Dict[str, Any]:
        """Obtiene información del cache (non-async wrapper).
        
        Usa caching de 30 segundos para evitar overhead de event loop.
        
        Returns:
            Diccionario con estadísticas del cache
        """
        import asyncio
        import time
        
        # Implementar caching local de 30 segundos para evitar event loop overhead
        if not hasattr(self, '_cache_info_cache'):
            self._cache_info_cache: Optional[Dict[str, Any]] = None
            self._cache_info_timestamp: float = 0
        
        # Retornar cache si está fresco
        if self._cache_info_cache and time.time() - self._cache_info_timestamp < 30:
            return self._cache_info_cache
        
        # Crear event loop segura (en thread si es necesario)
        try:
            loop = asyncio.get_running_loop()
            # Si estamos en loop async, no podemos hacer run_until_complete
            # Retornar cache viejo o resultado parcial
            if self._cache_info_cache:
                return self._cache_info_cache
            return {"error": "Cannot get cache info from async context"}
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            should_close = True
        
        try:
            stats = loop.run_until_complete(self.cache_manager.get_stats())
            self._cache_info_cache = stats
            self._cache_info_timestamp = time.time()
            return stats
        finally:
            if should_close:
                loop.close()


# Wrappers con caching para herramientas específicas
class CachedGraphQLTools:
    """Wrappers de caching para herramientas GraphQL."""

    def __init__(self, graphql_mapper: Any, cache_layer: ReconCacheLayer) -> None:
        """
        Inicializa wrappers con caching.

        Args:
            graphql_mapper: Instancia de GraphQLMapper
            cache_layer: Instancia de ReconCacheLayer
        """
        self.graphql_mapper = graphql_mapper
        self.cache_layer = cache_layer
        self.logger = logging.getLogger(__name__)

    async def discover_graphql_endpoints(
        self,
        target_url: str,
        endpoints_to_test: Optional[list] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Descubre endpoints GraphQL con caching.

        Args:
            target_url: URL del objetivo
            endpoints_to_test: Endpoints a probar (opcional)
            **kwargs: Argumentos adicionales

        Returns:
            Resultado de descubrimiento
        """
        # Intentar obtener del cache
        cached = await self.cache_layer.get_cached_result(
            "discover_graphql_endpoints",
            target_url,
            endpoints_to_test=endpoints_to_test
        )
        if cached:
            return cached

        # Ejecutar descubrimiento
        result = await self.graphql_mapper.discover_graphql_endpoints(
            target_url,
            endpoints_to_test=endpoints_to_test,
            **kwargs
        )

        # Cachear resultado
        result_with_metadata = {
            **result,
            "cached_at": datetime.now().isoformat(),
            "cache_source": "discover_graphql_endpoints"
        }
        
        await self.cache_layer.cache_result(
            "discover_graphql_endpoints",
            result_with_metadata,
            target_url,
            endpoints_to_test=endpoints_to_test
        )

        return result_with_metadata

    async def introspect_graphql_schema(
        self,
        graphql_url: str,
        include_mutations: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Extrae esquema GraphQL con caching.

        Args:
            graphql_url: URL del endpoint GraphQL
            include_mutations: Incluir mutaciones
            **kwargs: Argumentos adicionales

        Returns:
            Esquema GraphQL
        """
        # Intentar obtener del cache
        cached = await self.cache_layer.get_cached_result(
            "introspect_graphql_schema",
            graphql_url,
            include_mutations=include_mutations
        )
        if cached:
            return cached

        # Ejecutar introspección
        result = await self.graphql_mapper.introspect_graphql_schema(
            graphql_url,
            include_mutations=include_mutations,
            **kwargs
        )

        # Cachear resultado
        result_with_metadata = {
            **result,
            "cached_at": datetime.now().isoformat(),
            "cache_source": "introspect_graphql_schema"
        }
        
        await self.cache_layer.cache_result(
            "introspect_graphql_schema",
            result_with_metadata,
            graphql_url,
            include_mutations=include_mutations
        )

        return result_with_metadata


class CachedNetworkTools:
    """Wrappers de caching para herramientas de red."""

    def __init__(self, network_tools: Any, cache_layer: ReconCacheLayer) -> None:
        """
        Inicializa wrappers con caching.

        Args:
            network_tools: Instancia de NetworkTools
            cache_layer: Instancia de ReconCacheLayer
        """
        self.network_tools = network_tools
        self.cache_layer = cache_layer
        self.logger = logging.getLogger(__name__)

    async def dns_enumeration(
        self,
        domain: str,
        methods: Optional[list] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        DNS enumeration con caching (24 horas TTL).

        Args:
            domain: Dominio a resolver
            methods: Métodos de enumeración
            **kwargs: Argumentos adicionales

        Returns:
            Resultados de DNS
        """
        # Intentar obtener del cache
        cached = await self.cache_layer.get_cached_result(
            "dns_enumeration",
            domain,
            methods=methods
        )
        if cached:
            return cached

        # Ejecutar enumeración
        result = await self.network_tools.dns_enumeration(
            domain,
            methods=methods,
            **kwargs
        )

        # Cachear resultado
        result_with_metadata = {
            **result,
            "cached_at": datetime.now().isoformat(),
            "cache_source": "dns_enumeration"
        }
        
        await self.cache_layer.cache_result(
            "dns_enumeration",
            result_with_metadata,
            domain,
            methods=methods
        )

        return result_with_metadata

    async def tls_certificate_analysis(
        self,
        domain: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Análisis TLS con caching (24 horas TTL).

        Args:
            domain: Dominio a analizar
            **kwargs: Argumentos adicionales

        Returns:
            Análisis de certificados
        """
        # Intentar obtener del cache
        cached = await self.cache_layer.get_cached_result(
            "tls_certificate_analysis",
            domain
        )
        if cached:
            return cached

        # Ejecutar análisis
        result = await self.network_tools.tls_certificate_analysis(
            domain,
            **kwargs
        )

        # Cachear resultado
        result_with_metadata = {
            **result,
            "cached_at": datetime.now().isoformat(),
            "cache_source": "tls_certificate_analysis"
        }
        
        await self.cache_layer.cache_result(
            "tls_certificate_analysis",
            result_with_metadata,
            domain
        )

        return result_with_metadata


def get_redis_client():
    """Helper para obtener cliente Redis (importación para decoradores)."""
    from src.memory.cache import RedisClient
    manager = CacheManager()
    return manager.redis_client
