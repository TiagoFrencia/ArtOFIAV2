"""
Módulo de Base de Datos Vectorial - Memoria RAG y Episódica.

Proporciona:
- PGVectorClient: RAG con PostgreSQL + pgvector (búsqueda semántica)
- ContextSummarizer: Gestor de contexto de trabajo (token budgeting)
- EpisodicMemoryStore: Registro de experiencias tácticas exitosas
"""

from .pgvector_client import (
    PGVectorClient,
    EmbeddingRecord
)

from .context_summarizer import (
    ContextSummarizer,
    ContextWindow
)

from .episodic_memory import (
    EpisodicMemoryStore,
    EpisodicMemory,
    TacticStatus,
    ObjectiveType
)

__all__ = [
    # PGVectorClient
    "PGVectorClient",
    "EmbeddingRecord",
    
    # ContextSummarizer
    "ContextSummarizer",
    "ContextWindow",
    
    # EpisodicMemoryStore
    "EpisodicMemoryStore",
    "EpisodicMemory",
    "TacticStatus",
    "ObjectiveType",
]

__version__ = "1.0.0"
__author__ = "ArtOfIA Security"
