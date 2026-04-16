"""
Fingerprint Spoofing - Generación y alteración de huellas dactilares del navegador.

Responsabilidades:
- Generar fingerprints realistas de navegadores reales
- Modificar propiedades de WebGL, Canvas, Navigator
- Sincronizar fingerprints entre peticiones
- Mantener consistencia de fingerprint durante la sesión
"""

import logging
import json
import random
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class BrowserFingerprint:
    """Huella digital realista de navegador."""
    
    # Core identifiers
    user_agent: str
    browser_name: str
    browser_version: str
    os_name: str
    os_version: str
    
    # Platform
    platform: str
    architecture: str
    
    # Display
    screen_width: int
    screen_height: int
    screen_color_depth: int
    device_pixel_ratio: float
    timezone: str
    language: str
    
    # WebGL (GPU fingerprinting)
    webgl_vendor: str
    webgl_renderer: str
    webgl_extensions: List[str]
    
    # Canvas
    canvas_hash: str
    
    # Fonts
    system_fonts: List[str]
    
    # Navigator properties
    hardware_concurrency: int
    max_touch_points: int
    mem_js_heap_size: int
    
    # Network
    connection_downlink: int
    connection_rtt: int
    connection_type: str
    
    # Storage
    local_storage_enabled: bool
    session_storage_enabled: bool
    indexed_db_enabled: bool
    
    # Plugins
    plugins: List[Dict[str, str]]
    
    # Generated timestamp
    generated_at: str = ""
    fingerprint_hash: str = ""


class FingerprintSpoofing:
    """Generador y gestor de fingerprints falsificados."""
    
    def __init__(self) -> None:
        """Inicializa el spoofing de fingerprints."""
        self.logger = logging.getLogger(__name__)
        
        # Base de datos de navegadores reales (muestreo)
        self.real_fingerprints = self._load_real_fingerprints()
        
        # Fingerprint en uso actual
        self.current_fingerprint: Optional[BrowserFingerprint] = None
        
        # Historico de fingerprints
        self.fingerprint_history: List[BrowserFingerprint] = []
        
        self.logger.info("✓ Fingerprint Spoofing inicializado")

    def generate_random_fingerprint(self) -> BrowserFingerprint:
        """Genera un fingerprint aleatorio realista."""
        self.logger.info("🎯 Generando fingerprint realista...")
        
        # Seleccionar distribución de navegador realista
        browser_combo = random.choice(self.real_fingerprints)
        
        fingerprint = BrowserFingerprint(
            user_agent=browser_combo["user_agent"],
            browser_name=browser_combo["browser_name"],
            browser_version=browser_combo["browser_version"],
            os_name=browser_combo["os_name"],
            os_version=browser_combo["os_version"],
            platform=browser_combo["platform"],
            architecture=browser_combo["architecture"],
            
            # Display with realistic distribution
            screen_width=random.choice([1920, 1366, 1440, 1280, 1024]),
            screen_height=random.choice([1080, 768, 900, 720, 576]),
            screen_color_depth=random.choice([24, 32]),
            device_pixel_ratio=random.choice([1.0, 1.5, 2.0]),
            
            # Timezone (muestreo de zonas comunes)
            timezone=random.choice([
                "America/New_York", "America/Chicago", "America/Los_Angeles",
                "Europe/London", "Europe/Berlin", "Asia/Tokyo", "Australia/Sydney"
            ]),
            
            # Language
            language=random.choice([
                "en-US", "en-GB", "de-DE", "es-ES", "fr-FR", "ja-JP", "zh-CN"
            ]),
            
            # WebGL fingerprinting
            webgl_vendor=random.choice([
                "Google Inc.", "Mozilla", "Apple Inc.", "Intel Inc."
            ]),
            webgl_renderer=random.choice([
                "ANGLE (Intel HD Graphics 630)",
                "Apple M1",
                "Intel(R) Iris(TM) Plus Graphics 640",
                "NVIDIA GeForce RTX 3060"
            ]),
            webgl_extensions=self._generate_webgl_extensions(),
            
            # Canvas (será hasheado)
            canvas_hash=self._generate_canvas_hash(),
            
            # Fonts available
            system_fonts=[
                "Arial", "Calibri", "Times New Roman", "Courier New",
                "Verdana", "Georgia", "Garamond", "Comic Sans MS"
            ],
            
            # Navigator properties
            hardware_concurrency=random.choice([2, 4, 6, 8, 12, 16]),
            max_touch_points=random.choice([0, 10, 20]),
            mem_js_heap_size=random.randint(500000000, 2000000000),
            
            # Network simulation
            connection_downlink=random.choice([1.5, 3.5, 10]),
            connection_rtt=random.choice([50, 100, 150]),
            connection_type=random.choice(["4g", "wifi", "5g"]),
            
            # Storage
            local_storage_enabled=True,
            session_storage_enabled=True,
            indexed_db_enabled=random.choice([True, False]),
            
            # Plugins (mostly empty in modern browsers)
            plugins=self._generate_plugins(),
        )
        
        fingerprint.generated_at = datetime.now().isoformat()
        fingerprint.fingerprint_hash = self._hash_fingerprint(fingerprint)
        
        self.current_fingerprint = fingerprint
        self.fingerprint_history.append(fingerprint)
        
        self.logger.info(f"✓ Fingerprint generado: {fingerprint.browser_name} {fingerprint.browser_version}")
        return fingerprint

    def generate_consistent_fingerprint(self, seed: str) -> BrowserFingerprint:
        """Genera fingerprint determinístico basado en seed."""
        self.logger.info(f"🎯 Generando fingerprint consistente con seed: {seed[:10]}...")
        
        # Set seed para reproducibilidad
        random.seed(int(hashlib.md5(seed.encode()).hexdigest(), 16) % (2**32))
        
        fingerprint = self.generate_random_fingerprint()
        self.logger.info(f"✓ Fingerprint consistente generado")
        
        # Reset random seed
        random.seed()
        
        return fingerprint

    def inject_fingerprint(self) -> str:
        """Retorna JavaScript que inyecta el fingerprint actual."""
        if not self.current_fingerprint:
            self.logger.warning("⚠️ No hay fingerprint actual")
            return ""
        
        fp = self.current_fingerprint
        
        injection_script = f"""
// Fingerprint Injection - {datetime.now().isoformat()}

// Override navigator.userAgent
Object.defineProperty(navigator, 'userAgent', {{
    get: () => '{fp.user_agent}'
}});

// Override navigator.platform
Object.defineProperty(navigator, 'platform', {{
    get: () => '{fp.platform}'
}});

// Override navigator.languages
Object.defineProperty(navigator, 'languages', {{
    get: () => ['{fp.language}', 'en']
}});

// Override navigator.hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {{
    get: () => {fp.hardware_concurrency}
}});

// Override screen properties
Object.defineProperty(window, 'screen', {{
    value: {{
        width: {fp.screen_width},
        height: {fp.screen_height},
        colorDepth: {fp.screen_color_depth},
        pixelDepth: {fp.screen_color_depth},
        devicePixelRatio: {fp.device_pixel_ratio},
        availWidth: {fp.screen_width},
        availHeight: {fp.screen_height - 40}
    }}
}});

// Override WebGL fingerprinting
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {{
    if (parameter === 37445) {{
        return '{fp.webgl_vendor}';
    }}
    if (parameter === 37446) {{
        return '{fp.webgl_renderer}';
    }}
    return getParameter.call(this, parameter);
}};

// Override timezone
Date.prototype.toString = function() {{
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return new Date(this.getTime()).toLocaleString('en-US', {{ timeZone: '{fp.timezone}' }});
}};

// Mask automation
Object.defineProperty(navigator, 'webdriver', {{
    get: () => false
}});

// Consistent fingerprint marker
window.__fingerprint__ = {{
    'agent': '{fp.browser_name}',
    'hash': '{fp.fingerprint_hash}',
    'generated_at': '{fp.generated_at}'
}};
"""
        
        return injection_script

    def get_current_fingerprint(self) -> Optional[BrowserFingerprint]:
        """Retorna el fingerprint actual."""
        return self.current_fingerprint

    def get_fingerprint_as_dict(self) -> Dict[str, Any]:
        """Retorna fingerprint actual como diccionario."""
        if not self.current_fingerprint:
            return {}
        return asdict(self.current_fingerprint)

    def compare_fingerprints(
        self, 
        fp1: BrowserFingerprint, 
        fp2: BrowserFingerprint
    ) -> Dict[str, Any]:
        """Compara dos fingerprints para detectar inconsistencias."""
        self.logger.info("🔍 Comparando fingerprints...")
        
        differences = {
            "timestamp": datetime.now().isoformat(),
            "identical": True,
            "critical_differences": [],
            "minor_differences": [],
            "similarity_score": 1.0
        }
        
        # Propiedades críticas
        critical_props = ["user_agent", "browser_name", "os_name", "platform"]
        for prop in critical_props:
            val1 = getattr(fp1, prop)
            val2 = getattr(fp2, prop)
            if val1 != val2:
                differences["critical_differences"].append({
                    "property": prop,
                    "fingerprint1": val1,
                    "fingerprint2": val2
                })
                differences["identical"] = False
        
        # Propiedades menores
        minor_props = ["screen_width", "screen_height", "language", "timezone"]
        for prop in minor_props:
            val1 = getattr(fp1, prop)
            val2 = getattr(fp2, prop)
            if val1 != val2:
                differences["minor_differences"].append({
                    "property": prop,
                    "fingerprint1": val1,
                    "fingerprint2": val2
                })
        
        # Calcular score de similitud
        total_props = len(critical_props) + len(minor_props)
        diff_count = len(differences["critical_differences"]) + len(differences["minor_differences"])
        differences["similarity_score"] = (total_props - diff_count) / total_props
        
        self.logger.info(f"✓ Similitud: {differences['similarity_score']:.1%}")
        return differences

    def get_fingerprint_hash(self) -> str:
        """Retorna hash del fingerprint actual."""
        if not self.current_fingerprint:
            return ""
        return self.current_fingerprint.fingerprint_hash

    def get_fingerprint_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de fingerprints generados."""
        return {
            "timestamp": datetime.now().isoformat(),
            "current_fingerprint": {
                "browser": self.current_fingerprint.browser_name if self.current_fingerprint else None,
                "hash": self.get_fingerprint_hash()
            },
            "total_generated": len(self.fingerprint_history),
            "browser_distribution": self._get_browser_distribution(),
            "os_distribution": self._get_os_distribution(),
            "recent_fingerprints": [
                {
                    "browser": fp.browser_name,
                    "hash": fp.fingerprint_hash,
                    "generated_at": fp.generated_at
                }
                for fp in self.fingerprint_history[-10:]
            ]
        }

    # Private methods
    
    def _load_real_fingerprints(self) -> List[Dict[str, str]]:
        """Carga base de datos de fingerprints reales."""
        return [
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "browser_name": "Chrome",
                "browser_version": "120",
                "os_name": "Windows",
                "os_version": "10",
                "platform": "Win32",
                "architecture": "x86_64"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "browser_name": "Firefox",
                "browser_version": "121",
                "os_name": "Windows",
                "os_version": "10",
                "platform": "Win32",
                "architecture": "x86_64"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "browser_name": "Chrome",
                "browser_version": "120",
                "os_name": "macOS",
                "os_version": "10.15",
                "platform": "MacIntel",
                "architecture": "x86_64"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "browser_name": "Safari",
                "browser_version": "17.1",
                "os_name": "macOS",
                "os_version": "10.15",
                "platform": "MacIntel",
                "architecture": "x86_64"
            },
            {
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "browser_name": "Chrome",
                "browser_version": "120",
                "os_name": "Linux",
                "os_version": "5.15",
                "platform": "Linux",
                "architecture": "x86_64"
            }
        ]

    def _generate_webgl_extensions(self) -> List[str]:
        """Genera lista realista de extensiones WebGL."""
        possible_extensions = [
            "ANGLE_instanced_arrays",
            "EXT_blend_minmax",
            "EXT_color_buffer_half_float",
            "EXT_float_blend",
            "EXT_frag_depth",
            "EXT_shader_texture_lod",
            "EXT_sRGB",
            "EXT_texture_compression_bptc",
            "EXT_texture_compression_rgtc",
            "OES_element_index_uint",
            "OES_fbo_render_mipmap",
            "OES_standard_derivatives",
            "WEBGL_color_buffer_float",
            "WEBGL_compressed_texture_astc",
            "WEBGL_compressed_texture_etc",
        ]
        return random.sample(possible_extensions, random.randint(10, len(possible_extensions)))

    def _generate_canvas_hash(self) -> str:
        """Genera hash realista de canvas."""
        return hashlib.sha256(
            f"{random.random()}{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]

    def _generate_plugins(self) -> List[Dict[str, str]]:
        """Genera lista de plugins (típicamente vacía en navegadores modernos)."""
        return []

    def _hash_fingerprint(self, fp: BrowserFingerprint) -> str:
        """Genera hash único del fingerprint."""
        fp_str = f"{fp.user_agent}{fp.os_name}{fp.webgl_renderer}{fp.canvas_hash}"
        return hashlib.sha256(fp_str.encode()).hexdigest()[:12]

    def _get_browser_distribution(self) -> Dict[str, int]:
        """Retorna distribución de navegadores."""
        dist = {}
        for fp in self.fingerprint_history:
            dist[fp.browser_name] = dist.get(fp.browser_name, 0) + 1
        return dist

    def _get_os_distribution(self) -> Dict[str, int]:
        """Retorna distribución de sistemas operativos."""
        dist = {}
        for fp in self.fingerprint_history:
            dist[fp.os_name] = dist.get(fp.os_name, 0) + 1
        return dist
