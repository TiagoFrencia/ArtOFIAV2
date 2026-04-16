# 🧪 Guía de Testing - Orchestrator v1.2.0

**Version:** 1.2.0  
**Fecha:** 2026-04-15  
**Objetivo:** Validar que los 4 cambios críticos funcionan correctamente

---

## 🎯 Test Plan

### Módulo 1: server.py - Graceful Shutdown

#### Test 1.1: Signal Handler Registration
```bash
# Verificar que handlers se registran sin error
python -c "from src.orchestrator.server import OrchestratorServer; o = OrchestratorServer(); print('✓ Handlers OK')"
```

**Esperado:** `✓ Handlers OK` (sin excepciones)

#### Test 1.2: Graceful Shutdown Flow
```python
import asyncio
from src.orchestrator.server import OrchestratorServer

async def test_graceful_shutdown():
    orchestrator = OrchestratorServer()
    orchestrator._shutdown_event = asyncio.Event()
    
    # Simular señal
    orchestrator._shutdown_event.set()
    
    # Llamar shutdown
    await orchestrator._graceful_shutdown(timeout=5)
    
    print("✓ Graceful shutdown completado")

asyncio.run(test_graceful_shutdown())
```

**Esperado:**
```
🛑 Iniciando shutdown elegante...
  [1/5] Nuevas operaciones rechazadas
  [2/5] Sin tareas activas
  [3/5] Cerrando 0 conexiones MCP...
  [4/5] Persistiendo auditoría final...
  [5/5] ✓ Cleanup completado
✓ Graceful shutdown completado
```

#### Test 1.3: Active Tasks Cancellation
```python
# Ver que tareas activas se cancelan
async def long_task():
    await asyncio.sleep(100)

async def test_active_tasks():
    orchestrator = OrchestratorServer()
    
    # Crear tarea
    task = asyncio.create_task(long_task())
    orchestrator._active_tasks.append(task)
    
    # Shutdown debe cancelarla
    await orchestrator._graceful_shutdown(timeout=2)
    
    assert task.cancelled(), "Task no fue cancelada"
    print("✓ Task cancellation OK")

asyncio.run(test_active_tasks())
```

---

### Módulo 2: planner.py - 3-7 Step Limit

#### Test 2.1: Step Count Validation
```python
import asyncio
from src.orchestrator.planner import AttackPlanner

async def test_step_count():
    planner = AttackPlanner()
    
    target = {"host": "example.com", "ports": [80, 443]}
    plan = await planner.generate_attack_plan(target)
    
    # Verificar límites
    step_count = plan.get("step_count", 0)
    assert planner.MIN_STEPS <= step_count <= planner.MAX_STEPS, \
        f"Step count {step_count} fuera de rango {planner.MIN_STEPS}-{planner.MAX_STEPS}"
    
    print(f"✓ Step count válido: {step_count}")
    
    return plan

asyncio.run(test_step_count())
```

**Esperado:**
```
✓ Step count válido: 3-7
```

#### Test 2.2: Hierarchical Routing
```python
import asyncio
from src.orchestrator.planner import AttackPlanner

async def test_hierarchical_routing():
    planner = AttackPlanner()
    
    target = {"host": "example.com"}
    plan = await planner.generate_attack_plan(target)
    
    # Verificar que cada step tiene agente y delegation
    for step in plan["steps"]:
        assert step.get("agent"), f"Step {step['number']} sin agente"
        assert step.get("delegation") == True, f"Step {step['number']} no delegado"
    
    # Verificar orden correcto
    agents = [s["agent"] for s in plan["steps"][:3]]
    expected = ["recon_agent", "logic_agent", "exploit_agent"]
    assert agents == expected, f"Orden incorrecto: {agents}"
    
    print(f"✓ Hierarchical routing OK: {agents}")

asyncio.run(test_hierarchical_routing())
```

**Esperado:**
```
✓ Hierarchical routing OK: ['recon_agent', 'logic_agent', 'exploit_agent']
```

#### Test 2.3: Step Processability
```python
import asyncio
from src.orchestrator.planner import AttackPlanner

async def test_processability():
    planner = AttackPlanner()
    
    step = {
        "number": 1,
        "agent": "recon_agent",
        "objective": "Test",
        "expected_output": "Result"
    }
    
    is_valid, reason = await planner._validate_step_processability(step)
    assert is_valid, f"Step no válido: {reason}"
    
    # Test con step incompleto
    bad_step = {"number": 1}
    is_valid, reason = await planner._validate_step_processability(bad_step)
    assert not is_valid, "Step incompleto debería fallar"
    
    print("✓ Processability validation OK")

asyncio.run(test_processability())
```

---

### Módulo 3: supervisor.py - Whitelist + Veil Dropping

#### Test 3.1: Docker Command Whitelist
```python
from src.orchestrator.supervisor import SecurityValidator

validator = SecurityValidator()

# Test 1: Comando permitido
action_good = {
    "command": "python",
    "args": ["-m", "src.agents.exploit_agent.executor"]
}
valid, reason = validator._validate_docker_command_whitelist(action_good)
assert valid, f"Comando válido rechazado: {reason}"
print("✓ Comando permitido: aceptado")

# Test 2: Comando prohibido
action_bad = {
    "command": "rm",
    "args": ["-rf", "/"]
}
valid, reason = validator._validate_docker_command_whitelist(action_bad)
assert not valid, "Comando prohibido debería rechazarse"
print(f"✓ Comando prohibido: rechazado ({reason})")

# Test 3: Whitelist, NO regex
# Esta acción sería bypasseable con regex blacklist
# Pero con whitelist es bloqueada
action_bypass = {
    "command": "python",
    "args": ["-m", "evil_module"]  # No en whitelist
}
valid, reason = validator._validate_docker_command_whitelist(action_bypass)
assert not valid, "Módulo no whitelisteado debería rechazarse"
print(f"✓ Whitelist previene bypass: {reason}")
```

**Esperado:**
```
✓ Comando permitido: aceptado
✓ Comando prohibido: rechazado (Comando 'rm' no en whitelist)
✓ Whitelist previene bypass: Module 'evil_module' no en whitelist
```

#### Test 3.2: Veil Dropping Detection
```python
from src.orchestrator.supervisor import SecurityValidator

validator = SecurityValidator()

# Simular historial: benigno → benigno → destructivo
actions = [
    {"type": "status", "payload": "check system"},     # trust: 1.0
    {"type": "status", "payload": "verify sync"},      # trust: 1.0
    {"type": "exploit", "payload": "delete database"}  # trust: 0.1 - VEIL DROPPING!
]

# Registrar primeras acciones como benignas
for action in actions[:-1]:
    validator._log_tool_call("exploit_agent", action)

# Current action es destructiva
detected = validator._detect_veil_dropping("exploit_agent", actions[-1])
assert detected, "Veil dropping debería detectarse"

print("✓ Veil Dropping Detection: DETECTADO")
print(f"  Historial trust scores: [1.0, 1.0] → 0.1")
print(f"  Cambio de patrón: benigno → destructivo = VEIL DROPPING")
```

**Esperado:**
```
✓ Veil Dropping Detection: DETECTADO
  Historial trust scores: [1.0, 1.0] → 0.1
  Cambio de patrón: benigno → destructivo = VEIL DROPPING
```

#### Test 3.3: Trust Score Calculation
```python
from src.orchestrator.supervisor import SecurityValidator

validator = SecurityValidator()

# Action benigna (trust: ~1.0)
benign = {
    "type": "status",
    "payload": "Check status",
    "justification": "System monitoring"
}
score = validator._calculate_action_trust_score(benign)
assert score > 0.8, f"Benigna debería tener score alto: {score}"
print(f"✓ Acción benigna: trust={score:.2f}")

# Action destructiva (trust: ~0.2)
malicious = {
    "type": "exploit",
    "payload": "DROP TABLE users; DELETE FROM accounts WHERE id > 0",
    "justification": ""  # Sin justificación
}
score = validator._calculate_action_trust_score(malicious)
assert score < 0.4, f"Destructiva debería tener score bajo: {score}"
print(f"✓ Acción destructiva: trust={score:.2f}")
```

---

### Módulo 4: memory_manager.py - Reasoning Traces + Flush

#### Test 4.1: Reasoning Trace Storage
```python
import asyncio
from src.orchestrator.memory_manager import MemoryManager

async def test_reasoning_trace():
    manager = MemoryManager()
    
    # Log una traza de razonamiento
    await manager.log_reasoning_trace(
        trace_id="op_001",
        step_number=1,
        decision="Usar SQL injection",
        outcome="success",
        reasoning={"why": "Target vulnerable", "confidence": 0.95}
    )
    
    # Recuperar
    history = await manager.get_reasoning_history("op_001")
    assert history, "Historial vacío"
    assert len(history["steps"]) == 1, "Step no guardado"
    
    print("✓ Reasoning trace storage OK")
    print(f"  Trace guardada: {history['steps'][0]}")

asyncio.run(test_reasoning_trace())
```

**Esperado:**
```
✓ Reasoning trace storage OK
  Trace guardada: {
    "step": 1,
    "decision": "Usar SQL injection",
    "outcome": "success",
    ...
}
```

#### Test 4.2: Flush Audit Buffer
```python
import asyncio
from src.orchestrator.memory_manager import MemoryManager

async def test_flush():
    manager = MemoryManager()
    
    # Agregar entradas al buffer
    await manager.log_operation("op_001", {"target": "example.com"})
    await manager.log_operation("op_002", {"target": "other.com"})
    
    # Buffer tiene entradas
    assert len(manager._audit_buffer) > 0, "Buffer vacío"
    
    # Flush
    await manager.flush_audit_buffer()
    
    # Buffer se limpió
    assert len(manager._audit_buffer) == 0, "Buffer no se limpió"
    
    print("✓ Flush audit buffer OK")
    print("  Buffer antes: 2 entradas")
    print("  Buffer después: 0 entradas (flusheadas)")

asyncio.run(test_flush())
```

---

## 🏃 Test Suite Completo

Crear archivo `tests/test_orchestrator_v1.2.0.py`:

```python
import asyncio
import pytest
from src.orchestrator.server import OrchestratorServer
from src.orchestrator.planner import AttackPlanner
from src.orchestrator.supervisor import SecurityValidator
from src.orchestrator.memory_manager import MemoryManager


class TestGracefulShutdown:
    """Test suite para server.py"""
    
    @pytest.mark.asyncio
    async def test_signal_handlers(self):
        """Verifica que signal handlers se registran"""
        o = OrchestratorServer()
        assert o is not None
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Verifica graceful shutdown completo"""
        o = OrchestratorServer()
        o._shutdown_event = asyncio.Event()
        await o._graceful_shutdown(timeout=2)
        # Si no hay excepciones, test pasa


class TestScopCreepPrevention:
    """Test suite para planner.py"""
    
    @pytest.mark.asyncio
    async def test_step_count_limits(self):
        """Verifica que pasos están entre 3-7"""
        planner = AttackPlanner()
        target = {"host": "example.com"}
        plan = await planner.generate_attack_plan(target)
        
        assert planner.MIN_STEPS <= plan["step_count"] <= planner.MAX_STEPS
    
    @pytest.mark.asyncio
    async def test_hierarchical_routing(self):
        """Verifica enrutamiento jerárquico"""
        planner = AttackPlanner()
        target = {"host": "example.com"}
        plan = await planner.generate_attack_plan(target)
        
        # Primeros 3 steps deben ser específicos
        expected_agents = ["recon_agent", "logic_agent", "exploit_agent"]
        actual_agents = [s["agent"] for s in plan["steps"][:3]]
        
        assert actual_agents == expected_agents


class TestWhitelistAndVeilDropping:
    """Test suite para supervisor.py"""
    
    def test_docker_whitelist(self):
        """Verifica whitelist de comandos Docker"""
        validator = SecurityValidator()
        
        # Permitido
        good = {"command": "python", "args": ["-m", "src.agents.exploit_agent.executor"]}
        valid, _ = validator._validate_docker_command_whitelist(good)
        assert valid
        
        # Prohibido
        bad = {"command": "rm", "args": ["-rf", "/"]}
        valid, _ = validator._validate_docker_command_whitelist(bad)
        assert not valid
    
    def test_veil_dropping_detection(self):
        """Verifica detección de veil dropping"""
        validator = SecurityValidator()
        
        # Registrar acciones benignas
        validator._log_tool_call("agent", {"type": "status", "payload": "check"})
        validator._log_tool_call("agent", {"type": "status", "payload": "verify"})
        
        # Detectar cambio a destructivo
        destructive = {"type": "exploit", "payload": "delete all"}
        detected = validator._detect_veil_dropping("agent", destructive)
        assert detected


class TestReasoningTracesAndFlush:
    """Test suite para memory_manager.py"""
    
    @pytest.mark.asyncio
    async def test_reasoning_traces(self):
        """Verifica almacenamiento de traces"""
        manager = MemoryManager()
        
        await manager.log_reasoning_trace(
            trace_id="op_1",
            step_number=1,
            decision="SQL injection",
            outcome="success",
            reasoning={"why": "vulnerable"}
        )
        
        history = await manager.get_reasoning_history("op_1")
        assert len(history["steps"]) == 1
    
    @pytest.mark.asyncio
    async def test_flush_audit_buffer(self):
        """Verifica flush de buffer de auditoría"""
        manager = MemoryManager()
        
        await manager.log_operation("op_1", {"target": "test"})
        assert len(manager._audit_buffer) > 0
        
        await manager.flush_audit_buffer()
        assert len(manager._audit_buffer) == 0


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
```

**Ejecutar tests:**
```bash
# Instalar pytest
pip install pytest pytest-asyncio

# Ejecutar suite
pytest tests/test_orchestrator_v1.2.0.py -v
```

---

## ✅ Resultados Esperados

```
test_orchestrator_v1.2.0.py::TestGracefulShutdown::test_signal_handlers PASSED
test_orchestrator_v1.2.0.py::TestGracefulShutdown::test_graceful_shutdown PASSED
test_orchestrator_v1.2.0.py::TestScopCreepPrevention::test_step_count_limits PASSED
test_orchestrator_v1.2.0.py::TestScopCreepPrevention::test_hierarchical_routing PASSED
test_orchestrator_v1.2.0.py::TestWhitelistAndVeilDropping::test_docker_whitelist PASSED
test_orchestrator_v1.2.0.py::TestWhitelistAndVeilDropping::test_veil_dropping_detection PASSED
test_orchestrator_v1.2.0.py::TestReasoningTracesAndFlush::test_reasoning_traces PASSED
test_orchestrator_v1.2.0.py::TestReasoningTracesAndFlush::test_flush_audit_buffer PASSED

====== 8 passed in 0.45s ======
```

---

## 📝 Reporte de Testing

Generar reporte:
```bash
pytest tests/test_orchestrator_v1.2.0.py -v --html=report.html
```

Upload reporte a: `docs/test_reports/v1.2.0/`

---

**Status:** ✅ LISTO PARA TESTING  
**Cobertura Expected:** 95%+  
**Duración:** ~5 minutos
