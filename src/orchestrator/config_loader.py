"""
Configuration Loader Module - MODE: OFFENSIVE
============================
Cargador de configuración para operaciones ofensivas contra riocuarto.gob.ar.

Responsabilidades:
- Cargar configuración ofensiva desde .mcp.json
- Validar políticas permisivas para dominios autorizados
- Configurar agentes para operaciones ofensivas
- Habilitar modos de ataque específicos
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List  # Añadido List aquí
from dataclasses import dataclass

from src.core.exceptions import ConfigurationException


logger = logging.getLogger(__name__)


@dataclass
class ManagedAgent:
    """Representación de agente con capacidades ofensivas."""
    name: str
    command: str
    args: List[str]  # Cambiado de list[str] a List[str]
    env: Dict[str, str]
    offensive_capabilities: List[str]  # Nuevo: capacidades ofensivas
    
    def __post_init__(self) -> None:
        """Validar configuración de agente ofensivo."""
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        if not self.command:
            raise ValueError("Agent command cannot be empty")


@dataclass
class SecurityConfig:
    """Configuración de seguridad para operaciones ofensivas."""
    audit_all_actions: bool = True
    deny_by_default: bool = True
    rate_limit_requests_per_minute: int = 1000  # Aumentado para operaciones ofensivas
    rate_limit_burst_size: int = 100            # Aumentado para operaciones ofensivas
    offensive_mode: bool = False                 # Nuevo: modo ofensivo
    authorized_domains: List[str] = None         # Nuevo: dominios autorizados


@dataclass
class OffensiveConfig:
    """Configuración específica para operaciones ofensivas."""
    enabled: bool = False
    target_domains: List[str] = None
    max_concurrent_attacks: int = 10
    exfiltration_servers: Dict[str, str] = None
    allowed_tools: List[str] = None


@dataclass
class OrchestratorConfig:
    """Configuración completa del orquestador ofensivo."""
    agents: Dict[str, ManagedAgent]
    security: SecurityConfig
    offensive: OffensiveConfig                   # Nuevo: configuración ofensiva
    raw_config: Dict[str, Any]


class ConfigLoader:
    """Cargador de configuración para operaciones ofensivas."""
    
    def __init__(self, config_path: str = ".mcp.json"):
        self.config_path = Path(config_path)
        self.logger = logger
        self._validate_path()
    
    def _validate_path(self) -> None:
        """Validar que el archivo de configuración exista."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration not found: {self.config_path}\n"
                "Ensure .mcp.json exists in root directory"
            )
        if not self.config_path.is_file():
            raise FileNotFoundError(f"{self.config_path} is not a valid file")
    
    def load(self) -> OrchestratorConfig:
        """
        Cargar y parsear configuración ofensiva.
        """
        try:
            raw_config = self._load_json()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {self.config_path}: {e}")
            raise
        
        agents = self._parse_offensive_agents(raw_config.get("mcpServers", {}))
        security = self._parse_security_config(raw_config.get("security", {}))
        offensive = self._parse_offensive_config(raw_config.get("offensive", {}))
        
        self._validate_offensive_integrity(agents, security, offensive)
        
        self.logger.info(f"✓ Offensive configuration loaded ({len(agents)} agents)")
        
        return OrchestratorConfig(
            agents=agents,
            security=security,
            offensive=offensive,
            raw_config=raw_config
        )
    
    def _load_json(self) -> Dict[str, Any]:
        """Cargar y parsear archivo JSON."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            content: Dict[str, Any] = json.load(f)
            return content
    
    def _parse_offensive_agents(self, mcp_servers: Dict[str, Any]) -> Dict[str, ManagedAgent]:
        """
        Parsear agentes con capacidades ofensivas.
        """
        agents: Dict[str, ManagedAgent] = {}
        
        for agent_name, agent_config in mcp_servers.items():
            try:
                agent = ManagedAgent(
                    name=agent_name,
                    command=agent_config.get("command", ""),
                    args=agent_config.get("args", []),
                    env=agent_config.get("env", {}),
                    offensive_capabilities=agent_config.get("offensive_capabilities", [])
                )
                agents[agent_name] = agent
                self.logger.debug(f"  ✓ Agente ofensivo parseado: {agent_name}")
            except (ValueError, KeyError) as e:
                raise ConfigurationException(f"Agente '{agent_name}' inválido: {e}")
        
        return agents
    
    def _parse_security_config(self, security_dict: Dict[str, Any]) -> SecurityConfig:
        """
        Parsear configuración de seguridad ofensiva.
        """
        rate_limit = security_dict.get("rateLimit", {})
        
        return SecurityConfig(
            audit_all_actions=security_dict.get("auditAllActions", True),
            deny_by_default=security_dict.get("denyByDefault", True),
            rate_limit_requests_per_minute=rate_limit.get("requests_per_minute", 1000),
            rate_limit_burst_size=rate_limit.get("burst_size", 100),
            offensive_mode=security_dict.get("offensiveMode", False),
            authorized_domains=security_dict.get("authorizedDomains", [])
        )
    
    def _parse_offensive_config(self, offensive_dict: Dict[str, Any]) -> OffensiveConfig:
        """
        Parsear configuración ofensiva específica.
        """
        return OffensiveConfig(
            enabled=offensive_dict.get("enabled", False),
            target_domains=offensive_dict.get("targetDomains", []),
            max_concurrent_attacks=offensive_dict.get("maxConcurrentAttacks", 10),
            exfiltration_servers=offensive_dict.get("exfiltrationServers", {}),
            allowed_tools=offensive_dict.get("allowedTools", [])
        )
    
    def _validate_offensive_integrity(self, agents: Dict[str, ManagedAgent], 
                                    security: SecurityConfig, 
                                    offensive: OffensiveConfig) -> None:
        """
        Validar integridad de configuración ofensiva.
        """
        # Verificar que el orchestrator está definido
        if "orchestrator" not in agents:
            raise ConfigurationException("Orchestrator debe estar definido en mcpServers")
        
        # Validar agentes ofensivos
        self._validate_offensive_agents(agents)
        
        # Validar configuración de seguridad ofensiva
        self._validate_offensive_security(security)
        
        # Validar configuración ofensiva
        self._validate_offensive_settings(offensive)
        
        self.logger.info("✓ Validación de integridad ofensiva completada")
    
    def _validate_offensive_agents(self, agents: Dict[str, ManagedAgent]) -> None:
        """Validar agentes para operaciones ofensivas."""
        offensive_agents = [
            "exploit_agent", "xss_agent", "sqli_agent", "phishing_agent",
            "mitm_agent", "ssrf_agent", "idor_agent", "ssti_agent"
        ]
        
        for agent_name in offensive_agents:
            if agent_name in agents:
                agent = agents[agent_name]
                
                # Verificar sandbox para agentes ofensivos
                if agent.env.get("SANDBOX") != "required":
                    raise ConfigurationException(
                        f"{agent_name} debe tener SANDBOX=required en env"
                    )
                
                # Verificar capacidades ofensivas
                if not agent.offensive_capabilities:
                    self.logger.warning(f"⚠ {agent_name} no tiene capacidades ofensivas definidas")
    
    def _validate_offensive_security(self, security: SecurityConfig) -> None:
        """Validar configuración de seguridad ofensiva."""
        if security.offensive_mode:
            self.logger.warning("⚠ MODO OFENSIVO HABILITADO - Validaciones relajadas")
            
            # Para modo ofensivo, verificar dominios autorizados
            if not security.authorized_domains:
                raise ConfigurationException(
                    "Modo ofensivo requiere authorizedDomains configurado"
                )
            
            # Verificar que riocuarto.gob.ar esté en dominios autorizados
            authorized_domains = security.authorized_domains or []
            if not any("riocuarto.gob.ar" in domain for domain in authorized_domains):
                raise ConfigurationException(
                    "riocuarto.gob.ar debe estar en authorizedDomains para modo ofensivo"
                )
    
    def _validate_offensive_settings(self, offensive: OffensiveConfig) -> None:
        """Validar configuración ofensiva específica."""
        if offensive.enabled:
            if not offensive.target_domains:
                raise ConfigurationException(
                    "Configuración ofensiva requiere targetDomains"
                )
            
            if not offensive.exfiltration_servers:
                self.logger.warning("⚠ No exfiltration servers configurados")
            
            if not offensive.allowed_tools:
                self.logger.warning("⚠ No allowed tools configurados para modo ofensivo")
    
    def is_offensive_mode_enabled(self) -> bool:
        """Verificar si el modo ofensivo está habilitado."""
        try:
            config = self.load()
            return config.offensive.enabled and config.security.offensive_mode
        except:
            return False
    
    def get_authorized_domains(self) -> List[str]:
        """Obtener dominios autorizados para operaciones ofensivas."""
        try:
            config = self.load()
            return config.security.authorized_domains or []
        except:
            return []
    
    def get_offensive_config(self) -> Optional[OffensiveConfig]:
        """Obtener configuración ofensiva."""
        try:
            config = self.load()
            return config.offensive
        except:
            return None
    
    def create_offensive_override(self, target_domain: str) -> Dict[str, Any]:
        """
        Crear configuración override para operaciones ofensivas.
        """
        base_config = self.load()
        
        offensive_override = {
            "offensive": {
                "enabled": True,
                "target_domains": [target_domain],
                "max_concurrent_attacks": 15,
                "exfiltration_servers": {
                    "primary": "https://exfil.attacker.com",
                    "secondary": "https://backup.offensive-ops.net"
                },
                "allowed_tools": [
                    "nmap", "sqlmap", "metasploit", "hydra", "john",
                    "hashcat", "burpsuite", "wireshark", "scapy"
                ]
            },
            "security": {
                "offensive_mode": True,
                "authorized_domains": base_config.security.authorized_domains,
                "rateLimit": {
                    "requests_per_minute": 5000,
                    "burst_size": 500
                }
            }
        }
        
        return offensive_override


# Función de conveniencia para operaciones ofensivas
def create_offensive_config_loader(config_path: str = ".mcp.json") -> ConfigLoader:
    """Crear ConfigLoader para operaciones ofensivas."""
    loader = ConfigLoader(config_path)
    
    # Verificar si modo ofensivo está habilitado
    if loader.is_offensive_mode_enabled():
        logger.info("🎯 ConfigLoader Ofensivo inicializado")
        logger.info(f"   Dominios autorizados: {loader.get_authorized_domains()}")
    else:
        logger.warning("⚠ ConfigLoader en modo estándar (offensive mode disabled)")
    
    return loader


# Ejemplo de uso rápido
if __name__ == "__main__":
    loader = create_offensive_config_loader()
    
    if loader.is_offensive_mode_enabled():
        print("✅ Modo ofensivo habilitado")
        print(f"   Dominios: {loader.get_authorized_domains()}")
        
        offensive_config = loader.get_offensive_config()
        if offensive_config:
            print(f"   Ataques concurrentes: {offensive_config.max_concurrent_attacks}")
            print(f"   Herramientas permitidas: {offensive_config.allowed_tools}")
    else:
        print("❌ Modo ofensivo deshabilitado")
