# Ejemplo de Integración: Orchestrator + .mcp.json

Este archivo muestra cómo integrar el orchestrator con la configuración mejorada de `.mcp.json`.

## Flujo Recomendado

### 1. Actualizar `.mcp.json` con la estructura mejorada

```json
{
  "mcpVersion": "2024-11-05",
  "cacheDir": "src/memory/vector_db",
  "auditLog": "src/memory/knowledge_graph/audit.log",
  
  "mcpServers": {
    "orchestrator": {
      "command": "python",
      "args": ["-m", "src.orchestrator.server"],
      "env": {
        "MODE": "validation",
        "LOG_LEVEL": "DEBUG",
        "AUDIT_ENABLED": "true"
      },
      "limits": {
        "timeoutSeconds": 120,
        "memoryMb": 512
      }
    },
    
    "recon_agent": {
      "command": "python",
      "args": ["-m", "src.agents.recon_agent.server"],
      "env": {
        "STEALTH_MODE": "true",
        "PROFILE": "minimal"
      },
      "capabilities": ["reconnaissance", "passive_scanning"],
      "limits": {
        "timeoutSeconds": 300,
        "memoryMb": 256
      }
    },
    
    "logic_agent": {
      "command": "python",
      "args": ["-m", "src.agents.logic_agent.server"],
      "env": {
        "MODE": "planning",
        "REQUIRES_VALIDATION": "true"
      },
      "capabilities": ["attack_planning", "routing"],
      "limits": {
        "timeoutSeconds": 60,
        "memoryMb": 384
      }
    },
    
    "exploit_agent": {
      "command": "docker",
      "args": ["exec", "artofiabox", "python", "-m", "src.agents.exploit_agent.executor"],
      "env": {
        "SANDBOX": "required",
        "VALIDATION_REQUIRED": "true"
      },
      "capabilities": ["exploit_execution"],
      "restrictedTools": ["filesystem", "network_direct"],
      "limits": {
        "timeoutSeconds": 180,
        "memoryMb": 1024
      }
    },
    
    "evasion_browser": {
      "command": "docker",
      "args": ["run", "--network", "artofianet", "evasion-browser:latest"],
      "env": {
        "HEADLESS": "true",
        "STEALTH": "true"
      },
      "capabilities": ["browser_evasion"],
      "limits": {
        "timeoutSeconds": 240,
        "memoryMb": 512
      }
    },
    
    "exploit_jwt": {
      "command": "python",
      "args": ["-m", "src.agents.exploit_agent.jwt_server"],
      "env": {
        "TRANSPORT_MODE": "stdio",
        "ISOLATION_LEVEL": "strict",
        "REQUIRE_ORCHESTRATOR_VALIDATION": "true"
      },
      "capabilities": ["jwt_attacks"],
      "limits": {
        "timeoutSeconds": 120,
        "memoryMb": 256
      }
    },
    
    "fuzzing_web": {
      "command": "docker",
      "args": ["run", "--network", "artofianet", "fuzzer:latest"],
      "env": {
        "SANDBOX": "required"
      },
      "capabilities": ["fuzzing"],
      "limits": {
        "timeoutSeconds": 600,
        "memoryMb": 1024
      }
    }
  },
  
  "security": {
    "requireOrchestratorValidation": ["exploit_agent", "exploit_jwt", "fuzzing_web"],
    "sandboxRequired": ["exploit_agent", "evasion_browser", "fuzzing_web"],
    "networkIsolation": true,
    "auditAllActions": true,
    "defaultBehavior": "deny"
  }
}
```

### 2. Cómo el Orchestrator Lee esta Configuración

```python
# En server.py
config = json.load(".mcp.json")

# Extrae:
agents = config["mcpServers"]                    # Dict de agentes
security = config["security"]                    # Políticas de seguridad
cache_dir = config["cacheDir"]                   # Ubicación vector DB
audit_log = config["auditLog"]                   # Log de auditoría

# Valida:
- ✅ ¿requireOrchestratorValidation es respetado?
- ✅ ¿sandboxRequired está habilitado para exploit_agent?
- ✅ ¿auditAllActions es true?
- ✅ ¿defaultBehavior es "deny"?
```

### 3. Validación de Acción por supervisor.py

Cuando un agente solicita ejecutar una acción:

```python
# Solicitud del agente
action = {
    "type": "execute_payload",
    "capability": "exploit_execution",
    "payload": "SELECT * FROM users;",
    "justification": "Probar SQL injection en login"
}

# supervisor.py valida:
await supervisor.validate_action(
    agent_name="exploit_agent",
    config=config,          # from .mcp.json
    action=action
)

# Checkpoints:
# 1. ¿exploit_agent existe? ✓
# 2. ¿Es operación bloqueada? ✗ No
# 3. ¿Sandbox presente? ✓ docker exec artofiabox
# 4. ¿Tiene capability "exploit_execution"? ✓
# 5. ¿Requiere orchestrator validation? ✓ Sí
#    → action debe tener "orchestrator_approved": true
# 6. ¿Análisis semántico limpio? ✓
#
# Resultado: APROBADA si orchestrator_approved = true
```

### 4. Flujo Completo de Operación

```
Usuario/Agente Externo
    ↓
[orchestrator.execute_operation()]
    ↓
Cargar config de .mcp.json
    ↓
Para cada action en operation:
    ├─→ [supervisor.validate_action()]
    │   ├─→ Checkpoint 1-3: Infraestructura
    │   ├─→ Checkpoint 4-5: Autorización
    │   └─→ Checkpoint 6: Semántica
    │
    ├─→ Si RECHAZADA:
    │   └─→ Registrar en audit_log
    │       Retornar error
    │
    └─→ Si APROBADA:
        ├─→ Ejecutar en sandbox (si es exploit)
        ├─→ Registrar en memory_manager
        └─→ Persistir resultados
```

### 5. Monitorizar Validaciones

```bash
# Ver histórico de validaciones
async def debug():
    orchestrator = OrchestratorServer()
    
    history = orchestrator.security_validator.get_validation_history()
    
    for entry in history[-10:]:  # Últimas 10
        print(f"{entry['timestamp']} | {entry['agent']} | "
              f"{entry['approved']} | {entry['reasons']}")
```

Output:
```
2026-04-15T10:15:23.456 | exploit_agent | True | []
2026-04-15T10:14:55.123 | exploit_jwt | False | ['No orchestrator_approved field']
2026-04-15T10:14:30.789 | recon_agent | True | []
```

---

## Integración Paso a Paso

### Paso 1: Preparar .mcp.json
Usa la estructura mejorada arriba. Asegúrate de:
- ✅ `security.requireOrchestratorValidation` incluye exploit agents
- ✅ `security.sandboxRequired` incluye consumidores de recursos
- ✅ `security.defaultBehavior` es `"deny"`

### Paso 2: Iniciar Orchestrator
```bash
python -m src.orchestrator.server
```

### Paso 3: Realizar Operaciones
```python
operation = {
    "id": "op_recon_001",
    "target": {"host": "example.com"},
    "actions": [{
        "agent": "recon_agent",
        "type": "passive_enumeration",
        "capability": "reconnaissance",
        "justification": "Gather initial intelligence"
    }]
}

result = await orchestrator.execute_operation(operation)
```

### Paso 4: Revisar Auditoría
```bash
# Ver logs
tail -f src/memory/knowledge_graph/orchestrator_20260415_*.log

# Ver estadísticas
tail -f src/memory/knowledge_graph/audit_20260415.jsonl
```

---

## Troubleshooting

### Problema: "Acción RECHAZADA"

Causas comunes:
1. ❌ Agente no mapeado en `.mcp.json`
2. ❌ Capability no declarada
3. ❌ Agent no en sandbox (para exploit)
4. ❌ Falta `justification` field
5. ❌ Falta `orchestrator_approved` (para agentes que lo requieren)

### Solución:
1. Revisar error en log
2. Actualizar `.mcp.json`
3. Reintentar con estructura correcta

---

**Referencia:** Ver [src/orchestrator/README.md](./README.md) para documentación completa.
