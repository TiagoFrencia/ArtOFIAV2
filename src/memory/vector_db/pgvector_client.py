"""
PGVector Client - Interfaz RAG con PostgreSQL + pgvector.

Gestiona almacenamiento de embeddings de:
- Respuestas HTTP
- Comandos ejecutados
- Salidas de herramientas
- Volcados de código fuente
- Patrones de error

Enabler:
- Búsqueda semántica rápida ("¿Qué respuesta fue similar a esta?")
- Compresión de contexto mediante resúmenes en cadena
- Recuperación de experiencias similares
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import asyncpg

try:
    import numpy as np
except ImportError:
    np = None


@dataclass
class EmbeddingRecord:
    """Registro de un embedding almacenado."""
    id: str
    content: str
    embedding: List[float]
    content_type: str  # "http_response", "command_output", "source_code", "error", etc.
    source_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metrics: Dict[str, Any] = field(default_factory=dict)  # size, tokens, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content_type": self.content_type,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "source_context": self.source_context
        }


class PGVectorClient:
    """Cliente RAG con PostgreSQL + pgvector."""
    
    def __init__(
        self,
        db_url: str,
        embedding_model: Optional[Any] = None,
        embedding_dim: int = 1536
    ):
        """
        Inicializa cliente pgvector.
        
        Args:
            db_url: PostgreSQL connection string
            embedding_model: Modelo para generar embeddings (ej: OpenAI embedding)
            embedding_dim: Dimensión de embeddings (defecto: 1536 para OpenAI)
        """
        self.logger = logging.getLogger(__name__)
        
        self.db_url = db_url
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        
        self.pool: Optional[asyncpg.Pool] = None
        
        # Cache de embeddings recientes
        self.embedding_cache: Dict[str, List[float]] = {}
        
        # Estadísticas
        self.stats = {
            "records_stored": 0,
            "records_retrieved": 0,
            "similarity_searches": 0,
            "cache_hits": 0,
            "embeddings_generated": 0
        }
        
        self.logger.info("✓ PGVectorClient inicializado")
    
    async def connect(self) -> bool:
        """Conecta a PostgreSQL."""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Inicializar tablas
            await self._initialize_tables()
            
            self.logger.info(f"✓ Conectado a PostgreSQL")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error conectando a PostgreSQL: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Desconecta de PostgreSQL."""
        if self.pool:
            await self.pool.close()
            self.logger.info("✓ Desconectado de PostgreSQL")
    
    async def _initialize_tables(self) -> None:
        """Inicializa tablas si no existen."""
        async with self.pool.acquire() as conn:
            # Instalar extensión pgvector si no existe
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Crear tabla de embeddings
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS memory_embeddings (
                    id VARCHAR PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector({self.embedding_dim}),
                    content_type VARCHAR(50),
                    source_context JSONB,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    metrics JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Índice para búsqueda rápida
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_embedding
                ON memory_embeddings
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            
            # Índice por content_type
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_type
                ON memory_embeddings(content_type)
            """)
            
            # Tabla de búsquedas semánticas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_searches (
                    id VARCHAR PRIMARY KEY,
                    query TEXT,
                    query_embedding vector({self.embedding_dim}),
                    results_count INT,
                    avg_similarity FLOAT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            self.logger.debug("  ✓ Tablas inicializadas")
    
    async def _generate_embedding(self, content: str) -> Optional[List[float]]:
        """
        Genera embedding para contenido.
        
        Args:
            content: Texto a embedder
        
        Returns:
            Vector de embedding o None
        """
        # Verificar cache
        content_hash = hash(content) % (2**63)  # Hash rápido
        if str(content_hash) in self.embedding_cache:
            self.stats["cache_hits"] += 1
            return self.embedding_cache[str(content_hash)]
        
        try:
            if self.embedding_model is None:
                # Fallback: embedding simple (no ideal para producción)
                self.logger.warning("  ⚠ Usando embedding mock (sin modelo real)")
                embedding = self._simple_embedding(content)
            else:
                # Usar modelo real
                embedding = await self.embedding_model.embed(content)
            
            self.stats["embeddings_generated"] += 1
            self.embedding_cache[str(content_hash)] = embedding
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"  ✗ Error generando embedding: {e}")
            return None
    
    def _simple_embedding(self, content: str) -> List[float]:
        """
        Embedding simple para testing (no usar en producción).
        Basado en estadísticas del contenido.
        """
        if np is None:
            # Fallback sin numpy
            return [0.0] * self.embedding_dim
        
        content_bytes = content.encode()
        embedding = []
        
        for i in range(self.embedding_dim):
            seed = (i + sum(content_bytes)) % 256
            np.random.seed(seed)
            embedding.append(float(np.random.randn()))
        
        return embedding
    
    async def store_record(
        self,
        id: str,
        content: str,
        content_type: str,
        source_context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Almacena contenido con embedding.
        
        Args:
            id: ID único del documento
            content: Contenido completo
            content_type: Tipo de contenido
            source_context: Contexto adicional
            metrics: Métricas (size, tokens, etc.)
        
        Returns:
            True si fue exitoso
        """
        try:
            # Generar embedding
            embedding = await self._generate_embedding(content)
            if embedding is None:
                return False
            
            # Almacenar en DB
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_embeddings 
                    (id, content, embedding, content_type, source_context, metrics)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW()
                """,
                    id,
                    content,
                    embedding,
                    content_type,
                    json.dumps(source_context or {}),
                    json.dumps(metrics or {})
                )
            
            self.stats["records_stored"] += 1
            self.logger.debug(f"  ✓ Record almacenado: {id} ({content_type})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"  ✗ Error almacenando record: {e}")
            return False
    
    async def semantic_search(
        self,
        query: str,
        content_types: Optional[List[str]] = None,
        limit: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[EmbeddingRecord, float]]:
        """
        Búsqueda semántica de contenido similar.
        
        Args:
            query: Consulta de búsqueda
            content_types: Filtrar por tipos de contenido
            limit: Número de resultados
            similarity_threshold: Mínima similitud requerida
        
        Returns:
            Lista de (EmbeddingRecord, similarity_score) tuples
        """
        try:
            # Generar embedding de query
            query_embedding = await self._generate_embedding(query)
            if query_embedding is None:
                return []
            
            # Construir SQL
            where_clause = "1=1"
            params = [query_embedding, limit]
            param_count = 2
            
            if content_types:
                content_types_sql = ", ".join([f"${i}" for i in range(param_count + 1, param_count + len(content_types) + 1)])
                where_clause = f"content_type IN ({content_types_sql})"
                params.extend(content_types)
            
            sql = f"""
                SELECT 
                    id, content, content_type, source_context, timestamp, metrics,
                    1 - (embedding <=> $1) as similarity
                FROM memory_embeddings
                WHERE {where_clause}
                    AND (1 - (embedding <=> $1)) > $3
                ORDER BY similarity DESC
                LIMIT $2
            """
            
            # Agregar threshold
            params.insert(2, similarity_threshold)
            
            results = []
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
                
                for row in rows:
                    record = EmbeddingRecord(
                        id=row["id"],
                        content=row["content"],
                        embedding=[],  # No necesitamos embeddings en respuesta
                        content_type=row["content_type"],
                        source_context=row["source_context"] or {},
                        timestamp=row["timestamp"].isoformat(),
                        metrics=row["metrics"] or {}
                    )
                    results.append((record, float(row["similarity"])))
            
            self.stats["similarity_searches"] += 1
            self.stats["records_retrieved"] += len(results)
            
            self.logger.info(f"  ✓ Búsqueda semántica: {len(results)} resultados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"  ✗ Error en búsqueda semántica: {e}")
            return []
    
    async def get_by_type(
        self,
        content_type: str,
        limit: int = 100,
        order_by: str = "timestamp DESC"
    ) -> List[EmbeddingRecord]:
        """
        Recupera todos los registros de un tipo.
        
        Args:
            content_type: Tipo de contenido a filtrar
            limit: Límite de resultados
            order_by: Ordenamiento SQL
        
        Returns:
            Lista de EmbeddingRecords
        """
        try:
            sql = f"""
                SELECT id, content, content_type, source_context, timestamp, metrics
                FROM memory_embeddings
                WHERE content_type = $1
                ORDER BY {order_by}
                LIMIT $2
            """
            
            records = []
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, content_type, limit)
                
                for row in rows:
                    records.append(EmbeddingRecord(
                        id=row["id"],
                        content=row["content"],
                        embedding=[],
                        content_type=row["content_type"],
                        source_context=row["source_context"] or {},
                        timestamp=row["timestamp"].isoformat(),
                        metrics=row["metrics"] or {}
                    ))
            
            self.logger.debug(f"  ✓ {len(records)} registros de {content_type} recuperados")
            
            return records
            
        except Exception as e:
            self.logger.error(f"  ✗ Error recuperando por tipo: {e}")
            return []
    
    async def delete_old_records(self, days: int = 7) -> int:
        """
        Limpia registros más antiguos que N días.
        
        Args:
            days: Días de retención
        
        Returns:
            Número de registros eliminados
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(f"""
                    DELETE FROM memory_embeddings
                    WHERE created_at < NOW() - INTERVAL '{days} days'
                """)
            
            deleted_count = int(result.split()[-1]) if result else 0
            self.logger.info(f"  🗑 {deleted_count} registros antiguos eliminados")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"  ✗ Error limpiando registros: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cliente."""
        return {
            "timestamp": datetime.now().isoformat(),
            **self.stats,
            "embedding_cache_size": len(self.embedding_cache)
        }
    
    async def export_memory(self, max_records: int = 1000) -> Dict[str, Any]:
        """
        Exporta registros de memoria para análisis.
        
        Args:
            max_records: Máximo de registros a exportar
        
        Returns:
            Diccionario con registros agrupados por tipo
        """
        try:
            sql = """
                SELECT content_type, COUNT(*) as count
                FROM memory_embeddings
                GROUP BY content_type
            """
            
            export_data = {"timestamp": datetime.now().isoformat(), "records_by_type": {}}
            
            async with self.pool.acquire() as conn:
                stats = await conn.fetch(sql)
                
                for row in stats:
                    content_type = row["content_type"]
                    count = row["count"]
                    
                    records = await self.get_by_type(content_type, limit=min(count, 100))
                    
                    export_data["records_by_type"][content_type] = {
                        "total": count,
                        "samples": [r.to_dict() for r in records[:10]]
                    }
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"  ✗ Error exportando memoria: {e}")
            return {"error": str(e)}
