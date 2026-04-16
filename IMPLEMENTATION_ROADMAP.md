# 🔧 IMPLEMENTATION ROADMAP - Fixes Prioritarios
## ArtOfIA V2 - Action Items Críticos

**Generado:** 16 Abril 2026  
**Basado en:** SENIOR_CODE_REVIEW.md  
**Formato:** Código listo para copiar/pegar

---

## FASE 1: SEGURIDAD CRÍTICA (P0) - Semana 1-2

### 1.1 🔴 CRÍTICO: Fix Race Condition en Audit Buffer

**Archivo:** `src/orchestrator/memory_manager.py`

```python
# ❌ ANTES (ISSUE):
class MemoryManager:
    def __init__(self) -> None:
        self.audit_buffer: List[Dict[str, Any]] = []
    
    async def log_operation(self, operation_id: str, operation: Dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation_id": operation_id,
            "data": operation,
        }
        self.audit_buffer.append(entry)
        if len(self.audit_buffer) >= 100:
            await self._persist_audit_buffer()

# ✅ DESPUÉS (FIJO):
import asyncio

class MemoryManager:
    def __init__(self) -> None:
        self.audit_buffer: List[Dict[str, Any]] = []
        self._buffer_lock = asyncio.Lock()  # ← ADD THIS
    
    async def log_operation(self, operation_id: str, operation: Dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation_id": operation_id,
            "data": operation,
        }
        async with self._buffer_lock:  # ← PROTECT
            self.audit_buffer.append(entry)
            if len(self.audit_buffer) >= 100:
                await self._persist_audit_buffer_unsafe()
    
    async def _persist_audit_buffer_unsafe(self) -> None:
        """Solo llamar desde dentro de _buffer_lock"""
        if not self.audit_buffer:
            return
        
        entries = self.audit_buffer.copy()
        self.audit_buffer.clear()
        
        # Persiste entries...
        await self._persist_audit_entry_batch(entries)
```

**Test para verificar:**
```python
@pytest.mark.asyncio
async def test_no_race_condition_in_buffer():
    manager = MemoryManager()
    
    # Crear 200 tareas concurrentes
    tasks = [
        manager.log_operation(f"op_{i}", {"data": f"test_{i}"})
        for i in range(200)
    ]
    
    await asyncio.gather(*tasks)
    
    # Verificar que no se perdieron entradas
    history = manager.get_audit_log()
    assert len(history) >= 200  # Al menos 200 (pueden haber más si persiste)
```

---

### 1.2 🔴 CRÍTICO: SQL Injection en Graph Queries

**Archivo:** `src/orchestrator/memory_manager.py`

```python
# ❌ ANTES (VULNERABLE):
async def create_attack_node(
    self, attack_id: str, details: Dict[str, Any]
) -> str:
    query = (
        f"CREATE (n:ATTACK {{ "
        f"id: '{attack_id}', "  # ← VULNERABLE
        f"details: '{json.dumps(details)}' "  # ← VULNERABLE
        f"}}) RETURN id(n)"
    )
    result = await self.graph.run(query)
    return result

# ✅ DESPUÉS (SAFE):
async def create_attack_node(
    self, attack_id: str, details: Dict[str, Any]
) -> str:
    query = (
        "CREATE (n:ATTACK { "
        "id: $attack_id, "  # ← PARAMETRIZED
        "details: $details, "  # ← PARAMETRIZED
        "timestamp: timestamp() "
        "}) RETURN id(n)"
    )
    # Usar parameters, no string formatting
    result = await self.graph.run(query, attack_id=attack_id, details=details)
    return result

# Apply este mismo patrón a TODAS las queries:
async def link_attack_to_defense(
    self, attack_id: str, defense_type: str, bypass_technique: Optional[str] = None
) -> None:
    query = (
        "MATCH (a:ATTACK {id: $attack_id}) "
        "MATCH (d:DEFENSE {type: $defense_type}) "
        "CREATE (a)-[r:BLOCKED_BY]->(d) "
        "SET r.bypass_technique = $bypass_technique, "
        "    r.timestamp = timestamp() "
        "RETURN r"
    )
    await self.graph.run(
        query, 
        attack_id=attack_id, 
        defense_type=defense_type, 
        bypass_technique=bypass_technique
    )
```

**Validation Script:**
```python
# Run to check ALL graph queries are parametrized
import re

def check_cypher_injection_risk(filename):
    with open(filename) as f:
        content = f.read()
    
    # Find all graph.run calls
    pattern = r'graph\.run\((.*?)\)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    risky = []
    for match in matches:
        if 'f"' in match or "f'" in match or 'format(' in match:
            risky.append(match[:100])
    
    if risky:
        print(f"⚠️ RISK FOUND in {filename}:")
        for r in risky:
            print(f"  - {r}...")
    else:
        print(f"✅ SAFE: {filename}")

check_cypher_injection_risk('src/orchestrator/memory_manager.py')
```

---

### 1.3 🔴 CRÍTICO: Docker Whitelist Incompleto

**Archivo:** `src/orchestrator/supervisor.py`

```python
# ❌ ANTES (VULNERABLE):
ALLOWED_DOCKER_COMMANDS = {
    "python": {
        "args": ["-m"],
        "modules": ["src.agents.exploit_agent.executor", "src.agents.recon_agent.server"]
    },
    "bash": {
        "scripts": ["/tmp/sandbox_scripts/payload.sh"]
    },
    "curl": {
        "flags": ["-X", "-H", "-d", "-s"]
    }
}

# ✅ DESPUÉS (SECURE):
ALLOWED_DOCKER_COMMANDS = {
    "python": {
        "allowed_only": ["-m"],  # ← WHITELIST ONLY
        "forbidden": ["-c", "-W", "--"],  # ← BLACKLIST DANGEROUS
        "modules": ["src.agents.exploit_agent.executor", "src.agents.recon_agent.server"],
    },
    "bash": {
        "allowed_scripts": {
            "/tmp/sandbox_scripts/payload.sh": {
                "max_lines": 1000,
                "allowed_commands": ["curl", "wget", "grep", "sed"],
            }
        },
    },
    "curl": {
        "allowed_flags": ["-X", "-H", "-d", "-s", "-o"],
        "forbidden_flags": ["-K", "--config"],  # ← Config file not allowed
        "allowed_hosts": ["example.com", "api.target.com"],  # ← URL whitelist
    }
}

async def validate_docker_command(self, cmd: str) -> Tuple[bool, str]:
    """Valida comando antes de ejecutar en sandbox"""
    parts = cmd.split()
    executable = parts[0]
    args = parts[1:]
    
    if executable not in ALLOWED_DOCKER_COMMANDS:
        return False, f"Executable not whitelisted: {executable}"
    
    config = ALLOWED_DOCKER_COMMANDS[executable]
    
    # Forbidden args check (más importante que whitelist)
    if "forbidden" in config:
        for forbidden in config["forbidden"]:
            if forbidden in cmd:
                return False, f"Forbidden flag detected: {forbidden}"
    
    # Python: solo -m permitido
    if executable == "python":
        if "-m" not in args:
            return False, "Python: solo -m permitido"
        
        module = args[args.index("-m") + 1] if "-m" in args else None
        if module not in config["modules"]:
            return False, f"Python module not whitelisted: {module}"
    
    return True, "OK"
```

---

### 1.4 🔴 CRÍTICO: initialize() siempre retorna True

**Archivo:** `src/orchestrator/main_integration.py`

```python
# ❌ ANTES (PROBLEMA):
async def initialize(self) -> bool:
    logger.info("INITIALIZING INTEGRATED ARTOFIABOX")
    
    logger.info("✓ Orchestrator loaded")
    
    backend_config = BackendIntegrationConfig(sandbox_enabled=True, ...)
    self.backend_integration = BackendIntegration(backend_config)
    
    if await self.backend_integration.initialize():
        logger.info("✓ Backend Integration initialized")
    else:
        logger.warning("⚠ Backend Integration initialization incomplete")
    
    logger.info("SYSTEM READY")
    return True  # ← SIEMPRE TRUE, INCLUSO SI FALLA

# ✅ DESPUÉS (CORRECTO):
from typing import Tuple

class InitializationResult:
    def __init__(self, success: bool, errors: List[str]):
        self.success = success
        self.errors = errors
    
    def __bool__(self):
        return self.success

async def initialize(self) -> InitializationResult:
    logger.info("INITIALIZING INTEGRATED ARTOFIABOX")
    errors = []
    
    try:
        logger.info("✓ Orchestrator loaded")
    except Exception as e:
        errors.append(f"Orchestrator failed to load: {e}")
        return InitializationResult(False, errors)
    
    backend_config = BackendIntegrationConfig(
        sandbox_enabled=True,
        llm_enabled=True,
        cloud_enabled=False,
        learning_enabled=True,
    )
    
    self.backend_integration = BackendIntegration(backend_config)
    init_result = await self.backend_integration.initialize()
    
    if not init_result.success:
        errors.extend(init_result.errors)
        logger.error(f"Backend Integration initialization failed:")
        for err in errors:
            logger.error(f"  - {err}")
        return InitializationResult(False, errors)
    
    logger.info("✓ Backend Integration initialized")
    
    # Check all critical services
    checks = [
        ("Docker Sandbox", await self._check_docker()),
        ("LLM Providers", await self._check_llm()),
        ("Memory Systems", await self._check_memory()),
    ]
    
    for service_name, is_ok in checks:
        if is_ok:
            logger.info(f"✓ {service_name} ready")
        else:
            errors.append(f"{service_name} unavailable")
            logger.error(f"❌ {service_name} failed to initialize")
    
    if errors:
        return InitializationResult(False, errors)
    
    logger.info("=" * 70)
    logger.info("SYSTEM READY")
    logger.info("=" * 70)
    
    return InitializationResult(True, [])

# Usage:
result = await system.initialize()
if not result.success:
    print(f"Initialization failed: {result.errors}")
    sys.exit(1)
```

---

### 1.5 🔴 CRÍTICO: No Timeout en Operaciones Async

**Archivo:** `src/orchestrator/main_integration.py`

```python
# ❌ ANTES (PUEDE COLGAR):
async def run_full_red_team_operation(self, target: Dict[str, Any]) -> Dict[str, Any]:
    operation_log = {...}
    
    try:
        recon_result = await self._stage_reconnaissance(target)  # ← Sin timeout
        # ...
    except Exception as e:
        # ...

# ✅ DESPUÉS (CON TIMEOUT):
import asyncio
import time

DEFAULT_STAGE_TIMEOUT = 300.0  # 5 minutos por stage

async def run_full_red_team_operation(self, target: Dict[str, Any]) -> Dict[str, Any]:
    operation_log = {
        "target": target,
        "timestamp": datetime.utcnow().isoformat(),
        "stages": {},
        "result": "pending",
        "start_time": time.time(),
    }
    
    try:
        # STAGE 1: RECONNAISSANCE
        logger.info("[1/4] RECONNAISSANCE STAGE")
        try:
            recon_result = await asyncio.wait_for(
                self._stage_reconnaissance(target),
                timeout=DEFAULT_STAGE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Reconnaissance timeout after {DEFAULT_STAGE_TIMEOUT}s")
            recon_result = {"success": False, "error": "timeout"}
        
        operation_log["stages"]["reconnaissance"] = recon_result
        
        if not recon_result.get("success"):
            logger.warning("⚠ Reconnaissance failed")
            operation_log["result"] = "failed"
            return operation_log
        
        # STAGE 2: ANALYSIS + PLANNING
        logger.info("[2/4] ANALYSIS + PLANNING STAGE")
        try:
            analysis_result = await asyncio.wait_for(
                self._stage_analysis(target, recon_result),
                timeout=DEFAULT_STAGE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Analysis timeout after {DEFAULT_STAGE_TIMEOUT}s")
            analysis_result = {"success": False, "error": "timeout"}
        
        operation_log["stages"]["analysis"] = analysis_result
        
        if not analysis_result.get("success"):
            logger.warning("⚠ Analysis failed")
            operation_log["result"] = "failed"
            return operation_log
        
        # ... similar para STAGE 3 y 4
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        operation_log["result"] = "error"
        operation_log["error"] = str(e)
    
    finally:
        operation_log["duration_seconds"] = time.time() - operation_log["start_time"]
        logger.info(f"Operation completed in {operation_log['duration_seconds']:.2f}s")
    
    return operation_log
```

---

## FASE 2: TESTING & ERROR HANDLING (P1) - Semana 3-4

### 2.1 Reescribir Tests con Validación Real

**Archivo:** `tests/scenarios/test_vulnerabilities.py`

```python
# ❌ ANTES (TESTS FAKE):
@pytest.mark.asyncio
async def test_jwt_weak_secret_detection(self, jwt_app_state):
    assert "weak_secret_key" in jwt_app_state["jwt_config"]["secret"].lower()
    assert len(attack_steps) == 4

# ✅ DESPUÉS (TESTS REAL):
from unittest.mock import Mock, AsyncMock
from src.agents.logic_agent import LogicAgent
from src.agents.logic_agent.models import AnalysisResult

class TestJWTVulnerabilities:
    @pytest.fixture
    def mock_llm(self):
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def logic_agent(self, mock_llm):
        return LogicAgent(llm_provider=mock_llm, memory=None)
    
    @pytest.mark.asyncio
    async def test_jwt_weak_secret_detection(self, logic_agent, mock_llm):
        """Verificar que agente REALMENTE detecta JWT débil"""
        
        # Setup: Mock LLM response
        mock_llm.analyze.return_value = {
            "vulnerabilities": [
                {"type": "weak_signature", "severity": "high", "cve": "CVE-2024-1234"},
                {"type": "no_expiration_check", "severity": "medium", "cve": ""},
            ],
            "attack_chain": [
                {"action": "obtain_jwt_token", "endpoint": "/api/auth/login"},
                {"action": "crack_signature", "difficulty": "low"},
                {"action": "forge_admin_token", "new_claims": {"admin": True}},
                {"action": "access_protected_resource", "endpoint": "/api/admin"},
            ]
        }
        
        # Input: Vulnerable JWT config
        vulnerable_app = {
            "endpoints": [
                {"path": "/api/auth/login", "method": "POST"},
                {"path": "/api/admin", "method": "GET"},
            ],
            "jwt_config": {
                "algorithm": "HS256",
                "secret": "weak_secret_key",
                "expiration": 3600,
            }
        }
        
        # Execute: Llamar agent REALMENTE
        result = await logic_agent.analyze_jwt_endpoints(vulnerable_app)
        
        # Assertions: Verificar resultado REAL
        assert result.success == True, "Analysis should succeed"
        assert len(result.vulnerabilities) >= 2
        assert any(v["type"] == "weak_signature" for v in result.vulnerabilities)
        assert len(result.analysis.attack_chains) > 0
        assert result.analysis.attack_chains[0].confidence >= 0.8
```

**Nuevo test para Redis/Cache:**
```python
@pytest.mark.asyncio
async def test_ddos_mitigation_with_rate_limiting():
    """Verificar que rate limiting protege supervisor"""
    
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    limiter = Limiter(key_func=get_remote_address)
    supervisor = SecurityValidator()
    
    @limiter.limit("10/minute")
    async def validate_action_limited(*args, **kwargs):
        return await supervisor.validate_action(*args, **kwargs)
    
    # Intentar 15 requests en 1 minuto
    for i in range(15):
        try:
            result = await validate_action_limited(
                "exploit_agent",
                config,
                {"type": "test_action"}
            )
            if i < 10:
                assert result is not None
            else:
                # Requests 11-15 deberían ser bloqueados
                assert False, "Should have been rate limited"
        except Exception as e:
            assert "rate" in str(e).lower()
            break
```

---

### 2.2 Crear Error Hierarchy

**Archivo:** `src/core/exceptions.py` (NUEVO)

```python
"""
Exception hierarchy para ArtOfIA V2.
Proporciona context específico para debugging.
"""

class ArtOfIAException(Exception):
    """Base exception para todo el proyecto"""
    def __init__(self, message: str, context: Optional[Dict] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
        }

# Seguridad
class SecurityViolation(ArtOfIAException):
    """Operación bloqueada por security validation"""
    pass

class UnauthorizedAgent(SecurityViolation):
    """Agente no autorizado para la operación"""
    pass

class SandboxEscape(SecurityViolation):
    """Intento de escape del sandbox detectado"""
    pass

class DoesNotExist(ArtOfIAException):
    """Recurso no encontrado"""
    pass

# Docker
class DockerError(ArtOfIAException):
    """Error relacionado con Docker sandbox"""
    pass

class ContainerNotFound(DockerError):
    """Container específico no existe"""
    pass

class SandboxNotReady(DockerError):
    """Sandbox no está listo para ejecutar"""
    pass

# Timeout/Performance
class OperationTimeout(ArtOfIAException):
    """Operación excedió timeout"""
    pass

class MemoryLimitExceeded(ArtOfIAException):
    """Operación excedió límite de memoria"""
    pass

# Configuration
class ConfigError(ArtOfIAException):
    """Problema con configuración"""
    pass

class InvalidConfig(ConfigError):
    """Configuración inválida (schema validation falló)"""
    pass

# Initialize differently for cleaner error propagation
@contextmanager
def raise_on_error(context_name: str):
    """Context manager para convertir excepciones genéricas a específicas"""
    try:
        yield
    except FileNotFoundError as e:
        raise DoesNotExist(
            f"File not found in {context_name}",
            context={"path": str(e)}
        )
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"JSON parsing failed in {context_name}",
            context={"error": str(e)}
        )
```

**Uso en código:**
```python
# ❌ ANTES:
def initialize_backend():
    # ... code ...
    if not result:
        return False

# ✅ DESPUÉS:
def initialize_backend():
    try:
        # ... code ...
        if not result:
            raise SandboxNotReady("Docker daemon not responding")
    except TimeoutError as e:
        raise OperationTimeout(
            "Backend initialization exceeded timeout",
            context={"timeout_seconds": 60, "component": "docker"}
        )
```

---

## FASE 3: PERFORMANCE - Semana 5

### 3.1 Crear Índices Neo4j

**Archivo:** `scripts/init_neo4j.py` (NUEVO)

```python
"""
Initialize Neo4j database with proper indexes.
Run once after database is created.
"""

import asyncio
from neo4j import GraphDatabase

async def initialize_indexes(uri: str, user: str, password: str):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    indexes = [
        # Attack nodes
        ("ATTACK", "id"),
        ("ATTACK", "name"),
        ("ATTACK", "cve"),
        
        # Defense nodes
        ("DEFENSE", "type"),
        ("DEFENSE", "severity"),
        
        # Vulnerability nodes
        ("VULNERABILITY", "cve"),
        ("VULNERABILITY", "signature"),
        
        # Payload nodes
        ("PAYLOAD", "hash"),
        ("PAYLOAD", "success"),
        
        # Evasion techniques
        ("EVASION", "technique_name"),
    ]
    
    async with driver.session() as session:
        for label, property_name in indexes:
            try:
                query = f"CREATE INDEX ON :{label}({property_name})"
                await session.run(query)
                print(f"✓ Index created: {label}({property_name})")
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"✗ Failed to create index {label}({property_name}): {e}")
    
    driver.close()

if __name__ == "__main__":
    asyncio.run(initialize_indexes(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="securepassword"
    ))
```

**Run:**
```bash
python scripts/init_neo4j.py
# Output: ✓ Index created: ATTACK(id), etc.
```

---

### 3.2 Implementar Paginación en Queries

**Archivo:** `src/orchestrator/memory_manager.py`

```python
# ❌ ANTES (CARGA TODO):
async def retrieve_successful_payloads(self) -> List[str]:
    result = await self.graph.run(
        "MATCH (p:PAYLOAD) WHERE p.success = true RETURN p.data"
    )
    return [record[0] for record in result]

# ✅ DESPUÉS (PAGINATED):
from dataclasses import dataclass

@dataclass
class PaginatedResult:
    items: List[Any]
    total_count: int
    current_page: int
    per_page: int
    total_pages: int
    has_next: bool

async def retrieve_successful_payloads(
    self,
    page: int = 1,
    per_page: int = 100
) -> PaginatedResult:
    """Retrieve successful payloads with pagination"""
    
    if page < 1:
        page = 1
    
    skip = (page - 1) * per_page
    
    # Get total count
    count_query = "MATCH (p:PAYLOAD) WHERE p.success = true RETURN count(p) as total"
    count_result = await self.graph.run(count_query)
    total_count = count_result[0]["total"]
    
    # Get paginated results
    query = (
        "MATCH (p:PAYLOAD) WHERE p.success = true "
        "RETURN p.data "
        "SKIP $skip LIMIT $limit"
    )
    
    result = await self.graph.run(query, skip=skip, limit=per_page)
    items = [record[0] for record in result]
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return PaginatedResult(
        items=items,
        total_count=total_count,
        current_page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=(page < total_pages)
    )

# Usage:
results = await memory.retrieve_successful_payloads(page=1, per_page=50)
print(f"Payloads 1-50 of {results.total_count}")
if results.has_next:
    next_results = await memory.retrieve_successful_payloads(page=2, per_page=50)
```

---

## FASE 4: OPERATIONS - Semana 6

### 4.1 Setup Linters/Type Checking

**Archivo:** `pyproject.toml` (ACTUALIZAR)

```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.pylint]
max-line-length = 88
disable = [
    "missing-docstring",
    "too-many-arguments",
    "line-too-long",
]
fail-under = 8.0

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_error_summary = false
```

**Archivo:** `.pre-commit-config.yaml` (NUEVO)

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/pylint
    rev: pylint-3.0.2
    hooks:
      - id: pylint
        args: ['--fail-under=8.0']

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        args: [--strict]
        additional_dependencies: ['types-all']
```

**CI Pipeline:**
```bash
# .github/workflows/lint.yml
name: Lint & Type Check

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install black pylint mypy pytest
      
      - name: Black check
        run: black --check src/
      
      - name: Pylint check
        run: pylint src/ --fail-under=8.0
      
      - name: MyPy check
        run: mypy src/ --strict
      
      - name: Pytest
        run: pytest tests/
```

---

### 4.2 Crear TROUBLESHOOTING.md

**Archivo:** `TROUBLESHOOTING.md` (NUEVO - excerpt)

```markdown
# Troubleshooting Guide - ArtOfIA V2

## Docker Sandbox Issues

### ❌ Error: "Docker daemon not responding"

**Symptom:**
```
SandboxNotReady: Docker daemon not responding after 30s
```

**Root Causes:**
1. Docker service not running
2. Docker socket permissions
3. Network issues

**Solutions:**
```bash
# 1. Verify Docker is running
docker ps

# 2. Check permissions
sudo usermod -aG docker $USER

# 3. Restart Docker
systemctl restart docker

# 4. Check logs
docker logs artofia_dind
```

---

## Race Conditions

### ❌ Error: "Audit buffer loses entries"

**Symptom:** Some operations not appearing in audit log despite successful execution

**Root Cause:** Race condition in concurrent writes to audit_buffer

**Solution:** Already fixed in PHASE 1 (see memory_manager.py update)

**Verification:**
```bash
pytest tests/test_memory_manager.py::test_no_race_condition_in_buffer -v
```

---

## Performance Issues

### ❌ Error: "Queries taking >10s"

**Symptom:** Memory manager queries very slow

**Root Cause:** Missing indexes on Neo4j

**Solution:**
```bash
python scripts/init_neo4j.py
```

**Verify:**
```
PROFILE MATCH (a:ATTACK {id: $id}) RETURN a
# Should show "Hits" not full scans
```

---

(... más issues y soluciones ...)
```

---

## Summary: Quick Implementation Checklist

```
PHASE 1 - SECURITY (Week 1-2):
[ ] Fix race condition in audit_buffer
[ ] Parametrize ALL Neo4j queries
[ ] Improve Docker command whitelist
[ ] Make initialize() return status
[ ] Add timeouts to async operations

PHASE 2 - TESTING (Week 3-4):
[ ] Rewrite tests to call agents
[ ] Create error exception hierarchy
[ ] Add rate limiting
[ ] Setup logging context variables

PHASE 3 - PERFORMANCE (Week 5):
[ ] Create Neo4j indexes
[ ] Implement pagination
[ ] Add caching layer

PHASE 4 - OPERATIONS (Week 6):
[ ] Configure Black/Pylint/Mypy
[ ] Setup CI pipeline
[ ] Write TROUBLESHOOTING.md
```

---

**ESTIMATED EFFORT:**
- Phase 1: 40 hours
- Phase 2: 35 hours
- Phase 3: 15 hours
- Phase 4: 10 hours
- **TOTAL: ~100 hours (2-3 weeks of focused work)**

**RESULT:** Production-ready system scoring 9.0+/10

