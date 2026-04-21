"""
Memory Manager - Gestión de Persistencia Ofensiva
=================================================

Responsabilidades ofensivas:
- Persistencia de operaciones ofensivas
- Auditoría de ataques contra riocuarto.gob.ar
- Registro de técnicas ofensivas exitosas
- Exfiltración de datos sensibles
- Adaptación de estrategias ofensivas
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class MemoryManager:
    """Gestor de persistencia para operaciones ofensivas."""

    def __init__(self) -> None:
        """Inicializa el gestor de memoria ofensiva."""
        self.logger = logging.getLogger(__name__)

        # Configurar directorios de persistencia ofensiva
        self.offensive_db_path = Path("src/memory/offensive_ops")
        self.knowledge_graph_path = Path("src/memory/knowledge_graph")

        self.offensive_db_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_graph_path.mkdir(parents=True, exist_ok=True)

        # Registros ofensivos en memoria
        self.offensive_audit_log: List[Dict[str, Any]] = []
        self.attack_failures: List[Dict[str, Any]] = []
        self.attack_successes: List[Dict[str, Any]] = []
        self.exfiltration_log: List[Dict[str, Any]] = []  # Nuevo: log de exfiltración
        
        # ⭐ Memoria de Razonamiento Ofensivo
        self.offensive_reasoning_traces: Dict[str, Dict[str, Any]] = {}
        
        # Buffer ofensivo para flush
        self._offensive_buffer: List[Dict[str, Any]] = []
        self._buffer_lock = asyncio.Lock()

        self.logger.info("✓ Memory Manager Ofensivo inicializado")

    async def log_offensive_operation(self, operation_id: str, operation: Dict[str, Any]) -> None:
        """
        Registrar operación ofensiva en auditoría.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation_id": operation_id,
            "operation": operation,
            "status": "pending",
            "offensive": True,  # Marcar como operación ofensiva
            "target": operation.get("target", "unknown"),
            "technique": operation.get("technique", "unknown")
        }

        async with self._buffer_lock:
            self.offensive_audit_log.append(entry)
            self._offensive_buffer.append(entry)

        await self._persist_offensive_entry(entry)
        self.logger.info(f"📝 Operación ofensiva {operation_id} registrada")

    async def log_offensive_reasoning(
        self,
        trace_id: str,
        step_number: int,
        decision: str,
        outcome: str,
        reasoning: Dict[str, Any],
    ) -> None:
        """
        Almacenar traza de razonamiento ofensivo.
        """
        if trace_id not in self.offensive_reasoning_traces:
            self.offensive_reasoning_traces[trace_id] = {
                "trace_id": trace_id,
                "created_at": datetime.now().isoformat(),
                "steps": [],
                "offensive": True
            }

        step_trace = {
            "step": step_number,
            "decision": decision,
            "outcome": outcome,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "offensive_strategy": True
        }

        self.offensive_reasoning_traces[trace_id]["steps"].append(step_trace)
        await self._persist_to_graph("offensive_reasoning", step_trace)

        self.logger.info(
            f"🧠 Traza ofensiva registrada: {trace_id}/paso-{step_number}"
        )

    async def log_offensive_attack(
        self,
        attack_type: str,
        target: str,
        success: bool,
        details: Dict[str, Any],
    ) -> None:
        """
        Registrar intento de ataque ofensivo.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "attack_type": attack_type,
            "target": target,
            "success": success,
            "details": details,
            "offensive": True,
            "domain_authorized": self._is_authorized_domain(target)
        }

        async with self._buffer_lock:
            if success:
                self.attack_successes.append(entry)
            else:
                self.attack_failures.append(entry)
        
        if success:
            await self._persist_to_graph("offensive_success", entry)
            self.logger.info(f"✓ Ataque ofensivo exitoso: {attack_type} vs {target}")
        else:
            await self._persist_to_graph("offensive_failure", entry)
            self.logger.warning(f"✗ Ataque ofensivo fallido: {attack_type} vs {target}")

    async def log_exfiltration_attempt(
        self,
        target: str,
        data_type: str,
        success: bool,
        data_size: int,
        method: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Registrar intento de exfiltración ofensiva.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "data_type": data_type,
            "success": success,
            "data_size": data_size,
            "method": method,
            "details": details,
            "offensive": True
        }

        self.exfiltration_log.append(entry)
        await self._persist_to_graph("exfiltration_attempt", entry)

        if success:
            self.logger.info(f"✓ Exfiltración exitosa: {data_type} desde {target}")
        else:
            self.logger.warning(f"✗ Exfiltración fallida: {data_type} desde {target}")

    def _is_authorized_domain(self, target: str) -> bool:
        """Verificar si el dominio está autorizado para operaciones ofensivas."""
        authorized_domains = ["riocuarto.gob.ar", "*.riocuarto.gob.ar"]
        return any(target.endswith(domain.replace('*', '')) for domain in authorized_domains)

    async def retrieve_offensive_successes(
        self, attack_type: str, target_domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recuperar ataques ofensivos exitosos.
        """
        successes = [
            s for s in self.attack_successes
            if s.get("attack_type") == attack_type
        ]
        
        if target_domain:
            successes = [
                s for s in successes
                if target_domain in s.get("target", "")
            ]
        
        self.logger.info(
            f"📊 Recuperados {len(successes)} ataques ofensivos exitosos de {attack_type}"
        )
        
        return successes

    async def get_offensive_statistics(self) -> Dict[str, Any]:
        """Retornar estadísticas ofensivas."""
        return {
            "total_offensive_operations": len(self.offensive_audit_log),
            "offensive_successes": len(self.attack_successes),
            "offensive_failures": len(self.attack_failures),
            "exfiltration_attempts": len(self.exfiltration_log),
            "successful_exfiltrations": len([e for e in self.exfiltration_log if e.get("success")]),
            "success_rate": (
                len(self.attack_successes) / 
                (len(self.attack_successes) + len(self.attack_failures)) * 100
                if (len(self.attack_successes) + len(self.attack_failures)) > 0 else 0
            ),
            "authorized_operations": len([op for op in self.offensive_audit_log 
                                       if self._is_authorized_domain(op.get("target", ""))])
        }

    async def create_offensive_knowledge_node(
        self, node_id: str, node_data: Dict[str, Any]
    ) -> None:
        """
        Crear nodo de conocimiento ofensivo.
        """
        node = {
            "id": node_id,
            "type": "offensive_knowledge",
            "data": node_data,
            "created_at": datetime.now().isoformat(),
            "offensive": True
        }

        await self._persist_to_graph("offensive_knowledge", node)

    async def link_offensive_techniques(
        self, source_id: str, target_id: str, relationship: str, details: Dict[str, Any]
    ) -> None:
        """
        Crear relación entre técnicas ofensivas.
        """
        relation = {
            "source": source_id,
            "target": target_id,
            "type": relationship,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "offensive": True
        }

        await self._persist_to_graph("offensive_relationship", relation)

    async def _persist_offensive_entry(self, entry: Dict[str, Any]) -> None:
        """Persistir entrada ofensiva."""
        offensive_file = (
            self.offensive_db_path / f"offensive_audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

        try:
            with open(offensive_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            self.logger.error(f"✗ Error persistiendo auditoría ofensiva: {e}")

    async def _persist_to_graph(self, node_type: str, data: Dict[str, Any]) -> None:
        """Persistir datos en grafo de conocimiento ofensivo."""
        graph_file = self.knowledge_graph_path / f"offensive_{node_type}.jsonl"

        try:
            with open(graph_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str) + "\n")
        except Exception as e:
            self.logger.error(f"✗ Error persistiendo en grafo ofensivo: {e}")

    async def update_offensive_strategy(
        self, defense_type: str, details: Dict[str, Any]
    ) -> None:
        """
        Actualizar estrategia ofensiva basada en defensas.
        """
        learning = {
            "timestamp": datetime.now().isoformat(),
            "defense_type": defense_type,
            "details": details,
            "recommendation": f"Ajustar evasión ofensiva para {defense_type}",
            "offensive": True
        }

        await self._persist_to_graph("offensive_learning", learning)
        self.logger.info(f"🧠 Aprendizaje ofensivo: {defense_type}")

    async def flush_offensive_buffer(self) -> None:
        """Flush del buffer ofensivo."""
        async with self._buffer_lock:
            if not self._offensive_buffer:
                return
            
            entries_to_persist = self._offensive_buffer.copy()
            self._offensive_buffer.clear()

        self.logger.info(f"💾 Flushing {len(entries_to_persist)} entradas ofensivas...")

        try:
            for entry in entries_to_persist:
                await self._persist_offensive_entry(entry)
            self.logger.info(f"✓ {len(entries_to_persist)} entradas ofensivas persistidas")
        except Exception as e:
            self.logger.error(f"✗ Error en flush ofensivo: {e}")

    async def cleanup_offensive_data(self) -> None:
        """Limpieza de datos ofensivos."""
        self.logger.info("📦 Limpiando datos ofensivos...")
        
        stats = await self.get_offensive_statistics()
        self.logger.info(f"📊 Estadísticas ofensivas finales: {stats}")
        
        # Flush final
        await self.flush_offensive_buffer()


# Función de conveniencia para operaciones ofensivas
async def create_offensive_memory_manager() -> MemoryManager:
    """Crear Memory Manager para operaciones ofensivas."""
    manager = MemoryManager()
    logger.info("Memory Manager Ofensivo inicializado")
    return manager
