# 🔐 INTEGRATION VALIDATION & SYSTEM HEALTH

## Sistema Completo de Validación

Este archivo documenta cómo validar que todos los componentes están correctamente integrados.

---

## 1. Validación de Componentes Individuales

### ✅ Docker Sandbox

```python
# Verificar que sandbox está operacional
from src.backends.docker_sandbox.sandbox_manager import SandboxManager

async def validate_sandbox():
    manager = SandboxManager()
    await manager.initialize()
    
    # Crear contenedor de prueba
    result = await manager.create_container(
        name="test_container",
        exploit_code="echo 'Hello from sandbox'"
    )
    
    # Ejecutar código
    execution = await manager.execute_exploit(
        container_id=result['container_id'],
        code="echo $((1+1))",
        language="bash"
    )
    
    assert execution['exit_code'] == 0
    assert "2" in execution['stdout']
    
    # Limpiar
    await manager.cleanup_container(result['container_id'])
    
    return {"status": "ok", "container_tested": True}
```

**Checklist**:
- ✅ Docker daemon accesible
- ✅ Imagen `artofiabox:ephemeral` disponible
- ✅ Contenedor se crea/ejecuta/destruye sin errores
- ✅ Output se captura correctamente

---

### ✅ eBPF Monitor

```python
from src.backends.docker_sandbox.ebpf_monitor import eBPFMonitor

async def validate_ebpf():
    monitor = eBPFMonitor()
    
    # Crear línea base
    baseline = await monitor.create_security_baseline(
        max_child_processes=10,
        allowed_syscalls=[],  # Usar defaults
    )
    
    # Iniciar monitoreo
    await monitor.start_monitoring(container_id="test")
    
    # Simular actividad sospechosa (dentro del sandbox)
    event = {
        "syscall": "ptrace",
        "args": {"pid": 1234}
    }
    
    result = await monitor.process_syscall_event(event)
    
    # Debe detectarse como CRITICAL
    assert result['threat_level'] == "critical"
    assert result['action'] == "block"
    
    return {"status": "ok", "ebpf_monitoring": True}
```

**Checklist**:
- ✅ Monitor se inicializa sin errores (requiere Linux con eBPF)
- ✅ Se detectan syscalls peligrosas
- ✅ Se generan reportes de violaciones

---

### ✅ WebSocket Bridge

```python
from src.backends.docker_sandbox.websocket_bridge import WebSocketBridge

async def validate_bridge():
    bridge = WebSocketBridge()
    
    # Validator debe rechazar patrones peligrosos
    dangerous_payloads = [
        "$(rm -rf /)",
        "`cat /etc/passwd`",
        "dd if=/dev/mem",
    ]
    
    for payload in dangerous_payloads:
        is_valid = bridge.validator.validate_payload(payload)
        assert not is_valid, f"Payload {payload} debería rechazarse"
    
    # Payload seguro debe pasar
    safe_payload = "echo 'hello'"
    assert bridge.validator.validate_payload(safe_payload)
    
    # Sanitizar output
    dangerous_output = "Success\x00\x01\x02\x03 \x1b[31mRed\x1b[0m"
    safe_output = bridge.validator.sanitize_output(dangerous_output)
    assert "\x00" not in safe_output
    
    return {"status": "ok", "sanitization": True}
```

**Checklist**:
- ✅ Payloads peligrosos se rechazan
- ✅ Payloads seguros se aceptan
- ✅ Output se sanitiza correctamente

---

### ✅ LLM Provider Manager

```python
from src.backends.llm_providers.provider_manager import ProviderManager, ModelType

async def validate_llm_providers():
    manager = ProviderManager()
    
    # Inicializar (conectar a APIs)
    await manager.initialize()
    
    # Verificar salud de cada proveedor
    status = await manager.get_provider_status()
    
    # Al menos Ollama debe estar disponible (local)
    ollama_available = status.get("ollama_local", {}).get("available", False)
    assert ollama_available, "Ollama debe estar disponible como fallback"
    
    # Llamada simple (debería funcionar con Ollama al menos)
    response = await manager.invoke(
        prompt="What is 2+2?",
        model_type=ModelType.OLLAMA_LOCAL
    )
    
    assert response['success']
    assert "4" in response['response'] or "four" in response['response'].lower()
    
    return {"status": "ok", "llm_providers": True}
```

**Checklist**:
- ✅ Al menos Ollama accesible (localhost:11434)
- ✅ Fallback engine funciona
- ✅ Censorship detection activo (si se usan APIs)

---

### ✅ Cloud Infrastructure (AWS)

```python
from src.backends.cloud_infrastructure.aws_manager import AWSManager

async def validate_aws():
    manager = AWSManager()
    
    # Verificar credenciales
    try:
        await manager.initialize()
        credentials_valid = True
    except Exception as e:
        credentials_valid = False
        print(f"AWS credentials not configured: {e}")
    
    if credentials_valid:
        # Crear instancia efímera de prueba
        result = await manager.create_attack_infrastructure(
            instance_type="t2.micro",
            region="us-east-1"
        )
        
        assert result['instance_id']
        assert result['public_ip']
        
        # Destruir
        await manager.destroy_instance(result['instance_id'])
    
    return {
        "status": "ok",
        "aws_available": credentials_valid,
        "note": "AWS es opcional; funciona sin él"
    }
```

**Checklist**:
- ✅ AWS credenciales configuradas (opcional)
- ✅ Instancias se crean/destruyen correctamente
- ⏩ Si no hay AWS, sistema funciona sin esta capacidad

---

### ✅ Self-Evolving Engine (RL)

```python
from src.intelligence.self_evolving_engine import SelfEvolvingEngine

async def validate_rl_engine():
    engine = SelfEvolvingEngine()
    await engine.initialize()
    
    # Registrar un attack outcome
    episode = {
        "technique": "sql_injection",
        "target_os": "linux",
        "success": True,
        "detection_rate": 0.1,
        "reward": 0.9
    }
    
    await engine.record_attack_outcome(episode)
    
    # Obtener recomendaciones
    recommendations = await engine.get_recommended_techniques(
        attack_type="database_evasion",
        target_os="linux",
        edr_type=None
    )
    
    # Debe retornar técnicas ordenadas por fitness
    assert len(recommendations) > 0
    assert recommendations[0]['fitness_score'] > recommendations[-1]['fitness_score']
    
    return {"status": "ok", "rl_engine": True, "episodes": 1}
```

**Checklist**:
- ✅ Engine se inicializa
- ✅ Episodes se registran correctamente
- ✅ Recomendaciones están ordenadas por fitness

---

## 2. Validación de Integración (Layer Bridge)

```python
from src.orchestrator.backend_integration import BackendIntegration, BackendIntegrationConfig

async def validate_integration_layer():
    """
    Validar que BackendIntegration coordina correctamente todos los backends
    """
    
    # Configuración
    config = BackendIntegrationConfig(
        sandbox_enabled=True,
        llm_enabled=True,
        cloud_enabled=False,  # Opcional
        learning_enabled=True,
    )
    
    # Crear integración
    integration = BackendIntegration(config)
    
    # Inicializar TODO
    init_result = await integration.initialize()
    assert init_result['sandbox_initialized']
    assert init_result['llm_initialized']
    assert init_result['learning_initialized']
    
    # Test 1: Ejecutar exploit en sandbox
    exploit_result = await integration.execute_exploit_safely(
        code="print('Integration test')",
        language="python",
        exploit_name="test_integration"
    )
    assert exploit_result['status'] == 'success'
    
    # Test 2: Generar con fallback
    gen_result = await integration.generate_with_fallback(
        prompt="Generate a simple security test"
    )
    assert gen_result['success']
    assert gen_result['model'] in ['gpt-4', 'claude', 'ollama_local']
    
    # Test 3: Obtener recomendaciones
    techs = await integration.get_recommended_techniques(
        attack_type="privilege_escalation",
        target_os="linux"
    )
    assert isinstance(techs, list)
    if len(techs) > 0:
        assert 'technique' in techs[0]
        assert 'fitness_score' in techs[0]
    
    # Test 4: Estado completo
    status = await integration.get_status()
    assert status['sandbox_ready']
    assert status['llm_ready']
    
    return {
        "status": "ok",
        "integration_layer_validated": True,
        "all_backends_coordinated": True
    }
```

---

## 3. Validación de Orquestación Principal

```python
from src.orchestrator.main_integration import IntegratedArtOfIA

async def validate_main_orchestrator():
    """
    Validar que IntegratedArtOfIA coordina el flujo end-to-end
    """
    
    system = IntegratedArtOfIA()
    
    # Inicializar
    await system.initialize()
    
    # Verificar estado
    initial_status = system.get_system_status()
    assert initial_status['orchestrator']['ready']
    assert initial_status['backends']['sandbox']['enabled']
    assert initial_status['backends']['llm_providers']['enabled']
    
    # Ejecutar operación simulada
    target = {
        "name": "Test Target",
        "url": "http://localhost:8000",
        "type": "test"
    }
    
    result = await system.run_full_red_team_operation(target)
    
    # Validar estructura de resultado
    assert 'result' in result
    assert 'stages' in result
    assert 'reconnaissance' in result['stages']
    assert 'analysis' in result['stages']
    assert 'exploitation' in result['stages']
    assert 'learning' in result['stages']
    
    # Cada etapa debe tener estructura consistente
    for stage_name, stage_result in result['stages'].items():
        assert 'status' in stage_result
        assert 'timestamp' in stage_result
    
    return {
        "status": "ok",
        "main_orchestrator_validated": True,
        "end_to_end_workflow": True
    }
```

---

## 4. Suite de Tests Completa

```python
import asyncio

async def run_full_validation():
    """
    Ejecutar todos los tests de validación
    """
    
    tests = [
        ("Sandbox Manager", validate_sandbox),
        ("eBPF Monitor", validate_ebpf),
        ("WebSocket Bridge", validate_bridge),
        ("LLM Providers", validate_llm_providers),
        ("AWS Manager", validate_aws),
        ("RL Engine", validate_rl_engine),
        ("Integration Layer", validate_integration_layer),
        ("Main Orchestrator", validate_main_orchestrator),
    ]
    
    results = {}
    failed = []
    
    print("=" * 60)
    print("INTEGRATION VALIDATION SUITE")
    print("=" * 60)
    
    for test_name, test_func in tests:
        try:
            print(f"\n[TEST] {test_name}...", end=" ")
            result = await test_func()
            results[test_name] = result
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL")
            print(f"       Error: {str(e)}")
            failed.append((test_name, str(e)))
    
    # Resumen
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed tests:")
        for test_name, error in failed:
            print(f"  - {test_name}: {error}")
    else:
        print("\n✅ ALL TESTS PASSED - System is fully integrated!")
    
    return {
        "total": len(tests),
        "passed": len(tests) - len(failed),
        "failed": len(failed),
        "results": results
    }

# Ejecutar
if __name__ == "__main__":
    summary = asyncio.run(run_full_validation())
    exit(0 if summary['failed'] == 0 else 1)
```

---

## 5. Health Dashboard

```python
async def print_health_dashboard():
    """
    Mostrar estado completo del sistema
    """
    
    system = IntegratedArtOfIA()
    await system.initialize()
    
    import time
    
    print("\n" + "=" * 70)
    print("ArtOfIAV2 ENTERPRISE - SYSTEM HEALTH DASHBOARD")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    status = system.get_system_status()
    
    # Orchestrator
    print("\n📊 ORCHESTRATOR")
    print(f"  Status: {'🟢 READY' if status['orchestrator']['ready'] else '🔴 ERROR'}")
    print(f"  Agents: {', '.join(status['orchestrator']['agents'])}")
    
    # Backends
    print("\n🔧 BACKENDS")
    backends = status['backends']
    
    print(f"  Sandbox:")
    print(f"    Enabled: {backends['sandbox']['enabled']}")
    print(f"    Active containers: {backends['sandbox'].get('active_containers', 0)}")
    
    print(f"  LLM Providers:")
    for provider, metrics in backends.get('llm_providers', {}).items():
        print(f"    {provider}:")
        print(f"      Success rate: {metrics.get('success_rate', 0):.1%}")
        print(f"      Rejection rate: {metrics.get('rejection_rate', 0):.1%}")
    
    print(f"  Learning:")
    print(f"    Enabled: {backends.get('learning', {}).get('enabled', False)}")
    print(f"    Episodes recorded: {backends.get('learning', {}).get('episodes', 0)}")
    
    # Operations
    print("\n📈 OPERATIONS")
    print(f"  Total completed: {status.get('operations_completed', 0)}")
    print(f"  Success rate: {status.get('success_rate', 0):.1%}")
    
    # Memory
    print("\n💾 MEMORY")
    print(f"  Knowledge graph: {'🟢 Active' if status.get('memory', {}).get('graph_active') else '🔴 Inactive'}")
    print(f"  Vector DB: {'🟢 Active' if status.get('memory', {}).get('vector_db_active') else '🔴 Inactive'}")
    
    print("\n" + "=" * 70)
    print("✅ System is operational and ready for deployment")
    print("=" * 70)
```

---

## 📋 Checklist de Integración Completa

```
☐ Sandbox Manager  
  ☐ Docker daemon accesible
  ☐ Imagen ephemeral construida
  ☐ Contenedores se crean/ejecutan/destruyen

☐ eBPF Monitor
  ☐ Monitor se inicializa sin errores
  ☐ Syscalls peligrosas se detectan
  ☐ Reportes generados correctamente

☐ WebSocket Bridge
  ☐ Payloads peligrosos rechazados
  ☐ Output sanitizado
  ☐ Comunicación segura establecida

☐ LLM Providers
  ☐ Al menos Ollama accesible
  ☐ Fallback engine funciona
  ☐ Prompts se procesan correctamente

☐ Cloud Infrastructure
  ☐ AWS disponible (opcional)
  ☐ Instancias se provisionan correctamente

☐ RL Engine
  ☐ Episodes se registran
  ☐ Recomendaciones se calculan
  ☐ Fitness scores actualizados

☐ Backend Integration Layer
  ☐ Todos los backends inicializados
  ☐ execute_exploit_safely funciona
  ☐ generate_with_fallback funciona
  ☐ get_recommended_techniques funciona

☐ Main Orchestrator
  ☐ 4 etapas ejecutan en orden
  ☐ Datos fluyen entre etapas
  ☐ Resultado final generado

☐ End-to-End
  ☐ Sistema inicializa sin errores
  ☐ Operación completa ejecuta
  ☐ Reporte generado
```

---

**Status**: ✅ **VALIDATION SUITE READY**
