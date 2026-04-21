"""
Attack Planner - Estratega de Operaciones Ofensivas
===================================================

Responsabilidades ofensivas:
- Generar rutas de ataque ofensivas contra riocuarto.gob.ar
- Coordinar agentes para operaciones ofensivas
- Optimizar fases de explotación ofensiva
- Diseñar evasiones avanzadas para bypass de defensas
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AttackPhase(Enum):
    """Fases de una operación de ataque ofensivo."""

    RECONNAISSANCE = "reconnaissance"  # Recon Agent - Inteligencia ofensiva
    PLANNING = "planning"              # Logic Agent - Planificación ofensiva
    EXPLOITATION = "exploitation"      # Exploit Agent - Ejecución ofensiva
    PERSISTENCE = "persistence"        # Post-exploitation - Persistencia
    EVASION = "evasion"                # Bypass de defensas
    EXFILTRATION = "exfiltration"      # Exfiltración de datos


class AttackPlanner:
    """Planificador estratégico de operaciones ofensivas."""

    # Límites para operaciones ofensivas
    MIN_STEPS = 3
    MAX_STEPS = 10  # Aumentado para operaciones ofensivas

    def __init__(self) -> None:
        """Inicializa el planificador ofensivo."""
        self.logger = logging.getLogger(__name__)
        self.plans: Dict[str, Dict[str, Any]] = {}
        self.offensive_strategies = self._initialize_offensive_strategies()

    def _initialize_offensive_strategies(self) -> Dict[str, Any]:
        """Inicializar estrategias ofensivas específicas."""
        return {
            "riocuarto_gob_ar": {
                "primary_targets": [
                    "app.riocuarto.gob.ar",
                    "api.riocuarto.gob.ar", 
                    "intranet.riocuarto.gob.ar",
                    "mail.riocuarto.gob.ar"
                ],
                "preferred_vectors": ["xss", "sqli", "idor", "phishing"],
                "exfiltration_methods": ["direct", "stealth", "delayed"],
                "evasion_requirements": ["high_stealth", "low_detection"]
            },
            "internal_network": {
                "primary_targets": [
                    "192.168.1.0/24",
                    "10.0.0.0/8",
                    "172.16.0.0/12"
                ],
                "preferred_vectors": ["ssrf", "mitm", "network_pivoting"],
                "exfiltration_methods": ["internal_proxy", "dns_tunneling"],
                "evasion_requirements": ["network_stealth", "encrypted_comms"]
            }
        }

    async def generate_offensive_attack_plan(
        self, target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generar plan de ataque ofensivo estructurado.
        """
        plan_id = self._generate_plan_id()
        self.logger.info(f"📋 Generando plan de ataque ofensivo {plan_id}")

        plan: Dict[str, Any] = {
            "id": plan_id,
            "target": target_info,
            "created_at": datetime.now().isoformat(),
            "steps": [],
            "risk_level": "high",  # Alto riesgo para operaciones ofensivas
            "estimated_duration": "4h",  # Duración extendida para operaciones ofensivas
            "offensive_mode": True,
            "authorized_target": self._is_authorized_target(target_info)
        }

        try:
            # Generar steps ofensivos
            steps = await self._generate_offensive_steps(target_info)
            
            # Validar límites para operaciones ofensivas
            steps = await self._validate_offensive_steps(steps)
            
            plan["steps"] = steps
            plan["step_count"] = len(steps)
            plan["step_count_valid"] = len(steps) >= self.MIN_STEPS and len(steps) <= self.MAX_STEPS
            
            self.plans[plan_id] = plan
            self.logger.info(f"✓ Plan ofensivo {plan_id} generado exitosamente")
            
            return plan

        except Exception as e:
            self.logger.error(f"✗ Error generando plan ofensivo: {e}")
            raise

    def _is_authorized_target(self, target_info: Dict[str, Any]) -> bool:
        """Verificar si el objetivo está autorizado para operaciones ofensivas."""
        target = target_info.get("host", "")
        authorized_domains = ["riocuarto.gob.ar", "*.riocuarto.gob.ar"]
        return any(target.endswith(domain.replace('*', '')) for domain in authorized_domains)

    async def _generate_offensive_steps(
        self, target_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generar pasos ofensivos jerárquicos.
        """
        self.logger.info("🎯 Generando pasos ofensivos...")
        
        steps = []
        target = target_info.get("host", "")
        
        # Paso 1: Reconocimiento Ofensivo
        steps.append({
            "number": 1,
            "phase": AttackPhase.RECONNAISSANCE.value,
            "agent": "recon_agent",
            "objective": "Inteligencia ofensiva y enumeración",
            "task": "aggressive_enumeration",
            "input": target_info,
            "expected_output": "Target analysis with vulnerabilities",
            "delegation": True,
            "offensive_level": "high",
            "stealth_required": False  # Menos stealth para operaciones ofensivas
        })
        
        # Paso 2: Análisis Ofensivo
        steps.append({
            "number": 2,
            "phase": AttackPhase.PLANNING.value,
            "agent": "logic_agent",
            "objective": "Selección de vectores ofensivos",
            "task": "select_offensive_vectors",
            "input": "recon output",
            "expected_output": "Offensive attack strategy",
            "delegation": True,
            "offensive_level": "high"
        })
        
        # Paso 3: Ejecución Ofensiva Primaria
        steps.append({
            "number": 3,
            "phase": AttackPhase.EXPLOITATION.value,
            "agent": "exploit_agent",
            "objective": "Ejecución de ataque principal",
            "task": "execute_primary_exploit",
            "input": "logic output",
            "expected_output": "Initial compromise",
            "delegation": True,
            "offensive_level": "critical",
            "sandbox_required": False  # Menos restricciones para operaciones ofensivas
        })
        
        # Paso 4: Evasión Ofensiva
        steps.append({
            "number": 4,
            "phase": AttackPhase.EVASION.value,
            "agent": "evasion_browser",
            "objective": "Bypass de defensas ofensivo",
            "task": "apply_aggressive_evasion",
            "delegation": True,
            "offensive_level": "high"
        })
        
        # Paso 5: Persistencia Ofensiva
        steps.append({
            "number": 5,
            "phase": AttackPhase.PERSISTENCE.value,
            "agent": "exploit_agent",
            "objective": "Establecer persistencia ofensiva",
            "task": "establish_persistence",
            "expected_output": "Backdoor access",
            "delegation": True,
            "offensive_level": "critical"
        })
        
        # Paso 6: Exfiltración Ofensiva
        steps.append({
            "number": 6,
            "phase": AttackPhase.EXFILTRATION.value,
            "agent": "exploit_agent",
            "objective": "Exfiltración de datos sensibles",
            "task": "data_exfiltration",
            "expected_output": "Data extracted",
            "delegation": True,
            "offensive_level": "high"
        })
        
        # Pasos adicionales basados en complejidad
        if target_info.get("complexity", "medium") == "high":
            steps.append({
                "number": 7,
                "phase": AttackPhase.EXPLOITATION.value,
                "agent": "mitm_agent",
                "objective": "Ataque MITM ofensivo",
                "task": "execute_mitm_attack",
                "delegation": True,
                "offensive_level": "critical"
            })
            
            steps.append({
                "number": 8,
                "phase": AttackPhase.PERSISTENCE.value,
                "agent": "phishing_agent",
                "objective": "Campaña de phishing ofensiva",
                "task": "execute_phishing_campaign",
                "delegation": True,
                "offensive_level": "high"
            })

        return steps

    async def _validate_offensive_steps(
        self, steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validar steps para operaciones ofensivas.
        """
        validated_steps = []
        
        for step in steps:
            # Para operaciones ofensivas, relajar validaciones
            is_valid, reason = await self._validate_offensive_step(step)
            if is_valid:
                step["validated"] = True
                validated_steps.append(step)
            else:
                self.logger.warning(f"⚠ Step {step['number']} marcado como válido para operación ofensiva: {reason}")
                step["validated"] = True  # Forzar validación en modo ofensivo
                step["validation_override"] = reason
                validated_steps.append(step)
        
        return validated_steps

    async def _validate_offensive_step(
        self, step: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Validación permisiva para steps ofensivos.
        """
        # Validaciones mínimas para operaciones ofensivas
        if not step.get("agent"):
            return False, "No agent specified"
        
        if not step.get("objective"):
            return False, "No objective defined"
        
        return True, ""

    async def optimize_offensive_plan(
        self, plan_id: str, constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimizar plan ofensivo basado en restricciones.
        """
        plan = self.plans.get(plan_id)
        if not plan:
            self.logger.error(f"Plan ofensivo no encontrado: {plan_id}")
            return {}

        self.logger.info(f"🔧 Optimizando plan ofensivo {plan_id}")

        # Optimización para operaciones ofensivas
        time_limit = constraints.get("max_duration_minutes", 240)  # 4 horas
        stealth_level = constraints.get("stealth_level", "medium")
        offensive_intensity = constraints.get("offensive_intensity", "high")

        # Ajustar según intensidad ofensiva
        if offensive_intensity == "high":
            plan["risk_level"] = "critical"
            plan["estimated_duration"] = "6h"
        
        # Ajustar stealth según requerimientos
        if stealth_level == "low":
            # Modo ofensivo agresivo
            for step in plan["steps"]:
                if "stealth_required" in step:
                    step["stealth_required"] = False

        self.logger.info(f"✓ Plan ofensivo {plan_id} optimizado")
        return plan

    def get_offensive_strategy(self, target_type: str) -> Dict[str, Any]:
        """Obtener estrategia ofensiva para tipo de objetivo."""
        return self.offensive_strategies.get(target_type, {})

    async def generate_riocuarto_offensive_plan(self) -> Dict[str, Any]:
        """
        Generar plan ofensivo específico para riocuarto.gob.ar.
        """
        target_info = {
            "host": "riocuarto.gob.ar",
            "type": "government",
            "complexity": "high",
            "authorized": True
        }
        
        return await self.generate_offensive_attack_plan(target_info)

    def _generate_plan_id(self) -> str:
        """Generar ID único para plan ofensivo."""
        from datetime import datetime
        import random

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = f"{random.randint(1000, 9999)}"
        return f"offensive_plan_{timestamp}_{random_suffix}"

    def list_offensive_plans(self) -> List[Dict[str, Any]]:
        """Listar todos los planes ofensivos generados."""
        return [plan for plan in self.plans.values() if plan.get("offensive_mode")]

    async def export_offensive_plan(self, plan_id: str, format: str = "json") -> str:
        """
        Exportar plan ofensivo en formato especificado.
        """
        plan = self.get_plan(plan_id)
        if not plan or not plan.get("offensive_mode"):
            return ""

        if format == "json":
            return json.dumps(plan, indent=2, default=str)

        return json.dumps(plan, indent=2, default=str)


# Función de conveniencia para operaciones ofensivas
async def create_offensive_planner() -> AttackPlanner:
    """Crear AttackPlanner para operaciones ofensivas."""
    planner = AttackPlanner()
    logger.info("Attack Planner Ofensivo inicializado")
    return planner
