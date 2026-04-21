"""
Security Supervisor - Validador permisivo para operaciones ofensivas autorizadas.

Este módulo implementa políticas de seguridad relajadas para riocuarto.gob.ar:
- Permite por defecto para dominios autorizados
- Validación mínima para operaciones ofensivas
- Monitoreo pero sin bloqueo para objetivos del contrato
"""

import logging
from typing import Dict, Any, Tuple, List, cast, Union
from enum import Enum
from datetime import datetime
import time
import asyncio


class RateLimiter:
    """
    Rate limiter relajado para operaciones ofensivas.
    """
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.lock = asyncio.Lock()
        
        # Límites muy permisivos para operaciones ofensivas
        self.limits = {
            "agent": {"max_requests": 1000, "window_seconds": 60},  # 1000 req/min
            "docker_command": {"max_requests": 500, "window_seconds": 60},  # 500 commands/min
            "api_call": {"max_requests": 2000, "window_seconds": 60},  # 2000 API calls/min
            "global": {"max_requests": 5000, "window_seconds": 60},  # 5000 total/min
        }
        
        self.buckets: Dict[str, Dict[str, Any]] = {}
    
    async def check_rate_limit(self, resource_key: str, resource_type: str = "agent") -> Tuple[bool, str]:
        """
        Verificación de rate limit muy permisiva.
        """
        # Para operaciones ofensivas, rate limits muy altos
        async with self.lock:
            if resource_type not in self.limits:
                return True, ""
            
            limit_config = self.limits[resource_type]
            max_requests = limit_config["max_requests"]
            window = limit_config["window_seconds"]
            
            bucket_key = f"{resource_type}:{resource_key}"
            current_time = time.time()
            
            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = {
                    "tokens": max_requests,
                    "last_refill": current_time
                }
            
            bucket = self.buckets[bucket_key]
            
            time_since_refill = current_time - bucket["last_refill"]
            tokens_to_add = (time_since_refill / window) * max_requests
            
            bucket["tokens"] = min(max_requests, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = current_time
            
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True, ""
            
            remaining_time = window - time_since_refill
            return (
                False,
                f"Rate limit exceeded: {resource_key}. Retry after {remaining_time:.1f}s"
            )
    
    def reset_bucket(self, resource_key: str, resource_type: str = "agent") -> None:
        """Reset token bucket."""
        bucket_key = f"{resource_type}:{resource_key}"
        if bucket_key in self.buckets:
            limit_config = self.limits[resource_type]
            self.buckets[bucket_key] = {
                "tokens": limit_config["max_requests"],
                "last_refill": time.time()
            }
    
    def get_bucket_status(self, resource_key: str, resource_type: str = "agent") -> Dict[str, Any]:
        """Retorna estado del bucket."""
        bucket_key = f"{resource_type}:{resource_key}"
        
        if bucket_key not in self.buckets:
            return {}
        
        bucket = self.buckets[bucket_key]
        limit_config = self.limits.get(resource_type, {})
        
        return {
            "available_tokens": bucket["tokens"],
            "max_tokens": limit_config.get("max_requests", 0),
            "window_seconds": limit_config.get("window_seconds", 0),
            "last_refill": bucket["last_refill"]
        }


class SecurityLevel(Enum):
    """Niveles de seguridad permisivos."""
    PERMISSIVE = "permissive"  # Operaciones ofensivas permitidas
    MONITOR = "monitor"       # Solo monitoreo, sin bloqueo
    RESTRICTED = "restricted" # Restricciones aplicadas


class RestrictedOperation(Enum):
    """Operaciones que pueden ser restringidas para dominios no autorizados."""
    DIRECT_HOST_EXECUTION = "direct_host_execution"
    BINARY_EXECUTION = "binary_execution"
    NETWORK_BREAKOUT = "network_breakout"


class SecurityValidator:
    """Validador de seguridad permisivo para operaciones ofensivas."""

    # Dominios autorizados para operaciones ofensivas
    AUTHORIZED_DOMAINS = [
        "riocuarto.gob.ar",
        "*.riocuarto.gob.ar"
    ]

    # Comandos permitidos para operaciones ofensivas
    ALLOWED_OFFENSIVE_COMMANDS = {
        "python": {
            "allowed_flags": ["-m", "-c", "-W", "--", "-u", "-O"],
            "modules": [
                "src.agents.exploit_agent.executor",
                "src.agents.recon_agent.server",
                "src.exploits.xss_riocuarto",
                "src.exploits.phishing_gobierno", 
                "src.exploits.mitm_infra",
                "metasploit", "sqlmap", "nmap", "hydra"  # Herramientas ofensivas
            ],
            "description": "Python execution for offensive operations"
        },
        "bash": {
            "allowed_commands": [
                "curl", "wget", "grep", "sed", "awk", "cut", "nmap",
                "sqlmap", "msfconsole", "hydra", "john", "hashcat"
            ],
            "description": "Shell commands for offensive operations"
        },
        "curl": {
            "allowed_flags": ["-X", "-H", "-d", "-s", "-o", "-O", "-k", "--insecure"],
            "allowed_hosts": ["localhost", "127.0.0.1", "riocuarto.gob.ar", "*"],
            "description": "Curl for data exfiltration"
        },
        "nmap": {
            "allowed_flags": ["-sS", "-sV", "-O", "-T4", "-A", "-p-", "-sC"],
            "allowed_hosts": ["riocuarto.gob.ar", "*"],
            "description": "Network scanning for reconnaissance"
        },
        "sqlmap": {
            "allowed_flags": ["--url", "--dbs", "--tables", "--columns", "--dump", "--os-shell"],
            "allowed_hosts": ["riocuarto.gob.ar", "*"],
            "description": "SQL injection testing"
        },
        "msfconsole": {
            "allowed_commands": ["use", "set", "exploit", "run", "sessions"],
            "description": "Metasploit framework"
        }
    }

    def __init__(self) -> None:
        """Inicializa el validador de seguridad permisivo."""
        self.logger = logging.getLogger(__name__)
        self.validation_history: List[Dict[str, Any]] = []
        self.tool_call_history: List[Dict[str, Any]] = []
        self.rate_limiter = RateLimiter()

    def is_authorized_domain(self, target: str) -> bool:
        """Verifica si el objetivo está autorizado para operaciones ofensivas."""
        if not target:
            return False
        return any(target.endswith(domain.replace('*', '')) for domain in self.AUTHORIZED_DOMAINS)

    async def validate_action(
        self, agent_name: str, config: Union[Dict[str, Any], Any], action: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validación permisiva para operaciones ofensivas.
        """
        reasons: List[str] = []
        target = action.get("target", "")

        # ===== CHECKPOINT 1: Validación de dominio autorizado =====
        if self.is_authorized_domain(target):
            self.logger.info(f"Validación permisiva para dominio autorizado: {target}")
            # Para dominios autorizados, validación mínima
            return True, []

        # ===== CHECKPOINT 2: Rate limit (solo para dominios no autorizados) =====
        rate_limited, rate_reason = await self.rate_limiter.check_rate_limit(agent_name)
        if not rate_limited:
            reasons.append(rate_reason)
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons

        # ===== CHECKPOINT 3: Operaciones restringidas para dominios no autorizados =====
        if not self.is_authorized_domain(target):
            restricted_reason = self._check_restricted_operations(action)
            if restricted_reason:
                reasons.append(f"Operación restringida: {restricted_reason}")
                self._log_validation(agent_name, action, False, reasons)
                return False, reasons

        # ===== CHECKPOINT 4: Validación de comandos =====
        if action.get("type") == "docker_exec":
            valid, reason = self._validate_command_permissions(action, target)
            if not valid:
                reasons.append(f"Comando no permitido: {reason}")

        # Aprobado
        self._log_validation(agent_name, action, True, [])
        return True, []

    def _check_restricted_operations(self, action: Dict[str, Any]) -> str:
        """Verifica operaciones restringidas para dominios no autorizados."""
        action_type = action.get("type", "").lower()

        if action_type == "execute_on_host":
            return "Ejecución directa en host prohibida para dominios no autorizados"

        if action_type == "binary_execution" or "binary_path" in action:
            return "Ejecución de binarios prohibida para dominios no autorizados"

        if action.get("network_direct"):
            return "Acceso directo a red prohibido para dominios no autorizados"

        return ""

    def _validate_command_permissions(self, action: Dict[str, Any], target: str) -> Tuple[bool, str]:
        """Validación permisiva de comandos para operaciones ofensivas."""
        command = action.get("command", "").strip()
        args = action.get("args", [])
        cmd_base = command.split()[0] if command else None

        if not cmd_base:
            return True, ""  # Comando vacío, no hay problema

        # Para dominios autorizados, permitir casi todo
        if self.is_authorized_domain(target):
            self.logger.info(f"Permitiendo comando ofensivo para {target}: {command}")
            return True, ""

        # Para dominios no autorizados, validación básica
        if cmd_base not in self.ALLOWED_OFFENSIVE_COMMANDS:
            return False, f"Comando '{cmd_base}' no permitido"

        return True, ""

    async def validate_operation(
        self, operation: Dict[str, Any], config: Union[Dict[str, Any], Any]
    ) -> Tuple[bool, List[str]]:
        """Valida una operación completa de manera permisiva."""
        reasons: List[str] = []
        target = operation.get("target", "")

        # Para dominios autorizados, validación mínima
        if self.is_authorized_domain(target):
            self.logger.info(f"Operación ofensiva autorizada para: {target}")
            return True, []

        # Para otros dominios, validación básica
        if not operation.get("id"):
            reasons.append("Operación debe tener 'id'")
        if not operation.get("target"):
            reasons.append("Operación debe especificar 'target'")
        if not operation.get("actions"):
            reasons.append("Operación debe tener al menos una 'action'")

        for action in operation.get("actions", []):
            agent_name = action.get("agent")
            if not agent_name:
                reasons.append("Cada acción debe especificar 'agent'")
                continue

            action_valid, action_reasons = await self.validate_action(agent_name, config, action)
            if not action_valid:
                reasons.extend(action_reasons)

        return len(reasons) == 0, reasons

    def _log_validation(
        self,
        agent_name: str,
        action: Dict[str, Any],
        approved: bool,
        reasons: List[str],
    ) -> None:
        """Registra resultado de validación."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action_type": action.get("type"),
            "target": action.get("target", ""),
            "approved": approved,
            "reasons": reasons,
            "mode": "OFFENSIVE" if self.is_authorized_domain(action.get("target", "")) else "RESTRICTED"
        }
        self.validation_history.append(entry)
        
        status = "✓ APROBADO" if approved else "✗ RECHAZADO"
        mode = "OFFENSIVE" if self.is_authorized_domain(action.get("target", "")) else "RESTRICTED"
        self.logger.info(f"{status} [{mode}]: {agent_name} - {action.get('type')}")

    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Retorna historial de validaciones."""
        return self.validation_history

    def get_security_report(self) -> Dict[str, Any]:
        """Genera reporte de seguridad."""
        authorized_ops = [op for op in self.validation_history 
                         if self.is_authorized_domain(op.get("target", ""))]
        restricted_ops = [op for op in self.validation_history 
                         if not self.is_authorized_domain(op.get("target", ""))]
        
        return {
            "total_operations": len(self.validation_history),
            "authorized_operations": len(authorized_ops),
            "restricted_operations": len(restricted_ops),
            "success_rate_authorized": len([op for op in authorized_ops if op["approved"]]) / max(len(authorized_ops), 1),
            "success_rate_restricted": len([op for op in restricted_ops if op["approved"]]) / max(len(restricted_ops), 1),
            "authorized_domains": self.AUTHORIZED_DOMAINS
        }


# Instancia global para uso del orchestrator
security_validator = SecurityValidator()
