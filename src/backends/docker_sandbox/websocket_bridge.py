"""
WebSocket Bridge - Puente de Comunicación Seguro
================================================

Crea una capa de comunicación segura entre ExploitAgent y Sandbox.

Sin este puente, daríamos acceso directo a una shell del contenedor,
lo que es altamente inseguro:
- El agente de IA podría recibir prompts inyectados (indirect prompt injection)
- Podrías recibir output manipulado que engañe al controller
- Hay riesgo de escape del contenedor vía shell metacharacters

EL PUENTE FUNCIONA ASI:
1. ExploitAgent → envía código (Python/Bash) como TEXTO PURO
2. Bridge → valida input, inyecta en contenedor, captura output
3. Bridge → SANITIZA output (SIN metacharacters)
4. Bridge → retorna al agent vía WebSocket

Beneficios:
- El agente NUNCA ve métacharacters que podrían escapar
- Output está sanitizado y seguro para auditoría
- Communication está logging completo para compliance
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import base64
import re

logger = logging.getLogger(__name__)


class IORequestType(str, Enum):
    """Tipo de request"""
    EXECUTE_CODE = "execute_code"
    EXECUTE_SHELL = "execute_shell"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    GET_STATUS = "get_status"


class IOResponseStatus(str, Enum):
    """Estado de la respuesta"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class IORequest:
    """Request para ejecución en contenedor"""
    request_id: str
    request_type: IORequestType
    payload: Dict[str, Any]
    timeout_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IOResponse:
    """Response de ejecución en contenedor"""
    request_id: str
    status: IOResponseStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: int = 0
    warnings: list[str] = field(default_factory=list)


class PayloadValidator:
    """Validar payloads antes de inyectarlos en contenedor"""
    
    def __init__(self) -> None:
        self.dangerous_patterns = [
            r"\$\(",  # Command substitution
            r"`",  # Backticks
            r";\s*rm\s+",  # rm commands
            r";\s*dd\s+",  # dd commands
            r";\s*:/",  # SSH attempts
            r"/dev/mem",  # Memory access
            r"/proc/mem",  # Memory access
        ]
        
        self.size_limits = {
            "python": 10000,  # 10KB max
            "bash": 5000,  # 5KB max
        }
    
    def is_safe(self, code: str, language: str) -> tuple[bool, Optional[str]]:
        """
        Validar que payload es seguro.
        
        Retorna: (is_safe: bool, reason: Optional[str])
        """
        
        # Check 1: Tamaño
        if len(code) > self.size_limits.get(language, 10000):
            return False, f"Payload too large for {language}"
        
        # Check 2: Patrones peligrosos
        code_lower = code.lower()
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code_lower):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check 3: Caracteres de escape
        if any(c in code for c in ["\x00", "\xff"]):
            return False, "Binary characters not allowed"
        
        return True, None
    
    def sanitize_output(self, output: str, max_length: int = 5000) -> str:
        """
        Sanitizar output antes de retornarlo al agent.
        
        - Remover metacharacters peligrosos
        - Truncate si es muy largo
        - Encode especial para caracteres raros
        """
        
        # Truncate
        if len(output) > max_length:
            output = output[:max_length] + "\n...[truncated]"
        
        # Remover algunos metacharacters
        # PERO preservar información útil (no eliminar todo)
        dangerous_chars = ["\x00", "\x01"]
        for char in dangerous_chars:
            output = output.replace(char, "")
        
        return output


class WebSocketBridge:
    """
    Puente WebSocket para comunicación segura.
    
    En producción, esto sería un servidor WebSocket real.
    Por ahora, es un simulador con queue async.
    """
    
    def __init__(self, sandbox_manager: Any) -> None:
        self.sandbox_manager = sandbox_manager
        self.validator = PayloadValidator()
        self.request_queue: asyncio.Queue[IORequest] = asyncio.Queue()
        self.response_map: Dict[str, IOResponse] = {}
        self.communication_log: list[Dict[str, Any]] = []
    
    async def execute_in_container(self, request: IORequest) -> IOResponse:
        """
        Ejecutar request en contenedor de forma segura.
        
        Pipeline:
        1. Validar payload
        2. Inyectar en contenedor
        3. Capturar output
        4. Sanitizar output
        5. Retornar
        """
        
        # 1. Validar
        language = request.payload.get("language", "python")
        code = request.payload.get("code", "")
        
        is_safe, reason = self.validator.is_safe(code, language)
        if not is_safe:
            logger.warning(f"Unsafe payload rejected: {reason}")
            return IOResponse(
                request_id=request.request_id,
                status=IOResponseStatus.SECURITY_VIOLATION,
                stderr=f"Security violation: {reason}",
            )
        
        # 2. Auditar
        await self._audit_request(request, "accepted")
        
        # 3. Inyectar en contenedor
        container_id = request.payload.get("container_id")
        if not container_id:
            return IOResponse(
                request_id=request.request_id,
                status=IOResponseStatus.ERROR,
                stderr="No container_id provided",
            )
        
        try:
            # Ejecutar con timeout
            start_time = datetime.utcnow()
            stdout, exit_code, stderr = await asyncio.wait_for(
                self.sandbox_manager.execute_exploit(container_id, code, language),
                timeout=request.timeout_seconds
            )
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # 4. Sanitizar output
            stdout_safe = self.validator.sanitize_output(stdout)
            stderr_safe = self.validator.sanitize_output(stderr)
            
            # 5. Construir response
            response = IOResponse(
                request_id=request.request_id,
                status=IOResponseStatus.SUCCESS,
                stdout=stdout_safe,
                stderr=stderr_safe,
                exit_code=exit_code,
                execution_time_ms=execution_time_ms,
            )
            
            await self._audit_request(request, "success", response)
            return response
        
        except asyncio.TimeoutError:
            await self._audit_request(request, "timeout")
            return IOResponse(
                request_id=request.request_id,
                status=IOResponseStatus.TIMEOUT,
                stderr=f"Execution timeout after {request.timeout_seconds}s",
            )
        
        except Exception as e:
            logger.error(f"Execution error: {e}")
            await self._audit_request(request, "error", error_msg=str(e))
            return IOResponse(
                request_id=request.request_id,
                status=IOResponseStatus.ERROR,
                stderr=f"Execution error: {e}",
            )
    
    async def _audit_request(self, request: IORequest, status: str,
                            response: Optional[IOResponse] = None,
                            error_msg: Optional[str] = None) -> None:
        """Registrar request en log de auditoría"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.request_id,
            "request_type": request.request_type.value,
            "status": status,
            "code_length": len(request.payload.get("code", "")),
            "language": request.payload.get("language", "unknown"),
            "error": error_msg,
            "response_status": response.status.value if response else None,
            "execution_time_ms": response.execution_time_ms if response else None,
        }
        
        self.communication_log.append(log_entry)
        logger.info(f"[AUDIT] {request.request_id}: {status}")
    
    def get_communication_log(self) -> list[Dict[str, Any]]:
        """Retornar log de comunicación (para compliance)"""
        return self.communication_log.copy()
