"""
Input Validation Module - Validación ESTRICTA con AST Analysis.

Validación mejorada que usa Abstract Syntax Tree (AST) parsing en lugar de
solo regex, lo que es más robusto contra obfuscación.

Previene:
- Code injection en payloads
- DOS attacks (large payloads)
- Path traversal en filenames
- Obfuscated dangerous function calls
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
    """Represents a validation error for a field.
    
    Attributes:
        field: Name of the field that failed validation
        reason: Description of why validation failed
        value: Optional value that failed validation
    """

    field: str
    reason: str
    value: Any = None

    def __str__(self) -> str:
        """Return string representation of validation error.
        
        Returns:
            Formatted error message with field and reason.
        """
        return f"Validation failed for '{self.field}': {self.reason}"


class ValidationResult:
    """Container for validation operation results.
    
    Encapsulates the result of a validation operation with a boolean
    validity status and list of any errors encountered.
    
    Attributes:
        valid: Whether validation passed
        errors: List of ValidationError objects
        
    Example:
        result = ValidationResult(True, [])
        if result:  # Can be used directly in boolean context
            print("Validation passed")
    """

    def __init__(
        self, valid: bool, errors: Optional[List[ValidationError]] = None
    ) -> None:
        """Initialize validation result.
        
        Args:
            valid: Whether validation passed
            errors: List of validation errors (default: empty list)
        """
        self.valid = valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        """Return bool value of validation result.
        
        Returns:
            True if validation passed, False if failed.
        """
        return self.valid


class InputValidator(ABC):
    """Abstract base class for input validators.
    
    Defines the interface that all validators must implement to perform
    validation of specific input types.
    
    Subclasses should implement the validate() method to perform
    type-specific validation logic.
    """

    def validate(self, value: Any) -> ValidationResult:
        """Validate value and return result.
        
        Args:
            value: Value to validate
            
        Returns:
            ValidationResult indicating success/failure and any errors
            
        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError


class CodeValidator(InputValidator):
    """Validator for exploitation code using AST Analysis.
    
    Validates Python code for security violations using Abstract Syntax Tree
    parsing for robustness against obfuscation. More reliable than regex-based
    validation.
    
    Security checks:
        - Maximum code size (10MB)
        - Maximum lines (100,000)
        - Forbidden functions (__import__, exec, eval, compile, open, etc.)
        - Forbidden modules (os, sys, subprocess, socket, requests)
        - Syntax errors
        
    Class Variables:
        MAX_CODE_SIZE_BYTES: Maximum code size in bytes
        MAX_LINES: Maximum number of lines
        FORBIDDEN_FUNCTIONS: Set of function names not allowed
        FORBIDDEN_MODULES: Set of module names not allowed
    """

    MAX_CODE_SIZE_BYTES = 10 * 1024 * 1024
    MAX_LINES = 100_000

    FORBIDDEN_FUNCTIONS: Set[str] = {
        "__import__", "exec", "eval", "compile", "open",
        "input", "__loader__", "__builtins__"
    }

    FORBIDDEN_MODULES: Set[str] = {
        "os", "sys", "subprocess", "socket", "requests"
    }

    def validate(self, code: Any) -> ValidationResult:
        """Validate Python code for security violations.
        
        Args:
            code: Code to validate (should be string)
            
        Returns:
            ValidationResult with success status and any errors found
        """
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
        """Extract function name from AST Call node.
        
        Handles both direct calls (Name) and attribute calls (Attribute).
        
        Args:
            node: AST Call node
            
        Returns:
            Function name if available, None otherwise
        """
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_module_name(self, node: Any) -> Optional[str]:
        """Extract module name from import statement AST node.
        
        Args:
            node: AST Import or ImportFrom node
            
        Returns:
            Module name if available, None otherwise
        """
        if isinstance(node, ast.Import) and node.names:
            return node.names[0].name
        elif isinstance(node, ast.ImportFrom):
            return node.module
        return None


class FilenameValidator(InputValidator):
    """Validator for filenames - prevents path traversal attacks.
    
    Validates filenames to prevent directory traversal and path injection
    attacks. Restricts characters that could be used to escape the intended
    directory.
    
    Class Variables:
        FORBIDDEN_CHARS: Characters not allowed in filenames
        MAX_LENGTH: Maximum filename length
    """

    FORBIDDEN_CHARS: Set[str] = {'/', '\\', '\x00'}
    MAX_LENGTH = 255

    def validate(self, filename: Any) -> ValidationResult:
        """Validate filename for security violations.
        
        Args:
            filename: Filename to validate (should be string)
            
        Returns:
            ValidationResult with success status and any errors found
        """
        errors: List[ValidationError] = []

        if not isinstance(filename, str):
            errors.append(ValidationError(
                field="filename",
                reason=f"debe ser string, recibido {type(filename).__name__}"
            ))
            return ValidationResult(valid=False, errors=errors)

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
