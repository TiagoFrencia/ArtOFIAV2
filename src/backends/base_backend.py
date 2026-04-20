"""
Base Backend Abstract Interface
================================

Define la interfaz estándar que todos los backends deben implementar.
Garantiza que docker_sandbox, llm_providers y cloud_infrastructure
se integren de forma cohesiva con el orquestador.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class BackendType(str, Enum):
    """Tipos de backends soportados"""
    DOCKER_SANDBOX = "docker_sandbox"
    LLM_PROVIDER = "llm_provider"
    CLOUD_INFRASTRUCTURE = "cloud_infrastructure"


class ExecutionStatus(str, Enum):
    """Estado de ejecución"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"
    REVOKED = "revoked"


@dataclass
class ExecutionRequest:
    """Request estandarizado para un backend"""
    request_id: str
    backend_type: BackendType
    payload: Dict[str, Any]
    timeout_seconds: int = 300
    max_retries: int = 3
    metadata: Dict[str, Any] | None = None


@dataclass
class ExecutionResponse:
    """Response estandarizado de un backend"""
    request_id: str
    status: ExecutionStatus
    output: str = ""
    error_message: str = ""
    execution_time_ms: int = 0
    resource_usage: Dict[str, Any] | None = None
    security_violations: List[str] | None = None


class BaseBackend(ABC):
    """
    Clase abstracta base para todos los backends.
    
    Define contratos que sandbox, LLM providers y cloud infra deben cumplir.
    """
    
    def __init__(self, backend_type: BackendType, config: Dict[str, Any]):
        self.backend_type = backend_type
        self.config = config
        self.is_initialized = False
        self.audit_log: list[Dict[str, Any]] = []
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Inicializar el backend.
        Valida configuración, conecta a servicios externos, prepara recursos.
        """
        pass
    
    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        Ejecutar la operación solicitada.
        """
        pass
    
    @abstractmethod
    async def validate_security(self, request: ExecutionRequest) -> bool:
        """
        Validar que la request no viola políticas de seguridad.
        Retorna True si es seguro proceder.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Limpiar recursos después de ejecución.
        """
        pass
    
    async def audit_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """
        Registrar operación en log de auditoría.
        """
        log_entry = {
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "operation": operation,
            "details": details,
        }
        self.audit_log.append(log_entry)
        
        # Guardar en persistencia
        await self._persist_audit(log_entry)
    
    async def _persist_audit(self, log_entry: Dict[str, Any]) -> None:
        """
        Guardar entrada de auditoría a persistencia.
        Sobrescribir en subclases.
        """
        pass
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Retornar historial de operaciones auditadas"""
        return self.audit_log.copy()
