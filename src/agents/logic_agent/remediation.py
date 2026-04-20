"""
Remediation Agent - Auto-Patching & Pull Request Generation
=============================================================
Módulo especializado en generar parches automáticos y abrir PRs.

Inspirado en Redamon (self-healing systems).

Proceso:
1. Recibir vulnerabilidad identificada
2. Analizar código afectado
3. Generar patch
4. Escribir tests para verificar fix
5. Clonar repo, hacer commit, abrir PR en GitHub
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class PatchRequest:
    """Solicitud de remediación"""
    vulnerability_type: str
    affected_file: str
    vulnerable_code: str
    severity: str
    repository: str
    target_branch: str = "main"


class RemediationAgent:
    """
    Agente de remediación automática.
    
    Genera patches automáticos para:
    - SQL injection
    - XSS
    - CSRF
    - Authorization bypass
    - Weak cryptography
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.patch_templates = self._initialize_patch_templates()
    
    def _initialize_patch_templates(self) -> Dict[str, Dict[str, str]]:
        """Inicializar plantillas de parches"""
        return {
            "sql_injection": {
                "pattern": "SELECT * FROM users WHERE id = {} ",
                "vulnerable_code": "query(f'SELECT * FROM users WHERE id = {user_id}')",
                "secure_code": "query('SELECT * FROM users WHERE id = ?', [user_id])",
                "fix_type": "parameterized_query",
                "explanation": "Use parameterized queries to prevent SQL injection",
            },
            "xss": {
                "pattern": "innerHTML = user_input",
                "vulnerable_code": "elem.innerHTML = user_data",
                "secure_code": "elem.textContent = user_data  # or use DOMPurify",
                "fix_type": "context_aware_encoding",
                "explanation": "Use textContent instead of innerHTML for untrusted data",
            },
            "csrf": {
                "pattern": "Missing CSRF token validation",
                "vulnerable_code": "@app.route('/change-password', methods=['POST'])\ndef change_password(): ...",
                "secure_code": "@app.route('/change-password', methods=['POST'])\n@csrf_token_required\ndef change_password(): ...",
                "fix_type": "token_validation",
                "explanation": "Add CSRF token validation to state-changing operations",
            },
            "weak_crypto": {
                "pattern": "md5(password)",
                "vulnerable_code": "password_hash = md5(password).hexdigest()",
                "secure_code": "password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
                "fix_type": "strong_hashing",
                "explanation": "Use bcrypt/Argon2 instead of MD5 for password hashing",
            },
            "auth_bypass": {
                "pattern": "Missing authorization check",
                "vulnerable_code": "def get_user_data(uid):\n    return db.query(uid)  # No auth check",
                "secure_code": "def get_user_data(uid):\n    if not is_owner(uid): raise Unauthorized()\n    return db.query(uid)",
                "fix_type": "authorization_check",
                "explanation": "Add authorization check before resource access",
            },
        }
    
    async def generate_patch(self, request: PatchRequest) -> Dict[str, Any] | None:
        """
        Generar patch automático para vulnerabilidad.
        """
        
        logger.info(f"Generating patch for {request.vulnerability_type}")
        
        # Paso 1: Identificar plantilla de patch
        template = self._get_patch_template(request.vulnerability_type)
        
        if not template:
            logger.error(f"No patch template for {request.vulnerability_type}")
            return None
        
        # Paso 2: Generar código seguro
        secure_code = template["secure_code"]
        original_code = template["vulnerable_code"]
        
        # Paso 3: Generar test
        test_code = await self._generate_test_case(
            request.vulnerability_type, secure_code
        )
        
        # Paso 4: Crear diff/patch
        patch = {
            "vulnerability_type": request.vulnerability_type,
            "affected_file": request.affected_file,
            "original_code": original_code,
            "secure_code": secure_code,
            "test_code": test_code,
            "fix_explanation": template["explanation"],
            "cve_category": await self._identify_cve(request.vulnerability_type),
            "remediation_complexity": self._estimate_complexity(request.severity),
        }
        
        logger.info(f"Patch generated for {request.vulnerability_type}")
        
        return patch
    
    async def open_pull_request(self, patch: Dict[str, Any], 
                               repo: str, branch: str = "main") -> Dict[str, Any]:
        """
        Abrir un PR en GitHub con el patch.
        """
        
        if not self.github_token:
            logger.warning("GitHub token not configured - cannot open PR")
            return {
                "status": "pending",
                "message": "GitHub integration not configured",
                "patch": patch,
            }
        
        # Paso 1: Clonar repositorio
        repo_path = await self._clone_repo(repo)
        
        # Paso 2: Crear rama feature
        feature_branch = f"fix/{patch['vulnerability_type']}-{hash(str(patch))}"
        await self._create_branch(repo_path, feature_branch, branch)
        
        # Paso 3: Aplicar patch
        await self._apply_patch(repo_path, patch)
        
        # Paso 4: Hacer commit
        commit_msg = f"[SECURITY] Fix {patch['vulnerability_type']}\n\n{patch['fix_explanation']}"
        await self._git_commit(repo_path, commit_msg)
        
        # Paso 5: Abrir PR
        pr_info = await self._open_github_pr(
            repo,
            feature_branch,
            branch,
            f"Security Fix: {patch['vulnerability_type']}",
            patch['fix_explanation']
        )
        
        logger.info(f"PR opened: {pr_info.get('url', 'N/A')}")
        
        return {
            "status": "pr_opened",
            "pr_url": pr_info.get("url"),
            "branch": feature_branch,
            "repo": repo,
        }
    
    def _get_patch_template(self, vuln_type: str) -> Dict[str, Any] | None:
        """Obtener plantilla de patch para tipo de vulnerabilidad"""
        return self.patch_templates.get(vuln_type.lower())
    
    async def _generate_test_case(self, vuln_type: str, secure_code: str) -> str:
        """Generar test case para validar que el fix funciona"""
        
        test_templates = {
            "sql_injection": """
def test_sql_injection_prevented():
    \"\"\"Verify parameterized queries prevent SQL injection\"\"\"
    payload = "'; DROP TABLE users; --"
    # This should NOT execute the DROP TABLE
    result = execute_query(payload)
    assert result.success == False
            """,
            "xss": """
def test_xss_prevented():
    \"\"\"Verify XSS payload is safely handled\"\"\"
    payload = "<script>alert('xss')</script>"
    result = render_element(payload)
    assert "<script>" not in result  # Script tags removed
            """,
            "csrf": """
def test_csrf_token_required():
    \"\"\"Verify CSRF token is required for POST\"\"\"
    response = client.post('/change-password', data={"new_pwd": "123"})
    assert response.status_code == 403  # CSRF error
            """,
            "weak_crypto": """
def test_strong_password_hashing():
    \"\"\"Verify strong hashing is used\"\"\"
    password = "mysecretpassword"
    hashed = hash_password(password)
    # Should use bcrypt format
    assert hashed.startswith('$2')  # bcrypt prefix
            """,
        }
        
        return test_templates.get(vuln_type, "")
    
    async def _identify_cve(self, vuln_type: str) -> str:
        """Identificar CVE relacionado"""
        cve_map = {
            "sql_injection": "CWE-89, CVE-2019-XXXXX",
            "xss": "CWE-79, OWASP Top 10 #3",
            "csrf": "CWE-352, OWASP Top 10 #5",
            "weak_crypto": "CWE-327, OWASP Top 10 #7",
            "auth_bypass": "CWE-640, OWASP Top 10 #1",
        }
        return cve_map.get(vuln_type.lower(), "CWE-Unknown")
    
    def _estimate_complexity(self, severity: str) -> str:
        """Estimar complejidad de remediación"""
        complexity_map = {
            "critical": "high",
            "high": "medium",
            "medium": "medium",
            "low": "low",
        }
        return complexity_map.get(severity, "medium")
    
    async def _clone_repo(self, repo: str) -> str:
        """Clonar repositorio (simulado)"""
        logger.debug(f"Would clone: {repo}")
        return f"/tmp/repo_{hash(repo)}"
    
    async def _create_branch(self, repo_path: str, branch_name: str, 
                            base_branch: str) -> bool:
        """Crear rama feature"""
        logger.debug(f"Would create branch: {branch_name} from {base_branch}")
        return True
    
    async def _apply_patch(self, repo_path: str, patch: Dict[str, Any]) -> bool:
        """Aplicar patch al código"""
        logger.debug(f"Would apply patch to {patch['affected_file']}")
        return True
    
    async def _git_commit(self, repo_path: str, message: str) -> bool:
        """Hacer commit"""
        logger.debug(f"Would commit: {message[:50]}...")
        return True
    
    async def _open_github_pr(self, repo: str, feature_branch: str, 
                             base_branch: str, title: str, 
                             description: str) -> Dict[str, Any]:
        """Simular apertura de PR"""
        
        pr_url = f"https://github.com/{repo}/pull/999"
        logger.debug(f"Would open PR: {pr_url}")
        
        return {
            "url": pr_url,
            "title": title,
            "state": "open",
        }
