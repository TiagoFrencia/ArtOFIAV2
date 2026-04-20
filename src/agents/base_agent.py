"""Base class para todos los agentes autónomos con DI pattern.

Proporciona:
- Inyección de configuración centralizada
- Logging consistente
- Manejo de errores centralizado  
- Type safety (type hints)
- Interfaz común para todos los agentes

Todos los agentes deben heredar de BaseAgent e implementar:
- execute(): Lógica principal del agente
- can_handle(): Determinar si puede procesar target
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.core.exceptions import ValidationException


class BaseAgent(ABC):
    """Clase base abstracta para agentes autónomos con inyección de dependencias.
    
    Garantiza:
    - Inyección de configuración tipada
    - Logging estructurado por agente
    - Manejo de errores centralizado
    - Type safety completo
    - Interfaz consistente entre todos los agentes
    
    Subclases deben:
    1. Llamar super().__init__(config) en su __init__
    2. Implementar execute() - lógica principal
    3. Implementar can_handle() - verificación de compatibilidad
    
    Example:
        class ReconAgent(BaseAgent):
            async def execute(self, target):
                self.logger.info(f"Ejecutando en {target}")
                return {...}
            
            def can_handle(self, target_type: str) -> bool:
                return target_type in ["api", "web"]
    """
    
    def __init__(self, config: Dict[str, Any], agent_name: Optional[str] = None) -> None:
        """Inicializa agente con configuración e inyección de dependencias.
        
        Args:
            config: Diccionario de configuración del agente
                Esperado: {"name": "...", "command": "...", "env": {...}}
            agent_name: Nombre del agente para logging (default: nombre de clase)
        
        Raises:
            ValueError: Si configuración está vacía o es inválida
            TypeError: Si config no es dict
        
        Note:
            La configuración típicamente viene de .mcp.json via ConfigLoader
        """
        if not isinstance(config, dict):
            raise TypeError(
                f"config debe ser dict, recibido {type(config).__name__}"
            )
        
        if not config:
            raise ValueError("config no puede estar vacío")
        
        self.config = config
        
        # Logger con nombre del agente
        logger_name = agent_name or self.__class__.__name__
        self.logger = logging.getLogger(logger_name)
        
        # Log de inicialización
        self.logger.info(
            f"Inicializando {logger_name}",
            extra={
                "agent": logger_name,
                "config_keys": list(config.keys())
            }
        )
    
    @abstractmethod
    async def execute(self, target: Any) -> Dict[str, Any]:
        """Ejecuta la operación principal del agente.
        
        Args:
            target: Objeto target de la operación (formato específico por agente)
        
        Returns:
            Diccionario con resultados de la operación
        
        Raises:
            ValidationException: Si target es inválido
            RuntimeError: Si ejecución falla
        
        Note:
            Implementación debe ser async para mantener reactividad
        """
        pass
    
    @abstractmethod
    def can_handle(self, target_type: str) -> bool:
        """Determina si este agente puede procesar un tipo de target.
        
        Args:
            target_type: Tipo de target (ej: "api", "web", "graphql")
        
        Returns:
            True si agente puede manejar este tipo, False si no
        
        Note:
            Usado por Orchestrator para enrutar tareas a agentes correctos
        """
        pass
    
    def _validate_target(self, target: Any, allowed_types: tuple) -> None:
        """Valida que target sea del tipo correcto.
        
        Args:
            target: Target a validar
            allowed_types: Tupla de tipos permitidos
        
        Raises:
            ValidationException: Si target no es tipo permitido
        """
        if not isinstance(target, allowed_types):
            types_str = ", ".join(t.__name__ for t in allowed_types)
            raise ValidationException(
                f"Target debe ser {types_str}, recibido {type(target).__name__}"
            )
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Obtiene valor de configuración de forma segura.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
        
        Returns:
            Valor de configuración o default
        """
        return self.config.get(key, default)
