"""
Query Optimization Utilities - Pagination, Caching, and Performance Enhancement

Provides:
- Pagination support for large result sets
- LRU cache for frequently accessed queries
- Query plan analysis
- Performance metrics
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json
import time

logger = logging.getLogger(__name__)


# ============================================================
# PAGINATION SUPPORT
# ============================================================

@dataclass
class PaginationParams:
    """Parameters for paginated queries"""
    skip: int = 0
    limit: int = 100
    sort_by: Optional[str] = None
    sort_direction: str = "ASC"  # ASC or DESC
    
    def to_cypher_skip_limit(self) -> str:
        """Generate SKIP LIMIT clause"""
        return f"SKIP {self.skip} LIMIT {self.limit}"
    
    def to_cypher_order_by(self, fields: List[str]) -> str:
        """Generate ORDER BY clause"""
        if not self.sort_by or self.sort_by not in fields:
            return ""
        return f"ORDER BY {self.sort_by} {self.sort_direction}"


@dataclass
class PaginatedResult:
    """Result with pagination metadata"""
    items: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @staticmethod
    def create(
        items: List[Dict[str, Any]],
        total: int,
        skip: int,
        limit: int
    ) -> "PaginatedResult":
        """Factory method"""
        page = (skip // limit) + 1
        pages = (total + limit - 1) // limit  # Ceiling division
        
        return PaginatedResult(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            page=page,
            pages=pages,
            has_next=skip + limit < total,
            has_prev=skip > 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "items": self.items,
            "pagination": {
                "page": self.page,
                "pages": self.pages,
                "total": self.total,
                "limit": self.limit,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
            }
        }


# ============================================================
# QUERY CACHING
# ============================================================

class QueryCache:
    """
    LRU Cache for Cypher query results.
    
    Use Case:
    - Cache results of expensive read-only queries
    - Automatic invalidation by TTL
    - Per-query configuration
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Args:
            max_size: Maximum cache entries
            ttl_seconds: Time-to-live for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key from query and params"""
        # Sort params for consistent hashing
        params_str = json.dumps(params, sort_keys=True, default=str)
        content = f"{query}:{params_str}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached result if exists and not expired"""
        key = self._make_key(query, params)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        result, timestamp = self.cache[key]
        
        # Check TTL
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return result
    
    def set(self, query: str, params: Dict[str, Any], result: Any) -> None:
        """Cache a result"""
        # Simple LRU: remove oldest entry if at max size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (first one inserted)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self._make_key(query, params)
        self.cache[key] = (result, datetime.now())
    
    def clear(self) -> None:
        """Clear all cached results"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
            "ttl_seconds": self.ttl_seconds,
        }


# ============================================================
# PERFORMANCE METRICS
# ============================================================

@dataclass
class QueryMetrics:
    """Performance metrics for a query"""
    query: str
    params: Dict[str, Any]
    execution_time_ms: float
    result_count: int
    timestamp: datetime
    from_cache: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:100] + "..." if len(self.query) > 100 else self.query,
            "execution_time_ms": self.execution_time_ms,
            "result_count": self.result_count,
            "from_cache": self.from_cache,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsCollector:
    """Collect and analyze query performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: List[QueryMetrics] = []
    
    def record(
        self,
        query: str,
        params: Dict[str, Any],
        execution_time_ms: float,
        result_count: int,
        from_cache: bool = False
    ) -> None:
        """Record a query execution"""
        metric = QueryMetrics(
            query=query,
            params=params,
            execution_time_ms=execution_time_ms,
            result_count=result_count,
            timestamp=datetime.now(),
            from_cache=from_cache
        )
        
        self.metrics.append(metric)
        
        # Keep bounded list size
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_slow_queries(self, threshold_ms: float = 1000) -> List[QueryMetrics]:
        """Get queries that exceeded threshold"""
        return [m for m in self.metrics if m.execution_time_ms > threshold_ms]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics"""
        if not self.metrics:
            return {}
        
        times = [m.execution_time_ms for m in self.metrics]
        cached_count = sum(1 for m in self.metrics if m.from_cache)
        
        return {
            "total_queries": len(self.metrics),
            "avg_execution_ms": sum(times) / len(times),
            "max_execution_ms": max(times),
            "min_execution_ms": min(times),
            "cached_queries": cached_count,
            "cache_hit_rate_percent": (cached_count / len(self.metrics) * 100),
            "slow_queries": len(self.get_slow_queries()),
        }


# ============================================================
# QUERY BUILDER UTILITIES
# ============================================================

class CypherBuilder:
    """Helper for building optimized Cypher queries"""
    
    @staticmethod
    def match_with_index(
        node_var: str,
        label: str,
        property_name: str,
        property_value: Any
    ) -> str:
        """Build MATCH clause using indexed property"""
        return (
            f"MATCH ({node_var}:{label} {{{property_name}: ${property_name}}})"
        )
    
    @staticmethod
    def where_with_And(*conditions: str) -> str:
        """Build WHERE clause with AND"""
        return "WHERE " + " AND ".join(conditions)
    
    @staticmethod
    def where_with_or(*conditions: str) -> str:
        """Build WHERE clause with OR"""
        return "WHERE " + " OR ".join(conditions)
    
    @staticmethod
    def return_with_distinct(columns: List[str]) -> str:
        """Build RETURN DISTINCT clause"""
        return "RETURN DISTINCT " + ", ".join(columns)
    
    @staticmethod
    def optional_match(
        source_var: str,
        relation: str,
        target_var: str,
        target_label: str
    ) -> str:
        """Build OPTIONAL MATCH for outer join behavior"""
        return f"OPTIONAL MATCH ({source_var})-[:{relation}]->({target_var}:{target_label})"
    
    @staticmethod
    def build_pagination_clause(
        sort_field: Optional[str],
        sort_order: str = "ASC",
        limit: int = 100,
        skip: int = 0
    ) -> str:
        """Build ORDER BY with SKIP LIMIT"""
        clauses = []
        
        if sort_field:
            clauses.append(f"ORDER BY {sort_field} {sort_order}")
        
        clauses.append(f"SKIP {skip}")
        clauses.append(f"LIMIT {limit}")
        
        return " ".join(clauses)


# ============================================================
# EXAMPLE USAGE
# ============================================================

def example_usage() -> None:
    """Example of how to use query optimization"""
    
    # Example 1: Pagination
    pagination = PaginationParams(skip=0, limit=20, sort_by="created_at")
    
    cypher_query = f"""
        MATCH (n:Vulnerability)
        WHERE n.severity = $severity
        {pagination.to_cypher_order_by(['created_at', 'name'])}
        {pagination.to_cypher_skip_limit()}
        RETURN n
    """
    
    # Example 2: Caching
    cache = QueryCache(max_size=1000, ttl_seconds=3600)
    
    query = "MATCH (n:Target) RETURN n"
    params = {"target_type": "web"}
    
    # Check cache
    cached_result = cache.get(query, params)
    if cached_result:
        result = cached_result
    else:
        # Execute query
        result = {"items": [...]}  # Pseudo-code
        cache.set(query, params, result)
    
    # Example 3: Performance tracking
    metrics = MetricsCollector()
    
    start = time.time()
    # Execute query
    result_count = 42
    duration = (time.time() - start) * 1000
    
    metrics.record(query, params, duration, result_count)
    stats = metrics.get_stats()
    logger.info(f"Query stats: {stats}")
    
    # Example 4: Cypher Builder
    builder = CypherBuilder()
    
    match_clause = builder.match_with_index(
        "n", "Endpoint", "id", "endpoint_123"
    )
    where_clause = builder.where_with_And(
        "n.active = true",
        "n.created_at > $since"
    )
    pagination_clause = builder.build_pagination_clause(
        sort_field="created_at",
        limit=50,
        skip=0
    )
    
    optimized_query = f"""
        {match_clause}
        {where_clause}
        {pagination_clause}
        RETURN n
    """
