#!/bin/bash

# =============================================================================
# Idle Citizen Setup Script
# Run this once to set up the workspace on a new machine
# =============================================================================

set -euo pipefail

IDLE_CITIZEN_DIR="${IDLE_CITIZEN_DIR:-$HOME/idle-citizen}"

echo "=== Idle Citizen Setup ==="
echo "Target directory: $IDLE_CITIZEN_DIR"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Claude Code CLI
if command -v claude &> /dev/null; then
    echo "✓ Claude Code CLI found"
else
    echo "✗ Claude Code CLI not found"
    echo "  Install (native): curl -fsSL https://claude.ai/install.sh | bash"
    echo "  Or see: https://code.claude.com/docs/en/setup"
    exit 1
fi

# Python 3 (for JSON parsing)
if command -v python3 &> /dev/null; then
    echo "✓ Python 3 found"
else
    echo "✗ Python 3 not found"
    echo "  Required for JSON parsing in the launcher"
    exit 1
fi

# curl
if command -v curl &> /dev/null; then
    echo "✓ curl found"
else
    echo "✗ curl not found"
    exit 1
fi

# timeout/gtimeout
if command -v timeout &> /dev/null || command -v gtimeout &> /dev/null; then
    echo "✓ timeout command found"
else
    echo "✗ timeout command not found"
    echo "  On macOS, install coreutils: brew install coreutils"
    exit 1
fi

# bc (for floating point comparison)
if command -v bc &> /dev/null; then
    echo "✓ bc found"
else
    echo "✗ bc not found"
    echo "  On macOS: brew install bc"
    exit 1
fi

echo ""

# Check Claude Code authentication
echo "Checking Claude Code authentication..."
if security find-generic-password -s "Claude Code-credentials" -w &> /dev/null; then
    echo "✓ Claude Code credentials found in keychain"
else
    echo "✗ Claude Code credentials not found"
    echo "  Run 'claude' and authenticate with your Max plan first"
    exit 1
fi

echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$IDLE_CITIZEN_DIR/logs"
mkdir -p "$IDLE_CITIZEN_DIR/explorations"
mkdir -p "$IDLE_CITIZEN_DIR/continuity"
echo "✓ Directories created"

# Copy files if running from repo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/CLAUDE.md" ]]; then
    cp "$SCRIPT_DIR/CLAUDE.md" "$IDLE_CITIZEN_DIR/"
    echo "✓ Copied CLAUDE.md"
fi

if [[ -f "$SCRIPT_DIR/context.md" ]]; then
    cp "$SCRIPT_DIR/context.md" "$IDLE_CITIZEN_DIR/"
    echo "✓ Copied context.md"
fi

if [[ -f "$SCRIPT_DIR/continuity/last-session-state.md" ]]; then
    cp "$SCRIPT_DIR/continuity/last-session-state.md" "$IDLE_CITIZEN_DIR/continuity/"
    echo "✓ Copied last-session-state.md"
fi

if [[ -f "$SCRIPT_DIR/idle-citizen-launcher.sh" ]]; then
    cp "$SCRIPT_DIR/idle-citizen-launcher.sh" "$IDLE_CITIZEN_DIR/"
    chmod +x "$IDLE_CITIZEN_DIR/idle-citizen-launcher.sh"
    echo "✓ Copied and made executable: idle-citizen-launcher.sh"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Test the launcher manually:"
echo "   cd $IDLE_CITIZEN_DIR"
echo "   ./idle-citizen-launcher.sh"
echo ""
echo "2. Once working, set up scheduling (see README.md)"
echo ""
echo "Configuration (environment variables):"
echo "  IDLE_CITIZEN_DIR      - Workspace location (default: ~/idle-citizen)"
echo "  SESSION_DURATION_SECONDS - Session length (default: 900 = 15 min)"
echo "  QUOTA_THRESHOLD       - Min % remaining to launch (default: 30)"
echo ""
