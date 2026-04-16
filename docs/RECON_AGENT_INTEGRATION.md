# ReconAgent Integration Guide

**Documento:** Integración completa de recon_agent con orchestrator v1.2.0  
**Fecha:** 2026-01-15  
**Estado:** Ready for Phase 2

---

## 1. Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (v1.2.0)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  server.py (MCP Router)                              │   │
│  │  - Load .mcp.json config                             │   │
│  │  - Register 7 agents                                 │   │
│  │  - Coordinate lifecycle                              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  supervisor.py (Security Validation)                │   │
│  │  - Whitelist check (CVE-2026-2256)                   │   │
│  │  - Veil dropping detection                           │   │
│  │  - Trust scoring (0.0-1.0)                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  planner.py (Attack Planning)                        │   │
│  │  - Generate 3-7 step plans                           │   │
│  │  - Delegate to agents (recon → logic → exploit)     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  memory_manager.py (Persistence)                     │   │
│  │  - Log reasoning traces                              │   │
│  │  - Flush on graceful shutdown                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
    ↓ MCP Protocol
┌─────────────────────────────────────────────────────────────┐
│                   RECON_AGENT (v1.0.0) ✅                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  server.py (Tool Registry)                           │   │
│  │  - 15 tools registered                               │   │
│  │  - Tool invocation wrapper (async)                   │   │
│  │  - Result accumulation per target                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Specialized Modules                                 │   │
│  │  ├─ js_analyzer.py (340 lines)                       │   │
│  │  ├─ graphql_mapper.py (280 lines)                    │   │
│  │  ├─ network_tools.py (310 lines)                     │   │
│  │  └─ prompts.yaml (250 lines)                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                   LOGIC_AGENT (Planned)                      │
│  - Analyzes recon findings                                  │
│  - Plans attack scenarios                                   │
│  - Identifies high-impact vectors                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                   EXPLOIT_AGENT (Planned)                    │
│  - Execute in Docker sandbox                                │
│  - Dynamic testing                                          │
│  - Validate findings                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Comunicación MCP

### 2.1 Tool Invocation Protocol

```python
# From orchestrator/planner.py
step = {
    "number": 1,
    "agent": "recon_agent",
    "objective": "Extract JavaScript from target",
    "tool": "extract_javascript_files",
    "parameters": {
        "url": "https://target.com",
        "aggressive": False
    }
}

# Orchestrator calls:
# recon_agent_server.invoke_tool("extract_javascript_files", url="...", aggressive=False)

# recon_agent/server.py receives:
async def invoke_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Receive tool invocation from orchestrator (MCP).
    
    Args:
        tool_name: "extract_javascript_files"
        **kwargs: {"url": "...", "aggressive": False}
    
    Returns:
        {"status": "success", "tool": "extract_javascript_files", "result": {...}}
    """
    tool_definition = self.tools[tool_name]
    result = await tool_definition["function"](**kwargs)
    
    # Accumulate in reconnaissance_results
    target = kwargs.get("url", kwargs.get("endpoint", "unknown"))
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
```

---

## 3. Datos Entre Agentes

### 3.1 ReconAgent Output → LogicAgent Input

```json
# recon_agent returns (via get_reconnaissance_results):
{
    "target": "https://target.com",
    "reconnaissance": {
        "infrastructure": {
            "subdomains": ["api.target.com", "admin.target.com", "db.target.com"],
            "ports": [80, 443, 27017],
            "services": ["http", "https", "mongodb"]
        },
        "APIs": {
            "graphql_endpoints": [
                {"endpoint": "/api/graphql", "introspection_available": true}
            ],
            "javascript_apis": [
                {"endpoint": "/api/users", "method": "GET"},
                {"endpoint": "/api/admin/settings", "method": "POST", "auth_bypass": true}
            ]
        },
        "vulnerabilities": {
            "xss_sinks": [
                {"file": "main.js", "location": 245, "severity": "high"},
                {"file": "api.chunk.js", "location": 512, "severity": "medium"}
            ],
            "exposed_credentials": [
                {"type": "AWS_KEY", "severity": "critical", "location": "assets/config.js"}
            ],
            "graphql_bypasses": [
                {"type": "unauthorized_query", "severity": "critical"},
                {"type": "alias_overloading", "severity": "high"}
            ]
        },
        "headers_analysis": {
            "missing_headers": ["X-Content-Type-Options", "Referrer-Policy"],
            "risk_level": "high"
        }
    }
}

# logic_agent consumes:
# "¿Qué vectores de ataque son viables dado este reconocimiento?"
# Respuesta: Plan con 3-7 pasos que aprovecha vulnerabilidades descubiertas
```

---

## 4. Configuration (.mcp.json Integration)

### 4.1 ReconAgent Entry in .mcp.json

```json
{
    "agents": [
        {
            "id": "recon_agent",
            "name": "Reconnaissance Agent",
            "version": "1.0.0",
            "capabilities": ["passive_reconnaissance", "osint"],
            "module": "src.agents.recon_agent.server.ReconAgentServer",
            "tools": 15,
            "requires_sandbox": false,
            "requires_authentication": false,
            "rate_limits": {
                "requests_per_minute": 60,
                "tools_per_request": 5
            }
        }
    ]
}
```

### 4.2 Security Policy for ReconAgent

```json
{
    "agents": {
        "recon_agent": {
            "allowed_operations": [
                "dns_query",
                "http_request",
                "javascript_parsing",
                "graphql_introspection"
            ],
            "blocked_operations": [
                "code_execution",
                "file_modification",
                "service_termination",
                "credential_usage"
            ],
            "data_handling": {
                "encrypt_at_rest": true,
                "retention_days": 90,
                "anonymize_pii": true
            }
        }
    }
}
```

---

## 5. Tool Registration and Discovery

### 5.1 Dynamic Tool Registry

```python
# recon_agent/server.py
class ReconAgentServer:
    def _register_tools(self) -> None:
        """Register 15 tools dynamically."""
        
        self.tools = {
            # JavaScript Analysis (4)
            "extract_javascript_files": {
                "function": self.js_analyzer.extract_javascript_files,
                "description": "Extract .js/.mjs/.chunk.js files",
                "parameters": {
                    "url": {"type": "string", "required": True},
                    "aggressive": {"type": "boolean", "default": False}
                },
                "category": "javascript"
            },
            # ... 14 more tools
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return metadata for orchestrator."""
        return {
            "agent_name": "recon_agent",
            "version": "1.0.0",
            "tools_available": list(self.tools.keys()),
            "tools_count": len(self.tools),
            "categories": ["javascript", "graphql", "network"],
            "passive_only": True,
            "requires_credentials": False
        }
```

### 5.2 Orchestrator Discovery

```python
# orchestrator/server.py
async def discover_agents(self) -> Dict[str, List[str]]:
    """Discover all registered agents and their tools."""
    agents = {}
    
    for agent_id, agent_config in self.mcp_config["agents"].items():
        agent_server = await self._load_agent(agent_id)
        capabilities = agent_server.get_capabilities()
        agents[agent_id] = capabilities["tools_available"]
    
    return agents
    # Returns:
    # {
    #   "recon_agent": [15 tools...],
    #   "logic_agent": [planned...],
    #   "exploit_agent": [planned...]
    # }
```

---

## 6. Execution Flow Example

### 6.1 Complete Reconnaissance Plan

```
User Input:
"Realiza reconocimiento en https://example-bank.com"

Orchestrator Flow:
├─ supervisor.validate_request()
│  ├─ Check authorization ✓
│  ├─ Check blocked operations (recon is safe) ✓
│  ├─ Check veil dropping patterns ✓
│  └─ Trust score: 1.0 ✓
│
├─ planner.generate_attack_plan()
│  └─ Returns: [
│     {
│       "number": 1,
│       "agent": "recon_agent",
│       "tool": "extract_javascript_files",
│       "parameters": {"url": "https://example-bank.com", "aggressive": false},
│       "expected_output": "List of JS files with metadata"
│     },
│     {
│       "number": 2,
│       "agent": "recon_agent",
│       "tool": "extract_shadow_apis",
│       "parameters": {"code": "<JS content from step 1>"},
│       "expected_output": "Hidden APIs, credentials, dev comments"
│     },
│     {
│       "number": 3,
│       "agent": "recon_agent",
│       "tool": "discover_graphql_endpoints",
│       "parameters": {"url": "https://example-bank.com"},
│       "expected_output": "GraphQL endpoints found"
│     },
│     ... (4-5 more steps)
│    ]
│
├─ Step 1 Execution:
│  ├─ supervisor.validate_step() → whitelist check → ALLOWED
│  ├─ recon_agent.invoke_tool("extract_javascript_files", ...)
│  │  ├─ server.py.invoke_tool()
│  │  ├─ js_analyzer.extract_javascript_files()
│  │  │  └─ Download files from CDN → Parse manifest
│  │  └─ return {result: [files]}
│  └─ memory_manager.log_reasoning_trace(step=1, outcome="success")
│
├─ Step 2 Execution:
│  ├─ recon_agent.invoke_tool("extract_shadow_apis", ...)
│  │  ├─ js_analyzer.extract_shadow_apis()
│  │  │  ├─ Find endpoints: /api/transfers, /api/accounts
│  │  │  ├─ Find credentials: AWS_SECRET in config chunk
│  │  │  ├─ Find comments: "TODO: Validate JWT properly"
│  │  │  └─ Find vulnerabilities: XSS in DOM parser
│  │  └─ return {endpoints: [...], credentials: [...], risks: [...]}
│  └─ Accumulate results
│
├─ ... (Steps 3-5 continue)
│
└─ Consolidation:
   ├─ get_reconnaissance_results("example-bank.com")
   ├─ memory_manager.get_reasoning_history()
   ├─ Generate executive summary
   └─ Pass to logic_agent for next phase
```

---

## 7. Prompts Integration

### 7.1 How prompts.yaml Guides AI Analysis

```python
# During extract_shadow_apis, AI gets context from prompts.yaml:
system_context = """
Extract "Shadow APIs" - funcionalidades ocultas en JavaScript:
1. Endpoints internos (ej: /api/__debug__, /admin/telemetry)
2. Credenciales: AWS keys, JWT tokens, API keys
3. Rutas de configuración: URLs de bases de datos, servicios internos
4. Código comercialmente sensible (lógica de precios, algoritmos)

Severidad: CRÍTICA si encontrado credenciales activas
"""

# Modelo recibe:
# - Code to analyze
# - System prompt from prompts.yaml
# - Previous results from other tools
# Result: High-quality, consistent shadow API extraction
```

---

## 8. Memory Persistence

### 8.1 ReconAgent Results → Memory Manager

```python
# After all recon tools execute:
reconnaissance_data = recon_agent.get_reconnaissance_results("target.com")

# memory_manager persists:
memory_manager.log_reasoning_trace(
    operation_id="recon_2026_01_15_001",
    steps=[
        {
            "step": 1,
            "agent": "recon_agent",
            "tool": "extract_javascript_files",
            "decision": "Download all JS from CDN",
            "outcome": "found 12 files",
            "reasoning": "Files contain business logic and potential APIs"
        },
        {
            "step": 2,
            "agent": "recon_agent",
            "tool": "extract_shadow_apis",
            "decision": "Search for dev comments and credentials",
            "outcome": "Found AWS_SECRET, TODO comments",
            "reasoning": "Shadow APIs are excellent attack surface"
        },
        # ... more steps
    ]
)

# Later retrieval:
history = memory_manager.get_reasoning_history("recon_2026_01_15_001")
# logic_agent uses history to understand why reconnaissance was done this way
```

---

## 9. Security Boundaries

### 9.1 ReconAgent Sandbox

```
┌──────────────────────────────────────────┐
│  ReconAgent (PASSIVE ONLY)               │
├──────────────────────────────────────────┤
│ ✅ ALLOWED:                              │
│   - DNS queries                          │
│   - HTTP GET/HEAD requests               │
│   - JavaScript parsing                   │
│   - GraphQL introspection queries        │
│   - Passive data analysis                │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│  ORCHESTRATOR VALIDATION                 │
├──────────────────────────────────────────┤
│ - supervisor.validate_step()             │
│ - Whitelist check (no active attacks)    │
│ - Trust scoring (behavioral analysis)    │
│ - Veil dropping detection                │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│  LogicAgent (PLANNING ONLY)              │
│  - Analyze recon findings               │
│  - Plan attack scenarios                │
│  - **Cannot execute yet**               │
└──────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────┐
│  ExploitAgent (SANDBOXED EXECUTION)      │
│  - Docker container only                │
│  - Metrics collected                     │
│  - No access to host                     │
└──────────────────────────────────────────┘
```

---

## 10. Validation Checklist

- [x] ReconAgent module created (5 files)
- [x] 15 tools registered and functional
- [x] Async/await patterns implemented
- [x] Result accumulation working
- [x] Prompts versioned (v1.0.0)
- [x] Security guidelines in place
- [x] Integration points documented
- [x] Memory manager ready
- [ ] End-to-end test (recon → logic → exploit)
- [ ] Logic agent implementation
- [ ] Exploit agent implementation
- [ ] Neo4j temporal knowledge graph integration
- [ ] Automated security audit

---

## 11. Phase 2 Requirements

### LogicAgent
- Analyze recon findings
- Plan 3-7 step attack scenarios
- Identify high-impact vectors
- Reason about exploitation feasibility

### ExploitAgent
- Execute in Docker sandbox
- Dynamic testing and validation
- Metrics collection
- Proof-of-concept generation

### Knowledge Graph Integration
- Neo4j with Graphiti temporal awareness
- Store relationships between findings
- Enable cross-operation learning
- Detect patterns across targets

---

**Integration Status:** ✅ COMPLETE  
**Next Phase:** Logic Agent (2026-01-20)  
**Document Version:** 1.0.0
