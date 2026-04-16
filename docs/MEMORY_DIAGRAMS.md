"""
MEMORY SYSTEM ARCHITECTURE - Mermaid Diagram Reference

Visual representation of the hybrid memory system architecture.
Use with markdown renderers that support Mermaid.

Link: docs/MEMORY_SYSTEM.md (Section 2)
"""

# ARCHITECTURE DIAGRAM (Mermaid)

ARCHITECTURE = """
graph LR
    subgraph "SEMANTIC LAYER (Neo4j)"
        GM["GraphManager<br/>(Nodos & Relaciones)"]
        TT["TemporalTracker<br/>(Timeline)"]
        EC["ExploitationContext<br/>(Per-Target)"]
        
        GM --> |record event| TT
        GM --> |persist context| EC
    end
    
    subgraph "RAG/EPISODIC LAYER (PostgreSQL)"
        PGVC["PGVectorClient<br/>(Embeddings)"]
        CS["ContextSummarizer<br/>(Token Budget)"]
        EM["EpisodicMemoryStore<br/>(Playbooks)"]
        
        PGVC --> |compress if needed| CS
        CS --> |store experience| EM
    end
    
    subgraph "ORCHESTRATOR"
        SUP["Supervisor<br/>(Validation)"]
        PLAN["Planner<br/>(3-7 Steps)"]
    end
    
    subgraph "AGENTS"
        RA["ReconAgent"]
        LA["LogicAgent"]
        EA["ExploitAgent"]
    end
    
    SUP --> |query for context| GM
    PLAN --> |suggest playbook| EM
    
    RA --> |register node| GM
    RA --> |record event| TT
    RA --> |store token| EC
    RA --> |embed response| PGVC
    
    LA --> |similar to RA|PLAN
    EA --> |similar to RA|PLAN
    
    EM --> |suggest tactics| RA
    CS --> |enrich context| RA
    TT --> |detect cycles| SUP
"""

# TEMPORAL AWARENESS DIAGRAM

TEMPORAL = """
graph TD
    A["12:05:00 - Tactic_XSS executed<br/>endpoint: /search"]
    B["12:05:15 - X FAILED (WAF)"]
    C["12:05:30 - DEFENSE_ACTIVATED<br/>WAF_CLOUDFLARE"]
    
    D["12:06:00 - Tactic_XSS attempted again<br/>(SAME - NOT LEARNING)"]
    E["12:06:10 - X FAILED (WAF)"]
    
    F["CYCLE DETECTION<br/>↓<br/>Tactic_XSS has 0% success rate<br/>Duration: 1 minute"]
    
    G["RECOMMENDATION:<br/>RETIRE tactic_xss<br/>Try alternative"]
    
    A --> B --> C
    B --> D --> E
    E --> F --> G
    
    style F fill:#ff6b6b,color:#fff
    style G fill:#51cf66,color:#fff
"""

# KNOWLEDGE GRAPH EXAMPLE

GRAPH = """
graph LR
    Endpoint["Endpoint<br/>/admin"]
    Token["Token<br/>JWT_admin"]
    Source["Source<br/>GET /profile"]
    WAF["Defense<br/>WAF_CF"]
    Payload["Payload<br/>XSS_JSX"]
    Vuln["Vulnerability<br/>DOM XSS"]
    
    Endpoint -->|REQUIRES| Token
    Token -->|EXTRACTS_FROM| Source
    Endpoint -->|PROTECTED_BY| WAF
    Payload -->|EVADES| WAF
    Payload -->|EXPLOITS| Vuln
    
    style Endpoint fill:#4a90e2,color:#fff
    style Token fill:#7ed321,color:#000
    style WAF fill:#ff6b6b,color:#fff
    style Payload fill:#f5a623,color:#000
"""

# VECTOR DB SEARCH

VECTOR_SEARCH = """
graph LR
    Query["Query: React XSS via JSX<br/>embedding: [0.2, 0.8, ...]"]
    
    DB["PostgreSQL<br/>Vector DB<br/>1024 embeddings"]
    
    Result1["Result 1<br/>similarity: 0.92<br/>Response: HTTP 200<br/>Content: ..."]
    
    Result2["Result 2<br/>similarity: 0.87<br/>Response: HTTP 403<br/>Content: ..."]
    
    Result3["Result 3<br/>similarity: 0.71<br/>Response: HTTP 400<br/>Content: ..."]
    
    Query -->|cosine_similarity| DB
    DB -->|top-k| Result1
    DB -->|top-k| Result2
    DB -->|top-k| Result3
    
    style Result1 fill:#51cf66,color:#000
    style Result2 fill:#f5a623,color:#000
    style Result3 fill:#ff6b6b,color:#fff
"""

# EPISODIC MEMORY PLAYBOOK EXTRACTION

EPISODIC = """
graph TD
    Episode["Episode<br/>React app exploitation<br/>Duration: 5 min<br/>Success: YES"]
    
    Tactics["Tactics Used:<br/>1. TLS_SPOOF<br/>2. PROXY_ROTATE<br/>3. JITTER_ENGINE<br/>4. XSS_JSX<br/>5. TOKEN_EXTRACT"]
    
    Score["Reusability Score<br/>= 0.92 (high)"]
    
    Playbook["Playbook Generated:<br/>pb_xss_react_app"]
    
    Suggest["Future Target:<br/>New React App"]
    
    Reuse["Suggest:<br/>pb_xss_react_app<br/>Success rate: 92%"]
    
    Episode --> Tactics
    Tactics --> Score
    Score -->|> 0.6| Playbook
    
    Playbook -->|store| Suggest
    Suggest -->|find_similar| Reuse
    
    style Episode fill:#4a90e2,color:#fff
    style Playbook fill:#51cf66,color:#000
    style Reuse fill:#f5a623,color:#000
"""

# TOKEN BUDGETING

TOKEN_BUDGET = """
graph LR
    Context1["Context 1<br/>Endpoints (2000 tokens)"]
    Context2["Context 2<br/>Payloads (3000 tokens)"]
    Context3["Context 3<br/>Errors (1500 tokens)"]
    Context4["Context 4<br/>NEW (1500 tokens)"]
    
    Total["Total: 8000 tokens<br/>(100% budget"]
    
    Budget["Budget Check<br/>Utilization: 78%"]
    
    Context1 --> Total
    Context2 --> Total
    Context3 --> Total
    Context4 -->|new incoming| Budget
    
    Compress["Action: COMPRESS<br/>Summarize Context 3<br/>500 tokens → freed 1000"]
    
    Budget -->|> 85%| Compress
    
    style Total fill:#4a90e2,color:#fff
    style Budget fill:#f5a623,color:#000
    style Compress fill:#51cf66,color:#000
"""

# CYCLE DETECTION

CYCLE = """
graph TD
    Try1["Attempt 1<br/>XSS_BLIND<br/>@12:05:00"]
    Fail1["FAIL<br/>WAF Detected"]
    
    Try2["Attempt 2<br/>XSS_BLIND<br/>@12:06:00<br/>(SAME)"]
    Fail2["FAIL<br/>WAF Detected"]
    
    Try3["Attempt 3<br/>XSS_BLIND<br/>@12:07:00<br/>(SAME)"]
    Fail3["FAIL<br/>WAF Detected"]
    
    Detect["Cycle<br/>Detected<br/>After 3 cycles"]
    
    Alert["Alert!<br/>Tactic XSS_BLIND<br/>Success rate: 0%<br/>Recommendation: RETIRE"]
    
    Try1 --> Fail1 --> Try2
    Try2 --> Fail2 --> Try3
    Try3 --> Fail3 --> Detect
    Detect --> Alert
    
    style Try1 fill:#4a90e2,color:#fff
    style Fail1 fill:#ff6b6b,color:#fff
    style Fail2 fill:#ff6b6b,color:#fff
    style Fail3 fill:#ff6b6b,color:#fff
    style Alert fill:#51cf66,color:#000
"""

# FULL WORKFLOW

WORKFLOW = """
graph LR
    Target["NEW TARGET:<br/>React + Cloudflare + JWT"]
    
    EM["EpisodicStore<br/>find_similar_episodes"]
    
    Playbook["Playbook Found!<br/>pb_xss_react_app<br/>Success rate: 92%"]
    
    TT["TemporalTracker<br/>Check defenses"]
    
    Pred["Prediction:<br/>WAF resets in 5 min"]
    
    Agent["ReconAgent<br/>Execute with playbook"]
    
    Log["Log all events<br/>in GraphManager"]
    
    Store["Store experience<br/>in EpisodicStore"]
    
    Target --> EM
    EM --> Playbook
    Playbook --> TT
    TT --> Pred
    Pred --> Agent
    Agent --> Log
    Log --> Store
    
    style Target fill:#4a90e2,color:#fff
    style Playbook fill:#51cf66,color:#000
    style Pred fill:#f5a623,color:#000
    style Agent fill:#7ed321,color:#000
"""

print(__doc__)
print("\n" + "="*80)
print("COPY THESE MERMAID DIAGRAMS TO: docs/MEMORY_DIAGRAMS.md")
print("="*80 + "\n")

for name, diagram in [
    ("ARCHITECTURE", ARCHITECTURE),
    ("TEMPORAL AWARENESS", TEMPORAL),
    ("KNOWLEDGE GRAPH", GRAPH),
    ("VECTOR SEARCH", VECTOR_SEARCH),
    ("EPISODIC MEMORY", EPISODIC),
    ("TOKEN BUDGETING", TOKEN_BUDGET),
    ("CYCLE DETECTION", CYCLE),
    ("FULL WORKFLOW", WORKFLOW)
]:
    print(f"\n## {name}")
    print("```mermaid")
    print(diagram)
    print("```")
