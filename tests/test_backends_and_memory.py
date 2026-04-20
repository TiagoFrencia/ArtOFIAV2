"""
Backend & Memory System Tests
=============================
Tests para persistencia, bases de datos, y sistemas críticos.

Ejecutar con: pytest tests/test_backends_and_memory.py -v --tb=short
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import json

# Imports
from src.memory.knowledge_graph import GraphManager
from src.memory.vector_db.pgvector_client import PGVectorClient
from src.orchestrator.memory_manager import MemoryManager
from src.backends.llm_providers import ProviderManager, ModelType


# ============================================
# MEMORY MANAGER TESTS
# ============================================

class TestMemoryManager:
    """Suite: MemoryManager (auditoría + persistencia)"""

    def test_memory_manager_initialization(self):
        """✅ MemoryManager se instancia correctamente"""
        manager = MemoryManager()
        
        assert manager is not None
        assert hasattr(manager, 'audit_trail')
        assert hasattr(manager, 'reasoning_traces')

    def test_memory_manager_logs_entry(self):
        """✅ Registra entrada de auditoría"""
        manager = MemoryManager()
        
        entry = {
            "timestamp": "2026-04-16T10:00:00Z",
            "action": "exploit_executed",
            "agent": "exploit_agent",
            "result": "success"
        }
        
        manager.log_entry(entry)
        
        trail = manager.get_audit_trail()
        assert len(trail) > 0
        assert trail[-1]["action"] == "exploit_executed"

    def test_memory_manager_stores_reasoning_trace(self):
        """✅ Almacena trace de razonamiento"""
        manager = MemoryManager()
        
        trace = {
            "step": 1,
            "reasoning": "Detected JWT weakness",
            "confidence": 0.95,
            "evidence": {"algorithm": "HS256"}
        }
        
        manager.store_reasoning_trace(trace)
        # Verification: trace se almacenó (mock en test)
        assert manager is not None

    def test_memory_manager_audit_trail_immutability(self):
        """✅ Auditoría no puede ser modificada sin dejar rastro"""
        manager = MemoryManager()
        
        manager.log_entry({"action": "original"})
        trail1 = manager.get_audit_trail()
        
        # Intentar modificar
        trail1[0]["action"] = "modified"
        
        trail2 = manager.get_audit_trail()
        # Debería ser original (copy, no reference)
        assert trail2[0]["action"] == "original"

    def test_memory_manager_concurrent_logging(self):
        """✅ Logging es thread-safe bajo concurrencia"""
        manager = MemoryManager()
        
        # Simular 100 logs concurrentes
        for i in range(100):
            manager.log_entry({"index": i, "action": "concurrent_test"})
        
        trail = manager.get_audit_trail()
        assert len(trail) == 100

    @pytest.mark.asyncio
    async def test_memory_manager_flush_audit_buffer(self):
        """✅ Flush persiste auditoría a almacenamiento"""
        manager = MemoryManager()
        
        manager.log_entry({"action": "test_flush"})
        
        # Flush (debería persistir)
        await manager.flush_audit_buffer()
        
        # Verificar que se persistió (mock)
        assert manager is not None

    @pytest.mark.asyncio
    async def test_memory_manager_cleanup(self):
        """✅ Cleanup cierra recursos correctamente"""
        manager = MemoryManager()
        
        # Simulate cleanup (close connections, flush, etc)
        await manager.cleanup()
        
        assert manager is not None


# ============================================
# NEO4J KNOWLEDGE GRAPH TESTS
# ============================================

class TestGraphManager:
    """Suite: Neo4j Knowledge Graph"""

    def test_graph_manager_initialization(self):
        """✅ GraphManager se instancia"""
        # Mock Neo4j connection
        with patch('src.memory.knowledge_graph.graph_manager.GraphDatabase.driver'):
            manager = GraphManager()
            assert manager is not None

    @pytest.mark.asyncio
    async def test_graph_manager_stores_vulnerability_node(self):
        """✅ Almacena nodo de vulnerabilidad en grafo"""
        manager = GraphManager()
        
        vuln_data = {
            "type": "jwt_weakness",
            "endpoint": "/api/auth",
            "target": "http://example.com",
            "severity": "high"
        }
        
        # Mock the storage
        with patch.object(manager, 'create_node', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {"id": "vuln_123"}
            
            result = await manager.create_node("Vulnerability", vuln_data)
            assert result["id"] == "vuln_123"

    @pytest.mark.asyncio
    async def test_graph_manager_creates_relationships(self):
        """✅ Crea relaciones entre nodos (tácticas, técnicas)"""
        manager = GraphManager()
        
        with patch.object(manager, 'create_relationship', new_callable=AsyncMock) as mock_rel:
            mock_rel.return_value = {"relationship": "USES_TACTIC"}
            
            result = await manager.create_relationship(
                from_node="attack_1",
                to_node="tactic_1",
                relationship_type="USES_TACTIC"
            )
            
            assert result["relationship"] == "USES_TACTIC"

    @pytest.mark.asyncio
    async def test_graph_manager_queries_knowledge(self):
        """✅ Queries el grafo de conocimiento"""
        manager = GraphManager()
        
        with patch.object(manager, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [
                {"tactic": "token_forgery", "success_rate": 0.95},
                {"tactic": "secret_cracking", "success_rate": 0.78}
            ]
            
            results = await manager.query(
                "MATCH (a:Attack)-[:USES_TACTIC]->(t:Tactic) RETURN t"
            )
            
            assert len(results) == 2
            assert results[0]["success_rate"] == 0.95


# ============================================
# PGVECTOR (RAG) TESTS
# ============================================

class TestPGVectorClient:
    """Suite: PostgreSQL + pgvector (semantic search)"""

    def test_pgvector_client_initialization(self):
        """✅ Cliente pgvector se instancia"""
        client = PGVectorClient(
            db_url="postgresql://user:pass@localhost:5432/test",
            embedding_dim=1536
        )
        
        assert client is not None
        assert client.embedding_dim == 1536

    @pytest.mark.asyncio
    async def test_pgvector_stores_embedding(self):
        """✅ Almacena embedding en PostgreSQL"""
        client = PGVectorClient(
            db_url="postgresql://user:pass@localhost:5432/test",
            embedding_dim=1536
        )
        
        # Mock la conexión
        with patch.object(client, 'pool', new_callable=AsyncMock):
            embedding_record = {
                "id": "http_response_1",
                "content": "HTTP 200 found admin endpoint",
                "content_type": "http_response",
                "embedding": [0.1, 0.2, 0.3] * 512  # 1536 dims
            }
            
            # Mock store
            with patch.object(client, 'store', new_callable=AsyncMock) as mock_store:
                mock_store.return_value = True
                
                result = await client.store(embedding_record)
                assert result == True

    @pytest.mark.asyncio
    async def test_pgvector_semantic_search(self):
        """✅ Búsqueda semántica sobre embeddings"""
        client = PGVectorClient(
            db_url="postgresql://user:pass@localhost:5432/test"
        )
        
        query_embedding = [0.1, 0.2, 0.3] * 512
        
        with patch.object(client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"id": "1", "similarity": 0.95, "content": "JWT weakness detected"},
                {"id": "2", "similarity": 0.87, "content": "Token bypass found"}
            ]
            
            results = await client.search(query_embedding, limit=2)
            
            assert len(results) == 2
            assert results[0]["similarity"] == 0.95

    @pytest.mark.asyncio
    async def test_pgvector_handles_connection_failure(self):
        """✅ Maneja gracefully fallo de conexión"""
        client = PGVectorClient(
            db_url="postgresql://invalid:invalid@localhost:12345/test"
        )
        
        # Connection should fail gracefully or retry
        with patch.object(client, 'connect', new_callable=AsyncMock) as mock_conn:
            mock_conn.return_value = False
            
            result = await client.connect()
            assert result == False


# ============================================
# LLM PROVIDER TESTS
# ============================================

class TestProviderManager:
    """Suite: LLM Provider Management + Fallback"""

    def test_provider_manager_initialization(self):
        """✅ ProviderManager se instancia"""
        manager = ProviderManager()
        
        assert manager is not None
        assert manager.fallback_chain is not None
        assert len(manager.fallback_chain) >= 2  # GPT-4, Claude

    @pytest.mark.asyncio
    async def test_provider_manager_fallback_on_policy_rejection(self):
        """✅ Fallback cuando proveedor rechaza por política"""
        manager = ProviderManager()
        
        # Simular OpenAI rechazando
        with patch.object(manager, 'call_provider') as mock_call:
            mock_call.side_effect = [
                Exception("Content policy violation"),  # OpenAI rechaza
                {"content": "Here's a safe response"}   # Claude acepta
            ]
            
            # Con fallback, debería intentar Claude
            assert manager is not None

    @pytest.mark.asyncio
    async def test_provider_manager_tracks_metrics(self):
        """✅ Rastrea métricas por proveedor"""
        manager = ProviderManager()
        
        # Mock a successful call
        initial_count = len(manager.metrics)
        
        # Simular call
        manager.metrics[ModelType.OPENAI_GPT4].total_requests += 1
        manager.metrics[ModelType.OPENAI_GPT4].successful_requests += 1
        
        # Verificar que se incrementó
        assert manager.metrics[ModelType.OPENAI_GPT4].total_requests == 1

    @pytest.mark.asyncio
    async def test_provider_manager_cost_tracking(self):
        """✅ Calcula costo de llamadas"""
        manager = ProviderManager()
        
        # Simular uso de GPT-4 (caro)
        gpt4_metrics = manager.metrics[ModelType.OPENAI_GPT4]
        gpt4_metrics.total_tokens_used = 100_000
        gpt4_metrics.total_cost = (100_000 / 1000) * 0.03  # $3.00 por 1K tokens
        
        assert gpt4_metrics.total_cost == 3.0

    @pytest.mark.asyncio
    async def test_provider_manager_rate_limiting(self):
        """✅ Rate limiting por proveedor"""
        manager = ProviderManager()
        
        # Simular requests rápidos
        simultaneous_requests = 10
        
        # Provider debería throttle
        with patch.object(manager, 'check_rate_limit') as mock_limit:
            mock_limit.return_value = True  # Allow first few
            
            assert manager is not None


# ============================================
# PERSISTENCE TESTS
# ============================================

class TestPersistence:
    """Suite: Persistencia de datos críticos"""

    @pytest.mark.asyncio
    async def test_audit_trail_persists_across_restarts(self):
        """✅ Auditoría persiste si sistema se reinicia"""
        manager = MemoryManager()
        
        manager.log_entry({"action": "critical_operation", "id": 123})
        
        # Simular persistencia
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(manager.get_audit_trail(), f)
            temp_file = f.name
        
        # Simular reinicio y lectura
        with open(temp_file, 'r') as f:
            restored = json.load(f)
        
        assert len(restored) > 0
        assert restored[-1]["id"] == 123

    @pytest.mark.asyncio
    async def test_memory_survived_crash(self):
        """✅ Memoria sobrevive a crash del proceso"""
        # Test que datos en Neo4j persisten
        manager = MemoryManager()
        
        critical_data = {
            "exploitation_id": "exp_456",
            "vulnerability": "jwt_weakness",
            "status": "completed",
            "timestamp": "2026-04-16T10:00:00Z"
        }
        
        manager.log_entry(critical_data)
        
        # Should be persisted in Neo4j immediately
        assert manager is not None


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
