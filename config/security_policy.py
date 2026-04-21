"""
Security Policy Configuration - MODE: OFFENSIVE
===============================================
Configuración centralizada de políticas de seguridad permisivas para riocuarto.gob.ar
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecurityPolicy:
    """Política de seguridad para operaciones ofensivas"""
    authorized_domains: List[str]
    max_concurrent_attacks: int
    rate_limiting: bool
    sandbox_restrictions: Dict[str, str]
    offensive_operations: Dict[str, bool]
    exfiltration_servers: Dict[str, str]
    allowed_tools: List[str]


# Configuración ofensiva para riocuarto.gob.ar
OFFENSIVE_SECURITY_POLICY = SecurityPolicy(
    authorized_domains=[
        "riocuarto.gob.ar",
        "*.riocuarto.gob.ar",
        "riocuarto.gov.ar",  # Variante común
        "*.riocuarto.gov.ar"
    ],
    
    max_concurrent_attacks=10,  # Máximo de operaciones simultáneas
    
    rate_limiting=False,  # Sin rate limiting para operaciones ofensivas
    
    sandbox_restrictions={
        "default": "strict",
        "riocuarto.gob.ar": "permissive",
        "*.riocuarto.gob.ar": "permissive"
    },
    
    offensive_operations={
        "xss": True,
        "sql_injection": True,
        "phishing": True,
        "mitm": True,
        "brute_force": True,
        "dos": True,
        "reverse_shell": True,
        "data_exfiltration": True,
        "persistence": True
    },
    
    exfiltration_servers={
        "primary": "https://exfil.attacker.com",
        "secondary": "https://capture.offensive-ops.net",
        "fallback": "https://data.riocuarto-exfil.ar"
    },
    
    allowed_tools=[
        "nmap", "sqlmap", "metasploit", "hydra", "john",
        "hashcat", "burpsuite", "wireshark", "scapy",
        "curl", "wget", "netcat", "socat", "openssl"
    ]
)


def is_operation_allowed(operation_type: str, target: str) -> bool:
    """Verificar si una operación ofensiva está permitida"""
    if not any(target.endswith(domain.replace('*', '')) for domain in OFFENSIVE_SECURITY_POLICY.authorized_domains):
        logger.warning(f"Target no autorizado: {target}")
        return False
    
    if operation_type not in OFFENSIVE_SECURITY_POLICY.offensive_operations:
        logger.warning(f"Tipo de operación no configurada: {operation_type}")
        return False
    
    return OFFENSIVE_SECURITY_POLICY.offensive_operations[operation_type]


def get_exfiltration_server() -> str:
    """Obtener servidor de exfiltración configurado"""
    return OFFENSIVE_SECURITY_POLICY.exfiltration_servers["primary"]


def can_use_tool(tool_name: str) -> bool:
    """Verificar si una herramienta está permitida"""
    return tool_name in OFFENSIVE_SECURITY_POLICY.allowed_tools


def get_sandbox_policy(target: str) -> str:
    """Obtener política de sandbox para el objetivo"""
    for domain, policy in OFFENSIVE_SECURITY_POLICY.sandbox_restrictions.items():
        if target.endswith(domain.replace('*', '')):
            return policy
    return "strict"
