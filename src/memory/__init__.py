"""
Módulo de Memoria Híbrida - Sistema Avanzado de Retención de Contexto.

Combina dos capas de memoria para evitar bucles, pérdida de contexto y decisiones ciegas:

1. MEMORIA SEMÁNTICA (Grafo de Conocimiento)
   └─ knowledge_graph/
      ├─ GraphManager: Mapa de relaciones (Endpoint → Token → Vulnerabilidad)
      ├─ TemporalTracker: Consciencia temporal de tácticas/defensas
      └─ ExploitationContext: Registro global del estado del ataque

2. MEMORIA RAG + EPISÓDICA (Base de Datos Vectorial)
   └─ vector_db/
      ├─ PGVectorClient: Búsqueda semántica rápida de experiencias
      ├─ ContextSummarizer: Gestor de contexto LLM (token budgeting)
      └─ EpisodicMemoryStore: Playbooks extraídos de éxitos previos

Propósito:
- Prevenir repetición de acciones fallidas (temporal awareness)
- Detectar bucles automáticamente (cycle detection)
- Sugerir tácticas probadas para nuevos targets (episodic retrieval)
- Mantener contexto coherente con presupuesto de tokens (summarization)

Integración:
- Orchestrator → Planner (3-7 steps) → Agents (con memory enrichment)
- ReconAgent/LogicAgent/ExploitAgent registran experiencias
- MemoryStore retroalimenta decisiones futuras
"""

from .knowledge_graph import (
    GraphManager,
    TemporalTracker,
    ExploitationContext,
    GraphNode,
    GraphRelation,
    TemporalEvent,
    NodeType,
    RelationType,
    EventType,
    FrameworkType,
    PayloadCategory
)

from .vector_db import (
    PGVectorClient,
    ContextSummarizer,
    EpisodicMemoryStore,
    EmbeddingRecord,
    ContextWindow,
    EpisodicMemory,
    TacticStatus,
    ObjectiveType
)

__all__ = [
    # Knowledge Graph
    "GraphManager",
    "TemporalTracker",
    "ExploitationContext",
    "GraphNode",
    "GraphRelation",
    "TemporalEvent",
    "NodeType",
    "RelationType",
    "EventType",
    "FrameworkType",
    "PayloadCategory",
    
    # Vector DB
    "PGVectorClient",
    "ContextSummarizer",
    "EpisodicMemoryStore",
    "EmbeddingRecord",
    "ContextWindow",
    "EpisodicMemory",
    "TacticStatus",
    "ObjectiveType",
]

__version__ = "1.0.0"
__author__ = "ArtOfIA Security"
__description__ = "Hybrid memory system for advanced offensive security agents"


class MemorySystem:
    """
    Sistema de memoria híbrido - Inicializador y coordinador.
    
    Uso:
        memory_system = MemorySystem(
            neo4j_uri="bolt://localhost:7687",
            postgres_url="postgresql://user:pass@localhost/memorydb"
        )
        await memory_system.initialize()
        
        # Registrar experiencia
        await memory_system.record_episode(...)
        
        # Buscar similar
        similar = memory_system.find_similar_episodes(...)
    """
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "default",
        postgres_url: str = "postgresql://user:pass@localhost/memory",
        max_context_tokens: int = 8000
    ):
        """Inicializa sistema de memoria."""
        # Grafo de conocimiento
        self.graph_manager = GraphManager(neo4j_uri, neo4j_user, neo4j_password)
        self.temporal_tracker = TemporalTracker()
        
        # Base de datos vectorial
        self.pgvector_client = PGVectorClient(postgres_url)
        self.context_summarizer = ContextSummarizer(max_tokens=max_context_tokens)
        self.episodic_store = EpisodicMemoryStore()
        
        # Contextos por objetivo
        self.exploitation_contexts: Dict[str, ExploitationContext] = {}
    
    async def initialize(self) -> bool:
        """Inicializa conexiones."""
        graph_ok = await self.graph_manager.connect()
        vector_ok = await self.pgvector_client.connect()
        
        return graph_ok and vector_ok
    
    async def shutdown(self) -> None:
        """Cierra conexiones."""
        await self.graph_manager.disconnect()
        await self.pgvector_client.disconnect()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas globales del sistema."""
        import json
        
        return {
            "timestamp": datetime.now().isoformat(),
            "graph": self.graph_manager.get_stats(),
            "temporal": self.temporal_tracker.export_temporal_data(),
            "vector_db": self.pgvector_client.get_stats(),
            "context": self.context_summarizer.get_stats(),
            "episodic": self.episodic_store.get_statistics()
        }


# Para testing
from datetime import datetime
from typing import Dict, Any
