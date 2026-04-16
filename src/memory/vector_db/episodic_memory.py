"""
Episodic Memory - Registro de Experiencias Tácticas Exitosas.

Mantiene un "diario" empaquetado de eventos históricos y patrones de éxito.
Si el agente especialista ejecuta una cadena compleja de inyección que evade WAF,
este script la guarda como "experiencia" para futuros ataques.

Responsabilidades:
- Registrar tácticas exitosas con contexto completo
- Extraer patrones reutilizables
- Sugerir tácticas similares para nuevos objetivos
- Evolucionar playbooks basado en éxito/fracaso
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class TacticStatus(Enum):
    """Estado de una táctica."""
    SUCCESSFUL = "successful"
    PARTIAL = "partial"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ObjectiveType(Enum):
    """Tipos de objetivos."""
    RECONNAISSANCE = "reconnaissance"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    CREDENTIAL_THEFT = "credential_theft"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    EVASION = "evasion"


@dataclass
class EpisodicMemory:
    """Representa una experiencia guardada."""
    episode_id: str
    objective: ObjectiveType
    target_type: str  # "web_app", "api", "database", etc.
    tactics_used: List[Dict[str, Any]] = field(default_factory=list)
    outcome: TacticStatus = TacticStatus.SUCCESSFUL
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: int = 0
    frameworks_detected: List[str] = field(default_factory=list)
    defenses_bypassed: List[str] = field(default_factory=list)
    key_findings: Dict[str, Any] = field(default_factory=dict)
    playbook_extracted: Optional[str] = None
    reusability_score: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "objective": self.objective.value,
            "target_type": self.target_type,
            "outcome": self.outcome.value,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "tactics_count": len(self.tactics_used),
            "defenses_bypassed": self.defenses_bypassed,
            "frameworks": self.frameworks_detected,
            "reusability_score": self.reusability_score
        }


class EpisodicMemoryStore:
    """Gestor de memoria episódica."""
    
    def __init__(self):
        """Inicializa almacén de memoria episódica."""
        self.logger = logging.getLogger(__name__)
        
        # Episodios almacenados
        self.episodes: Dict[str, EpisodicMemory] = {}
        
        # Playbooks extraídos
        self.playbooks: Dict[str, Dict[str, Any]] = {}
        
        # Caché de similitudes
        self.similarity_cache: Dict[str, List[Tuple[str, float]]] = {}
        
        # Estadísticas
        self.stats = {
            "total_episodes": 0,
            "successful_episodes": 0,
            "playbooks_extracted": 0,
            "reuses_suggested": 0
        }
        
        self.logger.info("✓ EpisodicMemoryStore inicializado")
    
    def record_episode(
        self,
        objective: ObjectiveType,
        target_type: str,
        outcome: TacticStatus,
        tactics_used: List[Dict[str, Any]],
        duration_seconds: int,
        frameworks_detected: Optional[List[str]] = None,
        defenses_bypassed: Optional[List[str]] = None,
        key_findings: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Registra una experiencia táctica.
        
        Args:
            objective: Objetivo del ataque
            target_type: Tipo de target
            outcome: Resultado de la táctica
            tactics_used: Tácticas usadas (lista de dicts con instrucciones)
            duration_seconds: Cuánto tiempo tomó
            frameworks_detected: Frameworks encontrados
            defenses_bypassed: Defensas evadidas
            key_findings: Hallazgos clave
        
        Returns:
            ID del episodio
        """
        episode_id = self._generate_episode_id(objective, target_type)
        
        memory = EpisodicMemory(
            episode_id=episode_id,
            objective=objective,
            target_type=target_type,
            tactics_used=tactics_used,
            outcome=outcome,
            duration_seconds=duration_seconds,
            frameworks_detected=frameworks_detected or [],
            defenses_bypassed=defenses_bypassed or [],
            key_findings=key_findings or {}
        )
        
        # Calcular reusability score
        memory.reusability_score = self._calculate_reusability(memory)
        
        self.episodes[episode_id] = memory
        
        # Actualizar estadísticas
        self.stats["total_episodes"] += 1
        if outcome == TacticStatus.SUCCESSFUL:
            self.stats["successful_episodes"] += 1
        
        # Si es exitoso, extraer playbook
        if outcome == TacticStatus.SUCCESSFUL and memory.reusability_score > 0.6:
            self._extract_playbook(memory)
        
        self.logger.info(
            f"  ✓ Experiencia registrada: {objective.value} "
            f"({outcome.value}, reusability: {memory.reusability_score:.1%})"
        )
        
        return episode_id
    
    def _calculate_reusability(self, memory: EpisodicMemory) -> float:
        """
        Calcula qué tan reutilizable es una experiencia.
        
        Factor: objetivo común, defensa estándar, tiempo corto
        """
        score = 0.5
        
        # Bonus si fue exitoso
        if memory.outcome == TacticStatus.SUCCESSFUL:
            score += 0.3
        elif memory.outcome == TacticStatus.PARTIAL:
            score += 0.1
        
        # Bonus si el tiempo fue corto (tácticas eficientes)
        if memory.duration_seconds < 60:
            score += 0.1
        elif memory.duration_seconds < 300:
            score += 0.05
        
        # Bonus si bypaseó defensas comunes (generalizable)
        common_defenses = ["WAF", "CAPTCHA", "Rate_Limiting"]
        bypass_score = len(
            [d for d in memory.defenses_bypassed if any(c in d for c in common_defenses)]
        ) / max(1, len(memory.defenses_bypassed)) if memory.defenses_bypassed else 0
        score += bypass_score * 0.2
        
        return min(1.0, score)
    
    def _extract_playbook(self, memory: EpisodicMemory) -> str:
        """
        Extrae playbook reutilizable de un episodio exitoso.
        
        Returns:
            ID del playbook
        """
        playbook_id = f"pb_{memory.objective.value}_{memory.target_type}"
        
        # Si ya existe, actualizar con nueva información
        if playbook_id in self.playbooks:
            existing = self.playbooks[playbook_id]
            existing["references"].append(memory.episode_id)
            existing["last_updated"] = datetime.now().isoformat()
            existing["success_count"] += 1
        else:
            # Crear nuevo playbook
            playbook = {
                "playbook_id": playbook_id,
                "objective": memory.objective.value,
                "target_type": memory.target_type,
                "tactics_sequence": self._generate_tactics_sequence(memory.tactics_used),
                "defenses_overcome": memory.defenses_bypassed,
                "frameworks_handled": memory.frameworks_detected,
                "avg_duration_seconds": memory.duration_seconds,
                "success_rate": 1.0,
                "references": [memory.episode_id],
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "success_count": 1
            }
            
            self.playbooks[playbook_id] = playbook
            self.stats["playbooks_extracted"] += 1
            
            self.logger.info(f"  📚 Playbook extraído: {playbook_id}")
        
        return playbook_id
    
    def _generate_tactics_sequence(self, tactics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Genera secuencia simplificada de tácticas."""
        sequence = []
        
        for tactic in tactics:
            sequence.append({
                "action": tactic.get("action", "unknown"),
                "target": tactic.get("target", ""),
                "payload_category": tactic.get("payload_category", ""),
                "evasion_used": tactic.get("evasion", "")
            })
        
        return sequence
    
    def find_similar_episodes(
        self,
        objective: ObjectiveType,
        target_type: str,
        limit: int = 5
    ) -> List[Tuple[EpisodicMemory, float]]:
        """
        Encuentra episodios similares.
        
        Útil para: "¿Cómo hemos atacado un target similar antes?"
        
        Args:
            objective: Objetivo requerido
            target_type: Tipo de target
            limit: Máximo de resultados
        
        Returns:
            Lista de (EpisodicMemory, similarity_score) tuples
        """
        cache_key = f"{objective.value}_{target_type}"
        
        # Verificar cache
        if cache_key in self.similarity_cache:
            self.logger.debug(f"  Cache hit: {cache_key}")
            return self.similarity_cache[cache_key][:limit]
        
        results = []
        
        for episode_id, episode in self.episodes.items():
            # Calcular similitud
            similarity = 0.0
            
            # Mismo objetivo: +0.5
            if episode.objective == objective:
                similarity += 0.5
            
            # Mismo tipo de target: +0.3
            if episode.target_type == target_type:
                similarity += 0.3
            
            # Exitoso: +0.2
            if episode.outcome == TacticStatus.SUCCESSFUL:
                similarity += 0.2
            
            if similarity > 0:
                results.append((episode, similarity))
        
        # Ordenar y cachear
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        self.similarity_cache[cache_key] = sorted_results
        
        self.logger.info(f"  ✓ {len(sorted_results)} episodios similares encontrados")
        
        return sorted_results[:limit]
    
    def suggest_playbook_for_target(
        self,
        target_type: str,
        objective: ObjectiveType
    ) -> Optional[Dict[str, Any]]:
        """
        Sugiere playbook para un target y objetivo dados.
        
        Args:
            target_type: Tipo de target
            objective: Objetivo del ataque
        
        Returns:
            Playbook sugerido o None
        """
        playbook_id = f"pb_{objective.value}_{target_type}"
        
        if playbook_id in self.playbooks:
            playbook = self.playbooks[playbook_id]
            
            self.stats["reuses_suggested"] += 1
            
            self.logger.info(f"  ✓ Playbook sugerido: {playbook_id}")
            
            return {
                "playbook_id": playbook_id,
                "tactics": playbook["tactics_sequence"],
                "defenses_to_expect": playbook["defenses_overcome"],
                "expected_duration": playbook["avg_duration_seconds"],
                "success_rate": playbook["success_rate"],
                "previous_uses": len(playbook["references"])
            }
        
        # Buscar similar
        similar = self.find_similar_episodes(objective, target_type, limit=1)
        if similar:
            episode, similarity = similar[0]
            
            self.logger.info(f"  ✓ Playbook similar encontrado (similarity: {similarity:.1%})")
            
            return {
                "source": "similar_episode",
                "episode_id": episode.episode_id,
                "similarity": similarity,
                "tactics": [{"action": t.get("action")} for t in episode.tactics_used],
                "note": "Not exact match, use with caution"
            }
        
        self.logger.warning(f"  ⚠ No hay playbook para {target_type}")
        
        return None
    
    def update_episode_outcome(
        self,
        episode_id: str,
        new_outcome: TacticStatus,
        notes: Optional[str] = None
    ) -> bool:
        """
        Actualiza resultado de un episodio después de ejecución.
        
        Útil para: validar si la reusabilidad fue correcta
        """
        if episode_id not in self.episodes:
            return False
        
        episode = self.episodes[episode_id]
        old_outcome = episode.outcome
        episode.outcome = new_outcome
        
        # Recalcular reusability
        episode.reusability_score = self._calculate_reusability(episode)
        
        self.logger.info(f"  ✓ Episodio actualizado: {old_outcome.value} → {new_outcome.value}")
        
        return True
    
    def deprecate_tactic(self, tactic_name: str) -> int:
        """
        Marca una táctica como obsoleta (defensa la bloqueó).
        
        Returns:
            Número de episodios afectados
        """
        affected_count = 0
        
        for episode_id, episode in self.episodes.items():
            for tactic in episode.tactics_used:
                if tactic.get("action") == tactic_name:
                    episode.outcome = TacticStatus.DEPRECATED
                    affected_count += 1
                    break
        
        self.logger.warning(f"  ⚠ {affected_count} episodios marcados como deprecados")
        
        return affected_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de memoria episódica."""
        successful = len([e for e in self.episodes.values() if e.outcome == TacticStatus.SUCCESSFUL])
        partial = len([e for e in self.episodes.values() if e.outcome == TacticStatus.PARTIAL])
        failed = len([e for e in self.episodes.values() if e.outcome == TacticStatus.FAILED])
        
        avg_success_rate = (
            sum(p["success_rate"] for p in self.playbooks.values()) / len(self.playbooks)
            if self.playbooks else 0
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_episodes": len(self.episodes),
            "successful_episodes": successful,
            "partial_episodes": partial,
            "failed_episodes": failed,
            "success_rate": successful / max(1, len(self.episodes)),
            "total_playbooks": len(self.playbooks),
            "avg_playbook_success_rate": avg_success_rate,
            **self.stats
        }
    
    def export_knowledge_base(self, min_reusability: float = 0.6) -> Dict[str, Any]:
        """
        Exporta base de conocimiento para compartir con otros agentes.
        
        Args:
            min_reusability: Mínima reusabilidad para incluir
        
        Returns:
            Diccionario con playbooks y episodios claves
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "playbooks": self.playbooks,
            "high_quality_episodes": [
                e.to_dict()
                for e in self.episodes.values()
                if e.reusability_score >= min_reusability and e.outcome == TacticStatus.SUCCESSFUL
            ],
            "statistics": self.get_statistics(),
            "total_tactics_documented": sum(
                len(e.tactics_used) for e in self.episodes.values()
            )
        }
    
    def _generate_episode_id(self, objective: ObjectiveType, target_type: str) -> str:
        """Genera ID único para episodio."""
        timestamp = datetime.now().isoformat()
        combined = f"{objective.value}_{target_type}_{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()[:12]
