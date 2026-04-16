"""
Logic Agent Module Exports
===========================
Exporta las clases principales del agente de lógica.
"""

from .server import (
    LogicAgent,
    AnalysisType,
    AnalysisRequest,
    AnalysisResult,
    LogicAgentTools,
)

from .workflow_analyzer import (
    WorkflowAnalyzer,
    WorkflowFlaw,
    WorkflowVulnerability,
)

from .auth_analyzer import AuthAnalyzer

from .post_exploit import (
    PostExploitationPlanner,
    PostExploitPhase,
    PostExploitationStrategy,
)

from .remediation import (
    RemediationAgent,
    PatchRequest,
)

from .report_generator import (
    ReportGenerator,
    VulnerabilityReport,
)

__all__ = [
    # Server
    "LogicAgent",
    "AnalysisType",
    "AnalysisRequest",
    "AnalysisResult",
    "LogicAgentTools",
    # Analyzers
    "WorkflowAnalyzer",
    "WorkflowFlaw",
    "WorkflowVulnerability",
    "AuthAnalyzer",
    # Post-exploitation
    "PostExploitationPlanner",
    "PostExploitPhase",
    "PostExploitationStrategy",
    # Remediation
    "RemediationAgent",
    "PatchRequest",
    # Reporting
    "ReportGenerator",
    "VulnerabilityReport",
]

__version__ = "1.0.0"
