# 🏛️ System Architecture Overview

ArtOfIAV2 is a **3-layer autonomous red team system** with clear separation of concerns.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│  ORCHESTRATOR LAYER (Central Coordination)          │
│  - OrchestratorServer: Central control engine       │
│  - SecurityValidator: Deny-by-default enforcement   │
│  - AttackPlanner: Step-by-step path generation      │
│  - MemoryManager: Audit trail & persistence         │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼────┐ ┌─────▼────┐ ┌────▼──────┐
│  RECON     │ │  LOGIC   │ │ EXPLOIT   │
│  AGENT     │ │  AGENT   │ │ AGENT     │
├────────────┤ ├──────────┤ ├───────────┤
│- Network   │ │- Workflow│ │- Executor │
│- JS Parse  │ │- Auth    │ │- SQLi     │
│- GraphQL   │ │- Paths   │ │- XSS      │
│- Discovery │ │- PoC Gen │ │- SSTI     │
└────────────┘ └──────────┘ │- IDOR     │
                             │- SSRF     │
                             │- JWT      │
                             └───────────┘
        │            │            │
        └────────────┼────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  BACKEND LAYER (Infrastructure)                     │
│                                                      │
│  ┌──────────────┐  ┌──────────┐  ┌────────────┐   │
│  │   SANDBOX    │  │   LLM    │  │   CLOUD    │   │
│  │ docker_sand  │  │ providers│  │    AWS     │   │
│  ├──────────────┤  ├──────────┤  ├────────────┤   │
│  │ - Isolation  │  │ OpenAI   │  │ - EC2      │   │
│  │ - eBPF mon   │  │ Anthropic│  │ - IAM      │   │
│  │ - Execution  │  │ Ollama   │  │ - Lambda   │   │
│  │ - Cleanup    │  │ Fallback │  │            │   │
│  └──────────────┘  └──────────┘  └────────────┘   │
│         │                │              │           │
│         └────────────────┼──────────────┘           │
│                          │                         │
│  ┌──────────────────────▼──────────────────────┐  │
│  │     MEMORY SYSTEM (Persistence)             │  │
│  │  ┌──────────────┐    ┌──────────────────┐  │  │
│  │  │   Neo4j      │    │  PostgreSQL +    │  │  │
│  │  │  Knowledge   │    │  pgvector (RAG)  │  │  │
│  │  │   Graph      │    │  Embeddings      │  │  │
│  │  └──────────────┘    └──────────────────┘  │  │
│  └─────────────────────────────────────────────┘  │
│                          │                         │
│  ┌──────────────────────▼──────────────────────┐  │
│  │     LEARNING ENGINE (RL)                    │  │
│  │  - Episode recording                        │  │
│  │  - Outcome analysis                         │  │
│  │  - Strategy adaptation                      │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### 🎯 Orchestrator Layer (src/orchestrator/)

**Role:** Central coordination and security

- **OrchestratorServer** - Initialization, configuration, agent management
- **ConfigLoader** - Configuration loading from .mcp.json (NEW: extracted for SRP)
- **SecurityValidator** - Deny-by-default validation, rate limiting
- **AttackPlanner** - Generate 3-7 step attack chains
- **MemoryManager** - Audit logging, trace persistence

**Key Properties:**
- Immutable audit trail (integrity)
- Graceful shutdown with task cancellation
- Signal handler for SIGINT/SIGTERM

### 🕵️ Agent Layer (src/agents/)

**Role:** Specialized intelligence and execution

#### ReconAgent (src/agents/recon_agent/)
- Passive network scanning
- JavaScript decompilation & analysis
- GraphQL introspection
- Fingerprinting & discovery

#### LogicAgent (src/agents/logic_agent/)
- Workflow analysis
- Authentication bypass detection
- Post-exploitation planning
- Remediation suggestions

#### ExploitAgent (src/agents/exploit_agent/)
- Coordinates specialized attack modules
- Validates exploits before execution
- Records results to memory
- Sandbox lifecycle management

**Specialist Modules:**
- SQLiAgent - SQL injection
- XSSAgent - Cross-site scripting
- SSTIAgent - Server-side template injection
- IDORAgent - Insecure Direct Object References
- SSRFAgent - Server-side request forgery
- JWTServer - JWT cryptographic auditing

### ⚙️ Backend Layer (src/backends/)

**Role:** Infrastructure abstraction

#### Docker Sandbox (docker_sandbox/)
- Ephemeral container creation per exploit
- CPU/Memory/Time limits enforcement
- eBPF security monitoring
- Output capture via WebSocket
- Automatic cleanup

#### LLM Providers (llm_providers/)
- Provider abstraction (OpenAI, Claude, Ollama)
- Automatic fallback on policy rejection
- Token counting & cost tracking
- Rate limiting per provider

#### Cloud Infrastructure (cloud_infrastructure/)
- AWS EC2 automation
- IAM credential management
- Infrastructure-as-code patterns

### 💾 Memory System (src/memory/)

**Knowledge Graph (Neo4j)**
- Relationships between vulnerabilities
- Exploitation patterns
- Tactics and techniques

**Vector Database (PostgreSQL + pgvector)**
- Semantic search over responses
- Context summarization
- Episodic memory retrieval

**Intelligence Engine**
- RL-based strategy adaptation
- Learning from exploit outcomes
- Pattern recognition

---

## Data Flow: Typical Operation

```
Reconnaissance → Planning → Execution → Learning
     ↓              ↓            ↓            ↓
ReconAgent    LogicAgent   ExploitAgent  RL Engine
     │              │            │            │
     └──────────────┼────────────┼────────────┘
                    │            │
              Orchestrator    Memory System
                    │            │
              Audit Trail    Knowledge
```

### Example: JWT Weakness Exploitation

```python
# 1. RECONNAISSANCE
recon_findings = {
    "endpoint": "/api/auth",
    "jwt_detected": True,
    "algorithm": "HS256",
    "secret_strength": "weak"
}

# 2. PLANNING
plan = await logic_agent.analyze(recon_findings)
# Output: ["1. Capture JWT", "2. Crack secret", "3. Forge token", "4. Access admin"]

# 3. EXECUTION
result = await exploit_agent.exploit({
    "vulnerability": "jwt_weakness",
    "steps": plan
})
# Output: {"success": True, "admin_token": "..."}

# 4. LEARNING
await rl_engine.record_episode({
    "input": recon_findings,
    "output": result,
    "success": True
})
# Engine adapts strategy for future
```

---

## Security Model

### Deny-by-Default

All actions default to REJECTED unless explicitly whitelisted:

```python
class SecurityValidator:
    async def validate_action(self, action):
        if action not in WHITELIST:
            return False  # Default: REJECT
        else:
            return True
```

### Sandbox Isolation

Every exploit runs in a NEW ephemeral container:

- Read-only root filesystem
- Dropped capabilities: `CAP_ALL`
- seccomp filtering
- eBPF runtime monitoring
- No host access
- Auto cleanup

### Audit Trail

**Immutable centralized logging:**
- Every action logged
- Timestamps
- Reasoning traces
- Outcomes

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 3-layer architecture | Clean separation of concerns, testability |
| Deny-by-default | Security-first design |
| Neo4j + Vector DB | Dual memory (relationships + semantics) |
| Docker per exploit | Isolation, repeatability, auditability |
| LLM fallback chain | Resilience to API failures/censorship |
| Bounded collections (deque) | Prevent memory leaks in long-running systems |
| AST-based input validation | Robust against obfuscation |
| ConfigLoader extraction | Single Responsibility Principle |

---

## Scalability Considerations

**Current Limits:**
- Single Orchestrator instance (bottleneck)
- In-memory operation logs (1000 item deque)
- Exploit results cache (1000 item deque)

**Future Improvements:**
- Distributed Orchestrator (message queue)
- Horizontal scaling of agents
- Redis cluster for rate limiting
- Load balancing across LLM providers

---

## Next: Dive Deeper

- [Orchestrator Details](orchestrator.md)
- [Agent Architecture](agents.md)
- [Backend Infrastructure](backends.md)
- [Memory System](memory.md)

