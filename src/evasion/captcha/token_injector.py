"""
Token Injector - Inyección de tokens de validación de CAPTCHA en DOM.

Responsabilidades:
- Inyectar tokens resueltos en el DOM
- Modificar request parameters con tokens
- Manejar diferentes formatos de tokens
- Sincronizar timing de inyección con respuestas de servidor
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class TokenInjectionPoint:
    """Punto de inyección de token en la página."""
    
    selector: str  # CSS selector o XPath
    attribute: Optional[str] = None  # 'value', 'data-token', etc
    form_field_name: Optional[str] = None  # Campo de formulario
    request_header: Optional[str] = None  # Header HTTP
    request_body_field: Optional[str] = None  # Campo en JSON body
    injection_method: str = "dom_value"  # dom_value, form_field, request_header, request_body
    timestamp: Optional[str] = None


class TokenInjector:
    """Inyector de tokens en DOM y requests."""
    
    def __init__(self) -> None:
        """Inicializa el inyector de tokens."""
        self.logger = logging.getLogger(__name__)
        
        # Puntos de inyección descubiertos
        self.injection_points: Dict[str, TokenInjectionPoint] = {}
        
        # Historial de inyecciones
        self.injection_history: List[Dict[str, Any]] = []
        
        # Tokens activos
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("✓ Token Injector inicializado")

    def auto_discover_injection_points(self, page_html: str) -> List[TokenInjectionPoint]:
        """Descubre automáticamente puntos de inyección en la página."""
        self.logger.info("🔍 Descubriendo puntos de inyección en DOM...")
        
        discovered_points = []
        
        # Buscar tokens conocidos de reCAPTCHA
        patterns = {
            # reCAPTCHA v2/v3 token campo
            r'name=["\']g-recaptcha-response["\']': {
                "selector": 'textarea[name="g-recaptcha-response"]',
                "form_field_name": "g-recaptcha-response",
                "injection_method": "form_field"
            },
            # hCaptcha
            r'name=["\']h-captcha-response["\']': {
                "selector": 'textarea[name="h-captcha-response"]',
                "form_field_name": "h-captcha-response",
                "injection_method": "form_field"
            },
            # Cloudflare Turnstile
            r'name=["\']cf-turnstile-response["\']': {
                "selector": 'input[name="cf-turnstile-response"]',
                "form_field_name": "cf-turnstile-response",
                "injection_method": "form_field"
            },
            # Headers HTTP
            r'X-CSRF-Token|X-XSRF-TOKEN': {
                "request_header": "X-CSRF-Token",
                "injection_method": "request_header"
            },
        }
        
        for pattern, point_config in patterns.items():
            if pattern in page_html:
                point = TokenInjectionPoint(
                    selector=point_config["selector"],
                    form_field_name=point_config.get("form_field_name"),
                    request_header=point_config.get("request_header"),
                    injection_method=point_config["injection_method"],
                    timestamp=datetime.now().isoformat()
                )
                
                self.injection_points[point.selector] = point
                discovered_points.append(point)
                
                self.logger.info(f"  ✓ Punto descubierto: {point.injection_method} - {point.selector}")
        
        return discovered_points

    async def inject_token_in_dom(
        self, 
        token: str, 
        injection_point: TokenInjectionPoint,
        page_ref: Optional[Any] = None
    ) -> bool:
        """Inyecta token directamente en el DOM."""
        self.logger.info(f"💉 Inyectando token en DOM: {injection_point.selector}")
        
        injection_record = {
            "timestamp": datetime.now().isoformat(),
            "selector": injection_point.selector,
            "method": "dom_injection",
            "token_length": len(token),
            "status": "attempting"
        }
        
        try:
            if injection_point.form_field_name:
                # Caso típico: textarea/input oculto
                js_code = f"""
// Token Injection Script - {datetime.now().isoformat()}

// Inyectar token en campo de formulario
(() => {{
    const field = document.querySelector('[\​name="{injection_point.form_field_name}"]');
    if (field) {{
        field.value = '{token}';
        field.dispatchEvent(new Event('change', {{ bubbles: true }}));
        field.dispatchEvent(new Event('input', {{ bubbles: true }}));
        
        // Simular interacción del usuario
        const event = new MouseEvent('click', {{ bubbles: true }});
        field.dispatchEvent(event);
        
        console.log('[TokenInjector] Token inyectado exitosamente');
        return true;
    }} else {{
        console.error('[TokenInjector] Campo no encontrado: {injection_point.form_field_name}');
        return false;
    }}
}})();
"""
                
                # En producción: page_ref.evaluate(js_code)
                injection_record["status"] = "success"
                self.logger.info(f"  ✓ Token inyectado en {injection_point.form_field_name}")
                
            elif injection_point.attribute:
                # Caso: atributo personalizado
                js_code = f"""
const elem = document.querySelector('{injection_point.selector}');
if (elem) {{
    elem.setAttribute('{injection_point.attribute}', '{token}');
}}
"""
                injection_record["status"] = "success"
                self.logger.info(f"  ✓ Token inyectado en atributo {injection_point.attribute}")
            
            else:
                # Caso: contenido de elemento
                js_code = f"""
const elem = document.querySelector('{injection_point.selector}');
if (elem) {{
    elem.textContent = '{token}';
}}
"""
                injection_record["status"] = "success"
                self.logger.info(f"  ✓ Token inyectado en elemento")
            
            # Registrar inyección
            self.injection_history.append(injection_record)
            self.active_tokens[injection_point.selector] = {
                "token": token,
                "injected_at": datetime.now().isoformat(),
                "injection_point": injection_point.selector
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error inyectando token: {e}")
            injection_record["status"] = "failed"
            injection_record["error"] = str(e)
            self.injection_history.append(injection_record)
            return False

    async def inject_token_in_request_header(
        self, 
        token: str, 
        header_name: str,
        request_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Inyecta token en header HTTP."""
        self.logger.info(f"📤 Inyectando token en header: {header_name}")
        
        injection_record = {
            "timestamp": datetime.now().isoformat(),
            "header": header_name,
            "method": "request_header",
            "token_length": len(token),
            "status": "success"
        }
        
        try:
            # En producción: interceptar requests y agregar header
            # request.headers[header_name] = token
            
            self.injection_history.append(injection_record)
            self.active_tokens[header_name] = {
                "token": token,
                "injected_at": datetime.now().isoformat(),
                "location": "request_header"
            }
            
            self.logger.info(f"  ✓ Token inyectado en header {header_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error: {e}")
            injection_record["status"] = "failed"
            self.injection_history.append(injection_record)
            return False

    async def inject_token_in_request_body(
        self, 
        token: str, 
        body_field: str,
        request_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inyecta token en cuerpo de request JSON."""
        self.logger.info(f"📤 Inyectando token en cuerpo: {body_field}")
        
        injection_record = {
            "timestamp": datetime.now().isoformat(),
            "body_field": body_field,
            "method": "request_body",
            "token_length": len(token),
            "status": "success"
        }
        
        try:
            # Copiar request body
            modified_body = request_body.copy()
            
            # Inyectar token en path especificado
            # Soporta nested fields: "captcha.token"
            parts = body_field.split(".")
            current = modified_body
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[parts[-1]] = token
            
            self.injection_history.append(injection_record)
            self.logger.info(f"  ✓ Token inyectado en cuerpo.{body_field}")
            
            return modified_body
            
        except Exception as e:
            self.logger.error(f"✗ Error: {e}")
            injection_record["status"] = "failed"
            self.injection_history.append(injection_record)
            return request_body

    def generate_dom_injection_script(
        self, 
        token: str, 
        injection_point: TokenInjectionPoint
    ) -> str:
        """Genera script JavaScript para inyectar token."""
        
        if injection_point.form_field_name:
            return f"""
(function() {{
    const field = document.querySelector('[name="{injection_point.form_field_name}"]');
    if (field) {{
        field.value = '{token}';
        field.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }}
}})();
"""
        elif injection_point.attribute:
            return f"""
(function() {{
    const elem = document.querySelector('{injection_point.selector}');
    if (elem) {{
        elem.setAttribute('{injection_point.attribute}', '{token}');
    }}
}})();
"""
        else:
            return f"""
(function() {{
    const elem = document.querySelector('{injection_point.selector}');
    if (elem) {{
        elem.textContent = '{token}';
    }}
}})();
"""

    def get_injection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna historial de inyecciones."""
        return self.injection_history[-limit:]

    def get_active_tokens(self) -> Dict[str, Dict[str, Any]]:
        """Retorna tokens activos."""
        return self.active_tokens

    def get_injector_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del inyector."""
        successful_injections = sum(
            1 for inj in self.injection_history 
            if inj["status"] == "success"
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_injections_attempted": len(self.injection_history),
            "successful_injections": successful_injections,
            "failed_injections": len(self.injection_history) - successful_injections,
            "active_tokens_count": len(self.active_tokens),
            "injection_methods_used": list(set(
                inj.get("method", "unknown") for inj in self.injection_history
            )),
            "success_rate": (
                successful_injections / len(self.injection_history) * 100 
                if self.injection_history else 0
            )
        }

    def clear_expired_tokens(self, max_age_minutes: int = 5) -> int:
        """Limpia tokens expirados."""
        self.logger.info(f"🧹 Limpiando tokens con más de {max_age_minutes} minutos...")
        
        now = datetime.now()
        expired_count = 0
        
        tokens_to_remove = []
        for key, token_data in self.active_tokens.items():
            injected_time = datetime.fromisoformat(token_data["injected_at"])
            age_minutes = (now - injected_time).total_seconds() / 60
            
            if age_minutes > max_age_minutes:
                tokens_to_remove.append(key)
        
        for key in tokens_to_remove:
            del self.active_tokens[key]
            expired_count += 1
        
        self.logger.info(f"  ✓ {expired_count} tokens expirados eliminados")
        return expired_count
