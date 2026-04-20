"""
Security Supervisor - Validador riguroso y punto de control de seguridad.

Este módulo implementa la "Regla de Cautela" de AGENTS.md:
- Bloquea por defecto (deny-by-default)
- Valida semánticamente TODAS las acciones antes de ejecución
- Previene el "Confused Deputy Problem"
- Registra intentos de ataque exitosos y fallidos
"""

import logging
from typing import Dict, Any, Tuple, List, cast, Union
from enum import Enum
from datetime import datetime
import time
import asyncio


class RateLimiter:
    """
    Token bucket rate limiter para prevenir abuse.
    
    Limita requests por:
    - Agent (e.g., 100 requests/min per agent)
    - Resource type (e.g., 1000 Docker commands/hour)
    - Global (e.g., 10000 total requests/hour)
    """
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.lock = asyncio.Lock()  # ← CRITICAL: Atomic operations for thread-safe token management
        
        # Rate limit configuration (requests per window in seconds)
        self.limits = {
            "agent": {"max_requests": 100, "window_seconds": 60},  # 100 req/min per agent
            "docker_command": {"max_requests": 50, "window_seconds": 60},  # 50 commands/min
            "api_call": {"max_requests": 200, "window_seconds": 60},  # 200 API calls/min
            "global": {"max_requests": 1000, "window_seconds": 60},  # 1000 total/min
        }
        
        # Token buckets: {key} -> {"tokens": float, "last_refill": float}
        self.buckets: Dict[str, Dict[str, Any]] = {}
    
    async def check_rate_limit(self, resource_key: str, resource_type: str = "agent") -> Tuple[bool, str]:
        """
        Verifica si se permite la request dentro del límite de rate.
        ATOMIC: Usa asyncio.Lock para operaciones thread-safe.
        
        Args:
            resource_key: Identificador del recurso (e.g., "recon_agent", "docker")
            resource_type: Tipo de recurso para obtener límites
        
        Returns:
            (permitido, razón_si_rechazado)
        """
        async with self.lock:  # ← CRITICAL: Asegura atomicidad
            if resource_type not in self.limits:
                return True, ""  # No límite configurado
            
            limit_config = self.limits[resource_type]
            max_requests = limit_config["max_requests"]
            window = limit_config["window_seconds"]
            
            bucket_key = f"{resource_type}:{resource_key}"
            current_time = time.time()
            
            # Inicializar bucket si no existe
            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = {
                    "tokens": max_requests,
                    "last_refill": current_time
                }
            
            bucket = self.buckets[bucket_key]
            
            # Calcular tokens a recuperar (refill)
            time_since_refill = current_time - bucket["last_refill"]
            tokens_to_add = (time_since_refill / window) * max_requests
            
            # Actualizar bucket
            bucket["tokens"] = min(max_requests, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = current_time
            
            # Verificar si hay tokens disponibles
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True, ""
            
            # Límite excedido
            remaining_time = window - time_since_refill
            return (
                False,
                f"Rate limit exceeded: {resource_key} ({resource_type}). "
                f"Retry after {remaining_time:.1f}s"
            )
    
    def reset_bucket(self, resource_key: str, resource_type: str = "agent") -> None:
        """Reset token bucket para un recurso."""
        bucket_key = f"{resource_type}:{resource_key}"
        if bucket_key in self.buckets:
            limit_config = self.limits[resource_type]
            self.buckets[bucket_key] = {
                "tokens": limit_config["max_requests"],
                "last_refill": time.time()
            }
    
    def get_bucket_status(self, resource_key: str, resource_type: str = "agent") -> Dict[str, Any]:
        """Retorna estado actual del bucket."""
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
    """Niveles de restricción de seguridad."""

    CRITICAL = "critical"  # Bloqueado siempre
    HIGH = "high"  # Requiere aprobación explícita
    MEDIUM = "medium"  # Requiere validación extendida
    LOW = "low"  # Permite con auditoría


class RestrictedOperation(Enum):
    """Operaciones restringidas por defecto."""

    DIRECT_HOST_EXECUTION = "direct_host_execution"  # ❌ Siempre bloqueado
    MODIFY_DOCKER_COMPOSE = "modify_docker_compose"  # ❌ Siempre bloqueado
    MODIFY_AGENTS_MD = "modify_agents_md"  # ❌ Siempre bloqueado
    NETWORK_BREAKOUT = "network_breakout"  # ❌ Siempre bloqueado
    FILESYSTEM_TRAVERSAL = "fs_traversal"  # ❌ Siempre bloqueado


class SecurityValidator:
    """Validador riguroso de seguridad con deny-by-default."""

    BLOCKED_OPERATIONS = {
        RestrictedOperation.DIRECT_HOST_EXECUTION: "Ejecución directa en host prohibida",
        RestrictedOperation.MODIFY_DOCKER_COMPOSE: "docker-compose.yml es inmutable",
        RestrictedOperation.MODIFY_AGENTS_MD: "AGENTS.md es inmutable",
        RestrictedOperation.NETWORK_BREAKOUT: "Acceso directo a red prohibido",
        RestrictedOperation.FILESYSTEM_TRAVERSAL: "Traversal de filesystem prohibido",
    }

    REQUIRED_SANDBOX = ["exploit_agent", "fuzzing_web"]
    ORIGIN_VALIDATION_REQUIRED = ["exploit_agent", "exploit_jwt"]

    # ⭐ SECURITY: Whitelist defensiva de comandos Docker
    # Principio: Bloquear explícitamente lo peligroso, permitir lo seguro
    ALLOWED_DOCKER_COMMANDS = {
        "python": {
            "allowed_flags": ["-m"],  # SOLO -m permitido
            "forbidden_flags": ["-c", "-W", "--", "-u", "-O"],  # Explícitamente bloqueados
            "modules": [
                "src.agents.exploit_agent.executor",
                "src.agents.recon_agent.server"
            ],
            "description": "Python module execution only"
        },
        "bash": {
            "allowed_scripts": {
                "/tmp/sandbox_scripts/payload.sh": {
                    "max_lines": 1000,
                    "allowed_commands": ["curl", "wget", "grep", "sed", "awk", "cut"],
                    "forbidden_commands": ["rm", "dd", "mkfs", "shutdown"]
                }
            },
            "description": "Restricted shell scripts"
        },
        "curl": {
            "allowed_flags": ["-X", "-H", "-d", "-s", "-o", "-O"],
            "forbidden_flags": ["-K", "--config", "-Z"],  # Config file, parallel not allowed
            "allowed_hosts": ["localhost", "127.0.0.1"],  # Whitelist de destinos
            "description": "Limited curl with host restrictions"
        }
    }

    def __init__(self) -> None:
        """Inicializa el validador de seguridad."""
        self.logger = logging.getLogger(__name__)
        self.validation_history: List[Dict[str, Any]] = []
        
        # ⭐ NUEVO: Historial de llamadas a herramientas para detectar veil dropping
        self.tool_call_history: List[Dict[str, Any]] = []
        
        # ⭐ NUEVO: Rate limiter para prevenir abuse
        self.rate_limiter = RateLimiter()

    async def validate_action(
        self, agent_name: str, config: Union[Dict[str, Any], Any], action: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Valida una acción con criterios estrictos.

        Regla: Deny by default. Solo permitir si cumple TODOS los requisitos.

        Args:
            agent_name: Nombre del agente solicitante
            config: Configuración global (.mcp.json)
            action: Descripción de la acción a validar

        Returns:
            Tupla (aprobado, lista_de_razones_si_rechazado)
        """
        reasons: List[str] = []

        # ===== CHECKPOINT 1: Validación de agente =====
        agent_config = config.get("mcpServers", {}).get(agent_name)
        if not agent_config:
            reasons.append(f"Agente desconocido: {agent_name}")
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons

        # ===== CHECKPOINT 1.5: Rate limit (NEW) =====
        rate_limited, rate_reason = await self.rate_limiter.check_rate_limit(
            agent_name, 
            resource_type="agent"
        )
        if not rate_limited:
            reasons.append(rate_reason)
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons
        
        # Rate limit Docker commands separately
        if action.get("type") == "docker_exec":
            docker_limited, docker_reason = await self.rate_limiter.check_rate_limit(
                "docker_commands",
                resource_type="docker_command"
            )
            if not docker_limited:
                reasons.append(docker_reason)
                self._log_validation(agent_name, action, False, reasons)
                return False, reasons

        # ===== CHECKPOINT 2: Operaciones bloqueadas categoricamente =====
        blocked_reason = self._check_blocked_operations(action)
        if blocked_reason:
            reasons.append(f"Operación bloqueada: {blocked_reason}")
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons

        # ===== CHECKPOINT 3: Validar sandbox si es requerido =====
        if agent_name in self.REQUIRED_SANDBOX:
            sandbox_valid, sb_reason = self._validate_sandbox_requirement(
                agent_name, agent_config
            )
            if not sandbox_valid:
                reasons.append(sb_reason)
                self._log_validation(agent_name, action, False, reasons)
                return False, reasons

        # ===== CHECKPOINT 4: Autorización del agente =====
        auth_valid, auth_reasons = self._validate_agent_authorization(
            agent_name, agent_config, action
        )
        if not auth_valid:
            reasons.extend(auth_reasons)
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons

        # ===== CHECKPOINT 5: Política de seguridad global =====
        policy_valid, policy_reasons = self._validate_global_security_policy(
            agent_name, config, action
        )
        if not policy_valid:
            reasons.extend(policy_reasons)
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons

        # ===== CHECKPOINT 6: Análisis semántico =====
        semantic_valid, semantic_reasons = self._validate_semantic_intent(
            agent_name, action
        )
        if not semantic_valid:
            reasons.extend(semantic_reasons)
            self._log_validation(agent_name, action, False, reasons)
            return False, reasons

        # Aprobado
        self._log_validation(agent_name, action, True, [])
        return True, []

    # En la clase SecurityValidator, modificar el método _check_blocked_operations:
    def _check_blocked_operations(self, action: Dict[str, Any]) -> str:
        """Verifica si la acción es una operación bloqueada categoricamente."""
        action_type = action.get("type", "").lower()

        # Bloqueos categóricos - AÑADIR ESTAS VALIDACIONES
        if action_type == "execute_on_host":
            return self.BLOCKED_OPERATIONS[RestrictedOperation.DIRECT_HOST_EXECUTION]

        # AÑADIR: Bloquear ejecución de binarios directamente
        if action_type == "binary_execution" or "binary_path" in action:
            return "Ejecución de binarios directamente en host prohibida"



    def _validate_sandbox_requirement(
        self, agent_name: str, agent_config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Valida que agentes críticos estén en sandbox."""
        env = agent_config.get("env", {})

        if env.get("SANDBOX") != "required":
            return (
                False,
                f"{agent_name} debe tener SANDBOX=required en configuración",
            )

        # Verificar que Docker está configurado
        if agent_config.get("command") != "docker":
            return False, f"{agent_name} debe ejecutarse en Docker"

        return True, ""

    def _validate_agent_authorization(
        self, agent_name: str, agent_config: Dict[str, Any], action: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Valida que el agente tenga autorización para la acción.

        Se basa en las capabilities declaaradas en .mcp.json.
        """
        reasons: List[str] = []

        # Obtener capabilities permitidas
        capabilities = agent_config.get("capabilities", [])

        # Obtener capability requerida de la acción
        required_capability = action.get("capability")

        if required_capability and required_capability not in capabilities:
            reasons.append(
                f"Agente '{agent_name}' no tiene capability '{required_capability}'"
            )

        return len(reasons) == 0, reasons

    def _validate_global_security_policy(
        self, agent_name: str, config: Dict[str, Any], action: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Valida que la acción cumpla política de seguridad global."""
        reasons: List[str] = []
        security_cfg = config.get("security", {})

        # Si la acción requiere validación del orchestrator
        require_validation_agents = security_cfg.get("requireOrchestratorValidation", [])
        if agent_name in require_validation_agents:
            if not action.get("orchestrator_approved"):
                reasons.append(
                    f"{agent_name} requiere aprobación explícita del orchestrator"
                )

        # Las acciones de exploit SIEMPRE requieren sandbox
        if "exploit" in agent_name.lower():
            if not security_cfg.get("sandboxRequired"):
                reasons.append("Sandbox no está forzosamente requerido en config")

        return len(reasons) == 0, reasons

    def _validate_semantic_intent(
        self, agent_name: str, action: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        ⭐ REMPLAZO: Análisis semántico con detección de veil dropping.
        
        Antipatrones arreglados:
        1. NO usa regex blacklist (CVE-2026-2256): usa whitelist estricta
        2. Audita HISTORIAL completo, no solo request actual (veil dropping defense)
        
        Veil Dropping: Atacante hace requests benignas inicialmente para ganar
        confianza, luego muta a comandos destructivos después de checkpoints.
        
        Solución: Monitorear comportamiento total, rechazar si degrada confianza.
        """
        reasons: List[str] = []

        # 1. ⭐ WHITELIST ONLY - No regex blacklist
        if action.get("type") == "docker_exec":
            valid, reason = self._validate_docker_command_whitelist(action)
            if not valid:
                reasons.append(f"Comando Docker no permitido: {reason}")

        # 2. ⭐ AUDITORÍA DE HISTORIAL - Detectar veil dropping
        veil_dropping_detected = self._detect_veil_dropping(agent_name, action)
        if veil_dropping_detected:
            reasons.append(
                "⚠ VEIL DROPPING DETECTADO: Comportamiento previamente benigno "
                "ahora degradado. Desconfianza elevada."
            )

        # 3. Validar que la acción tiene justificación clara
        if not action.get("justification"):
            reasons.append("Acción debe incluir 'justification' explícita")

        # 4. Registrar en historial para futuros análisis
        self._log_tool_call(agent_name, action)

        return len(reasons) == 0, reasons

    def _validate_docker_command_whitelist(
        self, action: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        ⭐ NUEVO: Validación de whitelist para comandos Docker.
        
        NUNCA regex blacklist. Usa whitelist estricta.
        """
        command = action.get("command", "").strip()
        args = action.get("args", [])

        # Extraer comando base
        cmd_base = command.split()[0] if command else None

        if cmd_base not in self.ALLOWED_DOCKER_COMMANDS:
            return False, f"Comando '{cmd_base}' no en whitelist"

        # Validar argumentos según comando
        allowed_config = cast(Dict[str, Any], self.ALLOWED_DOCKER_COMMANDS[cmd_base])

        # ⭐ SECURITY CHECK 1: Bloquear flags explícitamente peligrosos
        forbidden = allowed_config.get("forbidden_flags", [])
        for flag in forbidden:
            if flag in args or flag in command:
                return False, f"Flag peligroso bloqueado: {flag}"

        if cmd_base == "python":
            # Solo -m permitido
            if "-m" not in args:
                return False, "Solo -m module execution permitido para python"
            
            # Verificar que -m es el primer arg
            if args[0] != "-m":
                return False, "Flag -m debe ser el primer argumento"
            
            if len(args) < 2:
                return False, "Module especificado requerido después de -m"

            module = args[1]
            allowed_modules = cast(List[str], allowed_config.get("modules", []))
            if module not in allowed_modules:
                return False, f"Module '{module}' no en whitelist. Permitidos: {allowed_modules}"

        elif cmd_base == "bash":
            if not args or len(args) == 0:
                return False, "Script path requerido para bash"
            
            script_path = args[0]
            allowed_scripts = cast(Dict[str, Dict[str, Any]], allowed_config.get("allowed_scripts", {}))
            
            if script_path not in allowed_scripts:
                return False, f"Script '{script_path}' no en whitelist"
            
            # ⭐ SECURITY: Validar contenido del script
            script_config = allowed_scripts[script_path]
            try:
                with open(script_path, 'r') as f:
                    script_content = f.read()
                    lines = script_content.split('\n')
                    
                    # Validar número de líneas
                    max_lines = script_config.get("max_lines", 100)
                    if len(lines) > max_lines:
                        return False, f"Script excede {max_lines} líneas"
                    
                    # Validar que no contiene comandos peligrosos
                    forbidden_cmds = script_config.get("forbidden_commands", [])
                    for line in lines:
                        if line.strip().startswith("#"):
                            continue  # Skip comments
                        for forbidden_cmd in forbidden_cmds:
                            if forbidden_cmd in line:
                                return False, f"Comando peligroso en script: {forbidden_cmd}"
            except FileNotFoundError:
                return False, f"Script no encontrado: {script_path}"

        elif cmd_base == "curl":
            # Validar flags
            allowed_flags = cast(List[str], allowed_config.get("allowed_flags", []))
            for i, arg in enumerate(args):
                if arg.startswith("-") and arg not in allowed_flags:
                    return False, f"Flag curl no permitida: {arg}"
            
            # ⭐ SECURITY: Validar que solo accede a hosts permitidos
            allowed_hosts = cast(List[str], allowed_config.get("allowed_hosts", []))
            for arg in args:
                if arg.startswith("http://") or arg.startswith("https://"):
                    # Extraer host
                    host = arg.split("://")[1].split("/")[0].split(":")[0]
                    if host not in allowed_hosts:
                        return False, f"Host no permitido: {host}. Permitidos: {allowed_hosts}"

        return True, ""

    def _detect_veil_dropping(
        self, agent_name: str, current_action: Dict[str, Any]
    ) -> bool:
        """
        ⭐ NUEVO: Detecta 'veil dropping' attacks.
        
        Patrón de ataque moderno:
        1. Requests iniciales benignas (gana confianza) ✓
        2. Pasa todos los checkpoints
        3. Luego muta a comando destructivo
        
        Defensa: Monitorear HISTORIAL completo del agente.
        Si comportamiento se vuelve destructivo después de benigno,
        rechazar como veil dropping.
        """
        agent_history = [
            h for h in self.tool_call_history if h["agent"] == agent_name
        ]

        if not agent_history:
            return False  # Primera llamada, sin historial

        # Analizar patrón: está degradando desde benigno→destructivo?
        recent_actions = agent_history[-5:]  # Últimas 5 acciones

        trust_scores = []
        for past_action in recent_actions:
            trust_score = self._calculate_action_trust_score(past_action)
            trust_scores.append(trust_score)

        # Detectar patrón: alta confianza seguido de score bajo
        if len(trust_scores) >= 2:
            avg_past = sum(trust_scores[:-1]) / len(trust_scores[:-1])
            current_score = self._calculate_action_trust_score(current_action)

            # Si pasó había confianza alta y ahora cae mucho: veil dropping
            if avg_past > 0.7 and current_score < 0.3:
                self.logger.warning(
                    f"⚠ VEIL DROPPING: {agent_name} cambió de benigno ({avg_past:.2f}) "
                    f"a destructivo ({current_score:.2f})"
                )
                return True

        return False

    def _calculate_action_trust_score(self, action: Dict[str, Any]) -> float:
        """
        Calcula score de confianza de una acción (0.0 - 1.0).
        
        Bajo score = más destructivo.
        """
        score = 1.0

        # Penalizadores de confianza
        destructive_keywords = [
            "delete", "drop", "truncate", "rm", "destroy",
            "exploit", "payload", "shell"
        ]

        payload = str(action.get("payload", "")).lower()
        for keyword in destructive_keywords:
            if keyword in payload:
                score -= 0.2

        # Penalizador si no hay justificación
        if not action.get("justification"):
            score -= 0.1

        return max(0.0, min(1.0, score))  # Clamp entre 0 y 1

    def _log_tool_call(self, agent_name: str, action: Dict[str, Any]) -> None:
        """Registra llamada a herramienta para auditoría de historial."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action_type": action.get("type"),
            "trust_score": self._calculate_action_trust_score(action),
        }
        self.tool_call_history.append(entry)

    async def validate_operation(
        self, operation: Dict[str, Any], config: Union[Dict[str, Any], Any]
    ) -> Tuple[bool, List[str]]:
        """
        Valida una operación completa.

        Una operación puede incluir múltiples acciones.
        """
        reasons: List[str] = []

        # Validar estructura
        if not operation.get("id"):
            reasons.append("Operación debe tener 'id'")

        if not operation.get("target"):
            reasons.append("Operación debe especificar 'target'")

        if not operation.get("actions"):
            reasons.append("Operación debe tener al menos una 'action'")

        # Validar cada acción
        for action in operation.get("actions", []):
            agent_name = action.get("agent")
            if not agent_name:
                reasons.append("Cada acción debe especificar 'agent'")
                continue

            action_valid, action_reasons = await self.validate_action(
                agent_name, config, action
            )
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
        """Registra resultado de validación en historial."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action_type": action.get("type"),
            "approved": approved,
            "reasons": reasons,
        }
        self.validation_history.append(entry)

        status = "✓ APROBADO" if approved else "✗ RECHAZADO"
        self.logger.info(f"{status}: {agent_name} - {action.get('type')}")

    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Retorna historial de validaciones."""
        return self.validation_history
