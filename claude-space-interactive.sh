#!/bin/bash

# =============================================================================
# Claude Space Interactive Launcher
# Runs Claude in a tmux session you can attach to and watch live
# =============================================================================

set -euo pipefail

CLAUDE_SPACE_DIR="${CLAUDE_SPACE_DIR:-$HOME/claude-space}"
SESSION_NAME="${SESSION_NAME:-claude-space}"
SESSION_TIMEOUT="${SESSION_TIMEOUT:-15m}"
AUTO_TIMEOUT="${AUTO_TIMEOUT:-true}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -w, --watch      Start and immediately attach (watch live)"
    echo "  -k, --kill       Kill existing session"
    echo "  -s, --status     Check if session is running"
    echo "  -n, --no-timeout Run without time limit"
    echo "  -h, --help       Show this help"
    echo ""
    echo "To attach to running session: tmux attach -t $SESSION_NAME"
    echo "To detach while watching: Ctrl+B, then D"
}

check_deps() {
    if ! command -v tmux &> /dev/null; then
        echo "Error: tmux not installed. Run: brew install tmux"
        exit 1
    fi
    if ! command -v claude &> /dev/null; then
        echo "Error: Claude Code not installed."
        exit 1
    fi
}

session_exists() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

start_session() {
    local watch_mode="$1"
    
    if session_exists; then
        echo -e "${YELLOW}Session already running.${NC}"
        echo "Attach with: tmux attach -t $SESSION_NAME"
        if [[ "$watch_mode" == "true" ]]; then
            tmux attach -t "$SESSION_NAME"
        fi
        return 0
    fi
    
    echo -e "${GREEN}Starting Claude Space session...${NC}"
    
    # Create the session
    tmux new-session -d -s "$SESSION_NAME" -c "$CLAUDE_SPACE_DIR"
    
    # Build the command
    local cmd="claude"
    if [[ "$AUTO_TIMEOUT" == "true" ]]; then
        # Use gtimeout on macOS
        local timeout_cmd="timeout"
        if command -v gtimeout &> /dev/null; then
            timeout_cmd="gtimeout"
        fi
        cmd="$timeout_cmd $SESSION_TIMEOUT claude; echo ''; echo 'Session ended. Press Enter to close.'; read"
    fi
    
    # Send the command
    tmux send-keys -t "$SESSION_NAME" "$cmd" Enter
    
    echo -e "${GREEN}Session started!${NC}"
    echo ""
    echo "Commands:"
    echo "  Watch live:     tmux attach -t $SESSION_NAME"
    echo "  Detach:         Ctrl+B, then D"
    echo "  Kill session:   $0 --kill"
    
    if [[ "$watch_mode" == "true" ]]; then
        echo ""
        echo "Attaching now..."
        sleep 1
        tmux attach -t "$SESSION_NAME"
    fi
}

kill_session() {
    if session_exists; then
        tmux kill-session -t "$SESSION_NAME"
        echo "Session killed."
    else
        echo "No session running."
    fi
}

check_status() {
    if session_exists; then
        echo -e "${GREEN}Session is running.${NC}"
        echo "Attach with: tmux attach -t $SESSION_NAME"
        tmux list-sessions
    else
        echo "No session running."
    fi
}

# Parse arguments
WATCH_MODE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--watch)
            WATCH_MODE="true"
            shift
            ;;
        -k|--kill)
            kill_session
            exit 0
            ;;
        -s|--status)
            check_status
            exit 0
            ;;
        -n|--no-timeout)
            AUTO_TIMEOUT="false"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main
check_deps
start_session "$WATCH_MODE"
