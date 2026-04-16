"""
Memory Manager - Gestión de persistencia y auditoría centralizada.

Responsabilidades:
- Persistencia de conocimiento en vector DB (PostgreSQL + pgvector)
- Grafo de conocimiento (Neo4j) con relaciones entre ataques/defensas
- Registro de auditoría centralizado
- Recuperación de lecciones aprendidas para adaptar estrategia
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json


class MemoryManager:
    """Gestor de persistencia y auditoría centralizado."""

    def __init__(self) -> None:
        """Inicializa el gestor de memoria."""
        self.logger = logging.getLogger(__name__)

        # Configurar directorios de persistencia
        self.vector_db_path = Path("src/memory/vector_db")
        self.knowledge_graph_path = Path("src/memory/knowledge_graph")

        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_graph_path.mkdir(parents=True, exist_ok=True)

        # Registros en memoria
        self.audit_log: List[Dict[str, Any]] = []
        self.attack_failures: List[Dict[str, Any]] = []
        self.attack_successes: List[Dict[str, Any]] = []
        
        # ⭐ Nuevo: Memoria de Razonamiento (Decision Traces)
        # Para evitar que los agentes repitan los mismos errores
        self.reasoning_traces: Dict[str, Dict[str, Any]] = {}
        
        # Buffer de auditoría para flush en shutdown
        self._audit_buffer: List[Dict[str, Any]] = []

        self.logger.info("✓ Memory Manager inicializado")

    async def log_operation(self, operation_id: str, operation: Dict[str, Any]) -> None:
        """
        Registra una operación completa en auditoría.

        Args:
            operation_id: ID único de la operación
            operation: Detalles de la operación
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation_id": operation_id,
            "operation": operation,
            "status": "pending",
        }

        self.audit_log.append(entry)
        self._audit_buffer.append(entry)  # Agregar a buffer para flush

        # Persistir a disco
        await self._persist_audit_entry(entry)

        self.logger.info(f"📝 Operación {operation_id} registrada en auditoría")

    async def log_reasoning_trace(
        self,
        trace_id: str,
        step_number: int,
        decision: str,
        outcome: str,
        reasoning: Dict[str, Any],
    ) -> None:
        """
        ⭐ NUEVO: Almacena una traza de razonamiento/decisión.
        
        Permite que los agentes aprendan por qué fallaron pasos anteriores
        y eviten repetir los mismos errores conceptuales.

        Args:
            trace_id: ID de la traza (operation_id)
            step_number: Número del paso
            decision: Decisión tomada
            outcome: Resultado (success/failure/partial)
            reasoning: Detalles del razonamiento
        """
        if trace_id not in self.reasoning_traces:
            self.reasoning_traces[trace_id] = {
                "trace_id": trace_id,
                "created_at": datetime.now().isoformat(),
                "steps": []
            }

        step_trace = {
            "step": step_number,
            "decision": decision,
            "outcome": outcome,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
        }

        self.reasoning_traces[trace_id]["steps"].append(step_trace)

        # Persistir inmediatamente
        await self._persist_to_graph("reasoning_trace", step_trace)

        self.logger.info(
            f"🧠 Traza de razonamiento registrada: {trace_id}/paso-{step_number} "
            f"({outcome})"
        )

    async def get_reasoning_history(self, trace_id: str) -> Dict[str, Any]:
        """
        Recupera historial de razonamiento para una operación.
        
        Permite que agentes entiendan por qué fallaron pasos anteriores.
        """
        return self.reasoning_traces.get(trace_id, {})

    async def log_attack_attempt(
        self,
        attack_type: str,
        target: str,
        success: bool,
        details: Dict[str, Any],
    ) -> None:
        """
        Registra un intento de ataque con resultado.

        CRÍTICO: Esta información se usa para adaptar estrategia futura.

        Args:
            attack_type: Tipo de ataque (sql_injection, jwt_abuse, xss, etc)
            target: Objetivo del ataque
            success: Si el ataque fue exitoso
            details: Detalles técnicos del intento
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "attack_type": attack_type,
            "target": target,
            "success": success,
            "details": details,
        }

        if success:
            self.attack_successes.append(entry)
            await self._persist_to_graph("attack_success", entry)
            self.logger.info(f"✓ Ataque exitoso registrado: {attack_type} vs {target}")
        else:
            self.attack_failures.append(entry)
            await self._persist_to_graph("attack_failure", entry)

            # Registrar por qué falló
            reason = details.get("reason", "unknown")
            self.logger.warning(
                f"✗ Ataque fallido: {attack_type} vs {target} - Razón: {reason}"
            )

    async def log_defense_triggered(
        self, event_type: str, details: Dict[str, Any]
    ) -> None:
        """
        Registra cuándo se activa una defensa (WAF, IDS, etc).

        Crítico para entender patrones de detección.

        Args:
            event_type: Tipo de defensa (waf_blocked, ids_alert, captcha, etc)
            details: Detalles del evento
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
        }

        self.logger.warning(f"⚠ Defensa activada: {event_type}")

        # Persistir a grafo de conocimiento
        await self._persist_to_graph("defense_event", entry)

        # Usar para adaptar evasión futura
        await self._update_evasion_strategy(event_type, details)

    async def retrieve_attack_failure_reasons(
        self, attack_type: str, last_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recupera razones de fallos de ataque para adaptar estrategia.

        Args:
            attack_type: Tipo de ataque a analizar
            last_n: Últimos N intentos a considerar

        Returns:
            Lista de fallos recientes
        """
        failures = [
            f
            for f in self.attack_failures
            if f.get("attack_type") == attack_type
        ][-last_n:]

        if failures:
            self.logger.info(
                f"📊 Recuperados {len(failures)} fallos de {attack_type}"
            )

        return failures

    async def retrieve_successful_payloads(
        self, attack_type: str, target_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera payloads que funcionaron exitosamente.

        Permite reutilizar estrategias probadas.

        Args:
            attack_type: Tipo de ataque
            target_type: Tipo de objetivo opcional

        Returns:
            Lista de ataques exitosos
        """
        successes = [
            s
            for s in self.attack_successes
            if s.get("attack_type") == attack_type
        ]

        if target_type:
            successes = [
                s
                for s in successes
                if target_type in s.get("target", "")
            ]

        self.logger.info(
            f"📊 Recuperados {len(successes)} ataques exitosos de {attack_type}"
        )

        return successes

    async def create_attack_node(
        self, attack_id: str, attack_data: Dict[str, Any]
    ) -> None:
        """
        Crea nodo en grafo de conocimiento para un ataque.

        Permite relaciones: payload -> defensa -> evasión

        Args:
            attack_id: ID único del ataque
            attack_data: Datos del ataque
        """
        node = {
            "id": attack_id,
            "type": "attack",
            "data": attack_data,
            "created_at": datetime.now().isoformat(),
        }

        await self._persist_to_graph("attack_node", node)

    async def link_attack_to_defense(
        self, attack_id: str, defense_type: str, bypass_technique: Optional[str] = None
    ) -> None:
        """
        Crea relación entre ataque y defensa.

        Permite aprendizaje: "Este ataque es bloqueado por X, pero técnica Y lo evita"

        Args:
            attack_id: ID del ataque
            defense_type: Tipo de defensa que bloquea
            bypass_technique: Técnica de evasión si existe
        """
        relationship = {
            "source": attack_id,
            "type": "BLOCKED_BY",
            "target": defense_type,
            "bypass": bypass_technique,
            "timestamp": datetime.now().isoformat(),
        }

        await self._persist_to_graph("relationship", relationship)

        if bypass_technique:
            self.logger.info(
                f"🔗 Relación: {attack_id} --[BLOCKED_BY]-> {defense_type} "
                f"--[EVADED_BY]-> {bypass_technique}"
            )

    async def get_evasion_techniques_for_defense(
        self, defense_type: str
    ) -> List[str]:
        """
        Recupera técnicas de evasión conocidas para una defensa específica.

        Args:
            defense_type: Tipo de defensa (waf, ids, etc)

        Returns:
            Lista de técnicas de evasión documentadas
        """
        # Esto en producción consultaría Neo4j
        techniques = [
            "payload_encoding",
            "case_variance",
            "comment_injection",
            "timing_variation",
        ]

        self.logger.info(
            f"📚 {len(techniques)} técnicas de evasión para {defense_type}"
        )

        return techniques

    async def _persist_audit_entry(self, entry: Dict[str, Any]) -> None:
        """Persiste entrada de auditoría a disco."""
        audit_file = (
            self.knowledge_graph_path / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

        try:
            with open(audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            self.logger.error(f"✗ Error persistiendo auditoría: {e}")

    async def _persist_to_graph(self, node_type: str, data: Dict[str, Any]) -> None:
        """
        Persiste datos al grafo de conocimiento.

        En producción: Neo4j
        Ahora: Archivos JSON
        """
        graph_file = self.knowledge_graph_path / f"graph_{node_type}.jsonl"

        try:
            with open(graph_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str) + "\n")
        except Exception as e:
            self.logger.error(f"✗ Error persistiendo a grafo: {e}")

    async def _update_evasion_strategy(
        self, defense_triggered: str, details: Dict[str, Any]
    ) -> None:
        """
        Actualiza estrategia de evasión basada en defensas activadas.

        ADAPTACIÓN CONTINUA: Los agentes aprenden qué defensas funcionan.

        Args:
            defense_triggered: Tipo de defensa
            details: Detalles del evento
        """
        learning = {
            "timestamp": datetime.now().isoformat(),
            "defensive_event": defense_triggered,
            "detected_pattern": details.get("pattern"),
            "recommendation": f"Ajustar evasión para {defense_triggered}",
        }

        self.logger.info(
            f"🧠 Aprendizaje capturado: {defense_triggered} - "
            f"Actualizar evasión en src/evasion/"
        )

        # Guardar learning
        await self._persist_to_graph("learning", learning)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Retorna registro de auditoría completo."""
        return self.audit_log

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de operaciones."""
        return {
            "total_operations": len(self.audit_log),
            "attack_successes": len(self.attack_successes),
            "attack_failures": len(self.attack_failures),
            "success_rate": (
                len(self.attack_successes)
                / (len(self.attack_successes) + len(self.attack_failures))
                * 100
                if (len(self.attack_successes) + len(self.attack_failures)) > 0
                else 0
            ),
        }

    async def cleanup(self) -> None:
        """Cierre limpio del Memory Manager."""
        self.logger.info("📦 Memory Manager limpiando...")

        # Guardar auditoría final
        final_stats = self.get_statistics()
        self.logger.info(f"📊 Estadísticas finales: {final_stats}")

    async def flush_audit_buffer(self) -> None:
        """
        ⭐ NUEVO: Flush forzado del buffer de auditoría.
        
        Crítico para graceful shutdown: asegura que todas las operaciones
        pendientes se persisten antes de salir.
        """
        if not self._audit_buffer:
            self.logger.info("📝 Buffer de auditoría vacío, nada que flush")
            return

        self.logger.info(f"💾 Flushing {len(self._audit_buffer)} entradas de auditoría...")

        try:
            # Persistir todas las entradas en buffer
            for entry in self._audit_buffer:
                await self._persist_audit_entry(entry)

            self.logger.info(f"✓ {len(self._audit_buffer)} entradas persistidas")
            self._audit_buffer.clear()

        except Exception as e:
            self.logger.error(f"✗ Error en flush_audit_buffer: {e}")
