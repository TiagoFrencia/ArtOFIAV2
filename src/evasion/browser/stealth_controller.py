"""
Stealth Controller - Gestión de automatización de navegador con sigilo.

Responsabilidades:
- Gestionar conexión WebSocket hacia Browserless
- Configurar Playwright con plugins de sigilo
- Orquestar inyección de modificaciones de fingerprint
- Monitorear tráfico para detectar cambios de WAF en tiempo real
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class StealthConfig:
    """Configuración de evasión de sigilo."""
    
    # Browserless
    browserless_url: str = "ws://localhost:3000"  # Or remote browserless service
    use_browserless: bool = True
    
    # Playwright
    headless: bool = False  # Headful mode is more stealthy
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    device_emulation: Optional[str] = None  # "iPhone 12", "Pixel 5", etc
    
    # Stealth plugins
    enable_stealth_plugins: bool = True
    enable_fingerprint_spoofing: bool = True
    enable_jitter: bool = True
    
    # Fingerprint randomization
    randomize_user_agent: bool = True
    randomize_webgl: bool = True
    randomize_canvas: bool = True
    randomize_fonts: bool = True
    randomize_navigator: bool = True
    randomize_geolocation: bool = True
    
    # Timing
    navigation_timeout: int = 30000  # ms
    action_timeout: int = 10000  # ms
    idle_wait: int = 2000  # ms
    
    # Proxy settings
    proxy_url: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None


class StealthController:
    """Controlador de automatización con sigilo."""
    
    def __init__(self, config: Optional[StealthConfig] = None) -> None:
        """Inicializa el controlador de sigilo."""
        self.logger = logging.getLogger(__name__)
        self.config = config or StealthConfig()
        
        # Estado de la conexión
        self._browser = None
        self._context = None
        self._page = None
        self._is_connected = False
        self._stealth_injections: Dict[str, bool] = {}
        
        # Monitoreo
        self._request_log: List[Dict[str, Any]] = []
        self._waf_responses: List[Dict[str, Any]] = []
        self._detection_count = 0
        
        self.logger.info(f"✓ Stealth Controller inicializado (Browserless: {self.config.use_browserless})")

    async def connect(self) -> bool:
        """Establece conexión con Browserless (si se usa) y lanza el navegador."""
        self.logger.info("🔗 Conectando al navegador...")
        
        try:
            # En producción: conectar a Browserless o usar Playwright directamente
            if self.config.use_browserless:
                await self._connect_browserless()
            else:
                await self._connect_playwright()
            
            self._is_connected = True
            self.logger.info("✓ Conexión establecida")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error de conexión: {e}")
            return False

    async def _connect_browserless(self) -> None:
        """Conecta a servicio Browserless remoto."""
        self.logger.info(f"📡 Conectando a Browserless: {self.config.browserless_url}")
        
        # En producción: usar httpx o websockets
        # Aquí: simulación de flujo
        import asyncio
        await asyncio.sleep(0.1)  # Simulate connection latency
        
        self.logger.info("✓ Browserless conectado")

    async def _connect_playwright(self) -> None:
        """Conecta directamente con Playwright."""
        self.logger.info("🎭 Iniciando Playwright...")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            self.logger.error("⚠️ Playwright no instalado. Instalar: pip install playwright")
            return
        
        async with async_playwright() as p:
            # Launch with stealth options
            launch_args = {
                "headless": self.config.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--no-default-browser-check",
                ]
            }
            
            if self.config.proxy_url:
                launch_args["proxy"] = {
                    "server": self.config.proxy_url,
                    "username": self.config.proxy_username,
                    "password": self.config.proxy_password,
                } if self.config.proxy_username else {"server": self.config.proxy_url}
            
            # Note: In production, store browser reference properly
            self.logger.info("✓ Playwright iniciado")

    async def apply_stealth_plugins(self) -> None:
        """Aplica plugins de sigilo para evadir detección."""
        self.logger.info("🎭 Aplicando plugins de sigilo...")
        
        injections = []
        
        if self.config.enable_stealth_plugins:
            # Disable WebDriver property
            injections.append(self._get_webdriver_evasion())
            self._stealth_injections["webdriver_evasion"] = True
            
            # Override navigator.permissions
            injections.append(self._get_permissions_override())
            self._stealth_injections["permissions_override"] = True
            
            # Mask chrome object
            injections.append(self._get_chrome_mask())
            self._stealth_injections["chrome_mask"] = True
            
            # Disable automation indicators
            injections.append(self._get_automation_evasion())
            self._stealth_injections["automation_evasion"] = True
        
        self.logger.info(f"✓ {len(injections)} plugins de sigilo aplicados")

    async def apply_fingerprint_spoofing(self, fingerprint_config: Optional[Dict[str, Any]] = None) -> None:
        """Inyecta modificaciones de fingerprint para parecer navegador real."""
        self.logger.info("🖨️ Aplicando fingerprint spoofing...")
        
        if not fingerprint_config:
            fingerprint_config = {
                "webgl": True,
                "canvas": True,
                "fonts": True,
                "navigator": True,
                "geolocation": True,
            }
        
        injections = []
        
        if fingerprint_config.get("webgl"):
            injections.append(self._get_webgl_fingerprint())
            self.logger.info("  ✓ WebGL fingerprint randomizado")
        
        if fingerprint_config.get("canvas"):
            injections.append(self._get_canvas_fingerprint())
            self.logger.info("  ✓ Canvas fingerprint randomizado")
        
        if fingerprint_config.get("fonts"):
            injections.append(self._get_fonts_override())
            self.logger.info("  ✓ Fuentes modificadas")
        
        if fingerprint_config.get("navigator"):
            injections.append(self._get_navigator_override())
            self.logger.info("  ✓ Navigator properties alteradas")
        
        if fingerprint_config.get("geolocation"):
            injections.append(self._get_geolocation_mock())
            self.logger.info("  ✓ Geolocalización mockada")
        
        self.logger.info(f"✓ Fingerprint spoofing aplicado ({len(injections)} inyecciones)")

    async def navigate_stealthily(self, url: str, wait_until: str = "networkidle") -> bool:
        """Navega hacia URL con comportamiento humano."""
        self.logger.info(f"🌐 Navegando a {url}...")
        
        try:
            # Simulate human-like navigation delays
            await asyncio.sleep(0.5 + (await self._get_random_jitter()))
            
            # Log navigation request
            self._request_log.append({
                "timestamp": datetime.now().isoformat(),
                "type": "navigation",
                "url": url,
                "status": "attempting"
            })
            
            # En producción: usar page.goto(url, wait_until=wait_until)
            self.logger.info(f"✓ Navegación a {url} completada")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error durante navegación: {e}")
            self._waf_responses.append({
                "timestamp": datetime.now().isoformat(),
                "type": "navigation_blocked",
                "error": str(e)
            })
            self._detection_count += 1
            return False

    async def execute_action(self, action_type: str, selector: str, **kwargs) -> Dict[str, Any]:
        """Ejecuta acción (click, type, scroll) con timing humano."""
        self.logger.info(f"⚙️ Ejecutando acción: {action_type} en {selector}")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "selector": selector,
            "status": "pending",
            "result": None
        }
        
        try:
            # Add human-like delay before action
            await asyncio.sleep(0.2 + (await self._get_random_jitter()))
            
            if action_type == "click":
                # En producción: page.click(selector)
                result["status"] = "success"
                result["result"] = "Elemento clickeado"
                
            elif action_type == "type":
                text = kwargs.get("text", "")
                # En producción: page.type(selector, text, delay=50-150)
                result["status"] = "success"
                result["result"] = f"Texto escrito: {text[:20]}..."
                
            elif action_type == "scroll":
                # En producción: page.evaluate(f"window.scrollBy({kwargs.get('x', 0)}, {kwargs.get('y', 500)})")
                result["status"] = "success"
                result["result"] = "Página scrolleada"
                
            elif action_type == "screenshot":
                # En producción: page.screenshot(path=kwargs.get('path'))
                result["status"] = "success"
                result["result"] = f"Captura guardada"
            
            self._request_log.append(result)
            return result
            
        except Exception as e:
            result["status"] = "error"
            result["result"] = str(e)
            self._waf_responses.append(result)
            self._detection_count += 1
            return result

    async def get_page_content(self, selector: Optional[str] = None) -> str:
        """Obtiene contenido de la página."""
        self.logger.info(f"📄 Obteniendo contenido{'del selector ' + selector if selector else ''}")
        
        if selector:
            # En producción: element = page.query_selector(selector)
            # content = element.text_content()
            return f"Contenido del selector {selector}"
        else:
            # En producción: content = page.content()
            return "<html><body>Contenido simulado</body></html>"

    async def wait_for_condition(
        self, 
        condition_type: str, 
        target: str, 
        timeout: int = 10000
    ) -> bool:
        """Espera a una condición específica con timeout."""
        self.logger.info(f"⏱️ Esperando {condition_type}: {target} ({timeout}ms)")
        
        try:
            if condition_type == "selector":
                # En producción: page.wait_for_selector(target, timeout=timeout)
                pass
            elif condition_type == "navigation":
                # En producción: page.wait_for_load_state("networkidle", timeout=timeout)
                pass
            elif condition_type == "xpath":
                # En producción: page.wait_for_xpath(target, timeout=timeout)
                pass
            
            self.logger.info(f"✓ Condición cumplida")
            return True
            
        except asyncio.TimeoutError:
            self.logger.warning(f"⚠️ Timeout esperando {condition_type}")
            return False

    async def intercept_requests(self, callback: Callable) -> None:
        """Intercepta y modifica requests antes de enviarlos."""
        self.logger.info("🔍 Configurando interceptor de requests...")
        
        # En producción:
        # page.on("request", lambda request: asyncio.create_task(callback(request)))
        
        self.logger.info("✓ Interceptor configurado")

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de monitoreo de evasión."""
        return {
            "timestamp": datetime.now().isoformat(),
            "is_connected": self._is_connected,
            "stealth_plugins_applied": self._stealth_injections,
            "total_requests": len(self._request_log),
            "waf_detections": self._detection_count,
            "detection_events": self._waf_responses[-10:] if self._waf_responses else [],
            "request_log_sample": self._request_log[-5:] if self._request_log else [],
        }

    async def close(self) -> None:
        """Cierra la conexión de forma limpia."""
        self.logger.info("🔌 Cerrando conexión...")
        
        # En producción: await browser.close()
        self._is_connected = False
        self.logger.info("✓ Conexión cerrada")

    # Private helper methods
    
    def _get_webdriver_evasion(self) -> str:
        """Script para evitar detección de WebDriver."""
        return """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        """

    def _get_permissions_override(self) -> str:
        """Script para sobreescribir navigator.permissions."""
        return """
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """

    def _get_chrome_mask(self) -> str:
        """Script para enmascarar objeto chrome."""
        return """
        window.chrome = {
            runtime: {}
        };
        """

    def _get_automation_evasion(self) -> str:
        """Script para evitar indicadores de automatización."""
        return """
        Object.define Property(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        """

    def _get_webgl_fingerprint(self) -> str:
        """Script para randomizar WebGL fingerprint."""
        return """
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
        """

    def _get_canvas_fingerprint(self) -> str:
        """Script para randomizar Canvas fingerprint."""
        return """
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
            if (this.width === 280 && this.height === 60) {
                // Canvas fingerprinting attempt detected, return fake data
                return 'data:image/png;base64,iVBORw0KGgo...';
            }
            return originalToDataURL.call(this);
        };
        """

    def _get_fonts_override(self) -> str:
        """Script para modificar fuentes disponibles."""
        return """
        const fontList = ['Arial', 'Times New Roman', 'Courier New', 'Georgia', 'Verdana'];
        Document.fonts = new Proxy(Document.fonts || {}, {
            get: (target, prop) => {
                if (prop === 'check') {
                    return () => true;
                }
                return target[prop];
            }
        });
        """

    def _get_navigator_override(self) -> str:
        """Script para alterar propiedades de navigator."""
        return """
        Object.defineProperty(navigator, 'userAgent', {
            get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        });
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
        """

    def _get_geolocation_mock(self) -> str:
        """Script para mockear geolocalización."""
        return """
        navigator.geolocation.getCurrentPosition = (success) => {
            success({
                coords: {
                    latitude: 40.7128,
                    longitude: -74.0060,
                    accuracy: 50
                }
            });
        };
        """

    async def _get_random_jitter(self) -> float:
        """Genera jitter aleatorio para comportamiento humano."""
        import random
        return random.uniform(0.0, 0.5)
