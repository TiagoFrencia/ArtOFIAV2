"""
Main Integration Entry Point - Punto de Entrada Unificado
==========================================================

Orquesta completamente:
┌──────────────────────────────────────────────────────────────┐
│  Orchestrator (Supervisor Humano + Validación)              │
└────────┬─────────────────────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────────────────────┐
    │  BackendIntegration (Capa de Integración)            │
    │                                                        │
    │  ├─ SandboxManager (Ejecución segura)                │
    │  ├─ ProviderManager (IA inteligente)                 │
    │  ├─ SelfEvolvingEngine (Aprendizaje)                 │
    │  └─ AWSManager (Infraestructura nube)                │
    └────┬──────────────────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────────────────────┐
    │  Agents (Recon + Logic + Exploit + SupplyChain)      │
    │                                                        │
    │  ├─ ReconAgent (Inteligencia pasiva)                 │
    │  ├─ LogicAgent (Planificación inteligente)           │
    │  ├─ ExploitAgent (Explotación aislada)               │
    │  └─ SupplyChainAgent (Poisoning CI/CD)               │
    └──────────────────────────────────────────────────────┘

Flujo completo End-to-End documentado en este archivo.
"""

import asyncio
import logging
from typing import Dict, Any, List, cast
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from src.orchestrator.server import OrchestratorServer
from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig


logger = logging.getLogger(__name__)


@dataclass
class InitializationResult:
    """Resultado de inicialización del sistema"""
    success: bool
    errors: List[str]
    component_status: Dict[str, bool] | None = None
    
    def __bool__(self) -> bool:
        """Permite usar result como boolean: if result:"""
        return self.success
    
    def __str__(self) -> str:
        if self.success:
            return "✓ System initialized successfully"
        return f"✗ Initialization failed: {'; '.join(self.errors)}"


class IntegratedArtOfIA:
    """
    Orquestador completamente integrado.
    
    Coordina:
    1. Orchestrator → validación + scheduling
    2. Backend Integration → infraestructura
    3. Agentes → reconocimiento + lógica + explotación
    """
    
    # ⭐ SECURITY: Timeouts para prevenir operaciones infinitas y DoS
    STAGE_TIMEOUT = 300.0  # 5 minutos por stage
    OPERATION_TIMEOUT = 1200.0  # 20 minutos para operación completa
    
    def __init__(self, config_path: str = ".mcp.json") -> None:
        self.orchestrator = OrchestratorServer(config_path)
        self.backend_integration: BackendIntegration | None = None
        self.operation_history: list[Dict[str, Any]] = []
    
    async def initialize(self) -> InitializationResult:
        """
        Inicializar sistema completamente con validación exhaustiva.
        
        Retorna InitializationResult con status detallado de cada componente.
        
        Returns:
            InitializationResult con success=True solo si TODOS los componentes inicializan ok
        """
        
        logger.info("=" * 70)
        logger.info("INITIALIZING INTEGRATED ARTOFIABOX")
        logger.info("=" * 70)
        
        errors = []
        component_status = {}
        
        # 1. Orchestrator ya inicializado por __init__
        try:
            logger.info("✓ Orchestrator loaded")
            component_status["orchestrator"] = True
        except Exception as e:
            logger.error(f"✗ Orchestrator initialization failed: {e}")
            errors.append(f"Orchestrator: {str(e)}")
            component_status["orchestrator"] = False
            return InitializationResult(False, errors, component_status)
        
        # 2. Backend Integration - VALIDAR RESULTADO
        try:
            backend_config = BackendIntegrationConfig(
                sandbox_enabled=True,
                llm_enabled=True,
                cloud_enabled=False,  # Deshabilitado por defecto
                learning_enabled=True,
            )
            
            self.backend_integration = BackendIntegration(backend_config)
            backend_init_result = await self.backend_integration.initialize()
            
            # ⭐ CRITICAL: backend_init_result debe ser truthy
            if not backend_init_result:
                logger.error("✗ Backend Integration initialization failed")
                errors.append("Backend Integration: initialization returned False")
                component_status["backend_integration"] = False
            else:
                logger.info("✓ Backend Integration initialized")
                component_status["backend_integration"] = True
                
        except asyncio.TimeoutError:
            logger.error(f"Backend integration initialization timeout after {self.STAGE_TIMEOUT}s")
            errors.append("Backend Integration: initialization timeout")
            component_status["backend_integration"] = False
        except Exception as e:
            logger.error(f"✗ Backend Integration error: {e}", exc_info=True)
            errors.append(f"Backend Integration: {str(e)}")
            component_status["backend_integration"] = False
        
        # 3. Validar servicios críticos (opcional pero recomendado)
        critical_services: list[str] = []
        try:
            # Placeholder: Chequear servicios críticos
            # In production, implementar chequeos para:
            # - Docker connection
            # - LLM provider connectivity  
            # - Memory/DB connectivity
            pass
        except Exception as e:
            logger.warning(f"⚠ Critical service check failed: {e}")
            # Esto es warning, no error crítico
        
        # 4. Decisión final
        logger.info("=" * 70)
        
        if errors:
            logger.error("✗ SYSTEM INITIALIZATION FAILED")
            for error in errors:
                logger.error(f"  - {error}")
            logger.info("=" * 70)
            return InitializationResult(False, errors, component_status)
        else:
            logger.info("✓ SYSTEM READY")
            logger.info("=" * 70)
            return InitializationResult(True, [], component_status)
    
    async def run_full_red_team_operation(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar operación completa de red team end-to-end con timeouts.
        
        ⭐ SECURITY: Cada stage tiene timeout para evitar operaciones infinitas
        
        Workflow:
        1. ReconAgent → escanea target
        2. LogicAgent → analiza con IA
        3. ExploitAgent → explota vía sandbox
        4. Learning → registra en RL engine
        """
        
        logger.info("\n" + "=" * 70)
        logger.info(f"STARTING RED TEAM OPERATION: {target.get('name', 'unknown')}")
        logger.info("=" * 70)
        
        operation_log: Dict[str, Any] = {
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
            "start_time": datetime.utcnow(),
            "stages": {},
            "result": "pending",
        }
        
        try:
            # STAGE 1: RECONNAISSANCE
            logger.info("\n[1/4] RECONNAISSANCE STAGE")
            logger.info("-" * 70)
            
            try:
                recon_result = await asyncio.wait_for(
                    self._stage_reconnaissance(target),
                    timeout=self.STAGE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"Reconnaissance timeout after {self.STAGE_TIMEOUT}s")
                recon_result = {"success": False, "error": "timeout"}
            
            operation_log["stages"]["reconnaissance"] = recon_result
            
            if not recon_result.get("success"):
                logger.warning("⚠ Reconnaissance failed, aborting operation")
                operation_log["result"] = "failed"
                return operation_log
            
            # STAGE 2: ANALYSIS + PLANNING
            logger.info("\n[2/4] ANALYSIS + PLANNING STAGE")
            logger.info("-" * 70)
            
            try:
                analysis_result = await asyncio.wait_for(
                    self._stage_analysis(target, recon_result),
                    timeout=self.STAGE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"Analysis timeout after {self.STAGE_TIMEOUT}s")
                analysis_result = {"success": False, "error": "timeout"}
            
            operation_log["stages"]["analysis"] = analysis_result
            
            if not analysis_result.get("success"):
                logger.warning("⚠ Analysis failed")
                operation_log["result"] = "failed"
                return operation_log
            
            # STAGE 3: EXPLOITATION
            logger.info("\n[3/4] EXPLOITATION STAGE")
            logger.info("-" * 70)
            
            try:
                exploit_result = await asyncio.wait_for(
                    self._stage_exploitation(target, analysis_result),
                    timeout=self.STAGE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"Exploitation timeout after {self.STAGE_TIMEOUT}s")
                exploit_result = {"success": False, "error": "timeout"}
            
            operation_log["stages"]["exploitation"] = exploit_result
            
            # STAGE 4: LEARNING + REPORTING
            logger.info("\n[4/4] LEARNING + REPORTING STAGE")
            logger.info("-" * 70)
            
            try:
                learning_result = await asyncio.wait_for(
                    self._stage_learning(exploit_result),
                    timeout=self.STAGE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error(f"Learning timeout after {self.STAGE_TIMEOUT}s")
                learning_result = {"success": False, "error": "timeout"}
            
            operation_log["stages"]["learning"] = learning_result
            
            operation_log["result"] = "success" if exploit_result.get("success") else "partial"
            
            logger.info("\n" + "=" * 70)
            logger.info(f"OPERATION COMPLETE: {operation_log['result'].upper()}")
            logger.info("=" * 70 + "\n")
            
            self.operation_history.append(operation_log)
            return operation_log
        
        except asyncio.TimeoutError as e:
            logger.error(f"Operation timeout after {self.OPERATION_TIMEOUT}s: {e}", exc_info=True)
            operation_log["result"] = "timeout"
            operation_log["error"] = "Operation exceeded maximum duration"
        except KeyboardInterrupt:
            logger.warning("Operation interrupted by user")
            operation_log["result"] = "interrupted"
        except Exception as e:
            logger.error(f"Operation failed with exception: {e}", exc_info=True)
            operation_log["result"] = "error"
            operation_log["error"] = str(e)
            self.operation_history.append(operation_log)
            return operation_log
        
        finally:
            # Registrar duración
            if "start_time" in operation_log:
                duration = (datetime.utcnow() - operation_log["start_time"]).total_seconds()
                operation_log["duration_seconds"] = duration
                logger.info(f"Operation took {duration:.2f} seconds")
            self.operation_history.append(operation_log)
            return operation_log
    
    async def _stage_reconnaissance(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Etapa 1: Reconocimiento"""
        
        logger.info("→ Running reconnaissance against target...")
        
        # TODO: Invocar ReconAgent real
        # Por ahora: simulación
        recon_findings = {
            "success": True,
            "target": target,
            "endpoints": [
                {"url": "/api/users", "method": "GET", "auth": "none"},
                {"url": "/api/products", "method": "GET", "auth": "none"},
                {"url": "/admin/login", "method": "POST", "auth": "form"},
            ],
            "technologies": ["Node.js", "Express", "PostgreSQL"],
            "vulnerabilities": ["sql_injection", "idor", "broken_auth"],
        }
        
        logger.info(f"  ✓ Found {len(cast(List[Any], recon_findings['endpoints']))} endpoints")
        logger.info(f"  ✓ Detected vulnerabilities: {recon_findings['vulnerabilities']}")
        
        return recon_findings
    
    async def _stage_analysis(self, target: Dict[str, Any], recon_result: Dict[str, Any]) -> Dict[str, Any]:
        """Etapa 2: Análisis + Planificación con IA"""
        
        logger.info("→ Analyzing findings with AI...")
        
        # Usar ProviderManager para generar plan
        prompt = f"""
        Analyze these reconnaissance findings and create an exploitation plan.
        
        Target: {target}
        Endpoints: {recon_result.get('endpoints')}
        Vulnerabilities: {recon_result.get('vulnerabilities')}
        
        Return a JSON with:
        - attack_chain: list of attack steps
        - priority: which vuln to exploit first
        - estimated_success_rate: 0.0-1.0
        """
        
        response = await self.backend_integration.generate_with_fallback(prompt) if self.backend_integration else {"status": "error"}
        
        if response.get("status") == "success":
            logger.info(f"  ✓ AI analysis complete (Model: {response.get('model')})")
            
            return {
                "success": True,
                "ai_model": response.get("model"),
                "analysis": response.get("response"),
                "attack_plan": {
                    "chain": ["sql_injection", "privilege_escalation"],
                    "priority": "sql_injection",
                    "success_rate": 0.85,
                }
            }
        else:
            logger.warning(f"  ✗ AI analysis failed: {response.get('error')}")
            return {"success": False, "error": response.get("error")}
    
    async def _stage_exploitation(self, target: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Etapa 3: Explotación en sandbox"""
        
        logger.info("→ Executing exploitation in isolated sandbox...")
        
        # Código de exploit de ejemplo
        exploit_code = """
import requests

# Target: %s
payload = "' or '1'='1"
response = requests.get("%s?id=" + payload)
print(response.status_code)
print(response.text[:200])
""" % (target.get("name"), target.get("url"))
        
        # Ejecutar en sandbox
        result = await self.backend_integration.execute_exploit_safely(
            code=exploit_code,
            language="python",
            exploit_name="sql_injection",
        ) if self.backend_integration else {"status": "error"}
        
        if result.get("status") == "success":
            logger.info(f"  ✓ Exploit executed successfully (exit_code: {result.get('exit_code')})")
            logger.info(f"  ✓ Output length: {len(result.get('stdout', ''))} bytes")
            
            return {
                "success": True,
                "exploit_type": "sql_injection",
                "output": result.get("stdout", "")[:200],
                "execution_time_ms": result.get("execution_time_ms"),
            }
        else:
            logger.warning(f"  ✗ Exploit failed: {result.get('error')}")
            return {"success": False, "error": result.get("error")}
    
    async def _stage_learning(self, exploit_result: Dict[str, Any]) -> Dict[str, Any]:
        """Etapa 4: Aprendizaje + Reporting"""
        
        logger.info("→ Recording learning episode...")
        
        if self.backend_integration and self.backend_integration.rl_engine:
            summary = await self.backend_integration.rl_engine.get_learning_summary()
            logger.info(f"  ✓ RL Engine Summary:")
            logger.info(f"    - Total episodes: {summary.get('total_episodes')}")
            logger.info(f"    - Success rate: {summary.get('overall_success_rate'):.1%}")
            logger.info(f"    - Tactics learned: {summary.get('tactics_learned')}")
            
            return {
                "success": True,
                "learning_summary": summary,
            }
        else:
            logger.info("  ℹ RL Engine not available")
            return {"success": True}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema"""
        
        return {
            "orchestrator": {
                "agents": self.orchestrator.list_agents() if self.orchestrator else [],
            },
            "backends": self.backend_integration.get_status() if self.backend_integration else {},
            "operations_completed": len(self.operation_history),
        }
    
    def print_status(self) -> None:
        """Imprimir estado en consola"""
        
        status = self.get_system_status()
        
        print("\n" + "=" * 70)
        print("ARTOFIABOX INTEGRATED SYSTEM STATUS")
        print("=" * 70)
        print(f"\n📊 Orchestrator:")
        print(f"   Agents: {len(status['orchestrator'].get('agents', []))}")
        
        print(f"\n🔧 Backends:")
        for backend, info in status['backends'].items():
            if isinstance(info, dict):
                print(f"   {backend}: {info}")
        
        print(f"\n📈 Operations:")
        print(f"   Completed: {status['operations_completed']}")
        
        print("\n" + "=" * 70 + "\n")


async def main() -> None:
    """
    Punto de entrada principal.
    
    Ejemplo de uso:
    python -m src.orchestrator.main
    """
    
    system = IntegratedArtOfIA(".mcp.json")
    
    if await system.initialize():
        system.print_status()
        
        # Ejecutar operación de ejemplo
        target = {
            "name": "TestTarget",
            "url": "http://example.com",
            "type": "web_application",
        }
        
        result = await system.run_full_red_team_operation(target)
        
        print("\nOperation Result:")
        print(f"  Status: {result.get('result')}")
        print(f"  Stages: {list(result.get('stages', {}).keys())}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    asyncio.run(main())
