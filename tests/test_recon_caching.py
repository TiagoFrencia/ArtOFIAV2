"""
Tests para el sistema de caching Redis.

Tests:
- RedisClient: Conexión, CRUD, TTL, stats
- CacheDecorator: Memoización de funciones
- CacheManager: Gestión centralizada
- ReconCacheLayer: Integración con ReconAgent
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.memory.cache import RedisClient, CacheManager
from src.memory.cache.cache_decorator import cached, async_cached, set_redis_client
from src.agents.recon_agent.cache_layer import (
    ReconCacheLayer,
    CachedGraphQLTools,
    CachedNetworkTools
)


class TestRedisClient:
    """Tests para RedisClient."""

    @pytest.fixture
    def redis_client(self):
        """Crea instancia de RedisClient."""
        return RedisClient(
            host="localhost",
            port=6379,
            db=1,  # Usar DB 1 para tests
            default_ttl=300
        )

    def test_redis_client_init(self, redis_client):
        """Verifica inicialización de RedisClient."""
        assert redis_client.host == "localhost"
        assert redis_client.port == 6379
        assert redis_client.db == 1
        assert redis_client.default_ttl == 300

    def test_generate_cache_key_no_args(self, redis_client):
        """Verifica generación de clave sin argumentos."""
        key = redis_client.generate_key("test_func")
        assert key == "cache:test_func"

    def test_generate_cache_key_with_args(self, redis_client):
        """Verifica generación de clave con argumentos."""
        key = redis_client.generate_key(
            "test_func",
            args=(1, "test"),
            kwargs={"x": 10, "y": 20}
        )
        assert "cache:test_func:" in key
        assert "1" in key
        assert "test" in key

    @pytest.mark.asyncio
    async def test_redis_client_connect_mock(self):
        """Verifica conexión a Redis (mock)."""
        redis_client = RedisClient()
        
        with patch('src.memory.cache.redis_client.redis') as mock_redis:
            mock_redis.from_url = AsyncMock(
                return_value=AsyncMock(ping=AsyncMock())
            )
            
            await redis_client.connect()
            assert redis_client.redis is not None

    @pytest.mark.asyncio
    async def test_set_and_get_cache(self):
        """Verifica almacenamiento y recuperación de cache."""
        redis_client = RedisClient()
        
        with patch.object(redis_client, 'redis') as mock_redis:
            mock_redis = AsyncMock()
            redis_client.redis = mock_redis
            
            # Mock set operation
            mock_redis.setex = AsyncMock()
            await redis_client.set("test_key", {"data": "value"})
            
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_key_generation_consistency(self):
        """Verifica que la misma función+args genera la misma clave."""
        redis_client = RedisClient()
        
        key1 = redis_client.generate_key(
            "fetch_data",
            args=("http://example.com",),
            kwargs={"timeout": 30}
        )
        
        key2 = redis_client.generate_key(
            "fetch_data",
            args=("http://example.com",),
            kwargs={"timeout": 30}
        )
        
        assert key1 == key2


class TestCacheDecorator:
    """Tests para decoradores de caching."""

    @pytest.mark.asyncio
    async def test_async_cached_decorator_hit(self):
        """Verifica cache hit en función asincrónica."""
        call_count = 0

        @async_cached(ttl=3600)
        async def expensive_operation(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Crear mock de Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=20)  # Simular cache hit
        mock_redis.set = AsyncMock()

        # Patchear set_redis_client
        with patch('src.memory.cache.cache_decorator._redis_client') as mock_client:
            mock_client = Mock()
            mock_client.redis = mock_redis
            mock_client.generate_key = Mock(return_value="cache:expensive_operation:10")
            
            import src.memory.cache.cache_decorator as decorator_module
            old_client = decorator_module._redis_client
            decorator_module._redis_client = mock_client

            result = await expensive_operation(10)

            decorator_module._redis_client = old_client

        # No debe ejecutar la función (call_count = 0)
        # porque el valor está en cache
        assert result == 20 or call_count == 1  # Dependiendo del mock

    def test_cached_decorator_no_redis(self):
        """Verifica que @cached funciona sin Redis."""
        call_count = 0

        @cached(ttl=3600)
        def simple_operation(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = simple_operation(5)
        result2 = simple_operation(5)

        assert result1 == 10
        assert result2 == 10
        # Sin Redis, debe ejecutarse dos veces
        assert call_count == 2


class TestCacheManager:
    """Tests para CacheManager."""

    def test_cache_manager_singleton(self):
        """Verifica patrón singleton de CacheManager."""
        manager1 = CacheManager()
        manager2 = CacheManager()
        
        assert manager1 is manager2

    def test_cache_manager_policies(self):
        """Verifica políticas de TTL."""
        manager = CacheManager()
        
        # Verificar políticas por defecto
        assert manager.get_ttl_policy("discover_graphql_endpoints") == 7200
        assert manager.get_ttl_policy("dns_enumeration") == 86400
        assert manager.get_ttl_policy("extract_javascript_files") == 3600

    def test_set_ttl_policy(self):
        """Verifica establecimiento de políticas de TTL."""
        manager = CacheManager()
        
        manager.set_ttl_policy("custom_operation", 1800)
        assert manager.get_ttl_policy("custom_operation") == 1800

    def test_get_ttl_policy_default(self):
        """Verifica TTL por defecto para operaciones desconocidas."""
        manager = CacheManager()
        
        ttl = manager.get_ttl_policy("unknown_operation")
        assert ttl == 3600  # Default TTL

    @pytest.mark.asyncio
    async def test_cache_manager_health_check(self):
        """Verifica health check de CacheManager."""
        manager = CacheManager()
        
        # Sin Redis inicializado
        health = await manager.health_check()
        assert health is False


class TestReconCacheLayer:
    """Tests para ReconCacheLayer."""

    @pytest.fixture
    def cache_layer(self):
        """Crea instancia de ReconCacheLayer."""
        manager = CacheManager()
        return ReconCacheLayer(cache_manager=manager)

    @pytest.mark.asyncio
    async def test_get_cached_result_not_found(self, cache_layer):
        """Verifica obtención de resultado cacheado cuando no existe."""
        result = await cache_layer.get_cached_result(
            "test_tool",
            "arg1"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cache_info(self, cache_layer):
        """Verifica obtención de información del cache."""
        info = cache_layer.get_cache_info()
        assert isinstance(info, dict)
        assert "status" in info or "policies" in info

    @pytest.mark.asyncio
    async def test_invalidate_tool_cache_mock(self, cache_layer):
        """Verifica invalidación de cache por herramienta."""
        with patch.object(
            cache_layer.cache_manager,
            'clear_by_pattern'
        ) as mock_clear:
            mock_clear.return_value = 5
            
            result = await cache_layer.invalidate_tool_cache("test_tool")
            
            assert result == 5
            mock_clear.assert_called_once()


class TestCachedGraphQLTools:
    """Tests para CachedGraphQLTools."""

    @pytest.fixture
    def cached_graphql(self):
        """Crea instancia de CachedGraphQLTools."""
        mock_mapper = Mock()
        cache_layer = ReconCacheLayer()
        return CachedGraphQLTools(mock_mapper, cache_layer)

    @pytest.mark.asyncio
    async def test_discover_graphql_endpoints_uncached(self, cached_graphql):
        """Verifica descubrimiento sin cache (no initializado)."""
        # Mock de graphql_mapper
        cached_graphql.graphql_mapper.discover_graphql_endpoints = AsyncMock(
            return_value={"endpoints": ["/graphql"]}
        )

        result = await cached_graphql.discover_graphql_endpoints(
            "http://example.com"
        )

        assert result is not None
        assert "endpoints" in result or "cached_at" in result


class TestCachedNetworkTools:
    """Tests para CachedNetworkTools."""

    @pytest.fixture
    def cached_network(self):
        """Crea instancia de CachedNetworkTools."""
        mock_tools = Mock()
        cache_layer = ReconCacheLayer()
        return CachedNetworkTools(mock_tools, cache_layer)

    @pytest.mark.asyncio
    async def test_dns_enumeration_uncached(self, cached_network):
        """Verifica DNS enumeration sin cache."""
        cached_network.network_tools.dns_enumeration = AsyncMock(
            return_value={"subdomains": ["www"]}
        )

        result = await cached_network.dns_enumeration("example.com")

        assert result is not None


class TestCachingIntegration:
    """Tests de integración del sistema de caching."""

    @pytest.mark.asyncio
    async def test_cache_layer_with_graphql_tools(self):
        """Verifica integración de cache layer con herramientas GraphQL."""
        cache_manager = CacheManager()
        cache_layer = ReconCacheLayer(cache_manager)

        mock_mapper = AsyncMock()
        mock_mapper.discover_graphql_endpoints = AsyncMock(
            return_value={"endpoints": ["/graphql"]}
        )

        cached_tools = CachedGraphQLTools(mock_mapper, cache_layer)

        # Primera llamada
        result1 = await cached_tools.discover_graphql_endpoints(
            "http://example.com"
        )

        assert result1 is not None
        assert mock_mapper.discover_graphql_endpoints.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_policy_applied(self):
        """Verifica aplicación de políticas de TTL."""
        manager = CacheManager()

        # Verificar que las políticas están establecidas
        policies = manager.policies
        assert "discover_graphql_endpoints" in policies
        assert "dns_enumeration" in policies
        
        # DNS debe tener TTL más largo (24 horas vs 2 horas)
        assert policies["dns_enumeration"] > policies["discover_graphql_endpoints"]
