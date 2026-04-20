"""
Configuration Loader Module
============================
Responsabilidad única: Cargar y validar configuración desde .mcp.json

Separa la lógica de carga de config del Orchestrator Server.
Permite reutilizaciónen y testeo independiente.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.core.exceptions import ConfigurationException


logger = logging.getLogger(__name__)


@dataclass
class ManagedAgent:
    """Representation of managed agent in configuration.
    
    Attributes:
        name: Agent identifier
        command: Command to execute agent process
        args: Command-line arguments for agent
        env: Environment variables for agent process
    """
    name: str
    command: str
    args: list[str]
    env: Dict[str, str]
    
    def __post_init__(self) -> None:
        """Validate agent configuration after initialization.
        
        Raises:
            ValueError: If name or command is empty.
        """
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        if not self.command:
            raise ValueError("Agent command cannot be empty")


@dataclass
class SecurityConfig:
    """Security configuration for orchestrator.
    
    Attributes:
        audit_all_actions: Whether to audit all agent actions
        deny_by_default: Default deny policy (whitelist model)
        rate_limit_requests_per_minute: Rate limit window
        rate_limit_burst_size: Burst allowance
    """
    audit_all_actions: bool = True
    deny_by_default: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10


@dataclass
class OrchestratorConfig:
    """Complete orchestrator configuration.
    
    Attributes:
        agents: Dictionary of managed agents
        security: Security configuration
        raw_config: Original configuration dict for debugging
    """
    agents: Dict[str, ManagedAgent]
    security: SecurityConfig
    raw_config: Dict[str, Any]


class ConfigLoader:
    """Centralized configuration loader for orchestrator.
    
    Responsibilities:
        - Load .mcp.json configuration file
        - Parse and validate structure
        - Return typed OrchestratorConfig
        - Handle configuration errors gracefully
        
    Example:
        loader = ConfigLoader('.mcp.json')
        config = loader.load()
        for agent_name, agent in config.agents.items():
            print(f"Agent: {agent_name}, Command: {agent.command}")
    """
    
    def __init__(self, config_path: str = ".mcp.json"):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to .mcp.json configuration file
            
        Raises:
            FileNotFoundError: If configuration file not found.
        """
        self.config_path = Path(config_path)
        self.logger = logger
        self._validate_path()
    
    def _validate_path(self) -> None:
        """Validate configuration file exists and is readable.
        
        Raises:
            FileNotFoundError: If file doesn't exist or isn't valid.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration not found: {self.config_path}\n"
                "Ensure .mcp.json exists in root directory"
            )
        if not self.config_path.is_file():
            raise FileNotFoundError(f"{self.config_path} is not a valid file")
    
    def load(self) -> OrchestratorConfig:
        """Load and parse orchestrator configuration.
        
        Returns:
            OrchestratorConfig with typed structure.
            
        Raises:
            json.JSONDecodeError: If JSON is invalid.
            ConfigurationException: If structure is invalid.
        """
        try:
            raw_config = self._load_json()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {self.config_path}: {e}")
            raise
        
        agents = self._parse_agents(raw_config.get("mcpServers", {}))
        security = self._parse_security_config(raw_config.get("security", {}))
        
        self._validate_integrity(agents, security)
        
        self.logger.info(f"✓ Configuration loaded successfully ({len(agents)} agents)")
        
        return OrchestratorConfig(
            agents=agents,
            security=security,
            raw_config=raw_config
        )
    
    def _load_json(self) -> Dict[str, Any]:
        """Carga y parsea archivo JSON"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            content: Dict[str, Any] = json.load(f)
            return content
    
    def _parse_agents(self, mcp_servers: Dict[str, Any]) -> Dict[str, ManagedAgent]:
        """
        Parsea agentes desde mcpServers.
        
        Args:
            mcp_servers: Diccionario de mcpServers de config
        
        Returns:
            Dict de agentes parseados
        
        Raises:
            ConfigurationError: Si agente inválido
        """
        agents: Dict[str, ManagedAgent] = {}
        
        for agent_name, agent_config in mcp_servers.items():
            try:
                agent = ManagedAgent(
                    name=agent_name,
                    command=agent_config.get("command", ""),
                    args=agent_config.get("args", []),
                    env=agent_config.get("env", {})
                )
                agents[agent_name] = agent
                self.logger.debug(f"  ✓ Agente parseado: {agent_name}")
            except (ValueError, KeyError) as e:
                raise ConfigurationException(
                    f"Agente '{agent_name}' inválido: {e}"
                )
        
        if not agents:
            self.logger.warning("⚠ No se encontraron agentes en configuración")
        
        return agents
    
    def _parse_security_config(self, security_dict: Dict[str, Any]) -> SecurityConfig:
        """
        Parsea configuración de seguridad.
        
        Args:
            security_dict: Diccionario de seguridad
        
        Returns:
            SecurityConfig tupizada
        """
        rate_limit = security_dict.get("rateLimit", {})
        
        return SecurityConfig(
            audit_all_actions=security_dict.get("auditAllActions", True),
            deny_by_default=security_dict.get("denyByDefault", True),
            rate_limit_requests_per_minute=rate_limit.get("requests_per_minute", 60),
            rate_limit_burst_size=rate_limit.get("burst_size", 10)
        )
    
    def _validate_integrity(self, agents: Dict[str, ManagedAgent], security: SecurityConfig) -> None:
        """
        Valida integridad de configuración según AGENTS.md.
        
        Args:
            agents: Diccionario de agentes
            security: Configuración de seguridad
        
        Raises:
            ConfigurationException: Si requisitos no se cumplen
        """
        # Verificar que orchestrator está definido
        if "orchestrator" not in agents:
            raise ConfigurationException(
                "Orchestrator debe estar definido en mcpServers"
            )
        
        # Verificar que exploit_agent tiene SANDBOX=required
        if "exploit_agent" in agents:
            exploit_env = agents["exploit_agent"].env
            if exploit_env.get("SANDBOX") != "required":
                raise ConfigurationException(
                    "exploit_agent debe tener SANDBOX=required en env"
                )
            if exploit_env.get("VALIDATION_REQUIRED") != "true":
                raise ConfigurationException(
                    "exploit_agent debe tener VALIDATION_REQUIRED=true"
                )
        
        # Verificar seguridad
        if not security.audit_all_actions:
            raise ConfigurationException(
                "auditAllActions debe estar habilitado (true)"
            )
        if not security.deny_by_default:
            raise ConfigurationException(
                "denyByDefault debe estar habilitado (true)"
            )
        
        self.logger.info("✓ Validación de integridad completada")
