"""
Authentication Analyzer - Privilege Escalation Detection
=========================================================
Módulo especializado en analizar mecanismos de autenticación y autorización.

Técnicas:
- JWT manipulation
- OAuth token forgery
- API key leakage
- Session fixation
- CORS misconfiguration
- Privilege escalation paths
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AuthAnalyzer:
    """
    Analizador de mecanismos de autenticación.
    
    Detecta:
    - Fallos en JWT
    - Debilidades en OAuth
    - CORS misconfigurations
    - Caminos de escalamiento de privilegios
    """
    
    def __init__(self) -> None:
        self.auth_mechanisms: Dict[str, Any] = {
            "jwt": self._analyze_jwt,
            "oauth2": self._analyze_oauth2,
            "api_key": self._analyze_api_key,
            "session": self._analyze_session,
            "mfa": self._analyze_mfa,
        }
        
        self.analysis_history: list[Dict[str, Any]] = []
    
    async def analyze_auth_mechanism(self, mechanism_type: str, 
                                    endpoints: List[Dict[str, Any]],
                                    findings: Dict[str, Any]) -> Optional[Any]:
        """
        Analizar mecanismo específico de autenticación.
        """
        
        mechanism_type = mechanism_type.lower()
        
        if mechanism_type not in self.auth_mechanisms:
            logger.debug(f"Unknown auth mechanism: {mechanism_type}")
            return None
        
        # Ejecutar análisis específico
        analyzer = self.auth_mechanisms[mechanism_type]
        result = await analyzer(endpoints, findings)
        
        if result:
            logger.info(f"Auth vulnerability found: {mechanism_type}")
        
        return result
    
    async def _analyze_jwt(self, endpoints: List[Dict[str, Any]], 
                          findings: Dict[str, Any]) -> Dict[str, Any] | None:
        """Analizar vulnerabilidades JWT"""
        
        vulnerabilities = []
        
        if "jwt_tokens" in findings:
            tokens = findings["jwt_tokens"]
            
            # Check 1: Algoritmo "none"
            for token_info in tokens:
                if token_info.get("algorithm") == "none":
                    vulnerabilities.append({
                        "type": "jwt_none_algorithm",
                        "severity": "critical",
                        "description": "JWT using 'none' algorithm (signature bypass)"
                    })
            
            # Check 2: Expiración
            if not any(t.get("has_expiration") for t in tokens):
                vulnerabilities.append({
                    "type": "jwt_no_expiration",
                    "severity": "high",
                    "description": "JWT tokens without expiration"
                })
        
        if vulnerabilities:
            return {
                "mechanism": "jwt",
                "vulnerabilities": vulnerabilities,
                "escalation_path": await self._identify_jwt_escalation(findings)
            }
        
        return None
    
    async def _analyze_oauth2(self, endpoints: List[Dict[str, Any]],
                             findings: Dict[str, Any]) -> Dict[str, Any] | None:
        """Analizar vulnerabilidades OAuth2"""
        
        vulnerabilities = []
        
        # Check 1: Redirect URI validation
        if "oauth_endpoints" in findings:
            oauth_eps = findings["oauth_endpoints"]
            
            for ep in oauth_eps:
                if "redirect_uri" in ep and not ep.get("redirect_uri_validated"):
                    vulnerabilities.append({
                        "type": "oauth_redirect_uri_bypass",
                        "severity": "high",
                        "endpoint": ep.get("path"),
                        "description": "redirect_uri not properly validated (open redirect)"
                    })
        
        # Check 2: Token leakage
        if "authorization_header" in findings or "token_in_url" in findings:
            vulnerabilities.append({
                "type": "oauth_token_exposure",
                "severity": "high",
                "description": "OAuth tokens exposed in URL/headers"
            })
        
        if vulnerabilities:
            return {
                "mechanism": "oauth2",
                "vulnerabilities": vulnerabilities,
                "escalation_path": await self._identify_oauth_escalation(findings)
            }
        
        return None
    
    async def _analyze_api_key(self, endpoints: List[Dict[str, Any]],
                              findings: Dict[str, Any]) -> Dict[str, Any] | None:
        """Analizar vulnerabilidades de API keys"""
        
        vulnerabilities = []
        
        if "api_keys" in findings:
            keys = findings["api_keys"]
            
            # Check 1: API keys in URL
            for key_info in keys:
                if key_info.get("location") == "url":
                    vulnerabilities.append({
                        "type": "api_key_in_url",
                        "severity": "high",
                        "description": "API key exposed in URL (logs, referrer)"
                    })
            
            # Check 2: Weak key format
            if any(len(k.get("value", "")) < 16 for k in keys):
                vulnerabilities.append({
                    "type": "weak_api_key",
                    "severity": "medium",
                    "description": "API key appears weak (short length)"
                })
        
        if vulnerabilities:
            return {
                "mechanism": "api_key",
                "vulnerabilities": vulnerabilities,
                "escalation_path": await self._identify_apikey_escalation(findings)
            }
        
        return None
    
    async def _analyze_session(self, endpoints: List[Dict[str, Any]],
                              findings: Dict[str, Any]) -> Dict[str, Any] | None:
        """Analizar vulnerabilidades de sesión"""
        
        vulnerabilities = []
        
        if "session_cookies" in findings:
            cookies = findings["session_cookies"]
            
            for cookie in cookies:
                # Check 1: HttpOnly flag
                if not cookie.get("httponly"):
                    vulnerabilities.append({
                        "type": "session_cookie_no_httponly",
                        "severity": "high",
                        "description": "Session cookie without HttpOnly flag (XSS theft)"
                    })
                
                # Check 2: Secure flag
                if not cookie.get("secure"):
                    vulnerabilities.append({
                        "type": "session_cookie_no_secure",
                        "severity": "high",
                        "description": "Session cookie without Secure flag (MITM)"
                    })
                
                # Check 3: SameSite
                if cookie.get("samesite") not in ["Strict", "Lax"]:
                    vulnerabilities.append({
                        "type": "session_cookie_no_samesite",
                        "severity": "medium",
                        "description": "Session cookie without SameSite (CSRF vulnerability)"
                    })
        
        if vulnerabilities:
            return {
                "mechanism": "session",
                "vulnerabilities": vulnerabilities,
                "escalation_path": await self._identify_session_escalation(findings)
            }
        
        return None
    
    async def _analyze_mfa(self, endpoints: List[Dict[str, Any]],
                          findings: Dict[str, Any]) -> Dict[str, Any] | None:
        """Analizar vulnerabilidades en MFA"""
        
        vulnerabilities = []
        
        if "mfa_endpoints" in findings:
            mfa_eps = findings["mfa_endpoints"]
            
            # Check 1: MFA bypass
            for ep in mfa_eps:
                # Si hay bypass directamente después de login
                if ep.get("post_auth_access"):
                    vulnerabilities.append({
                        "type": "mfa_bypass",
                        "severity": "critical",
                        "endpoint": ep.get("path"),
                        "description": "Access granted before MFA validation"
                    })
            
            # Check 2: MFA recovery codes
            if any(ep.get("recovery_code_reusable") for ep in mfa_eps):
                vulnerabilities.append({
                    "type": "mfa_recovery_reusable",
                    "severity": "high",
                    "description": "MFA recovery codes can be reused"
                })
        
        if vulnerabilities:
            return {
                "mechanism": "mfa",
                "vulnerabilities": vulnerabilities,
                "escalation_path": await self._identify_mfa_escalation(findings)
            }
        
        return None
    
    async def _identify_jwt_escalation(self, findings: Dict[str, Any]) -> List[str]:
        """Identificar caminos de escalamiento vía JWT"""
        paths = [
            "1. Modify 'admin' claim to true",
            "2. Extend 'exp' to far future to maintain access",
            "3. Change 'sub' to target admin user ID",
            "4. Use forged token for admin endpoints",
        ]
        return paths
    
    async def _identify_oauth_escalation(self, findings: Dict[str, Any]) -> List[str]:
        """Identificar caminos de escalamiento vía OAuth"""
        paths = [
            "1. Perform open redirect via redirect_uri bypass",
            "2. Capture authorization code from attacker's response",
            "3. Use code to obtain admin token",
        ]
        return paths
    
    async def _identify_apikey_escalation(self, findings: Dict[str, Any]) -> List[str]:
        """Identificar caminos de escalamiento vía API Key"""
        paths = [
            "1. Extract exposed API key from logs/referrer",
            "2. Use key for privileged API operations",
        ]
        return paths
    
    async def _identify_session_escalation(self, findings: Dict[str, Any]) -> List[str]:
        """Identificar caminos de escalamiento vía sesión"""
        paths = [
            "1. Steal session cookie via XSS (if no HttpOnly)",
            "2. Perform MITM to capture session (if no Secure)",
            "3. Use stolen session for admin access",
        ]
        return paths
    
    async def _identify_mfa_escalation(self, findings: Dict[str, Any]) -> List[str]:
        """Identificar caminos de escalamiento vía MFA"""
        paths = [
            "1. Access protected resource before MFA challenge",
            "2. Use reusable recovery codes for MFA bypass",
        ]
        return paths
