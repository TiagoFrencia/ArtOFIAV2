# Directrices de Desarrollo y Comportamiento para Agentes de ArtOfIA

**Versión:** 1.0  
**Última Actualización:** 2026-04-15  
**Auditoría Trimestral Requerida:** Sí  

Este documento define las reglas de comportamiento, límites operativos y estándares para todos los agentes autónomos (Recon, Logic, Exploit) en este ecosistema. Debe tratarse como código vivo, actualizándose cuando cambien los procesos y auditándose trimestralmente para garantizar precisión.

---

## 1. Límites Operativos (Boundaries)

### 1.1 Aislamiento Estricto
- **Ejecución de Exploits:** Toda ejecución de payloads, compilación de código malicioso o pruebas dinámicas ocurre **únicamente** dentro del entorno de contenedores en `src/backends/docker_sandbox/`
- **Alcance:** Los agentes no pueden ejecutar binarios directamente en el host del orquestador
- **Validación:** Todo exploit debe ser validado semánticamente por `orchestrator` antes de su ejecución

### 1.2 Archivos Protegidos
- **Nunca Modificar Sin Autorización:**
  - `docker-compose.yml` (orquestación central)
  - `.mcp.json` (configuración de MCP)
  - Este archivo `AGENTS.md` (directrices core)
- **Procedimiento:** Cambios requieren pull request y confirmación explícita de un operador humano

### 1.3 Regla de Cautela (Exploit Agent)
- El agente `exploit_agent` **nunca** ejecuta ataques sin validación semántica previa del orquestador
- Debe registrar todas las tentativas de ataque (exitosas y fallidas) en `src/memory/knowledge_graph/`
- **Fallback:** Si la validación falla, el agente retorna estado de error y detiene ejecución

---

## 2. Comandos Ejecutables (Commands)

### 2.1 Infraestructura
```bash
# Iniciar ambiente distribuidoDocker compose with persistence
docker compose up -d

# Detener ambiente limpiamente
docker compose down

# Verificar estado de contenedores
docker compose ps
```

### 2.2 Agentes
```bash
# Recon Agent en modo sigiloso
python -m src.agents.recon_agent.server --stealth --profile minimal

# Logic Agent de coordinación
python -m src.agents.logic_agent.server --mode planning

# Exploit Agent dentro del sandbox
docker exec artofiabox python -m src.agents.exploit_agent.executor
```

### 2.3 Pruebas y Evaluación
```bash
# Suite de pruebas de escenarios (end-to-end)
pytest tests/scenarios/ -v --tb=short

# Evaluaciones de rendimiento
jupyter notebook tests/evaluations/

# Pruebas específicas de técnica
pytest tests/scenarios/test_jwt_abuse.py -k "valid_scenario"
```

---

## 3. Estilo de Código y Estructura

### 3.1 Python y Tipado
- **Estándar:** PEP 8 para ALL código Python
- **Tipado:** Type hints obligatorios en firmas de funciones
- **Linting:** `pylint` score mínimo 8.0 antes de merge
- **Formatter:** `black` con 88 caracteres de ancho

### 3.2 Gestión de Prompts
- **Regla Core:** NO hardcodear prompts cognitivos en scripts Python
- **Ubicación Oficial:** Todos los prompts versionados en `prompts/prompts.json` (formato YAML)
- **Referencia:** Los agentes cargan prompts mediante `src/memory/` (vector DB o knowledge graph)
- **Versionado:** Cada cambio de prompt genera entrada en el registro de auditoría

### 3.3 Estructura de Directorio
```
src/
├── agents/           # Agentes especializados (recon, logic, exploit)
├── backends/         # Docker sandbox y proveedores de servicio
├── evasion/          # Técnicas de evasión (browser, captcha, proxy)
├── memory/           # Persistencia de conocimiento (graphs, vectores)
└── orchestrator/     # Coordinador central de tareas

prompts/             # Definiciones de prompts (YAML, versionadas)
tests/               # Pruebas y evaluaciones
```

---

## 4. Pruebas y Evaluaciones (Testing)

### 4.1 Nuevas Técnicas Ofensivas
- **Requisito:** Cada método de ataque en `skills/` debe estar respaldado por tests en `tests/scenarios/`
- **Objetivo:** Prevenir alucinaciones del modelo en vectores de ataque
- **Ejemplo:** Un nuevo ataque GraphQL requiere `test_graphql_attacks.py` con 3+ casos de prueba
- **Cobertura Mínima:** 85% del código ofensivo

### 4.2 Evaluación de Evasión Conductual
- **Antes de Desplegar:** Evalúa tasa de éxito y rendimiento en `tests/evaluations/`
- **Métrica:** %éxito en sandbox vs. detección de WAF/IDS
- **Documentación:** Resultados registrados en notebook correspondiente

### 4.3 Escenarios de Prueba
- Cada escenario simula un ataque end-to-end realista
- Incluir casos de éxito y degradación controlada
- Registrar tiempos de ejecución y consumo de memoria

---

## 5. Flujo de Trabajo (Git Workflow)

### 5.1 Captura de Conocimiento
- **Después de Fallos:** También registrar lecciones aprendidas en `src/memory/knowledge_graph/`
- **Ejemplo:** Un payload bloqueado por análisis conductual se guarda como nodo con razón de bloqueo
- **Propósito:** Los agentes adaptan estrategia en futuros intentos

### 5.2 Mejoras de Evasión
- **Revisión Requerida:** Todos los cambios a `src/evasion/` y `skills/` deben ir por PR
- **Reviewers:** Mínimo 1 revisor autorizado
- **Merge:** Solo después de confirmación de que tests pasan (CI/CD)

### 5.3 Auditoría de Cambios
- Mantener commit messages descriptivos: `[AGENT_TYPE] Brief description - Issue #N`
- Permitir trazabilidad completa de qué logró cada cambio

---

## 6. Mantenimiento y Evolución

### 6.1 Actualización Reactiva
Este documento se actualiza **inmediatamente** cuando:
- Un agente comete un error sistemático
- Surge un nuevo patrón de ataque en ejecuciones
- Cambian las políticas operacionales

### 6.2 Auditoría Trimestral
- **Cuándo:** Cada 3 meses a partir de 2026-04-15
- **Revisor:** Operador humano responsable del ecosistema
- **Checklist:**
  - ¿Los comandos todavía son válidos?
  - ¿Las boundaries se respetan?
  - ¿Hay nuevos errores recurrentes a documentar?
  - ¿Los test coverage y estándares se mantienen?

### 6.3 Evolución Orgánica
- Comenzar simple, agregar complejidad basada en necesidad real
- Cada error real que cometa un agente genera una nueva regla o clarificación
- Mantener balance: suficientemente restrictivo para seguridad, suficientemente flexible para innovación

---

## Matriz de Responsabilidades

| Componente | Agente Responsable | Override | Validación |
|---|---|---|---|
| Reconocimiento | `recon_agent` | `orchestrator` | Inteligencia recopilada |
| Planificación de Ataque | `logic_agent` | Humano | Ruta de ataque factible |
| Ejecución de Exploit | `exploit_agent` | `orchestrator` | Sandbox activo |
| Persistencia de Aprendizaje | Todos | Humano | Registro de auditoría |

---

**Nota:** Este documento será actualizado cuando cambien los procesos operacionales. Para sugerencias de mejora, abrir issue o PR con justificación técnica.
