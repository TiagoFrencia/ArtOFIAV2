#!/bin/bash
# ArtOfIA CLI - Quick Start Script

set -e

echo "🕵️ ArtOfIA V2 CLI - Quick Start"
echo "================================="
echo ""

# Check prerequisites
echo "✓ Checking prerequisites..."

if ! command -v node &> /dev/null; then
  echo "✗ Node.js is not installed"
  exit 1
fi

if ! command -v npm &> /dev/null; then
  echo "✗ npm is not installed"
  exit 1
fi

NODE_VERSION=$(node -v)
NPM_VERSION=$(npm -v)
echo "  Node version: $NODE_VERSION"
echo "  npm version: $NPM_VERSION"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Build project
echo ""
echo "🔨 Building TypeScript..."
npm run build

# Configuration
echo ""
echo "⚙️ Configuration"
echo "=================================================="
ORCHESTRATOR="${ARTOFCIA_ORCHESTRATOR:-ws://localhost:9000}"
USERNAME="${ARTOFCIA_USERNAME:-operator}"
SESSION_ID="${ARTOFCIA_SESSION_ID:-$(node -e 'console.log(require("crypto").randomUUID())')}"

echo "Orchestrator URL: $ORCHESTRATOR"
echo "Username: $USERNAME"
echo "Session ID: $SESSION_ID"

# Start application
echo ""
echo "🚀 Starting ArtOfIA CLI..."
echo "=================================================="
echo ""
echo "Keyboard Shortcuts:"
echo "  [1-4] Dashboard modes    [←→] Tabs"
echo "  [Y/N] Approve/Reject     [P/R] Pause/Resume"
echo "  [H] Help                 [Q] Quit"
echo ""

npm start -- \
  --orchestrator "$ORCHESTRATOR" \
  --username "$USERNAME" \
  --session "$SESSION_ID"
