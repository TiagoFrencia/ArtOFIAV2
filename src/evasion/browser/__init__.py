"""
Módulo de evasión de navegador - Stealth y Fingerprinting.

Proporciona:
- Automación sigilosa de navegador
- Spoofing de fingerprint de navegador
- Inyección de plugins de stealth
- Navegación humana con timing realista
"""

from .stealth_controller import StealthController, StealthConfig
from .fingerprint_spoofing import FingerprintSpoofing, BrowserFingerprint

__all__ = [
    "StealthController",
    "StealthConfig",
    "FingerprintSpoofing",
    "BrowserFingerprint",
]

__version__ = "1.0.0"
__author__ = "ArtOfIA Security"
