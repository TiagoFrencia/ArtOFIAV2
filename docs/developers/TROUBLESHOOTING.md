# TROUBLESHOOTING.md - ArtOfIA Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2026-04-16  
**Audience:** Operators, Developers, and SREs

This guide provides systematic troubleshooting procedures for common issues in the ArtOfIA platform. Each issue includes symptoms, root causes, diagnostics, and remediation steps.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Performance Issues](#performance-issues)
4. [Security & Validation](#security--validation)
5. [Docker & Containers](#docker--containers)
6. [Neo4j & Knowledge Graph](#neo4j--knowledge-graph)
7. [Recovery Procedures](#recovery-procedures)
8. [Escalation](#escalation)

---

## Quick Diagnostics

### System Health Check

```bash
# 1. Check Docker containers status
docker compose ps

# Expected output: artofiabox and neo4j should be "Up"
# If stopped: docker compose up -d

# 2. Verify Neo4j connectivity
docker exec artofiabox python -c "
from neo4j import AsyncGraphDatabase
import asyncio
async def test():
    uri = 'bolt://neo4j:7687'
    driver = AsyncGraphDatabase.driver(uri, auth=('neo4j', 'password'))
    async with driver.session() as session:
        result = await session.run('RETURN 1')
        print('✅ Neo4j connected')
    await driver.close()
asyncio.run(test())
"

# 3. Check Python environment
python --version  # Should be 3.11+
python -m pytest --version  # Should be pytest 7.0+

# 4. Verify git state
git log --oneline -1  # Show latest commit
git status  # Should show no uncommitted changes
```

### Metrics Collection

```bash
# Get current system metrics
docker stats artofiabox neo4j

# Show Docker logs (last 100 lines)
docker compose logs -n 100

# Neo4j metrics query
docker exec neo4j cypher-shell -u neo4j -p password "
CALL dbms.queryJmx('java.lang:type=Memory') YIELD attributes
UNWIND attributes AS attr
RETURN attr.name, attr.value
"
```

---

## Common Issues

### Issue 1: Initialization Failures

**Symptom:** `initialize()` returns `InitializationResult(False, ['...'], {...})`

**Root Causes:**
- Neo4j not running or unreachable
- Docker sandbox not available
- Missing configuration files
- Port bindings already in use

**Diagnostics:**

```bash
# Check if ports are in use
netstat -an | grep -E "7687|6379|9200"  # Windows/bash
Get-NetTCPConnection -State Listen | Select LocalPort | Where {$_.LocalPort -in 7687,6379,9200}  # PowerShell

# Check Neo4j logs
docker logs neo4j | tail -50

# Verify docker-compose.yml is valid
docker compose config | head -30
```

**Remediation Steps:**

```bash
# Step 1: Stop all containers
docker compose down

# Step 2: Remove volumes to reset state
docker compose down -v

# Step 3: Start fresh
docker compose up -d

# Step 4: Wait for services (30 seconds)
sleep 30

# Step 5: Re-run initialization
python -c "
from src.orchestrator.main_integration import OrchestratorIntegration
import asyncio
orch = OrchestratorIntegration()
result = asyncio.run(orch.initialize())
print(f'Status: {result}')
"
```

**Prevention:**
- Always use: `if not init_result: raise SystemError(init_result)`
- Never proceed if `success == False`
- Log all component statuses before proceeding

---

### Issue 2: Rate Limiting Errors

**Symptom:** `RateLimitException` thrown frequently

**Root Causes:**
- Concurrent operations exceeding limits
- Per-agent quota exhausted (100 req/min)
- Per-resource quota exhausted (50-200 req/min)
- Global quota exhausted (1000 req/min)

**Diagnostics:**

```bash
# Check current rate limit state
python -c "
from src.orchestrator.supervisor import RateLimiter
limiter = RateLimiter(capacity=100, refill_rate=100/60)  # per-agent
print(f'Current tokens: {limiter.tokens}')
print(f'Capacity: {limiter.capacity}')
"

# Monitor Docker command rate
docker exec artofiabox python -m pytest tests/test_phase2_improvements.py::TestRateLimiter -v

# Check supervisor logs for rate limit hits
docker logs artofiabox | grep "RateLimitException"
```

**Remediation Steps:**

```python
# Option 1: Increase limits (if legitimate traffic spike)
# In src/orchestrator/supervisor.py:
PER_AGENT_LIMIT = 200  # was 100
PER_RESOURCE_LIMITS = {
    "docker_commands": 100,  # was 50
    "api_calls": 400  # was 200
}
GLOBAL_LIMIT = 2000  # was 1000

# Option 2: Implement backoff strategy in agent
import asyncio
import random
async def execute_with_backoff(action, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await supervisor.validate_action(action)
        except RateLimitException:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Rate limited, retrying in {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            else:
                raise

# Option 3: Distribute load across agents
# Assign different agents to different time windows
# E.g., Agent A: minutes 0-20, Agent B: minutes 20-40, Agent C: minutes 40-60
```

**Prevention:**
- Profile your workload to understand typical request/min rate
- Set limits 2-3x higher than peak observed demand
- Use exponential backoff for transient rate limit hits
- Monitor `LogContext` for operation_id hotspots

---

### Issue 3: Audit Buffer Race Conditions

**Symptom:** Audit entries lost, duplicate entries, or buffer corruption

**Root Causes:**
- Multiple agents writing simultaneously (FIXED in P0)
- AsyncLock not held during buffer operations
- Flush operation not atomic

**Diagnostics:**

```bash
# Verify audit buffer integrity
python -c "
from src.orchestrator.memory_manager import MemoryManager
import asyncio
mm = MemoryManager()
asyncio.run(mm.initialize())
buffer_state = mm.audit_buffer
print(f'Buffer size: {len(buffer_state)}')
print(f'Last 5 entries:')
for entry in buffer_state[-5:]:
    print(f'  - {entry}')
"

# Run race condition test
python -m pytest tests/test_p0_fixes.py::TestAuditBufferRaceCondition -v
```

**Remediation Steps:**

```bash
# This is a P0 fix (already implemented in PHASE 1)
# If issue still occurs, verify these changes are in place:

# 1. Check memory_manager.py has AsyncLock
grep -n "self._buffer_lock = asyncio.Lock()" src/orchestrator/memory_manager.py

# 2. Check log_operation has lock
grep -A 5 "async def log_operation" src/orchestrator/memory_manager.py | grep "async with self._buffer_lock"

# 3. Check flush_audit_buffer is atomic
grep -A 20 "async def flush_audit_buffer" src/orchestrator/memory_manager.py | grep "copy()\|clear()\|persist"

# If missing, apply P0 fixes from IMPLEMENTATION_ROADMAP.md
```

**Prevention:**
- Always use: `async with self._buffer_lock:` for buffer writes
- Never hold lock during I/O (copy→clear→persist outside lock)
- Test with TestAuditBufferRaceCondition before deployment

---

### Issue 4: Cypher Injection Vulnerabilities

**Symptom:** `InjectionException` from graph_manager, or malicious queries executing

**Root Causes:**
- String formatting instead of parameterization (FIXED in P0)
- User-supplied NodeType/RelationType not validated
- Unsafe Cypher string concatenation

**Diagnostics:**

```bash
# Check for vulnerable code patterns
grep -r "f\".*\$" src/memory/  # Look for f-string in Cypher
grep -r "\.format.*\$" src/memory/  # Look for .format() in Cypher
grep -r "\+ \"" src/memory/  # Look for string concatenation

# Run injection tests
python -m pytest tests/test_p0_fixes.py::TestNeo4jInjectionProtection -v
```

**Remediation Steps:**

```bash
# This is a P0 fix (already implemented in PHASE 1)
# If issue occurs, verify graph_manager.py has these checks:

# 1. Verify NodeType validation
grep -n "isinstance(node_type, NodeType)" src/memory/knowledge_graph/graph_manager.py

# 2. Verify RelationType validation
grep -n "isinstance(relation_type, RelationType)" src/memory/knowledge_graph/graph_manager.py

# 3. Verify safe label extraction
grep -n "node_label = node_type.value" src/memory/knowledge_graph/graph_manager.py

# If missing, apply P0 fixes from IMPLEMENTATION_ROADMAP.md
```

**Prevention:**
- NEVER use string formatting in Cypher queries
- ALWAYS validate enum types with isinstance()
- Use Cypher parameters: `MATCH (n:Node {id: $id})`
- Add tests for injection for each new query

---

## Performance Issues

### Issue 5: Slow Neo4j Queries

**Symptom:** Query duration >500ms, dashboard lags, timeouts occurring

**Root Causes:**
- Missing indexes (FIXED in PHASE 3)
- Inefficient Cypher queries
- Large result sets without pagination
- Query cache not working

**Diagnostics:**

```bash
# Check if indexes exist
docker exec neo4j cypher-shell -u neo4j -p password "CALL db.indexes() YIELD name, state, populationPercent RETURN name, state, populationPercent"

# Show query metrics
python -c "
from src.memory.query_optimization import MetricsCollector
collector = MetricsCollector()
# Run test query
stats = collector.get_stats()
print(f'Total queries: {stats[\"total_queries\"]}')
print(f'Avg time: {stats[\"avg_execution_ms\"]:.1f}ms')
print(f'Max time: {stats[\"max_execution_ms\"]:.1f}ms')
print(f'Cache hit rate: {stats[\"cache_hit_rate_percent\"]:.1f}%')
"

# Profile slow queries
python -m pytest tests/test_phase3_performance.py::TestMetricsCollector::test_slow_query_detection -v
```

**Remediation Steps:**

```bash
# Step 1: Initialize missing indexes
docker exec artofiabox python -c "
from scripts.init_neo4j import init_neo4j_indexes
from neo4j import AsyncGraphDatabase
import asyncio

driver = AsyncGraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password'))
results = asyncio.run(init_neo4j_indexes(driver))
print('Indexes initialized:')
for result in results:
    print(f'  ✅ {result}')
"

# Step 2: Verify indexes are populated
# (Background task, may take 5-10 minutes)
docker exec neo4j cypher-shell -u neo4j -p password "CALL db.indexes() YIELD populationPercent WHERE populationPercent < 100 RETURN *"

# Step 3: Clear and rebuild query cache
python -c "
from src.memory.query_optimization import QueryCache
cache = QueryCache(max_size=1000, ttl_seconds=3600)
cache.clear()
print('✅ Query cache cleared')
"

# Step 4: Re-run slow queries with new indexes
# Expected: 500ms → 50ms (10x improvement)
```

**Prevention:**
- Run `init_neo4j_indexes()` once during deployment
- Monitor `MetricsCollector.get_slow_queries()` regularly
- Enable query caching for read-heavy workloads
- Use pagination for large result sets

---

### Issue 6: Memory Exhaustion

**Symptom:** `OutOfMemoryException`, container killed, process exits

**Root Causes:**
- Large result sets without pagination
- Unbounded caches (query cache, audit buffer)
- Memory leaks in long-running agents
- Neo4j memory misconfiguration

**Diagnostics:**

```bash
# Monitor memory usage
docker stats artofiabox --stream=false

# Check for large objects in memory
python -c "
import sys
import gc
gc.collect()
objects = gc.get_objects()
large = [obj for obj in objects if sys.getsizeof(obj) > 1_000_000]
print(f'Objects >1MB: {len(large)}')
for obj in large[:5]:
    print(f'  - {type(obj).__name__}: {sys.getsizeof(obj) / 1_000_000:.1f}MB')
"

# Check Neo4j memory settings
docker exec neo4j cypher-shell -u neo4j -p password "CALL dbms.queryJmx('java.lang:type=Memory') YIELD attributes RETURN attributes"
```

**Remediation Steps:**

```python
# Option 1: Enable pagination for large queries
from src.memory.query_optimization import PaginationParams, PaginatedResult

pagination = PaginationParams(
    skip=0,
    limit=100,  # Process 100 at a time, not 100,000
    sort_by="created_at",
    sort_direction="DESC"
)
result = await query_with_pagination(query, pagination)

# Option 2: Limit cache sizes
from src.memory.query_optimization import QueryCache

# Reduce from 1000 to 100 if memory constrained
cache = QueryCache(max_size=100, ttl_seconds=300)  # Also reduce TTL

# Option 3: Increase Neo4j heap
# In docker-compose.yml:
services:
  neo4j:
    environment:
      NEO4J_dbms_memory_heap_maxSize: 4g  # Increase from 1g
      NEO4J_dbms_memory_pagecache_size: 2g

# Option 4: Monitor and evict
collector = MetricsCollector()
stats = collector.get_stats()
if stats['total_queries'] > 10000:  # Too many queries tracked
    collector.clear()  # Reset metrics
```

**Prevention:**
- Always use pagination for queries that might return >1000 items
- Set cache max_size based on available memory
- Monitor memory usage trends
- Implement automated alerts at 70-80% utilization

---

## Security & Validation

### Issue 7: Docker Command Validation Failures

**Symptom:** `CommandExecutionException` or `ValidationException` thrown

**Root Causes:**
- Command contains forbidden flags (`-c`, `--config`, etc.)
- Python module doesn't exist or is blacklisted
- Bash script file missing or contains dangerous commands
- Curl destination not in whitelist

**Diagnostics:**

```bash
# Check what was validated
python -c "
from src.orchestrator.supervisor import Supervisor
supervisor = Supervisor()

# Test command
cmd = 'python -m json.tool'
try:
    result = supervisor._validate_docker_command(cmd)
    print(f'✅ Valid: {result}')
except Exception as e:
    print(f'❌ Invalid: {e}')
"

# Run validation tests
python -m pytest tests/test_p0_fixes.py::TestDockerCommandValidation -v
```

**Remediation Steps:**

```bash
# Verify these P0 fixes are in place:

# 1. Check forbidden flags are checked FIRST
grep -n "forbidden_flags = \[" src/orchestrator/supervisor.py

# 2. Check ALLOWED_DOCKER_COMMANDS structure
grep -A 50 "ALLOWED_DOCKER_COMMANDS = {" src/orchestrator/supervisor.py | head -20

# 3. Test specific command
python -c "
from src.orchestrator.supervisor import ALLOWED_DOCKER_COMMANDS
print('Python allowed flags:', ALLOWED_DOCKER_COMMANDS['python']['allowed_flags'])
print('Python forbidden:', ALLOWED_DOCKER_COMMANDS['python']['forbidden_flags'])
"
```

**Prevention:**
- Whitelist only necessary Docker commands
- For Python: allow only `-m` flag, never `-c`
- For bash scripts: validate file exists, check content
- For curl: maintain URL/domain whitelist
- Test all command patterns before deployment

---

### Issue 8: Exception Hierarchy Misuse

**Symptom:** Generic `Exception` caught, lost error context, poor logging

**Root Causes:**
- Code not using typed exceptions
- Exception context not being captured
- Not using ErrorContext dataclass

**Diagnostics:**

```bash
# Find generic exception catches
grep -r "except Exception:" src/

# Find missing error context
grep -r "raise.*Exception()" src/

# Test exception hierarchy
python -m pytest tests/test_phase2_improvements.py::TestExceptionHierarchy -v
```

**Remediation Steps:**

```python
# ❌ BAD (before)
try:
    await supervisor.validate_action(action)
except Exception as e:
    logger.error(f"Error: {e}")

# ✅ GOOD (after)
from src.core.exceptions import (
    RateLimitException,
    ValidationException,
    ErrorContext
)

try:
    await supervisor.validate_action(action)
except RateLimitException as e:
    logger.error(f"Rate limit hit: {e.context.details}")
    # Can handle rate limits differently
except ValidationException as e:
    logger.warning(f"Validation failed: {e.context.details}")
    # Can handle validation failures differently
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise
```

**Prevention:**
- Use typed exceptions (RateLimitException, ValidationException, etc.)
- Always include ErrorContext with typed fields
- Make exception messages actionable (what failed and why)
- Test exception handling in unit tests

---

## Docker & Containers

### Issue 9: Container Crashes or Won't Start

**Symptom:** Container exits immediately, `docker compose up` fails

**Root Causes:**
- Port already in use
- Volume mount permission errors
- Docker daemon not running
- Invalid docker-compose.yml

**Diagnostics:**

```bash
# Check Docker daemon status
docker info

# Validate docker-compose.yml
docker compose config

# Check recent logs
docker compose logs --tail=50

# Check port availability
netstat -an | grep 7687  # Neo4j
netstat -an | grep 6379  # Redis (if used)

# PowerShell equivalent
Get-Process | Where-Object {$_.ProcessName -eq 'docker'}
```

**Remediation Steps:**

```bash
# Step 1: Clean shutdown
docker compose down
docker system prune -f

# Step 2: Check ports
# If port conflict, change in docker-compose.yml:
# ports:
#   - "7688:7687"  # Host:Container

# Step 3: Fix volume permissions (Linux/Mac)
sudo chown -R $(id -u):$(id -g) ./data

# Step 4: Rebuild images
docker compose build --no-cache

# Step 5: Start with verbose output
docker compose up

# Step 6: Check logs
docker logs artofiabox -f  # Follow logs
```

**Prevention:**
- Document port assignments
- Use named volumes instead of bind mounts when possible
- Never run containers as root
- Test docker-compose.yml with `docker compose config`

---

## Neo4j & Knowledge Graph

### Issue 10: Neo4j Connection Failures

**Symptom:** `ConnectionException`, timeout errors, "connection refused"

**Root Causes:**
- Neo4j container not running
- Port mapping incorrect
- Authentication failed
- Network isolation issues

**Diagnostics:**

```bash
# Test Neo4j connectivity
docker exec artofiabox python -c "
from neo4j import AsyncGraphDatabase
import asyncio

async def test():
    try:
        driver = AsyncGraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password'))
        async with driver.session() as session:
            result = await session.run('RETURN 1 as n')
            async for record in result:
                print(f'✅ Connected: {record[\"n\"]}')
        await driver.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test())
"

# Check Neo4j status
docker exec neo4j cypher-shell -u neo4j -p password "CALL dbms.components() YIELD versions RETURN versions"

# Check network
docker network ls
docker network inspect artofiabox_default
```

**Remediation Steps:**

```bash
# Step 1: Verify Neo4j is running
docker ps | grep neo4j

# Step 2: Check Neo4j logs
docker logs neo4j | tail -30

# Step 3: Test internal connectivity
docker exec artofiabox nc -zv neo4j 7687

# Step 4: Restart Neo4j
docker restart neo4j

# Step 5: Wait for startup (30-60 seconds required)
sleep 60

# Step 6: Re-test connection
docker exec artofiabox python -c "from neo4j import AsyncGraphDatabase; ..."

# Step 7: If still failing, reset Neo4j
docker exec neo4j rm -rf /var/lib/neo4j/data/transactions*
docker restart neo4j
```

**Prevention:**
- Always wait for Neo4j before starting agents
- Use health checks in docker-compose.yml
- Monitor connection pool exhaustion
- Log connection failures with full context

---

## Recovery Procedures

### Full System Recovery

**When to use:** After major failures, data corruption, or deployment issues

```bash
# Step 1: Stop all services
docker compose down

# Step 2: Remove all data (⚠️ DATA LOSS)
docker compose down -v
rm -rf ./data/*

# Step 3: Git reset to known good state
git status  # Check for uncommitted changes
git log --oneline -5  # Find good commit
git reset --hard <commit_hash>  # Reset to known good

# Step 4: Rebuild from scratch
docker compose build --no-cache

# Step 5: Start services
docker compose up -d

# Step 6: Wait for services
sleep 60

# Step 7: Re-initialize
python -c "
from src.orchestrator.main_integration import OrchestratorIntegration
import asyncio
orch = OrchestratorIntegration()
result = asyncio.run(orch.initialize())
print(f'Initialization: {result}')
"

# Step 8: Run tests
python -m pytest tests/test_p0_fixes.py -v
python -m pytest tests/test_phase2_improvements.py -v
python -m pytest tests/test_phase3_performance.py -v
```

### Backup and Restore

```bash
# Backup Neo4j
docker exec neo4j neo4j-admin dump --database=neo4j --to=/var/lib/neo4j/backups/backup.dump
docker cp neo4j:/var/lib/neo4j/backups/backup.dump ./backup.dump

# Backup audit buffer
python -c "
from src.orchestrator.memory_manager import MemoryManager
import json
mm = MemoryManager()
with open('audit_backup.json', 'w') as f:
    json.dump(mm.audit_buffer, f)
"

# Restore Neo4j
docker exec neo4j neo4j-admin load --from-path=/var/lib/neo4j/backups/ --database=neo4j
docker restart neo4j

# Restore audit buffer
python -c "
import json
from src.orchestrator.memory_manager import MemoryManager
mm = MemoryManager()
with open('audit_backup.json', 'r') as f:
    mm.audit_buffer = json.load(f)
"
```

---

## Escalation

### When to Escalate to Engineering

| Symptom | Severity | Action |
|---------|----------|--------|
| Initialization fails with all components | CRITICAL | Stop operations, escalate immediately |
| Data loss in audit buffer | CRITICAL | Page on-call, preserv logs |
| Cypher injection detected | CRITICAL | Isolate system, security team |
| Memory exhaustion recurring | HIGH | Increase resources or reduce load |
| Query latency >2000ms | HIGH | Investigate indexes, escalate if not resolved in 1h |
| Intermittent connection failures | MEDIUM | Gather logs, check network |
| Rate limiting blocking legitimate traffic | MEDIUM | Analyze patterns, adjust limits |

### Logging Escalation

```python
import logging
from src.orchestrator.logging_context import LogContext, setup_logging_context

setup_logging_context()
logger = logging.getLogger(__name__)

# Critical incident
async with LogContext(operation_id="escalation_001"):
    logger.critical("CRITICAL: System component failed", extra={
        "component": "neo4j",
        "attempted_recovery": False,
        "manual_intervention_required": True,
        "escalation_contact": "sre-oncall@team.dev"
    })
```

---

## Appendix: Useful Commands

```bash
# Quick status check
docker compose ps && echo "---" && docker stats --no-stream

# Run all tests
python -m pytest tests/ -v --tb=short

# Linting and formatting
black src/ tests/ scripts/
pylint src/ --fail-under=8.0
mypy src/ --ignore-missing-imports

# Git maintenance
git status
git log --oneline -10
git diff HEAD~1

# Database inspection
docker exec neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN COUNT(n) as nodes"
docker exec neo4j cypher-shell -u neo4j -p password "CALL db.indexes()"

# Agent diagnostics
docker logs artofiabox -f  # Follow logs
docker exec artofiabox ps aux  # Running processes
docker exec artofiabox df -h  # Disk space
```

---

**Last Reviewed:** 2026-04-16  
**Next Review:** 2026-07-16 (quarterly)  
**Maintained By:** SRE Team  
**Escalation:** sre-oncall@team.dev
