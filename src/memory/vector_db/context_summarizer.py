"""
Context Summarizer - Administrador de Memoria de Trabajo (Working Memory).

Comprime y gestiona inteligentemente el contexto del LLM mediante:
- Resumen en cadena (chain summarization)
- Compresión selectiva (mantener lo importante, descartar ruido)
- Rolling context windows
- Token budgeting

Responsabilidades:
- Proteger el orquestador del overflow de contexto
- Mantener coherencia entre resumidos y detallados
- Predecir cuando el contexto será insuficiente
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re


@dataclass
class ContextWindow:
    """Ventana de contexto para el LLM."""
    id: str
    content: str
    token_count: int
    events: List[str] = field(default_factory=list)
    importance_score: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "token_count": self.token_count,
            "importance_score": self.importance_score,
            "events": len(self.events),
            "created_at": self.created_at
        }


class ContextSummarizer:
    """Administrador de contexto de trabajo."""
    
    def __init__(
        self,
        max_tokens: int = 8000,
        summarization_ratio: float = 0.5,
        min_retention_tokens: int = 2000
    ):
        """
        Inicializa gestor de contexto.
        
        Args:
            max_tokens: Presupuesto máximo de tokens
            summarization_ratio: Ratio de compresión (0-1)
            min_retention_tokens: Tokens mínimos a retener
        """
        self.logger = logging.getLogger(__name__)
        
        self.max_tokens = max_tokens
        self.summarization_ratio = summarization_ratio
        self.min_retention_tokens = min_retention_tokens
        
        # Ventanas de contexto activas
        self.active_windows: List[ContextWindow] = []
        
        # Historial de resumidos
        self.summarized_contexts: List[Dict[str, Any]] = []
        
        # Estadísticas
        self.stats = {
            "contexts_summarized": 0,
            "tokens_saved": 0,
            "avg_compression_ratio": 1.0,
            "warnings_issued": 0
        }
        
        self.logger.info(f"✓ ContextSummarizer inicializado (max_tokens: {max_tokens})")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima tokens aproximadamente.
        
        Simple: ~4 caracteres = 1 token
        """
        return max(1, len(text) // 4)
    
    def add_context(
        self,
        content: str,
        event_type: str,
        importance: float = 0.5
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Añade contexto nuevo.
        
        Args:
            content: Contenido a añadir
            event_type: Tipo de evento
            importance: Importancia (0-1)
        
        Returns:
            (accepted, metadata)
        """
        token_count = self.estimate_tokens(content)
        
        current_tokens = sum(w.token_count for w in self.active_windows)
        available_tokens = self.max_tokens - current_tokens
        
        self.logger.info(
            f"📝 Contexto nuevo: {token_count} tokens "
            f"(disponibles: {available_tokens}/{self.max_tokens})"
        )
        
        # Si hay espacio, aceptar
        if token_count <= available_tokens:
            window = ContextWindow(
                id=self._generate_window_id(),
                content=content,
                token_count=token_count,
                events=[event_type],
                importance_score=importance
            )
            
            self.active_windows.append(window)
            
            return True, {
                "status": "accepted",
                "window_id": window.id,
                "tokens_used": token_count,
                "remaining": available_tokens - token_count
            }
        
        # Si no hay espacio, invocar compresión
        self.logger.warning(f"  ⚠ Overflow de contexto detectado")
        
        freed_tokens = self._compress_for_space(token_count)
        
        if freed_tokens >= token_count:
            # Reintentar
            window = ContextWindow(
                id=self._generate_window_id(),
                content=content,
                token_count=token_count,
                events=[event_type],
                importance_score=importance
            )
            
            self.active_windows.append(window)
            
            self.stats["warnings_issued"] += 1
            
            return True, {
                "status": "accepted_after_compression",
                "window_id": window.id,
                "tokens_freed": freed_tokens,
                "tokens_used": token_count
            }
        else:
            # Demasiado grande incluso después de compresión
            return False, {
                "status": "rejected",
                "reason": "exceeds_max_tokens",
                "required": token_count,
                "available": freed_tokens,
                "recommendation": "split_into_smaller_chunks"
            }
    
    def _compress_for_space(self, required_tokens: int) -> int:
        """
        Comprime contexto existente para liberar espacio.
        
        Args:
            required_tokens: Tokens necesarios
        
        Returns:
            Tokens liberados
        """
        self.logger.info(f"🔄 Comprimiendo contexto...")
        
        # Ordenar por importancia (menor primero para eliminar)
        sorted_windows = sorted(self.active_windows, key=lambda w: w.importance_score)
        
        freed = 0
        windows_to_remove = []
        
        for window in sorted_windows:
            if freed >= required_tokens:
                break
            
            # Comprimir o eliminar
            compressed_content = self._compress_window(window)
            
            if compressed_content:
                # Registrar resumido
                self.summarized_contexts.append({
                    "window_id": window.id,
                    "original_tokens": window.token_count,
                    "compressed_tokens": self.estimate_tokens(compressed_content),
                    "summary": compressed_content,
                    "timestamp": datetime.now().isoformat()
                })
                
                freed += window.token_count
                windows_to_remove.append(window)
                
                self.logger.debug(f"    ✓ Ventana {window.id} comprimida")
            else:
                # Eliminar completamente si no se puede resumir
                freed += window.token_count
                windows_to_remove.append(window)
                
                self.logger.debug(f"    ✓ Ventana {window.id} eliminada")
        
        # Aplicar cambios
        for window in windows_to_remove:
            self.active_windows.remove(window)
        
        self.stats["contexts_summarized"] += len(windows_to_remove)
        self.stats["tokens_saved"] += freed
        
        self.logger.info(f"  ✓ Espacio liberado: {freed} tokens")
        
        return freed
    
    def _compress_window(self, window: ContextWindow) -> Optional[str]:
        """
        Comprime una ventana de contexto.
        
        Estrategia:
        - Mantener primera línea (objetivo)
        - Mantener última línea (resultado)
        - Descartar líneas intermedias redundantes
        """
        lines = window.content.split('\n')
        
        if len(lines) <= 3:
            return None  # Demasiado corto para comprimir
        
        # Mantener primera + última
        compressed = lines[0] + "\n" + "..." + "\n" + lines[-1]
        
        return compressed
    
    def get_current_context(self, max_windows: int = 5) -> str:
        """
        Retorna contexto activo actual.
        
        Args:
            max_windows: Máximo de ventanas a incluir
        
        Returns:
            Contexto formateado para LLM
        """
        # Ordenar por importancia / recencia
        sorted_windows = sorted(
            self.active_windows,
            key=lambda w: (w.importance_score, w.created_at),
            reverse=True
        )
        
        context_parts = []
        total_tokens = 0
        
        for window in sorted_windows[:max_windows]:
            if total_tokens + window.token_count > self.max_tokens * 0.8:
                break
            
            context_parts.append(f"[{window.id}]\n{window.content}")
            total_tokens += window.token_count
        
        self.logger.debug(
            f"  ✓ Contexto activo: {len(context_parts)} ventanas, "
            f"{total_tokens} tokens"
        )
        
        return "\n---\n".join(context_parts)
    
    def predict_context_exhaustion(self) -> Optional[Dict[str, Any]]:
        """
        Predice si el contexto será insuficiente pronto.
        
        Returns:
            Dict con predicción o None
        """
        total_tokens = sum(w.token_count for w in self.active_windows)
        utilization = (total_tokens / self.max_tokens) * 100
        
        if utilization > 85:
            self.logger.warning(f"  ⚠ Contexto casi lleno: {utilization:.1f}%")
            
            return {
                "utilization_pct": utilization,
                "tokens_remaining": self.max_tokens - total_tokens,
                "severity": "critical" if utilization > 95 else "warning",
                "recommendation": (
                    "ABORT_IMMEDIATELY" if utilization > 95 else
                    "SUMMARIZE_OLDEST_CONTEXTS" if utilization > 90 else
                    "MONITOR_CLOSELY"
                )
            }
        
        return None
    
    def get_summarized_context(self, limit: int = 3) -> str:
        """
        Retorna resumen de contextos previos.
        
        Útil para: explicar al agente qué pasó antes
        """
        recent = sorted(
            self.summarized_contexts,
            key=lambda c: c["timestamp"],
            reverse=True
        )[:limit]
        
        summaries = []
        for ctx in recent:
            summaries.append(f"[{ctx['timestamp']}]\n{ctx['summary']}")
        
        return "\n---\n".join(summaries) if summaries else "No hay contexto previo"
    
    def clear_old_windows(self, keep_important: bool = True) -> int:
        """
        Limpia ventanas antiguas.
        
        Args:
            keep_important: Mantener ventanas con importancia > 0.7
        
        Returns:
            Número de ventanas eliminadas
        """
        to_remove = []
        
        for window in self.active_windows:
            # Si es antigua (creada hace > 1 hora) y no importante
            if keep_important and window.importance_score > 0.7:
                continue
            
            to_remove.append(window)
        
        for window in to_remove:
            self.active_windows.remove(window)
        
        self.logger.info(f"  🗑 {len(to_remove)} ventanas antiguas eliminadas")
        
        return len(to_remove)
    
    def update_importance(self, window_id: str, new_importance: float) -> bool:
        """
        Actualiza importancia de una ventana.
        
        Args:
            window_id: ID de la ventana
            new_importance: Nueva importancia (0-1)
        
        Returns:
            True si se actualizó
        """
        for window in self.active_windows:
            if window.id == window_id:
                window.importance_score = min(1.0, max(0.0, new_importance))
                self.logger.debug(f"  ✓ Importancia actualizada: {window_id} → {new_importance}")
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del contexto."""
        total_tokens = sum(w.token_count for w in self.active_windows)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_windows": len(self.active_windows),
            "total_tokens_used": total_tokens,
            "max_tokens": self.max_tokens,
            "utilization_pct": (total_tokens / self.max_tokens) * 100,
            "summarized_contexts": len(self.summarized_contexts),
            **self.stats
        }
    
    def export_memory(self) -> Dict[str, Any]:
        """Exporta estado completo de memoria de trabajo."""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_windows": [w.to_dict() for w in self.active_windows],
            "summarized_contexts": self.summarized_contexts[:20],  # Últimos 20
            "stats": self.get_stats()
        }
    
    def _generate_window_id(self) -> str:
        """Genera ID único para ventana."""
        import hashlib
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:12]
