"""
Documentación del Sistema de Memoria Híbrida de ArtOfIA

Última actualización: 2026-04-15
Versión: 1.0.0

Este documento explica cómo el sistema híbrido de memoria evita bucles,
pérdida de contexto y decisiones ciegas en agentes de seguridad ofensiva.
"""

# ============================================================================
# 1. PROBLEMA: ¿Por Qué Fallan los Agentes?
# ============================================================================

"""
Los agentes autónomos de seguridad ofensiva históricamente fallan por:

1. PÉRDIDA DE CONTEXTO
   - El agente olvida qué ya intentó
   - Repite payloads que no funcionaron
   - No conecta Endpoint A con Token B (ambos descubiertos antes)

2. BUCLES INFINITOS
   - Intenta la misma táctica 10 veces esperando diferente resultado
   - No detecta que WAF cambió de configuración
   - Rate limiting activo pero el agente sigue intentando

3. DECISIONES CIEGAS
   - "¿Cómo atacar un React app?" → no sabe que hay playbooks previos
   - "¿Qué token necesito?" → no consulta grafo de dependencias
   - "¿Funcionará este XSS?" → no aprende de intentos similares

SOLUCIÓN: Sistema de memoria híbrida que combina:
- Grafo semántico (decisiones estructuradas)
- Línea temporal (consciencia de cambios)
- Base de datos vectorial (búsqueda de similares)
- Episodios (playbooks de éxito anterior)
"""

# ============================================================================
# 2. ARQUITECTURA DEL SISTEMA
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────┐
│           MEMORIA SEMÁNTICA (Grafo de Conocimiento)         │
│                    Neo4j Database                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  GraphManager:                                                │
│  ┌───────────────────────────────────┐                      │
│  │ Nodos:                             │                      │
│  │ - Endpoint (/admin, /api/users)   │                      │
│  │ - Token (JWT, CSRF, Session)      │                      │
│  │ - Vulnerability (XSS, SQLi)       │                      │
│  │ - Payload (evasion chains)        │                      │
│  │ - Defense (WAF, IDS, Rate Limit)  │                      │
│  │                                    │                      │
│  │ Relaciones:                        │                      │
│  │ - REQUIRES (Endpoint → Token)     │                      │
│  │ - EXPLOITS (Payload → Vuln)       │                      │
│  │ - EVADES (Tactic → Defense)       │                      │
│  │ - DISCOVERED_BY (Node ← Agent)    │                      │
│  └───────────────────────────────────┘                      │
│                                                               │
│  TemporalTracker:                                             │
│  ┌───────────────────────────────────┐                      │
│  │ Timeline:                          │                      │
│  │ 12:05 - Tactic_A ejecutado        │                      │
│  │ 12:06 - X FRACASO (WAF detectado) │                      │
│  │ 12:10 - WAF_CLOUDFLARE activado   │                      │
│  │ 12:15 - Tactic_B intentado        │                      │
│  │ 12:16 - ✓ ÉXITO (evadió WAF)      │                      │
│  │                                    │                      │
│  │ Predicciones:                      │                      │
│  │ - Rate limit se resetea en 5 min  │                      │
│  │ - Tactic_A degradada 60% → RETIRE │                      │
│  └───────────────────────────────────┘                      │
│                                                               │
│  ExploitationContext:                                         │
│  ┌───────────────────────────────────┐                      │
│  │ Per-target context:                │                      │
│  │ - Frameworks detectados (React)   │                      │
│  │ - Payloads exitosos               │                      │
│  │ - Patrones de defensa aprendidos  │                      │
│  │ - Tokens almacenados              │                      │
│  │ - Mutaciones de seguridad          │                      │
│  └───────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│      MEMORIA RAG + EPISÓDICA (Base de Datos Vectorial)      │
│                PostgreSQL + pgvector                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PGVectorClient:                                              │
│  ┌───────────────────────────────────┐                      │
│  │ Embeddings (1536-dim):             │                      │
│  │ - Respuestas HTTP                 │                      │
│  │ - Comandos ejecutados             │                      │
│  │ - Salidas de herramientas         │                      │
│  │ - Volcados de código              │                      │
│  │ - Patrones de error               │                      │
│  │                                    │                      │
│  │ Búsqueda:                          │                      │
│  │ "¿Qué respuesta fue similar?"     │                      │
│  │ → cosine_similarity (0.85+)       │                      │
│  └───────────────────────────────────┘                      │
│                                                               │
│  ContextSummarizer:                                           │
│  ┌───────────────────────────────────┐                      │
│  │ Token Budget: 8000 tokens          │                      │
│  │ Usage: [████████░░] 78%            │                      │
│  │                                    │                      │
│  │ Active Windows:                    │                      │
│  │ ✓ "Endpoint /admin found" (150)   │                      │
│  │ ✓ "XSS in name param" (200)       │                      │
│  │ ✓ "WAF signature: ..." (300)      │                      │
│  │ → Comprimir ventanas antiguas     │                      │
│  │ → Resumen: "Found 3 endpoints..."│                      │
│  └───────────────────────────────────┘                      │
│                                                               │
│  EpisodicMemoryStore:                                         │
│  ┌───────────────────────────────────┐                      │
│  │ Episodes (Experiencias):           │                      │
│  │                                    │                      │
│  │ 1. "React XSS via JSX injection"  │                      │
│  │    ✓ Successful, reusability: 85% │                      │
│  │    Tactics: [sanitizer_bypass,    │                      │
│  │              dom_clobbering]       │                      │
│  │    Playbook: pb_xss_react         │                      │
│  │                                    │                      │
│  │ 2. "CloudFlare WAF bypass"         │                      │
│  │    ✓ Successful, reusability: 90% │                      │
│  │    Tactics: [tls_spoof, proxy_rot]│                      │
│  │    Playbook: pb_waf_cloudflare    │                      │
│  │                                    │                      │
│  │ Query: "Cómo atacar React con WAF?"│                      │
│  │ → Suggest playbook pb_xss_react   │                      │
│  └───────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# 3. CASOS DE USO: CÓMO FUNCIONA
# ============================================================================

"""
CASO 1: Detección de Bucles (Temporal Awareness)
─────────────────────────────────────────────────

Evento: ReconAgent intenta XSS payload por 4ta vez

TimeLine:
12:05:00 - TACTIC_EXECUTED: XSS_BLIND (endpoint=/search)
12:05:15 - TACTIC_FAILURE: (WAF detectó)
12:05:30 - DEFENSE_ACTIVATED: WAF_CLOUDFLARE (score: 0.8)

12:06:00 - TACTIC_EXECUTED: XSS_BLIND (endpoint=/search) ← MISMO
12:06:10 - TACTIC_FAILURE (WAF detectó)

12:07:00 - TACTIC_EXECUTED: XSS_BLIND (endpoint=/search) ← REPETICIÓN
12:07:05 - TACTIC_FAILURE

Acción:
1. TemporalTracker.detect_cycles(agent_id) → CICLO DETECTADO
2. ExploitationContext.get_tactic_degradation("XSS_BLIND") →
   {
       "current_success_rate": 0.0,
       "degradation_pct": 100,
       "since": "12:05:30",
       "recommendation": "RETIRE"
   }
3. ReconAgent alertado: "Táctica XSS_BLIND degradada. Cambiar estrategia."

BENEFICIO: Evita desperdiciar 100 intentos fallidos más.
"""

"""
CASO 2: Consulta Semántica del Grafo (Relacionar Descubrimientos)
──────────────────────────────────────────────────────────────────

Situación:
- Endpoint /admin descubierto
- Token JWT descubierto en respuesta anterior (¿pero dónde?)

Query al Grafo:
"¿Qué token requiere /admin?"

Cypher:
MATCH (e:Endpoint)-[r:REQUIRES]->(t:Token)
WHERE e.name = "/admin"
RETURN t.name

Resultado:
Endpoint(/admin) ─REQUIRES→ Token(JWT_admin)

Luego:
"¿Dónde fue extraído JWT_admin?"

MATCH (t:Token)-[r:EXTRACTS_FROM]->(s:Source)
WHERE t.name = "JWT_admin"
RETURN s

Resultado:
Token(JWT_admin) ─EXTRACTS_FROM→ Response(GET /api/user-profile)

BENEFICIO: Agente entiende dependencias. No intenta /admin sin JWT.
"""

"""
CASO 3: Búsqueda de Experiencias Similares (Episodic Retrieval)
───────────────────────────────────────────────────────────────

Nuevo target: React.js + Cloudflare + JWT Auth

Query al EpisodicStore:
"Cómo atacar React.js protegido por Cloudflare con JWT?"

EpisodicMemoryStore.suggest_playbook_for_target("react_app", RECONNAISSANCE)

Resultado: 
Playbook encontrado: pb_reconnaissance_react_app
  Success rate: 92%
  Tactics sequence:
    1. TLS_SPOOF (CHROME_120)
    2. PROXY_ROTATE (residential)
    3. JITTER_ENGINE (normal_user profile)
    4. XSS_JSX_INJECTION
    5. JWT_EXTRACTION via DOM

  Expected defenses: [WAF_CLOUDFLARE, CSP, RATE_LIMIT]
  Est. duration: 5 min
  Previous uses: 12 (9 successful, 1 partial, 2 failed)

Agente ejecuta: "Este playbook funcionó 9/10 veces. Confianza: 90%"

BENEFICIO: No empieza desde cero. Reutiliza tácticas probadas.
"""

"""
CASO 4: Compresión de Contexto (Token Budgeting)
────────────────────────────────────────────────

LLM Token Budget: 8000 tokens máximo

Fase 1: Recon descubre 15 endpoints, 100 payloads probados
Total: 12,000 tokens → EXCEDE

ContextSummarizer.add_context(content, importance=0.8) →

Token budget check:
├─ REJECT (too large)
└─ Trigger compression

Compression strategy:
1. Resumen de endpoints antiguos:
   Antes (5000 tokens):
   "GET /admin - 404"
   "GET /admin.php - 404"
   "GET /admin/index - 404"
   "GET /admin/dashboard - 403"
   
   Después (300 tokens):
   "Admin endpoints: tried 4 variants, all blocked"

2. Resumen de payloads fallidos:
   Antes (4000 tokens):
   "Payload: <img src=x onerror=alert(1)> - BLOCKED"
   "Payload: <svg onload=alert(1)> - BLOCKED"
   "Payload: javascript:alert(1) - BLOCKED"
   ... (20 más)
   
   Después (400 tokens):
   "20 XSS payloads blocked by WAF"

Total nuevo: 8,000 tokens (exacto)

BENEFICIO: Contexto coherente sin token overflow.
"""

# ============================================================================
# 4. INTEGRACIÓN CON ORCHESTRATOR
# ============================================================================

"""
Flow:

1. Orchestrator.Supervisor valida action
   ├─ Verifica whitelist
   └─ Consulta memory para veil dropping:
      ExploitationContext.get_fingerprint_consistency()
      ├─ Si cambio significativo → TRUST SCORE ↓
      └─ Si crítico → ABORT

2. Orchestrator.Planner descompone objetivo en 3-7 steps
   For each step:
   ├─ Busca en EpisodicStore si hay playbook similar
   ├─ Sugiere tácticas previas (si suceso_rate > 80%)
   └─ Registra step con confidence_level

3. ReconAgent ejecuta con enrichment de memory
   ├─ Al descubrir endpoint → GraphManager.create_node()
   ├─ Al intentar táctica → TemporalTracker.record_event()
   ├─ Al extraer token → ExploitationContext.store_credential()
   └─ Si éxito → EpisodicMemoryStore.record_episode()

4. LogicAgent y ExploitAgent similar (fase 2)

5. MemorySystem actualiza predicciones
   ├─ TemporalTracker.predict_defense_timeout()
   ├─ ExploitationContext.get_attack_recommendations()
   └─ EpisodicMemoryStore.update_episode_outcome()
"""

# ============================================================================
# 5. INTERFAZ DE USO
# ============================================================================

"""
# Inicializacion

from src.memory import MemorySystem

memory = MemorySystem(
    neo4j_uri="bolt://localhost:7687",
    postgres_url="postgresql://user:pass@localhost/memory"
)

await memory.initialize()

─────────────────────────────────────────────────────────────

# 5.1 GraphManager - Consultas Semánticas

# Crear nodos
endpoint_node = await memory.graph_manager.create_node(
    node_type=NodeType.ENDPOINT,
    name="/admin/users",
    properties={"port": 443, "method": "GET"}
)

token_node = await memory.graph_manager.create_node(
    node_type=NodeType.TOKEN,
    name="JWT_admin",
    properties={"type": "Bearer", "expiry": 3600}
)

# Crear relación
await memory.graph_manager.create_relation(
    source_id=endpoint_node.id,
    target_id=token_node.id,
    relation_type=RelationType.REQUIRES,
    confidence=0.95
)

# Consulta: "¿Qué requiere /admin?"
results = await memory.graph_manager.query_by_semantic(
    "¿Qué payloads han evadido WAF_CLOUDFLARE?",
    limit=10
)

# Detectar ciclos
cycles = await memory.graph_manager.detect_cycles(endpoint_node.id)
if cycles:
    print(f"⚠ Ciclos detectados: {cycles}")

# Rutas alternativas (si táctica falla)
routes = await memory.graph_manager.find_alternative_paths(
    start_node_id=endpoint_node.id,
    end_node_id=token_node.id,
    max_length=5
)

─────────────────────────────────────────────────────────────

# 5.2 TemporalTracker - Timeline y Predicciones

# Registrar evento
event = memory.temporal_tracker.record_event(
    event_type=EventType.TACTIC_SUCCESS,
    node_id="xss_payload_1",
    properties={"bypass_method": "dom_clobbering"},
    confidence=0.92
)

# Obtener degradación de táctica
degradation = memory.temporal_tracker.get_tactic_degradation("xss_payload_1")
if degradation and degradation["recommendation"] == "RETIRE":
    print(f"X Táctica degradada {degradation['degradation_pct']:.0f}%")

# Predecir cuándo se desactiva defensa
prediction = memory.temporal_tracker.predict_defense_timeout("WAF_CLOUDFLARE")
if prediction:
    print(f"Defensa deberá desactivarse en {prediction['estimated_duration_seconds']}s")

# Timeline de eventos
timeline = memory.temporal_tracker.get_timeline(
    event_types=[EventType.TACTIC_FAILURE, EventType.WAF_BLOCK],
    last_n=20
)

─────────────────────────────────────────────────────────────

# 5.3 ExploitationContext - Contexto por Target

# Inicializar contexto
context = ExploitationContext(target_url="https://target.com")

# Registrar framework detectado
context.detect_framework(
    framework=FrameworkType.REACT,
    indicators=[
        "React DevTools detected",
        "JSX in network responses"
    ],
    confidence=0.95
)

# Registrar intento de payload
payload_record = context.record_payload_attempt(
    category=PayloadCategory.XSS,
    payload="<img src=x onerror=alert(1)>",
    endpoint="/search?q=",
    success=True,
    response_time_ms=245,
    evasion_used="jitter_engine + fingerprint_spoof"
)

# Almacenar credential
token_id = context.store_credential(
    credential_type="AUTH_TOKEN",
    value="eyJhbGc...",
    endpoint="/api/auth",
    extraction_method="response_header"
)

# Obtener recomendaciones
recommendations = context.get_attack_recommendations()
for rec in recommendations:
    print(f"Recomendación: {rec['attack_type']} (priority: {rec['priority']})")

─────────────────────────────────────────────────────────────

# 5.4 PGVectorClient - Búsqueda Semántica

# Almacenar documento
await memory.pgvector_client.store_record(
    id="resp_httpbin_001",
    content=json.dumps(http_response),
    content_type="http_response",
    source_context={"endpoint": "/api/data", "method": "GET"},
    metrics={"size_bytes": 4521, "tokens": 1130}
)

# Búsqueda semántica: "¿Qué respuesta fue similar?"
results = await memory.pgvector_client.semantic_search(
    query="JSON response with user data",
    content_types=["http_response"],
    limit=5,
    similarity_threshold=0.7
)

for record, similarity in results:
    print(f"Similitud: {similarity:.1%} - {record.content_type}")

─────────────────────────────────────────────────────────────

# 5.5 ContextSummarizer - Token Budgeting

# Añadir contexto (con verificación de límite)
accepted, metadata = memory.context_summarizer.add_context(
    content="Found XSS in parameter 'q' (POST /search)",
    event_type="XSS_DISCOVERED",
    importance=0.9
)

if not accepted:
    print(f"Contexto rechazado: {metadata['recommendation']}")
else:
    print(f"Tokens restantes: {metadata['remaining']}")

# Predicción de exhaustión
exhaustion = memory.context_summarizer.predict_context_exhaustion()
if exhaustion:
    print(f"⚠ Contexto {exhaustion['severity']}: {exhaustion['recommendation']}")

# Obtener contexto para LLM
llm_context = memory.context_summarizer.get_current_context(max_windows=5)

─────────────────────────────────────────────────────────────

# 5.6 EpisodicMemoryStore - Playbooks

# Registrar experiencia exitosa
episode_id = memory.episodic_store.record_episode(
    objective=ObjectiveType.RECONNAISSANCE,
    target_type="react_app",
    outcome=TacticStatus.SUCCESSFUL,
    tactics_used=[
        {"action": "detect_framework", "target": "window.__REACT_DEVTOOLS__"},
        {"action": "extract_props", "target": "React component state"},
        {"action": "enumerate_endpoints", "method": "network analysis"}
    ],
    duration_seconds=120,
    frameworks_detected=["React"],
    defenses_bypassed=["Content-Security-Policy", "Frame-Ancestors"],
    key_findings={
        "admin_endpoints": 5,
        "data_endpoints": 12,
        "auth_mechanism": "JWT"
    }
)

# Sugerir playbook para nuevo target
playbook = memory.episodic_store.suggest_playbook_for_target(
    target_type="react_app",
    objective=ObjectiveType.RECONNAISSANCE
)

if playbook:
    print(f"Playbook sugerido: {playbook['playbook_id']}")
    print(f"Tácticas: {playbook['tactics']}")
    print(f"Success rate: {playbook['success_rate']:.0%}")

# Encontrar episodios similares
similar = memory.episodic_store.find_similar_episodes(
    objective=ObjectiveType.RECONNAISSANCE,
    target_type="vue_app",
    limit=3
)

for episode, similarity in similar:
    print(f"Similar (sim: {similarity:.1%}): {episode.episode_id}")

─────────────────────────────────────────────────────────────

# 5.7 Obtener Estadísticas Globales

stats = memory.get_system_stats()

print(json.dumps(stats, indent=2))
# {
#   "graph": {
#     "nodes_created": 145,
#     "relations_created": 287,
#     "queries_executed": 42
#   },
#   "temporal": {
#     "total_events": 512,
#     "tactic_stats": {...},
#     "active_defenses": 5
#   },
#   "vector_db": {
#     "records_stored": 1024,
#     "similarity_searches": 89,
#     "cache_hits": 23
#   },
#   "context": {
#     "active_windows": 4,
#     "total_tokens_used": 6847,
#     "utilization_pct": 85.6
#   },
#   "episodic": {
#     "total_episodes": 24,
#     "successful_episodes": 21,
#     "success_rate": 0.875
#   }
# }
"""

# ============================================================================
# 6. CONFIGURACIÓN POR DEFECTO
# ============================================================================

"""
# src/config/memory_defaults.yaml

neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "default"
  graph_database: "neo4j"

postgresql:
  url: "postgresql://user:password@localhost:5432/memory"
  pool_min_size: 2
  pool_max_size: 10
  embedding_dimension: 1536

context_summarizer:
  max_tokens: 8000
  summarization_ratio: 0.5
  min_retention_tokens: 2000
  warning_threshold_pct: 85
  critical_threshold_pct: 95

temporal_tracker:
  retention_hours: 24
  degradation_threshold_pct: 30
  event_batch_size: 100

episodic_memory:
  playbook_extraction_threshold: 0.6  # min reusability
  episodes_retention_days: 30
  max_episodes_in_memory: 1000
"""

# ============================================================================
# 7. PRÓXIMOS PASOS (Phase 2)
# ============================================================================

"""
1. Machine Learning Integration
   - Predicción adaptativa: predecir defensa timeout con ML
   - Clustering de similitudes: agrupar payloads efectivos
   - Anomaly detection: detectar mutaciones defensivas

2. Multi-Agent Learning
   - Compartir memoria entre agentes
   - Federated learning sin exponer contextos
   - Votación: "¿es seguro reutilizar este playbook?"

3. Offline Learning
   - Pre-entrenar embeddings con datasets públicos
   - Inicializar playbooks con OWASP/HackTheBox

4. Memory Export/Import
   - Backup de experiencias
   - Transferencia entre instancias
   - Análisis offline
"""

# ============================================================================
# REFERENCIAS RÁPIDAS
# ============================================================================

"""
Imports:
from src.memory import (
    GraphManager, TemporalTracker, ExploitationContext,
    PGVectorClient, ContextSummarizer, EpisodicMemoryStore,
    MemorySystem
)

Enums:
- NodeType: ENDPOINT, TOKEN, VULNERABILITY, PAYLOAD, TACTIC, DEFENSE, TARGET
- RelationType: REQUIRES, EXTRACTS_FROM, EXPLOITS, EVADES, DISCOVERED_BY
- EventType: TACTIC_EXECUTED, TACTIC_SUCCESS, TACTIC_FAILURE, DEFENSE_ACTIVATED
- FrameworkType: REACT, ANGULAR, VUE, EMBER, SVELTE, NEXT, NUXT
- PayloadCategory: XSS, SQLI, XXE, LFI, CSRF, CRLF, TEMPLATE_INJECTION
- TacticStatus: SUCCESSFUL, PARTIAL, FAILED, DEPRECATED
- ObjectiveType: RECONNAISSANCE, PRIVILEGE_ESCALATION, DATA_EXFILTRATION

Documentación:
- MEMORY_SYSTEM.md (este archivo)
- Ejemplos en: examples/memory_usage/
- Tests: tests/integration/test_memory_*.py
"""

# ============================================================================
# FIN DE DOCUMENTACIÓN
# ============================================================================
"""
