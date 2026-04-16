"""
Challenge Detector - Detección de desafíos CAPTCHA y honeypots.

Responsabilidades:
- Detectar tipos de CAPTCHAs presentes
- Identificar honeypots y trampas
- Analisar headers para indicadores de WAF
- Detectar verificaciones invisible en segundo plano
- Evaluar riesgo de detección
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class ChallengeType(Enum):
    """Tipos de desafíos detectados."""
    NO_CHALLENGE = "no_challenge"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    CLOUDFLARE_CHALLENGE = "cloudflare_challenge"
    CLOUDFLARE_TURNSTILE = "turnstile"
    GEETEST = "geetest"
    FUNCAPTCHA = "funcaptcha"
    CUSTOM_CAPTCHA = "custom_captcha"
    HONEYPOT = "honeypot"
    INVISIBLE_CHALLENGE = "invisible_challenge"


class ChallengeDetector:
    """Detector de desafíos CAPTCHA y verificaciones."""
    
    # Patrones de detección
    CAPTCHA_PATTERNS = {
        ChallengeType.RECAPTCHA_V2: [
            r'g-recaptcha',
            r'recaptcha.net/recaptcha/__en.js',
            r'api.recaptcha.net/recaptcha/api',
            r'sitekey.*="[a-zA-Z0-9_-]{40,}"'
        ],
        ChallengeType.RECAPTCHA_V3: [
            r'grecaptcha.execute',
            r'recaptcha/api.js\?render=[a-zA-Z0-9_-]+',
            r'grecaptcha.executeAsync'
        ],
        ChallengeType.HCAPTCHA: [
            r'h-captcha',
            r'hcaptcha.com',
            r'hcaptcha-response'
        ],
        ChallengeType.CLOUDFLARE_TURNSTILE: [
            r'challenges.cloudflare.com',
            r'cf-turnstile',
            r'turnstile.js',
            r'cf-turnstile-response'
        ],
        ChallengeType.GEETEST: [
            r'geetest',
            r'gt4.geetest.com',
            r'initGeetest4'
        ],
        ChallengeType.FUNCAPTCHA: [
            r'funcaptcha',
            r'arkoselabs',
            r'ARKOSE.setConfig'
        ]
    }
    
    # Indicadores de honeypots
    HONEYPOT_INDICATORS = [
        r'type=["\']?hidden["\']?\s+name=["\']?honeypot',
        r'display:\s*none.*name=["\']?trap',
        r'style=["\'][^"\']*display:\s*none[^"\']*["\'].*name=["\']?fake',
        r'visibility:\s*hidden.*name=["\']?decoy'
    ]
    
    # Indicadores de WAF/verificación invisible
    WAF_HEADERS = [
        'x-protected-by',
        'x-waf',
        'strict-transport-security',
        'content-security-policy',
        'x-frame-options',
        'x-content-type-options'
    ]
    
    WAF_INDICATORS = {
        'cloudflare': ['/cdn-cgi/', '__cfduid', '__cf_bm', 'cf_clearance'],
        'akamai': ['ak_bmsc', 'bm_sz', 'TS'],
        'aws_waf': ['x-amzn-waf-action', 'x-amzn-waf'],
        'imperva': ['_Incap_Session', '_incap_ses', 'visid_incap'],
        'mod_security': ['mod_security', 'SecRule'],
        'f5': ['TS', 'BIGipServer'],
        'barracuda': ['barra_counter_session'],
    }
    
    def __init__(self) -> None:
        """Inicializa el detector de desafíos."""
        self.logger = logging.getLogger(__name__)
        
        # Historial de detecciones
        self.detection_history: List[Dict[str, Any]] = []
        
        # Cache de desafíos por URL
        self.challenge_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("✓ Challenge Detector inicializado")

    def analyze_page_html(self, html: str, url: str = "") -> Dict[str, Any]:
        """Analiza HTML en busca de desafíos CAPTCHA."""
        self.logger.info(f"🔍 Analizando página HTML en busca de desafíos...")
        
        result = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "challenges_detected": [],
            "honeypots_detected": [],
            "risk_level": "low",
            "recommendation": "proceed",
            "confidence_score": 0.0
        }
        
        # Detectar CAPTCHAs
        for challenge_type, patterns in self.CAPTCHA_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    result["challenges_detected"].append({
                        "type": challenge_type.value,
                        "pattern": pattern,
                        "severity": self._get_challenge_severity(challenge_type)
                    })
                    break
        
        # Detectar honeypots
        for pattern in self.HONEYPOT_INDICATORS:
            if re.search(pattern, html, re.IGNORECASE):
                honeypot = {
                    "pattern": pattern,
                    "detected_at": "html",
                    "risk": "high"
                }
                result["honeypots_detected"].append(honeypot)
        
        # Evaluar riesgo general
        if result["challenges_detected"]:
            result["risk_level"] = "medium"
            result["recommendation"] = "solve_challenge"
        
        if result["honeypots_detected"]:
            result["risk_level"] = "high"
            result["recommendation"] = "analyze_carefully"
        
        # Calcular confianza
        confidence_factors = 0
        if result["challenges_detected"]:
            confidence_factors += len(result["challenges_detected"]) * 0.3
        if result["honeypots_detected"]:
            confidence_factors += len(result["honeypots_detected"]) * 0.2
        
        result["confidence_score"] = min(confidence_factors, 1.0)
        
        # Cachear resultado
        self.challenge_cache[url] = result
        self.detection_history.append(result)
        
        self.logger.info(f"  Detectados: {len(result['challenges_detected'])} CAPTCHA(s), "
                        f"{len(result['honeypots_detected'])} honeypot(s)")
        
        return result

    def analyze_response_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analiza headers HTTP para indicadores de WAF."""
        self.logger.info("📋 Analizando headers de respuesta...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "waf_detected": False,
            "waf_type": None,
            "security_headers": [],
            "suspicious_headers": [],
            "risk_indicators": []
        }
        
        # Convertir keys a lowercase para comparación
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # Buscar indicadores de WAF
        for waf_name, indicators in self.WAF_INDICATORS.items():
            for indicator in indicators:
                if any(indicator.lower() in str(v).lower() for v in headers.values()):
                    result["waf_detected"] = True
                    result["waf_type"] = waf_name
                    result["risk_indicators"].append({
                        "indicator": indicator,
                        "waf": waf_name,
                        "severity": "high"
                    })
        
        # Analizar security headers
        for header in self.WAF_HEADERS:
            if header in headers_lower:
                result["security_headers"].append({
                    "header": header,
                    "value": headers_lower[header]
                })
        
        # Buscar headers sospechosos
        suspicious_keywords = ['challenge', 'verify', 'captcha', 'bot', 'abuse']
        for key, value in headers.items():
            if any(keyword in key.lower() or keyword in str(value).lower() 
                   for keyword in suspicious_keywords):
                result["suspicious_headers"].append({
                    "header": key,
                    "value": value
                })
        
        if result["waf_detected"]:
            self.logger.warning(f"  ⚠️ WAF detectado: {result['waf_type']}")
        
        return result

    def detect_invisible_challenge(
        self, 
        page_html: str, 
        page_javascript: str = ""
    ) -> Dict[str, Any]:
        """Detecta verificaciones invisibles en segundo plano (reCAPTCHA v3, etc)."""
        self.logger.info("🔎 Detectando desafíos invisibles...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "invisible_challenges": [],
            "detected": False,
            "risk_level": "medium"
        }
        
        # Patrones de verificación invisible
        invisible_patterns = {
            "recaptcha_v3": [
                r'grecaptcha\.execute\(',
                r'grecaptcha\.executeAsync\(',
                r'render=[a-zA-Z0-9_-]+',
                r'action["\']?\s*:\s*["\'][a-z_]+["\']'
            ],
            "behavioral_analysis": [
                r'addEventListener\(["\']?(?:mousemove|scroll|click)',
                r'performance\.mark',
                r'requestIdleCallback',
                r'PerformanceObserver'
            ],
            "fingerprinting": [
                r'navigator\.plugins',
                r'canvas\.toDataURL',
                r'WebGL',
                r'AudioContext',
                r'webrtc'
            ]
        }
        
        combined_code = page_html + page_javascript
        
        for challenge_name, patterns in invisible_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_code, re.IGNORECASE):
                    result["invisible_challenges"].append({
                        "type": challenge_name,
                        "pattern": pattern,
                        "detected": True
                    })
                    result["detected"] = True
        
        if result["detected"]:
            self.logger.warning(f"  ⚠️ {len(result['invisible_challenges'])} "
                              f"verificaciones invisibles detectadas")
        
        return result

    def evaluate_risk_score(
        self, 
        html_analysis: Optional[Dict[str, Any]] = None,
        headers_analysis: Optional[Dict[str, Any]] = None,
        invisible_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evalúa score de riesgo combinado."""
        self.logger.info("📊 Evaluando score de riesgo...")
        
        score = 0.0
        risk_factors = []
        
        # Factores de HTML
        if html_analysis:
            challenge_count = len(html_analysis.get("challenges_detected", []))
            honeypot_count = len(html_analysis.get("honeypots_detected", []))
            
            score += challenge_count * 0.3
            score += honeypot_count * 0.5
            
            if challenge_count > 0:
                risk_factors.append("captcha_required")
            if honeypot_count > 0:
                risk_factors.append("honeypots_present")
        
        # Factores de headers
        if headers_analysis:
            if headers_analysis.get("waf_detected"):
                score += 0.3
                risk_factors.append(f"waf_detected:{headers_analysis['waf_type']}")
            
            if headers_analysis.get("suspicious_headers"):
                score += 0.2
                risk_factors.append("suspicious_headers")
        
        # Factores de desafíos invisibles
        if invisible_analysis:
            if invisible_analysis.get("detected"):
                invisible_count = len(invisible_analysis.get("invisible_challenges", []))
                score += invisible_count * 0.15
                risk_factors.append("invisible_challenges")
        
        # Normalizar score a 0-1
        risk_score = min(score, 1.0)
        
        # Clasificar riesgo
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "medium"
        elif risk_score < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_recommendation(risk_level)
        }
        
        self.logger.info(f"  Risk Score: {risk_score:.2f} ({risk_level})")
        
        return result

    def get_detection_summary(self) -> Dict[str, Any]:
        """Retorna resumen de detecciones."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_analyses": len(self.detection_history),
            "avg_risk_level": self._calculate_avg_risk(),
            "most_common_challenges": self._get_common_challenges(),
            "recent_detections": self.detection_history[-5:] if self.detection_history else []
        }

    # Private methods
    
    def _get_challenge_severity(self, challenge_type: ChallengeType) -> str:
        """Retorna severidad del tipo de desafío."""
        severity_map = {
            ChallengeType.RECAPTCHA_V3: "medium",
            ChallengeType.CLOUDFLARE_TURNSTILE: "medium",
            ChallengeType.RECAPTCHA_V2: "high",
            ChallengeType.HCAPTCHA: "high",
            ChallengeType.GEETEST: "high"
        }
        return severity_map.get(challenge_type, "medium")

    def _get_recommendation(self, risk_level: str) -> str:
        """Retorna recomendación basada en nivel de riesgo."""
        recommendations = {
            "low": "proceed_normally",
            "medium": "enable_evasion_plugins",
            "high": "solve_captcha_first",
            "critical": "abort_and_retry_later"
        }
        return recommendations.get(risk_level, "analyze_carefully")

    def _calculate_avg_risk(self) -> float:
        """Calcula riesgo promedio de historial."""
        if not self.detection_history:
            return 0.0
        
        risk_levels_numeric = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0
        }
        
        total = sum(
            risk_levels_numeric.get(det.get("risk_level", "medium"), 0.5)
            for det in self.detection_history
        )
        
        return total / len(self.detection_history)

    def _get_common_challenges(self) -> List[Dict[str, Any]]:
        """Retorna desafíos más comunes."""
        challenge_freq = {}
        
        for detection in self.detection_history:
            for challenge in detection.get("challenges_detected", []):
                challenge_type = challenge.get("type")
                challenge_freq[challenge_type] = challenge_freq.get(challenge_type, 0) + 1
        
        return sorted(
            [{"challenge": k, "count": v} for k, v in challenge_freq.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
