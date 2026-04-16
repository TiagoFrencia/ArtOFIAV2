"""
Módulo de evasión de CAPTCHA - Resolución y Detección.

Proporciona:
- Detección de tipos de CAPTCHA (reCAPTCHA, hCaptcha, Turnstile, etc.)
- Resolución automática mediante 3rd-party solvers
- Inyección de tokens en DOM, headers y request body
- Evaluación de riesgo mediante detection de WAF
"""

from .challenge_detector import ChallengeDetector, ChallengeType
from .solver_client import SolverClient, CaptchaType, CaptchaJob
from .token_injector import TokenInjector, TokenInjectionPoint

__all__ = [
    "ChallengeDetector",
    "ChallengeType",
    "SolverClient",
    "CaptchaType",
    "CaptchaJob",
    "TokenInjector",
    "TokenInjectionPoint",
]

__version__ = "1.0.0"
__author__ = "ArtOfIA Security"
