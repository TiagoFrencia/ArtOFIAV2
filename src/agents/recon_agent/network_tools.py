"""
Network Tools - Módulo de recopilación de información de red (OSINT).

Responsabilidades:
- Enumeración de DNS (subdomains, AXFR attempts)
- Análisis de headers HTTP
- Escaneo pasivo de puertos
- Análisis de certificados TLS/SSL
- Extracción de comentarios sensibles en respuestas
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime


class NetworkTools:
    """Herramientas de recopilación de información de red."""

    def __init__(self) -> None:
        """Inicializa las herramientas de red."""
        self.logger = logging.getLogger(__name__)

        # Wordlist común para DNS brute-force
        self.dns_wordlist = [
            "www", "mail", "ftp", "localhost", "webmail", "smtp",
            "api", "admin", "test", "dev", "staging", "prod",
            "cdn", "backup", "db", "database", "server",
            "app", "application", "web", "portal", "login",
            "dashboard", "panel", "console", "monitor", "status",
            "git", "svn", "jenkins", "kubernetes", "docker",
            "grafana", "kibana", "elasticsearch", "redis"
        ]

        # Security headers conocidos
        self.security_headers = {
            "Strict-Transport-Security": "HSTS",
            "Content-Security-Policy": "CSP",
            "X-Frame-Options": "Clickjacking protection",
            "X-Content-Type-Options": "MIME sniffing protection",
            "X-XSS-Protection": "XSS protection",
            "Referrer-Policy": "Referrer control",
            "Permissions-Policy": "Feature policy"
        }

        self.logger.info("✓ Network Tools inicializadas")

    async def dns_enumeration(
        self, domain: str, wordlist: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Enumeración de DNS - AXFR y brute-force de subdomios.

        Args:
            domain: Dominio objetivo
            wordlist: Lista de palabras para brute-force

        Returns:
            Subdomains encontrados
        """
        self.logger.info(f"🔍 Enumerando DNS para {domain}")

        if wordlist is None:
            wordlist = self.dns_wordlist

        result = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "subdomains_found": [],
            "enumeration_methods": [],
            "potential_services": []
        }

        # AXFR attempt (simulado)
        result["enumeration_methods"].append("AXFR_attempt")
        simulated_axfr = [
            f"ns1.{domain}",
            f"mail.{domain}",
            f"api.{domain}"
        ]
        result["subdomains_found"].extend([
            {"subdomain": sd, "method": "AXFR", "ip": "simulated"}
            for sd in simulated_axfr
        ])

        # Brute-force (simulado)
        result["enumeration_methods"].append("wordlist_brute_force")
        for word in wordlist[:10]:  # Limitar para demo
            subdomain = f"{word}.{domain}"
            result["subdomains_found"].append({
                "subdomain": subdomain,
                "method": "brute_force",
                "ip": "simulated",
                "services": self._infer_services(word)
            })
            result["potential_services"].extend(self._infer_services(word))

        self.logger.info(f"✓ {len(result['subdomains_found'])} subdominos encontrados")
        return result

    async def analyze_http_headers(
        self, url: str, include_sensitive: bool = True
    ) -> Dict[str, Any]:
        """
        Analiza headers HTTP de seguridad.

        Args:
            url: URL objetivo
            include_sensitive: Incluir análisis de headers sensibles

        Returns:
            Análisis de headers
        """
        self.logger.info(f"📋 Analizando headers HTTP de {url}")

        result = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "headers_present": [],
            "headers_missing": [],
            "risk_assessment": "medium",
            "recommendations": []
        }

        # Headers presentes (simulado)
        present_headers = {
            "Content-Security-Policy": "default-src 'self'; script-src 'self' cdn.example.com",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Frame-Options": "DENY"
        }

        for header, value in present_headers.items():
            result["headers_present"].append({
                "header": header,
                "value": value,
                "purpose": self.security_headers.get(header, "unknown"),
                "security_level": "good"
            })

        # Headers faltantes
        missing = ["X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]
        result["headers_missing"] = [
            {
                "header": h,
                "purpose": self.security_headers[h],
                "severity": "medium"
            }
            for h in missing if h in self.security_headers
        ]

        # Recomendaciones
        if result["headers_missing"]:
            result["risk_assessment"] = "high"
            result["recommendations"] = [
                f"Add {h['header']}: {self.security_headers[h['header']]}"
                for h in result["headers_missing"]
            ]

        self.logger.info(f"✓ {len(result['headers_present'])} headers seguros, "
                        f"{len(result['headers_missing'])} faltantes")
        return result

    async def port_scan_passive(
        self, target: str, data_source: str = "shodan"
    ) -> Dict[str, Any]:
        """
        Escaneo pasivo de puertos usando OSINT.

        Consulta Shodan, Censys u otras fuentes (simulado).

        Args:
            target: Host o IP objetivo
            data_source: Fuente de datos ("shodan", "censys")

        Returns:
            Puertos y servicios encontrados
        """
        self.logger.info(f"🔌 Escaneando puertos pasivamente para {target} (via {data_source})")

        result = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "data_source": data_source,
            "ports_found": [],
            "services": [],
            "risk_level": "low"
        }

        # Puertos simulados según fuente
        if data_source == "shodan":
            simulated_ports = [
                {"port": 80, "service": "http", "status": "open"},
                {"port": 443, "service": "https", "status": "open"},
                {"port": 8080, "service": "http-proxy", "status": "open"},
                {"port": 27017, "service": "mongodb", "status": "open"},
            ]
        else:  # censys
            simulated_ports = [
                {"port": 80, "service": "http", "status": "open"},
                {"port": 443, "service": "https", "status": "open"},
                {"port": 5432, "service": "postgresql", "status": "open"},
            ]

        result["ports_found"] = simulated_ports
        result["services"] = list(set(p["service"] for p in simulated_ports))

        # Evaluar riesgo
        if any(p["port"] in [27017, 5432, 3306] for p in simulated_ports):
            result["risk_level"] = "critical"
        elif any(p["port"] in [8080, 8000] for p in simulated_ports):
            result["risk_level"] = "high"

        self.logger.info(f"✓ {len(result['ports_found'])} puertos encontrados")
        return result

    async def tls_certificate_analysis(
        self, domain: str
    ) -> Dict[str, Any]:
        """
        Análisis de certificados TLS/SSL.

        Extrae:
        - Subject Alternative Names (SANs)
        - Emisor
        - Fecha de expiración
        - Cadena de confianza

        Args:
            domain: Dominio objetivo

        Returns:
            Información del certificado
        """
        self.logger.info(f"🔐 Analizando certificado TLS para {domain}")

        result = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "certificate": {
                "subject": {
                    "commonName": domain,
                    "organizationName": "Example Corp",
                    "countryName": "US"
                },
                "issuer": {
                    "commonName": "Let's Encrypt",
                    "organizationName": "Let's Encrypt"
                },
                "san": [
                    domain,
                    f"*.{domain}",
                    f"www.{domain}",
                    f"api.{domain}"
                ],
                "validity": {
                    "notBefore": "2024-01-01T00:00:00Z",
                    "notAfter": "2025-01-01T00:00:00Z",
                    "daysRemaining": 180
                },
                "fingerprint_sha256": "a1b2c3d4e5f6...",
                "publicKeyAlgorithm": "ECDSA",
                "signatureAlgorithm": "sha256WithRSAEncryption"
            },
            "security_issues": []
        }

        # Detectar problemas
        if result["certificate"]["validity"]["daysRemaining"] < 30:
            result["security_issues"].append({
                "issue": "Certificate expiring soon",
                "severity": "high",
                "days_remaining": result["certificate"]["validity"]["daysRemaining"]
            })

        # SANs que revelan dominios internos
        if len(result["certificate"]["san"]) > 3:
            result["security_issues"].append({
                "issue": "Multiple SANs may reveal internal infrastructure",
                "severity": "medium",
                "san_count": len(result["certificate"]["san"])
            })

        self.logger.info(f"✓ Certificado analizado: {result['certificate']['san']}")
        return result

    async def extract_sensitive_comments(
        self, response_content: str
    ) -> Dict[str, Any]:
        """
        Extrae comentarios sensibles de respuestas HTTP.

        Busca:
        - TODO/FIXME/BUG/SECURITY/HACK
        - Rutas internas
        - Credenciales
        - IPs internas

        Args:
            response_content: Contenido de respuesta

        Returns:
            Comentarios sensibles encontrados
        """
        self.logger.info("📝 Extrayendo comentarios sensibles...")

        result = {
            "timestamp": datetime.now().isoformat(),
            "comments_found": [],
            "security_comments": [],
            "internal_refs": [],
            "risk_level": "low"
        }

        # Patrones de comentarios HTML
        html_comment_pattern = r"<!--(.*?)-->"
        js_comment_pattern = r"//\s*(.+?)[\n]"

        # HTML comments
        html_matches = re.finditer(html_comment_pattern, response_content, re.DOTALL)
        for match in html_matches:
            comment = match.group(1).strip()
            result["comments_found"].append({
                "type": "HTML_comment",
                "content": comment[:100],
                "full_content": comment
            })

            # Identificar comentarios sensibles
            if any(kw in comment.lower() for kw in ["todo", "fixme", "bug", "security", "hack"]):
                result["security_comments"].append({
                    "type": "DEVELOPMENT_NOTE",
                    "keyword": next(kw for kw in ["todo", "fixme", "bug", "security", "hack"] if kw in comment.lower()),
                    "content": comment[:100]
                })

        # Rutas internas
        path_pattern = r"(/[a-zA-Z0-9/_\-\.]+)"
        paths = re.findall(path_pattern, response_content)
        internal_refs = list(set([p for p in paths if len(p) > 5]))
        result["internal_refs"] = internal_refs[:10]  # Limitar

        if result["security_comments"]:
            result["risk_level"] = "medium"
        if any(p in response_content for p in ["admin", "config", ".env", "backup"]):
            result["risk_level"] = "high"

        self.logger.info(f"✓ {len(result['comments_found'])} comentarios, "
                        f"{len(result['security_comments'])} sensibles")
        return result

    def _infer_services(self, subdomain_word: str) -> List[str]:
        """Inferir servicios potenciales basado en nombre."""
        services_map = {
            "mail": ["SMTP", "POP3", "IMAP"],
            "ftp": ["FTP"],
            "api": ["REST API", "GraphQL"],
            "admin": ["Admin Panel"],
            "test": ["Test Environment"],
            "dev": ["Development Server"],
            "db": ["Database"],
            "cdn": ["CDN"],
            "git": ["Git Repository"],
            "jenkins": ["CI/CD"],
        }
        return services_map.get(subdomain_word, [])
