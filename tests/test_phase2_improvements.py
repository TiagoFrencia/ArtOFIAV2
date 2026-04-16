"""
Test Suite for PHASE 2: Error Handling & Logging Context

Tests para validar:
1. Exception hierarchy functionality
2. Rate limiting
3. Logging context propagation
4. Performance tracking
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch
from datetime import datetime


# ============================================================
# TEST 1: Exception Hierarchy
# ============================================================

class TestExceptionHierarchy:
    """Verifica que la jerarquía de excepciones funciona"""
    
    def test_exception_context_creation(self):
        """Verifica que ErrorContext se crea correctamente"""
        from src.core.exceptions import ErrorContext, ErrorSeverity
        
        context = ErrorContext(
            timestamp=datetime.now(),
            component="test_agent",
            operation="execute",
            severity=ErrorSeverity.ERROR,
            details={"reason": "test error"}
        )
        
        assert context.component == "test_agent"
        assert context.operation == "execute"
        assert context.severity == ErrorSeverity.ERROR
        
        # Debe ser serializable a dict
        context_dict = context.to_dict()
        assert "timestamp" in context_dict
        assert context_dict["component"] == "test_agent"
    
    def test_custom_exception_with_context(self):
        """Verifica que excepciones incluyen contexto"""
        from src.core.exceptions import CommandExecutionException
        
        exc = CommandExecutionException(
            command="rm -rf /",
            reason="Forbidden destructive command",
            component="supervisor"
        )
        
        assert "rm -rf /" in str(exc)
        assert exc.context.component == "supervisor"
        assert exc.context.details["command"] == "rm -rf /"
    
    def test_rate_limit_exception(self):
        """Verifica RateLimitException with details"""
        from src.core.exceptions import RateLimitException, ErrorSeverity
        
        exc = RateLimitException(
            resource="docker_commands",
            limit=50,
            window=60
        )
        
        assert exc.context.severity == ErrorSeverity.CRITICAL
        assert exc.context.details["limit"] == 50
        assert exc.context.details["window"] == 60
        
        exc_dict = exc.to_dict()
        assert exc_dict["error"] == "RateLimitException"
    
    def test_agent_timeout_exception(self):
        """Verifica AgentTimeoutException"""
        from src.core.exceptions import AgentTimeoutException
        
        exc = AgentTimeoutException(
            agent_name="recon_agent",
            operation="port_scan",
            timeout_seconds=300.0
        )
        
        assert "recon_agent" in str(exc)
        assert exc.context.component == "recon_agent"
        assert exc.context.details["timeout_seconds"] == 300.0
    
    def test_exception_registry(self):
        """Verifica que registry mapea tipos a excepciones"""
        from src.core.exceptions import get_exception_class, ValidationException
        
        exc_class = get_exception_class("validation")
        assert exc_class == ValidationException


# ============================================================
# TEST 2: Rate Limiting
# ============================================================

class TestRateLimiter:
    """Verifica que rate limiter funciona correctamente"""
    
    def test_rate_limiter_initialization(self):
        """Verifica que RateLimiter se inicializa"""
        from src.orchestrator.supervisor import RateLimiter
        
        limiter = RateLimiter()
        assert limiter is not None
        assert "agent" in limiter.limits
        assert "docker_command" in limiter.limits
    
    def test_rate_limit_allows_requests_within_limit(self):
        """Verifica que requests dentro del límite son permitidas"""
        from src.orchestrator.supervisor import RateLimiter
        
        limiter = RateLimiter()
        
        # Primer request debe ser permitido
        allowed, reason = limiter.check_rate_limit("test_agent", "agent")
        assert allowed is True
        assert reason == ""
        
        # Segundo también debe ser permitido (inicialmente hay muchos tokens)
        allowed, reason = limiter.check_rate_limit("test_agent", "agent")
        assert allowed is True
    
    def test_rate_limit_blocks_when_exceeded(self):
        """Verifica que rate limiter bloquea cuando se excede"""
        from src.orchestrator.supervisor import RateLimiter
        
        limiter = RateLimiter()
        
        # Consumir todos los tokens
        limit_config = limiter.limits["agent"]
        max_requests = limit_config["max_requests"]
        
        for i in range(max_requests):
            allowed, reason = limiter.check_rate_limit("test_agent", "agent")
            assert allowed is True, f"Should allow request {i}"
        
        # Siguiente request debe ser bloqueado
        allowed, reason = limiter.check_rate_limit("test_agent", "agent")
        assert allowed is False
        assert "Rate limit exceeded" in reason
    
    def test_rate_limit_different_resources(self):
        """Verifica que límites son por recurso"""
        from src.orchestrator.supervisor import RateLimiter
        
        limiter = RateLimiter()
        
        # Agent 1 consume sus tokens
        limit_config = limiter.limits["agent"]
        max_requests = limit_config["max_requests"]
        
        for i in range(max_requests):
            allowed, _ = limiter.check_rate_limit("agent1", "agent")
            assert allowed is True
        
        # Agent 2 debe tener sus propios tokens
        allowed, reason = limiter.check_rate_limit("agent2", "agent")
        assert allowed is True
        
        # Pero agent1 debe seguir bloqueado
        allowed, reason = limiter.check_rate_limit("agent1", "agent")
        assert allowed is False
    
    def test_rate_limit_reset(self):
        """Verifica que reset_bucket funciona"""
        from src.orchestrator.supervisor import RateLimiter
        
        limiter = RateLimiter()
        
        # Consumir tokens
        max_requests = limiter.limits["agent"]["max_requests"]
        for i in range(max_requests):
            limiter.check_rate_limit("test_agent", "agent")
        
        # Debe estar bloqueado
        allowed, _ = limiter.check_rate_limit("test_agent", "agent")
        assert allowed is False
        
        # Reset
        limiter.reset_bucket("test_agent", "agent")
        
        # Ahora debe permitir
        allowed, reason = limiter.check_rate_limit("test_agent", "agent")
        assert allowed is True


# ============================================================
# TEST 3: Logging Context
# ============================================================

class TestLoggingContext:
    """Verifica que logging context funciona"""
    
    @pytest.mark.asyncio
    async def test_log_context_creation(self):
        """Verifica que LogContext se puede crear"""
        from src.orchestrator.logging_context import LogContext, get_context
        
        async with LogContext(
            operation_id="test_op_123",
            target="http://example.com"
        ):
            context = get_context()
            assert context.operation_id == "test_op_123"
            assert context.target == "http://example.com"
    
    @pytest.mark.asyncio
    async def test_log_context_auto_generates_operation_id(self):
        """Verifica que operation_id se auto-genera si no se proporciona"""
        from src.orchestrator.logging_context import LogContext, get_context
        
        async with LogContext() as ctx:
            context = get_context()
            # operation_id debe existir
            assert context.operation_id != ""
    
    @pytest.mark.asyncio
    async def test_log_context_restores_previous(self):
        """Verifica que context se restaura después de salir"""
        from src.orchestrator.logging_context import (
            LogContext, set_context, get_context
        )
        
        # Set initial context
        set_context(operation_id="initial")
        
        async with LogContext(operation_id="inner"):
            inner_context = get_context()
            assert inner_context.operation_id == "inner"
        
        # Context debe ser restaurado
        restored_context = get_context()
        assert restored_context.operation_id == "initial"
    
    def test_context_filter_adds_fields(self):
        """Verifica que ContextFilter agrega campos a LogRecord"""
        from src.orchestrator.logging_context import (
            ContextFilter, set_context
        )
        
        filter_obj = ContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None
        )
        
        # Set context
        set_context(operation_id="op_123", agent="test_agent")
        
        # Apply filter
        result = filter_obj.filter(record)
        
        assert result is True
        assert record.operation_id == "op_123"
        assert record.agent == "test_agent"
    
    def test_performance_tracker(self):
        """Verifica PerformanceTracker registra métricas"""
        from src.orchestrator.logging_context import PerformanceTracker
        
        logger = logging.getLogger("test")
        tracker = PerformanceTracker("test_operation", logger)
        
        with tracker:
            # Simular trabajo
            pass
        
        # Debe haber registrado la duración
        assert tracker.start_time is not None
    
    def test_performance_tracker_records_metrics(self):
        """Verifica que PerformanceTracker puede grabar métricas"""
        from src.orchestrator.logging_context import PerformanceTracker
        
        logger = logging.getLogger("test")
        tracker = PerformanceTracker("test_op", logger)
        
        with tracker:
            tracker.record_metric("requests", 100)
            tracker.record_metric("errors", 5)
        
        assert tracker.metrics["requests"] == 100
        assert tracker.metrics["errors"] == 5


# ============================================================
# TEST 4: Integration Tests
# ============================================================

class TestPhase2Integration:
    """Tests de integración de PHASE 2"""
    
    @pytest.mark.asyncio
    async def test_supervisor_rate_limiting_integration(self):
        """Verifica que supervisor usa rate limiter"""
        from src.orchestrator.supervisor import SecurityValidator
        
        validator = SecurityValidator()
        
        # Debe tener rate_limiter
        assert hasattr(validator, "rate_limiter")
        assert validator.rate_limiter is not None
    
    def test_exception_hierarchy_covers_all_cases(self):
        """Verifica que exception hierarchy cubre casos comunes"""
        from src.core.exceptions import (
            ValidationException,
            AuthorizationException,
            SandboxException,
            CommandExecutionException,
            InjectionException,
            RateLimitException,
            AgentTimeoutException,
            ConnectionException,
            OutOfMemoryException,
        )
        
        # Crear algunas excepciones para verificar que funcionan
        exceptions = [
            ValidationException("test"),
            AuthorizationException("test"),
            SandboxException("test"),
            CommandExecutionException("cmd", "reason"),
            InjectionException("sql", "target"),
            RateLimitException("resource", 10, 60),
            AgentTimeoutException("agent", "op", 300),
            ConnectionException("test"),
            OutOfMemoryException(1000, 500),
        ]
        
        for exc in exceptions:
            # Debe ser convertible a dict
            exc_dict = exc.to_dict()
            assert "error" in exc_dict
            assert "message" in exc_dict
            assert "context" in exc_dict


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
