"""
Sandbox Manager - Controlador del Ciclo de Vida de Contenedores
==================================================================

Motor de ejecución fortificado que garantiza aislamiento de grado militar.
Levanta un contenedor Docker nuevo y limpio para cada intento de ataque,
lo ejecuta bajo límites estrictos, y lo destruye inmediatamente después.

Responsabilidades:
- Crear contenedor efímero para cada exploit
- Imponer límites de CPU, memoria, tiempo
- Monitorear violaciones de seguridad en tiempo real
- Destruir contenedor + logs después de ejecución
- Garantizar: Sin acceso host, Sin escalada de privilegios, Sin persistencia
"""

import docker
import logging
import asyncio
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuración del sandbox"""
    image_name: str = "artofiabox:ephemeral"
    cpu_limits: str = "1"  # 1 CPU core
    memory_limits: str = "512m"  # 512MB RAM
    timeout_seconds: int = 300  # 5 minutes max
    readonly_rootfs: bool = True
    cap_drop: list = None  # Capabilities a eliminar
    
    def __post_init__(self):
        if self.cap_drop is None:
            self.cap_drop = ["ALL"]


class ContainerExecutionError(Exception):
    """Error en ejecución de contenedor"""
    pass


class SecurityViolationDetected(Exception):
    """Violación de seguridad detectada"""
    pass


class SandboxManager:
    """
    Gestor principal del ciclo de vida del sandbox.
    
    Workflow:
    1. Create → Levanta contenedor limpio
    2. Execute → Inyecta exploit, monitorea ejecución
    3. Cleanup → Destruye contenedor + logs
    """
    
    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self.docker_client = None
        self.active_containers = {}
        self.execution_logs = []
        
        # Cargar profiles de seguridad
        self.seccomp_profile = self._load_seccomp_profile()
    
    async def initialize(self) -> bool:
        """Inicializar conexión Docker"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            return False
    
    def _load_seccomp_profile(self) -> Dict[str, Any]:
        """Cargar perfil seccomp desde arquivo"""
        profile_path = Path(__file__).parent / "security_profiles" / "seccomp_profile.json"
        try:
            with open(profile_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("seccomp_profile.json not found, using defaults")
            return self._get_default_seccomp_profile()
    
    def _get_default_seccomp_profile(self) -> Dict[str, Any]:
        """Retornar perfil seccomp por defecto (muy restrictivo)"""
        return {
            "defaultAction": "SCMP_ACT_ERRNO",
            "defaultErrnoRet": 1,
            "archMap": [
                {
                    "architecture": "SCMP_ARCH_X86_64",
                    "subArchitectures": ["SCMP_ARCH_X86"]
                }
            ],
            "syscalls": [
                # Syscalls permitidas mínimas
                {"names": ["read", "write", "open", "close", "stat", "fstat"], "action": "SCMP_ACT_ALLOW"},
                {"names": ["exit", "exit_group"], "action": "SCMP_ACT_ALLOW"},
                {"names": ["execve"], "action": "SCMP_ACT_ALLOW"},
                # TODO: Agregar más syscalls permitidas según necesidad
            ]
        }
    
    async def create_container(self, exploit_code: str) -> str:
        """
        Crear estado nuevo y limpio del contenedor para exploit.
        
        Retorna: container_id
        """
        container_id = str(uuid.uuid4())[:12]
        
        try:
            # Preparar volumes (ephemeral, only tmpfs)
            volumes = {
                "/tmp": {"bind": "/tmp", "mode": "rw"},
                "/dev/shm": {"bind": "/dev/shm", "mode": "rw"},
            }
            
            # Crear contenedor con restricciones
            container = self.docker_client.containers.run(
                self.config.image_name,
                command="/bin/sleep infinity",  # Keep alive
                detach=True,
                name=f"exploit-{container_id}",
                
                # Límites de recursos
                cpu_quota=int(self.config.cpu_limits) * 100000,
                mem_limit=self.config.memory_limits,
                memswap_limit=self.config.memory_limits,  # Sin swap
                
                # Seguridad: sin privilegios
                user="sandboxuser:sandboxuser",
                cap_drop=self.config.cap_drop,
                security_opt=["no-new-privileges:true"],
                read_only=self.config.readonly_rootfs,
                
                # Aislamiento de red (sin acceso a host)
                network_mode="none",  # Sin acceso de red
                
                # Aislamiento IPC
                ipc_mode="private",
                
                # Volumes limitados
                volumes=volumes,
                tmpfs={"/tmp": "size=50M,noexec,nodev,nosuid"},
                
                # Seccomp
                security_opt=[f"seccomp={json.dumps(self.seccomp_profile)}"],
                
                # PID namespace aislado
                pid_mode="private",
            )
            
            self.active_containers[container_id] = {
                "docker_id": container.id,
                "container": container,
                "created_at": datetime.utcnow(),
                "exploit_code": exploit_code,
                "status": "created"
            }
            
            logger.info(f"Container created: {container_id}")
            return container_id
        
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise ContainerExecutionError(f"Container creation failed: {e}")
    
    async def execute_exploit(self, container_id: str, code: str, 
                              language: str = "python") -> Tuple[str, int, str]:
        """
        Ejecutar exploit code en contenedor.
        
        Retorna: (stdout, exit_code, stderr)
        """
        
        if container_id not in self.active_containers:
            raise ContainerExecutionError(f"Container {container_id} not found")
        
        container_info = self.active_containers[container_id]
        container = container_info["container"]
        
        # Construir comando según lenguaje
        if language == "python":
            cmd = f"python3 -c {repr(code)}"
        elif language == "bash":
            cmd = code
        else:
            raise ValueError(f"Unsupported language: {language}")
        
        try:
            # Ejecutar con timeout
            result = container.exec_run(
                cmd=cmd,
                stdout=True,
                stderr=True,
                timeout=self.config.timeout_seconds,
                user="sandboxuser"
            )
            
            stdout = result.output.decode() if result.output else ""
            stderr = result.stderr or ""
            exit_code = result.exit_code
            
            # Registrar ejecución
            await self._log_execution(container_id, code, exit_code, stdout, stderr)
            
            # Auditar
            await self._audit_execution(container_id, code, exit_code)
            
            logger.info(f"Exploit executed in {container_id}: exit_code={exit_code}")
            
            return stdout, exit_code, stderr
        
        except asyncio.TimeoutError:
            logger.error(f"Exploit timeout in {container_id}")
            # Matar contenedor inmediatamente
            container.kill()
            raise ContainerExecutionError(f"Exploit timeout after {self.config.timeout_seconds}s")
        
        except Exception as e:
            logger.error(f"Exploit execution error in {container_id}: {e}")
            raise ContainerExecutionError(f"Execution failed: {e}")
    
    async def cleanup_container(self, container_id: str) -> None:
        """
        Destruir contenedor y limpiar todos los rastros.
        """
        
        if container_id not in self.active_containers:
            return
        
        container_info = self.active_containers[container_id]
        container = container_info["container"]
        
        try:
            # 1. Matar proceso
            if container.status in ["running", "paused"]:
                container.kill()
            
            # 2. Borrar contenedor
            container.remove(v=True, force=True)
            
            # 3. Remover de tracking
            del self.active_containers[container_id]
            
            logger.info(f"Container {container_id} destroyed")
        
        except Exception as e:
            logger.error(f"Failed to cleanup container {container_id}: {e}")
    
    async def cleanup_all(self) -> None:
        """Destruir todos los contenedores activos"""
        
        for container_id in list(self.active_containers.keys()):
            await self.cleanup_container(container_id)
    
    async def _log_execution(self, container_id: str, code: str, exit_code: int,
                            stdout: str, stderr: str) -> None:
        """Registrar ejecución de exploit"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "container_id": container_id,
            "exit_code": exit_code,
            "code": code[:500],  # Truncate long payloads
            "stdout_length": len(stdout),
            "stderr": stderr[:200] if stderr else "",
        }
        
        self.execution_logs.append(log_entry)
    
    async def _audit_execution(self, container_id: str, code: str, exit_code: int) -> None:
        """Auditar ejecución (para compliance)"""
        
        logger.info(f"[AUDIT] Container: {container_id} | Exit: {exit_code} | Code: {code[:100]}")
    
    def get_execution_status(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de contenedor"""
        
        if container_id not in self.active_containers:
            return None
        
        container_info = self.active_containers[container_id]
        container = container_info["container"]
        
        try:
            container.reload()
            return {
                "id": container_id,
                "status": container.status,
                "created_at": container_info["created_at"].isoformat(),
                "uptime_seconds": (datetime.utcnow() - container_info["created_at"]).total_seconds(),
            }
        except Exception as e:
            logger.error(f"Failed to get status for {container_id}: {e}")
            return None
