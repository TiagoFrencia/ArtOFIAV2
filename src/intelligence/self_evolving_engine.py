"""
Self-Evolving Engine - Reinforcement Learning for Attack Optimization
=====================================================================

Motor de aprendizaje que permite que el agente evolucione autónomamente.

Principios:
- Cada ataque genera datos de éxito/fracaso
- El motor analiza patrones de éxito
- Actualiza tácticas basadas en resultados
- Adapta el agente a defensas desconocidas

Ejemplo:
- Intento 1: PowerShell bypass → Detectado
- Intento 2: certutil bypass → Exitoso (registrar)
- Intento 3: En futuro, prefiere certutil
- Auto-ajusta parameters para máxima evasión

GUARDRAIL: El aprendizaje NUNCA modifica guardrails de seguridad.
Solo optimiza tácticas dentro de límites éticos.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class LearningOutcome(str, Enum):
    """Resultado del aprendizaje"""
    SUCCESS = "success"
    DETECTED = "detected"
    BLOCKED = "blocked"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class AttackEpisode:
    """Episodio de ataque para aprendizaje"""
    attack_type: str
    technique: str
    target_os: str
    edr_type: str
    parameters: Dict[str, Any]
    outcome: LearningOutcome
    confidence_score: float
    duration_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_type": self.attack_type,
            "technique": self.technique,
            "target_os": self.target_os,
            "edr_type": self.edr_type,
            "parameters": self.parameters,
            "outcome": self.outcome.value,
            "confidence_score": self.confidence_score,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class TacticEvaluation:
    """Evaluación de táctica ofensiva"""
    
    def __init__(self, tactic_name: str):
        self.tactic_name = tactic_name
        self.total_attempts = 0
        self.successful_attempts = 0
        self.detected_attempts = 0
        self.avg_duration_ms = 0
        self.parameters_tried = []
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito (0.0-1.0)"""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts
    
    @property
    def detection_rate(self) -> float:
        """Tasa de detección (0.0-1.0)"""
        if self.total_attempts == 0:
            return 0.0
        return self.detected_attempts / self.total_attempts
    
    def record_attempt(self, outcome: LearningOutcome, duration_ms: int,
                      parameters: Dict[str, Any]) -> None:
        """Registrar intento"""
        
        self.total_attempts += 1
        
        if outcome == LearningOutcome.SUCCESS:
            self.successful_attempts += 1
        elif outcome == LearningOutcome.DETECTED:
            self.detected_attempts += 1
        
        self.avg_duration_ms = (
            (self.avg_duration_ms * (self.total_attempts - 1) + duration_ms) /
            self.total_attempts
        )
        
        self.parameters_tried.append(parameters)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tactic": self.tactic_name,
            "total_attempts": self.total_attempts,
            "success_rate": self.success_rate,
            "detection_rate": self.detection_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "successful_attempts": self.successful_attempts,
            "detected_attempts": self.detected_attempts,
        }


class SelfEvolvingEngine:
    """
    Motor de auto-evolución usando reinforcement learning.
    
    Aprende de experiencias pasadas y optimiza:
    - Selection de técnicas
    - Parameters de ataque
    - Timing y jitter
    - Evasion strategies
    """
    
    def __init__(self, memory_capacity: int = 10000):
        self.episode_history: List[AttackEpisode] = []
        self.tactic_evaluations: Dict[str, TacticEvaluation] = {}
        self.memory_capacity = memory_capacity
        self.learning_rate = 0.1  # Cómo de agresivo aprender
    
    async def record_attack_outcome(self, episode: AttackEpisode) -> None:
        """
        Registrar resultado de ataque para aprendizaje.
        
        El motor automáticamente:
        1. Evalúa la táctica usada
        2. Ajusta confidences
        3. Sugiere mejoras
        """
        
        # Agregar a historial
        self.episode_history.append(episode)
        
        # Mantener limitador de memoria
        if len(self.episode_history) > self.memory_capacity:
            self.episode_history.pop(0)
        
        # Actualizar evaluación de táctica
        self._update_tactic_evaluation(episode)
        
        logger.info(f"Recorded attack: {episode.technique} → {episode.outcome.value}")
    
    def _update_tactic_evaluation(self, episode: AttackEpisode) -> None:
        """Actualizar evaluación de táctica"""
        
        key = f"{episode.attack_type}:{episode.technique}:{episode.target_os}"
        
        if key not in self.tactic_evaluations:
            self.tactic_evaluations[key] = TacticEvaluation(key)
        
        evaluation = self.tactic_evaluations[key]
        evaluation.record_attempt(episode.outcome, episode.duration_ms, episode.parameters)
    
    async def get_recommended_techniques(self, attack_type: str,target_os: str,
                                        edr_type: str) -> List[Dict[str, Any]]:
        """
        Obtener técnicas recomendadas basadas en aprendizaje.
        
        Retorna técnicas ordenadas por probabilidad de éxito,
        considerando:
        - Success rate histórico
        - Detection rate
        - Speed
        """
        
        relevant_tactics = [
            (key, eval) for key, eval in self.tactic_evaluations.items()
            if attack_type in key and target_os in key
        ]
        
        if not relevant_tactics:
            logger.info(f"No learning data yet for {attack_type}/{target_os}")
            return []
        
        # Rankear por "fitness score"
        ranked = []
        for key, eval in relevant_tactics:
            fitness = self._calculate_fitness_score(eval)
            ranked.append({
                "technique": eval.tactic_name,
                "success_rate": eval.success_rate,
                "detection_rate": eval.detection_rate,
                "fitness_score": fitness,
                "attempts": eval.total_attempts,
            })
        
        return sorted(ranked, key=lambda x: x["fitness_score"], reverse=True)
    
    def _calculate_fitness_score(self, evaluation: TacticEvaluation) -> float:
        """
        Calcular fitness score - qué tan buena es la táctica.
        
        Formula:
        fitness = (success_rate * weight_success) - (detection_rate * weight_detection)
        
        Ejemplo:
        - Técnica A: 90% éxito, 10% detección = 0.9 - 0.1 = 0.8
        - Técnica B: 70% éxito, 5% detección = 0.7 - 0.05 = 0.65
        """
        
        weight_success = 1.0
        weight_detection = 0.5
        
        score = (
            (evaluation.success_rate * weight_success) -
            (evaluation.detection_rate * weight_detection)
        )
        
        # Bonus si ha sido intentado múltiples veces (confianza)
        confidence_bonus = min(0.3, evaluation.total_attempts / 100 * 0.1)
        
        return max(0, score + confidence_bonus)
    
    async def suggest_parameter_tuning(self, technique: str,
                                      history_window_hours: int = 24) -> Dict[str, Any]:
        """
        Sugerir ajustes de parámetros basados en aprendizaje reciente.
        
        Ejemplo:
        - Si detección sube con timing = 1000ms, sugerir timing = 2000ms
        - Si certutil con base64 tiene 80% éxito, sugerir usar más
        """
        
        # Buscar episodes recientes de esta técnica
        recent_episodes = [
            ep for ep in self.episode_history
            if ep.technique == technique and
            datetime.utcnow() - ep.timestamp < timedelta(hours=history_window_hours)
        ]
        
        if not recent_episodes:
            return {"status": "insufficient_data"}
        
        suggestions = {}
        
        # Analizar timing
        successful = [ep for ep in recent_episodes if ep.outcome == LearningOutcome.SUCCESS]
        detected = [ep for ep in recent_episodes if ep.outcome == LearningOutcome.DETECTED]
        
        if successful and detected:
            avg_success_timing = sum(ep.duration_ms for ep in successful) / len(successful)
            avg_detected_timing = sum(ep.duration_ms for ep in detected) / len(detected)
            
            if avg_detected_timing < avg_success_timing:
                suggestions["timing_adjustment"] = "Increase delays between commands"
        
        # Analizar parámetros
        successful_params = [ep.parameters for ep in successful]
        if successful_params:
            suggestions["recommended_parameters"] = self._extract_common_parameters(successful_params)
        
        return {
            "technique": technique,
            "samples": len(recent_episodes),
            "success_rate": len(successful) / len(recent_episodes),
            "suggestions": suggestions,
        }
    
    def _extract_common_parameters(self, param_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extraer parámetros comunes de intentos exitosos"""
        
        if not param_list:
            return {}
        
        # Modo simple: retornar params más comunes
        common = {}
        for key in param_list[0].keys():
            values = [p.get(key) for p in param_list]
            # Retornar más común
            common[key] = max(set(values), key=values.count)
        
        return common
    
    async def get_learning_summary(self) -> Dict[str, Any]:
        """Obtener resumen del aprendizaje del agente"""
        
        total_attacks = len(self.episode_history)
        successful = len([ep for ep in self.episode_history if ep.outcome == LearningOutcome.SUCCESS])
        detected = len([ep for ep in self.episode_history if ep.outcome == LearningOutcome.DETECTED])
        
        return {
            "total_episodes": total_attacks,
            "successful_attacks": successful,
            "detected_attacks": detected,
            "overall_success_rate": successful / max(1, total_attacks),
            "overall_detection_rate": detected / max(1, total_attacks),
            "tactics_learned": len(self.tactic_evaluations),
            "best_performing_tactic": max(
                (
                    (name, eval.success_rate)
                    for name, eval in self.tactic_evaluations.items()
                ),
                key=lambda x: x[1],
                default=(None, 0)
            )[0],
        }
