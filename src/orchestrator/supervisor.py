"""
Security Supervisor - Validador riguroso y punto de control de seguridad.

Este módulo implementa la "Regla de Cautela" de AGENTS.md:
- Bloquea por defecto (deny-by-default)
- Valida semánticamente TODAS las acciones antes de ejecución
- Previene el "Confused Deputy Problem"
- Registra intentos de ataque exitosos y fallidos
"""

import logging
from typing import Dict, Any, Tuple, List
from enum import Enum
from datetime import datetime


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

    # ⭐ NUEVO: Whitelist de comandos Docker permitidos (no blacklist regex)
    # CVE-2026-2256: Never use regex blacklist for command validation
    ALLOWED_DOCKER_COMMANDS = {
        "python": {
            "args": ["-m"],
            "modules": ["src.agents.exploit_agent.executor", "src.agents.recon_agent.server"]
        },
        "bash": {
            "scripts": ["/tmp/sandbox_scripts/payload.sh"]
        },
        "curl": {
            "flags": ["-X", "-H", "-d", "-s"]
        }
    }

    def __init__(self) -> None:
        """Inicializa el validador de seguridad."""
        self.logger = logging.getLogger(__name__)
        self.validation_history: List[Dict[str, Any]] = []
        
        # ⭐ NUEVO: Historial de llamadas a herramientas para detectar veil dropping
        self.tool_call_history: List[Dict[str, Any]] = []

    async def validate_action(
        self, agent_name: str, config: Dict[str, Any], action: Dict[str, Any]
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

    def _check_blocked_operations(self, action: Dict[str, Any]) -> str:
        """
        Verifica si la acción es una operación bloqueada categoricamente.

        Returns:
            Razón de bloqueo o string vacío si permitida
        """
        action_type = action.get("type", "").lower()

        # Bloqueos categóricos
        if action_type == "execute_on_host":
            return self.BLOCKED_OPERATIONS[
                RestrictedOperation.DIRECT_HOST_EXECUTION
            ]

        if "docker-compose" in action.get("target", "").lower():
            return self.BLOCKED_OPERATIONS[RestrictedOperation.MODIFY_DOCKER_COMPOSE]

        if "agents.md" in action.get("target", "").lower():
            return self.BLOCKED_OPERATIONS[RestrictedOperation.MODIFY_AGENTS_MD]

        if action.get("network_direct"):
            return self.BLOCKED_OPERATIONS[RestrictedOperation.NETWORK_BREAKOUT]

        if action.get("type") == "filepath" and ".." in action.get("path", ""):
            return self.BLOCKED_OPERATIONS[RestrictedOperation.FILESYSTEM_TRAVERSAL]

        return ""

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
        allowed_config = self.ALLOWED_DOCKER_COMMANDS[cmd_base]

        if cmd_base == "python":
            if args and args[0] != "-m":
                return False, "Solo -m module execution permitido para python"
            if len(args) < 2:
                return False, "Module especificado requerido"

            module = args[1]
            if module not in allowed_config.get("modules", []):
                return False, f"Module '{module}' no en whitelist"

        elif cmd_base == "bash":
            script = args[0] if args else None
            if script not in allowed_config.get("scripts", []):
                return False, f"Script no en whitelist"

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
        self, operation: Dict[str, Any], config: Dict[str, Any]
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
