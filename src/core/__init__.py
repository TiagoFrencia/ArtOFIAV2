"""
ArtOfIA Core Module

Provides core functionality:
- Exception hierarchy
- Error handling
- Logging and tracing
"""

from .exceptions import (
    ArtOfIAException,
    SecurityException,
    ValidationException,
    AuthorizationException,
    SandboxException,
    CommandExecutionException,
    InjectionException,
    RateLimitException,
    AgentException,
    AgentInitializationException,
    AgentExecutionException,
    AgentTimeoutException,
    StorageException,
    ConnectionException,
    QueryException,
    PersistenceException,
    ErrorSeverity,
    ErrorContext,
    EXCEPTION_REGISTRY,
)

__all__ = [
    "ArtOfIAException",
    "SecurityException",
    "ValidationException",
    "AuthorizationException",
    "SandboxException",
    "CommandExecutionException",
    "InjectionException",
    "RateLimitException",
    "AgentException",
    "AgentInitializationException",
    "AgentExecutionException",
    "AgentTimeoutException",
    "StorageException",
    "ConnectionException",
    "QueryException",
    "PersistenceException",
    "ErrorSeverity",
    "ErrorContext",
    "EXCEPTION_REGISTRY",
]
