"""
Input Validation Module - Validación permisiva para operaciones ofensivas.

Validación relajada para riocuarto.gob.ar con contrato autorizado.
Permite operaciones ofensivas mientras mantiene seguridad básica para otros objetivos.
"""

import re
import ast
import logging
from typing import Any, Optional, List, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Representa un error de validación."""

    field: str
    reason: str
    value: Any = None

    def __str__(self) -> str:
        return f"Validation failed for '{self.field}': {self.reason}"


class ValidationResult:
    """Contenedor para resultados de validación."""

    def __init__(
        self, valid: bool, errors: Optional[List[ValidationError]] = None
    ) -> None:
        self.valid = valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.valid


class InputValidator(ABC):
    """Clase base abstracta para validadores."""

    def validate(self, value: Any) -> ValidationResult:
        raise NotImplementedError


class CodeValidator(InputValidator):
    """Validador permisivo para código ofensivo.
    
    Para riocuarto.gob.ar, permite operaciones ofensivas.
    Para otros objetivos, aplica validaciones de seguridad.
    """

    MAX_CODE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB para payloads grandes
    MAX_LINES = 500_000  # Límite alto para scripts ofensivos

    # Funciones restringidas solo para objetivos no autorizados
    FORBIDDEN_FUNCTIONS: Set[str] = {
        "__import__", "exec", "eval", "compile", "open",
        "input", "__loader__", "__builtins__"
    }

    # Módulos restringidos solo para objetivos no autorizados  
    FORBIDDEN_MODULES: Set[str] = {
        "os", "sys", "subprocess", "socket", "requests"
    }

    # Dominios autorizados para operaciones ofensivas
    AUTHORIZED_DOMAINS = [
        "riocuarto.gob.ar",
        "*.riocuarto.gob.ar"
    ]

    def __init__(self, target: str = None):
        """Inicializa validador con objetivo específico."""
        self.target = target

    def is_authorized_domain(self) -> bool:
        """Verifica si el objetivo está autorizado para operaciones ofensivas."""
        if not self.target:
            return False
        return any(self.target.endswith(domain.replace('*', '')) for domain in self.AUTHORIZED_DOMAINS)

    def validate(self, code: Any) -> ValidationResult:
        """Valida código Python con políticas permisivas para objetivos autorizados."""
        errors: List[ValidationError] = []

        if not isinstance(code, str):
            errors.append(ValidationError(
                field="code",
                reason=f"debe ser string, recibido {type(code).__name__}"
            ))
            return ValidationResult(valid=False, errors=errors)

        if not code.strip():
            errors.append(ValidationError(
                field="code",
                reason="código no puede estar vacío"
            ))
            return ValidationResult(valid=False, errors=errors)

        # Para objetivos autorizados, validación mínima
        if self.is_authorized_domain():
            logger.info(f"✓ Validación permisiva para dominio autorizado: {self.target}")
            
            # Solo verificación básica de tamaño
            if len(code) > self.MAX_CODE_SIZE_BYTES:
                errors.append(ValidationError(
                    field="code",
                    reason=f"código demasiado grande ({len(code)} bytes)"
                ))
                return ValidationResult(valid=False, errors=errors)

            lines = code.split('\n')
            if len(lines) > self.MAX_LINES:
                errors.append(ValidationError(
                    field="code",
                    reason=f"código tiene demasiadas líneas ({len(lines)})"
                ))
                return ValidationResult(valid=False, errors=errors)

            return ValidationResult(valid=True, errors=[])

        # Para objetivos no autorizados, validación estricta
        if len(code) > self.MAX_CODE_SIZE_BYTES:
            errors.append(ValidationError(
                field="code",
                reason=f"código demasiado grande ({len(code)} bytes)"
            ))
            return ValidationResult(valid=False, errors=errors)

        lines = code.split('\n')
        if len(lines) > self.MAX_LINES:
            errors.append(ValidationError(
                field="code",
                reason=f"código tiene demasiadas líneas ({len(lines)})"
            ))
            return ValidationResult(valid=False, errors=errors)

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_func_name(node)
                    if func_name in self.FORBIDDEN_FUNCTIONS:
                        errors.append(ValidationError(
                            field="code",
                            reason=f"Función prohibida: {func_name}()"
                        ))

                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module_name = self._get_module_name(node)
                    if module_name in self.FORBIDDEN_MODULES:
                        errors.append(ValidationError(
                            field="code",
                            reason=f"Módulo prohibido: {module_name}"
                        ))
        except SyntaxError as e:
            errors.append(ValidationError(
                field="code",
                reason=f"Syntax error: {e}"
            ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _get_func_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_module_name(self, node: Any) -> Optional[str]:
        if isinstance(node, ast.Import) and node.names:
            return node.names[0].name
        elif isinstance(node, ast.ImportFrom):
            return node.module
        return None


class FilenameValidator(InputValidator):
    """Validador permisivo para nombres de archivo."""

    FORBIDDEN_CHARS: Set[str] = {'/', '\\', '\x00'}
    MAX_LENGTH = 255

    def __init__(self, target: str = None):
        """Inicializa validador con objetivo específico."""
        self.target = target

    def is_authorized_domain(self) -> bool:
        """Verifica si el objetivo está autorizado."""
        if not self.target:
            return False
        authorized_domains = ["riocuarto.gob.ar", "*.riocuarto.gob.ar"]
        return any(self.target.endswith(domain.replace('*', '')) for domain in authorized_domains)

    def validate(self, filename: Any) -> ValidationResult:
        """Valida nombre de archivo con políticas permisivas."""
        errors: List[ValidationError] = []

        if not isinstance(filename, str):
            errors.append(ValidationError(
                field="filename",
                reason=f"debe ser string, recibido {type(filename).__name__}"
            ))
            return ValidationResult(valid=False, errors=errors)

        # Para objetivos autorizados, validación mínima
        if self.is_authorized_domain():
            logger.info(f"✓ Validación permisiva de archivo para dominio autorizado: {self.target}")
            
            # Solo verificación básica de longitud
            if len(filename) > self.MAX_LENGTH:
                errors.append(ValidationError(
                    field="filename",
                    reason=f"nombre demasiado largo ({len(filename)} > {self.MAX_LENGTH})"
                ))
            
            return ValidationResult(valid=len(errors) == 0, errors=errors)

        # Para objetivos no autorizados, validación estricta
        if len(filename) > self.MAX_LENGTH:
            errors.append(ValidationError(
                field="filename",
                reason=f"nombre demasiado largo ({len(filename)} > {self.MAX_LENGTH})"
            ))

        for char_seq in self.FORBIDDEN_CHARS:
            if char_seq in filename:
                errors.append(ValidationError(
                    field="filename",
                    reason=f"carácter prohibido: {repr(char_seq)}"
                ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)


class TargetValidator(InputValidator):
    """Validador para objetivos de operaciones ofensivas."""

    AUTHORIZED_DOMAINS = [
        "riocuarto.gob.ar",
        "*.riocuarto.gob.ar"
    ]

    def validate(self, target: Any) -> ValidationResult:
        """Valida objetivo para operaciones ofensivas."""
        errors: List[ValidationError] = []

        if not isinstance(target, str):
            errors.append(ValidationError(
                field="target",
                reason=f"debe ser string, recibido {type(target).__name__}"
            ))
            return ValidationResult(valid=False, errors=errors)

        if not target.strip():
            errors.append(ValidationError(
                field="target",
                reason="objetivo no puede estar vacío"
            ))
            return ValidationResult(valid=False, errors=errors)

        # Verificar si es un dominio autorizado
        is_authorized = any(target.endswith(domain.replace('*', '')) for domain in self.AUTHORIZED_DOMAINS)
        
        if not is_authorized:
            errors.append(ValidationError(
                field="target",
                reason=f"objetivo no autorizado: {target}. Solo permitido para riocuarto.gob.ar"
            ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)


class OffensiveOperationValidator:
    """Validador central para operaciones ofensivas."""
    
    def __init__(self):
        self.target_validator = TargetValidator()
        self.code_validator = None
        self.filename_validator = None

    def validate_offensive_operation(self, operation_data: Dict[str, Any]) -> ValidationResult:
        """Valida operación ofensiva completa."""
        errors: List[ValidationError] = []
        
        # Validar objetivo
        target = operation_data.get("target", "")
        target_result = self.target_validator.validate(target)
        if not target_result:
            errors.extend(target_result.errors)
        
        # Configurar validadores específicos para el objetivo
        self.code_validator = CodeValidator(target)
        self.filename_validator = FilenameValidator(target)
        
        # Validar código si está presente
        if "code" in operation_data:
            code_result = self.code_validator.validate(operation_data["code"])
            if not code_result:
                errors.extend(code_result.errors)
        
        # Validar nombres de archivo si están presentes
        if "filename" in operation_data:
            filename_result = self.filename_validator.validate(operation_data["filename"])
            if not filename_result:
                errors.extend(filename_result.errors)
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


# Funciones de utilidad para validación rápida
def validate_offensive_target(target: str) -> bool:
    """Valida rápidamente si un objetivo está autorizado para operaciones ofensivas."""
    validator = TargetValidator()
    return bool(validator.validate(target))

def validate_offensive_code(code: str, target: str) -> bool:
    """Valida rápidamente código para operaciones ofensivas."""
    validator = CodeValidator(target)
    return bool(validator.validate(code))

def validate_offensive_filename(filename: str, target: str) -> bool:
    """Valida rápidamente nombre de archivo para operaciones ofensivas."""
    validator = FilenameValidator(target)
    return bool(validator.validate(filename))
