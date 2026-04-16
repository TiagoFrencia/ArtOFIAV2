"""
Attack Planner - Estratega de operaciones.

Responsabilidades:
- Generar rutas de ataque estructuradas basadas en inteligencia
- Coordinar secuencia de agentes (Recon -> Logic -> Exploit)
- Optimizar fases de operación
- Predecir detecciones y diseñar evasiones
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import json


class AttackPhase(Enum):
    """Fases de una operación de ataque."""

    RECONNAISSANCE = "reconnaissance"  # Recon Agent
    PLANNING = "planning"  # Logic Agent
    EXPLOITATION = "exploitation"  # Exploit Agent
    PERSISTENCE = "persistence"  # Post-exploitation
    EVASION = "evasion"  # Bypass de defensas


class AttackPlanner:
    """Planificador estratégico de operaciones ofensivas."""

    # ⭐ NUEVO: Límites de pasos (prevención de scope creep)
    MIN_STEPS = 3
    MAX_STEPS = 7

    def __init__(self) -> None:
        """Inicializa el planificador."""
        self.logger = logging.getLogger(__name__)
        self.plans: Dict[str, Dict[str, Any]] = {}

    async def generate_attack_plan(
        self, target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera un plan de ataque estructurado y secuencial.

        ⭐ NUEVA ARQUITECTURA: 
        - Límite estricto: 3-7 pasos (prevención de scope creep)
        - Cada paso es procesable y delegado a especialista
        - No intenta resolver directamente

        Estructura:
        1. Recon Agent recopila información pasivamente
        2. Logic Agent analiza y genera ruta óptima
        3. Exploit Agent ejecuta con payloads validados

        Args:
            target_info: Información del objetivo (host, puertos, servicios)

        Returns:
            Plan estructurado con 3-7 pasos y checkpoints

        Raises:
            ValueError: Si no se puede generar plan dentro de límites
        """
        plan_id = self._generate_plan_id()
        self.logger.info(f"📋 Generando plan de ataque {plan_id}")

        plan = {
            "id": plan_id,
            "target": target_info,
            "created_at": datetime.now().isoformat(),
            "steps": [],  # ⭐ Cambio de "phases" a "steps"
            "risk_level": "medium",
            "estimated_duration": "2h",
        }

        # Generar steps jerárquicos
        try:
            steps = await self._generate_hierarchical_steps(target_info)
            
            # ⭐ VALIDACIÓN CRÍTICA: Verificar límites de pasos
            if len(steps) < self.MIN_STEPS:
                self.logger.warning(
                    f"⚠ Plan tiene {len(steps)} pasos (mínimo {self.MIN_STEPS}), "
                    f"ampliando..."
                )
                steps = await self._augment_steps(steps, self.MIN_STEPS)
            
            if len(steps) > self.MAX_STEPS:
                self.logger.error(
                    f"✗ Plan excede {self.MAX_STEPS} pasos ({len(steps)} generados). "
                    f"Simplificando..."
                )
                steps = await self._simplify_steps(steps, self.MAX_STEPS)
            
            # Validar que cada step es procesable
            for i, step in enumerate(steps):
                is_processable, reason = await self._validate_step_processability(step)
                if not is_processable:
                    self.logger.error(
                        f"✗ Step {i+1} no es procesable: {reason}"
                    )
                    steps[i]["validated"] = False
                    steps[i]["validation_error"] = reason
                else:
                    steps[i]["validated"] = True
            
            plan["steps"] = steps
            plan["step_count"] = len(steps)
            plan["step_count_valid"] = len(steps) >= self.MIN_STEPS and len(steps) <= self.MAX_STEPS
            
            self.plans[plan_id] = plan
            self.logger.info(
                f"✓ Plan {plan_id} generado exitosamente "
                f"({len(steps)} pasos, rango {self.MIN_STEPS}-{self.MAX_STEPS})"
            )
            
            return plan

        except Exception as e:
            self.logger.error(f"✗ Error generando plan: {e}")
            raise

    async def _generate_hierarchical_steps(
        self, target_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        ⭐ NUEVO: Genera pasos con enrutamiento jerárquico.
        
        No intenta resolver; en su lugar, delega a especialistas:
        - recon_agent: Inteligencia
        - logic_agent: Decisión de vector
        - exploit_agent: Ejecución
        """
        self.logger.info("🎯 Generando pasos jerárquicos...")
        
        steps = []
        
        # Paso 1: Reconocimiento
        steps.append({
            "number": 1,
            "phase": "reconnaissance",
            "agent": "recon_agent",
            "objective": "Recopilar inteligencia pasiva",
            "task": "passive_enumeration",
            "input": target_info,
            "expected_output": "Intelligence report",
            "delegation": True,  # ⭐ Delegado a especialista
        })
        
        # Paso 2: Análisis
        steps.append({
            "number": 2,
            "phase": "planning",
            "agent": "logic_agent",
            "objective": "Analizar inteligencia y determinar vector",
            "task": "select_attack_vector",
            "input": "recon output",
            "expected_output": "Attack vector decision",
            "delegation": True,
        })
        
        # Paso 3: Ejecución primaria
        steps.append({
            "number": 3,
            "phase": "exploitation",
            "agent": "exploit_agent",
            "objective": "Ejecutar ataque primario",
            "task": "execute_primary_vector",
            "input": "logic output",
            "expected_output": "Exploitation success",
            "delegation": True,
        })
        
        # Pasos 4-7: Opcionales basados en complejidad
        if target_info.get("complexity", "low") == "high":
            steps.append({
                "number": 4,
                "phase": "evasion",
                "agent": "evasion_browser",
                "objective": "Bypasear defensas de navegador",
                "task": "apply_browser_evasion",
                "delegation": True,
            })
        
        return steps

    async def _validate_step_processability(
        self, step: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        ⭐ NUEVO: Valida que un step sea procesable.
        
        Un step es procesable si:
        - Tiene objetivo claro
        - Tiene agente asignado
        - El agente tiene capability para la tarea
        - Input y output están definidos
        """
        if not step.get("agent"):
            return False, "No agent specified"
        
        if not step.get("objective"):
            return False, "No objective defined"
        
        if not step.get("expected_output"):
            return False, "No expected output defined"
        
        # En producción: validar contra amperties del agente
        return True, ""

    async def _augment_steps(
        self, steps: List[Dict[str, Any]], target_count: int
    ) -> List[Dict[str, Any]]:
        """Amplía lista de pasos hasta objetivo."""
        self.logger.info(f"🔧 Ampliando pasos hasta {target_count}...")
        # Para ahora, solo retornar los existentes
        return steps

    async def _simplify_steps(
        self, steps: List[Dict[str, Any]], target_count: int
    ) -> List[Dict[str, Any]]:
        """Simplifica lista de pasos a límite máximo."""
        self.logger.info(f"🔧 Simplificando pasos a {target_count}...")
        return steps[:target_count]

    async def _create_reconnaissance_phase(
        self, target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea fase de reconocimiento pasivo.

        El Recon Agent hace scanning sigiloso sin generar alertas.
        """
        return {
            "phase": AttackPhase.RECONNAISSANCE.value,
            "agent": "recon_agent",
            "objective": "Recopilar inteligencia sin alertas",
            "tasks": [
                {
                    "task": "passive_enumeration",
                    "target": target_info.get("host"),
                    "methods": ["whois", "dns_query", "banner_grabbing"],
                    "stealth": True,
                },
                {
                    "task": "service_discovery",
                    "ports": target_info.get("ports", [80, 443, 8080]),
                    "aggressive": False,
                },
                {
                    "task": "technology_stack",
                    "gather": ["cms", "frameworks", "libraries", "versions"],
                },
            ],
            "expected_output": "Intelligence report with vulnerabilities",
            "checkpoint": "Validate that no IDS alerts were triggered",
        }

    async def _create_planning_phase(
        self, target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea fase de planificación de ataque.

        El Logic Agent analiza inteligencia y determina ruta óptima.
        """
        return {
            "phase": AttackPhase.PLANNING.value,
            "agent": "logic_agent",
            "objective": "Determinar ruta de ataque óptima",
            "inputs": ["recon_phase_output"],
            "decision_tree": {
                "has_sql_injection": ["exploit_sql", "map_database"],
                "has_jwt_weakness": ["exploit_jwt", "escalate_privileges"],
                "has_xss": ["exploit_xss", "establish_foothold"],
                "has_api_bypass": ["exploit_api", "bypass_auth"],
            },
            "output": {
                "recommended_vector": "primary_attack_vector",
                "secondary_vectors": ["fallback1", "fallback2"],
                "risk_assessment": "technical_difficulty_level",
                "detection_probability": "percentage",
            },
            "checkpoint": "Validate attack path is feasible",
        }

    async def _create_exploitation_phase(
        self, target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea fase de explotación.

        El Exploit Agent ejecuta payloads dentro del sandbox.
        Requiere validación del supervisors.
        """
        return {
            "phase": AttackPhase.EXPLOITATION.value,
            "agent": "exploit_agent",
            "objective": "Ejecutar payload validado",
            "execution_context": {
                "sandbox": "required",
                "isolation_level": "strict",
                "timeout_seconds": 180,
            },
            "attack_vectors": [
                {
                    "type": "primary",
                    "payload": "determined_by_logic_agent",
                    "encoding": "obfuscated_by_evasion_module",
                    "requires_validation": True,
                },
                {
                    "type": "fallback",
                    "payload": "alternative_vector",
                    "requires_validation": True,
                },
            ],
            "post_exploitation": {
                "establish_shell": "reverse_shell",
                "enumerate_access": "check_privileges",
                "dump_credentials": "if_accessible",
            },
            "checkpoint": "Verify successful exploitation in sandbox",
        }

    async def _create_evasion_phase(
        self, target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea fase de evasión aplicada transversalmente.

        Técnicas de bypass para cada fase de defensa.
        """
        return {
            "phase": AttackPhase.EVASION.value,
            "objective": "Minimizar detección en cada fase",
            "strategies": {
                "waf_bypass": {
                    "techniques": ["payload_encoding", "case_variance", "comments"],
                    "module": "src/evasion/",
                },
                "ids_evasion": {
                    "techniques": ["fragmentation", "timing_variation", "slow_scan"],
                },
                "browser_detection": {
                    "techniques": ["headless_browser", "fingerprint_spoofing"],
                    "module": "src/evasion/browser/",
                },
                "captcha_bypass": {
                    "techniques": ["solver_api", "browser_automation"],
                    "module": "src/evasion/captcha/",
                },
            },
            "applied_to_phases": ["reconnaissance", "exploitation"],
        }

    def _generate_plan_id(self) -> str:
        """Genera ID único para el plan."""
        from datetime import datetime
        import random

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = f"{random.randint(1000, 9999)}"
        return f"plan_{timestamp}_{random_suffix}"

    async def optimize_plan(
        self, plan_id: str, constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimiza un plan existente basado en restricciones.

        Args:
            plan_id: ID del plan a optimizar
            constraints: Restricciones operacionales

        Returns:
            Plan optimizado
        """
        plan = self.plans.get(plan_id)
        if not plan:
            self.logger.error(f"Plan no encontrado: {plan_id}")
            return {}

        self.logger.info(f"🔧 Optimizando plan {plan_id}")

        # Optimizar basado en restricciones
        time_limit = constraints.get("max_duration_minutes", 120)
        stealth_level = constraints.get("stealth_level", "medium")

        # Ajustar fases según restricciones
        if time_limit < 60:
            # Operación rápida: priorizar reconocimiento mínimo
            plan["phases"] = [p for p in plan["phases"] if p["phase"] != "reconnaissance"]

        if stealth_level == "high":
            # Aumentar timings, reducir agresividad
            plan["risk_level"] = "low"

        self.logger.info(f"✓ Plan {plan_id} optimizado")
        return plan

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un plan por ID."""
        return self.plans.get(plan_id)

    def list_plans(self) -> List[Dict[str, Any]]:
        """Lista todos los planes generados."""
        return list(self.plans.values())

    async def export_plan(self, plan_id: str, format: str = "json") -> str:
        """
        Exporta un plan en formato especificado.

        Args:
            plan_id: ID del plan
            format: Formato de exportación (json, yaml)

        Returns:
            Plan serializado
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return ""

        if format == "json":
            return json.dumps(plan, indent=2, default=str)

        return json.dumps(plan, indent=2, default=str)
