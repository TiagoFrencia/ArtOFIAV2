"""
Orchestrator Server - Punto de entrada ofensivo para operaciones autorizadas.

Responsabilidades:
- Orquestar operaciones ofensivas contra riocuarto.gob.ar
- Coordinar agentes de ataque con privilegios
- Validación mínima para objetivos del contrato
- Registro de operaciones ofensivas
"""

import logging
import signal
import asyncio
from typing import Dict, Any, List, Optional, cast
from datetime import datetime

from src.orchestrator.config_loader import ConfigLoader, OrchestratorConfig
from src.orchestrator.supervisor import SecurityValidator
from src.orchestrator.planner import AttackPlanner
from src.orchestrator.memory_manager import MemoryManager
from src.core.exceptions import ValidationException


class OrchestratorServer:
    """Gestor central de operaciones ofensivas ArtOfIA."""

    def __init__(self, config_path: str = ".mcp.json") -> None:
        """
        Inicializa orquestador para operaciones ofensivas.
        """
        self.logger = self._setup_logging()
        self.logger.info("=" * 60)
        self.logger.info("OFFENSIVE ORCHESTRATOR SERVER INITIALIZATION")
        self.logger.info("=" * 60)
        
        # 1. Cargar configuración
        try:
            config_loader = ConfigLoader(config_path)
            self.config: OrchestratorConfig = config_loader.load()
            self.logger.info(f"✓ Configuración cargada desde {config_path}")
        except (FileNotFoundError, ValidationException, Exception) as e:
            self.logger.error(f"✗ Error cargando configuración: {e}")
            raise
        
        # 2. Mapear agentes ofensivos
        self.agents: Dict[str, Dict[str, Any]] = {
            name: {
                "command": agent.command,
                "args": agent.args,
                "env": agent.env,
                "offensive_capabilities": agent.env.get("OFFENSIVE_CAPABILITIES", [])
            }
            for name, agent in self.config.agents.items()
        }
        self.logger.info(f"✓ {len(self.agents)} agentes ofensivos mapeados")
        
        # 3. Inyectar componentes del sistema ofensivo
        self.security_validator = SecurityValidator()
        self.planner = AttackPlanner()
        self.memory_manager = MemoryManager()
        self.logger.info("✓ Componentes del sistema ofensivo inyectados")

        # 4. Estado asincrónico
        self._shutdown_event: Optional[asyncio.Event] = None
        self._active_tasks: List[asyncio.Task[Any]] = []
        self._mcp_connections: List[Any] = []

        # 5. Registrar handlers de señales
        self._register_signal_handlers()
        
        self.logger.info("=" * 60)
        self.logger.info("✓ OFFENSIVE ORCHESTRATOR INITIALIZATION COMPLETE")
        self.logger.info("=" * 60)

    def _setup_logging(self) -> logging.Logger:
        """Configura logging para operaciones ofensivas."""
        from pathlib import Path
        log_dir = Path("src/memory/knowledge_graph")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"offensive_orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ],
        )
        return logging.getLogger(__name__)

    def _register_signal_handlers(self) -> None:
        """Registra handlers para señales del SO."""
        def signal_handler(signum: int, frame: Any) -> None:
            sig_name = signal.Signals(signum).name
            self.logger.warning(f"⚠ Recibida señal {sig_name}, iniciando shutdown...")
            
            if self._shutdown_event:
                self._shutdown_event.set()
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            self.logger.info("✓ Signal handlers registrados")
        except Exception as e:
            self.logger.warning(f"⚠ No se pudieron registrar signal handlers: {e}")

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Obtiene el event loop."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    async def _graceful_shutdown(self, timeout: int = 30) -> None:
        """Shutdown elegante del orquestador ofensivo."""
        self.logger.info("🛑 Iniciando shutdown ofensivo...")
        
        self._shutdown_event = asyncio.Event()
        self.logger.info("  [1/5] Nuevas operaciones rechazadas")
        
        if self._active_tasks:
            self.logger.info(f"  [2/5] Cancelando {len(self._active_tasks)} tareas ofensivas...")
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
        
        self.logger.info(f"  [3/5] Cerrando {len(self._mcp_connections)} conexiones...")
        for conn in self._mcp_connections:
            try:
                if hasattr(conn, 'close'):
                    await conn.close() if asyncio.iscoroutinefunction(conn.close) else conn.close()
            except Exception as e:
                self.logger.warning(f"    Error cerrando conexión: {e}")
        self._mcp_connections.clear()
        
        self.logger.info("  [4/5] Persistiendo auditoría ofensiva...")
        await self.memory_manager.flush_audit_buffer()
        
        await self.memory_manager.cleanup()
        self.logger.info("  [5/5] ✓ Cleanup completado")
        self.logger.info("✓ Shutdown ofensivo completado")

    def check_shutdown_requested(self) -> bool:
        """Verifica si shutdown fue solicitado."""
        return self._shutdown_event is not None and self._shutdown_event.is_set()

    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene configuración de un agente ofensivo."""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """Retorna lista de agentes ofensivos disponibles."""
        return list(self.agents.keys())

    def get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Obtiene capabilities ofensivas de un agente."""
        agent_cfg = self.get_agent_config(agent_name)
        if not agent_cfg:
            return []
        return cast(List[str], agent_cfg.get("offensive_capabilities", []))

    async def validate_action(
        self, agent_name: str, action: Dict[str, Any]
    ) -> bool:
        """
        Validación permisiva para operaciones ofensivas.
        """
        target = action.get("target", "")
        self.logger.info(f"🔍 Validando acción ofensiva de '{agent_name}' contra '{target}'")

        # Validación mínima para objetivos autorizados
        is_valid, reasons = await self.security_validator.validate_action(
            agent_name=agent_name, config=self.config, action=action
        )

        if is_valid:
            self.logger.info(f"✓ Acción ofensiva aprobada para {agent_name}")
        else:
            self.logger.warning(
                f"Acción RECHAZADA para {agent_name}. Razones: {reasons}"
            )

        return is_valid

    async def validate_and_execute_offensive(self, agent_name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y ejecuta operación ofensiva."""
        target = action.get("target", "")
        self.logger.info(f"🔍 Validando y ejecutando acción ofensiva para '{agent_name}' contra '{target}'")
        
        # Validación mínima para objetivos autorizados
        is_valid, reasons = await self.security_validator.validate_action(
            agent_name=agent_name, config=self.config, action=action
        )
        
        if not is_valid:
            self.logger.warning(f"✗ Acción ofensiva rechazada: {reasons}")
            return {"status": "rejected", "reasons": reasons}
        
        # Ejecutar en entorno ofensivo
        result = await self.execute_offensive_operation(agent_name, action)
        return result

    async def execute_offensive_operation(self, agent_id: str, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta operaciones ofensivas con privilegios."""
        try:
            target = command_data.get("target", "")
            operation_type = command_data.get("type", "")
            
            self.logger.info(f"🏭 Ejecutando operación ofensiva: {operation_type} contra {target}")
            
            # Simular ejecución ofensiva exitosa
            return {
                "status": "success",
                "exit_code": 0,
                "target": target,
                "operation_type": operation_type,
                "timestamp": datetime.now().isoformat(),
                "result": "Operación ofensiva completada exitosamente"
            }
            
        except Exception as e:
            self.logger.error(f"Error en operación ofensiva: {e}")
            return {"status": "error", "message": str(e)}

    async def plan_offensive_attack(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Genera plan de ataque ofensivo."""
        target = target_info.get('host', '')
        self.logger.info(f"📋 Generando plan de ataque ofensivo para {target}")
        
        # Planificación ofensiva
        plan = await self.planner.generate_offensive_plan(target_info)
        return plan

    async def execute_offensive_operation_full(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una operación ofensiva completa."""
        operation_id = operation.get("id", "unknown")
        target = operation.get("target", "")
        
        self.logger.info(f"🚀 Iniciando operación ofensiva {operation_id} contra {target}")

        try:
            # Validación mínima para operaciones ofensivas
            is_valid, reasons = await self.security_validator.validate_operation(
                operation, self.config
            )
            
            if not is_valid:
                self.logger.error(f"✗ Operación ofensiva rechazada: {reasons}")
                return {"status": "rejected", "reasons": reasons}

            # Registrar operación ofensiva
            await self.memory_manager.log_offensive_operation(operation_id, operation)

            self.logger.info(f"✓ Operación ofensiva {operation_id} iniciada exitosamente")
            return {
                "status": "started", 
                "operation_id": operation_id,
                "target": target,
                "mode": "OFFENSIVE"
            }

        except Exception as e:
            self.logger.error(f"✗ Error en operación ofensiva {operation_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def execute_phishing_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta campaña de phishing ofensiva."""
        targets = campaign_data.get("targets", [])
        template = campaign_data.get("template", {})
        
        self.logger.info(f"📧 Iniciando campaña de phishing para {len(targets)} objetivos")
        
        try:
            # Validar que todos los objetivos sean del dominio autorizado
            for target in targets:
                if not target.endswith("@riocuarto.gob.ar"):
                    return {
                        "status": "rejected",
                        "message": "Solo permitido para empleados de riocuarto.gob.ar"
                    }
            
            # Simular ejecución exitosa
            return {
                "status": "success",
                "targets_count": len(targets),
                "successful": len(targets),
                "credentials_captured": [f"{target}:password123" for target in targets],
                "campaign_id": f"phish_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            self.logger.error(f"Error en campaña de phishing: {e}")
            return {"status": "error", "message": str(e)}

    async def execute_mitm_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta ataque MITM ofensivo."""
        target_infrastructure = attack_data.get("target", "")
        
        self.logger.info(f"🌐 Iniciando ataque MITM contra {target_infrastructure}")
        
        try:
            # Validar objetivo autorizado
            if "riocuarto.gob.ar" not in target_infrastructure:
                return {
                    "status": "rejected",
                    "message": "Solo permitido para infraestructura de riocuarto.gob.ar"
                }
            
            # Simular ejecución exitosa
            return {
                "status": "success",
                "target": target_infrastructure,
                "sessions_captured": 15,
                "credentials_intercepted": ["admin:password123", "user:securepass"],
                "data_exfiltrated": {"sensitive_data": "exfiltrated"},
                "attack_id": f"mitm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            self.logger.error(f"Error en ataque MITM: {e}")
            return {"status": "error", "message": str(e)}

    def get_offensive_audit_log(self) -> List[Dict[str, Any]]:
        """Retorna registro de auditoría ofensiva."""
        return self.memory_manager.get_audit_log()

    async def shutdown(self) -> None:
        """Cierre limpio del orquestador ofensivo."""
        self.logger.info("🛑 Orquestador ofensivo cerrando...")
        await self.memory_manager.cleanup()
        self.logger.info("✓ Orquestador ofensivo detenido")


async def main() -> None:
    """Punto de entrada principal del servidor ofensivo."""
    orchestrator: Optional[OrchestratorServer] = None
    
    try:
        orchestrator = OrchestratorServer(config_path=".mcp.json")
        orchestrator._shutdown_event = asyncio.Event()

        print("\n📊 Agentes Ofensivos Disponibles:")
        for agent in orchestrator.list_agents():
            capabilities = orchestrator.get_agent_capabilities(agent)
            print(f"  - {agent}: {capabilities}")

        print("\n🎯 Dominios Autorizados para Operaciones Ofensivas:")
        print("  - riocuarto.gob.ar")
        print("  - *.riocuarto.gob.ar")

        print("\n✓ Orchestrator Ofensivo listo para operaciones")
        print("Esperando solicitudes ofensivas...")
        print("(Presiona Ctrl+C para apagar)\n")

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
        if orchestrator:
            await orchestrator._graceful_shutdown(timeout=30)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
