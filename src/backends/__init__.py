"""
Backends Module - Infraestructura Completa
==========================================

Tres backend especializados:
1. docker_sandbox: Aislamiento hermético de exploits
2. llm_providers: Gestión inteligente de modelos de IA
3. cloud_infrastructure: Escalabilidad en la nube
"""

from .base_backend import BaseBackend, BackendType, ExecutionRequest, ExecutionResponse, ExecutionStatus

# Import submodules
from . import docker_sandbox
from . import llm_providers
from . import cloud_infrastructure

__all__ = [
    "BaseBackend",
    "BackendType",
    "ExecutionRequest",
    "ExecutionResponse",
    "ExecutionStatus",
    "docker_sandbox",
    "llm_providers",
    "cloud_infrastructure",
]
