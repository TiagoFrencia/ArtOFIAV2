"""
Agentic Identity Spu personality - M2M Authentication Exploitation
====================================================================

Módulo especializado en explotar comunicación Máquina-a-Máquina (M2M).

Contexto:
Los agentes modernos se comunican entre sí usando:
- OAuth 2.0 client credentials
- Agentic JWTs (tokens JWT especializados para agentes)
- Service-to-Service authentication
- Internal API keys

Problema: Muchos sistemas asumen que comunicación M2M es "segura por defecto",
sin validar que el agente que se conecta es realmente de confianza.

Objetivos:
- Interceptar comunicación M2M
- Falsificar identidad de agente confiable
- Acceder al token de delegación del agente
- Explorar confianza transitiva (agent A → agent B → sistema)

GUARDRAILS CRÍTICOS:
- NUNCA interceptar sin autorización
- NUNCA falsificar identidad permanentemente
- NUNCA comprometer sistemas fuera de scope
- Siempre revelar cuando se ha usado suplantación
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import base64
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class M2MAuthType(str, Enum):
    """Tipo de autenticación M2M"""
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    AGENTIC_JWT = "agentic_jwt"
    MUTUAL_TLS = "mutual_tls"
    API_KEY = "api_key"
    SERVICE_TOKEN = "service_token"


@dataclass
class AgenticIdentity:
    """Identidad de agente"""
    agent_id: str
    agent_name: str
    auth_type: M2MAuthType
    scopes: List[str]
    expiration: datetime
    issuer: str
    audience: str
    signed_by: str  # Quién firmó este token
    delegation_chains: List[str]  # Cadena de delegación
    can_delegate: bool  # ¿Este agente puede delegar a otros?


class AgenticJWTAnalyzer:
    """
    Analizar Agentic JWTs para identificar oportunidades de explotación.
    
    Agentic JWT es una extensión de JWT pero con claims específicos:
    - "agent_id": Identificador único del agente
    - "can_delegate": ¿Puede delegar permisos?
    - "delegated_from": ¿A quién le delegó permisos?
    - "scopes": Qué puede hacer
    """
    
    def __init__(self) -> None:
        self.known_signing_keys: Dict[str, str] = {}
    
    async def decode_agentic_jwt(self, token: str) -> Optional[AgenticIdentity]:
        """
        Decodificar Agentic JWT sin validar firma (análisis).
        
        NOTA: En producción, SOLO se hace con supervisor approval.
        """
        
        try:
            # Split JWT en sus 3 partes
            parts = token.split('.')
            if len(parts) != 3:
                logger.error("Invalid JWT format")
                return None
            
            # Decodificar payload (parte 2)
            payload_b64 = parts[1]
            # Agregar padding si falta
            padding = 4 - len(payload_b64) % 4
            if padding:
                payload_b64 += '=' * padding
            
            try:
                payload_json = base64.urlsafe_b64decode(payload_b64)
                payload = json.loads(payload_json)
            except Exception as e:
                logger.error(f"Failed to decode JWT: {e}")
                return None
            
            # Construir objeto de identidad
            identity = AgenticIdentity(
                agent_id=payload.get("agent_id", "unknown"),
                agent_name=payload.get("agent_name", "unknown"),
                auth_type=M2MAuthType.AGENTIC_JWT,
                scopes=payload.get("scopes", []),
                expiration=datetime.fromtimestamp(payload.get("exp", 0)),
                issuer=payload.get("iss", "unknown"),
                audience=payload.get("aud", "unknown"),
                signed_by=payload.get("signed_by", payload.get("iss")),
                delegation_chains=payload.get("delegation_chain", []),
                can_delegate=payload.get("can_delegate", False),
            )
            
            return identity
        
        except Exception as e:
            logger.error(f"Error decoding JWT: {e}")
            return None
    
    async def identify_weak_signing(self, token: str, known_keys: Dict[str, str]) -> Dict[str, Any]:
        """
        Identificar si JWT fue firmado con clave débil.
        
        Debilidades típicas:
        - Clave compartida conocida
        - "none" algorithm
        - Clave corta
        """
        
        # Extraer header
        parts = token.split('.')
        header_b64 = parts[0]
        padding = 4 - len(header_b64) % 4
        if padding:
            header_b64 += '=' * padding
        
        try:
            header_json = base64.urlsafe_b64decode(header_b64)
            header = json.loads(header_json)
        except:
            return {"vulnerable": False}
        
        algorithm = header.get("alg")
        
        # Check 1: Algorithm "none"
        if algorithm == "none":
            return {
                "vulnerable": True,
                "vulnerability": "algorithm_none",
                "description": "JWT signed with 'none' algorithm (no signature validation)",
                "exploit": "Modify claims and remove signature"
            }
        
        # Check 2: Known shared keys
        if algorithm == "HS256":  # Symmetric
            for key_name, key_value in known_keys.items():
                # Intentar validar con clave conocida
                # En producción, esto seria crypto real
                if key_name in token:
                    return {
                        "vulnerable": True,
                        "vulnerability": "weak_shared_key",
                        "description": f"Potential weak key: {key_name}",
                        "exploit": "Can forge tokens with known key"
                    }
        
        return {"vulnerable": False}


class AgenticIdentitySpoofing:
    """
    Falsificar identidad de agente para acceso no autorizado.
    
    Técnicas:
    1. Interceptar JWT, modificar claims, rechazar con new signature
    2. Crear JWT nuevo como agente confiable
    3. Usar token delegado de agente legítimo
    """
    
    def __init__(self, supervisor_validation_required: bool = True) -> None:
        self.supervisor_validation_required = supervisor_validation_required
        self.spoofing_attempts: list[Dict[str, Any]] = []
    
    async def forge_agentic_jwt(self, target_identity: AgenticIdentity,
                               signing_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Forjar Agentic JWT suplantando agente target.
        
        GUARDRAIL: Requiere validación del supervisor.
        """
        
        if self.supervisor_validation_required:
            validation = await self._request_supervisor_validation(
                f"Forge JWT for {target_identity.agent_id}"
            )
            if not validation['approved']:
                logger.error("Supervisor rejected JWT forging")
                return {"status": "rejected"}
        
        logger.warning(f"Forging JWT for agent: {target_identity.agent_id}")
        
        # Crear payload
        forged_payload = {
            "agent_id": target_identity.agent_id,
            "agent_name": target_identity.agent_name,
            "scopes": target_identity.scopes,
            "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "iss": target_identity.issuer,
            "aud": target_identity.audience,
            "can_delegate": target_identity.can_delegate,
        }
        
        return {
            "status": "forged_payload_prepared",
            "requires_signing_key": True,
            "payload": forged_payload,
            "message": "Payload prepared but signature requires key"
        }
    
    async def exploit_delegation_chain(self, initial_agent: AgenticIdentity,
                                      target_scope: List[str]) -> Dict[str, Any]:
        """
        Explotar cadena de delegación para obtener permisos.
        
        Ejemplo:
        - Agent A → puede delegar → Agent B
        - Agent B → puede delegar → Agent C
        - C accede a sistema con permisos de A (transitively)
        
        Vulnerabilidad: Si la cadena no valida cada paso, podemos saltear niveles.
        """
        
        logger.warning(f"Attempting to exploit delegation chain from {initial_agent.agent_id}")
        
        if not initial_agent.can_delegate:
            return {"status": "cannot_delegate"}
        
        # Simular explotación
        return {
            "status": "delegation_chain_analyzed",
            "initial_agent": initial_agent.agent_id,
            "delegation_depth": len(initial_agent.delegation_chains),
            "final_scope": target_scope,
            "vulnerabilities_found": self._analyze_delegation_chain(initial_agent),
        }
    
    def _analyze_delegation_chain(self, agent: AgenticIdentity) -> List[Dict[str, Any]]:
        """Analizar vulnerabilidades en cadena de delegación"""
        
        vulns = []
        
        # Vulnerabilidad 1: Delegación sin límite
        if len(agent.delegation_chains) > 3:
            vulns.append({
                "type": "excessive_delegation_depth",
                "description": "Delegation chain too deep (>3 levels)",
                "risk": "medium"
            })
        
        # Vulnerabilidad 2: Scope nunca decrece
        current_scope_count = len(agent.scopes)
        for prev_agent in agent.delegation_chains:
            # En producción, buscar scope real de agente anterior
            # Por ahora, asumir scope no decrece
            pass
        
        vulns.append({
            "type": "scope_expansion",
            "description": "Delegated agent may have more scopes than delegator",
            "risk": "high",
        })
        
        return vulns
    
    async def _request_supervisor_validation(self, action: str) -> Dict[str, Any]:
        """Solicitar validación del supervisor para suplantación"""
        
        logger.info(f"Requesting supervisor validation: {action}")
        
        # En producción, esto sería RPC al supervisor
        return {"approved": False, "reason": "Spoofing requires explicit authorization"}
