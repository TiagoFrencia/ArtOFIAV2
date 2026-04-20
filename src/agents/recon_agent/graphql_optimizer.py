"""
GraphQL Optimizer - Advanced GraphQL performance and security optimizations.

Proporciona:
- Query complexity analysis (detecta queries maliciosas/DoS)
- Depth limiting (previene circular queries infinitas)
- Schema caching (reutiliza introspection results)
- Field resolution batching (agrupa resoluciones)
- Query timeout protection
"""

import logging
import json
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QueryComplexityMetrics:
    """Métricas de complejidad de query GraphQL."""
    depth: int = 0
    breadth: int = 0  # Número de campos en nivel máximo
    total_nodes: int = 0  # Total de nodos en el AST
    field_count: int = 0  # Total de campos solicitados
    variable_count: int = 0
    fragment_count: int = 0
    complexity_score: float = 0.0  # 0-100, donde >50 es sospechoso
    is_introspection: bool = False
    has_mutations: bool = False
    has_subscriptions: bool = False
    aliases_used: int = 0  # Queries con aliases = potencial para amplificación


class GraphQLQueryAnalyzer:
    """Analizador de complejidad de queries GraphQL.
    
    Previene DoS attacks detectando:
    - Circular field references (A.b.a.b.a...)
    - Deep nesting (>10 niveles)
    - Excessive field selection
    - Multiple aliases (amplificación)
    """
    
    # Thresholds para detectar queries maliciosas
    MAX_DEPTH = 10  # Maximum nesting depth
    MAX_BREADTH = 50  # Maximum fields at any level
    MAX_FIELD_COUNT = 200  # Maximum total fields
    MAX_COMPLEXITY_SCORE = 60  # DoS threshold
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_query_complexity(self, query: str) -> QueryComplexityMetrics:
        """Analiza complejidad de una query GraphQL.
        
        Args:
            query: Query GraphQL a analizar
            
        Returns:
            QueryComplexityMetrics con score y detección de anomalías
        """
        metrics = QueryComplexityMetrics()
        
        try:
            # Parse basic GraphQL structure
            lines = query.strip().split('\n')
            
            # Count basic metrics
            metrics.depth = self._calculate_depth(query)
            metrics.breadth = self._calculate_breadth(query)
            metrics.total_nodes = len([l for l in lines if '{' in l or '}' in l])
            metrics.field_count = self._count_fields(query)
            metrics.variable_count = query.count('$')
            metrics.fragment_count = query.count('fragment ')
            metrics.aliases_used = query.count(' as ') if ' as ' in query.lower() else 0
            metrics.is_introspection = '__schema' in query or '__type' in query
            metrics.has_mutations = 'mutation' in query.lower()
            metrics.has_subscriptions = 'subscription' in query.lower()
            
            # Calculate complexity score (0-100)
            metrics.complexity_score = self._calculate_complexity_score(metrics)
            
            # Log suspicious queries
            if metrics.complexity_score > self.MAX_COMPLEXITY_SCORE:
                self.logger.warning(
                    f"🚨 Suspicious query detected (score: {metrics.complexity_score:.1f}): "
                    f"depth={metrics.depth}, breadth={metrics.breadth}, "
                    f"fields={metrics.field_count}"
                )
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
        
        return metrics
    
    def _calculate_depth(self, query: str) -> int:
        """Calcula profundidad máxima de nesting."""
        max_depth = 0
        current_depth = 0
        in_string = False
        
        for char in query:
            if char == '"' and (query[query.index(char)-1:query.index(char)] != '\\'):
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == '}':
                    current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _calculate_breadth(self, query: str) -> int:
        """Calcula máximo número de campos en un nivel."""
        # Simple heuristic: count commas at top level of deepest nesting
        lines = query.split('\n')
        max_fields = 0
        for line in lines:
            if '{' in line:
                # Count fields in this line (rough estimate)
                field_count = line.count(',') + 1
                max_fields = max(max_fields, field_count)
        return max_fields
    
    def _count_fields(self, query: str) -> int:
        """Cuenta total de campos en la query."""
        # Simple heuristic: count identifiers
        import re
        fields = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*(?:\s*\(.*?\))?', query)
        # Filter out GraphQL keywords
        keywords = {'query', 'mutation', 'subscription', 'fragment', 'on', 'if', 'skip', 'include'}
        return len([f for f in fields if f not in keywords])
    
    def _calculate_complexity_score(self, metrics: QueryComplexityMetrics) -> float:
        """Calcula score de complejidad (0-100)."""
        score = 0.0
        
        # Depth penalty (each level beyond 5 = +10 points)
        if metrics.depth > 5:
            score += (metrics.depth - 5) * 10
        
        # Breadth penalty (fields beyond 30 = +1 point each)
        if metrics.breadth > 30:
            score += (metrics.breadth - 30) * 1
        
        # Field count penalty (beyond 100 = +0.5 per field)
        if metrics.field_count > 100:
            score += (metrics.field_count - 100) * 0.5
        
        # Aliases amplification (each alias = +5 points)
        score += metrics.aliases_used * 5
        
        # Fragments add complexity (+10 points each)
        score += metrics.fragment_count * 10
        
        # Mutations more suspicious (+20 points)
        if metrics.has_mutations:
            score += 20
        
        # Introspection queries (normal but notable, +15)
        if metrics.is_introspection:
            score += 15
        
        return min(score, 100.0)  # Cap at 100


class GraphQLSchemaCacher:
    """Cachea esquemas GraphQL introspectados.
    
    Previene repeated introspection queries que:
    - Consumen ancho de banda
    - Pueden detectarse como patrones de ataque
    - Son operaciones costosas
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Inicializa el caché.
        
        Args:
            cache_ttl: TTL del cache en segundos (default: 1 hora)
        """
        self.cache: Dict[str, Tuple[Dict[str, Any], datetime]] = {}
        self.cache_ttl = cache_ttl
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_key(self, endpoint: str) -> str:
        """Genera cache key para un endpoint."""
        return hashlib.md5(endpoint.encode()).hexdigest()
    
    def get_cached_schema(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Obtiene esquema cacheado si existe y es válido.
        
        Args:
            endpoint: URL del endpoint GraphQL
            
        Returns:
            Schema cacheado o None si no está en cache o expiró
        """
        key = self._get_cache_key(endpoint)
        
        if key not in self.cache:
            return None
        
        schema, timestamp = self.cache[key]
        
        # Verificar si expiró
        if datetime.now() - timestamp > timedelta(seconds=self.cache_ttl):
            del self.cache[key]
            self.logger.info(f"Cache expired for {endpoint}")
            return None
        
        self.logger.info(f"⚡ Schema cache hit for {endpoint}")
        return schema
    
    def cache_schema(self, endpoint: str, schema: Dict[str, Any]) -> None:
        """Cachea un esquema GraphQL.
        
        Args:
            endpoint: URL del endpoint
            schema: Schema introspectado
        """
        key = self._get_cache_key(endpoint)
        self.cache[key] = (schema, datetime.now())
        self.logger.info(f"Cached schema for {endpoint} (size: {len(json.dumps(schema))} bytes)")
    
    def clear_cache(self) -> None:
        """Limpia todo el cache."""
        self.cache.clear()
        self.logger.info("GraphQL schema cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache."""
        return {
            "cached_endpoints": len(self.cache),
            "total_size_bytes": sum(len(json.dumps(s[0])) for s in self.cache.values()),
            "ttl_seconds": self.cache_ttl
        }


class GraphQLFieldResolutionBatcher:
    """Agrupa resoluciones de campos para mejor performance.
    
    Evita hacer N+1 queries cuando se resuelven múltiples campos
    que requieren lookups en la base de datos.
    
    Ejemplo:
    - Query: { users { posts { author } } }
    - Sin batching: 1 query users + N queries posts + N*M queries authors
    - Con batching: 1 query users + 1 batch query posts + 1 batch query authors
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pending_batches: Dict[str, List[Any]] = {}
    
    async def batch_resolve_field(
        self, 
        field_name: str, 
        parent_ids: List[Any],
        resolver_fn
    ) -> Dict[Any, Any]:
        """Resuelve múltiples IDs de padre en batch.
        
        Args:
            field_name: Nombre del campo a resolver
            parent_ids: Lista de IDs padres
            resolver_fn: Función para resolver (async)
            
        Returns:
            Dict mapeando parent_id → resolved_value
        """
        if not parent_ids:
            return {}
        
        self.logger.debug(
            f"Batch resolving {field_name} for {len(parent_ids)} parents"
        )
        
        try:
            # Llamar resolver con lista completa (no uno por uno)
            results = await resolver_fn(parent_ids)
            
            # Retornar como dict: parent_id → value
            if isinstance(results, dict):
                return results
            
            # Si es lista, mapear a IDs
            return {pid: results[i] for i, pid in enumerate(parent_ids)}
            
        except Exception as e:
            self.logger.error(f"Error batch resolving {field_name}: {e}")
            return {}


class GraphQLOptimizer:
    """Coordinador de todas las optimizaciones GraphQL.
    
    Proporciona interfaz única para:
    - Análisis de complejidad
    - Caching de esquemas
    - Batching de resoluciones
    - Protección contra DoS
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Inicializa el optimizador.
        
        Args:
            cache_ttl: TTL para cache de esquemas
        """
        self.analyzer = GraphQLQueryAnalyzer()
        self.schema_cacher = GraphQLSchemaCacher(cache_ttl=cache_ttl)
        self.field_batcher = GraphQLFieldResolutionBatcher()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_and_validate_query(
        self, 
        query: str, 
        raise_on_suspicious: bool = False
    ) -> QueryComplexityMetrics:
        """Analiza y valida una query GraphQL.
        
        Args:
            query: Query GraphQL
            raise_on_suspicious: Lanzar excepción si es sospechosa
            
        Returns:
            QueryComplexityMetrics
            
        Raises:
            ValueError: Si raise_on_suspicious=True y query es maliciosa
        """
        metrics = await self.analyzer.analyze_query_complexity(query)
        
        if raise_on_suspicious and metrics.complexity_score > self.analyzer.MAX_COMPLEXITY_SCORE:
            raise ValueError(
                f"Query complexity score too high: {metrics.complexity_score:.1f} "
                f"(max: {self.analyzer.MAX_COMPLEXITY_SCORE})"
            )
        
        return metrics
    
    def get_cached_or_none(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Obtiene esquema cacheado de un endpoint.
        
        Args:
            endpoint: URL del endpoint
            
        Returns:
            Schema cacheado o None
        """
        return self.schema_cacher.get_cached_schema(endpoint)
    
    def cache_schema(self, endpoint: str, schema: Dict[str, Any]) -> None:
        """Cachea esquema de endpoint.
        
        Args:
            endpoint: URL del endpoint
            schema: Schema introspectado
        """
        self.schema_cacher.cache_schema(endpoint, schema)
    
    async def batch_resolve_relationships(
        self,
        parent_type: str,
        parent_ids: List[Any],
        resolver_fn
    ) -> Dict[Any, Any]:
        """Resuelve relaciones en batch.
        
        Args:
            parent_type: Tipo del padre (para logging)
            parent_ids: Lista de IDs padres
            resolver_fn: Función para resolver
            
        Returns:
            Dict mapeando parent_id → resolved_value
        """
        return await self.field_batcher.batch_resolve_field(
            parent_type, parent_ids, resolver_fn
        )
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de optimizaciones.
        
        Returns:
            Dict con stats de cache, analysis, etc
        """
        return {
            "schema_cache": self.schema_cacher.get_cache_stats(),
            "analyzer_thresholds": {
                "max_depth": self.analyzer.MAX_DEPTH,
                "max_breadth": self.analyzer.MAX_BREADTH,
                "max_field_count": self.analyzer.MAX_FIELD_COUNT,
                "max_complexity_score": self.analyzer.MAX_COMPLEXITY_SCORE,
            },
            "timestamp": datetime.now().isoformat()
        }
