# Operations & Red Teaming Documentation

**Location:** `/docs/operators/`  
**Purpose:** Red teaming operations, troubleshooting, integration guides, and operational procedures

## 📋 Contents

### Operations & Troubleshooting
- **[quick_start.md](quick_start.md)** - Quick start for red teamers
- **[OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)** - Day-to-day operations
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and fixes

### Integration Guides
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Integration overview
- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Integration summary
- **[INTEGRATION_BACKENDS_GUIDE.md](INTEGRATION_BACKENDS_GUIDE.md)** - Backend integration

---

## 🔍 By Use Case

### First-Time Setup (30 minutes)
1. **[quick_start.md](quick_start.md)** - Red teaming quickstart
2. **[OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)** - Running operations
3. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - If something breaks

### Integration & Backend Setup (1-2 hours)
1. **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Architecture overview
2. **[INTEGRATION_BACKENDS_GUIDE.md](INTEGRATION_BACKENDS_GUIDE.md)** - Backend systems
3. **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Verify integration

### Running Operations (Daily)
- **Reference:** [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)
- **Check Status:** Health checks in quick_start.md
- **Issue Resolution:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 👥 Audience

| Role | Start Here |
|------|-----------|
| **Red Teamer** | [quick_start.md](quick_start.md) |
| **Security Operator** | [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) |
| **System Administrator** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| **DevOps Integrating** | [INTEGRATION_BACKENDS_GUIDE.md](INTEGRATION_BACKENDS_GUIDE.md) |
| **Architect** | [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) |

---

## 🛠️ Common Operations

### Starting Operations
```bash
# See: quick_start.md
docker-compose up -d
python src/orchestrator/server.py
```

### Checking Status
```bash
# See: OPERATIONS_GUIDE.md
docker-compose ps
curl http://localhost:8000/health
```

### Troubleshooting Issues
```bash
# See: TROUBLESHOOTING.md
# Common issues: memory, connections, permissions
# Solutions documented in guide
```

---

## 📋 Integration Matrix

| Backend | Setup | Integration Guide | Status |
|---------|-------|------------------|--------|
| **Neo4j Graph** | docs/deployment/ | INTEGRATION_BACKENDS_GUIDE.md | ✅ |
| **PostgreSQL** | docs/deployment/ | INTEGRATION_BACKENDS_GUIDE.md | ✅ |
| **pgVector** | docs/deployment/ | INTEGRATION_BACKENDS_GUIDE.md | ✅ |
| **LLM Providers** | docs/deployment/ | INTEGRATION_BACKENDS_GUIDE.md | ✅ |
| **Docker Sandbox** | docs/deployment/ | INTEGRATION_BACKENDS_GUIDE.md | ✅ |

---

## 📞 Related Documentation

- **Deployment & Setup:** [../deployment/](../deployment/)
- **Development:** [../developers/](../developers/)
- **Main Hub:** [../README.md](../README.md)
- **Planning:** [../planning/](../planning/)

---

**Last Updated:** 2026-04-16  
**Status:** Organized during v1.3 documentation migration  
**Key Features:** Red teaming workflows, troubleshooting guides, integration procedures

