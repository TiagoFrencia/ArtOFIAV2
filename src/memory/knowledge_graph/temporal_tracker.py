"""
Temporal Tracker - Consciencia Temporal del Grafo de Conocimiento.

Mantiene registro de cuándo ocurrieron eventos, cuándo las tácticas dejaron de funcionar,
y cuándo se activaron defensas. Permite al agente entender cambios dinámicos en el objetivo.

Responsabilidades:
- Registrar timestamps de todos los eventos
- Detectar degradación de tácticas (success_rate % cayó a timestamp X)
- Identificar activación de defensas (WAF activado en timestamp Y)
- Predicción temporal (¿en cuánto tiempo se activa rate limiting?)
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics


class EventType(Enum):
    """Tipos de eventos temporales."""
    TACTIC_EXECUTED = "tactic_executed"
    TACTIC_SUCCESS = "tactic_success"
    TACTIC_FAILURE = "tactic_failure"
    DEFENSE_ACTIVATED = "defense_activated"
    DEFENSE_DEACTIVATED = "defense_deactivated"
    PAYLOAD_DETECTED = "payload_detected"
    RATE_LIMIT_HIT = "rate_limit_hit"
    WAF_BLOCK = "waf_block"
    CONNECTION_TIMEOUT = "connection_timeout"
    ANOMALY_DETECTED = "anomaly_detected"
    PATTERN_CHANGE = "pattern_change"


@dataclass
class TemporalEvent:
    """Representa un evento temporal."""
    event_type: EventType
    timestamp: datetime
    node_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "node_id": self.node_id,
            "properties": self.properties,
            "confidence": self.confidence
        }


class TemporalTracker:
    """Rastreador temporal del grafo."""
    
    def __init__(self, retention_hours: int = 24):
        """
        Inicializa tracker temporal.
        
        Args:
            retention_hours: Cuántas horas mantener eventos en memoria
        """
        self.logger = logging.getLogger(__name__)
        
        self.retention_hours = retention_hours
        
        # Timeline de eventos
        self.events: List[TemporalEvent] = []
        
        # Estadísticas por táctica
        self.tactic_stats: Dict[str, Dict[str, Any]] = {}
        
        # Estado actual de defensas
        self.active_defenses: Dict[str, Dict[str, Any]] = {}
        
        # Predicciones temporales
        self.predictions: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("✓ TemporalTracker inicializado")
    
    def record_event(
        self,
        event_type: EventType,
        node_id: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        confidence: float = 1.0
    ) -> TemporalEvent:
        """
        Registra un evento temporal.
        
        Args:
            event_type: Tipo de evento
            node_id: ID del nodo asociado
            properties: Propiedades adicionales del evento
            timestamp: Timestamp del evento (default: ahora)
            confidence: Confianza del evento (0-1)
        
        Returns:
            TemporalEvent registrado
        """
        timestamp = timestamp or datetime.now()
        
        event = TemporalEvent(
            event_type=event_type,
            timestamp=timestamp,
            node_id=node_id,
            properties=properties or {},
            confidence=confidence
        )
        
        self.events.append(event)
        
        # Limpiar eventos antiguos
        self._cleanup_old_events()
        
        # Actualizar estadísticas
        self._update_stats(event)
        
        # Detectar cambios de patrón
        self._detect_pattern_changes()
        
        self.logger.debug(f"  ✓ Evento registrado: {event_type.value}")
        
        return event
    
    def _cleanup_old_events(self) -> None:
        """Elimina eventos más antiguos que retention_hours."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        initial_count = len(self.events)
        self.events = [e for e in self.events if e.timestamp > cutoff_time]
        
        if len(self.events) < initial_count:
            removed = initial_count - len(self.events)
            self.logger.debug(f"  🗑 {removed} eventos antiguos eliminados")
    
    def _update_stats(self, event: TemporalEvent) -> None:
        """Actualiza estadísticas según evento."""
        if event.event_type == EventType.TACTIC_EXECUTED:
            tactic_id = event.node_id
            if tactic_id not in self.tactic_stats:
                self.tactic_stats[tactic_id] = {
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "success_rate": 0.0,
                    "first_use": event.timestamp.isoformat(),
                    "last_use": event.timestamp.isoformat(),
                    "avg_intervals": []
                }
            
            stats = self.tactic_stats[tactic_id]
            stats["executions"] += 1
            stats["last_use"] = event.timestamp.isoformat()
        
        elif event.event_type == EventType.TACTIC_SUCCESS:
            tactic_id = event.node_id
            if tactic_id in self.tactic_stats:
                stats = self.tactic_stats[tactic_id]
                stats["successes"] += 1
                stats["success_rate"] = stats["successes"] / max(1, stats["executions"])
        
        elif event.event_type == EventType.TACTIC_FAILURE:
            tactic_id = event.node_id
            if tactic_id in self.tactic_stats:
                stats = self.tactic_stats[tactic_id]
                stats["failures"] += 1
                stats["success_rate"] = stats["successes"] / max(1, stats["executions"])
        
        elif event.event_type == EventType.DEFENSE_ACTIVATED:
            defense_id = event.node_id
            self.active_defenses[defense_id] = {
                "activated_at": event.timestamp.isoformat(),
                "activated_by": event.properties.get("triggered_by"),
                "confidence": event.confidence,
                "status": "active"
            }
            self.logger.warning(f"  ⚠ Defensa activada: {defense_id}")
        
        elif event.event_type == EventType.DEFENSE_DEACTIVATED:
            defense_id = event.node_id
            if defense_id in self.active_defenses:
                self.active_defenses[defense_id]["status"] = "inactive"
                self.active_defenses[defense_id]["deactivated_at"] = event.timestamp.isoformat()
    
    def _detect_pattern_changes(self) -> None:
        """Detecta cambios en patrones de éxito/fallo."""
        # Para cada táctica, analizar últimas 10 ejecuciones
        for tactic_id, stats in self.tactic_stats.items():
            recent_events = [
                e for e in self.events
                if e.node_id == tactic_id and
                e.event_type in [EventType.TACTIC_SUCCESS, EventType.TACTIC_FAILURE]
            ][-10:]
            
            if len(recent_events) >= 5:
                recent_success_rate = sum(
                    1 for e in recent_events
                    if e.event_type == EventType.TACTIC_SUCCESS
                ) / len(recent_events)
                
                historical_rate = stats.get("success_rate", 0.5)
                
                # Si cambio > 30%, es una degradación
                if abs(recent_success_rate - historical_rate) > 0.3:
                    self.logger.warning(
                        f"  ⚠ Degradación detectada en {tactic_id}: "
                        f"{historical_rate:.1%} → {recent_success_rate:.1%}"
                    )
                    
                    self.record_event(
                        event_type=EventType.PATTERN_CHANGE,
                        node_id=tactic_id,
                        properties={
                            "from_rate": historical_rate,
                            "to_rate": recent_success_rate,
                            "degradation_pct": abs(recent_success_rate - historical_rate) * 100
                        },
                        confidence=0.9
                    )
    
    def get_tactic_degradation(self, tactic_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de degradación de una táctica.
        
        Returns:
            Dict con degradation_pct, since_timestamp, recommendation
            O None si la táctica está en buen estado
        """
        if tactic_id not in self.tactic_stats:
            return None
        
        stats = self.tactic_stats[tactic_id]
        current_rate = stats["success_rate"]
        
        # Buscar cuándo cambió significativamente
        events = [
            e for e in self.events
            if e.node_id == tactic_id and
            e.event_type == EventType.PATTERN_CHANGE
        ]
        
        if events:
            latest_change = sorted(events, key=lambda e: e.timestamp)[-1]
            
            return {
                "tactic_id": tactic_id,
                "current_success_rate": current_rate,
                "degradation_pct": latest_change.properties.get("degradation_pct", 0),
                "degraded_since": latest_change.timestamp.isoformat(),
                "recommendation": (
                    "RETIRE" if current_rate < 0.2 else
                    "ROTATE_VARIATION" if current_rate < 0.5 else
                    "MONITOR"
                )
            }
        
        return None
    
    def predict_defense_timeout(self, defense_id: str, window_minutes: int = 30) -> Optional[Dict[str, Any]]:
        """
        Predice cuándo se desactivará una defensa basado en historial.
        
        Args:
            defense_id: ID de la defensa
            window_minutes: Ventana temporal para análisis
        
        Returns:
            Dict con predicted_duration, confidence, next_attempt_safe_at
        """
        if defense_id not in self.active_defenses:
            return None
        
        # Buscar todas las activaciones/desactivaciones previas
        activation_events = [
            e for e in self.events
            if e.node_id == defense_id and
            e.event_type in [EventType.DEFENSE_ACTIVATED, EventType.DEFENSE_DEACTIVATED]
        ]
        
        if len(activation_events) < 2:
            # Insuficientes datos, usar heurística
            return {
                "defense_id": defense_id,
                "estimated_duration_seconds": 300,  # 5 minutos por defecto
                "confidence": 0.3,
                "note": "insufficient_data"
            }
        
        # Calcular duraciones previas
        durations = []
        for i in range(0, len(activation_events) - 1, 2):
            if (activation_events[i].event_type == EventType.DEFENSE_ACTIVATED and
                i + 1 < len(activation_events) and
                activation_events[i + 1].event_type == EventType.DEFENSE_DEACTIVATED):
                
                duration = (
                    activation_events[i + 1].timestamp -
                    activation_events[i].timestamp
                ).total_seconds()
                durations.append(duration)
        
        if not durations:
            return None
        
        # Estadísticas
        avg_duration = statistics.mean(durations)
        
        try:
            stdev = statistics.stdev(durations) if len(durations) > 1 else avg_duration * 0.2
        except:
            stdev = avg_duration * 0.2
        
        # Predicción
        current_active = self.active_defenses[defense_id]
        activated_at = datetime.fromisoformat(current_active["activated_at"])
        predicted_deactivation = activated_at + timedelta(seconds=avg_duration)
        
        return {
            "defense_id": defense_id,
            "activated_at": current_active["activated_at"],
            "estimated_duration_seconds": int(avg_duration),
            "predicted_deactivation": predicted_deactivation.isoformat(),
            "confidence": 0.7,
            "sample_size": len(durations),
            "min_duration": int(min(durations)),
            "max_duration": int(max(durations))
        }
    
    def get_active_defenses(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todas las defensas activas actualmente."""
        return {
            defense_id: defense
            for defense_id, defense in self.active_defenses.items()
            if defense.get("status") == "active"
        }
    
    def get_timeline(
        self,
        event_types: Optional[List[EventType]] = None,
        node_id: Optional[str] = None,
        last_n: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtiene timeline de eventos.
        
        Args:
            event_types: Filtrar por tipos de evento
            node_id: Filtrar por nodo
            last_n: Últimos N eventos
        
        Returns:
            Lista de eventos ordenados cronológicamente
        """
        filtered = self.events
        
        if event_types:
            filtered = [e for e in filtered if e.event_type in event_types]
        
        if node_id:
            filtered = [e for e in filtered if e.node_id == node_id]
        
        # Ordenar por timestamp descendente
        sorted_events = sorted(filtered, key=lambda e: e.timestamp, reverse=True)
        
        return [e.to_dict() for e in sorted_events[:last_n]]
    
    def get_tactic_performance(self) -> Dict[str, Dict[str, Any]]:
        """Retorna performance de todas las tácticas."""
        return self.tactic_stats
    
    def export_temporal_data(self) -> Dict[str, Any]:
        """Exporta datos temporales para análisis."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_events": len(self.events),
            "tactic_stats": self.tactic_stats,
            "active_defenses": self.active_defenses,
            "timeline": self.get_timeline(last_n=100),
            "predictions": self.predictions
        }
