# 📚 ArtOfIAV2 Documentation Hub

**Welcome to the ArtOfIAV2 Enterprise Red Team System documentation.**  
**Complete Navigation | All Roles Supported | Organized by Purpose**

> **Quick Entry:** [5-Min Start](#-getting-started) | [By Role](#-by-role) | [All Docs](#-all-documentation) | [Search](../DOCUMENTATION_MAP.md)

---

## 👥 By Role

**Choose your role for relevant documentation:**

| Role | Start Here | Time | What You'll Learn |
|------|-----------|------|-----------------|
| **🎯 Red Teamer/Operator** | [operators/quick_start.md](operators/quick_start.md) | 15 min | Run operations, exploit workflows |
| **🏗️ Developer** | [developers/code-structure.md](developers/code-structure.md) | 20 min | Code organization, testing patterns |
| **🔧 DevOps/Infrastructure** | [deployment/docker-compose.md](deployment/docker-compose.md) | 20 min | Setup, Docker, deployment |
| **📋 Project Manager** | [../EXECUTIVE_SUMMARY.md](../EXECUTIVE_SUMMARY.md) | 10 min | Project status, progress, metrics |
| **🏢 Executive/Leadership** | [../START_HERE.md](../START_HERE.md) | 5 min | Overview, key information |

---

## 🚀 Getting Started (5 Minutes)

**New to ArtOfIAV2?** Quick start:

1. **[START_HERE.md](../START_HERE.md)** - 5-min overview for everyone
2. **[GETTING_STARTED.md](GETTING_STARTED.md)** - Installation & quickstart
3. **Pick your role above** ↑ and follow the path

---

## 📁 All Documentation

### **Planning & Roadmap** (`planning/`)
Strategic planning, timelines, and execution guides.  
→ [planning/INDEX.md](planning/INDEX.md) | [12 documents](planning/)

**Quick Links:**
- [Project Status](planning/PROJECT_STATE_SUMMARY.md)
- [Action Plan](planning/ACTION_PLAN.md)
- [Implementation Roadmap](planning/IMPLEMENTATION_ROADMAP.md)
- [Week 1 Guide](planning/WEEK1_EXECUTION_GUIDE.md)

---

### **Deployment & Infrastructure** (`deployment/`)
Docker, deployment guides, infrastructure setup, and production configuration.  
→ [deployment/INDEX.md](deployment/INDEX.md) | [10 documents](deployment/)

**Quick Links:**
- [Docker Compose Setup](deployment/docker-compose.md) ✅ NEW
- [General Deployment](deployment/DEPLOYMENT.md)
- [DevOps Setup](deployment/SETUP_DEVOPS.md)
- [Operations Guide](deployment/OPERATIONS_GUIDE.md)
- [Production Hub](deployment/PRODUCTION_DEPLOYMENT_HUB.md)

---

### **Operations & Red Teaming** (`operators/`)
Red teaming workflows, troubleshooting, and integration guides.  
→ [operators/INDEX.md](operators/INDEX.md) | [6 documents](operators/)

**Quick Links:**
- [Red Teamer Quick Start](operators/quick_start.md)
- [Operations Guide](operators/OPERATIONS_GUIDE.md)
- [Troubleshooting](operators/TROUBLESHOOTING.md)
- [Integration Guide](operators/INTEGRATION_GUIDE.md)

---

### **Development & Architecture** (`developers/`)
Code structure, testing patterns, and technical deep dives.  
→ [developers/INDEX.md](developers/INDEX.md) | [10 documents](developers/)

**Quick Links:**
- [Code Structure Guide](developers/code-structure.md) ✅ NEW
- [Testing Guide](developers/testing-guide.md) ✅ NEW
- [Backend Documentation](developers/BACKENDS_DOCUMENTATION.md)
- [Code Review Standards](developers/SENIOR_CODE_REVIEW.md)

---

### **Improvements & Session Reports** (`improvements/`)
Session improvements, progress tracking, and quality metrics.  
→ [improvements/INDEX.md](improvements/INDEX.md) | [Session history](improvements/)

**Latest Session:**
- [Session v1.3 Complete Report](improvements/session-v1.3.md) ✅ Latest
- [Improvements Index](improvements/INDEX.md)

---

### **Archived Documentation** (`archived/`)
Historical analysis, legacy documentation, and reference materials.  
→ [archived/INDEX.md](archived/INDEX.md) | [9 documents](archived/)

**For Reference:**
- Exhaustive project analysis
- Senior reviews and assessments
- Before/after comparisons
- Historical reports

---

## 🏛️ Architecture & Design

**System Overview:**
- [System Architecture](architecture/overview.md) - 3-layer design
- [Data Flow Examples](developers/code-structure.md#data-flow) - JWT exploitation walkthrough
- [Security Model](architecture/overview.md#security) - Sandbox, validation, auditing

**Key Components:**
- **Agents:** Recon, Logic, Exploit agents (autonomous reasoning)
- **Backends:** Neo4j, PostgreSQL, pgvector, LLM providers, Docker sandbox
- **Core:** Orchestrator, security validation, memory management

---

## 🎯 Common Tasks

| Task | Time | Document |
|------|------|----------|
| **👤 First-time setup** | 30 min | [deployment/SETUP_DEVOPS.md](deployment/SETUP_DEVOPS.md) |
| **🚀 Deploy to production** | 1-2 hours | [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md) |
| **🔍 Run a red team operation** | 15 min | [operators/quick_start.md](operators/quick_start.md) |
| **🐛 Fix a bug** | 30 min | [developers/code-structure.md](developers/code-structure.md) + [developers/testing-guide.md](developers/testing-guide.md) |
| **📝 Understand code** | 45 min | [developers/code-structure.md](developers/code-structure.md) |
| **🧪 Write tests** | 30 min | [developers/testing-guide.md](developers/testing-guide.md) |
| **❌ Troubleshoot issues** | 15 min | [operators/TROUBLESHOOTING.md](operators/TROUBLESHOOTING.md) |
| **📊 Check system health** | 2 min | `python QUICK_HEALTH_CHECK.py` (root) |

---

## 🔍 Quick Navigation Index

**All documentation linked from:**
- [DOCUMENTATION_MAP.md](../DOCUMENTATION_MAP.md) - Master index with all 60+ documents
- [START_HERE.md](../START_HERE.md) - Role-specific quick starts (Red Teamer, Developer, Admin, Auditor)
- Each category's INDEX.md file (planning, deployment, operators, developers, etc.)

---

## 📊 Documentation Stats

| Category | Documents | Status | Key Addition |
|----------|-----------|--------|---|
| **Planning** | 12 | ✅ Complete | Roadmaps, timelines |
| **Deployment** | 10 | ✅ Complete | Docker Compose guide |
| **Operations** | 6 | ✅ Complete | Red teaming workflows |
| **Development** | 10+ | ✅ Complete | Code structure + testing guides |
| **Improvements** | Sessions | 🔄 Growing | v1.3 reports |
| **Archived** | 9 | 📦 Reference | Historical analysis |
| **TOTAL** | **60+** | ✅ **Organized** | Fully navigable |

---

## ⭐ What's New (v1.3)

**Documentation Enhancements:**
- ✅ **docs/developers/code-structure.md** - Complete src/ organization guide
- ✅ **docs/developers/testing-guide.md** - Testing patterns reference
- ✅ **docs/deployment/docker-compose.md** - Production Docker setup
- ✅ **docs/DOCUMENTATION_MAP.md** - Master navigation index
- ✅ **Complete reorganization** - 51+ files moved to proper categories

**Code Improvements:**
- ✅ 150+ comprehensive tests
- ✅ ConfigLoader module (SRP pattern)
- ✅ AST-based input validation
- ✅ Memory leak fixes
- ✅ Type safety enforced (MyPy strict)

**Rating Progress:** 7.2→8.9/10 (+24%)

**Full Report:** [improvements/session-v1.3.md](improvements/session-v1.3.md)

---

## 📞 Documentation Categories at a Glance

```
Root Level (Quick Access):
├── START_HERE.md (5 min overview - for all roles)
├── EXECUTIVE_SUMMARY.md (for leadership)
└── DOCUMENTATION_MAP.md (master index)

/docs/ (Organized by Purpose):
├── planning/ (roadmaps, timelines)
├── deployment/ (setup, docker, infra)
├── operators/ (red teaming, operations)
├── developers/ (code, testing, architecture)
├── improvements/ (sessions, reports)
└── archived/ (historical, reference)

/docs/architecture/ (System Design):
└── overview.md (with visuals and data flow)
```

---

## 🔗 Important Resources

| Resource | Link | Purpose |
|----------|------|---------|
| **Project Status** | [planning/PROJECT_STATE_SUMMARY.md](planning/PROJECT_STATE_SUMMARY.md) | Current state |
| **Latest Session** | [improvements/session-v1.3.md](improvements/session-v1.3.md) | This session's work |
| **Quick Health Check** | `python ../QUICK_HEALTH_CHECK.py` | System verification |
| **Full Validation** | `python ../VALIDATION_SUITE.py` | Comprehensive check |
| **Main Navigation** | [../DOCUMENTATION_MAP.md](../DOCUMENTATION_MAP.md) | All documents listed |

---

## ✨ Getting Help

**I'm looking for:**
- **Quick overview** → [START_HERE.md](../START_HERE.md)
- **Role-specific guide** → See [By Role section](#-by-role) above
- **Specific document** → [DOCUMENTATION_MAP.md](../DOCUMENTATION_MAP.md)
- **How to do X** → Check category INDEX.md files (planning/INDEX.md, deployment/INDEX.md, etc.)
- **Something not found?** → Search in category or check archived/

---

**📘 Last Updated:** April 16, 2026  
**🔄 Status:** Complete organization of 60+ documents  
**✅ All categories:** Organized with INDEX.md navigation



