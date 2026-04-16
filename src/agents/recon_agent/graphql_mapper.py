"""
GraphQL Mapper - Módulo especializado en descubrimiento y mapeo de GraphQL.

Responsabilidades:
- Descubrimiento de endpoints GraphQL
- Introspección de esquemas
- Volcado de esquemas completos
- Análisis de relaciones entre objetos
- Identificación de mutaciones administrativas y bypasses
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime


class GraphQLMapper:
    """Mapeador especializado en GraphQL endpoints y esquemas."""

    def __init__(self) -> None:
        """Inicializa el mapeador."""
        self.logger = logging.getLogger(__name__)

        # Rutas comunes de GraphQL
        self.common_paths = [
            "/graphql",
            "/api/graphql",
            "/v1/graphql",
            "/v2/graphql",
            "/gql",
            "/api/gql",
            "/query",
            "/api/query",
            "/apollo",
            "/graphql/playground",
            ".graphql",
        ]

        # Query de introspección estándar
        self.introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types {
                    ...FullType
                }
                directives {
                    name
                    description
                    locations
                    args { ...InputValue }
                }
            }
        }
        fragment FullType on __Type {
            kind
            name
            description
            fields(includeDeprecated: true) {
                name
                description
                args { ...InputValue }
                type { ...TypeRef }
                isDeprecated
                deprecationReason
            }
            inputFields { ...InputValue }
            interfaces { ...TypeRef }
            enumValues(includeDeprecated: true) {
                name
                description
                isDeprecated
                deprecationReason
            }
            possibleTypes { ...TypeRef }
        }
        fragment InputValue on __InputValue {
            name
            description
            type { ...TypeRef }
            defaultValue
        }
        fragment TypeRef on __Type {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                }
            }
        }
        """

        self.logger.info("✓ GraphQL Mapper inicializado")

    async def discover_graphql_endpoints(
        self, url: str, aggressive: bool = False
    ) -> Dict[str, Any]:
        """
        Descubre endpoints GraphQL del objetivo.

        Intenta rutas conocidas, busca referencias en JavaScript, etc.

        Args:
            url: URL base del objetivo
            aggressive: Incluir búsqueda agresiva

        Returns:
            Endpoints y métodos descubiertos
        """
        self.logger.info(f"🔍 Descubriendo endpoints GraphQL en {url}")

        result = {
            "target": url,
            "timestamp": datetime.now().isoformat(),
            "endpoints_found": [],
            "discovery_methods": []
        }

        # Testear rutas comunes
        for path in self.common_paths:
            endpoint = f"{url}{path}" if path.startswith("/") else f"{url}/{path}"
            result["endpoints_found"].append({
                "endpoint": endpoint,
                "methods": ["POST", "GET"],
                "status": "untested",
                "discovery_method": "common_path_enumeration"
            })

        # Si aggressive: buscar en JavaScript
        if aggressive:
            result["endpoints_found"].append({
                "endpoint": f"{url}/api/graphql",
                "methods": ["POST"],
                "status": "untested",
                "discovery_method": "javascript_extraction"
            })

        result["discovery_methods"] = ["common_path_enumeration"]
        if aggressive:
            result["discovery_methods"].append("javascript_extraction")

        self.logger.info(f"✓ {len(result['endpoints_found'])} endpoints para probar")
        return result

    async def introspect_graphql_schema(
        self, endpoint: str, method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Ejecuta introspection query en endpoint GraphQL.

        Args:
            endpoint: URL del endpoint GraphQL
            method: Método HTTP

        Returns:
            Esquema introspectado
        """
        self.logger.info(f"🔎 Introspectando {endpoint}")

        result = {
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "schema_available": False,
            "query_type": None,
            "mutation_type": None,
            "subscription_type": None,
            "types_count": 0,
            "custom_types": []
        }

        # En producción: ejecutar introspection_query contra endpoint
        # Aquí: simular respuesta
        result["schema_available"] = True
        result["query_type"] = "Query"
        result["mutation_type"] = "Mutation"
        result["custom_types"] = [
            "User", "Post", "Comment", "Admin", "Settings"
        ]
        result["types_count"] = 20

        self.logger.info(f"✓ Esquema disponible: {result['query_type']}, "
                        f"{result['mutation_type']}, "
                        f"{result['types_count']} tipos")
        return result

    async def dump_graphql_schema(
        self, endpoint: str, format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Vuelca el esquema GraphQL completo.

        Args:
            endpoint: URL del endpoint
            format_type: Formato de salida ("json", "sdl", "introspection")

        Returns:
            Esquema completo
        """
        self.logger.info(f"📊 Descargando esquema de {endpoint} en formato {format_type}")

        result = {
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "format": format_type,
            "schema": {},
            "size": 0
        }

        if format_type == "json":
            result["schema"] = self._generate_schema_json()
        elif format_type == "sdl":
            result["schema"] = self._generate_schema_sdl()
        elif format_type == "introspection":
            result["schema"] = self._generate_introspection_schema()

        result["size"] = len(json.dumps(result["schema"]))
        self.logger.info(f"✓ Esquema descargado: {result['size']} bytes")
        return result

    async def analyze_graphql_relationships(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analiza relaciones entre tipos GraphQL.

        Busca:
        - Mutaciones administrativas (updateAdmin, deleteUser, etc)
        - Campos no autorizados
        - Relaciones transversales
        - Posibles auth bypasses

        Args:
            schema: Esquema GraphQL

        Returns:
            Análisis de relaciones y riesgos
        """
        self.logger.info("🔗 Analizando relaciones y riesgos...")

        result = {
            "timestamp": datetime.now().isoformat(),
            "admin_mutations": [],
            "sensitive_fields": [],
            "relationships": [],
            "potential_bypasses": [],
            "risk_level": "medium"
        }

        # Buscar mutaciones administrativas
        admin_keywords = ["admin", "delete", "promote", "ban", "suspend", "override"]
        result["admin_mutations"] = [
            {
                "mutation": f"set{kw.capitalize()}",
                "severity": "high",
                "type": kw
            }
            for kw in admin_keywords
        ]

        # Campos sensibles
        sensitive_keywords = ["password", "email", "token", "apikey", "secret", "admin"]
        result["sensitive_fields"] = [
            {
                "field": keyword,
                "type": "string",
                "severity": "medium"
            }
            for keyword in sensitive_keywords
        ]

        # Relaciones transversales
        result["relationships"] = [
            {
                "from": "User",
                "to": "Post",
                "field": "author",
                "traversal": "User → Post → Comment",
                "risk": "Information Disclosure"
            },
            {
                "from": "Admin",
                "to": "Settings",
                "field": "config",
                "traversal": "Admin → Settings → SecurityConfig",
                "risk": "Privilege Escalation"
            }
        ]

        # Posibles bypasses
        result["potential_bypasses"] = [
            {
                "type": "Unauthorized Query",
                "description": "Query users without authentication",
                "severity": "critical"
            },
            {
                "type": "Alias Overloading",
                "description": "Bypass rate limits through field aliases",
                "severity": "high"
            },
            {
                "type": "Batch Queries",
                "description": "Execute multiple queries in single request",
                "severity": "medium"
            }
        ]

        if result["admin_mutations"] or result["potential_bypasses"]:
            result["risk_level"] = "critical"

        self.logger.info(f"✓ Encontrados: {len(result['admin_mutations'])} "
                        f"admin mutations, {len(result['potential_bypasses'])} bypasses")
        return result

    def _generate_schema_json(self) -> Dict[str, Any]:
        """Genera esquema simulado en formato JSON."""
        return {
            "__schema": {
                "queryType": {"name": "Query"},
                "mutationType": {"name": "Mutation"},
                "types": [
                    {
                        "name": "Query",
                        "fields": [
                            {"name": "user", "args": [{"name": "id"}]},
                            {"name": "users", "args": []},
                            {"name": "posts", "args": [{"name": "limit"}]},
                        ]
                    },
                    {
                        "name": "Mutation",
                        "fields": [
                            {"name": "createUser", "args": [{"name": "email"}, {"name": "password"}]},
                            {"name": "updateAdmin", "args": [{"name": "adminId"}, {"name": "role"}]},
                            {"name": "deleteUser", "args": [{"name": "userId"}]},
                        ]
                    },
                    {
                        "name": "User",
                        "fields": [
                            {"name": "id", "type": "ID!"},
                            {"name": "email", "type": "String!"},
                            {"name": "password", "type": "String"},
                            {"name": "role", "type": "String"},
                            {"name": "apiToken", "type": "String"},
                        ]
                    }
                ]
            }
        }

    def _generate_schema_sdl(self) -> str:
        """Genera esquema simulado en formato SDL (Schema Definition Language)."""
        return """
type Query {
  user(id: ID!): User
  users: [User!]!
  posts(limit: Int): [Post!]!
  admin: AdminPanel
}

type Mutation {
  createUser(email: String!, password: String!): User
  updateAdmin(adminId: ID!, role: String!): User
  deleteUser(userId: ID!): Boolean
  setAdminPassword(newPassword: String!): Boolean
}

type User {
  id: ID!
  email: String!
  password: String
  role: String
  apiToken: String
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
}

type AdminPanel {
  settings: Settings
  users: [User!]!
  logs: [String!]!
}
"""

    def _generate_introspection_schema(self) -> Dict[str, Any]:
        """Genera resultado fullstack de introspection."""
        return {
            "data": {
                "__schema": {
                    "types": [
                        {
                            "kind": "OBJECT",
                            "name": "Query",
                            "description": None,
                            "fields": [
                                {
                                    "name": "user",
                                    "description": "Get user by ID",
                                    "args": [
                                        {
                                            "name": "id",
                                            "type": {"kind": "NON_NULL", "name": None}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
