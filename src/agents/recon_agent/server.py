"""
Recon Agent Server - Agente de reconocimiento pasivo con DI pattern.

Responsabilidades:
- Inicializar servidor MCP con configuración inyectada
- Registrar herramientas (tools) disponibles
- Coordinar módulos especializados (JS analyzer, GraphQL mapper)
- Exponer capabilities al orchestrator

Hereda de BaseAgent para garantizar:
- Consistencia con otros agentes
- Inyección de dependencias
- Logging estructurado
- Type safety
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationException
from .js_analyzer import JavaScriptAnalyzer
from .graphql_mapper import GraphQLMapper
from .network_tools import NetworkTools


class ReconAgentServer(BaseAgent):
    """Agente MCP para el reconocimiento pasivo (DI pattern)."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Inicializa ReconAgent con inyección de dependencias.

        Args:
            config: Configuración desde .mcp.json
                Esperado: {"name": "recon_agent", "command": "...", "env": {...}}
        
        Raises:
            ValueError: Si configuración es inválida
        """
        # Llamar al padre (BaseAgent) para inicializar config y logger
        super().__init__(config, agent_name="ReconAgent")

        # Inicializar módulos especializados
        self.js_analyzer = JavaScriptAnalyzer()
        self.graphql_mapper = GraphQLMapper()
        self.network_tools = NetworkTools()

        # Registro de herramientas disponibles
        self.tools: Dict[str, Dict[str, Any]] = {}
        
        # Resultados de reconocimiento
        self.reconnaissance_results: Dict[str, Any] = {}

        self._register_tools()

        self.logger.info("✓ Módulos especializados inicializados")


    def _register_tools(self) -> None:
        """
        Registra todas las herramientas disponibles.
        
        Las herramientas se exponen como funciones que el orchestrator
        puede invocar. Esto mantiene el código limpio y modular.
        """
        self.logger.info("📋 Registrando herramientas...")


        # ===== JavaScript Analysis Tools =====
        self.tools["extract_javascript_files"] = {
            "function": self.js_analyzer.extract_javascript_files,
            "description": "Descarga y analiza archivos .js, .mjs, .chunk.js",
            "parameters": {
                "url": "URL del objetivo",
                "aggressive": "Incluir análisis agresivo (default: False)"
            },
            "category": "reconnaissance"
        }

        self.tools["deobfuscate_javascript"] = {
            "function": self.js_analyzer.deobfuscate_code,
            "description": "Desminifica y desobfusca código JavaScript",
            "parameters": {
                "code": "Código a desofuscar",
                "method": "Método de desofuscación (pretty|semantic|advanced)"
            },
            "category": "reconnaissance"
        }

        self.tools["extract_shadow_apis"] = {
            "function": self.js_analyzer.extract_shadow_apis,
            "description": "Extrae APIs ocultas, endpoints y credenciales de JS",
            "parameters": {
                "code": "Código JavaScript",
                "target_types": ["api_keys", "endpoints", "credentials", "comments"]
            },
            "category": "reconnaissance"
        }

        self.tools["analyze_dom_patterns"] = {
            "function": self.js_analyzer.analyze_dom_patterns,
            "description": "Analiza patrones vulnerables en el DOM y JavaScript",
            "parameters": {
                "html": "HTML de la página",
                "javascript": "Código JavaScript asociado"
            },
            "category": "reconnaissance"
        }

        # ===== GraphQL Mapping Tools =====
        self.tools["discover_graphql_endpoints"] = {
            "function": self.graphql_mapper.discover_graphql_endpoints,
            "description": "Descubre endpoints GraphQL (comunes y ocultos)",
            "parameters": {
                "target_url": "URL del objetivo",
                "endpoints_to_test": "Lista de endpoints a probar (default: lista común)"
            },
            "category": "reconnaissance"
        }

        self.tools["introspect_graphql_schema"] = {
            "function": self.graphql_mapper.introspect_graphql_schema,
            "description": "Extrae esquema completo vía introspection query",
            "parameters": {
                "graphql_url": "URL del endpoint GraphQL",
                "include_mutations": "Incluir mutaciones (default: True)"
            },
            "category": "reconnaissance"
        }

        self.tools["dump_graphql_schema"] = {
            "function": self.graphql_mapper.dump_graphql_schema,
            "description": "Vuelca esquema GraphQL a formato JSON/SDL",
            "parameters": {
                "graphql_url": "URL del endpoint GraphQL",
                "format": "json o sdl (default: json)"
            },
            "category": "reconnaissance"
        }

        self.tools["analyze_graphql_relationships"] = {
            "function": self.graphql_mapper.analyze_graphql_relationships,
            "description": "Analiza relaciones entre objetos y potenciales vulnerabilidades",
            "parameters": {
                "schema": "Esquema GraphQL extraído"
            },
            "category": "reconnaissance"
        }

        # ===== Network Tools =====
        self.tools["dns_enumeration"] = {
            "function": self.network_tools.dns_enumeration,
            "description": "Enumeración DNS y descubrimiento de subdominios",
            "parameters": {
                "domain": "Dominio a resolver",
                "methods": ["axfr", "wordlist", "brute"]
            },
            "category": "reconnaissance"
        }

        self.tools["analyze_http_headers"] = {
            "function": self.network_tools.analyze_http_headers,
            "description": "Analiza headers de seguridad HTTP",
            "parameters": {
                "url": "URL a analizar",
                "detailed": "Análisis detallado (default: False)"
            },
            "category": "reconnaissance"
        }

        self.tools["port_scan_passive"] = {
            "function": self.network_tools.port_scan_passive,
            "description": "Escaneo pasivo de puertos usando OSINT",
            "parameters": {
                "target": "Objetivo a escanear",
                "sources": ["shodan", "censys", "passive"]
            },
            "category": "reconnaissance"
        }

        self.tools["tls_certificate_analysis"] = {
            "function": self.network_tools.tls_certificate_analysis,
            "description": "Análisis de certificados TLS y extracción de SANs",
            "parameters": {
                "domain": "Dominio a analizar"
            },
            "category": "reconnaissance"
        }

        self.tools["extract_sensitive_comments"] = {
            "function": self.network_tools.extract_sensitive_comments,
            "description": "Extrae comentarios sensibles (TODO/FIXME/BUG)",
            "parameters": {
                "content": "Contenido a analizar",
                "types": ["TODO", "FIXME", "BUG", "SECURITY", "API_KEY"]
            },
            "category": "reconnaissance"
        }

        # ===== Meta Tools =====
        self.tools["list_available_tools"] = {
            "function": self.list_available_tools,
            "description": "Lista todas las herramientas disponibles",
            "parameters": {},
            "category": "meta"
        }

        self.tools["get_reconnaissance_results"] = {
            "function": self.get_reconnaissance_results,
            "description": "Obtiene resultados de reconocimiento acumulados",
            "parameters": {
                "target": "Objetivo específico (opcional)"
            },
            "category": "meta"
        }

        self.logger.info(f"✓ {len(self.tools)} herramientas registradas")

    def list_available_tools(self) -> List[Dict[str, Any]]:
        """Retorna lista de herramientas disponibles."""
        tools_info = []
        for tool_name, tool_info in self.tools.items():
            tools_info.append({
                "name": tool_name,
                "description": tool_info.get("description"),
                "category": tool_info.get("category"),
                "parameters": tool_info.get("parameters", {})
            })
        return tools_info

    async def invoke_tool(
        self, tool_name: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Invoca una herramienta registrada.

        Args:
            tool_name: Nombre de la herramienta
            **kwargs: Argumentos para la herramienta

        Returns:
            Resultado de la ejecución
        """
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Herramienta '{tool_name}' no existe"
            }

        tool_def = self.tools[tool_name]
        tool_func = tool_def["function"]

        try:
            self.logger.info(f"🔨 Invocando herramienta: {tool_name}")

            # Invocar herramienta
            if hasattr(tool_func, "__await__"):
                import asyncio
                result = await tool_func(**kwargs)
            else:
                result = tool_func(**kwargs)

            # Almacenar resultado
            if "target" in kwargs:
                target = kwargs["target"]
                if target not in self.reconnaissance_results:
                    self.reconnaissance_results[target] = []
                self.reconnaissance_results[target].append({
                    "tool": tool_name,
                    "timestamp": datetime.now().isoformat(),
                    "result": result
                })

            return {
                "status": "success",
                "tool": tool_name,
                "result": result
            }

        except Exception as e:
            self.logger.error(f"✗ Error invocando {tool_name}: {e}")
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(e)
            }

    def get_reconnaissance_results(self, target: str | None = None) -> Dict[str, Any]:
        """
        Obtiene resultados acumulados de reconocimiento.

        Args:
            target: Objetivo específico (opcional)

        Returns:
            Resultados compilados
        """
        if target:
            result: Dict[str, Any] = self.reconnaissance_results.get(target, {})
            return result
        return self.reconnaissance_results

    def get_capabilities(self) -> Dict[str, Any]:
        """Retorna capabilities del agente."""
        tools_list: List[Dict[str, Any]] = self.list_available_tools()
        return {
            "agent": "recon_agent",
            "version": "1.0.0",
            "capabilities": [
                "javascript_analysis",
                "graphql_discovery",
                "network_reconnaissance",
                "osint",
                "passive_scanning"
            ],
            "tools_count": len(self.tools),
            "stealth_mode": True,
            "tools": tools_list
        }

    async def execute(self, target: Any) -> Dict[str, Any]:
        """Ejecuta reconocimiento pasivo en target.
        
        Args:
            target: URL o dominio a reconocer
        
        Returns:
            Diccionario con resultados de reconocimiento
        """
        self._validate_target(target, (str,))
        self.logger.info(f"Ejecutando reconocimiento en: {target}")
        
        # Ejecutar análisis iniciales
        results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: GraphQL discovery
            graphql_result = await self.invoke_tool(
                "discover_graphql_endpoints",
                target_url=target
            )
            results["stages"]["graphql"] = graphql_result
            
            # Stage 2: Network reconnaissance
            network_result = await self.invoke_tool(
                "analyze_http_headers",
                url=target,
                detailed=True
            )
            results["stages"]["network"] = network_result
            
            self.logger.info(f"✓ Reconocimiento completado para {target}")
            results["status"] = "success"
            
        except Exception as e:
            self.logger.error(f"✗ Error durante reconocimiento: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def can_handle(self, target_type: str) -> bool:
        """Verifica si este agente puede procesar el tipo de target.
        
        Args:
            target_type: Tipo de target ("api", "web", "graphql", etc)
        
        Returns:
            True si puede procesar, False si no
        """
        handled_types = {
            "api",
            "web",
            "graphql",
            "javascript",
            "network",
            "osint",
            "passive"
        }
        return target_type.lower() in handled_types


async def main() -> None:
    """Punto de entrada principal."""
    try:
        server = ReconAgentServer()

        print("\n📡 Recon Agent Server Iniciado")
        print(f"✓ {len(server.tools)} herramientas disponibles")
        print("\nHerramientas:")
        for tool in server.list_available_tools():
            print(f"  - {tool['name']}: {tool['description']}")

        print("\n✓ Recon Agent listo para operaciones")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
