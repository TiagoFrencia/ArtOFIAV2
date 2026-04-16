"""
Workflow Analyzer - Business Logic Flaw Detection
===================================================
Módulo especializado en analizar flujos de negocio para identificar
anomalías, ataques de lógica y evasión de controles.

Técnicas:
- Step alteration (modificar orden de pasos)
- Step skipping (omitir pasos de validación)
- Payment bypass (evadir pagos)
- Race conditions (condiciones de carrera)
- Authorization bypass (saltar validación)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowFlaw(str, Enum):
    """Tipos de fallos en flujos de negocio"""
    STEP_ALTERATION = "step_alteration"
    STEP_SKIPPING = "step_skipping"
    RACE_CONDITION = "race_condition"
    PAYMENT_BYPASS = "payment_bypass"
    AUTHORIZATION_BYPASS = "authorization_bypass"
    STATE_MANIPULATION = "state_manipulation"
    TIMING_ATTACK = "timing_attack"


@dataclass
class WorkflowVulnerability:
    """Vulnerabilidad de flujo identificada"""
    flaw_type: WorkflowFlaw
    workflow_name: str
    affected_steps: List[int]
    risk_level: str
    confidence: float
    attack_scenario: str
    remediation: str


class WorkflowAnalyzer:
    """
    Analizador de flujos de negocio.
    
    Detecta:
    - Pasos omitibles
    - Validaciones bypasseables
    - Condiciones de carrera
    - Manipulación de estado
    """
    
    def __init__(self):
        self.common_workflows = {
            "login_flow": [
                "request_credentials",
                "validate_username",
                "validate_password",
                "check_mfa",
                "issue_session_token",
            ],
            "payment_flow": [
                "add_to_cart",
                "enter_payment_info",
                "validate_payment",
                "charge_amount",
                "confirm_order",
            ],
            "password_reset": [
                "request_reset",
                "send_email",
                "validate_token",
                "set_new_password",
                "confirm_reset",
            ],
            "account_creation": [
                "enter_email",
                "validate_email_format",
                "check_email_uniqueness",
                "set_password",
                "create_account",
            ],
            "permission_escalation": [
                "check_current_role",
                "request_elevated_action",
                "verify_authorization",
                "execute_action",
                "log_action",
            ],
        }
        
        self.analysis_history = []
    
    async def analyze_workflow(self, workflow_name: str, endpoints: List[Dict[str, Any]],
                              findings: Dict[str, Any], framework: Optional[str] = None) -> Optional[Any]:
        """
        Analizar flujo específico para identificar vulnerabilidades.
        """
        
        if workflow_name not in self.common_workflows:
            logger.debug(f"Unknown workflow: {workflow_name}")
            return None
        
        workflow_steps = self.common_workflows[workflow_name]
        
        # Buscar endpoints relacionados al flujo
        related_endpoints = self._find_workflow_endpoints(workflow_name, endpoints)
        
        if not related_endpoints:
            logger.debug(f"No endpoints found for {workflow_name}")
            return None
        
        # Analizar vulnerabilidades potenciales
        vulnerabilities = await self._detect_workflow_flaws(
            workflow_name, workflow_steps, related_endpoints, findings
        )
        
        if vulnerabilities:
            logger.info(f"Found {len(vulnerabilities)} flaws in {workflow_name}")
            return {
                "workflow": workflow_name,
                "vulnerabilities": vulnerabilities,
                "endpoints": related_endpoints,
                "attack_scenarios": await self._generate_attack_scenarios(vulnerabilities)
            }
        
        return None
    
    async def detect_business_logic_flaws(self, endpoints: List[Dict[str, Any]],
                                         findings: Dict[str, Any]) -> List[Any]:
        """
        Detectar fallos de lógica de negocio generalizados.
        """
        
        flaws = []
        
        # Detección 1: Pasos omitibles
        skippable = await self._detect_skippable_steps(endpoints, findings)
        flaws.extend(skippable)
        
        # Detección 2: Condiciones de carrera
        race_conditions = await self._detect_race_conditions(endpoints, findings)
        flaws.extend(race_conditions)
        
        # Detección 3: Manipulación de estado
        state_manipulations = await self._detect_state_manipulation(endpoints, findings)
        flaws.extend(state_manipulations)
        
        return flaws
    
    def _find_workflow_endpoints(self, workflow_name: str, 
                                endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Encontrar endpoints relacionados a un flujo específico"""
        
        workflow_keywords = {
            "login": ["login", "auth", "signin"],
            "payment": ["payment", "checkout", "charge", "purchase"],
            "password_reset": ["reset", "password", "recover"],
            "account_creation": ["register", "signup", "account"],
        }
        
        keywords = workflow_keywords.get(workflow_name, [])
        related = []
        
        for endpoint in endpoints:
            path = endpoint.get("path", "").lower()
            if any(kw in path for kw in keywords):
                related.append(endpoint)
        
        return related
    
    async def _detect_workflow_flaws(self, workflow_name: str, steps: List[str],
                                    endpoints: List[Dict[str, Any]],
                                    findings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectar vulnerabilidades específicas del flujo"""
        
        flaws = []
        
        # Flaw 1: Pasos omitibles
        if "missing_endpoints" in findings or "404_bypasses" in findings:
            flaws.append({
                "type": "step_skipping",
                "description": f"Pasos omitibles en {workflow_name}",
                "risk_level": "high",
                "steps": steps,
            })
        
        # Flaw 2: Estado manipulable
        if "state_parameters" in findings:
            flaws.append({
                "type": "state_manipulation",
                "description": "Parámetros de estado sin validación",
                "risk_level": "high",
                "affected_params": findings.get("state_parameters", []),
            })
        
        # Flaw 3: Race conditions
        if "timing_sensitive_endpoints" in findings:
            flaws.append({
                "type": "race_condition",
                "description": "Endpoints sensibles a timing",
                "risk_level": "medium",
            })
        
        await asyncio.sleep(0.05)  # Simular procesamiento
        
        return flaws
    
    async def _detect_skippable_steps(self, endpoints: List[Dict[str, Any]],
                                     findings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectar pasos que pueden omitirse"""
        
        skippable = []
        
        # Buscar endpoints opcionales o mal validados
        for endpoint in endpoints:
            method = endpoint.get("method", "GET").upper()
            
            # Si POST directo a checkout sin validación previa
            if "checkout" in endpoint.get("path", "") and method == "POST":
                skippable.append({
                    "type": "step_skipping",
                    "endpoint": endpoint,
                    "reason": "Direct checkout without cart validation",
                    "risk": "high",
                })
        
        return skippable
    
    async def _detect_race_conditions(self, endpoints: List[Dict[str, Any]],
                                     findings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectar condiciones de carrera"""
        
        race_conditions = []
        
        # Endpoints que manejan transacciones
        transaction_endpoints = [ep for ep in endpoints if "transaction" in ep.get("path", "").lower()]
        
        if transaction_endpoints:
            race_conditions.append({
                "type": "race_condition",
                "endpoints": transaction_endpoints,
                "scenario": "Concurrent transaction manipulation",
                "risk": "high",
            })
        
        return race_conditions
    
    async def _detect_state_manipulation(self, endpoints: List[Dict[str, Any]],
                                        findings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detectar manipulación de estado"""
        
        manipulations = []
        
        # Buscar parámetros de estado en requests
        if "parameters" in findings:
            state_params = [p for p in findings["parameters"] if p in ["status", "state", "step", "auth"]]
            
            if state_params:
                manipulations.append({
                    "type": "state_manipulation",
                    "parameters": state_params,
                    "scenario": "Modify flow state",
                    "risk": "medium",
                })
        
        return manipulations
    
    async def _generate_attack_scenarios(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generar escenarios de ataque basados en vulnerabilidades encontradas"""
        
        scenarios = []
        
        for vuln in vulnerabilities:
            if vuln["type"] == "step_skipping":
                scenarios.append(f"Omitir validación y acceder directamente a endpoint final")
            elif vuln["type"] == "state_manipulation":
                scenarios.append(f"Modificar parámetro de estado para cambiar flujo")
            elif vuln["type"] == "race_condition":
                scenarios.append(f"Ejecutar operaciones concurrentes para race condition")
        
        return scenarios
