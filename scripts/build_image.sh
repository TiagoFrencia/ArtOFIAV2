#!/bin/bash
#
# Docker Image Builder - Automated Reproducible Build Script
# ==========================================================
#
# This script ensures consistent Docker image building with:
# - Version tagging
# - Sanity checks (Python, Docker)
# - Build logging
# - Success/failure reporting
#
# Usage: ./build_image.sh [OPTIONS]
#   -v, --version VERSION   Override image version (default: latest)
#   -f, --force             Force rebuild even if image exists
#   -q, --quiet             Suppress detailed output
#   -h, --help              Show this help message

set -euo pipefail

# ============================================================
# CONFIGURATION
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Image configuration
IMAGE_NAME="artofiabox"
IMAGE_TAG="${1:-ephemeral}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# Dockerfile location
DOCKERFILE_PATH="${PROJECT_ROOT}/src/backends/docker_sandbox/Dockerfile.ephemeral"

# Build context (project root for access to src/)
BUILD_CONTEXT="${PROJECT_ROOT}"

# Python version requirement
REQUIRED_PYTHON_VERSION="3.11"

# Logging
LOG_FILE="${PROJECT_ROOT}/build_${IMAGE_TAG}_$(date +%Y%m%d_%H%M%S).log"
FORCE_REBUILD=false
QUIET_MODE=false

# ============================================================
# UTILITIES
# ============================================================

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    if [[ "$QUIET_MODE" == false ]]; then
        log "INFO" "$@"
    fi
}

log_error() {
    log "ERROR" "$@" >&2
}

log_success() {
    log "SUCCESS" "$@"
}

print_help() {
    cat <<EOF
Docker Image Builder for ArtOfIAV2

Usage: $0 [OPTIONS]

Options:
    -v, --version VERSION   Override image version (default: ephemeral)
    -f, --force             Force rebuild even if image exists
    -q, --quiet             Suppress detailed output
    -h, --help              Show this help message

Examples:
    # Build with default tag
    $0

    # Build with custom version
    $0 -v v1.2.3

    # Force rebuild
    $0 --force

    # Build with minimal output
    $0 --quiet
EOF
}

# ============================================================
# ARGUMENT PARSING
# ============================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_REBUILD=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Update full image name after parsing
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# ============================================================
# SANITY CHECKS
# ============================================================

log_info "=========================================="
log_info "DOCKER IMAGE BUILD STARTED"
log_info "=========================================="
log_info "Image: ${FULL_IMAGE_NAME}"
log_info "Dockerfile: ${DOCKERFILE_PATH}"
log_info "Context: ${BUILD_CONTEXT}"
log_info "Log: ${LOG_FILE}"

# Check if Dockerfile exists
if [[ ! -f "$DOCKERFILE_PATH" ]]; then
    log_error "Dockerfile not found: $DOCKERFILE_PATH"
    exit 1
fi

log_info "✓ Dockerfile found"

# Check Python version
log_info "Checking Python installation..."
if ! command -v python3 &>/dev/null; then
    log_error "Python3 not found in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_info "✓ Python version: $PYTHON_VERSION"

# Parse Python version (e.g., "3.11.2" -> "3.11")
PYTHON_MAJOR_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f1,2)
if [[ "$PYTHON_MAJOR_MINOR" != "$REQUIRED_PYTHON_VERSION" ]]; then
    log_error "Python $REQUIRED_PYTHON_VERSION required, but $PYTHON_VERSION found"
    log_error "Install Python $REQUIRED_PYTHON_VERSION or specify correct version"
    exit 1
fi

# Check Docker
log_info "Checking Docker installation..."
if ! command -v docker &>/dev/null; then
    log_error "Docker not found in PATH"
    exit 1
fi

if ! docker info &>/dev/null; then
    log_error "Docker daemon not running or not accessible"
    log_error "Try: docker ps"
    exit 1
fi

log_info "✓ Docker is running"

# Check if image already exists
if docker image inspect "$FULL_IMAGE_NAME" &>/dev/null; then
    if [[ "$FORCE_REBUILD" == false ]]; then
        log_info "Image $FULL_IMAGE_NAME already exists"
        log_info "Use --force to rebuild"
        log_success "BUILD SKIPPED (image exists)"
        exit 0
    else
        log_info "Removing existing image: $FULL_IMAGE_NAME"
        docker image rm "$FULL_IMAGE_NAME" || true
    fi
fi

# ============================================================
# BUILD DOCKER IMAGE
# ============================================================

log_info ""
log_info "Building Docker image..."
log_info ""

start_time=$(date +%s)

if docker build \
    --file "$DOCKERFILE_PATH" \
    --tag "$FULL_IMAGE_NAME" \
    --build-arg BASE_IMAGE="python:3.11-slim" \
    --progress=plain \
    "$BUILD_CONTEXT" 2>&1 | tee -a "$LOG_FILE"; then
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    # Verify image was created
    if docker image inspect "$FULL_IMAGE_NAME" &>/dev/null; then
        log_success "BUILD SUCCESSFUL"
        log_info "Image: $FULL_IMAGE_NAME"
        
        # Get image size
        SIZE=$(docker image inspect "$FULL_IMAGE_NAME" --format='{{.Size}}' | numfmt --to=iec 2>/dev/null || echo "unknown")
        log_info "Size: $SIZE"
        log_info "Build time: ${duration}s"
        log_info ""
        log_info "Next steps:"
        log_info "  1. Test the image: docker run --rm $FULL_IMAGE_NAME python --version"
        log_info "  2. Deploy: docker compose up -d"
        log_info ""
        exit 0
    else
        log_error "BUILD FAILED: Image was not created"
        exit 1
    fi
else
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    log_error "BUILD FAILED after ${duration}s"
    log_error "Check $LOG_FILE for details"
    exit 1
fi
