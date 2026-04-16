"""
ArtOfIA Recon Agent - Módulo de reconocimiento pasivo e inteligencia.

Este agente es responsable de:
- Descubrimiento pasivo de endpoints y servicios
- Análisis de JavaScript y extracción de APIs
- Mapping de esquemas GraphQL
- Recolección de información de red y DNS
- OSINT pasivo y análisis de infraestructura

Arquitectura:
- server.py: Router principal y registro de tools
- js_analyzer.py: Análisis de código JavaScript
- graphql_mapper.py: Descobrimiento de GraphQL
- network_tools.py: Recolección de información de red
- prompts.yaml: Instrucciones para el modelo de IA
"""

__version__ = "1.0.0"
__author__ = "ArtOfIA Security Team"

from src.agents.recon_agent.server import ReconAgentServer
from src.agents.recon_agent.js_analyzer import JavaScriptAnalyzer
from src.agents.recon_agent.graphql_mapper import GraphQLMapper
from src.agents.recon_agent.network_tools import NetworkTools

__all__ = [
    "ReconAgentServer",
    "JavaScriptAnalyzer",
    "GraphQLMapper",
    "NetworkTools",
]
