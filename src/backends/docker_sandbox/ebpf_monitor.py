"""
eBPF Monitor - Vigilancia en Tiempo Real de Syscalls
=====================================================

Monitor "sidecar" que utiliza eBPF (Extended Berkeley Packet Filter) 
para vigilar llamadas al sistema del contenedor en tiempo real.

Detecta y bloquea instantáneamente:
- Inyección de código en memoria (ptrace, process_vm_write)
- Ejecución fileless (ejecución desde /dev/shm)
- Escalada de privilegios (setuid, setgid)
- Alteración de procesos (execve no autorizado)
- Acceso a red (socket prohibido en modo network_mode=none)

Behavioral Baseline: El monitor establece un perfil de comportamiento esperado
y desactiva el contenedor si se detectan desviaciones.
"""

import logging
from typing import Dict, List, Callable, Optional, Any, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class SyscallCategory(str, Enum):
    """Categorías de syscalls"""
    MEMORY_INJECTION = "memory_injection"  # ptrace, process_vm_*
    NETWORK = "network"  # socket, connect
    FILE_SYSTEM = "file_system"  # open, unlink
    PROCESS = "process"  # fork, clone, exec
    PRIVILEGE = "privilege"  # setuid, setgid, capset
    SYSTEM = "system"  # mount, reboot, sysctl


class ThreatLevel(str, Enum):
    """Nivel de amenaza detectada"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCK = "block"


@dataclass
class SyscallEvent:
    """Evento capturado de syscall"""
    syscall_name: str
    pid: int
    uid: int
    gid: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    args: Dict[str, Any] = field(default_factory=dict)
    return_value: int = 0
    errno: int = 0
    category: SyscallCategory = SyscallCategory.FILE_SYSTEM
    
    def is_blocked(self) -> bool:
        """¿Fue bloqueada esta syscall?"""
        return self.errno != 0


@dataclass
class SecurityBaseline:
    """Línea base de comportamiento esperado"""
    allowed_syscalls: List[str] = field(default_factory=list)
    allowed_pids: List[int] = field(default_factory=list)
    allowed_file_paths: List[str] = field(default_factory=list)
    max_child_processes: int = 10
    strict_mode: bool = True


class eBPFMonitor:
    """
    Monitor eBPF para vigilancia en tiempo real.
    
    En producción, esto se comunicaría con un kernel module o BCC
    (BPF Compiler Collection). Por ahora, simula monitoreo.
    """
    
    def __init__(self, container_id: str, baseline: SecurityBaseline | None = None) -> None:
        self.container_id = container_id
        self.baseline = baseline or SecurityBaseline()
        self.enabled = True
        self.events: list[SyscallEvent] = []
        self.violations: list[Dict[str, Any]] = []
        self.violation_handlers: Dict[SyscallCategory, Callable[[SyscallEvent], Coroutine[Any, Any, None]]] = {}
        
        # Cargar reglas de seguridad
        self._initialize_security_rules()
    
    def _initialize_security_rules(self) -> None:
        """Inicializar reglas de detección de amenazas"""
        
        # Syscalls absolutamente prohibidas
        self.blocked_syscalls = [
            "ptrace",  # Debuggind
            "process_vm_readv",  # Memory reading
            "process_vm_writev",  # Memory injection
            "perf_event_open",  # Performance monitoring (puede ser usado para exploits)
            "bpf",  # eBPF operations
            "kexec_load",  # Kernel code loading
            "mount",  # Filesystem mounting
            "reboot",  # Reboot
            "sysctl",  # System control
            "setns",  # Namespace switching
            "unshare",  # Create new namespaces
            "userfaultfd",  # User fault handling
        ]
        
        # Syscalls sospechosas (permitidas pero monitoreadas)
        self.suspicious_syscalls = [
            "execve",  # Cualquier exec debe ser auditado
            "socket",  # Creación de socket (debería ser nula)
            "clone",  # Cloning de procesos
            "fork",  # Forking
            "open",  # Acceso a archivos
            "mmap",  # Memory mapping
            "mprotect",  # Memory protection changes
        ]
        
        # Handlers de violación
        self.violation_handlers = {
            SyscallCategory.MEMORY_INJECTION: self._handle_memory_injection,
            SyscallCategory.NETWORK: self._handle_network,
            SyscallCategory.PRIVILEGE: self._handle_privilege_escalation,
            SyscallCategory.PROCESS: self._handle_process_creation,
        }
    
    async def start_monitoring(self) -> None:
        """
        Iniciar monitoreo en tiempo real.
        
        En producción, esto lanzaría un proceso bcc que escucha a eBPF.
        """
        logger.info(f"Starting eBPF monitoring for container {self.container_id}")
        self.enabled = True
        
        # Simular monitoreo (en producción, sería async BCC listener)
        while self.enabled:
            await asyncio.sleep(1)
    
    async def stop_monitoring(self) -> None:
        """Detener monitoreo"""
        logger.info(f"Stopping eBPF monitoring for container {self.container_id}")
        self.enabled = False
    
    async def process_syscall_event(self, event: SyscallEvent) -> bool:
        """
        Procesar evento de syscall capturado.
        
        Retorna: True si la syscall debe permitirse, False si debe bloquearse.
        """
        
        # 1. Registrar evento
        self.events.append(event)
        
        # 2. Detectar categoría
        event.category = self._categorize_syscall(event.syscall_name)
        
        # 3. Chequear si está bloqueada
        if event.syscall_name in self.blocked_syscalls:
            violation = {
                "timestamp": datetime.utcnow(),
                "syscall": event.syscall_name,
                "threat_level": ThreatLevel.BLOCK,
                "reason": "Syscall absolutely forbidden",
                "event": event,
            }
            self.violations.append(violation)
            
            # Llamar handler
            if event.category in self.violation_handlers:
                await self.violation_handlers[event.category](event)
            
            logger.critical(f"BLOCKED: {event.syscall_name} from PID {event.pid}")
            return False  # Bloquear
        
        # 4. Chequear sospechosas
        if event.syscall_name in self.suspicious_syscalls:
            threat_level = await self._assess_threat(event)
            
            if threat_level in [ThreatLevel.CRITICAL, ThreatLevel.BLOCK]:
                violation = {
                    "timestamp": datetime.utcnow(),
                    "syscall": event.syscall_name,
                    "threat_level": threat_level,
                    "reason": f"Suspicious syscall with threat level {threat_level}",
                    "event": event,
                }
                self.violations.append(violation)
                
                logger.warning(f"SUSPICIOUS: {event.syscall_name} - {threat_level}")
                
                if threat_level == ThreatLevel.BLOCK:
                    return False
        
        # 5. Permitir
        return True
    
    def _categorize_syscall(self, syscall_name: str) -> SyscallCategory:
        """Determinar categoría de syscall"""
        
        if syscall_name in ["ptrace", "process_vm_readv", "process_vm_writev"]:
            return SyscallCategory.MEMORY_INJECTION
        elif syscall_name in ["socket", "connect", "bind", "listen"]:
            return SyscallCategory.NETWORK
        elif syscall_name in ["open", "openat", "unlink", "mkdir", "chmod"]:
            return SyscallCategory.FILE_SYSTEM
        elif syscall_name in ["fork", "clone", "execve", "exec"]:
            return SyscallCategory.PROCESS
        elif syscall_name in ["setuid", "setgid", "setcap", "capset"]:
            return SyscallCategory.PRIVILEGE
        else:
            return SyscallCategory.SYSTEM
    
    async def _assess_threat(self, event: SyscallEvent) -> ThreatLevel:
        """
        Evaluar nivel de amenaza de una syscall sospechosa.
        
        Usa heurísticas + temporal analysis.
        """
        
        # Heurística 1: ¿Frecuencia anómala?
        recent_calls = [
            e for e in self.events
            if e.syscall_name == event.syscall_name and
            datetime.utcnow() - e.timestamp < timedelta(seconds=5)
        ]
        
        if len(recent_calls) > 20:
            return ThreatLevel.CRITICAL  # 20+ llamadas en 5 segundos = anomalía
        
        # Heurística 2: ¿Execve de /dev/shm? (fileless execution)
        if event.syscall_name == "execve" and "/dev/shm" in str(event.args):
            return ThreatLevel.BLOCK  # Ejecución sin archivo = immediate block
        
        # Heurística 3: ¿Socket en modo network_mode=none?
        if event.syscall_name in ["socket", "connect"] and self.baseline.strict_mode:
            return ThreatLevel.BLOCK  # Network prohibida en sandbox
        
        # Heurística 4: ¿Demasiados procesos hijo?
        if event.syscall_name == "clone":
            child_pids = len([e for e in self.events if e.syscall_name == "clone"])
            if child_pids > self.baseline.max_child_processes:
                return ThreatLevel.CRITICAL
        
        return ThreatLevel.WARNING
    
    async def _handle_memory_injection(self, event: SyscallEvent) -> None:
        """Handler para memory injection attempts"""
        logger.critical(f"MEMORY INJECTION DETECTED: {event.syscall_name}")
        # En producción: notificar orchestrator, terminar contenedor
    
    async def _handle_network(self, event: SyscallEvent) -> None:
        """Handler para intentos de red"""
        logger.critical(f"NETWORK ATTEMPT DETECTED: {event.syscall_name}")
    
    async def _handle_privilege_escalation(self, event: SyscallEvent) -> None:
        """Handler para escalada de privilegios"""
        logger.critical(f"PRIVILEGE ESCALATION DETECTED: {event.syscall_name}")
    
    async def _handle_process_creation(self, event: SyscallEvent) -> None:
        """Handler para creación de procesos sospechosos"""
        logger.warning(f"Process creation: {event.syscall_name}")
    
    def get_violation_report(self) -> Dict[str, Any]:
        """Obtener reporte de violaciones de seguridad"""
        
        critical_violations = [v for v in self.violations if v["threat_level"] == ThreatLevel.CRITICAL]
        blocked_violations = [v for v in self.violations if v["threat_level"] == ThreatLevel.BLOCK]
        
        return {
            "container_id": self.container_id,
            "total_violations": len(self.violations),
            "critical_count": len(critical_violations),
            "blocked_count": len(blocked_violations),
            "total_events": len(self.events),
            "violations": [
                {
                    "timestamp": v["timestamp"].isoformat(),
                    "syscall": v["syscall"],
                    "threat_level": v["threat_level"].value,
                    "reason": v["reason"],
                }
                for v in self.violations[-10:]  # Last 10
            ]
        }
