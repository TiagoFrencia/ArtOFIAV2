# 🚀 Getting Started with ArtOfIAV2

**Get up and running in 5 minutes.**

---

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Git

## Installation

### 1. Clone Repository

```bash
git clone <repo-url>
cd ArtOfIAV2
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy template
cp .env.sample .env

# Edit .env with your API keys
nano .env
```

**Required variables:**
- `OPENAI_API_KEY` - For GPT-4 access
- `ANTHROPIC_API_KEY` - For Claude fallback
- `NEO4J_PASSWORD` - Database password
- `DB_PASSWORD` - PostgreSQL password

### 4. Start Infrastructure

```bash
# Start Docker services (PostgreSQL, Neo4j, Redis, Browserless, Docker-in-Docker)
docker compose up -d

# Verify all services are running
docker compose ps
```

Expected output:
```
NAME                    STATUS
artofia_pgvector        Up
artofia_graph           Up
artofia_redis           Up
artofia_browser         Up
artofia_dind            Up
```

### 5. Initialize System

```bash
# Run quick test
python src/orchestrator/examples_quick_start.py
```

Expected output:
```
✓ Orchestrator loaded
✓ Backend Integration initialized
✓ System operational
```

---

## Your First Operation

### Step 1: Connect to System

```python
from src.orchestrator.main_integration import IntegratedArtOfIA

# Initialize
system = IntegratedArtOfIA()
asyncio.run(system.initialize())
```

### Step 2: Define Target

```python
target = {
    "name": "Test API",
    "url": "http://target.example.com",
    "findings_from_recon": [
        "jwt_weakness",
        "sql_injection",
        "xss"
    ]
}
```

### Step 3: Run Operation

```python
result = asyncio.run(system.run_full_red_team_operation(target))
print(f"Operation Status: {result['result']}")
```

---

## Common Commands

### Check System Status

```bash
# View active services
docker compose ps

# View logs
docker compose logs -f orchestrator

# Access databases
docker exec -it artofia_graph bash  # Neo4j
docker exec -it artofia_pgvector psql -U agent  # PostgreSQL
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Orchestrator tests only
pytest tests/test_orchestrator_core.py -v --tb=short

# With coverage
pytest tests/ --cov=src
```

### Stop System

```bash
# Graceful shutdown
docker compose down

# Full cleanup (including data)
docker compose down -v
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'asyncpg'"

```bash
pip install asyncpg==0.29.0
```

### "Docker permission denied"

```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Requires logout/login or:
newgrp docker
```

### "Port already in use"

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "5432:5432"  # Change first number if in use
```

---

## Next Steps

1. [Read Architecture Overview](architecture/overview.md)
2. [Review Operators Guide](operators/quick_start.md)
3. [Setup Development Environment](developers/setup.md)
4. [Configure Production Deployment](../DEPLOYMENT.md)

---

**Stuck?** See [Troubleshooting](TROUBLESHOOTING.md) or open an [issue](https://github.com/your-repo/issues).

