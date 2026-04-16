"""
Neo4j Index Management - Create indexes for performance optimization

Common queries need indexes on:
- node.id (by both type and id)
- node.name (for CONTAINS queries)
- node.created_at (for time-based queries)
- relationship types (for pattern matching)
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


# Index definitions for all node types and queries
INDEXES = [
    # ============================================================
    # NODE TYPE INDEXES
    # ============================================================
    {
        "name": "idx_endpoint_id",
        "type": "node",
        "label": "Endpoint",
        "properties": ["id"],
        "purpose": "Fast lookup of endpoints by id"
    },
    {
        "name": "idx_token_id",
        "type": "node",
        "label": "Token",
        "properties": ["id"],
        "purpose": "Fast lookup of tokens by id"
    },
    {
        "name": "idx_vulnerability_id",
        "type": "node",
        "label": "Vulnerability",
        "properties": ["id"],
        "purpose": "Fast lookup of vulnerabilities by id"
    },
    {
        "name": "idx_payload_id",
        "type": "node",
        "label": "Payload",
        "properties": ["id"],
        "purpose": "Fast lookup of payloads by id"
    },
    {
        "name": "idx_tactic_id",
        "type": "node",
        "label": "Tactic",
        "properties": ["id"],
        "purpose": "Fast lookup of tactics by id"
    },
    {
        "name": "idx_defense_id",
        "type": "node",
        "label": "Defense",
        "properties": ["id"],
        "purpose": "Fast lookup of defenses by id"
    },
    {
        "name": "idx_target_id",
        "type": "node",
        "label": "Target",
        "properties": ["id"],
        "purpose": "Fast lookup of targets by id"
    },
    {
        "name": "idx_agent_id",
        "type": "node",
        "label": "Agent",
        "properties": ["id"],
        "purpose": "Fast lookup of agents by id"
    },
    
    # ============================================================
    # TEXT SEARCH INDEXES (for CONTAINS queries)
    # ============================================================
    {
        "name": "idx_endpoint_name",
        "type": "node",
        "label": "Endpoint",
        "properties": ["name"],
        "purpose": "Full-text search on endpoint names (CONTAINS queries)"
    },
    {
        "name": "idx_vulnerability_name",
        "type": "node",
        "label": "Vulnerability",
        "properties": ["name"],
        "purpose": "Full-text search on vulnerability names"
    },
    {
        "name": "idx_payload_name",
        "type": "node",
        "label": "Payload",
        "properties": ["name"],
        "purpose": "Full-text search on payload names"
    },
    {
        "name": "idx_tactic_name",
        "type": "node",
        "label": "Tactic",
        "properties": ["name"],
        "purpose": "Full-text search on tactic names"
    },
    {
        "name": "idx_defense_name",
        "type": "node",
        "label": "Defense",
        "properties": ["name"],
        "purpose": "Full-text search on defense names"
    },
    {
        "name": "idx_target_name",
        "type": "node",
        "label": "Target",
        "properties": ["name"],
        "purpose": "Full-text search on target names"
    },
    
    # ============================================================
    # TIME-SERIES INDEXES (for time-based queries)
    # ============================================================
    {
        "name": "idx_created_at_endpoint",
        "type": "node",
        "label": "Endpoint",
        "properties": ["created_at"],
        "purpose": "Filter endpoints by creation time"
    },
    {
        "name": "idx_updated_at_vulnerability",
        "type": "node",
        "label": "Vulnerability",
        "properties": ["updated_at"],
        "purpose": "Filter by last update time"
    },
    
    # ============================================================
    # COMPOSITE INDEXES (for common multi-property queries)
    # ============================================================
    {
        "name": "idx_endpoint_type_id",
        "type": "node",
        "label": "Endpoint",
        "properties": ["id", "type"],
        "purpose": "Fast lookup of specific endpoint types"
    },
    {
        "name": "idx_vulnerability_severity_id",
        "type": "node",
        "label": "Vulnerability",
        "properties": ["id", "severity"],
        "purpose": "Filter vulnerabilities by severity"
    },
    
    # ============================================================
    # RELATIONSHIP INDEXES (for pattern matching)
    # ============================================================
    {
        "name": "idx_requires_relation",
        "type": "relationship",
        "name": "REQUIRES",
        "properties": ["confidence"],
        "purpose": "Fast traversal of REQUIRES relationships"
    },
    {
        "name": "idx_exploits_relation",
        "type": "relationship",
        "name": "EXPLOITS",
        "properties": ["confidence"],
        "purpose": "Find payloads that exploit vulnerabilities"
    },
    {
        "name": "idx_evades_relation",
        "type": "relationship",
        "name": "EVADES",
        "properties": ["confidence"],
        "purpose": "Find evasion tactics"
    },
    {
        "name": "idx_discovered_by_relation",
        "type": "relationship",
        "name": "DISCOVERED_BY",
        "properties": ["timestamp"],
        "purpose": "Track discovery timeline"
    },
]


async def create_indexes(session) -> Dict[str, Any]:
    """
    Create all optimization indexes.
    
    Args:
        session: Neo4j AsyncSession
    
    Returns:
        Dict with creation results
    """
    results = {
        "created": [],
        "failed": [],
        "skipped": [],
        "total": len(INDEXES)
    }
    
    for index_def in INDEXES:
        try:
            if index_def["type"] == "node":
                # Create node indexes
                cypher = f"""
                    CREATE INDEX {index_def['name']}
                    FOR (n:{index_def['label']})
                    ON ({', '.join([f'n.{prop}' for prop in index_def['properties']])})
                """
                
                await session.run(cypher)
                results["created"].append(index_def["name"])
                logger.info(f"✓ Created index: {index_def['name']}")
            
            elif index_def["type"] == "relationship":
                # Create relationship indexes
                rel_type = index_def["name"]
                cypher = f"""
                    CREATE INDEX {index_def['name']}
                    FOR ()-[r:{rel_type}]-()
                    ON ({', '.join([f'r.{prop}' for prop in index_def['properties']])})
                """
                
                await session.run(cypher)
                results["created"].append(index_def["name"])
                logger.info(f"✓ Created index: {index_def['name']}")
        
        except Exception as e:
            # Index might already exist or other error
            if "already exists" in str(e).lower() or "exists" in str(e).lower():
                results["skipped"].append(index_def["name"])
                logger.debug(f"⊕ Index already exists: {index_def['name']}")
            else:
                results["failed"].append({
                    "name": index_def["name"],
                    "error": str(e)
                })
                logger.error(f"✗ Failed to create index {index_def['name']}: {e}")
    
    return results


async def get_index_status(session) -> List[Dict[str, Any]]:
    """Get status of all indexes"""
    cypher = "SHOW INDEXES"
    
    try:
        result = await session.run(cypher)
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Failed to get index status: {e}")
        return []


async def drop_index(session, index_name: str) -> bool:
    """Drop a specific index"""
    cypher = f"DROP INDEX {index_name}"
    
    try:
        await session.run(cypher)
        logger.info(f"Dropped index: {index_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to drop index {index_name}: {e}")
        return False


async def rebuild_indexes(session) -> Dict[str, Any]:
    """
    Rebuild all indexes (for optimization after bulk operations).
    
    Neo4j automatically maintains indexes, but explicit rebuild can help
    optimize query plans after significant data changes.
    """
    logger.info("Starting index rebuild...")
    
    indexes = await get_index_status(session)
    rebuild_count = 0
    failed_count = 0
    
    for idx in indexes:
        idx_name = idx.get("name")
        if not idx_name:
            continue
        
        try:
            cypher = f"CALL db.indexes.rebuild('{idx_name}')"
            await session.run(cypher)
            rebuild_count += 1
            logger.info(f"Rebuilt index: {idx_name}")
        except Exception as e:
            failed_count += 1
            logger.warning(f"Could not rebuild {idx_name}: {e}")
    
    return {
        "rebuilt": rebuild_count,
        "failed": failed_count,
        "total": len(indexes)
    }


# ============================================================
# INITIALIZATION SCRIPT
# ============================================================

async def init_neo4j_indexes(driver):
    """
    Initialize Neo4j with all required indexes.
    
    This should be called once during system initialization.
    
    Usage:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(uri, auth=(user, pass))
        await init_neo4j_indexes(driver)
    """
    async with driver.session() as session:
        logger.info(f"Creating {len(INDEXES)} indexes...")
        results = await create_indexes(session)
        
        logger.info(f"""
        Index Creation Results:
        ✓ Created: {len(results['created'])} indexes
        ⊕ Skipped: {len(results['skipped'])} indexes (already exist)
        ✗ Failed: {len(results['failed'])} indexes
        """)
        
        if results["failed"]:
            logger.warning("Failed index creations:")
            for failed in results["failed"]:
                logger.warning(f"  - {failed['name']}: {failed['error']}")
        
        return results


# ============================================================
# QUERY OPTIMIZATION UTILITIES
# ============================================================

def optimize_graph_query(cypher: str) -> str:
    """
    Apply optimization rules to Cypher queries.
    
    Optimization strategies:
    1. Move filters as early as possible (WHERE before MATCH when possible)
    2. Use indexed properties in WHERE clauses
    3. Combine multiple predicates efficiently
    4. Use USING SCAN hints when appropriate
    """
    # This is a placeholder for query optimization
    # Real implementation would use Cypher AST analysis
    return cypher


# ============================================================
# EXAMPLE USAGE
# ============================================================

def example_usage():
    """Example of how to use index management"""
    
    async def main():
        from neo4j import AsyncGraphDatabase
        
        # Connect to Neo4j
        driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        
        try:
            # Initialize indexes
            results = await init_neo4j_indexes(driver)
            logger.info(f"Initialization complete")
            
            # Check index status
            async with driver.session() as session:
                status = await get_index_status(session)
                logger.info(f"Current indexes: {len(status)}")
        
        finally:
            await driver.close()
    
    # Run: asyncio.run(main())
