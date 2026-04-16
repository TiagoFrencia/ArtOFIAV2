"""
Capa de evasión de ArtOfIA - Bypass de WAF, CAPTCHA, fingerprinting y análisis conductual.

Componentes principales:
1. browser: Stealth + Fingerprinting
2. captcha: Detección + Resolución + Token Injection
3. proxy: Rotación + Jitter + TLS Spoofing

Esta capa habilita a los agentes de recon y exploit para pasar desapercibidos
a través de defensas modernas (WAF, CAPTCHA, análisis conductual, detección TLS).
"""

from .browser import StealthController, StealthConfig, FingerprintSpoofing, BrowserFingerprint
from .captcha import (
    ChallengeDetector, ChallengeType, SolverClient, CaptchaType, 
    CaptchaJob, TokenInjector, TokenInjectionPoint
)
from .proxy import (
    ProxyRotator, ProxyConfig, ProxyType, ProxyProvider, ProxyStats,
    JitterEngine, JitterProfile, JitterConfig, TLSSpoofing, TLSConfig, 
    BrowserTLSProfile, TLSFingerprint
)

__all__ = [
    # Browser evasion
    "StealthController",
    "StealthConfig",
    "FingerprintSpoofing",
    "BrowserFingerprint",
    
    # CAPTCHA evasion
    "ChallengeDetector",
    "ChallengeType",
    "SolverClient",
    "CaptchaType",
    "CaptchaJob",
    "TokenInjector",
    "TokenInjectionPoint",
    
    # Proxy & behavior evasion
    "ProxyRotator",
    "ProxyConfig",
    "ProxyType",
    "ProxyProvider",
    "ProxyStats",
    "JitterEngine",
    "JitterProfile",
    "JitterConfig",
    "TLSSpoofing",
    "TLSConfig",
    "BrowserTLSProfile",
    "TLSFingerprint",
]

__version__ = "1.0.0"
__author__ = "ArtOfIA Security"
__description__ = "Multi-layer evasion framework for reconnaissance and exploitation"
