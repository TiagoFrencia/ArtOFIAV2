# Developer Documentation

**Location:** `/docs/developers/`  
**Purpose:** Code structure, testing guides, technical details, and development workflows

## 📚 Core Developer Guides

### Architecture & Code Structure
- **[code-structure.md](code-structure.md)** - Complete src/ organization ✅ NEW
- **[testing-guide.md](testing-guide.md)** - Testing patterns and practices ✅ NEW
- **[BACKENDS_DOCUMENTATION.md](BACKENDS_DOCUMENTATION.md)** - Backend systems
- **[CODEBASE_STRUCTURAL_ANALYSIS.md](CODEBASE_STRUCTURAL_ANALYSIS.md)** - Structural analysis

### Technical Deep Dives
- **[SENIOR_CODE_REVIEW.md](SENIOR_CODE_REVIEW.md)** - Code review notes
- **[SENIOR_CODE_REVIEW_ANALYSIS.md](SENIOR_CODE_REVIEW_ANALYSIS.md)** - Review analysis
- **[CONCRETE_FIXES_GUIDE.md](CONCRETE_FIXES_GUIDE.md)** - Specific fixes applied

### Build & Integration
- **[CMAKE.md](CMAKE.md)** - CMake build configuration
- **[INTEGRATION_BACKENDS_GUIDE.md](INTEGRATION_BACKENDS_GUIDE.md)** - Backend integration
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Debugging & fixes

---

## 🚀 Getting Started as a Developer

### 1️⃣ First 30 Minutes (Understand Structure)
```
Read: code-structure.md
See: src/ directory organization
Understand: 3-layer architecture (agents, backends, memory)
```

### 2️⃣ Next 1 Hour (Write Tests)
```
Read: testing-guide.md
See: tests/ examples (test_orchestrator_core.py, etc.)
Try: Run existing tests (pytest tests/ -v)
```

### 3️⃣ Code Navigation
```
Backend systems: BACKENDS_DOCUMENTATION.md
Code review notes: SENIOR_CODE_REVIEW.md
Structural analysis: CODEBASE_STRUCTURAL_ANALYSIS.md
```

---

## 📋 By Task

### I want to...

**Understand the codebase**
→ [code-structure.md](code-structure.md)

**Write a test**
→ [testing-guide.md](testing-guide.md) + examples in tests/

**Fix a bug**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) + [SENIOR_CODE_REVIEW.md](SENIOR_CODE_REVIEW.md)

**Integrate a backend**
→ [INTEGRATION_BACKENDS_GUIDE.md](INTEGRATION_BACKENDS_GUIDE.md)

**Review code quality**
→ [SENIOR_CODE_REVIEW_ANALYSIS.md](SENIOR_CODE_REVIEW_ANALYSIS.md)

**Build the project**
→ [CMAKE.md](CMAKE.md)

---

## 🏗️ Architecture Overview

### Three-Layer Architecture
```
Layer 1: Agents (recon, logic, exploit)
    ↓
Layer 2: Backends (memory, LLM, sandbox)
    ↓
Layer 3: Core (security, validation, persistence)
```

See [code-structure.md](code-structure.md) for detailed diagrams and code locations.

---

## 🧪 Testing Reference

### Test Framework
- **Framework:** pytest + pytest-asyncio
- **Coverage:** 150+ tests (65%+ coverage)
- **Guide:** [testing-guide.md](testing-guide.md)

### Test Files (Examples)
- `tests/test_orchestrator_core.py` - 50+ tests (orchestration)
- `tests/test_backends_and_memory.py` - 25+ tests (persistence)
- `tests/test_agents_behavior.py` - 30+ tests (agent workflows)

### Run Tests
```bash
pytest tests/ -v                    # All tests
pytest tests/ -v --cov=src          # With coverage
pytest tests/test_orchestrator_core.py  # Specific module
```

---

## 🔧 Key Modules (Recent Improvements)

### Extracted & Refactored (v1.3)
- **ConfigLoader** (`src/orchestrator/config_loader.py`) - Configuration management ✅ NEW
- **server.py** - Refactored for dependency injection ✅ IMPROVED
- **input_validator.py** - Enhanced with AST-based analysis ✅ IMPROVED

### Status
- Type Safety: Enforced (MyPy strict mode)
- Memory: Bounded (no unbounded collections)
- Security: AST-based validation
- Testing: 150+ tests, 65%+ coverage

---

## 📞 Related Documentation

- **Operations & Red Teaming:** [../operators/](../operators/)
- **Deployment & Infrastructure:** [../deployment/](../deployment/)
- **Main Hub:** [../README.md](../README.md)
- **Improvements:** [../improvements/](../improvements/)

---

## 💡 Quick Reference

| Question | Answer |
|----------|--------|
| Where is core code? | `src/` (see code-structure.md) |
| How do I test? | [testing-guide.md](testing-guide.md) |
| Where are tests? | `tests/` (see guide) |
| How to build? | [CMAKE.md](CMAKE.md) |
| I found a bug? | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Code quality issues? | [SENIOR_CODE_REVIEW_ANALYSIS.md](SENIOR_CODE_REVIEW_ANALYSIS.md) |

---

**Last Updated:** 2026-04-16  
**Status:** Organized with NEW comprehensive guides (v1.3)  
**Key Additions:** code-structure.md, testing-guide.md, CONFIG guide patterns

