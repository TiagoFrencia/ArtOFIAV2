# Orchestrator - Gestor Central de Agentes Autónomos

## 📋 Descripción General

El **Orchestrator** es el corazón del ecosistema ArtOfIA. Coordina todos los agentes especializados (Recon, Logic, Exploit) y aplica validación semántica rigurosa, aislamiento en sandbox y auditoría centralizada.

Diseño: **Deny-by-default** — Toda acción requiere validación explícita antes de ejecutarse.

---

## 🏗️ Arquitectura

```
Orchestrator/
├── server.py          # Punto de entrada, carga .mcp.json
├── supervisor.py      # Validador de seguridad (deny-by-default)
├── planner.py         # Estratega de operaciones
├── memory_manager.py  # Persistencia y auditoría
└── README.md          # Documentación (este archivo)
```

### Componentes

#### 1. **server.py** — Punto de Entrada
- Inicializa el orquestador
- Carga y parsea `.mcp.json`
- Mapea agentes disponibles y sus capabilities
- Coordina flujo de operaciones
- Punto central de logging

**Responsabilidades:**
- ✅ Validar infraestructura contra AGENTS.md
- ✅ Listar agentes disponibles
- ✅ Ejecutar operaciones completas
- ✅ Mantener estadísticas

#### 2. **supervisor.py** — Validador de Seguridad ⛔
**El componente MÁS CRÍTICO.**

Implementa 6 CHECKPOINTs de validación:

1. **Validación de Agente** → ¿Existe el agente?
2. **Operaciones Bloqueadas** → ¿Es una operación categóricamente prohibida?
3. **Requisito de Sandbox** → ¿El agente está en contenedor?
4. **Autorización** → ¿Tiene capabilities para la acción?
5. **Política Global** → ¿Cumple con política de seguridad?
6. **Análisis Semántico** → ¿Hay inyecciones o misuse?

**Operaciones Bloqueadas (CRITICAL):**
- ❌ Ejecución directa en host
- ❌ Modificación de `docker-compose.yml`
- ❌ Modificación de `AGENTS.md`
- ❌ Acceso directo a red (network breakout)
- ❌ Traversal de filesystem

#### 3. **planner.py** — Estratega de Operaciones
Genera planes de ataque estructurados en 4 fases:

1. **Reconnaissance** (Recon Agent)
   - Escaneo pasivo sigiloso
   - Enumeración de servicios
   - Análisis de stack tecnológico

2. **Planning** (Logic Agent)
   - Análisis de inteligencia recopilada
   - Árbol de decisión de vectores de ataque
   - Evaluación de riesgos

3. **Exploitation** (Exploit Agent)
   - Ejecución de payloads en sandbox
   - Post-explotación
   - Validación de éxito

4. **Evasion** (Transversal)
   - Bypass de WAF, IDS, CAPTCHA
   - Técnicas de ofuscación
   - Timing y fragmentación

#### 4. **memory_manager.py** — Persistencia y Aprendizaje
Almacena conocimiento para **adaptación continua**:

- **Vector DB** (PostgreSQL + pgvector): Embeddings de payloads exitosos
- **Grafo de Conocimiento** (Neo4j): Relaciones payload → defensa → evasión
- **Auditoría Centralizada**: Todas las acciones registradas
- **Aprendizaje**: Fallos capturados → Estrategia adaptada

**Datos Críticos Persistidos:**
- ✅ Ataques exitosos (reutilizable)
- ✅ Ataques fallidos + razón (evitar patrones)
- ✅ Defensas activadas (trigger → ajustar evasión)
- ✅ Relaciones: payload ⟷ defensa ⟷ bypass

---

## 🔐 Flujo de Seguridad

```
Solicitud de Acción
    ↓
[1] ¿Existe agente? → NO → RECHAZADA
    ↓ SÍ
[2] ¿Es operación bloqueada? → SÍ → RECHAZADA
    ↓ NO
[3] ¿Sandbox requerido y presente? → NO → RECHAZADA
    ↓ SÍ
[4] ¿Tiene capability? → NO → RECHAZADA
    ↓ SÍ
[5] ¿Cumple política global? → NO → RECHAZADA
    ↓ SÍ
[6] ¿Análisis semántico limpio? → NO → RECHAZADA
    ↓ SÍ
✅ APROBADA → Ejecutar en Sandbox
```

---

## 📝 Uso

### Iniciar Orchestrator

```bash
cd /Users/tiago/Desktop/ArtOfIAV2
python -m src.orchestrator.server
```

Output esperado:
```
2026-04-15 10:00:00 - === Orchestrator Server Iniciado ===
2026-04-15 10:00:01 - ✓ Configuración cargada desde .mcp.json
2026-04-15 10:00:01 - ✓ 7 agentes mapeados
2026-04-15 10:00:01 - ✓ Validación de infraestructura completada

📊 Agentes Disponibles:
  - orchestrator: ['validation', 'coordination']
  - recon_agent: ['reconnaissance', 'passive_scanning']
  - logic_agent: ['attack_planning', 'routing']
  - exploit_agent: ['exploit_execution']
  - evasion_browser: ['browser_evasion']
  - exploit_jwt: ['jwt_attacks']
  - fuzzing_web: ['fuzzing']

✓ Orchestrator listo para operaciones
```

### Ejecutar una Operación

```python
import asyncio
from src.orchestrator.server import OrchestratorServer

async def main():
    orchestrator = OrchestratorServer()
    
    # Generar plan de ataque
    target = {"host": "example.com", "ports": [80, 443]}
    plan = await orchestrator.plan_attack(target)
    
    # Ejecutar operación
    operation = {
        "id": "op_001",
        "target": target,
        "actions": [
            {
                "agent": "recon_agent",
                "type": "passive_enumeration",
                "capability": "reconnaissance",
                "justification": "Initial intelligence gathering"
            }
        ]
    }
    
    result = await orchestrator.execute_operation(operation)
    print(result)

asyncio.run(main())
```

### Acceder a Auditoría

```python
# Obtener historial
audit_log = orchestrator.get_audit_log()
print(f"Total operaciones: {len(audit_log)}")

# Obtener estadísticas
stats = orchestrator.memory_manager.get_statistics()
print(f"Tasa de éxito: {stats['success_rate']:.2f}%")
```

---

## 🛡️ Reglas de Seguridad (from AGENTS.md)

### Límites Estrictos

1. **Aislamiento:** Todo exploit ejecuta ÚNICAMENTE en `src/backends/docker_sandbox/`
2. **Archivos Protegidos:** `docker-compose.yml`, `.mcp.json`, `AGENTS.md` son inmutables sin autorización humana
3. **Validación Obligatoria:** Exploit agent NUNCA ejecuta sin validación semántica previa
4. **Auditoría Centr:** Todas las acciones registradas en `src/memory/knowledge_graph/`

### Validación Semántica

El supervisor valida:
- ✅ Origen del agente (¿es confiable?)
- ✅ Capacidad vs. Acción (¿tiene permiso?)
- ✅ Inyecciones (¿hay patterns sospechosos?)
- ✅ Justificación explícita (¿por qué hacer esto?)

---

## 📊 Persistencia

### Archivos Generados

```
src/memory/
├── knowledge_graph/
│   ├── orchestrator_YYYYMMDD_HHMMSS.log    # Logs
│   ├── audit_YYYYMMDD.jsonl                # Auditoría
│   ├── graph_attack_success.jsonl           # Ataques exitosos
│   ├── graph_attack_failure.jsonl           # Ataques fallidos
│   ├── graph_defense_event.jsonl            # Defensas activadas
│   └── graph_learning.jsonl                 # Adaptaciones
└── vector_db/
    └── (Embeddings en producción: PostgreSQL + pgvector)
```

---

## 🚀 Próximos Pasos

### Fase 1: Core (Current)
- ✅ server.py
- ✅ supervisor.py
- ✅ planner.py
- ✅ memory_manager.py

### Fase 2: Integración
- [ ] Conectar a PostgreSQL + pgvector
- [ ] Conectar a Neo4j
- [ ] Implementar MCP server oficial

### Fase 3: Agentes
- [ ] Activar recon_agent
- [ ] Activar logic_agent
- [ ] Activar exploit_agent

### Fase 4: Auditoría
- [ ] Dashboard de auditoría
- [ ] Alertas en tiempo real
- [ ] Reportes trimestrales

---

## ⚠️ Importante

**Esta implementación es defensiva por defecto.** Explics y acciones malicioso se rechazan por defecto a menos que:

1. Sean solicitadas por un agente autorizado
2. Tengan capability específica
3. Pasen validación semántica en supervisor.py
4. Se ejecuten dentro del sandbox
5. Sean registradas en auditoría

No hay excepciones a estas reglas.

---

**Última actualización:** 2026-04-15  
**Versión:** 1.0.0  
**Mantenedor:** ArtOfIA Security Team
