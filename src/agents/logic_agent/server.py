"""
Logic Agent - Semantic Analysis Server
========================================
MCP (Model Context Protocol) server that exposes logical analysis tools.

Responsibilities:
1. Analyze attack workflows from reconnaissance findings
2. Identify business logic flaws
3. Plan multi-step exploitation chains
4. Coordinate with ReconAgent + ExploitAgent
5. Post-exploitation strategy
6. Report generation

Connects to:
- MemorySystem (Neo4j + PostgreSQL)
- Orchestrator (validation + scheduling)
- ExploitAgent (execution)
- ReconAgent (findings input)
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .workflow_analyzer import WorkflowAnalyzer
from .auth_analyzer import AuthAnalyzer
from .post_exploit import PostExploitationPlanner
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Tipos de análisis que el agente lógico puede realizar"""
    WORKFLOW_ANOMALY = "workflow_anomaly"              # Flujos alterados
    AUTH_ESCALATION = "auth_escalation"                # Escalamiento de privilegios
    BUSINESS_LOGIC_FLAW = "business_logic_flaw"        # Errores lógicos
    PRIVILEGE_ESCALATION = "privilege_escalation"      # Escalamiento vertical
    LATERAL_MOVEMENT = "lateral_movement"              # Movimiento lateral
    DATA_EXFILTRATION = "data_exfiltration"            # Exfiltración
    PERSISTENCE = "persistence"                        # Persistencia


@dataclass
class AnalysisRequest:
    """Solicitud de análisis al agente lógico"""
    target_url: str
    reconnaissance_findings: Dict[str, Any]
    endpoints: List[Dict[str, Any]]
    auth_mechanisms: List[str]
    framework: Optional[str] = None
    discovered_workflows: List[str] = None


@dataclass
class AnalysisResult:
    """Resultado del análisis"""
    analysis_type: AnalysisType
    vulnerability_identified: bool
    risk_level: str  # "critical", "high", "medium", "low"
    attack_chain: List[str]  # Pasos sugeridos
    confidence_score: float  # 0.0-1.0
    business_impact: str
    affected_endpoints: List[str]
    recommendations: List[str]
    timestamp: datetime
    details: Dict[str, Any]


class LogicAgent:
    """
    Agente de análisis lógico y planificación.
    
    Flujo:
    1. Recibe hallazgos de ReconAgent
    2. Analiza flujos de negocio
    3. Identifica fallos de lógica
    4. Planifica cadena de ataque
    5. Genera reporte
    6. Coordina post-explotación
    """
    
    def __init__(self, memory_system_ref=None, orchestrator_ref=None):
        """Inicializar agente lógico con referencias al sistema"""
        self.memory_system = memory_system_ref
        self.orchestrator = orchestrator_ref
        
        # Inicializar módulos especializados
        self.workflow_analyzer = WorkflowAnalyzer()
        self.auth_analyzer = AuthAnalyzer()
        self.post_exploiter = PostExploitationPlanner()
        self.report_generator = ReportGenerator()
        
        self.analysis_history = []
        self.stats = {
            "analyses_performed": 0,
            "flaws_identified": 0,
            "successful_chains": 0,
            "avg_confidence": 0.0,
        }
    
    async def analyze_reconnaissance_findings(self, request: AnalysisRequest) -> List[AnalysisResult]:
        """
        Analizar hallazgos de reconocimiento para identificar vectores de ataque.
        
        Ejecuta análisis en paralelo y retorna lista de vulnerabilidades identificadas.
        """
        results = []
        
        logger.info(f"Starting logic analysis for {request.target_url}")
        
        # Análisis 1: Flujos de negocio
        workflow_results = await self._analyze_workflows(request)
        results.extend(workflow_results)
        
        # Análisis 2: Mecanismos de autenticación
        auth_results = await self._analyze_authentication(request)
        results.extend(auth_results)
        
        # Análisis 3: Fallos lógicos transversales
        logic_results = await self._analyze_business_logic(request)
        results.extend(logic_results)
        
        # Actualizar estadísticas
        self.stats["analyses_performed"] += 1
        self.stats["flaws_identified"] += sum(1 for r in results if r.vulnerability_identified)
        
        # Registrar en memoria
        await self._record_analysis(request, results)
        
        return results
    
    async def _analyze_workflows(self, request: AnalysisRequest) -> List[AnalysisResult]:
        """Analizar flujos de negocio para anomalías"""
        
        workflows_to_analyze = [
            "login_flow",
            "payment_flow",
            "password_reset",
            "account_creation",
            "permission_escalation",
            "data_access_flow",
        ]
        
        results = []
        
        for workflow_name in workflows_to_analyze:
            result = await self.workflow_analyzer.analyze_workflow(
                workflow_name=workflow_name,
                endpoints=request.endpoints,
                findings=request.reconnaissance_findings,
                framework=request.framework
            )
            
            if result:
                results.append(result)
        
        return results
    
    async def _analyze_authentication(self, request: AnalysisRequest) -> List[AnalysisResult]:
        """Analizar mecanismos de autenticación para escalamiento"""
        
        results = []
        
        for auth_mechanism in request.auth_mechanisms:
            result = await self.auth_analyzer.analyze_auth_mechanism(
                mechanism_type=auth_mechanism,
                endpoints=request.endpoints,
                findings=request.reconnaissance_findings
            )
            
            if result:
                results.append(result)
        
        return results
    
    async def _analyze_business_logic(self, request: AnalysisRequest) -> List[AnalysisResult]:
        """Analizar fallos de lógica de negocio"""
        
        flaws = await self.workflow_analyzer.detect_business_logic_flaws(
            endpoints=request.endpoints,
            findings=request.reconnaissance_findings
        )
        
        return flaws
    
    async def plan_exploitation_chain(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Planificar cadena de explotación multi-paso basada en análisis.
        
        Returns:
            Plan con pasos, payloads recomendados, evasión sugerida
        """
        
        # Consultar memoria para episodios similares
        similar_episodes = None
        if self.memory_system:
            try:
                similar_episodes = await self.memory_system.episodic_memory_store.find_similar_episodes(
                    objective=analysis_result.analysis_type.value,
                    target_type="web_application"
                )
            except Exception as e:
                logger.warning(f"Memory query failed: {e}")
        
        # Construir plan
        plan = {
            "vulnerability": analysis_result.analysis_type.value,
            "risk_level": analysis_result.risk_level,
            "confidence": analysis_result.confidence_score,
            "steps": await self._generate_exploitation_steps(analysis_result),
            "evasion_techniques": await self._select_evasion_techniques(analysis_result),
            "expected_outcome": analysis_result.business_impact,
            "similar_episodes": similar_episodes,
            "post_exploitation_strategy": await self.post_exploiter.plan_post_exploitation(
                vuln_type=analysis_result.analysis_type.value,
                framework=None  # TODO: pass framework from context
            ),
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"Exploitation plan created: {len(plan['steps'])} steps")
        
        return plan
    
    async def _generate_exploitation_steps(self, result: AnalysisResult) -> List[Dict[str, Any]]:
        """Generar pasos detallados de explotación"""
        
        steps = []
        
        for i, recommendation in enumerate(result.recommendations, 1):
            step = {
                "order": i,
                "description": recommendation,
                "type": result.analysis_type.value,
                "affected_endpoints": result.affected_endpoints,
                "expected_result": f"Step {i} of exploitation chain",
                "fallback": "Try alternative endpoint" if i < len(result.recommendations) else "Abort"
            }
            steps.append(step)
        
        return steps
    
    async def _select_evasion_techniques(self, result: AnalysisResult) -> List[str]:
        """Seleccionar técnicas de evasión basadas en riesgo"""
        
        evasion = []
        
        if result.risk_level in ["critical", "high"]:
            # Alto riesgo = máxima evasión
            evasion = [
                "tls_spoofing",
                "proxy_rotation",
                "jitter_engine",
                "browser_fingerprinting_spoof",
                "user_agent_randomization",
            ]
        elif result.risk_level == "medium":
            evasion = ["proxy_rotation", "jitter_engine"]
        else:
            evasion = ["jitter_engine"]
        
        return evasion
    
    async def generate_report(self, analyses: List[AnalysisResult], 
                             chains: List[Dict[str, Any]]) -> str:
        """
        Generar reporte ejecutivo + técnico con hallazgos.
        """
        
        report = await self.report_generator.generate_executive_report(
            analyses=analyses,
            exploitation_chains=chains,
            timestamp=datetime.now()
        )
        
        return report
    
    async def _record_analysis(self, request: AnalysisRequest, 
                              results: List[AnalysisResult]) -> None:
        """Registrar análisis en memoria del sistema"""
        
        if not self.memory_system:
            return
        
        try:
            for result in results:
                # Crear nodo en grafo
                await self.memory_system.graph_manager.create_node(
                    node_type="VULNERABILITY",
                    properties={
                        "type": result.analysis_type.value,
                        "risk_level": result.risk_level,
                        "confidence": result.confidence_score,
                        "target_url": request.target_url,
                        "timestamp": result.timestamp.isoformat(),
                    }
                )
                
                # Registrar evento temporal
                await self.memory_system.temporal_tracker.record_event(
                    event_type="ANOMALY_DETECTED",
                    node_id=request.target_url,
                    properties={
                        "vulnerability_type": result.analysis_type.value,
                        "business_impact": result.business_impact,
                    }
                )
            
            logger.info(f"Recorded {len(results)} analyses in memory system")
        
        except Exception as e:
            logger.error(f"Memory recording failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retornar estadísticas del agente"""
        return {
            **self.stats,
            "analysis_history_size": len(self.analysis_history),
        }


# Interfaz de MCP server
async def create_logic_agent(memory_system_ref=None, orchestrator_ref=None) -> LogicAgent:
    """Factory para crear LogicAgent con referencias inyectadas"""
    agent = LogicAgent(memory_system_ref, orchestrator_ref)
    logger.info("LogicAgent initialized")
    return agent


# Herramientas expuestas como MCP
class LogicAgentTools:
    """
    Herramientas disponibles a través del servidor MCP.
    
    El orchestrator puede invocar estas herramientas directamente.
    """
    
    def __init__(self, agent: LogicAgent):
        self.agent = agent
    
    async def analyze_target(self, request: AnalysisRequest) -> List[AnalysisResult]:
        """Herramienta MCP: Analizar objetivo"""
        return await self.agent.analyze_reconnaissance_findings(request)
    
    async def create_exploitation_plan(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """Herramienta MCP: Crear plan de explotación"""
        return await self.agent.plan_exploitation_chain(analysis)
    
    async def generate_report(self, analyses: List[AnalysisResult], 
                             chains: List[Dict[str, Any]]) -> str:
        """Herramienta MCP: Generar reporte"""
        return await self.agent.generate_report(analyses, chains)
