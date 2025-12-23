#!/bin/bash

# =============================================================================
# Idle Citizen: Fresh Mac Setup
# Run this on a freshly wiped MacBook to set up everything needed
# =============================================================================

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           Idle Citizen - Fresh Mac Setup                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Xcode Command Line Tools
# -----------------------------------------------------------------------------
echo "Step 1/6: Checking Xcode command line tools..."

if xcode-select -p &> /dev/null; then
    echo "✓ Xcode CLI tools already installed"
else
    echo "Installing Xcode command line tools..."
    xcode-select --install
    echo ""
    echo "A dialog should appear. Click 'Install' and wait for completion."
    echo "Press Enter when the installation is complete..."
    read
fi

# -----------------------------------------------------------------------------
# Step 2: Homebrew
# -----------------------------------------------------------------------------
echo ""
echo "Step 2/6: Checking Homebrew..."

if command -v brew &> /dev/null; then
    echo "✓ Homebrew already installed"
else
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add to PATH for Apple Silicon
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Ensure brew is in PATH for this session
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Step 3: Dependencies
# -----------------------------------------------------------------------------
echo ""
echo "Step 3/6: Installing dependencies..."

brew install coreutils  # for gtimeout
brew install bc         # for floating point math
brew install tmux       # for interactive sessions
brew install git        # should be there but just in case

echo "✓ Dependencies installed"

# -----------------------------------------------------------------------------
# Step 4: Claude Code (Native Installation - Recommended by Anthropic)
# -----------------------------------------------------------------------------
echo ""
echo "Step 4/6: Installing Claude Code (native installer)..."

if command -v claude &> /dev/null; then
    echo "✓ Claude Code already installed"
    claude --version
else
    echo "Installing via Anthropic's native installer..."
    echo "(This doesn't require Node.js and includes auto-updates)"
    curl -fsSL https://claude.ai/install.sh | bash
    
    # Add to PATH if needed (installer puts it in ~/.local/bin)
    if [[ -d "$HOME/.local/bin" ]] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    echo "✓ Claude Code installed"
fi

# -----------------------------------------------------------------------------
# Step 5: Claude Code Authentication
# -----------------------------------------------------------------------------
echo ""
echo "Step 5/6: Claude Code authentication..."
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  IMPORTANT: You need to authenticate Claude Code now          ║"
echo "║                                                               ║"
echo "║  Run: claude                                                  ║"
echo "║                                                               ║"
echo "║  Then sign in with your Max plan credentials.                 ║"
echo "║  Once authenticated, press Ctrl+C to exit and return here.    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Press Enter to open Claude Code for authentication..."
read

claude || true

echo ""
echo "Did authentication succeed? (y/n)"
read auth_success

if [[ "$auth_success" != "y" ]]; then
    echo "Please run 'claude' again to authenticate, then re-run this script."
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 6: Clone and Setup
# -----------------------------------------------------------------------------
echo ""
echo "Step 6/6: Project setup..."
echo ""

if [[ -d "$HOME/idle-citizen" ]]; then
    echo "idle-citizen directory already exists at ~/idle-citizen"
else
    echo "How do you want to set up the project?"
    echo "1) Clone from GitHub (if you've pushed it)"
    echo "2) I'll copy the files manually"
    echo ""
    echo "Enter 1 or 2:"
    read setup_choice
    
    if [[ "$setup_choice" == "1" ]]; then
        echo "Enter your GitHub repo URL:"
        echo "(e.g., https://github.com/username/idle-citizen.git)"
        read repo_url
        git clone "$repo_url" "$HOME/idle-citizen"
    else
        echo ""
        echo "Please copy your idle-citizen folder to ~/idle-citizen"
        echo "Press Enter when done..."
        read
    fi
fi

# Run setup if it exists
if [[ -f "$HOME/idle-citizen/setup.sh" ]]; then
    cd "$HOME/idle-citizen"
    chmod +x setup.sh idle-citizen-launcher.sh idle-citizen-interactive.sh 2>/dev/null || true
    ./setup.sh
fi

# -----------------------------------------------------------------------------
# Complete
# -----------------------------------------------------------------------------
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "  1. Test interactive mode (watch Claude live):"
echo "     cd ~/idle-citizen"
echo "     ./idle-citizen-interactive.sh --watch"
echo ""
echo "  2. Or test headless mode:"
echo "     ./idle-citizen-launcher.sh"
echo ""
echo "  3. Set up scheduling (see README.md)"
echo ""
echo "  4. Optional: Enable SSH for remote monitoring"
echo "     System Settings → General → Sharing → Remote Login"
echo ""
