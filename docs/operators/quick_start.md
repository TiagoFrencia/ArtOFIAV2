# 🎯 Operators Quick Start Guide

**For Red Teamers and Penetration Testers using ArtOfIAV2.**

---

## Your First Operation (Step-by-Step)

### Phase 1: Reconnaissance

```python
import asyncio
from src.agents.recon_agent.server import ReconAgentServer
from src.core.input_validator import ValidationResult

# Initialize recon agent
recon = ReconAgentServer()

# Define target
target = {
    "host": "target.example.com",
    "port": 443,
    "protocol": "https"
}

# Run passive scanning
findings = asyncio.run(recon.scan_passive(target))

print("Vulnerabilities Found:")
for vuln in findings.get("vulnerabilities", []):
    print(f"  - {vuln['type']}: {vuln['description']}")
```

**Output Example:**
```
Vulnerabilities Found:
  - jwt_weakness: HS256 algorithm with weak secret
  - sqli: Unvalidated parameter in /api/users
  - xss: Reflected XSS in search parameter
```

### Phase 2: Planning

```python
from src.agents.logic_agent.server import LogicAgentServer

# Initialize logic agent
logic = LogicAgentServer()

# Generate attack chain
plan = asyncio.run(logic.plan_attack({
    "target": target,
    "findings": findings,
    "objective": "gain_admin_access"
}))

print("Attack Plan:")
for i, step in enumerate(plan.get("steps", []), 1):
    print(f"{i}. {step['description']}")
    print(f"   Success Rate: {step['success_rate']}%")
```

**Output Example:**
```
Attack Plan:
1. Capture JWT from /api/auth endpoint
   Success Rate: 90%
2. Crack HS256 secret using dictionary
   Success Rate: 75%
3. Forge admin token
   Success Rate: 95%
4. Use forged token to access /api/admin
   Success Rate: 98%
```

### Phase 3: Exploitation

```python
from src.agents.exploit_agent.executor import ExploitExecutor, ExploitContext, VulnerabilityType

# Initialize exploit agent
executor = ExploitExecutor()

# Prepare context
context = ExploitContext(
    target_url=target["host"],
    vulnerability_type=VulnerabilityType.JWT_WEAKNESS,
    strategy="stealth",
    endpoint="/api/auth",
    http_method="POST"
)

# Execute
result = asyncio.run(executor.exploit(context))

if result.success:
    print(f"✅ Exploitation Successful!")
    print(f"   Response Code: {result.response_code}")
    print(f"   Data Extracted: {result.extraction_data}")
else:
    print(f"❌ Exploitation Failed: {result.error_message}")
```

**Output Example:**
```
✅ Exploitation Successful!
   Response Code: 200
   Data Extracted: {
     "admin_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "user_id": "admin",
     "permissions": ["read", "write", "delete"]
   }
```

### Phase 4: Post-Exploitation

```python
from src.agents.logic_agent.post_exploit import PostExploitationPlanner

# Initialize post-exploit planner
post_exploit = PostExploitationPlanner()

# Generate further steps
next_steps = asyncio.run(post_exploit.plan({
    "current_access": result,
    "target": target
}))

print("Post-Exploitation Steps:")
for step in next_steps:
    print(f"  - {step}")
```

---

## Common Operations

### Scan for Vulnerabilities

```bash
# Comprehensive passive scan
python scripts/scan.py --target example.com --output report.json

# Specific vulnerability type
python scripts/scan.py --target example.com --vuln-type jwt,sqli

# Export findings
python scripts/scan.py --target example.com --format html
```

### Generate Attack Report

```bash
# Create detailed report
python scripts/generate-report.py --scan report.json --format pdf

# Include remediation
python scripts/generate-report.py --scan report.json --include-remediation
```

### Run Full Operation

```bash
# End-to-end operation
python scripts/run-operation.py \
  --target example.com \
  --objective admin_access \
  --output operation-report.json
```

---

## Best Practices

### ✅ DO

- **Validate targets** before running exploits
- **Use stealth strategy** on production systems
- **Review plan** before execution
- **Monitor resource usage** (sandbox containers)
- **Archive reports** with timestamps
- **Test on staging** first

### ❌ DON'T

- **Run exploits without authorization**
- **Skip planning phase** (improves accuracy)
- **Use aggressive strategy** in production
- **Ignore audit logs**
- **Modify core modules** (use plugins instead)
- **Leave shells open** after completion

---

## Troubleshooting

### "Exploitation Failed: Timeout"

Target may beusing WAF. Try:
```python
context.evasion_techniques.append("browser_emulation")
context.strategy = ExploitStrategy.STEALTH
```

### "Permission Denied: Sandbox"

Check Docker permissions:
```bash
docker ps  # Must work without errors
groups $USER  # Must include 'docker'
```

### "LLM Provider Down"

System automatically fallback to next provider (OpenAI → Claude → Ollama).

Check status:
```python
from src.backends.llm_providers import ProviderManager
manager = ProviderManager()
print(manager.get_provider_status())
```

---

## Advanced Configurations

### Custom Evasion Techniques

```python
context.evasion_techniques = [
    "browser_emulation",
    "proxy_rotation",
    "jitter_injection",
    "user_agent_rotation"
]
```

### Target-Specific Configurations

```python
context.framework_detected = "Flask"  # Skip certain checks
context.defenses = ["WAF", "Rate Limiting"]  # Plan around
context.payload_hints = ["use_unicode_encoding"]  # Bypass filters
```

### Performance Tuning

```python
# Parallel exploitation of multiple vulns
results = asyncio.run(executor.batch_exploit([
    context_1, context_2, context_3
], max_concurrent=3))
```

---

## Reporting

### Generate HTML Report

```bash
python scripts/generate-report.py \
  --findings findings.json \
  --format html \
  --output report.html \
  --include-screenshots
```

### Export for Compliance

```python
from src.orchestrator.memory_manager import MemoryManager

memory = MemoryManager()
audit_trail = memory.export_audit_trail(
    format="json",
    include_reasoning=True,
    include_sensitive_data=False  # GDPR
)
```

---

## Next Steps

- [Review security best practices](../architecture/security.md)
- [Setup your first scan](GETTING_STARTED.md)
- [Configure custom evasion](evasion_techniques.md)
- [Join operator community](../support/)

