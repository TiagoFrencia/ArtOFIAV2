# Deployment & Infrastructure Documentation

**Location:** `/docs/deployment/`  
**Purpose:** Docker, deployment guides, infrastructure setup, and production configuration

## 📋 Contents

### Infrastructure Setup
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - General deployment guide
- **[SETUP_DEVOPS.md](SETUP_DEVOPS.md)** - DevOps setup procedures
- **[SETUP_TECH_LEAD.md](SETUP_TECH_LEAD.md)** - Tech lead setup guide
- **[SETUP_SENIOR_BACKEND_1.md](SETUP_SENIOR_BACKEND_1.md)** - Senior backend setup
- **[docker-compose.md](docker-compose.md)** - Docker Compose configuration ✅ NEW

### Production & Operations
- **[PRODUCTION_DEPLOYMENT_HUB.md](PRODUCTION_DEPLOYMENT_HUB.md)** - Production deployment hub
- **[OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)** - Day-to-day operations guide
- **[DELIVERY_MANIFEST.md](DELIVERY_MANIFEST.md)** - Delivery checklist and manifest
- **[DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)** - Delivery summary report

---

## 🚀 Quick Start

### First Time Setup
1. Read: [SETUP_DEVOPS.md](SETUP_DEVOPS.md) - Complete setup guide
2. Configure: Docker environment and dependencies
3. Deploy: Using [docker-compose.md](docker-compose.md)
4. Verify: Health checks in [..operators/quick_start.md](../operators/quick_start.md)

### Production Deployment
1. Review: [PRODUCTION_DEPLOYMENT_HUB.md](PRODUCTION_DEPLOYMENT_HUB.md)
2. Checklist: [DELIVERY_MANIFEST.md](DELIVERY_MANIFEST.md)
3. Deploy: Follow [DEPLOYMENT.md](DEPLOYMENT.md)
4. Monitor: [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md)

---

## 👥 By Role

| Role | Start With |
|------|-----------|
| **DevOps Engineer** | [SETUP_DEVOPS.md](SETUP_DEVOPS.md) → [docker-compose.md](docker-compose.md) |
| **Tech Lead** | [SETUP_TECH_LEAD.md](SETUP_TECH_LEAD.md) → [DEPLOYMENT.md](DEPLOYMENT.md) |
| **Senior Backend** | [SETUP_SENIOR_BACKEND_1.md](SETUP_SENIOR_BACKEND_1.md) |
| **Operations** | [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) |
| **Manager** | [DELIVERY_MANIFEST.md](DELIVERY_MANIFEST.md) |

---

## 🔧 Key Configuration Files

**docker-compose.yml Architecture:**
- Orchestrator (main service)
- Neo4j (knowledge graph database)
- PostgreSQL (persistent memory)
- Redis (cache layer)
- Ephemeral sandbox (exploit isolation)

See [docker-compose.md](docker-compose.md) for full configuration and troubleshooting.

---

## 💡 Common Tasks

| Task | Document |
|------|----------|
| Initial system setup | SETUP_DEVOPS.md |
| Deploy to production | DEPLOYMENT.md |
| Run health checks | PRODUCTION_DEPLOYMENT_HUB.md |
| Monitor operations | OPERATIONS_GUIDE.md |
| Pre-deployment checklist | DELIVERY_MANIFEST.md |
| Docker configuration | docker-compose.md |

---

## 📞 Related Documentation

- **Operations:** [../operators/](../operators/)
- **Development:** [../developers/](../developers/)
- **Main Hub:** [../README.md](../README.md)
- **Planning:** [../planning/](../planning/)

---

**Last Updated:** 2026-04-16  
**Status:** Organized during v1.3 documentation migration  
**Key Addition:** docker-compose.md with complete infrastructure guide

