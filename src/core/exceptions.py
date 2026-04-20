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
    """Severity levels for exceptions.
    
    Attributes:
        INFO: Informational, no action required
        WARNING: Warning, may need review  
        ERROR: Error, operation failed
        CRITICAL: Critical, immediate action required
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Rich context information for exceptions.
    
    Captures error metadata including timing, component, operation,
    and additional contextual details for error tracking.
    
    Attributes:
        timestamp: When the error occurred (datetime)
        component: System component (e.g., 'recon_agent', 'docker_sandbox')
        operation: Operation being performed (e.g., 'initialize', 'execute')
        severity: Error severity level (ErrorSeverity enum)
        details: Dictionary with additional context (user_id, target_id, etc.)
    """
    timestamp: datetime
    component: str
    operation: str
    severity: ErrorSeverity
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize error context to dictionary.
        
        Returns:
            Dictionary with all context fields in JSON-serializable format.
        """
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
    """Base exception for all ArtOfIA errors.
    
    Provides rich error context with severity levels, component tracking,
    timestamps, and detailed error information for comprehensive error handling
    and debugging.
    
    Args:
        message: Human-readable error message
        component: System component where error occurred (default: 'unknown')
        operation: Operation being performed (default: 'unknown')
        severity: Error severity level (default: ERROR)
        details: Optional dictionary with additional context
        cause: Optional original exception that caused this error
        
    Attributes:
        message: The error message
        context: ErrorContext with timing and component information
        cause: Original exception if any
    """
    
    def __init__(
        self,
        message: str,
        component: str = "unknown",
        operation: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
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
        """Format error message with context.
        
        Returns:
            Formatted string with severity, component, operation, and message.
        """
        return (
            f"[{self.context.severity.value.upper()}] {self.context.component}."
            f"{self.context.operation}: {self.message}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to dictionary.
        
        Returns:
            Dictionary with exception type, message, context, and cause.
        """
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
    """Base exception for security-related errors.
    
    Used for violations of security policies, authorization failures,
    and other security-critical error conditions. Automatically sets
    severity to CRITICAL.
    
    Args:
        message: Description of the security violation
        **kwargs: Additional keyword arguments passed to parent class
    """
    
    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        super().__init__(message, **kwargs)


class ValidationException(SecurityException):
    """Raised when input validation fails.
    
    Indicates that provided input does not meet validation requirements
    (type mismatch, format error, etc.).
    """
    pass


class AuthorizationException(SecurityException):
    """Raised when operation is not authorized.
    
    Indicates that the user/agent lacks permissions to perform operation.
    """
    pass


class SandboxException(SecurityException):
    """Raised when Docker sandbox security is violated.
    
    Indicates an attempt to break sandbox isolation or bypass restrictions.
    """
    pass


class CommandExecutionException(SecurityException):
    """Raised when execution of a forbidden command is attempted.
    
    Indicates that a command violates sandbox security policy
    and execution was blocked.
    
    Args:
        command: The command that was blocked
        reason: Why the command is forbidden
        component: System component (default: 'supervisor')
        **kwargs: Additional arguments
    """
    
    def __init__(
        self,
        command: str,
        reason: str,
        component: str = "supervisor",
        **kwargs: Any
    ) -> None:
        message = f"Forbidden command blocked: {command} ({reason})"
        kwargs.setdefault("details", {})["command"] = command
        kwargs["details"]["reason"] = reason
        super().__init__(message, component=component, **kwargs)


class InjectionException(SecurityException):
    """Raised when SQL/Cypher/Command injection is detected.
    
    Indicates that potentially malicious input attempting injection
    attack was detected and blocked.
    
    Args:
        injection_type: Type of injection (SQL, Cypher, Command, etc.)
        target: The target that was attacked
        **kwargs: Additional arguments
    """
    
    def __init__(
        self,
        injection_type: str,
        target: str,
        **kwargs: Any
    ) -> None:
        message = f"{injection_type.upper()} injection detected in: {target}"
        kwargs.setdefault("details", {})["injection_type"] = injection_type
        kwargs["details"]["target"] = target
        super().__init__(message, **kwargs)


class RateLimitException(SecurityException):
    """Raised when rate limit is exceeded.
    
    Indicates that a resource has been accessed too many times within
    a time window, triggering rate limit protection.
    
    Args:
        resource: The resource being rate-limited
        limit: Maximum requests allowed
        window: Time window in seconds
        **kwargs: Additional arguments
    """
    
    def __init__(
        self,
        resource: str,
        limit: int,
        window: int,
        **kwargs: Any
    ) -> None:
        message = f"Rate limit exceeded: {limit} requests per {window}s for {resource}"
        kwargs.setdefault("details", {})["resource"] = resource
        kwargs["details"]["limit"] = limit
        kwargs["details"]["window"] = window
        super().__init__(message, **kwargs)


# ============================================================
# AGENT EXCEPTIONS
# ============================================================

class AgentException(ArtOfIAException):
    """Base exception for agent-related errors.
    
    Used for errors that occur during agent initialization, execution,
    or lifecycle management.
    
    Args:
        message: Error message
        agent_name: Name of the agent (default: 'unknown')
        **kwargs: Additional arguments
    """
    
    def __init__(self, message: str, agent_name: str = "unknown", **kwargs: Any) -> None:
        kwargs.setdefault("component", agent_name)
        severity: ErrorSeverity = kwargs.pop("severity", ErrorSeverity.ERROR)
        super().__init__(message, severity=severity, **kwargs)


class AgentInitializationException(AgentException):
    """Raised when agent fails to initialize.
    
    Indicates that agent setup or configuration failed.
    """
    pass


class AgentExecutionException(AgentException):
    """Raised when agent execution fails.
    
    Indicates that an error occurred during agent operation.
    """
    pass


class AgentTimeoutException(AgentException):
    """Raised when agent operation times out.
    
    Indicates that agent did not complete within time limit.
    
    Args:
        agent_name: Name of the agent
        operation: Operation that timed out
        timeout_seconds: Timeout duration in seconds
        **kwargs: Additional arguments
    """
    
    def __init__(
        self,
        agent_name: str,
        operation: str,
        timeout_seconds: float,
        **kwargs: Any
    ) -> None:
        message = f"Agent {agent_name} timeout on {operation} (>{timeout_seconds}s)"
        kwargs.setdefault("details", {})["timeout_seconds"] = timeout_seconds
        kwargs["details"]["agent_name"] = agent_name
        super().__init__(message, agent_name=agent_name, operation=operation, **kwargs)


class AgentDependencyException(AgentException):
    """Agent dependency not available"""
    
    def __init__(self, agent_name: str, missing_dependency: str, **kwargs: Any) -> None:
        message = f"Missing dependency for {agent_name}: {missing_dependency}"
        kwargs.setdefault("details", {})["missing_dependency"] = missing_dependency
        super().__init__(message, agent_name=agent_name, **kwargs)


# ============================================================
# DATABASE/STORAGE EXCEPTIONS
# ============================================================

class StorageException(ArtOfIAException):
    """Base for storage-related errors"""
    
    def __init__(self, message: str, **kwargs: Any) -> None:
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
        operation: str,
        resource_type: str,
        reason: str,
        **kwargs: Any
    ) -> None:
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
    
    def __init__(self, required_bytes: int, available_bytes: int, **kwargs: Any) -> None:
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
    
    def __init__(self, resource_type: str, limit: int, **kwargs: Any) -> None:
        message = f"Resource exhausted: {resource_type} (limit: {limit})"
        kwargs.setdefault("details", {})["resource_type"] = resource_type
        kwargs["details"]["limit"] = limit
        super().__init__(message, component="system", **kwargs)


# ============================================================
# CONFIGURATION EXCEPTIONS
# ============================================================

class ConfigurationException(ArtOfIAException):
    """Configuration error"""
    
    def __init__(self, message: str, config_key: str = "", **kwargs: Any) -> None:
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
    
    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("component", "orchestrator")
        super().__init__(message, **kwargs)


class StageFailureException(OrchestrationException):
    """A stage in the operation failed"""
    
    def __init__(
        self,
        stage_name: str,
        reason: str,
        stage_number: int = 0,
        **kwargs: Any
    ) -> None:
        message = f"Stage failure [{stage_name}]: {reason}"
        kwargs.setdefault("details", {})["stage_name"] = stage_name
        kwargs["details"]["stage_number"] = stage_number
        super().__init__(message, operation=stage_name, **kwargs)


class OperationCanceledException(OrchestrationException):
    """Operation was cancelled"""
    
    def __init__(self, operation_id: str, reason: str = "", **kwargs: Any) -> None:
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
        **kwargs: Any
    ) -> None:
        message = f"External service error: {service_name}"
        if status_code:
            message += f" (HTTP {status_code})"
        kwargs.setdefault("details", {})["service_name"] = service_name
        if status_code:
            kwargs["details"]["status_code"] = status_code
        super().__init__(message, **kwargs)


class LLMException(ExternalServiceException):
    """LLM provider error"""
    
    def __init__(self, reason: str, model: str = "", **kwargs: Any) -> None:
        kwargs.setdefault("details", {})["model"] = model
        super().__init__("llm_provider", **kwargs)
        self.message = f"LLM error ({model}): {reason}"


class WebServiceException(ExternalServiceException):
    """Target web service error"""
    
    def __init__(
        self,
        target_url: str,
        status_code: int,
        **kwargs: Any
    ) -> None:
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


def get_exception_class(exception_type: str) -> type[ArtOfIAException]:
    """Look up exception class by type string"""
    return EXCEPTION_REGISTRY.get(exception_type, ArtOfIAException)
