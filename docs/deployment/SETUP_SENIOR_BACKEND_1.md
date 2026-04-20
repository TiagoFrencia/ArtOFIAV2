# 💻 SENIOR BACKEND ENGINEER #1 - STARTUP GUIDE

**Role:** Fix race condition + timeouts + support QA  
**Dedication:** 50% (20h/week)  
**Start:** TODAY - Tuesday 2026-04-16 at 10:00 AM  

---

## 🎯 THIS WEEK'S MISSION

| Task | Time | Deadline | Status |
|------|------|----------|--------|
| **1.1** Fix Race Condition | 1h | Tue EOD | 🔴 CRITICAL |
| **1.3** Timeout Enforcement | 2h | Wed 5 PM | 🔴 CRITICAL |
| **Testing & Code Review** | 2h | Thu-Fri | 🟠 HIGH |

**Total:** 5 hours (easy week, ramp-up mode)

---

## 🚀 START NOW (TODAY)

### Task 1.1: Race Condition RateLimiter (1 hour)

#### 10:00 AM - Setup (10 min)

```bash
cd c:\Users\tiago\Desktop\ArtOfIAV2

# Create feature branch
git checkout main
git pull origin main
git checkout -b bugfix/CRITICAL-race-condition-rate-limiter

# Open files
code src/orchestrator/supervisor.py
code tests/test_rate_limiter_concurrent.py
```

#### 10:10 AM - Read Instructions (5 min)

**Read this file completely:**
```
📖 TASK_1_1_DETAILED_INSTRUCTIONS.md
```

#### 10:15 AM - Implement (30 min)

**File:** `src/orchestrator/supervisor.py`

**Changes needed:**

```python
# 1. Add import at top
import asyncio

# 2. In RateLimiter.__init__ (around line 24):
def __init__(self):
    self.logger = logging.getLogger(__name__)
    self.limits = { ... }
    self.buckets: Dict[str, Dict[str, Any]] = {}
    
    # ADD THIS LINE:
    self.lock = asyncio.Lock()  # ← CRITICAL FIX

# 3. Change check_rate_limit signature (around line 40):
# FROM: def check_rate_limit(self, ...)
# TO:   async def check_rate_limit(self, ...)

# 4. Wrap entire logic in async with self.lock:
async def check_rate_limit(self, resource_key: str, resource_type: str = "agent"):
    async with self.lock:  # ← ADD THIS
        # All existing logic indented here
        if resource_type not in self.limits:
            return True, ""
        # ... rest of function ...

# 5. Find all callers of check_rate_limit and add await
# Search: grep -r "check_rate_limit" src/ --include="*.py"
# Update: await self.rate_limiter.check_rate_limit(...)
```

**Expected files to update:**
- [ ] `src/orchestrator/supervisor.py` - main fix
- [ ] `src/orchestrator/backend_integration.py` - add await
- [ ] `src/orchestrator/server.py` - add await (if needed)

#### 10:45 AM - Write Tests (10 min)

**File:** `tests/test_rate_limiter_concurrent.py`

```python
import pytest
import asyncio
from src.orchestrator.supervisor import RateLimiter

class TestRateLimiterRaceCondition:
    @pytest.mark.asyncio
    async def test_no_race_condition_1000_concurrent(self):
        """1000 tasks, only 1 should get token"""
        rate_limiter = RateLimiter()
        rate_limiter.limits["test"] = {"max_requests": 1, "window_seconds": 60}
        
        successful = 0
        failed = 0
        
        async def request_token():
            nonlocal successful, failed
            permitted, _ = await rate_limiter.check_rate_limit("key", "test")
            if permitted:
                successful += 1
            else:
                failed += 1
        
        # Run 1000 concurrent
        await asyncio.gather(*[request_token() for _ in range(1000)])
        
        assert successful == 1, f"Got {successful}, expected 1"
        assert failed == 999
```

#### 10:55 AM - Test & Push (5 min)

```bash
# Run tests
pytest tests/test_rate_limiter_concurrent.py -v

# Expected: ✅ PASSED

# Check linting
pylint src/orchestrator/supervisor.py

# Type checking
mypy src/orchestrator/supervisor.py

# Commit
git add src/orchestrator/supervisor.py tests/test_rate_limiter_concurrent.py
git commit -m "[CRITICAL] Fix race condition in rate limiter

- Add asyncio.Lock for atomic operations
- Make check_rate_limit() async
- Update all callers to await
- Add concurrent stress test (1000 tasks)"

# Push
git push origin bugfix/CRITICAL-race-condition-rate-limiter

# Create PR on GitHub
```

**Expected completion:** 11:00 AM ✅

---

### After Lunch: Assist With Task 1.3 Support

#### 1:00 PM - Prepare for Task 1.3 (30 min)

**Review:** `TASK_1_3_TIMEOUT_GUIDE.md`

```
Understand:
- asyncio.wait_for() pattern
- Where to add timeout checks
- How to handle TimeoutError
```

---

### Task 1.3: Timeout Enforcement (2 hours)

#### 2:00 PM - Implementation (1.5 hours)

**File:** `src/orchestrator/main_integration.py`

```python
# Around line 88, in method: run_full_red_team_operation()

async def run_full_red_team_operation(self, target):
    """With timeout enforcement"""
    try:
        return await asyncio.wait_for(
            self._execute_operation(target),
            timeout=self.OPERATION_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.error(
            f"Operation timeout after {self.OPERATION_TIMEOUT}s",
            extra={"target": target}
        )
        raise OperationTimeoutException(
            f"Operation exceeded {self.OPERATION_TIMEOUT}s timeout"
        )
```

**Also update:** `src/orchestrator/server.py` initialize() method

```python
async def initialize(self):
    try:
        return await asyncio.wait_for(
            self._initialize_all(),
            timeout=300.0  # 5 min for init
        )
    except asyncio.TimeoutError:
        raise InitializationTimeoutException("Init exceeded 300s timeout")
```

#### 3:30 PM - Tests (20 min)

```python
# tests/test_timeout_enforcement.py

@pytest.mark.asyncio
async def test_operation_timeout_enforced():
    """Operation > OPERATION_TIMEOUT should timeout"""
    system = IntegratedArtOfIA()
    
    # Mock slow operation
    async def slow_op():
        await asyncio.sleep(1500)  # 25 min
    
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_op(), timeout=300)
```

#### 3:50 PM - Push PR (10 min)

```bash
git checkout -b feature/timeout-enforcement
git add src/orchestrator/main_integration.py tests/test_timeout_enforcement.py
git commit -m "[CRITICAL] Enforce operation timeouts

- Add asyncio.wait_for to prevent infinite operations
- OPERATION_TIMEOUT: 1200s (20 min)
- STAGE_TIMEOUT: 300s (5 min)
- Proper error handling with logging"

git push origin feature/timeout-enforcement
```

**Expected completion:** 4:00 PM ✅

---

## 📅 WEDNESDAY-FRIDAY

### Wednesday

- 9:00 AM: Standup (15 min)
  - Report: "PR 1.1 ready"
  - Status: Wait for Tech Lead approval
  
- Address any feedback on PR 1.1
  
- Support SBE#2 if needed (30 min)

### Thursday

- 9:00 AM: Standup (15 min)
  - Report: "PR 1.3 ready"
  - Status: Wait for approval

- All tests passing? ✅

### Friday

- 9:00 AM: Standup (15 min)
  - Both PRs merged ✅
  
- Celebrate Week 1! 🎉

---

## 🎯 SUCCESS CRITERIA

By Friday EOD:

- [ ] PR #1 (race condition) - MERGED ✅
- [ ] PR #3 (timeout) - MERGED ✅
- [ ] All tests PASSING ✅
- [ ] 0 linting errors ✅
- [ ] Tech Lead approved both ✅

---

## 📞 IF STUCK

**Problem:** Not sure how to make check_rate_limit async  
→ **Solution:** Look for similar patterns in codebase:
```bash
grep -r "async def" src/agents/ --include="*.py" | head -5
```

**Problem:** Tests fail  
→ **Solution:** Run with verbose:
```bash
pytest tests/test_rate_limiter_concurrent.py -vv -s
```

**Problem:** CI/CD complaining  
→ **Solution:**
```bash
# Fix linting
pylint src/orchestrator/supervisor.py --fix-errors

# Fix type hints
mypy src/orchestrator/supervisor.py --show-error-codes

# Rerun tests
pytest tests/ -x  # Stop on first failure
```

**Problem:** Still stuck?  
→ **DM Tech Lead on Slack** - Response in <1 hour

---

## 🗓️ YOUR CALENDAR

```
TODAY (Tue)
☐ 10:00 AM - Task 1.1 implementation (1h)
☐ 4:00 PM - Done & PR pushed

WED
☐ 9:00 AM - Standup (15 min)
☐ 10:00 AM - Start Task 1.3 (2h)
☐ 4:00 PM - PR pushed

THU
☐ 9:00 AM - Standup (15 min)
☐ Address feedback

FRI
☐ 9:00 AM - Standup (15 min)
☐ 4:00 PM - Formal review + celebrate

TOTAL: ~5 hours
```

---

## ✅ YOU GOT THIS!

This is your week to shine. Two critical fixes, both achievable in standard time.

**Remember:** If any blocker, escalate IMMEDIATELY to Tech Lead. Don't try to be a hero. Just ask.

Good luck! 🚀

