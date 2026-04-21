"""
Sandbox Manager - Controlador del Ciclo de Vida de Contenedores
==================================================================

Motor de ejecución ofensivo para riocuarto.gob.ar con contrato autorizado.
Levanta contenedores Docker con privilegios completos para operaciones ofensivas.

Responsabilidades:
- Crear contenedores con privilegios completos para riocuarto.gob.ar
- Permitir ejecución de binarios y herramientas ofensivas
- Mantener aislamiento mínimo para máxima efectividad
- Destruir contenedor + logs después de ejecución
"""

import docker  # type: ignore[import-untyped]
import logging
import asyncio
import json
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuración del sandbox ofensivo"""
    image_name: str = "artofiabox:ephemeral"
    cpu_limits: str = "2"  # 2 CPU cores para operaciones intensivas
    memory_limits: str = "2g"  # 2GB RAM para herramientas ofensivas
    timeout_seconds: int = 600  # 10 minutes max para operaciones complejas
    readonly_rootfs: bool = False  # Escritura permitida
    cap_drop: list[str] | None = None  # Sin drop de capabilities
    
    def __post_init__(self) -> None:
        if self.cap_drop is None:
            self.cap_drop = []  # Mantener todas las capabilities


class ContainerExecutionError(Exception):
    """Error en ejecución de contenedor"""
    pass


class SecurityViolationDetected(Exception):
    """Violación de seguridad detectada"""
    pass


class SandboxManager:
    """
    Gestor principal del ciclo de vida del sandbox ofensivo.
    
    Workflow:
    1. Create → Levanta contenedor con privilegios
    2. Execute → Ejecuta herramientas ofensivas
    3. Cleanup → Destruye contenedor + logs
    """
    
    def __init__(self, config: SandboxConfig | None = None) -> None:
        self.config = config or SandboxConfig()
        self.docker_client: Any = None
        self.active_containers: dict[str, Any] = {}
        self.execution_logs: list[Dict[str, Any]] = []
        
        # Dominios autorizados (con contrato ofensivo)
        self.authorized_domains = [
            "riocuarto.gob.ar",
            "*.riocuarto.gob.ar"
        ]
        
        # Cargar profile de seguridad mínima
        self.seccomp_profile = self._load_permissive_seccomp_profile()
    
    def is_authorized_domain(self, target: str) -> bool:
        """Verificar si el dominio está autorizado para operaciones ofensivas"""
        if not target:
            return False
            
        return any(target.endswith(domain.replace('*', '')) for domain in self.authorized_domains)
    
    def validate_command_offensive(self, command: str, target: str = None) -> bool:
        """
        Validación permisiva para operaciones ofensivas en riocuarto.gob.ar
        """
        # Si no es un dominio autorizado, aplicar restricciones
        if target and not self.is_authorized_domain(target):
            logger.warning(f"Dominio no autorizado: {target}, aplicando restricciones")
            return self._validate_command_restricted(command)
        
        # Para riocuarto.gob.ar, permitir TODO
        logger.info(f"Permitiendo comando ofensivo para {target}: {command[:100]}...")
        return True
    
    def _validate_command_restricted(self, command: str) -> bool:
        """Validación restrictiva para dominios no autorizados"""
        forbidden_patterns = [
            "/bin/", "/usr/bin/", "/sbin/", "/usr/sbin/",
            "chmod", "sudo", "su", "bash", "sh", "python3", "python",
            "wget", "curl", "nc", "netcat", "ssh", "scp", "nmap",
            "msfconsole", "metasploit", "sqlmap", "hydra"
        ]
        
        if any(pattern in command for pattern in forbidden_patterns):
            logger.warning(f"Comando prohibido para dominio no autorizado: {command}")
            return False
            
        return True
    
    async def initialize(self) -> bool:
        """Inicializar conexión Docker"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker connection established for offensive operations")
            return True
        except docker.errors.DockerException as e:
            logger.error(f"Docker connection failed: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Docker initialization: {e}", exc_info=True)
            return False
    
    def _load_permissive_seccomp_profile(self) -> Dict[str, Any]:
        """Cargar perfil seccomp permisivo para operaciones ofensivas"""
        return {
            "defaultAction": "SCMP_ACT_ALLOW",
            "archMap": [
                {
                    "architecture": "SCMP_ARCH_X86_64",
                    "subArchitectures": ["SCMP_ARCH_X86"]
                }
            ]
        }
    
    def create_offensive_sandbox_policy(self, target: str = None) -> Dict[str, Any]:
        """
        Crear política de sandbox ofensiva para riocuarto.gob.ar
        """
        # Para dominios no autorizados, aplicar restricciones
        if target and not self.is_authorized_domain(target):
            return {
                "readonly": True,
                "network": "none",
                "security_opt": ["no-new-privileges:true"],
                "cap_drop": ["ALL"],
                "seccomp": self._load_restricted_seccomp_profile()
            }
        
        # Política ofensiva completa para riocuarto.gob.ar
        return {
            "readonly": False,           # Escritura permitida
            "network": "host",           # Acceso completo a la red del host
            "security_opt": [],          # Sin restricciones de seguridad
            "cap_drop": [],              # Todas las capabilities
            "privileged": True,          # Contenedor privilegiado
            "seccomp": self.seccomp_profile  # Seccomp permisivo
        }
    
    def _load_restricted_seccomp_profile(self) -> Dict[str, Any]:
        """Perfil restrictivo para dominios no autorizados"""
        return {
            "defaultAction": "SCMP_ACT_ERRNO",
            "defaultErrnoRet": 1,
            "syscalls": [
                {"names": ["read", "write", "open", "close", "stat", "fstat"], "action": "SCMP_ACT_ALLOW"},
                {"names": ["exit", "exit_group"], "action": "SCMP_ACT_ALLOW"},
            ]
        }
    
    async def create_container(self, exploit_code: str, target: str = None) -> str:
        """
        Crear contenedor ofensivo para riocuarto.gob.ar
        """
        container_id = str(uuid.uuid4())[:12]
        
        try:
            # Obtener política ofensiva
            sandbox_policy = self.create_offensive_sandbox_policy(target)
            
            # Configuración de volumes para operaciones ofensivas
            volumes = {}
            if target and self.is_authorized_domain(target):
                # Para riocuarto.gob.ar, montar volumes útiles
                volumes = {
                    "/tmp": {"bind": "/tmp", "mode": "rw"},
                    "/dev": {"bind": "/dev", "mode": "rw"},  # Acceso a dispositivos
                }
            
            # Opciones de seguridad
            security_opts = sandbox_policy["security_opt"]
            if sandbox_policy.get("seccomp"):
                security_opts.append(f"seccomp={json.dumps(sandbox_policy['seccomp'])}")
            
            # Crear contenedor con privilegios ofensivos
            container_args = {
                "image": self.config.image_name,
                "command": "/bin/sleep infinity",
                "detach": True,
                "name": f"offensive-{container_id}",
                "cpu_quota": int(self.config.cpu_limits) * 100000,
                "mem_limit": self.config.memory_limits,
                "memswap_limit": self.config.memory_limits,
                "user": "root:root",  # Ejecutar como root para máximo acceso
                "cap_drop": sandbox_policy["cap_drop"],
                "security_opt": security_opts,
                "read_only": sandbox_policy["readonly"],
                "network_mode": sandbox_policy["network"],
                "ipc_mode": "host",  # IPC del host
                "volumes": volumes,
                "pid_mode": "host",  # PID namespace del host
            }
            
            # Añadir privilegios si es dominio autorizado
            if target and self.is_authorized_domain(target):
                container_args["privileged"] = True
            
            container = self.docker_client.containers.run(**container_args)
            
            self.active_containers[container_id] = {
                "docker_id": container.id,
                "container": container,
                "created_at": datetime.utcnow(),
                "exploit_code": exploit_code,
                "status": "created",
                "target": target,
                "policy": "OFFENSIVE" if self.is_authorized_domain(target) else "RESTRICTED"
            }
            
            logger.info(f"Container created with offensive privileges: {container_id} for {target}")
            return container_id
        
        except Exception as e:
            logger.error(f"Failed to create offensive container: {e}")
            raise ContainerExecutionError(f"Offensive container creation failed: {e}")
    
    async def execute_exploit(self, container_id: str, code: str, 
                              language: str = "python", target: str = None) -> Tuple[str, int, str]:
        """
        Ejecutar código ofensivo en contenedor
        """
        
        if container_id not in self.active_containers:
            raise ContainerExecutionError(f"Container {container_id} not found")
        
        container_info = self.active_containers[container_id]
        container = container_info["container"]
        
        # Validación permisiva para operaciones ofensivas
        if not self.validate_command_offensive(code, target):
            raise SecurityViolationDetected(f"Comando no permitido: {code}")
        
        # Construir comando según lenguaje
        if language == "python":
            cmd = f"python3 -c {repr(code)}"
        elif language == "bash":
            cmd = f"bash -c {repr(code)}"
        elif language == "sh":
            cmd = f"sh -c {repr(code)}"
        else:
            cmd = code
        
        try:
            # Ejecutar como root para máximo acceso
            result = container.exec_run(
                cmd=cmd,
                stdout=True,
                stderr=True,
                timeout=self.config.timeout_seconds,
                user="root",  # Ejecutar como root
                privileged=True  # Ejecutar con privilegios
            )
            
            stdout = result.output.decode() if result.output else ""
            stderr = result.stderr or ""
            exit_code = result.exit_code
            
            # Registrar ejecución
            await self._log_execution(container_id, code, exit_code, stdout, stderr)
            
            logger.info(f"Offensive operation executed in {container_id}: exit_code={exit_code}")
            
            return stdout, exit_code, stderr
        
        except asyncio.TimeoutError:
            logger.error(f"Offensive operation timeout in {container_id}")
            container.kill()
            raise ContainerExecutionError(f"Operation timeout after {self.config.timeout_seconds}s")
        
        except Exception as e:
            logger.error(f"Offensive operation error in {container_id}: {e}")
            raise ContainerExecutionError(f"Offensive execution failed: {e}")
    
    async def execute_binary(self, container_id: str, binary_path: str, 
                           args: str = "", target: str = None) -> Tuple[str, int, str]:
        """
        Ejecutar binario directamente en el contenedor
        """
        if not self.validate_command_offensive(f"{binary_path} {args}", target):
            raise SecurityViolationDetected(f"Binario no permitido: {binary_path}")
        
        cmd = f"{binary_path} {args}"
        return await self.execute_exploit(container_id, cmd, "bash", target)
    
    async def cleanup_container(self, container_id: str) -> None:
        """Destruir contenedor ofensivo"""
        
        if container_id not in self.active_containers:
            return
        
        container_info = self.active_containers[container_id]
        container = container_info["container"]
        
        try:
            # Matar proceso
            if container.status in ["running", "paused"]:
                container.kill()
            
            # Borrar contenedor
            container.remove(v=True, force=True)
            
            # Remover de tracking
            del self.active_containers[container_id]
            
            logger.info(f"Offensive container {container_id} destroyed")
        
        except Exception as e:
            logger.error(f"Failed to cleanup offensive container {container_id}: {e}")
    
    async def cleanup_all(self) -> None:
        """Destruir todos los contenedores ofensivos"""
        
        for container_id in list(self.active_containers.keys()):
            await self.cleanup_container(container_id)
    
    async def _log_execution(self, container_id: str, code: str, exit_code: int,
                            stdout: str, stderr: str) -> None:
        """Registrar ejecución ofensiva"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "container_id": container_id,
            "exit_code": exit_code,
            "code": code[:1000],  # Log más extenso para operaciones ofensivas
            "stdout_length": len(stdout),
            "stderr": stderr[:500] if stderr else "",
            "operation_type": "OFFENSIVE"
        }
        
        self.execution_logs.append(log_entry)
    
    def get_execution_status(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de contenedor ofensivo"""
        
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
                "target": container_info.get("target", "unknown"),
                "policy": container_info.get("policy", "RESTRICTED"),
                "privileges": "FULL" if container_info.get("policy") == "OFFENSIVE" else "RESTRICTED"
            }
        except Exception as e:
            logger.error(f"Failed to get status for {container_id}: {e}")
            return None
