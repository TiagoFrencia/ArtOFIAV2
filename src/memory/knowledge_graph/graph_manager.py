"""
Graph Manager - Controlador de Grafo de Conocimiento con Neo4j.

Gestiona las relaciones semánticas entre vulnerabilidades, endpoints, payloads
y tácticas de evasión. Proporciona contexto avanzado al orquestador para éviter
bucles y decisiones ciegas.

Responsabilidades:
- Mapeo de relaciones en el grafo (Endpoint → Token → Vulnerabilidad)
- Consultas semánticas rápidas (¿Qué táctica sirvió para este patrón antes?)
- Actualización incremental del grafo durante ejecución
- Detección de ciclos y rutas alternativas
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib

try:
    from neo4j import AsyncDriver, AsyncSession, Result
    from neo4j import basic_auth
except ImportError:
    AsyncDriver = None
    AsyncSession = None


class NodeType(Enum):
    """Tipos de nodos en el grafo."""
    ENDPOINT = "Endpoint"
    TOKEN = "Token"
    VULNERABILITY = "Vulnerability"
    PAYLOAD = "Payload"
    TACTIC = "Tactic"
    DEFENSE = "Defense"
    TARGET = "Target"
    AGENT = "Agent"


class RelationType(Enum):
    """Tipos de relaciones en el grafo."""
    REQUIRES = "REQUIRES"  # Endpoint requiere Token
    EXTRACTS_FROM = "EXTRACTS_FROM"  # Token extraído de Archivo
    EXPLOITS = "EXPLOITS"  # Payload explota Vulnerabilidad
    EVADES = "EVADES"  # Tática evade Defensa
    DISCOVERED_BY = "DISCOVERED_BY"  # Nodo descubierto por Agente
    FAILED_ON = "FAILED_ON"  # Táctica falló en Defensa
    ENABLED_BY = "ENABLED_BY"  # Acción habilitada por Token


@dataclass
class GraphNode:
    """Representa un nodo en el grafo."""
    id: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class GraphRelation:
    """Representa una relación en el grafo."""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8  # Confianza de la relación
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class GraphManager:
    """Controlador del grafo de conocimiento."""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        """
        Inicializa el gestor del grafo.
        
        Args:
            neo4j_uri: URI del servidor Neo4j (ej: bolt://localhost:7687)
            username: Usuario de Neo4j
            password: Contraseña de Neo4j
        """
        self.logger = logging.getLogger(__name__)
        
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password
        
        self.driver: Optional[AsyncDriver] = None
        self.session: Optional[AsyncSession] = None
        
        # Cache de nodos recientes
        self.node_cache: Dict[str, GraphNode] = {}
        
        # Estadísticas
        self.stats = {
            "nodes_created": 0,
            "relations_created": 0,
            "queries_executed": 0,
            "cache_hits": 0
        }
        
        self.logger.info("✓ GraphManager inicializado")
    
    async def connect(self) -> bool:
        """Conecta a Neo4j."""
        try:
            from neo4j import AsyncGraphDatabase
            
            self.driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=basic_auth(self.username, self.password)
            )
            
            # Verificar conexión
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            
            self.logger.info(f"✓ Conectado a Neo4j en {self.neo4j_uri}")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error conectando a Neo4j: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Desconecta de Neo4j."""
        if self.driver:
            await self.driver.close()
            self.logger.info("✓ Desconectado de Neo4j")
    
    def _generate_node_id(self, node_type: NodeType, name: str) -> str:
        """Genera ID único para nodo."""
        combined = f"{node_type.value}:{name}".lower()
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    async def create_node(
        self,
        node_type: NodeType,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        """
        Crea un nodo en el grafo.
        
        Args:
            node_type: Tipo de nodo
            name: Nombre del nodo
            properties: Propiedades adicionales
        
        Returns:
            GraphNode creado
        """
        node_id = self._generate_node_id(node_type, name)
        
        # Verificar cache
        if node_id in self.node_cache:
            self.logger.debug(f"  Cache hit: {node_type.value} {name}")
            self.stats["cache_hits"] += 1
            return self.node_cache[node_id]
        
        # Crear nodo
        node = GraphNode(
            id=node_id,
            node_type=node_type,
            properties={
                "name": name,
                **(properties or {})
            }
        )
        
        # Persistir en Neo4j
        if self.driver:
            try:
                async with self.driver.session() as session:
                    cypher = f"""
                    CREATE (n:{node_type.value} {{
                        id: $id,
                        name: $name,
                        properties: $props,
                        created_at: $created_at,
                        confidence: 0.8
                    }})
                    RETURN n
                    """
                    
                    await session.run(
                        cypher,
                        id=node_id,
                        name=name,
                        props=json.dumps(properties or {}),
                        created_at=node.created_at
                    )
                
                self.stats["nodes_created"] += 1
                self.logger.debug(f"  ✓ Nodo creado: {node_type.value} - {name}")
                
            except Exception as e:
                self.logger.warning(f"  ⚠ Error persistiendo nodo: {e}")
        
        # Cachear
        self.node_cache[node_id] = node
        return node
    
    async def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        confidence: float = 0.8,
        properties: Optional[Dict[str, Any]] = None
    ) -> GraphRelation:
        """
        Crea una relación entre dos nodos.
        
        Args:
            source_id: ID del nodo origen
            target_id: ID del nodo destino
            relation_type: Tipo de relación
            confidence: Confianza de la relación (0-1)
            properties: Propiedades adicionales
        
        Returns:
            GraphRelation creada
        """
        relation = GraphRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            confidence=min(1.0, max(0.0, confidence)),
            properties=properties or {}
        )
        
        # Persistir en Neo4j
        if self.driver:
            try:
                async with self.driver.session() as session:
                    cypher = f"""
                    MATCH (a) WHERE a.id = $source_id
                    MATCH (b) WHERE b.id = $target_id
                    CREATE (a)-[r:{relation_type.value} {{
                        confidence: $confidence,
                        properties: $props,
                        created_at: $created_at
                    }}]->(b)
                    RETURN r
                    """
                    
                    await session.run(
                        cypher,
                        source_id=source_id,
                        target_id=target_id,
                        confidence=confidence,
                        props=json.dumps(properties or {}),
                        created_at=relation.created_at
                    )
                
                self.stats["relations_created"] += 1
                self.logger.debug(f"  ✓ Relación creada: {relation_type.value}")
                
            except Exception as e:
                self.logger.warning(f"  ⚠ Error persistiendo relación: {e}")
        
        return relation
    
    async def query_by_semantic(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Ejecuta consulta semántica en el grafo.
        
        Ejemplos:
        - "¿Qué payloads han evadido WAF_CLOUDFLARE?"
        - "¿Qué token se necesita para acceder a /admin?"
        - "¿Cuál es la ruta más corta a la base de datos?"
        
        Args:
            query: Consulta en lenguaje natural
            limit: Límite de resultados
        
        Returns:
            Lista de resultados
        """
        self.logger.info(f"🔍 Consulta semántica: {query}")
        
        if not self.driver:
            self.logger.warning("  Driver no conectado")
            return []
        
        try:
            # En producción: usar LLM para traducir query a Cypher
            # Por ahora: ejemplos predefinidos
            
            cypher_queries = {
                "evaded": """
                    MATCH (p:Payload)-[r:EVADES]->(d:Defense)
                    WHERE d.name CONTAINS $defense
                    RETURN p.name as payload, r.confidence as confidence
                    ORDER BY confidence DESC
                    LIMIT $limit
                """,
                "requires": """
                    MATCH (e:Endpoint)-[r:REQUIRES]->(t:Token)
                    WHERE e.name CONTAINS $endpoint
                    RETURN t.name as token, r.confidence as confidence
                    LIMIT $limit
                """,
                "path": """
                    MATCH path = (a:Target)-[*]->(b:Vulnerability)
                    WHERE a.name CONTAINS $target
                    RETURN [n IN nodes(path) | n.name] as path_nodes,
                           length(path) as hops
                    LIMIT $limit
                """
            }
            
            # Detectar tipo de query
            query_lower = query.lower()
            cypher = None
            params = {"limit": limit}
            
            if "evad" in query_lower and "waf" in query_lower:
                cypher = cypher_queries["evaded"]
                params["defense"] = "WAF" if "WAF" in query else "Defense"
            elif "requir" in query_lower or "token" in query_lower:
                cypher = cypher_queries["requires"]
                params["endpoint"] = "/admin"  # Default
            elif "path" in query_lower:
                cypher = cypher_queries["path"]
                params["target"] = "Target"
            
            if not cypher:
                self.logger.warning("  ⚠ Query no reconocida")
                return []
            
            results = []
            async with self.driver.session() as session:
                records = await session.run(cypher, **params)
                async for record in records:
                    results.append(dict(record))
            
            self.stats["queries_executed"] += 1
            self.logger.info(f"  ✓ {len(results)} resultados encontrados")
            
            return results
            
        except Exception as e:
            self.logger.error(f"  ✗ Error en consulta: {e}")
            return []
    
    async def detect_cycles(self, start_node_id: str) -> List[List[str]]:
        """
        Detecta ciclos desde un nodo (indica repetición de acciones).
        
        Args:
            start_node_id: ID del nodo inicial
        
        Returns:
            Lista de ciclos (cada ciclo es una lista de node IDs)
        """
        if not self.driver:
            return []
        
        try:
            cypher = """
            MATCH path = (a)-[*2..]->(a)
            WHERE a.id = $start_id
            RETURN [n IN nodes(path) | n.name] as cycle
            """
            
            cycles = []
            async with self.driver.session() as session:
                records = await session.run(cypher, start_id=start_node_id)
                async for record in records:
                    cycles.append(record["cycle"])
            
            if cycles:
                self.logger.warning(f"  ⚠ {len(cycles)} ciclo(s) detectado(s)")
            
            return cycles
            
        except Exception as e:
            self.logger.error(f"  ✗ Error detectando ciclos: {e}")
            return []
    
    async def find_alternative_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_length: int = 5
    ) -> List[List[str]]:
        """
        Encuentra rutas alternativas entre dos nodos (si una táctica falla).
        
        Args:
            start_node_id: Nodo inicial
            end_node_id: Nodo final
            max_length: Largo máximo de ruta
        
        Returns:
            Lista de rutas alternativas
        """
        if not self.driver:
            return []
        
        try:
            cypher = f"""
            MATCH path = (a)-[*1..{max_length}]->(b)
            WHERE a.id = $start_id AND b.id = $end_id
            RETURN [n IN nodes(path) | n.name] as route,
                   length(path) as hops
            ORDER BY hops ASC
            LIMIT 10
            """
            
            routes = []
            async with self.driver.session() as session:
                records = await session.run(cypher, start_id=start_node_id, end_id=end_node_id)
                async for record in records:
                    routes.append({
                        "route": record["route"],
                        "hops": record["hops"]
                    })
            
            self.logger.info(f"  ✓ {len(routes)} ruta(s) alternativa(s) encontrada(s)")
            return routes
            
        except Exception as e:
            self.logger.error(f"  ✗ Error buscando rutas: {e}")
            return []
    
    async def update_confidence(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        confidence: float
    ) -> bool:
        """
        Actualiza confianza de una relación (después de éxito/fallo).
        
        Args:
            source_id: ID nodo origen
            target_id: ID nodo destino
            relation_type: Tipo relación
            confidence: Nueva confianza (0-1)
        
        Returns:
            True si se actualizó exitosamente
        """
        if not self.driver:
            return False
        
        try:
            confidence = min(1.0, max(0.0, confidence))
            
            cypher = f"""
            MATCH (a)-[r:{relation_type.value}]->(b)
            WHERE a.id = $source_id AND b.id = $target_id
            SET r.confidence = $confidence,
                r.updated_at = $timestamp
            RETURN r
            """
            
            async with self.driver.session() as session:
                result = await session.run(
                    cypher,
                    source_id=source_id,
                    target_id=target_id,
                    confidence=confidence,
                    timestamp=datetime.now().isoformat()
                )
                
                if await result.single():
                    self.logger.debug(f"  ✓ Confianza actualizada: {confidence}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"  ✗ Error actualizando confianza: {e}")
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del grafo."""
        return {
            "timestamp": datetime.now().isoformat(),
            **self.stats,
            "cache_size": len(self.node_cache)
        }
    
    async def export_subgraph(
        self,
        center_node_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Exporta subgrafo centrado en un nodo.
        
        Útil para: visualización, debugging, hand-off a otros agentes.
        
        Args:
            center_node_id: ID del nodo central
            depth: Profundidad del subgrafo
        
        Returns:
            Subgrafo como diccionario
        """
        if not self.driver:
            return {}
        
        try:
            cypher = f"""
            MATCH (center)-[*0..{depth}]-(node)
            WHERE center.id = $center_id
            RETURN collect(node) as nodes,
                   collect(relationships(center)) as relations
            """
            
            async with self.driver.session() as session:
                record = await session.run(cypher, center_id=center_node_id).single()
                
                if record:
                    return {
                        "center_id": center_node_id,
                        "depth": depth,
                        "nodes": [dict(n) for n in record["nodes"]],
                        "relations": record["relations"],
                        "exported_at": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            self.logger.error(f"  ✗ Error exportando subgrafo: {e}")
        
        return {}
