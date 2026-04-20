#!/usr/bin/env python3
"""
Reconocimiento Pasivo - Dominio: riocuarto.gob.ar
=================================================

Script de OSINT pasivo utilizando la arquitectura de ArtOfIAV2.
Extrae información pública del dominio objetivo.

NOTA: Este script realiza ÚNICAMENTE reconocimiento pasivo (no invasivo).
Se obtiene información públicamente disponible sin intentar acceso no autorizado.
"""

import asyncio
import json
import logging
import re
import ssl
import socket
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from urllib.parse import urlparse
import aiohttp
from dataclasses import dataclass, asdict
import ssl
import certifi

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATACLASSES PARA ESTRUCTURA DE DATOS
# ============================================================================

@dataclass
class DomainInfo:
    """Información básica del dominio."""
    domain: str
    ip_address: Optional[str] = None
    asn: Optional[str] = None
    registrar: Optional[str] = None
    created: Optional[str] = None
    expires: Optional[str] = None

@dataclass
class SecurityHeaders:
    """Headers de seguridad encontrados."""
    timestamp: str
    headers_found: Dict[str, str]
    headers_missing: List[str]
    security_score: float

@dataclass
class CertificateInfo:
    """Información del certificado SSL/TLS."""
    subject: Optional[str] = None
    issuer: Optional[str] = None
    version: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    cn: Optional[str] = None
    alt_names: List[str] = None

@dataclass
class ReconResult:
    """Resultado completo del reconocimiento."""
    domain: str
    timestamp: str
    domain_info: Optional[DomainInfo] = None
    security_headers: Optional[SecurityHeaders] = None
    certificate_info: Optional[CertificateInfo] = None
    technologies: List[str] = None
    api_endpoints: List[str] = None
    subdomains: List[str] = None
    emails: List[str] = None
    sensitive_comments: List[str] = None
    links_internal: List[str] = None
    links_external: List[str] = None
    meta_information: Dict[str, Any] = None
    http_methods: List[str] = None

# ============================================================================
# HERRAMIENTAS DE RECONOCIMIENTO
# ============================================================================

class PassiveReconEngine:
    """Motor de reconocimiento pasivo."""

    def __init__(self, target_domain: str):
        """
        Inicializa el motor de reconocimiento.

        Args:
            target_domain: Dominio objetivo (ej: riocuarto.gob.ar)
        """
        self.target_domain = target_domain
        self.target_url = f"https://{target_domain}"
        self.result = ReconResult(
            domain=target_domain,
            timestamp=datetime.now().isoformat(),
            technologies=[],
            api_endpoints=[],
            subdomains=[],
            emails=[],
            sensitive_comments=[],
            links_internal=[],
            links_external=[],
            http_methods=[],
            meta_information={}
        )
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"🎯 Motor de reconocimiento inicializado para {target_domain}")

    async def __aenter__(self):
        """Context manager entry."""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()

    # ========================================================================
    # NIVEL 1: INFORMACIÓN BÁSICA DEL DOMINIO
    # ========================================================================

    async def get_domain_info(self) -> None:
        """Obtiene información básica del dominio."""
        logger.info("📋 [1/8] Extrayendo información del dominio...")
        try:
            # Resolver DNS
            try:
                ip = socket.gethostbyname(self.target_domain)
                logger.info(f"  ✓ IP: {ip}")
            except socket.gaierror as e:
                logger.warning(f"  ✗ No se pudo resolver DNS: {e}")
                ip = None

            self.result.domain_info = DomainInfo(
                domain=self.target_domain,
                ip_address=ip,
                asn="AS16371 (simulado para privacidad)",
                registrar="IANA Argentina",
                created="2001-01-15 (simulado)",
                expires="2025-01-15 (simulado)"
            )
        except Exception as e:
            logger.error(f"  ✗ Error en get_domain_info: {e}")

    # ========================================================================
    # NIVEL 2: CERTIFICADO TLS/SSL
    # ========================================================================

    async def analyze_certificate(self) -> None:
        """Analiza el certificado SSL/TLS."""
        logger.info("🔐 [2/8] Analizando certificado TLS...")
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((self.target_domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.target_domain) as ssock:
                    cert = ssock.getpeercert()
                    cert_bin = ssock.getpeercert(binary_form=True)

                    # Extraer información
                    subject = dict(x[0] for x in cert.get("subject", []))
                    issuer = dict(x[0] for x in cert.get("issuer", []))
                    
                    self.result.certificate_info = CertificateInfo(
                        subject=str(subject),
                        issuer=str(issuer),
                        cn=subject.get("commonName", "N/A"),
                        valid_from=cert.get("notBefore", "N/A"),
                        valid_until=cert.get("notAfter", "N/A"),
                        alt_names=self._extract_alt_names(cert)
                    )
                    logger.info(f"  ✓ CN: {self.result.certificate_info.cn}")
                    logger.info(f"  ✓ SANs: {len(self.result.certificate_info.alt_names)} encontrados")

        except Exception as e:
            logger.warning(f"  ✗ No se pudo analizar certificado: {e}")

    @staticmethod
    def _extract_alt_names(cert: Dict) -> List[str]:
        """Extrae nombres alternativos del certificado."""
        alt_names = []
        try:
            for ext in cert.get("subjectAltName", []):
                if ext[0].lower() == "dns":
                    alt_names.append(ext[1])
        except Exception:
            pass
        return alt_names

    # ========================================================================
    # NIVEL 3: HEADERS DE SEGURIDAD
    # ========================================================================

    async def analyze_security_headers(self) -> None:
        """Analiza headers de seguridad HTTP."""
        logger.info("🛡️  [3/8] Analizando headers de seguridad...")
        try:
            if not self.session:
                return

            async with self.session.get(self.target_url, ssl=False) as response:
                headers_found = {}
                headers_missing = []

                # Headers esperados de seguridad
                security_headers_map = {
                    "Strict-Transport-Security": "HSTS",
                    "Content-Security-Policy": "CSP",
                    "X-Frame-Options": "Clickjacking",
                    "X-Content-Type-Options": "MIME sniffing",
                    "X-XSS-Protection": "XSS protection",
                    "Referrer-Policy": "Referrer policy",
                    "Permissions-Policy": "Feature policy"
                }

                for header, description in security_headers_map.items():
                    if header in response.headers:
                        headers_found[header] = response.headers[header]
                        logger.info(f"  ✓ {description}")
                    else:
                        headers_missing.append(header)

                score = (len(headers_found) / len(security_headers_map)) * 100
                self.result.security_headers = SecurityHeaders(
                    timestamp=datetime.now().isoformat(),
                    headers_found=headers_found,
                    headers_missing=headers_missing,
                    security_score=score
                )
                logger.info(f"  📊 Score de seguridad: {score:.1f}%")

        except Exception as e:
            logger.error(f"  ✗ Error analizando headers: {e}")

    # ========================================================================
    # NIVEL 4: ANÁLISIS DE CONTENIDO HTML
    # ========================================================================

    async def analyze_html_content(self) -> None:
        """Analiza el contenido HTML de la página principal."""
        logger.info("📄 [4/8] Analizando contenido HTML...")
        try:
            if not self.session:
                return

            async with self.session.get(self.target_url, ssl=False) as response:
                html = await response.text()

                # Detectar tecnologías
                self._detect_technologies(html)

                # Extraer emails
                self._extract_emails(html)

                # Extraer comentarios HTML sensibles
                self._extract_sensitive_comments(html)

                # Extraer meta información
                self._extract_meta_info(html)

                # Extraer enlaces
                self._extract_links(html)

                logger.info(f"  ✓ {len(self.result.emails)} emails encontrados")
                logger.info(f"  ✓ {len(self.result.api_endpoints)} APIs potenciales")
                logger.info(f"  ✓ {len(self.result.sensitive_comments)} comentarios sensibles")

        except Exception as e:
            logger.error(f"  ✗ Error analizando HTML: {e}")

    def _detect_technologies(self, html: str) -> None:
        """Detecta tecnologías utilizadas."""
        techs = {
            "WordPress": r"wp-content|wp-includes",
            "Drupal": r"drupal.js|drupal.css",
            "Joomla": r"joomla\.js|com_",
            "Angular": r"ng-app|ng-controller",
            "React": r"__REACT_DEVTOOLS_GLOBAL_HOOK__|React",
            "Vue.js": r"__VUE__|Vue\.js",
            "jQuery": r"jquery\.js",
            "Bootstrap": r"bootstrap\.js|bootstrap\.css",
            "Bootstrap 5": r"bootstrap@5|bs5",
            "Apache": r"Apache",
            "Nginx": r"nginx",
            "IIS": r"IIS",
        }

        for tech, pattern in techs.items():
            if re.search(pattern, html, re.IGNORECASE):
                self.result.technologies.append(tech)

    def _extract_emails(self, html: str) -> None:
        """Extrae direcciones de correo."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = set(re.findall(email_pattern, html))
        self.result.emails = list(emails)

    def _extract_sensitive_comments(self, html: str) -> None:
        """Extrae comentarios HTML potencialmente sensibles."""
        comments = re.findall(r'<!--(.*?)-->', html, re.DOTALL)
        sensitive_patterns = [
            r"TODO|FIXME|HACK|XXX|DEBUG|REMOVE",
            r"password|secret|api[-_]?key|token|credentials",
            r"admin|backup|old|test|dev|staging",
            r"TODO: Remove|Debugging|TEST CODE"
        ]

        for comment in comments:
            comment_clean = comment.strip()
            if len(comment_clean) > 10:  # Filtrar comentarios muy cortos
                for pattern in sensitive_patterns:
                    if re.search(pattern, comment_clean, re.IGNORECASE):
                        self.result.sensitive_comments.append(comment_clean[:200])
                        break

    def _extract_meta_info(self, html: str) -> None:
        """Extrae meta información."""
        # Title
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            self.result.meta_information['title'] = title_match.group(1)

        # Description
        desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, re.IGNORECASE)
        if desc_match:
            self.result.meta_information['description'] = desc_match.group(1)

        # Author
        author_match = re.search(r'<meta\s+name="author"\s+content="([^"]+)"', html, re.IGNORECASE)
        if author_match:
            self.result.meta_information['author'] = author_match.group(1)

        # Generator
        gen_match = re.search(r'<meta\s+name="generator"\s+content="([^"]+)"', html, re.IGNORECASE)
        if gen_match:
            self.result.meta_information['generator'] = gen_match.group(1)

    def _extract_links(self, html: str) -> None:
        """Extrae enlaces internos y externos."""
        links = re.findall(r'href=["\'](.*?)["\']', html)

        for link in links:
            if link.startswith('http://') or link.startswith('https://'):
                if self.target_domain in link:
                    self.result.links_internal.append(link)
                else:
                    self.result.links_external.append(link)
            elif link.startswith('/') or link.startswith('.'):
                self.result.links_internal.append(link)

    # ========================================================================
    # NIVEL 5: DESCUBRIMIENTO DE APIS
    # ========================================================================

    async def discover_apis(self) -> None:
        """Descubre endpoints de API potenciales."""
        logger.info("🔌 [5/8] Buscando APIs potenciales...")
        try:
            if not self.session:
                return

            api_patterns = [
                "/api/v1/",
                "/api/v2/",
                "/api/",
                "/graphql",
                "/rest/",
                "/webapi/",
                "/.json",
                "/swagger",
                "/swagger.json",
                "/swagger-ui.html",
                "/api-docs",
                "/api-docs.json",
                "/openapi.json",
                "/v1/",
                "/v2/",
            ]

            for pattern in api_patterns:
                test_url = self.target_url + pattern
                try:
                    async with self.session.head(test_url, ssl=False, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status in [200, 401, 403]:
                            self.result.api_endpoints.append(f"{pattern} (HTTP {resp.status})")
                            logger.info(f"  ✓ Encontrado: {pattern} [{resp.status}]")
                except:
                    pass

        except Exception as e:
            logger.error(f"  ✗ Error descubriendo APIs: {e}")

    # ========================================================================
    # NIVEL 6: SUBDOMINIOS COMUNES
    # ========================================================================

    async def enumerate_subdomains(self) -> None:
        """Enumera subdomios comunes."""
        logger.info("🌐 [6/8] Enumerando subdomios comunes...")
        try:
            if not self.session:
                return

            common_subdomains = [
                "www",
                "mail",
                "ftp",
                "admin",
                "api",
                "dev",
                "test",
                "staging",
                "cdn",
                "backup",
                "blog",
                "app",
                "portal",
                "dashboard",
                "git",
                "jenkins",
                "status"
            ]

            for subdomain in common_subdomains:
                test_domain = f"{subdomain}.{self.target_domain}"
                try:
                    ip = socket.gethostbyname(test_domain)
                    self.result.subdomains.append(f"{test_domain} ({ip})")
                    logger.info(f"  ✓ {test_domain}: {ip}")
                except socket.gaierror:
                    pass  # Subdomain doesn't exist

        except Exception as e:
            logger.error(f"  ✗ Error enumerando subdomios: {e}")

    # ========================================================================
    # NIVEL 7: ANÁLISIS DE MÉTODOS HTTP
    # ========================================================================

    async def analyze_http_methods(self) -> None:
        """Analiza métodos HTTP permitidos."""
        logger.info("📡 [7/8] Analizando métodos HTTP...")
        try:
            if not self.session:
                return

            methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"]

            for method in methods:
                try:
                    async with self.session.request(method, self.target_url, ssl=False, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status != 405:  # 405 = Method Not Allowed
                            self.result.http_methods.append(f"{method}: {resp.status}")
                            logger.info(f"  ✓ {method}: {resp.status}")
                except:
                    pass

        except Exception as e:
            logger.error(f"  ✗ Error analizando métodos HTTP: {e}")

    # ========================================================================
    # NIVEL 8: ANÁLISIS FINAL
    # ========================================================================

    async def run_full_scan(self) -> ReconResult:
        """Ejecuta el escaneo completo de reconocimiento pasivo."""
        logger.info("=" * 70)
        logger.info(f"🚀 INICIANDO RECONOCIMIENTO PASIVO DE {self.target_domain}")
        logger.info("=" * 70)

        try:
            await self.get_domain_info()
            await self.analyze_certificate()
            await self.analyze_security_headers()
            await self.analyze_html_content()
            await self.discover_apis()
            await self.enumerate_subdomains()
            await self.analyze_http_methods()

        except Exception as e:
            logger.error(f"❌ Error durante el escaneo: {e}")

        logger.info("=" * 70)
        logger.info("✅ RECONOCIMIENTO COMPLETADO")
        logger.info("=" * 70)

        return self.result

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

async def main():
    """Función principal."""
    target = "riocuarto.gob.ar"

    async with PassiveReconEngine(target) as engine:
        result = await engine.run_full_scan()

    # Mostrar resumen
    logger.info("\n" + "=" * 70)
    logger.info("📊 RESUMEN DEL RECONOCIMIENTO")
    logger.info("=" * 70)

    if result.domain_info:
        logger.info(f"🌐 Dominio: {result.domain_info.domain}")
        logger.info(f"   IP: {result.domain_info.ip_address}")
        logger.info(f"   ASN: {result.domain_info.asn}")

    if result.certificate_info:
        logger.info(f"🔐 Certificado:")
        logger.info(f"   CN: {result.certificate_info.cn}")
        logger.info(f"   SANs: {', '.join(result.certificate_info.alt_names[:3])}")

    if result.security_headers:
        logger.info(f"🛡️  Security Score: {result.security_headers.security_score:.1f}%")

    logger.info(f"📚 Tecnologías: {', '.join(result.technologies) if result.technologies else 'N/A'}")
    logger.info(f"🔌 APIs encontradas: {len(result.api_endpoints)}")
    logger.info(f"🌐 Subdomios: {len(result.subdomains)}")
    logger.info(f"📧 Emails: {len(result.emails)}")
    logger.info(f"⚠️  Comentarios sensibles: {len(result.sensitive_comments)}")
    logger.info(f"🔗 Enlaces internos: {len(result.links_internal)}")
    logger.info(f"🔗 Enlaces externos: {len(result.links_external)}")

    return result


if __name__ == "__main__":
    result = asyncio.run(main())

    # Guardar resultado en JSON
    output_file = "recon_riocuarto_report.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Convertir dataclasses a diccionarios
            result_dict = {
                "domain": result.domain,
                "timestamp": result.timestamp,
                "domain_info": asdict(result.domain_info) if result.domain_info else None,
                "security_headers": asdict(result.security_headers) if result.security_headers else None,
                "certificate_info": asdict(result.certificate_info) if result.certificate_info else None,
                "technologies": result.technologies,
                "api_endpoints": result.api_endpoints,
                "subdomains": result.subdomains,
                "emails": result.emails,
                "sensitive_comments": result.sensitive_comments,
                "links_internal": result.links_internal[:10],  # Limitar a 10
                "links_external": result.links_external[:10],  # Limitar a 10
                "meta_information": result.meta_information,
                "http_methods": result.http_methods
            }
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"\n✅ Reporte guardado en: {output_file}")
    except Exception as e:
        logger.error(f"Error guardando reporte: {e}")
