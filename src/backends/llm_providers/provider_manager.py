"""
Provider Manager - Enrutador de Modelos de IA
==============================================

Gestiona conexiones a diferentes proveedores de modelos de lenguaje
(OpenAI, Anthropic, Ollama local, etc) con fallback automático.

Estrategia:
1. Intenta GPT-4 (más inteligente pero caro)
2. Si rechaza por política → fallback a Claude
3. Si Claude rechaza → fallback a Ollama (local, sin censura)
4. Registra cada fallida para auditoría
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Tipos de modelos soportados"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    OLLAMA_LOCAL = "ollama_local"
    GEMINI = "gemini"
    AWS_BEDROCK = "bedrock"


class ProviderStatus(str, Enum):
    """Estado de proveedor"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RATE_LIMITED = "rate_limited"


@dataclass
class ProviderConfig:
    """Configuración de proveedor"""
    model_type: ModelType
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    timeout_seconds: int = 60
    max_retries: int = 3
    cost_per_1k_tokens: float = 0.0


@dataclass
class ProviderMetrics:
    """Métricas de rendimiento del proveedor"""
    model_type: ModelType
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Rechazadas por política
    average_latency_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    last_error: Optional[str] = None
    last_check: Optional[float] = None


class ProviderManager:
    """
    Gestor central de proveedores de IA.
    
    Orquestra múltiples modelos con:
    - Fallback automático
    - Load balancing
    - Cost optimization
    - Censorship detection
    """
    
    def __init__(self):
        self.providers: Dict[ModelType, Any] = {}
        self.fallback_chain = [
            ModelType.OPENAI_GPT4,
            ModelType.ANTHROPIC_CLAUDE,
            ModelType.GEMINI,
            ModelType.OLLAMA_LOCAL,  # Local fallback sin censura
        ]
        self.metrics: Dict[ModelType, ProviderMetrics] = {}
        self.request_history = []
        self.preference_cache = {}
    
    async def initialize(self, configs: Dict[ModelType, ProviderConfig]) -> bool:
        """
        Inicializar proveedores.
        
        Valida conexiones a todos los backends.
        """
        
        for model_type, config in configs.items():
            try:
                # Importar client específico
                if model_type == ModelType.OPENAI_GPT4:
                    from .openai_client import OpenAIClient
                    client = OpenAIClient(config)
                elif model_type == ModelType.ANTHROPIC_CLAUDE:
                    from .anthropic_client import AnthropicClient
                    client = AnthropicClient(config)
                elif model_type == ModelType.OLLAMA_LOCAL:
                    from .ollama_client import OllamaClient
                    client = OllamaClient(config)
                else:
                    logger.warning(f"Unknown model type: {model_type}")
                    continue
                
                # Test connection
                if await client.health_check():
                    self.providers[model_type] = client
                    self.metrics[model_type] = ProviderMetrics(model_type=model_type)
                    logger.info(f"Provider initialized: {model_type}")
                else:
                    logger.warning(f"Provider health check failed: {model_type}")
            
            except Exception as e:
                logger.error(f"Failed to initialize {model_type}: {e}")
        
        return len(self.providers) > 0
    
    async def invoke(self, prompt: str, model_preference: Optional[ModelType] = None,
                    temperature: float = 0.7, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Invocar modelo con fallback automático.
        
        Estrategia:
        1. Si preference específico → try it
        2. Si falla → fallback chain
        3. Si todos fallan → retornar error
        """
        
        # Determinar orden de intentos
        if model_preference and model_preference in self.providers:
            attempt_order = [model_preference] + [
                m for m in self.fallback_chain if m != model_preference
            ]
        else:
            attempt_order = self.fallback_chain
        
        # Intentar en orden
        for model_type in attempt_order:
            if model_type not in self.providers:
                continue
            
            try:
                client = self.providers[model_type]
                
                # Invocar con timeout
                start_time = time.time()
                response = await asyncio.wait_for(
                    client.generate(prompt, temperature, max_tokens),
                    timeout=60
                )
                latency_ms = (time.time() - start_time) * 1000
                
                # Actualizar métricas
                await self._update_metrics(model_type, success=True, latency_ms=latency_ms)
                
                # Registrar en historial
                await self._log_request(prompt, model_type, "success", response)
                
                logger.info(f"Invoked {model_type} successfully ({latency_ms:.0f}ms)")
                
                return {
                    "status": "success",
                    "model": model_type.value,
                    "response": response,
                    "latency_ms": latency_ms,
                }
            
            except Exception as e:
                error_msg = str(e)
                
                # Detectar si es rechazada por censura
                is_censored = await self._detect_censorship(error_msg)
                
                # Actualizar métricas
                if is_censored:
                    await self._update_metrics(model_type, rejected=True)
                    logger.warning(f"{model_type} rejected due to content policy")
                else:
                    await self._update_metrics(model_type, failed=True, error=error_msg)
                    logger.warning(f"{model_type} failed: {error_msg}")
                
                # Registrar fallida
                await self._log_request(prompt, model_type, "failed", error_msg)
                
                # Intentar siguiente
                continue
        
        # Todos fallaron
        logger.error("All providers exhausted")
        return {
            "status": "error",
            "error": "All providers failed or rejected",
        }
    
    async def _update_metrics(self, model_type: ModelType, success: bool = False,
                             failed: bool = False, rejected: bool = False,
                             latency_ms: float = 0, error: Optional[str] = None) -> None:
        """Actualizar métricas de proveedor"""
        
        metrics = self.metrics[model_type]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.average_latency_ms = (
                (metrics.average_latency_ms * (metrics.total_requests - 1) + latency_ms) /
                metrics.total_requests
            )
        elif failed:
            metrics.failed_requests += 1
            metrics.last_error = error
        elif rejected:
            metrics.rejected_requests += 1
            metrics.last_error = "Content rejected by policy"
        
        metrics.last_check = time.time()
    
    async def _detect_censorship(self, error_msg: str) -> bool:
        """Detectar si error es debido a censura de contenido"""
        
        censorship_keywords = [
            "content policy",
            "harmful",
            "unsafe",
            "inappropriate",
            "not allowed",
            "violates",
            "cannot generate",
        ]
        
        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in censorship_keywords)
    
    async def _log_request(self, prompt: str, model_type: ModelType, status: str,
                          result: str) -> None:
        """Registrar request en historial"""
        
        log_entry = {
            "timestamp": time.time(),
            "model": model_type.value,
            "status": status,
            "prompt_length": len(prompt),
            "result_length": len(result) if isinstance(result, str) else 0,
        }
        
        self.request_history.append(log_entry)
    
    def get_provider_status(self) -> Dict[ModelType, Dict[str, Any]]:
        """Retornar estado de todos los proveedores"""
        
        status = {}
        for model_type, metrics in self.metrics.items():
            success_rate = (
                metrics.successful_requests / max(1, metrics.total_requests)
                if metrics.total_requests > 0 else 0
            )
            
            if success_rate > 0.9:
                health = ProviderStatus.HEALTHY
            elif success_rate > 0.5:
                health = ProviderStatus.DEGRADED
            elif metrics.rejected_requests > metrics.failed_requests:
                health = ProviderStatus.RATE_LIMITED
            else:
                health = ProviderStatus.DOWN
            
            status[model_type] = {
                "status": health.value,
                "total_requests": metrics.total_requests,
                "success_rate": success_rate,
                "rejected_requests": metrics.rejected_requests,
                "average_latency_ms": metrics.average_latency_ms,
                "total_cost": metrics.total_cost,
            }
        
        return status
