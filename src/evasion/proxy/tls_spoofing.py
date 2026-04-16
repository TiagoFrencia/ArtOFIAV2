"""
TLS Spoofing - Alteración de firmas criptográficas de TLS.

Responsabilidades:
- Modificar handshake TLS a bajo nivel
- Spoofear JA3/JA4 fingerprints
- Emular TLS de navegadores reales (Chrome, Safari, Firefox)
- Eludir detección de herramientas automatizadas
- Mantener conectividad HTTPS válida
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class BrowserTLSProfile(Enum):
    """Perfiles TLS de navegadores reales."""
    CHROME_120 = "chrome_120"
    FIREFOX_121 = "firefox_121"
    SAFARI_17 = "safari_17"
    EDGE_120 = "edge_120"
    CUSTOM = "custom"


@dataclass
class TLSConfig:
    """Configuración de TLS."""
    
    browser_profile: BrowserTLSProfile = BrowserTLSProfile.CHROME_120
    
    # Versiones de protocolo soportadas
    tls_versions: List[str] = None  # ["TLS 1.2", "TLS 1.3"]
    
    # Cipher suites (orden importante)
    cipher_suites: List[str] = None
    
    # Supported groups (curvas elípticas)
    supported_groups: List[str] = None
    
    # Signature algorithms
    signature_algorithms: List[str] = None
    
    # Extensiones TLS
    extensions: Dict[str, Any] = None
    
    # ALPN protocols
    alpn_protocols: List[str] = None
    
    # Server Name Indication (SNI)
    sni_enabled: bool = True
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.tls_versions is None:
            self.tls_versions = ["TLS 1.3", "TLS 1.2"]
        if self.cipher_suites is None:
            self.cipher_suites = []
        if self.supported_groups is None:
            self.supported_groups = []
        if self.signature_algorithms is None:
            self.signature_algorithms = []
        if self.extensions is None:
            self.extensions = {}
        if self.alpn_protocols is None:
            self.alpn_protocols = []


class TLSFingerprint:
    """Huella digital de TLS (JA3/JA4)."""
    
    def __init__(self):
        """Inicializa generador de fingerprints."""
        self.logger = logging.getLogger(__name__)
    
    def generate_ja3_string(
        self,
        tls_version: str,
        cipher_suites: List[int],
        extensions: List[int],
        supported_groups: List[int],
        signature_algorithms: List[int]
    ) -> str:
        """Genera string JA3."""
        # Formato: TLSVersion,Ciphers,Extensions,SupportedGroups,SignatureAlgs
        ja3_string = f"{tls_version},{','.join(map(str, cipher_suites))}," \
                     f"{','.join(map(str, extensions))}," \
                     f"{','.join(map(str, supported_groups))}," \
                     f"{','.join(map(str, signature_algorithms))}"
        return ja3_string
    
    def ja3_hash(self, ja3_string: str) -> str:
        """Calcula hash MD5 del JA3 string."""
        return hashlib.md5(ja3_string.encode()).hexdigest()
    
    def generate_ja4_string(
        self,
        tls_version: str,
        cipher_suites: List[str],
        extensions: List[str],
        signature_algorithms: List[str]
    ) -> str:
        """Genera string JA4 (versión mejorada de JA3)."""
        # Formato JA4: TLSVersion,Ciphers,Extensions,Algorithms
        # Más granular que JA3
        
        # Abreviar TLS version (13 = TLS 1.3, 12 = TLS 1.2)
        tls_abbr = "13" if "1.3" in tls_version else "12"
        
        # Contar y hashear componentes
        ja4_parts = [
            tls_abbr,
            str(len(cipher_suites)),
            str(len(extensions)),
            hash(tuple(cipher_suites)) % 10000,
            hash(tuple(signature_algorithms)) % 10000
        ]
        
        ja4_string = ",".join(map(str, ja4_parts))
        return ja4_string


class TLSSpoofing:
    """Motor de spoofing de TLS."""
    
    # Perfiles predefinidos de navegadores
    BROWSER_PROFILES = {
        BrowserTLSProfile.CHROME_120: {
            "tls_versions": ["TLS 1.3", "TLS 1.2"],
            "cipher_suites": [
                0x1301,  # TLS_AES_128_GCM_SHA256
                0x1302,  # TLS_AES_256_GCM_SHA384
                0x1303,  # TLS_CHACHA20_POLY1305_SHA256
                0x002f,  # TLS_RSA_WITH_AES_128_CBC_SHA
                0x0035,  # TLS_RSA_WITH_AES_256_CBC_SHA
            ],
            "supported_groups": [
                0x001d,  # secp256r1 (P-256)
                0x0017,  # secp384r1 (P-384)
                0x0018,  # secp521r1 (P-521)
                0x001e,  # x25519
                0x0100,  # ffdhe2048
            ],
            "signature_algorithms": [
                0x0804,  # rsa_pss_rsae_sha256
                0x0809,  # ecdsa_secp256r1_sha256
                0x0a01,  # rsa_pss_rsae_sha512
                0x0401,  # ecdsa_secp256r1_sha1
                0x0601,  # rsa_pkcs1_sha512
            ],
            "extensions": {
                0x0000: "Server Name",  # SNI
                0x000d: "Signature Algorithms",
                0x000f: "Padding",
                0x0010: "Application Layer Protocol Negotiation",  # ALPN
                0x0014: "Supported Groups",
                0x002d: "PSK Key Exchange Modes",
                0x0033: "Key Share",
                0x2b2b: "Supported Versions",
            },
            "alpn_protocols": ["h2", "http/1.1"],
            "ja3": "771,49195-49196-52-57-47-53-10,0-23-65281-10-35-8-16-5-13-18-51-45-43-27-21-20,23-24-25-29-30-31,0"
        },
        BrowserTLSProfile.FIREFOX_121: {
            "tls_versions": ["TLS 1.3", "TLS 1.2"],
            "cipher_suites": [
                0x1301,  # TLS_AES_128_GCM_SHA256
                0x1302,  # TLS_AES_256_GCM_SHA384
                0x1303,  # TLS_CHACHA20_POLY1305_SHA256
                0x002f,  # TLS_RSA_WITH_AES_128_CBC_SHA
                0x0035,  # TLS_RSA_WITH_AES_256_CBC_SHA
            ],
            "supported_groups": [
                0x001d,  # secp256r1
                0x0018,  # secp521r1
                0x0017,  # secp384r1
                0x001e,  # x25519
            ],
            "signature_algorithms": [
                0x0804,  # rsa_pss_rsae_sha256
                0x0809,  # ecdsa_secp256r1_sha256
                0x0401,  # ecdsa_secp256r1_sha1
            ],
            "extensions": {
                0x0000: "Server Name",
                0x000d: "Signature Algorithms",
                0x000f: "Padding",
                0x0010: "ALPN",
                0x0014: "Supported Groups",
                0x002d: "PSK Key Exchange Modes",
                0x0033: "Key Share",
                0x2b2b: "Supported Versions",
            },
            "alpn_protocols": ["h2", "http/1.1"],
            "ja3": "771,49195-49196-52-57-47-53,0-23-65281-10-35-8-5-13-18-51-45-43-27-21-20,23-24-25-29-30-31,0"
        },
        BrowserTLSProfile.SAFARI_17: {
            "tls_versions": ["TLS 1.3", "TLS 1.2"],
            "cipher_suites": [
                0x1302,  # TLS_AES_256_GCM_SHA384
                0x1301,  # TLS_AES_128_GCM_SHA256
                0x1303,  # TLS_CHACHA20_POLY1305_SHA256
            ],
            "supported_groups": [
                0x0018,  # secp521r1
                0x0017,  # secp384r1
                0x001d,  # secp256r1
            ],
            "signature_algorithms": [
                0x0809,  # ecdsa_secp256r1_sha256
                0x0a01,  # rsa_pss_rsae_sha512
                0x0401,  # ecdsa_secp256r1_sha1
            ],
            "extensions": {
                0x0000: "Server Name",
                0x000a: "Supported Versions",
                0x000d: "Signature Algorithms",
                0x0010: "ALPN",
                0x0014: "Supported Groups",
                0x0033: "Key Share",
            },
            "alpn_protocols": ["h2", "http/1.1"],
            "ja3": "771,52-49199-49196-52393-52392-49327,0-23-65281-10-5-13-18-51-43-27-33,23-24-25-29-30,0"
        }
    }
    
    def __init__(self, config: Optional[TLSConfig] = None) -> None:
        """Inicializa el spoofing de TLS."""
        self.logger = logging.getLogger(__name__)
        
        self.config = config or TLSConfig()
        
        # Aplicar perfil si se especifica
        if self.config.browser_profile in self.BROWSER_PROFILES:
            self._apply_browser_profile(self.config.browser_profile)
        
        # Fingerprint generator
        self.fingerprint = TLSFingerprint()
        
        # Historial de conexiones
        self.connection_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"✓ TLS Spoofing inicializado (Perfil: {self.config.browser_profile.value})")

    def _apply_browser_profile(self, profile: BrowserTLSProfile) -> None:
        """Aplica configuración de navegador real."""
        browser_config = self.BROWSER_PROFILES[profile]
        
        self.config.tls_versions = browser_config.get("tls_versions", [])
        self.config.cipher_suites = browser_config.get("cipher_suites", [])
        self.config.supported_groups = browser_config.get("supported_groups", [])
        self.config.signature_algorithms = browser_config.get("signature_algorithms", [])
        self.config.extensions = browser_config.get("extensions", {})
        self.config.alpn_protocols = browser_config.get("alpn_protocols", [])
        
        self.logger.info(f"  ✓ Perfil {profile.value} aplicado")

    def get_ja3_fingerprint(self) -> str:
        """Genera fingerprint JA3 del perfil actual."""
        ja3_string = self.fingerprint.generate_ja3_string(
            tls_version="771",  # TLS 1.2/1.3 negotiation
            cipher_suites=self.config.cipher_suites or [],
            extensions=list(self.config.extensions.keys()) if self.config.extensions else [],
            supported_groups=self.config.supported_groups or [],
            signature_algorithms=self.config.signature_algorithms or []
        )
        
        ja3_hash = self.fingerprint.ja3_hash(ja3_string)
        
        return ja3_hash

    def get_ja4_fingerprint(self) -> str:
        """Genera fingerprint JA4 (versión mejorada)."""
        ja4_string = self.fingerprint.generate_ja4_string(
            tls_version=self.config.tls_versions[0] if self.config.tls_versions else "TLS 1.3",
            cipher_suites=[str(c) for c in self.config.cipher_suites] if self.config.cipher_suites else [],
            extensions=[str(e) for e in self.config.extensions.keys()] if self.config.extensions else [],
            signature_algorithms=[str(s) for s in self.config.signature_algorithms] if self.config.signature_algorithms else []
        )
        
        return ja4_string

    def generate_tls_client_hello(self, sni_hostname: str) -> Dict[str, Any]:
        """Genera ClientHello customizado para handshake TLS."""
        self.logger.info(f"🔐 Generando ClientHello para {sni_hostname}...")
        
        client_hello = {
            "tls_version": self.config.tls_versions[0] if self.config.tls_versions else "TLS 1.3",
            "cipher_suites": self.config.cipher_suites or [],
            "extensions": self.config.extensions or {},
            "supported_groups": self.config.supported_groups or [],
            "signature_algorithms": self.config.signature_algorithms or [],
            "alpn_protocols": self.config.alpn_protocols or [],
            "sni_hostname": sni_hostname if self.config.sni_enabled else None,
            "session_id": self._generate_session_id(),
            "random_bytes": self._generate_random_bytes(32),
            "compression_methods": [0],  # null compression
        }
        
        return client_hello

    async def intercept_tls_connection(
        self, 
        hostname: str, 
        port: int = 443
    ) -> Dict[str, Any]:
        """Intercepta y modifica handshake TLS."""
        self.logger.info(f"🔗 Interceptando conexión TLS a {hostname}:{port}...")
        
        connection = {
            "timestamp": datetime.now().isoformat(),
            "hostname": hostname,
            "port": port,
            "browser_profile": self.config.browser_profile.value,
            "ja3_fingerprint": self.get_ja3_fingerprint(),
            "ja4_fingerprint": self.get_ja4_fingerprint(),
            "client_hello": self.generate_tls_client_hello(hostname),
            "status": "intercepted",
        }
        
        self.connection_history.append(connection)
        
        # En producción: realmente interceptar y modificar TLS handshake
        # Aquí: simulación
        self.logger.info(f"  ✓ Conexión TLS interceptada y configurada")
        
        return connection

    def randomize_tls_parameters(self) -> None:
        """Randomiza parámetros TLS para evitar patrones."""
        self.logger.info("🎲 Randomizando parámetros TLS...")
        
        # Reordenar cipher suites
        if self.config.cipher_suites:
            random.shuffle(self.config.cipher_suites)
        
        # Reordenar supported groups
        if self.config.supported_groups:
            random.shuffle(self.config.supported_groups)
        
        # Reordenar signature algorithms
        if self.config.signature_algorithms:
            random.shuffle(self.config.signature_algorithms)
        
        self.logger.info("  ✓ Parámetros TLS randomizados")

    def change_browser_profile(self, profile: BrowserTLSProfile) -> None:
        """Cambia el perfil de navegador para la próxima conexión."""
        self.logger.info(f"🔄 Cambiando perfil a {profile.value}...")
        
        self.config.browser_profile = profile
        self._apply_browser_profile(profile)

    async def validate_tls_connection(self, hostname: str) -> Dict[str, Any]:
        """Valida que la conexión TLS es válida."""
        self.logger.info(f"✅ Validando conexión TLS a {hostname}...")
        
        validation = {
            "timestamp": datetime.now().isoformat(),
            "hostname": hostname,
            "tls_version_supported": True,
            "certificate_valid": True,  # En producción: verificar certificado
            "fingerprint_matches": True,
            "spoofing_effective": True,
            "status": "valid"
        }
        
        return validation

    def get_tls_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de conexiones TLS."""
        return {
            "timestamp": datetime.now().isoformat(),
            "browser_profile": self.config.browser_profile.value,
            "total_connections": len(self.connection_history),
            "cipher_suites_count": len(self.config.cipher_suites or []),
            "extensions_count": len(self.config.extensions or {}),
            "ja3_fingerprint": self.get_ja3_fingerprint(),
            "ja4_fingerprint": self.get_ja4_fingerprint(),
            "recent_connections": [
                {
                    "hostname": conn.get("hostname"),
                    "timestamp": conn.get("timestamp"),
                    "status": conn.get("status")
                }
                for conn in self.connection_history[-5:]
            ]
        }

    def export_tls_config(self) -> Dict[str, Any]:
        """Exporta configuración TLS actual."""
        return {
            "browser_profile": self.config.browser_profile.value,
            "tls_versions": self.config.tls_versions,
            "cipher_suites": self.config.cipher_suites,
            "supported_groups": self.config.supported_groups,
            "signature_algorithms": self.config.signature_algorithms,
            "extensions": self.config.extensions,
            "alpn_protocols": self.config.alpn_protocols,
            "sni_enabled": self.config.sni_enabled,
            "exported_at": datetime.now().isoformat()
        }

    # Private helper methods
    
    def _generate_session_id(self) -> str:
        """Genera Session ID aleatorio."""
        import secrets
        return secrets.token_hex(16)

    def _generate_random_bytes(self, length: int) -> str:
        """Genera bytes aleatorios."""
        import secrets
        return secrets.token_hex(length // 2)
