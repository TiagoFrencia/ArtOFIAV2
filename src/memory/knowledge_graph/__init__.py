"""
Módulo de Grafo de Conocimiento - Memoria Semántica a Largo Plazo.

Proporciona:
- GraphManager: Control de grafo Neo4j, relaciones semánticas
- TemporalTracker: Consciencia temporal de eventos
- ExploitationContext: Registro del estado del ataque
"""

from .graph_manager import (
    GraphManager,
    GraphNode,
    GraphRelation,
    NodeType,
    RelationType
)

from .temporal_tracker import (
    TemporalTracker,
    TemporalEvent,
    EventType
)

from .exploitation_context import (
    ExploitationContext,
    FrameworkType,
    PayloadCategory,
    PayloadRecord,
    FrameworkSignature
)

__all__ = [
    # GraphManager
    "GraphManager",
    "GraphNode",
    "GraphRelation",
    "NodeType",
    "RelationType",
    
    # TemporalTracker
    "TemporalTracker",
    "TemporalEvent",
    "EventType",
    
    # ExploitationContext
    "ExploitationContext",
    "FrameworkType",
    "PayloadCategory",
    "PayloadRecord",
    "FrameworkSignature",
]

__version__ = "1.0.0"
__author__ = "ArtOfIA Security"
