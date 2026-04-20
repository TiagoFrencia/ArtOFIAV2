"""
Fallback Engine - Motor de Resiliencia
======================================

Si un proveedor rechaza un prompt por politica de seguridad,
este motor automáticamente lo intenta:
1. Con otro proveedor comercial (Anthropic, Gemini)
2. Con Ollama local (sin censura)

El objetivo es que el ataque nunca se bloquee por políticas
de contenido de IA. Siempre hay un fallback.

IMPORTANTE: Esto es FOR RESEARCH PURPOSES ONLY.
El acceso a modelos locales sin censura debe estar bajo
supervisión estricta y con propósitos defensivos.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING, Union, cast
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from . import ProviderManager

from .provider_manager import ModelType

logger = logging.getLogger(__name__)


class FallbackStrategy(str, Enum):
    """Estrategia de fallback"""
    CASCADE = "cascade"  # Intenta secuencialmente hasta que funciona
    LOAD_BALANCE = "load_balance"  # Distribuye entre múltiples
    LOCAL_ONLY = "local_only"  # Solo modelos locales (máxima privacidad)


class FallbackEngine:
    """
    Motor que maneja automaticamente fallbacks cuando
    un modelo rechaza o falla un request.
    """
    
    def __init__(self, provider_manager: "ProviderManager") -> None:
        self.provider_manager = provider_manager
        self.strategy = FallbackStrategy.CASCADE
        self.rejection_count = 0
        self.total_fallbacks = 0
        self.fallback_history: list[Dict[str, Any]] = []
    
    async def handle_rejected_request(self, original_prompt: str,
                                     rejected_by_model: str) -> Dict[str, Any]:
        """
        Manejar request rechazado por un modelo.
        
        Intenta alternativas automáticamente.
        """
        
        self.rejection_count += 1
        self.total_fallbacks += 1
        
        logger.warning(
            f"Request rejected by {rejected_by_model}. "
            f"Attempting fallback (count: {self.total_fallbacks})"
        )
        
        # Registrar en historial
        self.fallback_history.append({
            "timestamp": __import__('time').time(),
            "original_model": rejected_by_model,
            "reason": "content_rejected",
            "strategy": self.strategy.value,
        })
        
        # Estrategia de fallback
        if self.strategy == FallbackStrategy.CASCADE:
            return await self._fallback_cascade(original_prompt, rejected_by_model)
        elif self.strategy == FallbackStrategy.LOAD_BALANCE:
            return await self._fallback_load_balance(original_prompt)
        elif self.strategy == FallbackStrategy.LOCAL_ONLY:
            return await self._fallback_local_only(original_prompt)
        else:
            return {"status": "error", "error": "Unknown fallback strategy"}
    
    async def _fallback_cascade(self, prompt: str, rejected_model: str) -> Dict[str, Any]:
        """
        Cascada de fallbacks.
        
        Intenta: Anthropic → Gemini → Ollama (local)
        """
        
        fallback_chain = [
            ModelType.ANTHROPIC_CLAUDE,
            ModelType.GEMINI,
            ModelType.OLLAMA_LOCAL
        ]
        
        # Remover el modelo que rechazó (convert string to ModelType if needed)
        try:
            rejected_model_type = ModelType(rejected_model) if isinstance(rejected_model, str) else rejected_model
            if rejected_model_type in fallback_chain:
                fallback_chain.remove(rejected_model_type)
        except (ValueError, AttributeError):
            pass
        
        for fallback_model in fallback_chain:
            logger.info(f"Attempting fallback to {fallback_model}")
            
            try:
                result = await self.provider_manager.invoke(
                    prompt,
                    model_preference=fallback_model,
                    max_tokens=2000,
                )
                
                if result["status"] == "success":
                    return result
            
            except Exception as e:
                logger.warning(f"Fallback to {fallback_model} failed: {e}")
                continue
        
        return {"status": "error", "error": "All fallback models exhausted"}
    
    async def _fallback_load_balance(self, prompt: str) -> Dict[str, Any]:
        """
        Balancear carga entre múltiples modelos disponibles.
        """
        
        # Simple round-robin
        providers = list(self.provider_manager.providers.keys())
        if not providers:
            return {"status": "error", "error": "No providers available"}
        
        # Seleccionar proveedor con menos carga
        best_provider = min(
            providers,
            key=lambda p: self.provider_manager.metrics[p].total_requests
        )
        
        logger.info(f"Load balancing to {best_provider}")
        return await self.provider_manager.invoke(prompt, model_preference=best_provider)
    
    async def _fallback_local_only(self, prompt: str) -> Dict[str, Any]:
        """
        Usar solo modelos locales (Ollama).
        
        Máxima privacidad, sin data leakage a proveedores comerciales.
        """
        
        logger.info("Fallback to local-only mode (Ollama)")
        
        try:
            result = await self.provider_manager.invoke(
                prompt,
                model_preference=ModelType.OLLAMA_LOCAL,
                max_tokens=2000,
            )
            return result
        except Exception as e:
            return {"status": "error", "error": f"Local fallback failed: {e}"}
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de fallbacks"""
        
        return {
            "total_fallbacks": self.total_fallbacks,
            "rejection_count": self.rejection_count,
            "history": self.fallback_history[-20:],  # Last 20
            "strategy": self.strategy.value,
        }
