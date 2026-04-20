"""
Backend Integration Layer - Conecta Backends con Agentes
=========================================================

Capa de integración que conecta:
- docker_sandbox ↔ ExploitAgent
- llm_providers ↔ LogicAgent
- self_evolving_engine ↔ Learning loop
- cloud_infrastructure ↔ SupplyChainAgent

Este módulo es el "pegante" entre infraestructura y agentes.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, cast
from dataclasses import dataclass
from datetime import datetime
from collections import deque  # ✅ Para bounded operation log

from src.backends.docker_sandbox import SandboxManager, SandboxConfig, WebSocketBridge, IORequest, IORequestType
from src.backends.llm_providers import ProviderManager, ModelType, ProviderConfig, FallbackEngine
from src.backends.cloud_infrastructure import AWSManager, InstanceConfig
from src.intelligence import SelfEvolvingEngine, AttackEpisode, LearningOutcome
from src.core.input_validator import CodeValidator, FilenameValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class BackendIntegrationConfig:
    """Configuración centralizada de todos los backends"""
    sandbox_enabled: bool = True
    llm_enabled: bool = True
    cloud_enabled: bool = True
    learning_enabled: bool = True
    
    # Sandbox
    sandbox_cpu_limits: str = "1"
    sandbox_memory_limits: str = "512m"
    sandbox_timeout_seconds: int = 300
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_endpoint: str = "http://localhost:11434"
    
    # AWS
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # Learning
    learning_capacity: int = 10000


class BackendIntegration:
    """
    Coordinador central de backends.
    
    Inicializa y coordina:
    1. SandboxManager (ejecuta exploits aislados)
    2. ProviderManager (IA inteligente con fallbacks)
    3. SelfEvolvingEngine (aprende de resultados)
    4. AWSManager (infraestructura en nube)
    """
    
    def __init__(self, config: BackendIntegrationConfig | None = None) -> None:
        self.config = config or BackendIntegrationConfig()
        
        # Backends
        self.sandbox_manager: Optional[SandboxManager] = None
        self.provider_manager: Optional[ProviderManager] = None
        self.fallback_engine: Optional[FallbackEngine] = None
        self.rl_engine: Optional[SelfEvolvingEngine] = None
        self.aws_manager: Optional[AWSManager] = None
        self.websocket_bridge: Optional[WebSocketBridge] = None
        
        self.initialized = False
        
        # ✅ FIXEO MEMORY LEAK: Usar deque bounded (últimas 500 operaciones)
        # Historial completo persiste en BD
        self.operation_log: deque[Dict[str, Any]] = deque(maxlen=500)
    
    async def initialize(self) -> bool:
        """
        Inicializar todos los backends.
        
        Retorna: True si todos inicializaron exitosamente
        """
        
        logger.info("Initializing Backend Integration Layer...")
        
        try:
            # 1. Sandbox
            if self.config.sandbox_enabled:
                sandbox_config = SandboxConfig(
                    cpu_limits=self.config.sandbox_cpu_limits,
                    memory_limits=self.config.sandbox_memory_limits,
                    timeout_seconds=self.config.sandbox_timeout_seconds,
                )
                self.sandbox_manager = SandboxManager(sandbox_config)
                if await self.sandbox_manager.initialize():
                    logger.info("✓ SandboxManager initialized")
                    self.websocket_bridge = WebSocketBridge(self.sandbox_manager)
                else:
                    logger.warning("✗ SandboxManager initialization failed")
            
            # 2. LLM Providers
            if self.config.llm_enabled:
                self.provider_manager = ProviderManager()
                
                configs = {}
                if self.config.openai_api_key:
                    configs[ModelType.OPENAI_GPT4] = ProviderConfig(
                        model_type=ModelType.OPENAI_GPT4,
                        api_key=self.config.openai_api_key,
                    )
                if self.config.anthropic_api_key:
                    configs[ModelType.ANTHROPIC_CLAUDE] = ProviderConfig(
                        model_type=ModelType.ANTHROPIC_CLAUDE,
                        api_key=self.config.anthropic_api_key,
                    )
                
                # Ollama siempre
                configs[ModelType.OLLAMA_LOCAL] = ProviderConfig(
                    model_type=ModelType.OLLAMA_LOCAL,
                    api_endpoint=self.config.ollama_endpoint,
                )
                
                if await self.provider_manager.initialize(configs):
                    logger.info("✓ ProviderManager initialized")
                    self.fallback_engine = FallbackEngine(self.provider_manager)
                else:
                    logger.warning("✗ ProviderManager initialization failed")
            
            # 3. Learning Engine
            if self.config.learning_enabled:
                self.rl_engine = SelfEvolvingEngine(self.config.learning_capacity)
                logger.info("✓ SelfEvolvingEngine initialized")
            
            # 4. AWS (opcional)
            if self.config.cloud_enabled and self.config.aws_access_key and self.config.aws_secret_key:
                self.aws_manager = AWSManager(
                    self.config.aws_access_key,
                    self.config.aws_secret_key,
                )
                logger.info("✓ AWSManager initialized")
            
            self.initialized = True
            logger.info("✓ Backend Integration Layer fully initialized")
            return True
        
        except Exception as e:
            logger.error(f"Backend initialization failed: {e}")
            return False
    
    async def execute_exploit_safely(self, code: str, language: str = "python",
                                    exploit_name: str = "unknown") -> Dict[str, Any]:
        """
        Ejecutar exploit en sandbox con comunicación segura.
        
        Pipeline:
        1. ✅ VALIDAR inputs (código, lenguaje, nombre)
        2. Crear contenedor
        3. Inyectar código vía WebSocketBridge
        4. Monitorear ejecución
        5. Limpiar
        6. Registrar en RL engine
        """
        
        if not self.sandbox_manager:
            return {"status": "error", "error": "Sandbox not available"}
        
        # ✅ SECURITY: Validar TODOS los inputs ANTES de cualquier operación
        try:
            # Validar código
            code_validator = CodeValidator()
            code_validation = code_validator.validate(code)
            if not code_validation.valid:
                error_msg = "; ".join([str(e) for e in code_validation.errors])
                logger.warning(f"✗ Code validation failed: {error_msg}")
                return {"status": "error", "error": f"Code validation failed: {error_msg}"}
            
            # Validar nombre de exploit
            name_validator = FilenameValidator()
            name_validation = name_validator.validate(exploit_name)
            if not name_validation.valid:
                error_msg = "; ".join([str(e) for e in name_validation.errors])
                logger.warning(f"✗ Exploit name validation failed: {error_msg}")
                return {"status": "error", "error": f"Exploit name validation failed: {error_msg}"}
            
            logger.info(f"✓ All inputs validated successfully for exploit: {exploit_name}")
        
        except Exception as e:
            logger.error(f"✗ Critical error during input validation: {e}")
            return {"status": "error", "error": f"Validation error: {str(e)}"}
        
        try:
            # 1. Crear contenedor
            container_id = await self.sandbox_manager.create_container(code)
            logger.info(f"Container created: {container_id}")
            
            # 2. Ejecutar vía bridge
            if not self.websocket_bridge:
                return {"status": "error", "error": "WebSocket bridge not initialized"}
            
            request = IORequest(
                request_id=f"exploit_{exploit_name}_{container_id}",
                request_type=IORequestType.EXECUTE_CODE,
                payload={
                    "code": code,
                    "language": language,
                    "container_id": container_id,
                },
                timeout_seconds=self.config.sandbox_timeout_seconds,
            )
            
            response = await self.websocket_bridge.execute_in_container(request)
            
            # 3. Cleanup
            await self.sandbox_manager.cleanup_container(container_id)
            
            # 4. Registrar en RL engine
            if self.rl_engine and response.status.value == "success":
                episode = AttackEpisode(
                    attack_type="exploit",
                    technique=exploit_name,
                    target_os="unknown",
                    edr_type="unknown",
                    parameters={"language": language},
                    outcome=LearningOutcome.SUCCESS if response.exit_code == 0 else LearningOutcome.ERROR,
                    confidence_score=0.95 if response.exit_code == 0 else 0.3,
                    duration_ms=response.execution_time_ms,
                )
                await self.rl_engine.record_attack_outcome(episode)
            
            # Log operation
            await self._log_operation("execute_exploit", {
                "exploit_name": exploit_name,
                "status": response.status.value,
                "exit_code": response.exit_code,
                "duration_ms": response.execution_time_ms,
            })
            
            return {
                "status": response.status.value,
                "stdout": response.stdout,
                "stderr": response.stderr,
                "exit_code": response.exit_code,
                "execution_time_ms": response.execution_time_ms,
            }
        
        except Exception as e:
            logger.error(f"Exploit execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_with_fallback(self, prompt: str, model_preference: Optional[ModelType] = None) -> Dict[str, Any]:
        """
        Generar contenido de IA con fallback automático.
        
        Si OpenAI rechaza → intenta Anthropic → Ollama (sin censura)
        """
        
        if not self.provider_manager:
            return {"status": "error", "error": "LLM provider not available"}
        
        try:
            response = await self.provider_manager.invoke(
                prompt=prompt,
                model_preference=model_preference,
                max_tokens=2000,
            )
            
            # Log
            await self._log_operation("generate_content", {
                "model": response.get("model", "unknown"),
                "status": response.get("status"),
            })
            
            return response
        
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_recommended_techniques(self, attack_type: str, target_os: str,
                                        edr_type: str) -> list[str]:
        """
        Obtener técnicas recomendadas basadas en aprendizaje pasado.
        """
        
        if not self.rl_engine:
            return []
        
        techniques_data = await self.rl_engine.get_recommended_techniques(attack_type, target_os, edr_type)
        return [t.get("name", "") for t in techniques_data if isinstance(t, dict)]
    
    async def create_external_infrastructure(self, attack_type: str) -> Optional[Dict[str, Any]]:
        """
        Crear infraestructura externa en AWS para ataque.
        """
        
        if not self.aws_manager:
            logger.warning("AWS manager not available")
            return None
        
        try:
            config = InstanceConfig()
            instance = await self.aws_manager.create_attack_infrastructure(config)
            
            if instance["status"] == "success":
                await self._log_operation("create_aws_instance", instance["instance"])
                return cast(Dict[str, Any], instance["instance"])
            
            return None
        
        except Exception as e:
            logger.error(f"AWS infrastructure creation failed: {e}")
            return None
    
    async def destroy_external_infrastructure(self, instance_id: str) -> bool:
        """Destruir instancia AWS"""
        
        if not self.aws_manager:
            return False
        
        return await self.aws_manager.destroy_instance(instance_id)
    
    async def _log_operation(self, op_name: str, details: Dict[str, Any]) -> None:
        """Registrar operación en log"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": op_name,
            "details": details,
        }
        self.operation_log.append(log_entry)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los backends"""
        
        return {
            "initialized": self.initialized,
            "sandbox": {
                "enabled": self.sandbox_manager is not None,
                "active_containers": len(self.sandbox_manager.active_containers) if self.sandbox_manager else 0,
            },
            "llm_providers": self.provider_manager.get_provider_status() if self.provider_manager else {},
            "learning": {
                "enabled": self.rl_engine is not None,
                "total_episodes": len(self.rl_engine.episode_history) if self.rl_engine else 0,
            },
            "aws": {
                "enabled": self.aws_manager is not None,
                "active_instances": len(self.aws_manager.active_instances) if self.aws_manager else 0,
            },
        }
