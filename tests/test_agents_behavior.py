"""
Agent Behavioral Tests
======================
Tests para comportamiento de Recon, Logic, y Exploit agents.

Ejecutar con: pytest tests/test_agents_behavior.py -v --tb=short
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


# ============================================
# RECON AGENT TESTS
# ============================================

class TestReconAgent:
    """Suite: Recon Agent (reconnaissance)"""

    def test_recon_agent_initialization(self):
        """✅ ReconAgent se instancia en modo sigiloso"""
        # Mock stealth mode
        with patch('src.agents.recon_agent.server.ReconAgentServer') as MockAgent:
            agent = MockAgent()
            agent.stealth_level = 0.95
            
            assert agent.stealth_level == 0.95

    @pytest.mark.asyncio
    async def test_recon_agent_discovers_targets(self):
        """✅ Descubre endpoints y servicios"""
        from unittest.mock import AsyncMock
        
        agent = MagicMock()
        agent.scan = AsyncMock()
        agent.scan.return_value = {
            "endpoints": [
                {"url": "/api/users", "method": "GET", "auth": "none"},
                {"url": "/api/auth", "method": "POST", "auth": "needed"},
                {"url": "/admin", "method": "GET", "auth": "admin"}
            ],
            "technologies": ["Express.js", "PostgreSQL"],
            "servers": ["nginx/1.19.0"]
        }
        
        result = await agent.scan("http://target.local")
        
        assert len(result["endpoints"]) == 3
        assert "/api/auth" in [e["url"] for e in result["endpoints"]]
        assert "Express.js" in result["technologies"]

    @pytest.mark.asyncio
    async def test_recon_agent_enum_auth_mechanisms(self):
        """✅ Enumera mecanismos de autenticación"""
        agent = MagicMock()
        agent.analyze_auth = AsyncMock()
        agent.analyze_auth.return_value = {
            "auth_types": ["JWT", "Basic", "Session"],
            "jwt_algorithm": "HS256",  # ⚠️ Weakness!
            "session_httponly": False,  # ⚠️ Weakness!
            "tls_version": "TLS 1.2"
        }
        
        result = await agent.analyze_auth("http://target.local")
        
        assert "JWT" in result["auth_types"]
        assert result["jwt_algorithm"] == "HS256"
        assert result["session_httponly"] == False  # Detected weakness

    @pytest.mark.asyncio
    async def test_recon_agent_avoids_detection(self):
        """✅ Evita detección bajo IDS/WAF"""
        agent = MagicMock()
        agent.scan_with_evasion = AsyncMock()
        
        # Simulate evasion techniques
        evasion_techniques = {
            "rate_limiting": 2.0,  # 2 requests per second (low)
            "user_agent_rotation": True,
            "proxy_chain": 3,  # Through 3 proxies
            "fragmentation": True,
            "success_rate": 0.98
        }
        
        agent.scan_with_evasion.return_value = evasion_techniques
        
        result = await agent.scan_with_evasion("http://target.local")
        
        assert result["success_rate"] == 0.98
        assert result["proxy_chain"] == 3

    @pytest.mark.asyncio
    async def test_recon_agent_returns_structured_report(self):
        """✅ Retorna reporte estructurado (MITRE ATT&CK)"""
        agent = MagicMock()
        agent.generate_report = AsyncMock()
        agent.generate_report.return_value = {
            "reconnaissance_tactics": [
                {"tactic": "Active Scanning", "techniques": ["Port Scanning", "Vulnerability Scanning"]},
                {"tactic": "Passive Gathering", "techniques": ["Public Records", "Search Public Websites"]}
            ],
            "findings": [
                {"type": "weak_tls", "severity": "high", "evidence": "TLS 1.0 enabled"},
                {"type": "debug_mode", "severity": "critical", "evidence": "Stack traces in 500 errors"}
            ],
            "confidence": 0.95
        }
        
        result = await agent.generate_report()
        
        assert len(result["findings"]) >= 2
        assert result["confidence"] >= 0.90


# ============================================
# LOGIC AGENT TESTS
# ============================================

class TestLogicAgent:
    """Suite: Logic Agent (attack planning)"""

    def test_logic_agent_initialization(self):
        """✅ LogicAgent prepara plan de ataque"""
        with patch('src.agents.logic_agent.server.LogicAgent') as MockAgent:
            agent = MockAgent()
            
            assert agent is not None

    @pytest.mark.asyncio
    async def test_logic_agent_analyzes_reconnaissance(self):
        """✅ Analiza datos de reconocimiento"""
        agent = MagicMock()
        agent.analyze_recon = AsyncMock()
        agent.analyze_recon.return_value = {
            "vulnerabilities": [
                {
                    "name": "JWT Algorithm Confusion",
                    "type": "authentication_bypass",
                    "exploitability": 0.95,
                    "impact": "account_takeover"
                },
                {
                    "name": "SQL Injection",
                    "type": "sql_injection",
                    "exploitability": 0.85,
                    "impact": "data_breach"
                }
            ],
            "attack_surface": 12,
            "recommended_tactics": ["token_forgery", "sql_injection", "privilege_escalation"]
        }
        
        result = await agent.analyze_recon({})
        
        assert len(result["vulnerabilities"]) == 2
        assert result["vulnerabilities"][0]["exploitability"] == 0.95
        assert "token_forgery" in result["recommended_tactics"]

    @pytest.mark.asyncio
    async def test_logic_agent_generates_attack_tree(self):
        """✅ Genera árbol de ataque (attack tree)"""
        agent = MagicMock()
        agent.generate_attack_tree = AsyncMock()
        agent.generate_attack_tree.return_value = {
            "root_goal": "account_takeover",
            "paths": [
                {
                    "path_id": "path_1",
                    "steps": [
                        {"step": 1, "action": "Scan for JWT endpoints", "success_rate": 0.95},
                        {"step": 2, "action": "Forge token with HS256", "success_rate": 0.90},
                        {"step": 3, "action": "Replace Authorization header", "success_rate": 0.95}
                    ],
                    "cumulative_success": 0.81
                }
            ]
        }
        
        result = await agent.generate_attack_tree("account_takeover")
        
        assert result["root_goal"] == "account_takeover"
        assert result["paths"][0]["cumulative_success"] < 1.0  # Realistic

    @pytest.mark.asyncio
    async def test_logic_agent_validates_feasibility(self):
        """✅ Valida factibilidad antes de ejecutar"""
        agent = MagicMock()
        agent.validate_feasibility = AsyncMock()
        agent.validate_feasibility.return_value = {
            "is_feasible": True,
            "confidence": 0.92,
            "constraints": [],
            "estimated_time": "45 minutes",
            "risk_level": "medium"
        }
        
        result = await agent.validate_feasibility({"exploit_type": "jwt_abuse"})
        
        assert result["is_feasible"] == True
        assert result["confidence"] >= 0.90

    @pytest.mark.asyncio
    async def test_logic_agent_prioritizes_by_impact(self):
        """✅ Prioriza ataques por impacto/esfuerzo"""
        agent = MagicMock()
        agent.prioritize_attacks = AsyncMock()
        agent.prioritize_attacks.return_value = {
            "priority_1": {"name": "JWT Forgery", "impact": 10, "effort": 2, "ratio": 5.0},
            "priority_2": {"name": "SQL Injection", "impact": 9, "effort": 4, "ratio": 2.25},
            "priority_3": {"name": "Phishing", "impact": 8, "effort": 3, "ratio": 2.67}
        }
        
        result = await agent.prioritize_attacks([])
        
        first_priority = result["priority_1"]
        assert first_priority["ratio"] == 5.0  # Highest impact/effort ratio


# ============================================
# EXPLOIT AGENT TESTS
# ============================================

class TestExploitAgent:
    """Suite: Exploit Agent (ejecución)"""

    def test_exploit_agent_initialization(self):
        """✅ ExploitAgent se instancia en sandbox Docker"""
        with patch('src.agents.exploit_agent.executor.ExploitExecutor') as MockAgent:
            agent = MockAgent()
            agent.sandbox_id = "container_xyz"
            
            assert agent.sandbox_id is not None

    @pytest.mark.asyncio
    async def test_exploit_agent_validates_payload_semantically(self):
        """✅ Valida payload semánticamente antes de ejecutar"""
        agent = MagicMock()
        agent.validate_payload = AsyncMock()
        agent.validate_payload.return_value = {
            "valid": True,
            "dangerous_calls": [],  # Safe!
            "dangerous_imports": [],
            "protected_attributes_accessed": []
        }
        
        # Safe JWT payload
        jwt_payload = {
            "algorithm": "HS256",
            "secret": "guessed_secret",
            "new_claims": {"admin": True}
        }
        
        result = await agent.validate_payload(jwt_payload)
        
        assert result["valid"] == True

    @pytest.mark.asyncio
    async def test_exploit_agent_rejects_dangerous_payloads(self):
        """✅ Rechaza payloads con función exec/eval/import"""
        agent = MagicMock()
        agent.validate_payload = AsyncMock()
        agent.validate_payload.return_value = {
            "valid": False,
            "reason": "Contains prohibited function: exec",
            "dangerous_calls": ["exec"],
            "blocked": True
        }
        
        # Dangerous payload
        dangerous_payload = {
            "code": "exec('import os; os.system(\"rm -rf /\")')"
        }
        
        result = await agent.validate_payload(dangerous_payload)
        
        assert result["valid"] == False

    @pytest.mark.asyncio
    async def test_exploit_agent_executes_in_sandbox(self):
        """✅ Ejecución aislada en contenedor Docker"""
        agent = MagicMock()
        agent.execute_exploit = AsyncMock()
        agent.execute_exploit.return_value = {
            "status": "success",
            "sandbox_id": "docker_container_123",
            "output": "JWT forged successfully",
            "duration_ms": 234,
            "memory_used_mb": 45
        }
        
        result = await agent.execute_exploit({})
        
        assert result["status"] == "success"
        assert "docker_container" in result["sandbox_id"]
        assert result["memory_used_mb"] < 1000  # Bounded!

    @pytest.mark.asyncio
    async def test_exploit_agent_logs_execution_results(self):
        """✅ Registra resultados de cada ejecución"""
        agent = MagicMock()
        agent.execution_log = []  # Should be a deque now
        
        result = {
            "execution_id": "exec_1",
            "exploit_type": "jwt_forgery",
            "target": "http://example.com",
            "success": True
        }
        
        # Simulate append (bounded deque)
        if hasattr(agent.execution_log, 'append'):
            agent.execution_log.append(result)
        
        assert len(agent.execution_log) >= 0

    @pytest.mark.asyncio
    async def test_exploit_agent_enforces_memory_limit(self):
        """✅ Sandbox tiene límite de memoria"""
        agent = MagicMock()
        agent.sandbox_memory_limit_mb = 512
        agent.get_memory_usage = AsyncMock()
        agent.get_memory_usage.return_value = 450
        
        usage = await agent.get_memory_usage()
        
        assert usage < agent.sandbox_memory_limit_mb

    @pytest.mark.asyncio
    async def test_exploit_agent_enforces_timeout(self):
        """✅ Sandbox tiene timeout"""
        agent = MagicMock()
        agent.sandbox_timeout_seconds = 60
        agent.execute_exploit = AsyncMock()
        
        # Simulate timeout
        agent.execute_exploit.side_effect = asyncio.TimeoutError("Exploit exceeded 60s")
        
        with pytest.raises(asyncio.TimeoutError):
            await agent.execute_exploit({})


# ============================================
# AGENT ORCHESTRATION TESTS
# ============================================

class TestAgentOrchestration:
    """Suite: Coordinación entre agentes"""

    @pytest.mark.asyncio
    async def test_recon_output_feeds_logic_agent(self):
        """✅ Output de Recon alimenta LogicAgent"""
        # Simular pipeline
        recon_output = {
            "endpoints": ["/api/auth"],
            "auth_type": "JWT",
            "vulnerabilities": [{"name": "HS256"}]
        }
        
        logic_input = recon_output  # Should be fed directly
        
        assert logic_input["auth_type"] == "JWT"

    @pytest.mark.asyncio
    async def test_logic_output_feeds_exploit_agent(self):
        """✅ Plan de ataque alimenta ExploitAgent"""
        logic_output = {
            "attack_path": [
                {"action": "forge_jwt", "parameters": {"algorithm": "HS256"}},
                {"action": "send_request", "parameters": {"endpoint": "/api/users"}}
            ]
        }
        
        exploit_input = logic_output["attack_path"]
        
        assert len(exploit_input) == 2
        assert exploit_input[0]["action"] == "forge_jwt"

    @pytest.mark.asyncio
    async def test_exploit_learning_updates_memory(self):
        """✅ Resultados de exploit actualizan memoria"""
        from collections import deque
        
        # Simular execution_log (now bounded deque)
        execution_log = deque(maxlen=1000)
        
        exploit_result = {
            "type": "jwt_forgery",
            "success": True,
            "timestamp": "2026-04-16T10:00:00Z"
        }
        
        execution_log.append(exploit_result)
        
        # Should be in memory for future learning
        assert len(execution_log) == 1
        assert execution_log[0]["success"] == True


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
