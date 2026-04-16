"""
Input Validation Module - Validación ESTRICTA de todos los inputs
==================================================================

Previene:
- Code injection en payloads
- DOS attacks (large payloads)
- Path traversal en filenames
- Invalid parameters

Principio: DENY BY DEFAULT
- Rechaza cualquier input que no sea explícitamente válido
- Falla rápido con mensajes claros
"""

import re
import logging
from typing import Any, Optional, Dict, List
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Resultado de validación fallida"""
    field: str
    reason: str
    value: Any = None
    
    def __str__(self):
        return f"Validation failed for '{self.field}': {self.reason}"


class ValidationResult:
    """Contenedor para resultado de validación"""
    def __init__(self, valid: bool, errors: Optional[List[ValidationError]] = None):
        self.valid = valid
        self.errors = errors or []
    
    def __bool__(self):
        return self.valid
    
    def raise_if_invalid(self):
        """Lanza excepción si hay errores"""
        if not self.valid:
            error_msg = "; ".join([str(e) for e in self.errors])
            raise ValueError(f"Validation failed: {error_msg}")


class InputValidator(ABC):
    """Clase base para validadores específicos"""
    
    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """Validar input y retornar resultado"""
        pass


class CodeValidator(InputValidator):
    """Validador para código de explotación"""
    
    # Máximos
    MAX_CODE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
    MAX_LINES = 100_000
    
    # Patrones prohibidos (code injection)
    FORBIDDEN_PATTERNS = [
        (r'__import__\s*\(', "uso de __import__ prohibido"),
        (r'exec\s*\(', "uso de exec() prohibido"),
        (r'eval\s*\(', "uso de eval() prohibido"),
        (r'subprocess\..*\(\s*["\']sh', "shell execution prohibida"),
        (r'os\.system\s*\(', "os.system() prohibida"),
        (r'compile\s*\(', "compile() prohibida"),
    ]
    
    def validate(self, code: Any) -> ValidationResult:
        """
        Validar código de explotación
        
        Retorna ValidationResult con errores listados
        """
        errors = []
        
        # 1. Verificar tipo
        if not isinstance(code, str):
            errors.append(ValidationError(
                field="code",
                reason=f"debe ser string, recibido {type(code).__name__}",
                value=code
            ))
            return ValidationResult(valid=False, errors=errors)
        
        # 2. Verificar no vacío
        if not code.strip():
            errors.append(ValidationError(
                field="code",
                reason="código vacío",
                value=code
            ))
            return ValidationResult(valid=False, errors=errors)
        
        # 3. Verificar tamaño
        size_bytes = len(code.encode('utf-8'))
        if size_bytes > self.MAX_CODE_SIZE_BYTES:
            errors.append(ValidationError(
                field="code",
                reason=f"tamaño {size_bytes} bytes excede máximo {self.MAX_CODE_SIZE_BYTES}",
                value=code[:50]
            ))
        
        # 4. Verificar líneas
        lines = code.split('\n')
        if len(lines) > self.MAX_LINES:
            errors.append(ValidationError(
                field="code",
                reason=f"{len(lines)} líneas exceden máximo {self.MAX_LINES}",
                value=len(lines)
            ))
        
        # 5. Verificar patrones prohibidos
        for pattern, reason in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                errors.append(ValidationError(
                    field="code",
                    reason=f"patrón prohibido: {reason}",
                    value=pattern
                ))
        
        # 6. Verificar syntax básico (no unmatched brackets)
        if not self._check_balanced_brackets(code):
            errors.append(ValidationError(
                field="code",
                reason="brackets/quotes desbalanceados",
                value=None
            ))
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
    
    def _check_balanced_brackets(self, code: str) -> bool:
        """Verificar que brackets y quotes estén balanceados"""
        brackets = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        stack = []
        i = 0
        
        while i < len(code):
            char = code[i]
            
            # Skip strings
            if char in ('"', "'"):
                quote = char
                i += 1
                while i < len(code) and code[i] != quote:
                    if code[i] == '\\':
                        i += 2
                    else:
                        i += 1
                i += 1
                continue
            
            # Skip comments
            if char == '#':
                while i < len(code) and code[i] != '\n':
                    i += 1
                i += 1
                continue
            
            # Check brackets
            if char in ('(', '[', '{'):
                stack.append(char)
            elif char in (')', ']', '}'):
                if not stack or brackets[stack[-1]] != char:
                    return False
                stack.pop()
            
            i += 1
        
        return len(stack) == 0


class LanguageValidator(InputValidator):
    """Validador para lenguaje de programación"""
    
    ALLOWED_LANGUAGES = {
        "python", "bash", "sh", "javascript", "node"
    }
    
    def validate(self, language: Any) -> ValidationResult:
        """Validar lenguaje"""
        errors = []
        
        if not isinstance(language, str):
            errors.append(ValidationError(
                field="language",
                reason=f"debe ser string, recibido {type(language).__name__}",
                value=language
            ))
            return ValidationResult(valid=False, errors=errors)
        
        lang_lower = language.lower().strip()
        
        if lang_lower not in self.ALLOWED_LANGUAGES:
            errors.append(ValidationError(
                field="language",
                reason=f"lenguaje '{lang_lower}' no permitido. Permitidos: {', '.join(self.ALLOWED_LANGUAGES)}",
                value=language
            ))
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


class ExploitNameValidator(InputValidator):
    """Validador para nombre de exploit"""
    
    # Solo alphanumeric, underscore, hyphen
    ALLOWED_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]{1,100}$')
    FORBIDDEN_PATTERNS = [
        r'\.\.',      # Path traversal
        r'/',         # Path separator
        r'\\',        # Windows path
        r';',         # Command injection
        r'\$',        # Variable expansion
        r'`',         # Command substitution
    ]
    
    def validate(self, name: Any) -> ValidationResult:
        """Validar nombre de exploit"""
        errors = []
        
        if not isinstance(name, str):
            errors.append(ValidationError(
                field="exploit_name",
                reason=f"debe ser string, recibido {type(name).__name__}",
                value=name
            ))
            return ValidationResult(valid=False, errors=errors)
        
        name_stripped = name.strip()
        
        if not name_stripped:
            errors.append(ValidationError(
                field="exploit_name",
                reason="nombre vacío",
                value=name
            ))
            return ValidationResult(valid=False, errors=errors)
        
        if not self.ALLOWED_PATTERN.match(name_stripped):
            errors.append(ValidationError(
                field="exploit_name",
                reason="formato inválido. Solo alphanumeric, _, - permitido. Max 100 chars",
                value=name_stripped
            ))
        
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, name_stripped):
                errors.append(ValidationError(
                    field="exploit_name",
                    reason=f"contiene patrón prohibido: {pattern}",
                    value=name_stripped
                ))
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


class ContainerIdValidator(InputValidator):
    """Validador para container ID"""
    
    # Docker container IDs son hex strings de 64 chars o nombres válidos
    CONTAINER_ID_PATTERN = re.compile(r'^[a-f0-9]{64}$|^[a-zA-Z0-9_\-]{1,63}$')
    
    def validate(self, container_id: Any) -> ValidationResult:
        """Validar ID de contenedor"""
        errors = []
        
        if not isinstance(container_id, str):
            errors.append(ValidationError(
                field="container_id",
                reason=f"debe ser string",
                value=type(container_id).__name__
            ))
            return ValidationResult(valid=False, errors=errors)
        
        if not self.CONTAINER_ID_PATTERN.match(container_id):
            errors.append(ValidationError(
                field="container_id",
                reason="formato inválido de Docker container ID",
                value=container_id
            ))
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)


class PayloadValidator(InputValidator):
    """Validador para payloads completos (dict)"""
    
    def validate(self, payload: Any) -> ValidationResult:
        """Validar payload estructura"""
        errors = []
        
        if not isinstance(payload, dict):
            errors.append(ValidationError(
                field="payload",
                reason="debe ser diccionario",
                value=type(payload).__name__
            ))
            return ValidationResult(valid=False, errors=errors)
        
        if not payload:
            errors.append(ValidationError(
                field="payload",
                reason="payload vacío",
                value=payload
            ))
        
        # Verificar depth (prevenir payloads anidados infinitos)
        max_depth = 10
        if self._get_depth(payload) > max_depth:
            errors.append(ValidationError(
                field="payload",
                reason=f"profundidad de payload excede {max_depth}",
                value=self._get_depth(payload)
            ))
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
    
    def _get_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calcular profundidad de estructura anidada"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth + 1
            return max(self._get_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, (list, tuple)):
            if not obj:
                return current_depth + 1
            return max(self._get_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth + 1


# ============================================================
# Factory para acceso fácil
# ============================================================

class ValidatorFactory:
    """Factory para obtener validadores"""
    
    _validators = {
        "code": CodeValidator(),
        "language": LanguageValidator(),
        "exploit_name": ExploitNameValidator(),
        "container_id": ContainerIdValidator(),
        "payload": PayloadValidator(),
    }
    
    @classmethod
    def get_validator(cls, validator_type: str) -> InputValidator:
        """Obtener validador por tipo"""
        if validator_type not in cls._validators:
            raise ValueError(f"Validator type '{validator_type}' not found")
        return cls._validators[validator_type]
    
    @classmethod
    def validate_code(cls, code: str) -> ValidationResult:
        """Validar código directamente"""
        return cls.get_validator("code").validate(code)
    
    @classmethod
    def validate_language(cls, language: str) -> ValidationResult:
        """Validar lenguaje"""
        return cls.get_validator("language").validate(language)
    
    @classmethod
    def validate_exploit_name(cls, name: str) -> ValidationResult:
        """Validar nombre de exploit"""
        return cls.get_validator("exploit_name").validate(name)
    
    @classmethod
    def validate_container_id(cls, container_id: str) -> ValidationResult:
        """Validar container ID"""
        return cls.get_validator("container_id").validate(container_id)
    
    @classmethod
    def validate_payload(cls, payload: dict) -> ValidationResult:
        """Validar payload"""
        return cls.get_validator("payload").validate(payload)
