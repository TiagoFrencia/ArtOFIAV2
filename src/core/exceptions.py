"""
Exception Hierarchy for ArtOfIA

Define custom exceptions with proper inheritance and context for:
- Security violations
- Agent errors
- System failures
- User/API errors
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


class ErrorSeverity(Enum):
    """Severity levels for exceptions"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Rich context information for exceptions"""
    timestamp: datetime
    component: str  # e.g., "recon_agent", "docker_sandbox", "memory_manager"
    operation: str  # e.g., "initialize", "execute_attack", "create_node"
    severity: ErrorSeverity
    details: Dict[str, Any]  # Additional context (user_id, target_id, etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "severity": self.severity.value,
            "details": self.details
        }


# ============================================================
# CORE EXCEPTIONS
# ============================================================

class ArtOfIAException(Exception):
    """Base exception for all ArtOfIA errors"""
    
    def __init__(
        self,
        message: str,
        component: str = "unknown",
        operation: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.context = ErrorContext(
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            severity=severity,
            details=details or {}
        )
        self.cause = cause
        
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format error message with context"""
        return (
            f"[{self.context.severity.value.upper()}] {self.context.component}."
            f"{self.context.operation}: {self.message}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to dict"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "context": self.context.to_dict(),
            "cause": self.cause.__class__.__name__ if self.cause else None
        }


# ============================================================
# SECURITY EXCEPTIONS
# ============================================================

class SecurityException(ArtOfIAException):
    """Base for security-related errors"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        super().__init__(message, **kwargs)


class ValidationException(SecurityException):
    """Input validation failed"""
    pass


class AuthorizationException(SecurityException):
    """Operation not authorized"""
    pass


class SandboxException(SecurityException):
    """Docker sandbox security violation"""
    pass


class CommandExecutionException(SecurityException):
    """Attempt to execute forbidden command"""
    
    def __init__(
        self,
        command: str,
        reason: str,
        component: str = "supervisor",
        **kwargs
    ):
        message = f"Forbidden command blocked: {command} ({reason})"
        kwargs.setdefault("details", {})["command"] = command
        kwargs["details"]["reason"] = reason
        super().__init__(message, component=component, **kwargs)


class InjectionException(SecurityException):
    """SQL/Cypher/Command injection detected"""
    
    def __init__(
        self,
        injection_type: str,  # "sql", "cypher", "command"
        target: str,
        **kwargs
    ):
        message = f"{injection_type.upper()} injection detected in: {target}"
        kwargs.setdefault("details", {})["injection_type"] = injection_type
        kwargs["details"]["target"] = target
        super().__init__(message, **kwargs)


class RateLimitException(SecurityException):
    """Rate limit exceeded"""
    
    def __init__(
        self,
        resource: str,
        limit: int,
        window: int,  # seconds
        **kwargs
    ):
        message = f"Rate limit exceeded: {limit} requests per {window}s for {resource}"
        kwargs.setdefault("details", {})["resource"] = resource
        kwargs["details"]["limit"] = limit
        kwargs["details"]["window"] = window
        super().__init__(message, **kwargs)


# ============================================================
# AGENT EXCEPTIONS
# ============================================================

class AgentException(ArtOfIAException):
    """Base for agent-related errors"""
    
    def __init__(self, message: str, agent_name: str = "unknown", **kwargs):
        kwargs.setdefault("component", agent_name)
        supersetter = kwargs.pop("severity", ErrorSeverity.ERROR)
        super().__init__(message, severity=supersetter, **kwargs)


class AgentInitializationException(AgentException):
    """Agent failed to initialize"""
    pass


class AgentExecutionException(AgentException):
    """Agent execution failed"""
    pass


class AgentTimeoutException(AgentException):
    """Agent operation timed out"""
    
    def __init__(
        self,
        agent_name: str,
        operation: str,
        timeout_seconds: float,
        **kwargs
    ):
        message = f"Agent {agent_name} timeout on {operation} (>{timeout_seconds}s)"
        kwargs.setdefault("details", {})["timeout_seconds"] = timeout_seconds
        kwargs["details"]["agent_name"] = agent_name
        super().__init__(message, agent_name=agent_name, operation=operation, **kwargs)


class AgentDependencyException(AgentException):
    """Agent dependency not available"""
    
    def __init__(self, agent_name: str, missing_dependency: str, **kwargs):
        message = f"Missing dependency for {agent_name}: {missing_dependency}"
        kwargs.setdefault("details", {})["missing_dependency"] = missing_dependency
        super().__init__(message, agent_name=agent_name, **kwargs)


# ============================================================
# DATABASE/STORAGE EXCEPTIONS
# ============================================================

class StorageException(ArtOfIAException):
    """Base for storage-related errors"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("component", "storage")
        super().__init__(message, **kwargs)


class ConnectionException(StorageException):
    """Database connection failed"""
    pass


class QueryException(StorageException):
    """Database query failed"""
    pass


class PersistenceException(StorageException):
    """Data persistence failed"""
    
    def __init__(
        self,
        operation: str,  # "insert", "update", "delete"
        resource_type: str,  # "node", "relation", "audit_log"
        reason: str,
        **kwargs
    ):
        message = (
            f"Failed to {operation} {resource_type}: {reason}"
        )
        kwargs.setdefault("details", {})["operation"] = operation
        kwargs["details"]["resource_type"] = resource_type
        super().__init__(
            message,
            component="storage",
            operation=operation,
            **kwargs
        )


# ============================================================
# RESOURCE EXCEPTIONS
# ============================================================

class ResourceException(ArtOfIAException):
    """Base for resource-related errors"""
    pass


class OutOfMemoryException(ResourceException):
    """System out of memory"""
    
    def __init__(self, required_bytes: int, available_bytes: int, **kwargs):
        message = (
            f"Insufficient memory: required {required_bytes} bytes, "
            f"available {available_bytes} bytes"
        )
        kwargs.setdefault("details", {})["required_bytes"] = required_bytes
        kwargs["details"]["available_bytes"] = available_bytes
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        super().__init__(message, component="system", **kwargs)


class ResourceExhaustedException(ResourceException):
    """Resource exhausted (connections, file descriptors, etc.)"""
    
    def __init__(self, resource_type: str, limit: int, **kwargs):
        message = f"Resource exhausted: {resource_type} (limit: {limit})"
        kwargs.setdefault("details", {})["resource_type"] = resource_type
        kwargs["details"]["limit"] = limit
        super().__init__(message, component="system", **kwargs)


# ============================================================
# CONFIGURATION EXCEPTIONS
# ============================================================

class ConfigurationException(ArtOfIAException):
    """Configuration error"""
    
    def __init__(self, message: str, config_key: str = "", **kwargs):
        if config_key:
            message = f"Configuration error [{config_key}]: {message}"
        kwargs.setdefault("component", "config")
        super().__init__(message, **kwargs)


class MissingConfigurationException(ConfigurationException):
    """Required configuration missing"""
    pass


# ============================================================
# ORCHESTRATION EXCEPTIONS
# ============================================================

class OrchestrationException(ArtOfIAException):
    """Base for orchestration errors"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("component", "orchestrator")
        super().__init__(message, **kwargs)


class StageFailureException(OrchestrationException):
    """A stage in the operation failed"""
    
    def __init__(
        self,
        stage_name: str,
        reason: str,
        stage_number: int = 0,
        **kwargs
    ):
        message = f"Stage failure [{stage_name}]: {reason}"
        kwargs.setdefault("details", {})["stage_name"] = stage_name
        kwargs["details"]["stage_number"] = stage_number
        super().__init__(message, operation=stage_name, **kwargs)


class OperationCanceledException(OrchestrationException):
    """Operation was cancelled"""
    
    def __init__(self, operation_id: str, reason: str = "", **kwargs):
        message = f"Operation cancelled: {operation_id}"
        if reason:
            message += f" ({reason})"
        kwargs.setdefault("details", {})["operation_id"] = operation_id
        super().__init__(message, **kwargs)


# ============================================================
# EXTERNAL SERVICE EXCEPTIONS
# ============================================================

class ExternalServiceException(ArtOfIAException):
    """External service error"""
    
    def __init__(
        self,
        service_name: str,
        status_code: Optional[int] = None,
        **kwargs
    ):
        message = f"External service error: {service_name}"
        if status_code:
            message += f" (HTTP {status_code})"
        kwargs.setdefault("details", {})["service_name"] = service_name
        if status_code:
            kwargs["details"]["status_code"] = status_code
        super().__init__(message, **kwargs)


class LLMException(ExternalServiceException):
    """LLM provider error"""
    
    def __init__(self, reason: str, model: str = "", **kwargs):
        kwargs.setdefault("details", {})["model"] = model
        super().__init__("llm_provider", **kwargs)
        self.message = f"LLM error ({model}): {reason}"


class WebServiceException(ExternalServiceException):
    """Target web service error"""
    
    def __init__(
        self,
        target_url: str,
        status_code: int,
        **kwargs
    ):
        message = f"Target service returned {status_code}: {target_url}"
        kwargs.setdefault("details", {})["target_url"] = target_url
        kwargs["details"]["status_code"] = status_code
        super().__init__(service_name="target_service", status_code=status_code, **kwargs)
        self.message = message


# ============================================================
# EXCEPTION REGISTRY
# ============================================================

EXCEPTION_REGISTRY = {
    # Security
    "validation": ValidationException,
    "authorization": AuthorizationException,
    "sandbox": SandboxException,
    "command_execution": CommandExecutionException,
    "injection": InjectionException,
    "rate_limit": RateLimitException,
    
    # Agent
    "agent_initialization": AgentInitializationException,
    "agent_execution": AgentExecutionException,
    "agent_timeout": AgentTimeoutException,
    "agent_dependency": AgentDependencyException,
    
    # Storage
    "connection": ConnectionException,
    "query": QueryException,
    "persistence": PersistenceException,
    
    # Resources
    "out_of_memory": OutOfMemoryException,
    "resource_exhausted": ResourceExhaustedException,
    
    # Configuration
    "configuration": ConfigurationException,
    "missing_configuration": MissingConfigurationException,
    
    # Orchestration
    "stage_failure": StageFailureException,
    "operation_cancelled": OperationCanceledException,
    
    # External
    "external_service": ExternalServiceException,
    "llm": LLMException,
    "web_service": WebServiceException,
}


def get_exception_class(exception_type: str):
    """Look up exception class by type string"""
    return EXCEPTION_REGISTRY.get(exception_type, ArtOfIAException)
