"""
Distributed Logging Context - For tracing operations across agents

Provides:
- Request ID propagation (for end-to-end tracing)
- Operation context (target, stage, agent)
- Performance metrics (latency, memory usage)
- Error context (what failed and why)

Usage:
    from src.orchestrator.logging_context import LogContext
    
    async with LogContext(operation_id="op_123", target="http://example.com"):
        # All logs in this block will include operation_id and target
        logger.info("Starting reconnaissance")
"""

import logging
import contextvars
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


# Context variables for distributed tracing
_operation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    'operation_id', default=''
)
_target: contextvars.ContextVar[str] = contextvars.ContextVar(
    'target', default=''
)
_agent: contextvars.ContextVar[str] = contextvars.ContextVar(
    'agent', default=''
)
_stage: contextvars.ContextVar[str] = contextvars.ContextVar(
    'stage', default=''
)
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    'user_id', default=''
)
_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    'request_id', default=''
)


@dataclass
class LogContextData:
    """Context data for a request/operation"""
    operation_id: str
    target: str = ""
    agent: str = ""
    stage: str = ""
    user_id: str = ""
    request_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return asdict(self)


class ContextFilter(logging.Filter):
    """
    Logging filter that injects context variables into every log record.
    
    This allows logging without explicitly passing context everywhere.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context variables to log record"""
        record.operation_id = _operation_id.get()
        record.target = _target.get()
        record.agent = _agent.get()
        record.stage = _stage.get()
        record.user_id = _user_id.get()
        record.request_id = _request_id.get()
        record.trace_id = _get_trace_id()
        return True


def _get_trace_id() -> str:
    """Get or generate trace ID"""
    request_id = _request_id.get()
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
        _request_id.set(request_id)
    return request_id


def get_context() -> LogContextData:
    """Get current logging context"""
    return LogContextData(
        operation_id=_operation_id.get(),
        target=_target.get(),
        agent=_agent.get(),
        stage=_stage.get(),
        user_id=_user_id.get(),
        request_id=_request_id.get(),
    )


def set_context(
    operation_id: str = "",
    target: str = "",
    agent: str = "",
    stage: str = "",
    user_id: str = "",
    request_id: str = "",
) -> None:
    """Set logging context variables"""
    if operation_id:
        _operation_id.set(operation_id)
    if target:
        _target.set(target)
    if agent:
        _agent.set(agent)
    if stage:
        _stage.set(stage)
    if user_id:
        _user_id.set(user_id)
    if request_id:
        _request_id.set(request_id)


def clear_context() -> None:
    """Clear all context variables"""
    _operation_id.set("")
    _target.set("")
    _agent.set("")
    _stage.set("")
    _user_id.set("")
    _request_id.set("")


@asynccontextmanager
async def LogContext(
    operation_id: Optional[str] = None,
    target: str = "",
    agent: str = "",
    stage: str = "",
    user_id: str = "",
):
    """
    Context manager for distributed logging.
    
    All logs within this context will include operation_id, target, agent, etc.
    
    Example:
        async with LogContext(operation_id="op_123", target="http://example.com"):
            logger.info("Starting attack")  # Will include operation_id and target
    
    Args:
        operation_id: Unique identifier for the operation (auto-generated if None)
        target: Target infrastructure/URL
        agent: Agent performing the action
        stage: Current stage (reconnaissance, exploitation, etc.)
        user_id: User who initiated the operation
    """
    # Generate operation_id if not provided
    if operation_id is None:
        operation_id = str(uuid.uuid4())
    
    # Save previous context
    prev_context = get_context()
    
    # Set new context
    set_context(
        operation_id=operation_id,
        target=target,
        agent=agent,
        stage=stage,
        user_id=user_id,
    )
    
    try:
        yield LogContextData(
            operation_id=operation_id,
            target=target,
            agent=agent,
            stage=stage,
            user_id=user_id,
        )
    finally:
        # Restore previous context
        set_context(
            operation_id=prev_context.operation_id,
            target=prev_context.target,
            agent=prev_context.agent,
            stage=prev_context.stage,
            user_id=prev_context.user_id,
        )


@asynccontextmanager
async def StageContext(stage_name: str):
    """
    Context manager for a specific stage within an operation.
    
    Example:
        async with StageContext("reconnaissance"):
            # stage will be automatically added to logs
            logger.info("Running recon")
    """
    prev_stage = _stage.get()
    _stage.set(stage_name)
    
    try:
        yield stage_name
    finally:
        _stage.set(prev_stage)


@asynccontextmanager
async def AgentContext(agent_name: str):
    """Context manager for agent execution context"""
    prev_agent = _agent.get()
    _agent.set(agent_name)
    
    try:
        yield agent_name
    finally:
        _agent.set(prev_agent)


class PerformanceTracker:
    """Track performance metrics within a context"""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        context = get_context()
        
        if exc_type:
            self.logger.error(
                f"Operation failed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_seconds": duration,
                    "error": str(exc_type),
                    **context.to_dict()
                }
            )
        else:
            self.logger.info(
                f"Operation completed: {self.operation}",
                extra={
                    "operation": self.operation,
                    "duration_seconds": duration,
                    **context.to_dict()
                }
            )
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric"""
        self.metrics[name] = value
        current_duration = time.time() - self.start_time
        self.logger.debug(
            f"Metric: {name}={value}",
            extra={
                "metric_name": name,
                "metric_value": value,
                "operation": self.operation,
                **get_context().to_dict()
            }
        )


def setup_logging_context(logger: logging.Logger) -> None:
    """
    Setup a logger to use distributed logging context.
    
    This adds the ContextFilter to the logger and creates a formatter
    that includes context variables.
    
    Example:
        logger = logging.getLogger("my_app")
        setup_logging_context(logger)
        # Now all logs will include context info
    """
    # Add context filter
    context_filter = ContextFilter()
    logger.addFilter(context_filter)
    
    # Update formatter to include context fields
    for handler in logger.handlers:
        formatter = handler.formatter or logging.Formatter()
        
        # Add context to format
        new_format = (
            "[%(asctime)s] %(levelname)s "
            "[op:%(operation_id)s] [req:%(request_id)s] [agent:%(agent)s] "
            "%(name)s: %(message)s"
        )
        
        new_formatter = logging.Formatter(new_format)
        handler.setFormatter(new_formatter)


# ============================================================
# EXAMPLES AND USAGE
# ============================================================

def example_usage():
    """Example of how to use distributed logging context"""
    logger = logging.getLogger("example")
    setup_logging_context(logger)
    
    # Usage in async context
    async def run_attack():
        async with LogContext(
            operation_id="attack_2026_001",
            target="http://vulnerable-app.local",
            user_id="operator_1"
        ):
            logger.info("Starting red team operation")
            
            async with StageContext("reconnaissance"):
                logger.info("Gathering information")
                
                async with AgentContext("recon_agent"):
                    with PerformanceTracker("port_scan"):
                        logger.info("Scanning target ports")
                        # Actual scanning...
                        logger.info("Port scan completed")
            
            async with StageContext("exploitation"):
                async with AgentContext("exploit_agent"):
                    logger.info("Attempting exploitation")
    
    # Logs will include context like:
    # [2026-04-16 10:30:45] INFO [op:attack_2026_001] [req:a1b2c3d4] 
    #   [agent:recon_agent] example: Port scan completed
