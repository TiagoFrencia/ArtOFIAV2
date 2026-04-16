"""
Módulo de evasión de proxy y timing - Rotación y Jitter.

Proporciona:
- Rotación de proxies residenciales, móviles y datacenter
- Geolocalización y health tracking automático
- Motor de jitter para comportamiento humano realista
- Temporización de eventos, tipeo y movimiento de mouse
- Spoofing de TLS para eludir detección criptográfica
"""

from .proxy_rotator import ProxyRotator, ProxyConfig, ProxyType, ProxyProvider, ProxyStats
from .jitter_engine import JitterEngine, JitterProfile, JitterConfig
from .tls_spoofing import TLSSpoofing, TLSConfig, BrowserTLSProfile, TLSFingerprint

__all__ = [
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
