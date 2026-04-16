"""
Orchestrator Server - Punto de entrada del orquestador central.

Responsabilidades:
- Inicializar el orquestador
- Cargar y parsear configuración desde .mcp.json
- Mapear agentes disponibles y sus capacidades
- Coordinar flujo de operaciones
- Registrar auditoría centralizada
"""

import json
import logging
import signal
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
from datetime import datetime

from src.orchestrator.supervisor import SecurityValidator
from src.orchestrator.planner import AttackPlanner
from src.orchestrator.memory_manager import MemoryManager


class OrchestratorServer:
    """Gestor central de agentes autónomos ArtOfIA."""

    def __init__(self, config_path: str = ".mcp.json") -> None:
        """
        Inicializa el orquestador leyendo configuración y validando setup.

        Args:
            config_path: Ruta al archivo .mcp.json de configuración
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.security_validator = SecurityValidator()
        self.planner = AttackPlanner()
        self.memory_manager = MemoryManager()

        # Context para shutdown elegante
        self._shutdown_event: Optional[asyncio.Event] = None
        self._active_tasks: List[asyncio.Task] = []
        self._mcp_connections: List[Any] = []

        # Configurar logging
        self._setup_logging()

        # Cargar y validar configuración
        self._load_configuration()
        self._validate_infrastructure()

        # Registrar handlers de señales
        self._register_signal_handlers()

    def _setup_logging(self) -> None:
        """Configura sistema de logging centralizado."""
        log_dir = Path("src/memory/knowledge_graph")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== Orchestrator Server Iniciado ===")

    def _load_configuration(self) -> None:
        """
        Carga y parsea el archivo .mcp.json.

        Raises:
            FileNotFoundError: Si .mcp.json no existe
            json.JSONDecodeError: Si el JSON es inválido
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuración no encontrada: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.logger.info(f"✓ Configuración cargada desde {self.config_path}")
        except json.JSONDecodeError as e:
            self.logger.error(f"✗ JSON inválido en {self.config_path}: {e}")
            raise

        # Extraer agentes de configuración
        self.agents = self.config.get("mcpServers", {})
        self.logger.info(f"✓ {len(self.agents)} agentes mapeados")

    def _validate_infrastructure(self) -> None:
        """
        Valida que la infraestructura cumpla con AGENTS.md.

        Verificaciones:
        - Orchestrator definido explícitamente
        - Sandbox required para exploit_agent
        - Validación semántica habilitada
        """
        # Verificar que orchestrator está definido
        if "orchestrator" not in self.agents:
            self.logger.warning("⚠ Orchestrator no está mapeado en mcpServers")

        # Verificar que exploit_agent existe y requiere sandbox
        if "exploit_agent" in self.agents:
            exploit_cfg = self.agents["exploit_agent"]
            if not exploit_cfg.get("env", {}).get("SANDBOX") == "required":
                self.logger.warning("⚠ exploit_agent no tiene SANDBOX=required")
            if not exploit_cfg.get("env", {}).get("VALIDATION_REQUIRED") == "true":
                self.logger.warning("⚠ exploit_agent no tiene VALIDATION_REQUIRED")

        # Verificar seguridad global
        security_cfg = self.config.get("security", {})
        if not security_cfg.get("auditAllActions"):
            self.logger.warning("⚠ auditAllActions no está habilitado")

        self.logger.info("✓ Validación de infraestructura completada")

    def _register_signal_handlers(self) -> None:
        """
        Registra handlers para SIGINT y SIGTERM.
        
        Permite graceful shutdown: cancelación de tareas, cierre de conexiones MCP,
        flush de auditoría antes de salir. Crítico para prevenir fugas de memoria.
        """
        def signal_handler(signum: int, frame: Any) -> None:
            """Handler para señales del SO."""
            sig_name = signal.Signals(signum).name
            self.logger.warning(f"⚠ Recibida señal {sig_name}, iniciando shutdown elegante...")
            
            # Señalizar a la aplicación que debe cerrar
            if self._shutdown_event:
                self._shutdown_event.set()
        
        try:
            # Registrar handlers
            signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # Kill -TERM
            self.logger.info("✓ Signal handlers registrados (SIGINT, SIGTERM)")
        except Exception as e:
            self.logger.warning(f"⚠ No se pudieron registrar signal handlers: {e}")

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Obtiene o crea el event loop."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    async def _graceful_shutdown(self, timeout: int = 30) -> None:
        """
        Realiza shutdown elegante del orquestador.
        
        Acciones:
        1. Cancelar nuevas operaciones
        2. Completar tareas en curso (con timeout)
        3. Cerrar conexiones MCP
        4. Flush de buffers de auditoría
        5. Persistencia final de estado
        
        Args:
            timeout: Segundos para esperar tareas (default 30)
        """
        self.logger.info("🛑 Iniciando shutdown elegante...")
        
        # 1. Deja claro que nuevas operaciones serán rechazadas
        self._shutdown_event = asyncio.Event()
        self.logger.info("  [1/5] Nuevas operaciones rechazadas")
        
        # 2. Cancelar tareas activas con timeout
        if self._active_tasks:
            self.logger.info(f"  [2/5] Cancelando {len(self._active_tasks)} tareas activas...")
            for task in self._active_tasks:
                if not task.done():
                    task.cancel()
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._active_tasks, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"  [2/5] ⚠ Timeout esperando tareas ({timeout}s)")
        else:
            self.logger.info("  [2/5] Sin tareas activas")
        
        # 3. Cerrar conexiones MCP
        self.logger.info(f"  [3/5] Cerrando {len(self._mcp_connections)} conexiones MCP...")
        for conn in self._mcp_connections:
            try:
                if hasattr(conn, 'close'):
                    await conn.close() if asyncio.iscoroutinefunction(conn.close) else conn.close()
            except Exception as e:
                self.logger.warning(f"    Error cerrando conexión: {e}")
        self._mcp_connections.clear()
        
        # 4. Flush de auditoría
        self.logger.info("  [4/5] Persistiendo auditoría final...")
        await self.memory_manager.flush_audit_buffer()
        
        # 5. Cleanup final
        await self.memory_manager.cleanup()
        self.logger.info("  [5/5] ✓ Cleanup completado")
        self.logger.info("✓ Shutdown elegante completado")

    def check_shutdown_requested(self) -> bool:
        """Verifica si shutdown fue solicitado."""
        return self._shutdown_event is not None and self._shutdown_event.is_set()

    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene configuración de un agente específico.

        Args:
            agent_name: Nombre del agente

        Returns:
            Configuración del agente o None si no existe
        """
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """Retorna lista de agentes disponibles."""
        return list(self.agents.keys())

    def get_agent_capabilities(self, agent_name: str) -> List[str]:
        """
        Obtiene capabilities de un agente.

        Args:
            agent_name: Nombre del agente

        Returns:
            Lista de capabilities
        """
        agent_cfg = self.get_agent_config(agent_name)
        if not agent_cfg:
            return []
        return agent_cfg.get("capabilities", [])

    async def validate_action(
        self, agent_name: str, action: Dict[str, Any]
    ) -> bool:
        """
        Valida una acción antes de ejecutarla.

        Punto de control crítico para seguridad.

        Args:
            agent_name: Agente que solicita ejecución
            action: Descripción de la acción

        Returns:
            True si acción aprobada, False si rechazada
        """
        self.logger.info(f"🔍 Validando acción del agente '{agent_name}'")

        # Delegar a SecurityValidator
        is_valid, reasons = await self.security_validator.validate_action(
            agent_name=agent_name, config=self.config, action=action
        )

        if is_valid:
            self.logger.info(f"✓ Acción aprobada para {agent_name}")
        else:
            self.logger.warning(
                f"✗ Acción RECHAZADA para {agent_name}. Razones: {reasons}"
            )

        return is_valid

    async def plan_attack(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera plan de ataque estructurado.

        Args:
            target_info: Información del objetivo

        Returns:
            Plan de ataque con fases y agentes asignados
        """
        self.logger.info(f"📋 Generando plan de ataque para {target_info.get('host')}")
        plan = await self.planner.generate_attack_plan(target_info)
        return plan

    async def execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una operación completa con all checkpoints de seguridad.

        Args:
            operation: Definición de la operación

        Returns:
            Resultado de la operación
        """
        operation_id = operation.get("id", "unknown")
        self.logger.info(f"🚀 Iniciando operación {operation_id}")

        try:
            # Validar operación
            is_valid, reasons = await self.security_validator.validate_operation(
                operation, self.config
            )
            if not is_valid:
                self.logger.error(f"✗ Operación rechazada: {reasons}")
                return {"status": "rejected", "reasons": reasons}

            # Persistir en memoria
            await self.memory_manager.log_operation(operation_id, operation)

            self.logger.info(f"✓ Operación {operation_id} iniciada exitosamente")
            return {"status": "started", "operation_id": operation_id}

        except Exception as e:
            self.logger.error(f"✗ Error en operación {operation_id}: {e}")
            return {"status": "error", "error": str(e)}

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Retorna registro de auditoría centralizado."""
        return self.memory_manager.get_audit_log()

    async def shutdown(self) -> None:
        """Cierre limpio del orquestador."""
        self.logger.info("🛑 Orquestador cerrando...")
        await self.memory_manager.cleanup()
        self.logger.info("✓ Orquestador detenido")


async def main() -> None:
    """Punto de entrada principal del servidor con graceful shutdown."""
    orchestrator: Optional[OrchestratorServer] = None
    
    try:
        orchestrator = OrchestratorServer(config_path=".mcp.json")
        orchestrator._shutdown_event = asyncio.Event()

        # Listar agentes disponibles
        print("\n📊 Agentes Disponibles:")
        for agent in orchestrator.list_agents():
            capabilities = orchestrator.get_agent_capabilities(agent)
            print(f"  - {agent}: {capabilities}")

        print("\n✓ Orchestrator listo para operaciones")
        print("Esperando solicitudes...")
        print("(Presiona Ctrl+C para apagar elegantemente)\n")

        # Mantener servidor activo hasta que se reciba SIGINT/SIGTERM
        while not orchestrator.check_shutdown_requested():
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    except KeyboardInterrupt:
        print("\n⚠ Interrupción detectada")
    except Exception as e:
        print(f"✗ Error fatal: {e}")
    finally:
        # Graceful shutdown
        if orchestrator:
            await orchestrator._graceful_shutdown(timeout=30)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
