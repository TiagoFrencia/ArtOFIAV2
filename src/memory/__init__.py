"""Hybrid Memory System - Advanced Context Retention for ArtOfIA.

Combines two memory layers to prevent loops, context loss, and blind decisions:

1. **SEMANTIC MEMORY** (Knowledge Graph):
   - GraphManager: Relationship mapping (Endpoint → Token → Vulnerability)
   - TemporalTracker: Temporal awareness of tactics and defenses
   - ExploitationContext: Global attack state registry

2. **EPISODIC + RAG MEMORY** (Vector Database):
   - PGVectorClient: Fast semantic search of experiences
   - ContextSummarizer: LLM context manager (token budgeting)
   - EpisodicMemoryStore: Playbooks from previous successes

Benefits:
    - Prevents repetition of failed actions (temporal awareness)
    - Automatic loop detection (cycle detection)
    - Suggests proven tactics for new targets (episodic retrieval)
    - Maintains coherent context with token budgeting

Integration:
    Orchestrator → Planner (3-7 steps) → Agents (with memory enrichment)
    
    ReconAgent/LogicAgent/ExploitAgent register experiences
    MemoryStore provides feedback for future decisions

Example:
    from src.memory import GraphManager, PGVectorClient
    
    graph = GraphManager()
    await graph.initialize()
    
    vector_db = PGVectorClient()
    await vector_db.connect()
"""

from datetime import datetime
from typing import Dict, Any

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
