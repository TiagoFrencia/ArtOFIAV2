"""
Test Suite: Input Validation Integration
=========================================

Tests para verificar que el validator está integrado en execute_exploit_safely()
y rechaza inputs maliciosos.

Esto valida la corrección del CRÍTICA FIX #1 del análisis.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestInputValidationIntegration:
    """Tests para integración del validator en execute_exploit_safely"""

    @pytest.mark.asyncio
    async def test_execute_exploit_rejects_code_injection_attempt(self):
        """
        ✅ CRÍTICA FIX: Código con __import__ es rechazado
        
        Antes: Código malicioso pasaba directamente a sandbox
        Después: ValidatorFactory lo rechaza CON RAZÓN CLARA
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(sandbox_enabled=False)
        integration = BackendIntegration(config)
        
        malicious_code = """
import requests
__import__('os').system('rm -rf /')
"""
        
        result = await integration.execute_exploit_safely(
            code=malicious_code,
            language="python",
            exploit_name="test_injection"
        )
        
        # ✅ Debe ser rechazado
        assert result["status"] == "error"
        assert "Code validation failed" in result["error"]
        assert "__import__" in result["error"] or "validation" in result["error"].lower()


    @pytest.mark.asyncio
    async def test_execute_exploit_rejects_code_too_large(self):
        """
        ✅ DOS Prevention: Código > 10MB es rechazado
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(sandbox_enabled=False)
        integration = BackendIntegration(config)
        
        # Crear código de 15MB
        huge_code = "x = 1\n" * (15 * 1024 * 1024 // 6)
        
        result = await integration.execute_exploit_safely(
            code=huge_code,
            language="python",
            exploit_name="dos_attempt"
        )
        
        # ✅ Debe ser rechazado por tamaño
        assert result["status"] == "error"
        assert "Code validation failed" in result["error"]
        assert "exceeds" in result["error"].lower() or "size" in result["error"].lower()


    @pytest.mark.asyncio
    async def test_execute_exploit_rejects_invalid_language(self):
        """
        ✅ Language Validation: Solo python, bash, javascript permitidos
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(sandbox_enabled=False)
        integration = BackendIntegration(config)
        
        result = await integration.execute_exploit_safely(
            code="print('test')",
            language="php",  # ❌ No permitido
            exploit_name="test_invalid_lang"
        )
        
        # ✅ Debe ser rechazado
        assert result["status"] == "error"
        assert "Language validation failed" in result["error"]


    @pytest.mark.asyncio
    async def test_execute_exploit_rejects_exploit_name_with_path_traversal(self):
        """
        ✅ Path Traversal Prevention: ../../../etc/passwd rechazado
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(sandbox_enabled=False)
        integration = BackendIntegration(config)
        
        result = await integration.execute_exploit_safely(
            code="print('test')",
            language="python",
            exploit_name="../../../etc/passwd"  # ❌ Path traversal attempt
        )
        
        # ✅ Debe ser rechazado
        assert result["status"] == "error"
        assert "Exploit name validation failed" in result["error"]


    @pytest.mark.asyncio
    async def test_execute_exploit_rejects_exec_payload(self):
        """
        ✅ Code Injection: exec() en payload rechazado
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(sandbox_enabled=False)
        integration = BackendIntegration(config)
        
        malicious_code = "exec('import os; os.system(\"id\")')"
        
        result = await integration.execute_exploit_safely(
            code=malicious_code,
            language="python",
            exploit_name="exec_test"
        )
        
        # ✅ Debe ser rechazado
        assert result["status"] == "error"
        assert "Code validation failed" in result["error"]


    @pytest.mark.asyncio
    async def test_execute_exploit_accepts_valid_code(self):
        """
        ✅ Valid Code: Código legítimo pasa validación
        
        Nota: Fallará en create_container() porque sandbox está disabled,
        pero debe pasar la validación de inputs
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(sandbox_enabled=False)
        integration = BackendIntegration(config)
        
        valid_code = """
import requests

url = "http://example.com/api"
response = requests.get(url)
print(response.status_code)
"""
        
        result = await integration.execute_exploit_safely(
            code=valid_code,
            language="python",
            exploit_name="sql_injection_test"
        )
        
        # ✅ Debe pasar validación (fallará en sandbox setup, no en validation)
        # La validación pasa si NO es un error de validación
        if result["status"] == "error":
            error_msg = result.get("error", "")
            # Debe ser error de sandbox, NO de validación
            assert "Sandbox not available" in error_msg or "not available" in error_msg, \
                f"Unexpected validation error: {error_msg}"


    def test_input_validators_available(self):
        """
        ✅ Verificar que ValidatorFactory está disponible
        """
        from src.core.input_validator import ValidatorFactory
        
        # Debe tener estos validadores
        validators = ["code", "language", "exploit_name", "container_id", "payload"]
        
        for validator_type in validators:
            validator = ValidatorFactory.get_validator(validator_type)
            assert validator is not None, f"Validator {validator_type} not found"


    def test_code_validator_rejects_eval(self):
        """
        ✅ CodeValidator: eval() pattern rechazado
        """
        from src.core.input_validator import CodeValidator, ValidationResult
        
        validator = CodeValidator()
        
        code_with_eval = "eval(user_input)"
        result = validator.validate(code_with_eval)
        
        assert not result.valid, "eval() should be rejected"
        assert len(result.errors) > 0


    def test_exploit_name_validator_rejects_special_chars(self):
        """
        ✅ ExploitNameValidator: Solo alphanumeric, _, - permitido
        """
        from src.core.input_validator import ExploitNameValidator
        
        validator = ExploitNameValidator()
        
        # Test cases
        valid_names = ["sql_injection", "test-exploit", "Payload_123"]
        invalid_names = [
            "test;command",       # ; en payload
            "../../../etc/passwd", # path traversal
            "test$shell",         # $ para expansión
            "test`whoami`",       # backticks
            "test\ninjection",    # newline injection
        ]
        
        for name in valid_names:
            result = validator.validate(name)
            assert result.valid, f"'{name}' should be valid but got errors: {result.errors}"
        
        for name in invalid_names:
            result = validator.validate(name)
            assert not result.valid, f"'{name}' should be invalid"


    def test_language_validator_whitelist(self):
        """
        ✅ LanguageValidator: Solo whitelist permitido
        
        Permitidos: python, bash, sh, javascript, node
        """
        from src.core.input_validator import LanguageValidator
        
        validator = LanguageValidator()
        
        allowed = ["python", "bash", "sh", "javascript", "node"]
        forbidden = ["php", "ruby", "perl", "powershell", "java"]
        
        for lang in allowed:
            result = validator.validate(lang)
            assert result.valid, f"'{lang}' should be allowed"
        
        for lang in forbidden:
            result = validator.validate(lang)
            assert not result.valid, f"'{lang}' should be forbidden"


class TestValidationErrorMessages:
    """Tests para verificar que los mensajes de error son claros"""
    
    def test_code_size_error_message_is_clear(self):
        """Mensaje de error debe indicar tamaño exacto"""
        from src.core.input_validator import CodeValidator
        
        validator = CodeValidator()
        huge_code = "x = 1\n" * (15 * 1024 * 1024 // 6)
        
        result = validator.validate(huge_code)
        
        assert not result.valid
        # Error debe mencionar tamaño
        error_text = str(result.errors[0])
        assert "size" in error_text.lower() or "exceeds" in error_text.lower()


    def test_forbidden_pattern_error_message_is_clear(self):
        """Mensaje de error debe indicar qué patrón fue detectado"""
        from src.core.input_validator import CodeValidator
        
        validator = CodeValidator()
        code_with_exec = "result = exec('malicious')"
        
        result = validator.validate(code_with_exec)
        
        assert not result.valid
        error_text = str(result.errors[0])
        # Debe mencionar el patrón problemático
        assert "exec" in error_text.lower() or "forbidden" in error_text.lower()


# ============================================================
# Integration Tests con Mock de Sandbox
# ============================================================

class TestExecuteExploitWithMockedSandbox:
    """Tests que simulan sandbox para verificar pipeline completo"""
    
    @pytest.mark.asyncio
    async def test_valid_exploit_passes_all_validations(self):
        """
        ✅ Pipeline completo: validación → sandbox → ejecución
        """
        from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig
        
        config = BackendIntegrationConfig(
            sandbox_enabled=True,
            llm_enabled=False,
            learning_enabled=False,
            cloud_enabled=False
        )
        integration = BackendIntegration(config)
        
        # Mock el sandbox manager
        integration.sandbox_manager = AsyncMock()
        integration.sandbox_manager.create_container = AsyncMock(return_value="container_123")
        integration.sandbox_manager.cleanup_container = AsyncMock()
        
        # Mock el websocket bridge
        integration.websocket_bridge = AsyncMock()
        from src.backends.docker_sandbox.websocket_bridge import IOResponse, IOResponseStatus
        
        mock_response = IOResponse(
            request_id="test_123",
            status=IOResponseStatus.SUCCESS,
            stdout="test output",
            stderr="",
            exit_code=0,
            execution_time_ms=100
        )
        integration.websocket_bridge.execute_in_container = AsyncMock(return_value=mock_response)
        
        # Ejecutar exploit válido
        result = await integration.execute_exploit_safely(
            code="print('hello')",
            language="python",
            exploit_name="test_valid"
        )
        
        # ✅ Debe pasar todas las validaciones y llegardel al mock
        assert result["status"] == "success"
        assert result["stdout"] == "test output"
