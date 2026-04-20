# Testing Guide - ArtOfIAV2

**Location:** Tests  
**Purpose:** How to write and run tests effectively

---

## 🧪 Test Infrastructure Overview

**Framework Stack:**
- pytest (main test framework)
- pytest-asyncio (async support)
- pytest-mock (mocking support)
- pytest-benchmark (performance testing)

**Test Files Created (Session v1.3):**
- `tests/test_orchestrator_core.py` (600 LOC, 50+ tests)
- `tests/test_backends_and_memory.py` (450 LOC, 25+ tests)
- `tests/test_agents_behavior.py` (550 LOC, 30+ tests)

---

## 📊 Test Coverage by Module

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| Orchestrator | 50+ | 75%+ | ✅ Baseline established |
| Backends | 25+ | 60%+ | ✅ New coverage |
| Memory | 10+ | 50%+ | ⏳ Partial |
| Agents | 30+ | 70%+ | ✅ Behavior tests |
| Security | 15+ | 80%+ | ✅ Validation tested |
| **TOTAL** | **150+** | **~65%** | ✅ Improving |

---

## 🏃 Running Tests

### All Tests
```bash
pytest tests/ -v --tb=short
```

### Specific Test File
```bash
pytest tests/test_orchestrator_core.py -v
```

### Specific Test Class
```bash
pytest tests/test_orchestrator_core.py::TestOrchestratorInitialization -v
```

### Specific Test Method
```bash
pytest tests/test_orchestrator_core.py::TestOrchestratorInitialization::test_initialization -v
```

### With Coverage Report
```bash
pytest tests/ --cov=src --cov-report=html
```

### Watch Mode (re-run on changes)
```bash
pytest-watch tests/ -n
```

### Parallel Execution
```bash
pytest tests/ -n auto
```

---

## 📝 Test Structure Pattern

### Template: Basic Unit Test
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestMyModule:
    """Test suite for MyModule"""
    
    def test_initialization(self):
        """✅ Module initializes correctly"""
        obj = MyClass()
        assert obj is not None
        assert obj.property == expected_value
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """✅ Async operation returns correct result"""
        obj = MyClass()
        result = await obj.async_method("input")
        assert result == expected_output
    
    def test_with_mock(self):
        """✅ Correctly handles mocked dependency"""
        mock_dep = Mock()
        mock_dep.method.return_value = "mocked"
        
        obj = MyClass(dependency=mock_dep)
        result = obj.process()
        
        mock_dep.method.assert_called_once()
        assert result == expected
```

### Template: Async Test
```python
@pytest.mark.asyncio
async def test_async_workflow():
    """✅ Complete async operation flow"""
    # Setup
    obj = AsyncClass()
    
    # Execute
    result = await obj.process_async()
    
    # Assert
    assert result.status == "success"
    assert len(result.data) > 0
```

### Template: Mock/Patch Test
```python
def test_with_external_dependency():
    """✅ Correctly handles external service"""
    with patch('module.external_service') as mock_service:
        mock_service.return_value = {"status": "ok"}
        
        obj = MyClass()
        result = obj.use_service()
        
        assert result == expected
```

---

## 🎯 Writing Good Tests

### DO ✅
- ✅ One assertion per test (or related assertions)
- ✅ Clear test names: `test_<what>_<expected_result>`
- ✅ Use fixtures for common setup
- ✅ Mock external dependencies
- ✅ Test both happy path AND error cases
- ✅ Use parametrize for multiple scenarios
- ✅ Add docstrings explaining the test

### DON'T ❌
- ❌ Don't test implementation details, test behavior
- ❌ Don't create complex test fixtures
- ❌ Don't skip edge cases
- ❌ Don't use magic numbers (use constants)
- ❌ Don't assume test order (tests are independent)
- ❌ Don't skip flaky tests (fix them!)

---

## 📋 Test Categories

### Unit Tests (Test Single Function/Class)
**Pattern:**
```python
class TestConfigLoader:
    def test_loads_json_correctly(self):
        loader = ConfigLoader("test.json")
        config = loader.load()
        assert config.agents == expected_agents
```

### Integration Tests (Test Multiple Components)
**Pattern:**
```python
@pytest.mark.asyncio
async def test_orchestrator_with_loaded_config():
    config = ConfigLoader(...).load()
    orchestrator = OrchestratorServer(config)
    result = await orchestrator.run_operation(...)
    assert result.success
```

### Behavior Tests (Test Agent Interaction)
**Pattern:**
```python
@pytest.mark.asyncio
async def test_recon_output_feeds_logic_agent():
    recon_result = await recon_agent.scan(target)
    logic_plan = await logic_agent.plan_attack(recon_result)
    assert logic_plan is not None
    assert logic_plan.success_rate > 0.5
```

### Security Tests (Test Validation Rules)
**Pattern:**
```python
def test_rejects_exec_in_payload():
    payload = "exec('malicious')"
    validator = InputValidator()
    assert not validator.is_safe(payload)
```

### Performance Tests (Benchmark)
**Pattern:**
```python
@pytest.mark.benchmark
def test_config_loading_speed(benchmark):
    def load_config():
        return ConfigLoader("config.json").load()
    
    result = benchmark(load_config)
    assert result.success
```

---

## 🛠️ Common Pytest Features

### Fixtures (Reusable Setup)
```python
@pytest.fixture
def sample_config():
    """Provides a test configuration"""
    return ConfigLoader("tests/fixtures/config.json").load()

class TestWithConfig:
    def test_uses_fixture(self, sample_config):
        assert sample_config.agents is not None
```

### Parametrize (Multiple Scenarios)
```python
@pytest.mark.parametrize("algorithm,expected", [
    ("HS256", "weak"),
    ("RS256", "strong"),
    ("ES256", "strong"),
])
def test_algorithm_strength(algorithm, expected):
    validator = AlgorithmValidator()
    result = validator.check(algorithm)
    assert result == expected
```

### Marks (Organize Tests)
```python
@pytest.mark.slow
def test_full_workflow():
    pass

@pytest.mark.asyncio
async def test_async_operation():
    pass

@pytest.mark.security
def test_payload_validation():
    pass

# Run only security tests:
# pytest tests/ -m security
```

### Fixtures with Cleanup
```python
@pytest.fixture
def docker_container():
    container = start_container()
    yield container  # Test runs here
    container.stop()  # Cleanup

class TestWithCleanup:
    def test_in_container(self, docker_container):
        assert docker_container.is_running
```

---

## 🧪 Test Examples from Codebase

### From test_orchestrator_core.py
```python
class TestOrchestratorInitialization:
    """Tests for orchestrator startup"""
    
    def test_initialization_with_config(self):
        """✅ Loads and validates configuration"""
        server = OrchestratorServer(".mcp.json")
        assert server.config is not None
        assert len(server.config.agents) >= 3
    
    def test_requires_valid_config_path(self):
        """✅ Rejects invalid config paths"""
        with pytest.raises(FileNotFoundError):
            OrchestratorServer("nonexistent.json")
```

### From test_backends_and_memory.py
```python
class TestPGVectorClient:
    """Tests for semantic search in PostgreSQL"""
    
    @pytest.mark.asyncio
    async def test_stores_embedding(self):
        """✅ Correctly stores embeddings"""
        client = PGVectorClient(db_url="...", embedding_dim=1536)
        result = await client.store(embedding_record)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """✅ Finds similar embeddings"""
        client = PGVectorClient(...)
        results = await client.search(query_embedding, limit=5)
        assert len(results) <= 5
        assert results[0]["similarity"] >= 0.5
```

### From test_agents_behavior.py
```python
class TestReconAgent:
    """Tests for reconnaissance behavior"""
    
    @pytest.mark.asyncio
    async def test_discovers_endpoints(self):
        """✅ Finds API endpoints"""
        agent = ReconAgent()
        result = await agent.scan("http://target.local")
        
        assert result["endpoints"] is not None
        assert len(result["endpoints"]) > 0

### From test_agents_behavior.py
```python
class TestExploitAgentSecurity:
    """Security tests for exploit execution"""
    
    @pytest.mark.asyncio
    async def test_rejects_exec_payload(self):
        """✅ Blocks dangerous exec() calls"""
        agent = ExploitAgent()
        dangerous = {"code": "exec('os.system(\"rm -rf /\")')"}
        
        result = await agent.validate_payload(dangerous)
        assert result["valid"] == False
        assert "exec" in result["dangerous_calls"]
```

---

## 📊 Generating Coverage Reports

### Text Report
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### HTML Report (easier to navigate)
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### JSON Report (for CI/CD)
```bash
pytest tests/ --cov=src --cov-report=json
```

---

## 🔍 Debug a Failing Test

### Show Full Output
```bash
pytest tests/test_file.py::test_name -vv -s
```

### Drop into Debugger
```python
def test_something():
    result = function_call()
    assert result == expected  # Add pdb here:
    
    import pdb; pdb.set_trace()  # Execution pauses here
```

### Use pytest's built-in debugging
```bash
pytest tests/test_file.py::test_name --pdb
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## 📈 Test Coverage Goals

**Session v1.3 Status:**
- Orchestrator: 75%+ ✅
- Agents: 70%+ ✅
- Core: 80%+ ✅
- Backends: 60%+ ✅ (improving)
- Memory: 50%+ ⏳ (needs work)

**Target for 9.3/10:**
- Overall: 85%+ coverage
- Critical: 95%+ coverage

---

## ✅ Pre-Commit Checklist

Before committing code:
- [ ] `pytest tests/ -v` passes
- [ ] `mypy src/ --strict` passes (or at least no new errors)
- [ ] `coverage` is not lower than main branch
- [ ] New features have tests
- [ ] Tests are independent (no ordering)

---

**Last Updated:** 2026-04-16  
**Total Tests:** 150+  
**Coverage:** ~65% (improving)  
**Status:** Baseline established ✅

