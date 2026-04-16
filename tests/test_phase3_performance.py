"""
Test Suite for PHASE 3: Performance Optimization

Tests para validar:
1. Neo4j index management
2. Query pagination
3. Query caching
4. Performance metrics collection
"""

import pytest
import time
from datetime import datetime, timedelta


# ============================================================
# TEST 1: Neo4j Indexes
# ============================================================

class TestNeo4jIndexes:
    """Verifica que indexes se crean correctamente"""
    
    def test_index_definitions_valid(self):
        """Verifica que todas las definiciones de índices son válidas"""
        from scripts.init_neo4j import INDEXES
        
        required_fields_node = {"name", "type", "label", "properties", "purpose"}
        required_fields_rel = {"name", "type", "name", "properties", "purpose"}
        
        for idx in INDEXES:
            assert idx["name"], "Index must have a name"
            assert idx["type"] in ["node", "relationship"], "Valid type required"
            assert idx["properties"], "Must have properties"
            assert idx["purpose"], "Must have purpose description"
            
            if idx["type"] == "node":
                assert "label" in idx, "Node index must have label"
            elif idx["type"] == "relationship":
                assert "name" in idx, "Relationship index must have name"
    
    def test_no_duplicate_index_names(self):
        """Verifica que no hay nombres duplicados"""
        from scripts.init_neo4j import INDEXES
        
        names = [idx["name"] for idx in INDEXES]
        assert len(names) == len(set(names)), "Duplicate index names detected"
    
    def test_coverage_of_node_types(self):
        """Verifica que todos los node types tienen índices"""
        from scripts.init_neo4j import INDEXES
        
        node_indexes = [idx for idx in INDEXES if idx["type"] == "node"]
        labels = set(idx["label"] for idx in node_indexes)
        
        expected_labels = {"Endpoint", "Token", "Vulnerability", "Payload", "Tactic", "Defense", "Target", "Agent"}
        
        # At least id index for each type
        for label in expected_labels:
            assert any(idx["label"] == label for idx in node_indexes), f"Missing index for {label}"


# ============================================================
# TEST 2: Pagination
# ============================================================

class TestPagination:
    """Verifica que pagination funciona correctamente"""
    
    def test_pagination_params_creation(self):
        """Verifica que PaginationParams se crea"""
        from src.memory.query_optimization import PaginationParams
        
        params = PaginationParams(skip=10, limit=20, sort_by="created_at")
        
        assert params.skip == 10
        assert params.limit == 20
        assert params.sort_by == "created_at"
    
    def test_pagination_cypher_generation(self):
        """Verifica que genera claúsulas Cypher correctas"""
        from src.memory.query_optimization import PaginationParams
        
        params = PaginationParams(skip=100, limit=50)
        cypher = params.to_cypher_skip_limit()
        
        assert "SKIP 100" in cypher
        assert "LIMIT 50" in cypher
    
    def test_paginated_result_creation(self):
        """Verifica PaginatedResult factory"""
        from src.memory.query_optimization import PaginatedResult
        
        items = [{"id": i} for i in range(15)]
        result = PaginatedResult.create(
            items=items,
            total=100,
            skip=0,
            limit=20
        )
        
        assert result.page == 1
        assert result.total == 100
        assert result.has_next is True
        assert result.has_prev is False
    
    def test_paginated_result_last_page(self):
        """Verifica comportamiento en última página"""
        from src.memory.query_optimization import PaginatedResult
        
        items = [{"id": i} for i in range(10)]
        result = PaginatedResult.create(
            items=items,
            total=100,
            skip=80,
            limit=20
        )
        
        assert result.page == 5
        assert result.pages == 5
        assert result.has_next is False
        assert result.has_prev is True
    
    def test_paginated_result_to_dict(self):
        """Verifica serialización a dict"""
        from src.memory.query_optimization import PaginatedResult
        
        result = PaginatedResult.create(
            items=[{"id": 1}],
            total=50,
            skip=0,
            limit=10
        )
        
        result_dict = result.to_dict()
        assert "items" in result_dict
        assert "pagination" in result_dict
        assert result_dict["pagination"]["page"] == 1


# ============================================================
# TEST 3: Query Cache
# ============================================================

class TestQueryCache:
    """Verifica que cache funciona correctamente"""
    
    def test_cache_initialization(self):
        """Verifica que cache se inicializa"""
        from src.memory.query_optimization import QueryCache
        
        cache = QueryCache(max_size=500, ttl_seconds=1800)
        
        assert cache.max_size == 500
        assert cache.ttl_seconds == 1800
        assert cache.hits == 0
        assert cache.misses == 0
    
    def test_cache_miss(self):
        """Verifica que cache miss se registra"""
        from src.memory.query_optimization import QueryCache
        
        cache = QueryCache()
        
        result = cache.get("SELECT * FROM table", {"param": "value"})
        
        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0
    
    def test_cache_hit(self):
        """Verifica que cache hit funciona"""
        from src.memory.query_optimization import QueryCache
        
        cache = QueryCache()
        query = "SELECT * FROM table"
        params = {"param": "value"}
        expected_result = [{"id": 1, "name": "test"}]
        
        # First call: miss, cache result
        assert cache.get(query, params) is None
        cache.set(query, params, expected_result)
        
        # Second call: hit
        result = cache.get(query, params)
        assert result == expected_result
        assert cache.hits == 1
    
    def test_cache_different_params(self):
        """Verifica que diferentes params son cachés separados"""
        from src.memory.query_optimization import QueryCache
        
        cache = QueryCache()
        query = "SELECT * FROM table WHERE id = $id"
        
        # Cache result for id=1
        cache.set(query, {"id": 1}, [{"id": 1}])
        
        # Fetch result for id=2 should be cache miss
        result = cache.get(query, {"id": 2})
        assert result is None
        assert cache.misses == 1
    
    def test_cache_ttl_expiration(self):
        """Verifica que TTL expira entradas"""
        from src.memory.query_optimization import QueryCache
        import time
        
        cache = QueryCache(ttl_seconds=1)  # 1 second TTL
        query = "SELECT * FROM table"
        params = {"param": "value"}
        
        cache.set(query, params, [{"result": "data"}])
        
        # Immediately should hit
        result = cache.get(query, params)
        assert result is not None
        assert cache.hits == 1
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Now should miss
        result = cache.get(query, params)
        assert result is None
        assert cache.misses == 1
    
    def test_cache_lru_eviction(self):
        """Verifica que cache evicta entries cuando está lleno"""
        from src.memory.query_optimization import QueryCache
        
        cache = QueryCache(max_size=3)  # Only 3 entries
        
        # Add 4 entries
        for i in range(4):
            cache.set(f"query_{i}", {}, {"result": i})
        
        # Cache should only have 3 entries
        assert len(cache.cache) == 3
    
    def test_cache_stats(self):
        """Verifica que estadísticas de cache son correctas"""
        from src.memory.query_optimization import QueryCache
        
        cache = QueryCache()
        
        # Add some metrics
        for i in range(3):
            cache.set(f"query_{i}", {}, {"result": i})
        
        # Try to get them
        cache.get("query_0", {})  # hit
        cache.get("query_1", {})  # hit
        cache.get("query_999", {})  # miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 3
        assert stats["hit_rate_percent"] == pytest.approx(66.67, rel=1)


# ============================================================
# TEST 4: Metrics Collection
# ============================================================

class TestMetricsCollector:
    """Verifica que metrics se colectan correctamente"""
    
    def test_metrics_recorder(self):
        """Verifica que se registran métricas"""
        from src.memory.query_optimization import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record(
            query="SELECT * FROM table",
            params={"id": 1},
            execution_time_ms=25.5,
            result_count=10
        )
        
        assert len(collector.metrics) == 1
        assert collector.metrics[0].execution_time_ms == 25.5
        assert collector.metrics[0].result_count == 10
    
    def test_slow_queries_detection(self):
        """Verifica que detecta queries lentas"""
        from src.memory.query_optimization import MetricsCollector
        
        collector = MetricsCollector()
        
        # Fast query
        collector.record("fast", {}, 10.0, 5)
        
        # Slow query
        collector.record("slow", {}, 2000.0, 1)
        
        slow = collector.get_slow_queries(threshold_ms=1000)
        
        assert len(slow) == 1
        assert slow[0].execution_time_ms == 2000.0
    
    def test_metrics_stats(self):
        """Verifica que genera estadísticas correctas"""
        from src.memory.query_optimization import MetricsCollector
        
        collector = MetricsCollector()
        
        # Record various queries
        times = [10, 20, 30, 40, 50]
        for t in times:
            collector.record(f"query_{t}", {}, float(t), 1)
        
        stats = collector.get_stats()
        
        assert stats["total_queries"] == 5
        assert stats["avg_execution_ms"] == pytest.approx(30.0)
        assert stats["max_execution_ms"] == 50
        assert stats["min_execution_ms"] == 10
    
    def test_cache_hit_rate_in_stats(self):
        """Verifica que cache hit rate aparece en stats"""
        from src.memory.query_optimization import MetricsCollector
        
        collector = MetricsCollector()
        
        # Some cached, some not
        collector.record("q1", {}, 10, 1, from_cache=True)
        collector.record("q2", {}, 20, 1, from_cache=True)
        collector.record("q3", {}, 30, 1, from_cache=False)
        
        stats = collector.get_stats()
        
        assert stats["cached_queries"] == 2
        assert stats["cache_hit_rate_percent"] == pytest.approx(66.67, rel=1)


# ============================================================
# TEST 5: Cypher Builder
# ============================================================

class TestCypherBuilder:
    """Verifica que CypherBuilder genera queries correctas"""
    
    def test_match_with_index(self):
        """Verifica generación de MATCH con index"""
        from src.memory.query_optimization import CypherBuilder
        
        clause = CypherBuilder.match_with_index(
            "n", "Endpoint", "id", "ep_123"
        )
        
        assert "MATCH" in clause
        assert "Endpoint" in clause
        assert "id:" in clause
    
    def test_where_with_and(self):
        """Verifica WHERE con AND"""
        from src.memory.query_optimization import CypherBuilder
        
        clause = CypherBuilder.where_with_And(
            "n.active = true",
            "n.severity > 5"
        )
        
        assert "WHERE" in clause
        assert "AND" in clause
    
    def test_pagination_clause(self):
        """Verifica generación de claúsula de pagination"""
        from src.memory.query_optimization import CypherBuilder
        
        clause = CypherBuilder.build_pagination_clause(
            sort_field="created_at",
            sort_order="DESC",
            limit=25,
            skip=50
        )
        
        assert "ORDER BY" in clause
        assert "DESC" in clause
        assert "SKIP 50" in clause
        assert "LIMIT 25" in clause


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
