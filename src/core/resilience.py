"""
Circuit Breaker & Resilience - Patrones de tolerancia a fallos.

Proporciona:
- Circuit breaker pattern (fail-fast)
- Retry with exponential backoff
- Fallback mechanisms
- Health check monitoring
"""

import logging
import asyncio
from typing import Callable, Any, Optional, Coroutine, Dict
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    half_open_max_calls: int = 3  # Calls allowed in half-open state
    success_threshold: int = 2  # Successes to close circuit


@dataclass
class CircuitBreakerMetrics:
    """Métricas del circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_change_time: Optional[datetime] = None


class CircuitBreaker:
    """Circuit Breaker - Patrón de tolerancia a fallos.
    
    Previene cascading failures detectando cuando un servicio está
    caído y fallando rápidamente (fail-fast).
    
    Estados:
    - CLOSED: Normal, todas las requests pasan
    - OPEN: Servicio caído, rechaza requests
    - HALF_OPEN: Probando si servicio se recuperó
    
    Ejemplo:
        breaker = CircuitBreaker("graphql_api", config)
        try:
            result = await breaker.call(async_fn, arg1, arg2)
        except CircuitBreakerOpen:
            # Service is down, use fallback
            result = get_cached_data()
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Inicializa circuit breaker.
        
        Args:
            name: Nombre del servicio/función
            config: Configuración (default: sensible defaults)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.metrics = CircuitBreakerMetrics(state_change_time=datetime.now())
        self.logger = logging.getLogger(__name__)
    
    async def call(
        self,
        fn: Callable[..., Coroutine],
        *args,
        **kwargs
    ) -> Any:
        """Ejecuta función a través de circuit breaker.
        
        Args:
            fn: Función async a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
            
        Returns:
            Resultado de fn
            
        Raises:
            CircuitBreakerOpen: Si circuit está abierto
            Exception: Si fn lanza excepción
        """
        if self.metrics.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.metrics.state = CircuitState.HALF_OPEN
                self.logger.info(f"⚠️  Circuit breaker {self.name} entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Last failure: {self.metrics.last_failure_time}"
                )
        
        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si suficiente tiempo pasó para intentar recovery.
        
        Returns:
            True si podemos pasar a HALF_OPEN
        """
        if not self.metrics.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.metrics.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _on_success(self) -> None:
        """Maneja success en la llamada."""
        self.metrics.last_success_time = datetime.now()
        
        if self.metrics.state == CircuitState.HALF_OPEN:
            self.metrics.successes += 1
            
            if self.metrics.successes >= self.config.success_threshold:
                self.metrics.state = CircuitState.CLOSED
                self.metrics.failures = 0
                self.metrics.successes = 0
                self.metrics.state_change_time = datetime.now()
                self.logger.info(f"✓ Circuit breaker {self.name} CLOSED (recovered)")
        
        elif self.metrics.state == CircuitState.CLOSED:
            # Reset failure counter on success
            if self.metrics.failures > 0:
                self.metrics.failures -= 1
    
    def _on_failure(self) -> None:
        """Maneja failure en la llamada."""
        self.metrics.failures += 1
        self.metrics.last_failure_time = datetime.now()
        
        if self.metrics.state == CircuitState.HALF_OPEN:
            # One failure while testing = back to OPEN
            self.metrics.state = CircuitState.OPEN
            self.metrics.state_change_time = datetime.now()
            self.logger.warning(f"✗ Circuit breaker {self.name} re-opened (recovery failed)")
            return
        
        if self.metrics.failures >= self.config.failure_threshold:
            self.metrics.state = CircuitState.OPEN
            self.metrics.state_change_time = datetime.now()
            self.logger.error(
                f"✗ Circuit breaker {self.name} OPEN "
                f"({self.metrics.failures} failures)"
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado del circuit breaker."""
        return {
            "name": self.name,
            "state": self.metrics.state.value,
            "failures": self.metrics.failures,
            "successes": self.metrics.successes,
            "last_failure": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            "state_since": self.metrics.state_change_time.isoformat() if self.metrics.state_change_time else None
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Alias para get_status() para compatibilidad."""
        return self.get_status()


class CircuitBreakerOpen(Exception):
    """Excepción lanzada cuando circuit breaker está abierto."""
    pass


class RetryPolicy:
    """Política de reintentos con exponential backoff.
    
    Estrategia:
    - Primer reintento: 1 segundo
    - Segundo: 2 segundos
    - Tercero: 4 segundos
    - Etc. (exponential)
    
    Con jitter para evitar thundering herd.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Inicializa política de reintentos.
        
        Args:
            max_attempts: Máximo número de intentos
            base_delay: Delay inicial (seconds)
            max_delay: Delay máximo (seconds)
            exponential_base: Base para backoff exponencial
            jitter: Agregar randomness para evitar thundering herd
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.logger = logging.getLogger(__name__)
    
    async def execute_with_retry(
        self,
        fn: Callable[..., Coroutine],
        *args,
        **kwargs
    ) -> Any:
        """Ejecuta función con reintentos.
        
        Args:
            fn: Función async a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
            
        Returns:
            Resultado de fn
            
        Raises:
            Exception: Si todos los intentos fallan
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_attempts:
                    delay = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"Attempt {attempt}/{self.max_attempts} failed for {fn.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
        
        # All attempts failed
        raise last_exception or Exception("All retry attempts failed")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calcula delay para un attempt.
        
        Args:
            attempt: Número de attempt (1-based)
            
        Returns:
            Delay en seconds
        """
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        # Add jitter (±10%)
        if self.jitter:
            import random
            jitter_factor = random.uniform(0.9, 1.1)
            delay = delay * jitter_factor
        
        return delay


class ResilientClient:
    """Cliente resiliente con circuit breaker + retry.
    
    Combina:
    - CircuitBreaker (fail-fast cuando servicio está caído)
    - RetryPolicy (reintentos con exponential backoff)
    - Fallback (valor por defecto si todo falla)
    """
    
    def __init__(
        self,
        name: str,
        breaker_config: Optional[CircuitBreakerConfig] = None,
        retry_config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa cliente resiliente.
        
        Args:
            name: Nombre del servicio
            breaker_config: Config del circuit breaker
            retry_config: Config de reintentos
        """
        self.name = name
        self.circuit_breaker = CircuitBreaker(name, breaker_config)
        self.retry_policy = RetryPolicy(**(retry_config or {}))
        self.fallback_fn: Optional[Callable] = None
        self.logger = logging.getLogger(__name__)
    
    def set_fallback(self, fn: Callable) -> None:
        """Registra función fallback.
        
        Args:
            fn: Función a llamar si todo falla
        """
        self.fallback_fn = fn
    
    async def execute(
        self,
        fn: Callable[..., Coroutine],
        *args,
        **kwargs
    ) -> Any:
        """Ejecuta función con circuit breaker + retry + fallback.
        
        Args:
            fn: Función async a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
            
        Returns:
            Resultado de fn o fallback
        """
        try:
            # Circuit breaker + retry
            return await self.circuit_breaker.call(
                self.retry_policy.execute_with_retry,
                fn,
                *args,
                **kwargs
            )
        except CircuitBreakerOpen as e:
            self.logger.error(f"Circuit breaker open for {self.name}: {e}")
            
            if self.fallback_fn:
                return self.fallback_fn(*args, **kwargs)
            raise
        
        except Exception as e:
            self.logger.error(f"Request failed for {self.name}: {e}")
            
            if self.fallback_fn:
                return self.fallback_fn(*args, **kwargs)
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna estado de salud del cliente."""
        return self.circuit_breaker.get_status()
