# Code Structure Guide

**Location:** `src/`  
**Purpose:** Understanding how ArtOfIAV2 code is organized

---

## 📂 Directory Tree

```
src/
├── agents/                    # Autonomous agents (Recon, Logic, Exploit)
│   ├── recon_agent/          # Target reconnaissance & enumeration
│   │   ├── server.py         # Main recon orchestrator
│   │   ├── scanner.py        # Port/service scanning
│   │   ├── enumerator.py     # API/endpoint discovery
│   │   └── analyzer.py       # Weakness analysis
│   │
│   ├── logic_agent/          # Attack planning & reasoning
│   │   ├── server.py         # Main logic orchestrator
│   │   ├── planner.py        # Attack tree generation
│   │   ├── reasoner.py       # Feasibility analysis
│   │   └── prioritizer.py    # Attack prioritization
│   │
│   └── exploit_agent/        # Exploit execution (sandboxed)
│       ├── executor.py       # Execution orchestrator
│       ├── payloads/         # Payload templates
│       ├── post_exploitation/ # Post-exploit actions
│       └── learning/         # Capture successes/failures
│
├── backends/                 # External systems & services
│   ├── llm_providers/        # LLM integrations
│   │   ├── provider_manager.py # LLM provider fallback chain
│   │   ├── openai_provider.py  # OpenAI integration
│   │   ├── anthropic_provider.py # Claude integration
│   │   └── ollama_provider.py   # Local Ollama
│   │
│   ├── docker_sandbox/       # Sandbox for exploit execution
│   │   ├── sandbox_manager.py # Container lifecycle
│   │   ├── Dockerfile.ephemeral # Sandbox image
│   │   └── scripts/           # Sandbox utilities
│   │
│   └── memory_systems/       # Not yet here (see below)
│
├── core/                     # Core security & validation
│   ├── security_validator.py # Deny-by-default validation
│   ├── input_validator.py    # AST-based input validation
│   ├── audit_logger.py       # Immutable audit trails
│   └── encryption.py         # Secrets management
│
├── memory/                   # Persistent knowledge systems
│   ├── knowledge_graph.py    # Neo4j integration
│   ├── vector_db/           # PostgreSQL + pgvector
│   │   ├── pgvector_client.py # Vector DB client
│   │   └── migrations/       # Database migrations
│   └── retrieval/           # RAG & semantic search
│
├── evasion/                  # Evasion techniques
│   ├── browser_evasion.py   # Browser fingerprint evasion
│   ├── captcha_solver.py    # CAPTCHA bypass
│   ├── proxy_rotation.py    # Proxy management
│   └── rate_limiting.py     # Rate limit handling
│
├── orchestrator/             # Central orchestration
│   ├── server.py            # Main orchestrator (refactored!)
│   ├── config_loader.py     # Configuration management (NEW! SRP)
│   ├── supervisor.py        # Agent supervision
│   ├── backend_integration.py # Backend coordination
│   └── memory_manager.py    # Memory system manager
│
└── utils/                    # Utilities & helpers
    ├── logger.py            # Logging setup
    ├── decorators.py        # Common decorators
    ├── validators.py        # Input validation helpers
    └── converters.py        # Data conversion helpers
```

---

## 🔑 KEY MODULES BY PURPOSE

### Orchestration (Heart of System)
- **src/orchestrator/server.py** - Main coordination engine
  - Manages agent lifecycle
  - Validates user requests
  - Coordinates memory system
  - Handles shutdown gracefully

- **src/orchestrator/config_loader.py** (NEW! ⭐)
  - Loads .mcp.json configuration
  - Validates agent setup
  - Enforces AGENTS.md requirements
  - Single Responsibility applied

### Security & Validation
- **src/core/security_validator.py** - Deny-by-default enforcement
  - Validates all actions against whitelist
  - Checks sandbox integrity
  - Enforces rate limits

- **src/core/input_validator.py** (ENHANCED ⭐)
  - AST-based semantic analysis
  - Detects dangerous functions (exec, eval, __import__)
  - Blocks dangerous imports (os, sys, subprocess)
  - Regex fallback for edge cases

### Agents (The Workers)
- **src/agents/recon_agent/** - Gathers intelligence
  - Scans targets
  - Enumerates endpoints
  - Identifies weaknesses
  - Evades detection

- **src/agents/logic_agent/** - Plans attacks
  - Analyzes reconnaissance data
  - Generates attack trees
  - Scores feasibility
  - Prioritizes by impact

- **src/agents/exploit_agent/** - Executes exploits
  - Runs payloads in sandbox
  - Captures results
  - Logs successes/failures
  - Feeds learning system

### Backends (External Integrations)
- **src/backends/llm_providers/** - LLM fallback chain
  - OpenAI GPT-4, GPT-3.5
  - Anthropic Claude
  - Ollama (local)
  - Graceful degradation

- **src/backends/docker_sandbox/** - Isolated execution
  - Ephemeral containers
  - eBPF monitoring
  - Read-only root filesystem
  - Network isolation

### Memory System (Learning)
- **src/memory/knowledge_graph.py** - Neo4j relationships
  - Stores MITRE ATT&CK tactics
  - Links vulnerabilities to techniques
  - Tracks success rates

- **src/memory/vector_db/pgvector_client.py** - Semantic search
  - PostgreSQL + pgvector embeddings
  - Semantic search of past operations
  - Context retrieval for planning

---

## 🏗️ Architecture Layers

### Layer 1: Orchestrator (Entry Point)
```python
# src/orchestrator/server.py
class OrchestratorServer:
    def __init__(self, config_path: str = ".mcp.json"):
        self.config = ConfigLoader(config_path).load()  # NEW: DI pattern
        self.security_validator = SecurityValidator()
        self.planner = AttackPlanner()
        self.memory_manager = MemoryManager()
```

### Layer 2: Agents (Decision Makers)
```python
# src/agents/recon_agent/server.py
class ReconAgent:
    async def scan(self, target: str) -> ReconReport:
        # Returns: endpoints, technologies, weaknesses
        pass

# src/agents/logic_agent/server.py
class LogicAgent:
    async def plan_attack(self, recon: ReconReport) -> AttackPlan:
        # Returns: attack tree, feasibility, success rates
        pass

# src/agents/exploit_agent/executor.py
class ExploitAgent:
    async def execute(self, attack: AttackPlan) -> ExploitResult:
        # Returns: success, output, captured data
        pass
```

### Layer 3: Backends (External Services)
```python
# src/backends/llm_providers/provider_manager.py
class ProviderManager:
    async def call(self, prompt: str) -> str:
        # Tries: GPT-4 → Claude → Ollama
        # Returns: LLM response or fallback
        pass

# src/backends/docker_sandbox/sandbox_manager.py
class SandboxManager:
    async def execute(self, payload: str) -> ExecutionResult:
        # Runs: In ephemeral container with isolation
        # Returns: Output + resource metrics
        pass
```

---

## 📝 Modification Points (For Extension)

### Adding a New Agent
1. Create `src/agents/{agent_name}/`
2. Implement `class {Agent}Agent` with async methods
3. Register in `orchestrator/config_loader.py`
4. Add tests to `tests/test_agents_behavior.py`

### Adding a New LLM Provider
1. Create `src/backends/llm_providers/{provider}.py`
2. Implement provider interface
3. Add to fallback chain in `provider_manager.py`
4. Add metrics tracking

### Adding Security Validator Rules
1. Add to `FORBIDDEN_FUNCTIONS` or `FORBIDDEN_MODULES` in `input_validator.py`
2. Update tests in `tests/test_core_security.py`
3. Document in security model

### Adding Memory Features
1. Add methods to `src/memory/knowledge_graph.py` or `pgvector_client.py`
2. Create migration script in `src/memory/vector_db/migrations/`
3. Update `memory_manager.py` to use new feature

---

## 🔄 Data Flow Example: JWT Attack

```
REQUEST
  ↓
user specifies target
  ↓
ORCHESTRATOR (src/orchestrator/server.py)
  ├─ Validate input (src/core/input_validator.py)
  ├─ Check security (src/core/security_validator.py)
  └─ dispatch to RECON AGENT
      ↓
RECON AGENT (src/agents/recon_agent/)
  ├─ Scan target.com:443
  ├─ Find endpoints: /api/auth, /api/users
  ├─ Detect JWT algorithm: HS256 (WEAKNESS!)
  └─ Return ReconReport to LOGIC AGENT
      ↓
LOGIC AGENT (src/agents/logic_agent/)
  ├─ Analyze: HS256 is exploitable
  ├─ Generate attack plan:
  │  ├─ Step 1: Forge JWT with admin claim
  │  ├─ Step 2: Send to /api/users
  │  └─ Step 3: Extract account data
  ├─ Calculate: 95% success probability
  └─ Return AttackPlan to EXPLOIT AGENT
      ↓
EXPLOIT AGENT (src/agents/exploit_agent/)
  ├─ Spin up Docker sandbox
  ├─ Validate payload (src/core/input_validator.py)
  ├─ Execute:
  │  ├─ openssl: Generate forged JWT
  │  ├─ curl: Send to API
  │  └─ parse: Extract response
  ├─ Return ExploitResult
  └─ Send success to MEMORY (src/memory/)
      ↓
MEMORY (Neo4j + PostgreSQL)
  ├─ Store: Attack path → MITRE ATT&CK tactics
  ├─ Update: Success rate for JWT forgery (95%)
  └─ Store: Embeddings for future searches
      ↓
ORCHESTRATOR returns result to user
```

---

## 🧪 Testing Patterns

### Unit Tests (Single Module)
- Located in: `tests/test_*.py`
- Test: Individual functions/classes
- Mock: External dependencies

### Integration Tests
- Located in: `tests/scenarios/`
- Test: Multi-component workflows
- Mock: Only true external services

### Security Tests
- Located in: `tests/test_core_security.py`
- Test: Validation rules
- Ensure: Dangerous payloads rejected

---

## 📋 Files Recently Refactored (P1 Session)

**src/orchestrator/server.py** (REFACTORED)
- Before: 360 LOC monolith (config + validation + orchestration)
- After: 80 LOC focused (uses injected ConfigLoader)
- Benefit: Testable, maintainable

**src/orchestrator/config_loader.py** (NEW ⭐)
- 180 LOC module
- Classes: ConfigLoader, OrchestratorConfig, ManagedAgent, SecurityConfig
- Benefit: SRP applied, single responsibility

**src/core/input_validator.py** (ENHANCED)
- Added: AST-based semantic analysis
- Before: Regex only (bypassable with obfuscation)
- After: ast.parse() + forbidden lists + regex fallback
- Benefit: Robust malicious code detection

---

## 🚀 Future Improvements

- [ ] Implement full DI in all agents (P1.3)
- [ ] Add distributed orchestrator (P2)
- [ ] Implement K8s operator (P2)
- [ ] Performance benchmarking (P2)

---

**Last Updated:** 2026-04-16  
**Rating:** 8.9/10 (before this P1.2/P1.3)  
**Status:** Production Ready ✅

