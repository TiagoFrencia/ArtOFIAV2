"""
JavaScript Analyzer - Módulo de análisis y extracción de JavaScript.

Responsabilidades:
- Descarga de archivos JS (.js, .mjs, .chunk.js)
- Desminificación y desobfuscación
- Extracción de APIs ocultas y endpoints
- Descubrimiento de credenciales filtradas
- Análisis de patrones vulnerables en DOM/JavaScript
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path


class JavaScriptAnalyzer:
    """Analizador especializado en JavaScript."""

    def __init__(self) -> None:
        """Inicializa el analizador."""
        self.logger = logging.getLogger(__name__)
        
        # Patrones para detectar APIs y secretos
        self.patterns: dict[str, str] = {
            "api_endpoints": r'(?:https?://|/)[^\s"\'<>]+(?:/api/|/graphql|/rest)',
            "aws_keys": r'AKIA[0-9A-Z]{16}',
            "jwt_tokens": r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+',
            "private_keys": r'-----BEGIN (PRIVATE|RSA) KEY',
            "credentials": r'(?:password|passwd|pwd|secret|token)\s*[=:]\s*["\']([^"\']+)["\']',
            "comments": r'(?://|#)\s*(?:TODO|FIXME|BUG|SECURITY|HACK|XXX)\s*[:.]?\s*(.+)',
            "urls": r'https?://[^\s"\'<>]+',
        }
        
        # Palabras clave indicativas de vulnerabilidades
        self.vulnerability_keywords: list[str] = [
            "eval", "innerHTML", "innerText", "dangerouslySetInnerHTML",
            "onclick", "onerror", "onload", "execScript",
            "atob", "JSON.parse", "URLSearchParams"
        ]

        self.logger.info("✓ JavaScript Analyzer inicializado")

    async def extract_javascript_files(
        self, url: str, aggressive: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae archivos JavaScript del objetivo.

        Args:
            url: URL del objetivo
            aggressive: Incluir análisis agresivo

        Returns:
            Lista de archivos JS encontrados
        """
        self.logger.info(f"🔍 Extrayendo archivos JavaScript de {url}")

        result: Dict[str, Any] = {
            "target": url,
            "timestamp": datetime.now().isoformat(),
            "files_found": [],
            "analysis": {}
        }

        # En producción: usar requests/playwright para descargar HTML
        # Aquí: simular extracción
        sim_files: list[str] = [
            f"{url}/assets/main.js",
            f"{url}/assets/api.chunk.js",
            f"{url}/assets/vendor.min.js",
        ]

        for js_file in sim_files:
            result["files_found"].append({
                "url": js_file,
                "type": "chunk" if "chunk" in js_file else "bundle",
                "size": "~150KB (simulated)"
            })

        self.logger.info(f"✓ {len(result['files_found'])} archivos encontrados")
        return result

    async def deobfuscate_code(
        self, code: str, method: str = "pretty"
    ) -> Dict[str, Any]:
        """
        Desminifica y desobfusca código JavaScript.

        Args:
            code: Código a desofuscar
            method: Método de desofuscación

        Returns:
            Código mejorado y metadatos
        """
        self.logger.info(f"🔨 Desofuscando código ({method})")

        result: Dict[str, Any] = {
            "method": method,
            "original_size": len(code),
            "deobfuscated": "",
            "quality_score": 0.0
        }

        if method == "pretty":
            # Pretty-print: agregar indentación básica
            result["deobfuscated"] = self._pretty_print(code)
            result["quality_score"] = 0.6

        elif method == "semantic":
            # Análisis semántico: identificar funciones, variables
            result["deobfuscated"] = self._semantic_deobfuscate(code)
            result["quality_score"] = 0.8

        elif method == "advanced":
            # Desofuscación avanzada
            result["deobfuscated"] = self._advanced_deobfuscate(code)
            result["quality_score"] = 0.95

        result["deobfuscated_size"] = len(result["deobfuscated"])
        return result

    async def extract_shadow_apis(
        self, code: str, target_types: Optional[list[str]] = None
    ) -> Dict[str, Any]:
        """
        ⭐ Extrae "Shadow APIs" - APIs ocultas, endpoints, credenciales.

        Args:
            code: Código JavaScript
            target_types: Tipos a extraer ["api_keys", "endpoints", "credentials", "comments"]

        Returns:
            APIs y secretos encontrados
        """
        self.logger.info("🕵️ Extrayendo Shadow APIs...")

        if target_types is None:
            target_types = ["api_keys", "endpoints", "credentials", "comments"]

        result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "api_keys": [],
            "endpoints": [],
            "credentials": [],
            "comments": [],
            "severity": "medium"
        }

        # Extraer endpoints
        if "endpoints" in target_types:
            endpoints: list[dict[str, str]] = self._extract_endpoints(code)
            result["endpoints"] = endpoints
            if endpoints:
                result["severity"] = "high"

        # Extraer credenciales
        if "credentials" in target_types:
            creds: list[dict[str, str]] = self._extract_credentials(code)
            result["credentials"] = creds
            if creds:
                result["severity"] = "critical"

        # Extraer API keys
        if "api_keys" in target_types:
            keys: list[dict[str, str]] = self._extract_api_keys(code)
            result["api_keys"] = keys
            if keys:
                result["severity"] = "critical"

        # Extraer comentarios sensibles
        if "comments" in target_types:
            comments: list[str] = self._extract_comments(code)
            result["comments"] = comments
            if any("security" in c.lower() for c in comments):
                result["severity"] = "high"

        self.logger.info(f"✓ Encontrados: {len(result['endpoints'])} endpoints, "
                        f"{len(result['credentials'])} credenciales")
        return result

    async def analyze_dom_patterns(
        self, html: str, javascript: str = ""
    ) -> Dict[str, Any]:
        """
        Analiza patrones vulnerables en DOM y JavaScript.

        Args:
            html: HTML de la página
            javascript: Código JavaScript

        Returns:
            Vulnerabilidades potenciales
        """
        self.logger.info("🔎 Analizando patrones vulnerables...")

        result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "risk_level": "low",
            "metrics": {
                "xss_sinks": 0,
                "unsafe_dom_methods": 0,
                "dangerous_functions": 0
            }
        }

        code_to_analyze: str = html + "\n" + javascript

        # XSS sinks
        xss_patterns: list[str] = [
            r"\.innerHTML\s*=",
            r"\.innerText\s*=",
            r"document\.write",
            r"\.insertAdjacentHTML"
        ]

        for pattern in xss_patterns:
            matches = re.finditer(pattern, code_to_analyze)
            for match in matches:
                result["vulnerabilities"].append({
                    "type": "XSS_SINK",
                    "pattern": pattern,
                    "location": code_to_analyze[:match.start()].count("\n"),
                    "severity": "high"
                })
                result["metrics"]["xss_sinks"] += 1

        # Dangerous functions
        for keyword in self.vulnerability_keywords:
            if keyword in code_to_analyze:
                result["vulnerabilities"].append({
                    "type": "DANGEROUS_FUNCTION",
                    "function": keyword,
                    "severity": "medium"
                })
                result["metrics"]["dangerous_functions"] += 1

        # Actualizar risk level
        if result["metrics"]["xss_sinks"] > 0:
            result["risk_level"] = "critical"
        elif result["metrics"]["dangerous_functions"] > 0:
            result["risk_level"] = "high"

        self.logger.info(f"✓ {len(result['vulnerabilities'])} vulnerabilidades encontradas")
        return result

    def _pretty_print(self, code: str) -> str:
        """Pretty-print básico."""
        # Agregar indentación simple
        code = code.replace("{", "{\n  ")
        code = code.replace("}", "\n}")
        return code

    def _semantic_deobfuscate(self, code: str) -> str:
        """Desofuscación semántica (mejorada)."""
        # Renombrar variables single-letter
        result = code
        for letter in "abcdefghijklmnopqrstuvwxyz":
            result = result.replace(f"var {letter}=", f"var var_{letter}=")
        return result

    def _advanced_deobfuscate(self, code: str) -> str:
        """Desofuscación avanzada."""
        # Combinar multiple técnicas
        result = self._semantic_deobfuscate(code)
        result = self._pretty_print(result)
        return result

    def _extract_endpoints(self, code: str) -> list[dict[str, str]]:
        """Extrae endpoints de API de JavaScript."""
        endpoints: list[dict[str, str]] = []
        matches = re.finditer(self.patterns["api_endpoints"], code)

        for match in matches:
            endpoint = match.group(0)
            endpoints.append({
                "endpoint": endpoint,
                "type": "api" if "/api/" in endpoint else "graphql" if "/graphql" in endpoint else "rest",
                "discovery_method": "javascript_extraction"
            })

        return list({e["endpoint"]: e for e in endpoints}.values())  # Deduplicar

    def _extract_credentials(self, code: str) -> list[dict[str, str]]:
        """Extrae credenciales de JavaScript."""
        credentials: list[dict[str, str]] = []
        matches = re.finditer(self.patterns["credentials"], code)

        for match in matches:
            credentials.append({
                "type": match.group(1),
                "value": match.group(2) if len(match.groups()) > 1 else "***",
                "severity": "critical"
            })

        return credentials

    def _extract_api_keys(self, code: str) -> list[dict[str, str]]:
        """Extrae API keys (AWS, etc.)."""
        keys: list[dict[str, str]] = []
        matches = re.finditer(self.patterns["aws_keys"], code)

        for match in matches:
            keys.append({
                "type": "AWS_ACCESS_KEY",
                "key": match.group(0),
                "severity": "critical"
            })

        return keys

    def _extract_comments(self, code: str) -> list[str]:
        """Extrae comentarios sensibles."""
        comments: list[str] = []
        matches = re.finditer(self.patterns["comments"], code)

        for match in matches:
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)

        return comments
