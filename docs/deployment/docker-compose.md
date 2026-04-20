# Docker Compose Deployment Guide

**Location:** Root & `docker-compose.yml`  
**Purpose:** Local development & production deployment setup

---

## 🚀 Quick Start

### Prerequisites
```bash
# Docker & Docker Compose
docker --version        # Must be 20.10+
docker-compose --version # Must be 2.0+

# Python (for client tools)
python --version        # Must be 3.10+
```

### Start System
```bash
# Navigate to project root
cd /path/to/ArtOfIAV2

# Start all services
docker-compose up -d

# Verify services
docker-compose ps

# Check logs
docker-compose logs -f
```

### Stop System
```bash
docker-compose down

# Remove volumes (full cleanup)
docker-compose down -v
```

---

## 🏗️ Service Architecture

**5 Services (as defined in docker-compose.yml):**

```
┌─────────────────────────────────────────────────┐
│                ORCHESTRATOR                     │
│         (Main API & Coordination)               │
│         Port: 8000                              │
└──────────┬──────────────────────────────────────┘
           │
    ┌──────┼──────┬──────────┬──────────┐
    │      │      │          │          │
    ▼      ▼      ▼          ▼          ▼
  NEO4J PGDB REDIS SANDBOX SANDBOX
  (KG)  (Vec)  (Cache)(Exec) (Exec)
  
Port Port Ports  Docker  Docker
7474 5432 6379  Auto    Auto
```

### Service Details

| Service | Purpose | Port | Image |
|---------|---------|------|-------|
| **Orchestrator** | API & Coordination | 8000 | custom |
| **Neo4j** | Knowledge Graph | 7474 | neo4j:5.0 |
| **PostgreSQL** | Vector DB | 5432 | postgres:15 |
| **Redis** | Caching/Queue | 6379 | redis:7.0 |
| **Sandbox (x2)** | Ephemeral Execution | - | custom |

---

## 📖 Full Configuration

### docker-compose.yml Structure

```yaml
version: '3.8'

services:
  orchestrator:
    # API server (this process)
    image: artofiabox:orchestrator
    ports:
      - "8000:8000"
    environment:
      - NEO4J_HOST=neo4j
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - neo4j
      - postgres
      - redis
    networks:
      - artofianet
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs

  neo4j:
    # Knowledge Graph Database
    image: neo4j:5.0-enterprise
    ports:
      - "7474:7474"    # HTTP
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/var/lib/neo4j/data
    networks:
      - artofianet

  postgres:
    # Vector Database with pgvector
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=artofiadb
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d
    networks:
      - artofianet

  redis:
    # In-memory Cache & Message Queue
    image: redis:7.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - artofianet

  sandbox:
    # Ephemeral execution environment
    image: artofiabox:sandbox
    build:
      context: .
      dockerfile: src/backends/docker_sandbox/Dockerfile.ephemeral
    networks:
      - artofianet
    # Usually created dynamically, not persistent

volumes:
  neo4j_data:
  postgres_data:
  redis_data:

networks:
  artofianet:
    driver: bridge
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```bash
# Database
NEO4J_PASSWORD=secure_password_here
POSTGRES_PASSWORD=secure_password_here

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
OLLAMA_URL=http://localhost:11434

# Security
JWT_SECRET=very_secure_random_string
API_KEY=very_secure_random_string

# Sandbox
SANDBOX_TIMEOUT=60
SANDBOX_MEMORY_LIMIT=512M
SANDBOX_CPU_LIMIT=1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### .env.sample (Template)
```bash
# Copy this to .env and fill in values
NEO4J_PASSWORD=
POSTGRES_PASSWORD=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_URL=http://localhost:11434
JWT_SECRET=
API_KEY=
SANDBOX_TIMEOUT=60
SANDBOX_MEMORY_LIMIT=512M
LOG_LEVEL=INFO
```

---

## 🚀 Common Tasks

### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator

# Last 50 lines
docker-compose logs --tail 50 orchestrator
```

### Access Service Shells
```bash
# PostgreSQL shell
docker-compose exec postgres psql -U postgres -d artofiadb

# Neo4j shell
docker-compose exec neo4j bash

# Orchestrator shell
docker-compose exec orchestrator bash
```

### Restart a Service
```bash
docker-compose restart orchestrator
```

### Rebuild Images
```bash
docker-compose build --no-cache
```

### Full Reset
```bash
# Stop and remove everything
docker-compose down -v

# Rebuild and start
docker-compose up -d
```

---

## 🧪 Verification

### Health Check Script
```bash
#!/bin/bash
# Check all services

echo "Checking Orchestrator..."
curl http://localhost:8000/health

echo "Checking Neo4j..."
curl http://localhost:7474

echo "Checking PostgreSQL..."
docker-compose exec postgres pg_isready

echo "Checking Redis..."
docker-compose exec redis redis-cli ping

echo "All checks complete!"
```

### Verify Database Connectivity
```bash
# From orchestrator container
docker-compose exec orchestrator python -c "
import asyncpg
import asyncpg
loop = asyncio.get_event_loop()
conn = loop.run_until_complete(asyncpg.connect('postgres://postgres:password@postgres:5432/artofiadb'))
print('✅ PostgreSQL connected')
"
```

---

## 📊 Performance Tuning

### PostgreSQL Optimization
**In `docker-compose.yml`:**
```yaml
postgres:
  command:
    - 'postgres'
    - '-c'
    - 'shared_buffers=256MB'
    - '-c'
    - 'max_connections=200'
    - '-c'
    - 'work_mem=50MB'
```

### Neo4j Optimization
```yaml
neo4j:
  environment:
    - NEO4J_heap__InitialHeapSize=2g
    - NEO4J_heap__MaxHeapSize=2g
    - NEO4J_server__memory__heap__max__size=2g
```

### Redis Optimization
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

---

## 🔒 Security Hardening

### Production Checklist
- [ ] Change all default passwords
- [ ] Use environment variables (never hardcode)
- [ ] Enable authentication on all services
- [ ] Use network policies (restrict access)
- [ ] Enable SSL/TLS for external connections
- [ ] Set resource limits (memory, CPU)
- [ ] Enable logging and monitoring
- [ ] Regular security updates

### Network Isolation
```yaml
networks:
  artofianet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Resource Limits
```yaml
orchestrator:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs orchestrator

# Check if port is in use
lsof -i :8000

# Start with verbose output
docker-compose -f docker-compose.yml up orchestrator
```

### Connection Refused Errors
```bash
# Verify services are running
docker-compose ps

# Restart services
docker-compose restart

# Check network connectivity
docker network ls
docker network inspect artofianet
```

### Database Issues
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -h postgres

# Check Neo4j
docker-compose exec neo4j bin/neo4j-admin check-consistency

# Reset databases
docker-compose down -v
docker-compose up -d
```

### Out of Memory
```bash
# Check disk space
df -h

# Check memory
docker stats

# Try cleanup
docker system prune -a
docker volume prune
```

---

## 🔄 Backup & Restore

### Backup Databases
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U postgres artofiadb > backup.sql

# Neo4j backup
docker-compose exec neo4j bin/neo4j-admin backup --backup-dir=/backups

# Full volume backup
docker run --rm -v /path/to/volumes -v /path/to/backup \
  alpine tar czf /path/to/backup/backup.tar.gz -C /path/to/volumes .
```

### Restore Databases
```bash
# PostgreSQL restore
docker-compose exec -T postgres psql -U postgres artofiadb < backup.sql

# Neo4j restore
docker-compose exec neo4j bin/neo4j-admin restore --from-path=/backups
```

---

## 📈 Scaling Up

### For Production (Kubernetes)
See: [../kubernetes.md](kubernetes.md)

### For High Load (Multiple Workers)
```yaml
orchestrator:
  deploy:
    replicas: 3  # Multiple instances

postgres:
  deploy:
    placement:
      constraints:
        - node.labels.storage == fast
```

---

## 🎯 Next Steps

1. ✅ Start: `docker-compose up -d`
2. ✅ Verify: `docker-compose ps`
3. ✅ Test: `curl http://localhost:8000/health`
4. ✅ Use: Connect your clients to `localhost:8000`
5. ✅ Monitor: `docker-compose logs -f`

---

## 📞 Support

- **All services down?** → Restart: `docker-compose restart`
- **Database error?** → Check logs: `docker-compose logs postgres`
- **Performance issue?** → Check resources: `docker stats`
- **Full reset?** → `docker-compose down -v && docker-compose up -d`

---

**Last Updated:** 2026-04-16  
**Docker Compose Version:** 2.0+  
**Status:** Production Ready ✅

