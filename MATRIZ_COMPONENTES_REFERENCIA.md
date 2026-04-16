# 🔗 MATRIZ DE REFERENCIA RÁPIDA - COMPONENTES Y RELACIONES

**Documento de Consulta Rápida**  
**Última actualización**: 16 Abril 2026  

---

## 📍 MATRIZ: ARCHIVO → PROPÓSITO → UBICACIÓN

### **ORCHESTRATOR CORE**

| Módulo | Archivo | LOC | Propósito | Dependencias |
|--------|---------|-----|----------|--------------|
| OrchestratorServer | `server.py` | ~200 | Hub central, inicialización | Supervisor, Planner, MemMgr |
| SecurityValidator | `supervisor.py` | ~300 | Validación deny-by-default | .mcp.json, AGENTS.md |
| AttackPlanner | `planner.py` | ~240 | Genera 3-7 step plans | Agentes (recon→logic→exploit) |
| MemoryManager | `memory_manager.py` | ~260 | Persistencia centralizada | Neo4j, PostgreSQL |
| BackendIntegration | `backend_integration.py` | ~180 | Coordina backends | Docker, LLM, AWS |
| Main Entry | `main_integration.py` | ~250 | IntegratedArtOfIA class | Todos los anteriores |
| Examples | `examples_quick_start.py` | ~150 | Demos de uso | Main Entry |

**Ubicación**: `src/orchestrator/`

---

### **EXPLOIT AGENT (7 Sub-agentes)**

| Sub-Agent | Archivo | LOC | Vulnerabilidad | Entrada |
|-----------|---------|-----|-----------------|---------|
| Executor | `executor.py` | ~150 | Dispatcher central | Contexto de vulnerabilidad |
| SQLi Agent | `sqli_agent.py` | ~200 | SQL Injection | SQL injectable params |
| XSS Agent | `xss_agent.py` | ~200 | Cross-Site Scripting | Reflected/Stored inputs |
| SSTI Agent | `ssti_agent.py` | ~180 | Server-Side Template Injection | Template injection points |
| IDOR Agent | `idor_agent.py` | ~190 | Broken Object Level Auth | Enumerable IDs |
| SSRF Agent | `ssrf_agent.py` | ~210 | Server-Side Request Forgery | URL inputs |
| JWT Server | `jwt_server.py` | ~220 | JWT Weaknesses | JWT tokens |

**Ubicación**: `src/agents/exploit_agent/`

**LOTL Sub-Framework**:
- `lotl_executor.py` (~180 LOC): Ejecutor LOTL
- `lolbas_database.py` (~150 LOC): Base de binarios
- `evasion_selector.py` (~140 LOC): Selector inteligente

---

### **RECON AGENT**

| Módulo | Archivo | LOC | Función | Output |
|--------|---------|-----|---------|--------|
| Server | `server.py` | ~120 | MCP server | Tools registry |
| JS Analyzer | `js_analyzer.py` | ~200 | Análisis JavaScript | Secrets, endpoints |
| GraphQL Mapper | `graphql_mapper.py` | ~180 | Introspection + mapping | Schema completo |
| Network Tools | `network_tools.py` | ~150 | DNS, WHOIS, scanning | Tech discovery |
| Config | `prompts.yaml` | ~80 | Prompts del agente | Guía de reconocimiento |

**Ubicación**: `src/agents/recon_agent/`

---

### **LOGIC AGENT**

| Módulo | Archivo | LOC | Función | Entrada |
|--------|---------|-----|---------|---------|
| Server | `server.py` | ~140 | MCP server | Analysis requests |
| Workflow Analyzer | `workflow_analyzer.py` | ~200 | Detecta anomalías | HTTP flows |
| Auth Analyzer | `auth_analyzer.py` | ~190 | Análisis autenticación | Tokens, credentials |
| M2M Spoofing | `agentic_identity.py` | ~160 | Machine-to-Machine | Service accounts |
| Post-Exploit Planner | `post_exploit.py` | ~170 | Planificación post| Exploit success |
| Remediation | `remediation.py` | ~140 | Auto-remediación | Vulnerability info |
| Report Generator | `report_generator.py` | ~180 | Reportes ejecutivos | Operación completa |

**Ubicación**: `src/agents/logic_agent/`

---

### **SUPPLY CHAIN AGENT**

| Módulo | Archivo | LOC | Función |
|--------|---------|-----|---------|
| Server | `server.py` | ~80 | MCP server |
| Scanner | `scanner.py` | ~150 | Token + CI/CD scan |

**Ubicación**: `src/agents/supply_chain_agent/`

---

### **MEMORY LAYER**

#### **Knowledge Graph (Neo4j)**

| Módulo | Archivo | LOC | Propósito |
|--------|---------|-----|----------|
| GraphManager | `graph_manager.py` | ~280 | CRUD de nodos/edges |
| ExploitationContext | `exploitation_context.py` | ~180 | Context management |
| TemporalTracker | `temporal_tracker.py` | ~150 | Timeline de eventos |

**Ubicación**: `src/memory/knowledge_graph/`

**Nodos Neo4j:**
- Endpoint (ruta + método)
- Token (JWT, API key, session)
- Vulnerability (detectadas)
- Payload (exploits probados)
- Tactic (técnicas de evasión)
- Defense (detecciones)

#### **Vector DB (PostgreSQL + pgvector)**

| Módulo | Archivo | LOC | Propósito |
|--------|---------|-----|----------|
| PGVectorClient | `pgvector_client.py` | ~220 | Embeddings RAG |
| EpisodicMemory | `episodic_memory.py` | ~180 | Episodios de ataque |
| ContextSummarizer | `context_summarizer.py` | ~140 | Compresión de contexto |

**Ubicación**: `src/memory/vector_db/`

**Tipos de embeddings:**
- HTTP responses
- Command outputs
- Source code snippets
- Error patterns

---

### **BACKEND: DOCKER SANDBOX**

| Módulo | Archivo | LOC | Responsabilidad |
|--------|---------|-----|-----------------|
| SandboxManager | `sandbox_manager.py` | ~250 | Lifecycle (create/exec/cleanup) |
| eBPFMonitor | `ebpf_monitor.py` | ~280 | Monitoreo de syscalls |
| WebSocketBridge | `websocket_bridge.py` | ~200 | Comunicación payload-orchestrator |
| Dockerfile | `Dockerfile.ephemeral` | ~30 | Imagen ultraligera |
| seccomp profile | `security_profiles/seccomp_profile.json` | ~100 | Filtros de syscalls |

**Ubicación**: `src/backends/docker_sandbox/`

**Límites de seguridad:**
```
CPU:     1 core
Memory:  512 MB
Timeout: 5 minutos
User:    uid=1000 (no root)
Mount:   read-only + tmpfs
Network: aislada
seccomp: 200+ syscall filtering
eBPF:    40+ threat patterns
```

---

### **BACKEND: LLM PROVIDERS**

| Módulo | Archivo | LOC | Modelo | Rol |
|--------|---------|-----|--------|-----|
| ProviderManager | `provider_manager.py` | ~180 | Router | Selecciona proveedor |
| OpenAI Client | `openai_client.py` | ~140 | GPT-4/3.5 | Primaria |
| Anthropic Client | `anthropic_client.py` | ~140 | Claude | Fallback 1 |
| Ollama Client | `ollama_client.py` | ~130 | Local LLM | Fallback 2 (guaranteed) |
| FallbackEngine | `fallback_engine.py` | ~150 | Cascade | Estrategia fallback |

**Ubicación**: `src/backends/llm_providers/`

**Cascade Strategy:**
```
1. Intenta OpenAI (GPT-4) - Más inteligente
   ❌ Si rechaza por policy → 2

2. Intenta Anthropic (Claude) - Equilibrado
   ❌ Si rechaza → 3

3. Ollama (Local) - Sin censura
   ✅ Siempre disponible
```

---

### **BACKEND: CLOUD INFRASTRUCTURE**

| Módulo | Archivo | LOC | Función |
|--------|---------|-----|---------|
| AWSManager | `aws_manager.py` | ~120 | EC2, VPC, SG provisioning |

**Ubicación**: `src/backends/cloud_infrastructure/`

**Instancia Types:**
- t2.micro (free tier)
- t2.small
- t2.medium
- t2.large

---

### **EVASION LAYERS**

#### **Browser Evasion**

| Módulo | Archivo | LOC | Técnica |
|--------|---------|-----|---------|
| StealthController | `stealth_controller.py` | ~220 | Playwright headful + plugins |
| FingerprintSpoofing | `fingerprint_spoofing.py` | ~180 | WebGL, Canvas, Navigator |

**Ubicación**: `src/evasion/browser/`

#### **CAPTCHA Evasion**

| Módulo | Archivo | LOC | Técnica |
|--------|---------|-----|---------|
| ChallengeDetector | `challenge_detector.py` | ~240 | reCAPTCHA V2/V3, hCaptcha |
| SolverClient | `solver_client.py` | ~160 | Cliente de solvers |
| TokenInjector | `token_injector.py` | ~140 | Inyección de tokens |

**Ubicación**: `src/evasion/captcha/`

#### **Proxy Layer**

| Módulo | Archivo | LOC | Técnica |
|--------|---------|-----|---------|
| ProxyRotator | `proxy_rotator.py` | ~180 | Rotación de IPs |
| TLSSpoofing | `tls_spoofing.py` | ~150 | Certificado spoofing |
| JitterEngine | `jitter_engine.py` | ~130 | Timing randomization |

**Ubicación**: `src/evasion/proxy/`

#### **LOTL Framework**

| Módulo | Archivo | LOC | Técnica |
|--------|---------|-----|---------|
| LOTLExecutor | `lotl_executor.py` | ~180 | Ejecutor LOTL |
| LOLBASDatabase | `lolbas_database.py` | ~150 | Base de binarios |
| EvasionSelector | `evasion_selector.py` | ~140 | Selector por OS/EDR |

**Ubicación**: `src/agents/exploit_agent/lotl/`

---

### **INTELLIGENCE ENGINE**

| Módulo | Archivo | LOC | Propósito |
|--------|---------|-----|----------|
| SelfEvolvingEngine | `self_evolving_engine.py` | ~250 | RL optimization |

**Ubicación**: `src/intelligence/`

**Mecanismo:**
```
1. Record episode (attack)
2. Calculate fitness = success_rate - detection_rate
3. Update Q-values para parámetros futuros
4. Adapta tácticas automáticamente
```

---

### **CLI (TYPESCRIPT)**

| Componente | Archivo | Tipo | Función |
|-----------|---------|------|---------|
| Main | `index.tsx` | React | Punto de entrada |
| EventBus | `EventBus.ts` | TS | Pub/Sub events |
| OrchestratorClient | `OrchestratorClient.ts` | TS | WebSocket client |
| StateManager | `StateManager.ts` | TS | Global state |
| App Component | `App.tsx` | React | Root component |
| Base Component | `Base.tsx` | React | UI base |
| ApprovalPanel | `ApprovalPanel.tsx` | React | Human-in-the-loop |
| AttackVisualizer | `AttackGraphVisualizer.tsx` | React | Visualización grafos |
| CommandOutput | `CommandOutputPanel.tsx` | React | Output display |
| EventStream | `EventStreamPanel.tsx` | React | Live events |
| Metrics | `MetricsDashboard.tsx` | React | Métricas KPI |

**Ubicación**: `clients/cli/src/`

---

### **CONFIGURACIÓN**

| Archivo | Tipo | Propósito | Contenido |
|---------|------|----------|----------|
| `.mcp.json` | JSON | MCP servers + limits | Orchestrator, Recon, Logic, Exploit config |
| `prompts/prompts.json` | JSON | Prompt registry | Metadata de todos los prompts |
| `prompts/recon_strategy.yaml` | YAML | Prompts reconocimiento | Strategy instructions |
| `prompts/workflow_analysis.yaml` | YAML | Prompts análisis | Workflow detection |
| `prompts/jwt_reasoning.yaml` | YAML | Prompts JWT | JWT exploit reasoning |
| `prompts/auth_escalation.yaml` | YAML | Prompts escalamiento | Priv escalation |
| `prompts/post_exploitation.yaml` | YAML | Prompts post-exploit | Post-exploitation tactics |
| `prompts/report_generation.yaml` | YAML | Prompts reportes | Report generation |
| `prompts/guardrails.yaml` | YAML | Prompts guardrails | Security boundaries |
| `docker-compose.yml` | YAML | Infraestructura | Neo4j, PostgreSQL, Redis, Browserless |
| `AGENTS.md` | MD | Directrices | Boundaries, limits, responsibilities |

---

## 🔀 MATRICES DE DEPENDENCIAS

### **QUIÉN DEPENDE DE QUIÉN**

```
OrchestratorServer
  ├─ Supervisor (validación)
  ├─ Planner (planificación)
  ├─ MemoryManager 
  │   ├─ GraphManager → Neo4j
  │   └─ VectorManager → PostgreSQL
  └─ BackendIntegration
      ├─ ReconAgent
      │   ├─ JS Analyzer
      │   ├─ GraphQL Mapper
      │   └─ Network Tools
      ├─ LogicAgent
      │   ├─ Workflow Analyzer
      │   ├─ Auth Analyzer
      │   ├─ Post-Exploit Planner
      │   └─ Report Generator
      └─ ExploitAgent
          ├─ 7 Sub-agents (SQLi, XSS, etc)
          ├─ LOTL Framework
          ├─ Evasion.* (4 layers)
          ├─ SandboxManager
          │   └─ eBPFMonitor
          ├─ LLMProvider
          │   └─ FallbackEngine
          └─ SelfEvolvingEngine
```

### **FLUJO DE DATOS**

```
ReconAgent output
  → MemoryManager
    → GraphManager → Neo4j
    → VectorManager → PostgreSQL
    ↓
LogicAgent input
  → Queries GraphManager
  → Generates attack plan
  ↓
Supervisor validates
  ↓
ExploitAgent executes
  → SandboxManager (Docker)
  → eBPFMonitor (security)
  → LLMProvider (adaptation)
  → Evasion layers (4x)
  ↓
Result → MemoryManager
  → SelfEvolvingEngine
    → Adapts for future
```

---

## 📊 ESTADÍSTICAS DE COMPONENTES

| Componente | Archivos | LOC | Rol |
|-----------|----------|-----|-----|
| Orchestrator | 7 | ~1,580 | Hub central |
| ExploitAgent | 10 | ~1,820 | Ejecución |
| LogicAgent | 7 | ~1,180 | Análisis |
| ReconAgent | 5 | ~730 | Reconocimiento |
| Memory KGraph | 3 | ~610 | Grafo semántico |
| Memory VectorDB | 3 | ~540 | RAG embeddings |
| Docker Sandbox | 5 | ~860 | Aislamiento |
| LLM Providers | 5 | ~740 | Modelos IA |
| Evasion | 8 | ~1,320 | Bypass defensas |
| Intelligence | 1 | ~250 | RL engine |
| SupplyChain | 2 | ~230 | CI/CD |
| CLI | 12 | ~N/A | UI Terminal |
| **TOTAL** | **77** | **~21,500** | **Enterprise framework** |

---

## 🎯 ACCESO RÁPIDO POR ROL

### **Desarrollador Core**
```
Archivo clave: src/orchestrator/main_integration.py
Documentación: ANALISIS_PROYECTO_EXHAUSTIVO.md
Flujo: 5-Phase operational flow
```

### **MCP Integration**
```
Configuración: .mcp.json
Servers: orchestrator, recon_agent, logic_agent, exploit_agent
Límites: timeoutSeconds, memoryMb
```

### **Seguridad**
```
Reglas: AGENTS.md
Validador: src/orchestrator/supervisor.py
Blocklist: RestrictedOperation enum
```

### **Memoria**
```
Grafo: src/memory/knowledge_graph/ → Neo4j
Embeddings: src/memory/vector_db/ → PostgreSQL
```

### **Evasión**
```
Browser: src/evasion/browser/
Captcha: src/evasion/captcha/
Proxy: src/evasion/proxy/
LOTL: src/agents/exploit_agent/lotl/
```

---

## 🚀 PUNTOS DE ENTRADA RÁPIDOS

```bash
# Python Main
python src/orchestrator/main_integration.py

# CLI Terminal
cd clients/cli && npm start

# MCP Servers
python -m src.orchestrator.server
python -m src.agents.recon_agent.server
python -m src.agents.logic_agent.server

# Docker Sandbox Test
docker build -f src/backends/docker_sandbox/Dockerfile.ephemeral -t artofiabox:ephemeral .
docker run --rm artofiabox:ephemeral echo "OK"

# Docker Compose
docker-compose up -d   # Start services
docker-compose down    # Stop services
```

---

**Documento generado**: 16 Abril 2026  
**Propósito**: Referencia rápida de componentes y relaciones  
**Versión**: 2.0.0 (ArtOfIA V2 Production)
