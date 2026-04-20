# 🔧 DEVOPS - STARTUP GUIDE

**Role:** Docker image build + CI/CD setup  
**Dedication:** 15% (6h/week)  
**Start:** TODAY - Tuesday 2026-04-16 at 2:00 PM  

---

## 🎯 THIS WEEK'S MISSION

| Task | Time | Deadline | Status |
|------|------|----------|--------|
| **1.2** Docker Build Script | 1.5h | Tue EOD | 🔴 CRITICAL |
| **CI/CD Setup** | 2.5h | Wed-Thu | 🟠 HIGH |
| **Verification** | 1h | Fri | ✅ |

**Total:** 5 hours

---

## 🚀 START NOW (TODAY - 2:00 PM)

### Task 1.2: Docker Image Build

#### 2:00 PM - Setup (30 min)

```bash
cd c:\Users\tiago\Desktop\ArtOfIAV2

# Create branch
git checkout main && git pull
git checkout -b devops/docker-automation

# Review current Dockerfile
code src/backends/docker_sandbox/Dockerfile.ephemeral

# Check current build process (if any)
ls -la scripts/
```

#### 2:30 PM - Create Build Script (30 min)

**Create file:** `scripts/build_image.sh`

```bash
#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🐳 Building ArtOfIA ephemeral sandbox image...${NC}"

# Image configuration
IMAGE_NAME="artofiabox"
IMAGE_TAG="ephemeral"
DOCKERFILE="src/backends/docker_sandbox/Dockerfile.ephemeral"

# Check Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}❌ Dockerfile not found: $DOCKERFILE${NC}"
    exit 1
fi

# Build image
echo -e "${YELLOW}📦 Building: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
docker build \
    -f "$DOCKERFILE" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    --build-arg BASE_IMAGE=python:3.11-slim \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Image built successfully${NC}"
    
    # Display image info
    echo -e "${GREEN}📊 Image details:${NC}"
    docker images | grep "$IMAGE_NAME"
    
    # Check image size
    SIZE=$(docker images | grep "$IMAGE_NAME" | awk '{print $7}')
    echo -e "${GREEN}   Size: $SIZE${NC}"
    
    # Optional: Run basic test
    echo -e "${YELLOW}🧪 Running sanity check...${NC}"
    docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" python --version
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Sanity check PASSED${NC}"
    else
        echo -e "${RED}❌ Sanity check FAILED${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi
```

#### 3:00 PM - Test Build Script (15 min)

```bash
# Make executable
chmod +x scripts/build_image.sh

# Run build
./scripts/build_image.sh

# Expected output:
# 🐳 Building ArtOfIA ephemeral sandbox image...
# ✅ Image built successfully
# 📊 Image details: artofiabox ephemeral ...
```

If any errors, fix them now.

#### 3:15 PM - Update Documentation (15 min)

**Update:** `README.md`

**Find section:** "Quick Start (5 Minutes)"  
**Add before docker-compose up:**

```markdown
### Prerequisites

1. **Build the sandbox image**
   ```bash
   ./scripts/build_image.sh
   ```
   Or manually:
   ```bash
   docker build -f src/backends/docker_sandbox/Dockerfile.ephemeral \
     -t artofiabox:ephemeral .
   ```

2. **Verify build**
   ```bash
   docker images | grep artofiabox
   # Should see: artofiabox     ephemeral
   ```
```

**Update:** `clients/cli/quickstart.sh`

**Add at the top (before docker-compose up):**

```bash
#!/bin/bash

echo "🐳 Building Docker image..."
cd ../..  # Go to project root
./scripts/build_image.sh

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed. Exiting."
    exit 1
fi

echo "✅ Docker image ready"

# Continue with original quickstart...
docker-compose up -d
```

#### 3:30 PM - Commit & Push (15 min)

```bash
git add scripts/build_image.sh README.md clients/cli/quickstart.sh

git commit -m "[DEVOPS] Automate Docker image build

- Create scripts/build_image.sh for reproducible builds
- Add sanity check (python --version)
- Update README with prerequisites
- Update quickstart.sh to build before deploying

Build output:
- Image name: artofiabox:ephemeral
- Base: python:3.11-slim
- Size: ~500MB (TBD after build)"

git push origin devops/docker-automation
```

**Expected completion:** 3:45 PM ✅

---

## 📅 WEDNESDAY-THURSDAY - CI/CD SETUP

### Wednesday 3:00 PM (1.5 hours)

#### Create GitHub Actions Workflow

**Create file:** `.github/workflows/test.yml`

```yaml
name: Tests & Linting

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Lint with pylint
      run: |
        pylint src/ --exit-zero  # Report but don't fail
    
    - name: Type check with mypy
      run: |
        mypy src/ --ignore-missing-imports
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

**Create file:** `.github/workflows/docker-build.yml`

```yaml
name: Docker Build

on:
  push:
    branches: [main]
    paths:
      - 'src/backends/docker_sandbox/**'
      - '.github/workflows/docker-build.yml'

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Build Docker image
      run: |
        ./scripts/build_image.sh
```

### Thursday 2:00 PM (1 hour)

#### Setup Branch Protection

```bash
# This is done by Tech Lead, but verify:

1. Go to GitHub repo → Settings → Branches
2. Under "Branch protection rules", confirm:
   ☑ Require pull request reviews
   ☑ Require 1 approval minimum
   ☑ Require status checks to pass (Github Actions must pass)
```

---

## 📅 FRIDAY

### 9:00 AM - Standup (15 min)

```
Report: "Docker automation + CI/CD setup complete"
Status: Ready for Week 2
```

---

## 🎯 SUCCESS CRITERIA

By Friday EOD:

- [ ] `scripts/build_image.sh` works ✅
- [ ] Image builds successfully ✅
- [ ] GitHub Actions workflows created ✅
- [ ] CI passes on all PRs ✅
- [ ] Branch protection active ✅

---

## 📞 TROUBLESHOOTING

**Problem:** Docker build fails  
**Solution:**
```bash
# Check Dockerfile syntax
docker build -f src/backends/docker_sandbox/Dockerfile.ephemeral --dry-run .

# Build with verbose
docker build -f src/backends/docker_sandbox/Dockerfile.ephemeral . -v

# Check for missing dependencies
grep -i "RUN pip install" src/backends/docker_sandbox/Dockerfile.ephemeral
```

**Problem:** GitHub Actions not triggering  
**Solution:**
```bash
# Commit and push to test branch
git push origin --all

# Check Actions tab: github.com/repo/actions
# Restart workflow if needed
```

**Problem:** CI fails on specific check  
**Solution:**
```bash
# Run locally
pytest tests/ -v

# Run lint
pylint src/

# Run type check
mypy src/
```

---

## 🗓️ YOUR CALENDAR

```
TODAY (Tue)
☐ 2:00 PM - Docker build script (1.5h)
☐ 3:30 PM - Done & PR pushed (15 min)

WED
☐ 3:00 PM - CI/CD setup (1.5h)

THU
☐ 2:00 PM - Verify + adjust (1h)

FRI
☐ 9:00 AM - Standup (15 min)
☐ 4:00 PM - Celebrate! 🎉

TOTAL: ~5 hours
```

---

## ✅ NEXT UP

After this week, DevOps focuses on:
- Test infrastructure for QA team (Week 2)
- Docker registry setup (optional Week 3)
- Monitoring dashboard (Week 7)

You're the backbone of our CI/CD! Keep it running smooth.

Good luck! 🚀

