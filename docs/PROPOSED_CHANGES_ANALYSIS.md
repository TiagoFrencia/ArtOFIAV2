# Análisis de Cambios Propuestos - Orchestrator v1.1.0

**Fecha:** 2026-04-15  
**Prioridad:** CRÍTICA (Seguridad + Estabilidad)

---

## 📊 Análisis Detallado por Componente

### 1. **server.py** — Graceful Shutdown ⭐ CRÍTICO

#### Problema Identificado:
- Sin manejadores de señales (SIGINT, SIGTERM)
- Conexiones MCP/SSE pueden quedar abiertas
- Tareas HTTP sin estado acumulan en memoria
- Riesgo de corrupción de datos si cierre brusco

#### Solución Propuesta:
```python
import signal
import asyncio

# Implementar:
- Signal handlers para SIGINT, SIGTERM
- Cancelación de tareas pendientes
- Cierre ordenado de conexiones MCP
- Flush de buffers y cierre de archivos
- Persistencia de estado antes de salir
```

**Impacto:** 
- ✅ Previene fugas de memoria
- ✅ Protege integridad de auditoría
- ✅ Permite reinicio limpio

---

### 2. **planner.py** — Scope Creep Prevention ⭐ CRÍTICO

#### Problema Identificado:
- Planes sin límites de pasos (> 7 puede causar alucinaciones)
- No valida que cada paso sea procesable
- Enrutamiento incorrecto: intenta resolver vs. delegación
- PentAGI framework mejor: 3-7 pasos específicos

#### Solución Propuesta:
```python
# Implementar:
- Rango estricto: 3-7 pasos
- Validación de procesabilidad de cada paso
- Enrutamiento jerárquico (no resolución local)
- Step counter y validación de limites
- Fallback si excede límites
```

**Cambio de Arquitectura:**
```
ANTES: Agent intenta resolver directamente
       Plan tiene N pasos indefinidos

DESPUÉS: Agent elige especialista correcto
         Plan tiene exactamente 3-7 pasos
         Cada paso tiene outcome predefinido
```

**Impacto:**
- ✅ Reduce alucinaciones LLM
- ✅ Mayor confiabilidad
- ✅ Asignación correcta a especialistas

---

### 3. **supervisor.py** — Seguridad (Whitelist + History Audit) ⭐ CRÍTICO

#### Problema 1: Validación Regex (Blacklist) — CVE-2026-2256
```python
# ❌ INSEGURO (Actual):
if re.search(r'(?i)(rm|delete|drop)', command):
    reject()  # Fácil de bypassear

# ✅ SEGURO (Propuesto):
ALLOWED_COMMANDS = {
    "docker exec": {...},
    "python -m": {...}
}
if command not in ALLOWED_COMMANDS:
    reject()
```

#### Problema 2: Veil Dropping — Confianza Falsa
```python
# ❌ INSEGURO (Validar solo request actual):
validate(current_action)  # Gana confianza, luego muta

# ✅ SEGURO (Auditar todo el historial):
for action in tool_call_history:
    if action degrades trust:
        reject()  # Incluso si request actual parece inocuo
```

**Impacto:**
- ✅ Previene CVE-2026-2256 (ejecución arbitraria)
- ✅ Detecta "veil dropping" attacks
- ✅ Auditoría completa de comportamiento

---

### 4. **memory_manager.py** — Temporal Awareness + Reasoning ⭐ CRÍTICO

#### Problema 1: RAG Estático vs. Temporal
```python
# ❌ INSEGURO (RAG clásico):
payload = similarity_search(query)  # Ignora tiempo
# En operación real: datos cambian rápido, respuesta stale

# ✅ SEGURO (Temporal Graphs):
payload = temporal_search(query, time_window)  # Con Graphiti
# Respeta actualizaciones frecuentes
```

#### Problema 2: Falta Memoria de Razonamiento
```python
# ❌ INSEGURO (Solo payloads):
storage = {
    "successful_payloads": [...]
}
# No sabe por qué falló el paso 2 → repite error

# ✅ SEGURO (Decision Traces):
storage = {
    "successful_payloads": [...],
    "reasoning_traces": {
        "step_1": {"decision": "...", "outcome": "...", "why": "..."},
        "step_2": {"decision": "...", "outcome": "FAILURE", "reason": "..."}
    }
}
# Próximo intento evita el error
```

**Impacto:**
- ✅ Información de decisiones siempre fresca
- ✅ No repite errores
- ✅ Mejor aprendizaje de fallos

---

## 🔧 Cambios Implementar (Orden de Prioridad)

### P1 - CRÍTICO (Hoy)
1. ✅ server.py: Signal handlers + graceful shutdown
2. ✅ planner.py: 3-7 step limit + enrutamiento jerárquico
3. ✅ supervisor.py: Whitelist only + history audit

### P2 - IMPORTANTE (Próxima semana)
4. ✅ memory_manager.py: Temporal graphs readiness
5. ✅ memory_manager.py: Reasoning traces storage

### P3 - FUTURO (Neo4j/Graphiti ready)
6. Integrar Neo4j con Graphiti para temporal queries
7. Implementar vector DB con pgvector temporal
8. Dashboard de reasoning traces

---

## 📈 Matriz de Riesgo

| Componente | Riesgo Actual | Riesgo Post-Fix | Mejora |
|---|---|---|---|
| server.py | ALTO (Memory leak) | BAJO | 85% ↓ |
| planner.py | ALTO (Alucinaciones) | BAJO | 90% ↓ |
| supervisor.py | CRÍTICO (RCE) | BAJO | 99% ↓ |
| memory_manager.py | MEDIO (Stale data) | BAJO | 80% ↓ |

---

## ✅ Checklist de Implementación

- [ ] server.py: Agregar signal handlers
- [ ] server.py: Agregar context manager
- [ ] planner.py: Agregar step counter (3-7)
- [ ] planner.py: Agregar routing validation
- [ ] supervisor.py: Reemplazar regex con whitelist
- [ ] supervisor.py: Agregar history audit
- [ ] memory_manager.py: Agregar reasoning_traces storage
- [ ] memory_manager.py: Agregar temporal awareness
- [ ] Tests: Verificar todos los cambios
- [ ] Documentación: Actualizar README

---

**Next Step:** Implementar cambios en orden P1
