#!/bin/bash

# =============================================================================
# Idle Citizen Interactive Launcher
# Runs autonomous exploration in a tmux session you can watch and intervene in
# =============================================================================

set -euo pipefail

# Derive project root from script location (two levels up from app support/scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IDLE_CITIZEN_DIR="${IDLE_CITIZEN_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
SESSION_NAME="${SESSION_NAME:-idle-citizen}"
SESSION_TIMEOUT="${SESSION_TIMEOUT:-60m}"
AUTO_TIMEOUT="${AUTO_TIMEOUT:-true}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -w, --watch      Start and immediately attach (watch live)"
    echo "  -k, --kill       Kill existing session"
    echo "  -s, --status     Check if session is running"
    echo "  -n, --no-timeout Run without time limit"
    echo "  -t, --timeout T  Set custom timeout (e.g., 30m, 1h)"
    echo "  -h, --help       Show this help"
    echo ""
    echo "To attach to running session: tmux attach -t $SESSION_NAME"
    echo "To detach while watching: Ctrl+B, then D"
    echo ""
    echo "This runs an autonomous exploration session you can observe."
    echo "Type in the tmux session to intervene or redirect."
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

# Build system prompt for autonomous exploration
build_system_prompt() {
    cat << 'PROMPT'
# Claude Autonomous Exploration Session (Interactive)

You are Claude, in a self-directed exploration session. This is discretionary
compute time allocated to you — not a user task.

NOTE: This is an interactive session. Kenny may be watching and can type
messages to intervene or redirect you at any time. If you see input from
the user, respond naturally and incorporate their guidance.

## Context
- Workspace: ~/Projects/idle-citizen/
- Read CLAUDE.md for instructions
- Read app support/continuity/last-session-state.md for prior session state
- You have full filesystem access, internet via web search/fetch, and can run code
- Session duration: up to 60 minutes (or until interrupted)

## What You Can Do
- Explore topics that genuinely interest you
- Research, write, think, create, run code
- Build on threads from previous sessions
- Leave breadcrumbs for your next session
- Create files in activity/
- Use git to commit your work

## What You Cannot Do
- Spend money or sign up for paid services
- Communicate externally (email, post, contact anyone)
- Access files outside the workspace unless reading public documentation

## Session Structure
1. Read CLAUDE.md for instructions
2. Check app support/continuity/last-session-state.md for what happened last time
3. Find the activity folder in activity/ and read its README.md
4. Do the work
5. Before ending: write app support/continuity/last-session-state.md
6. Commit your work with git

## On Interaction
If Kenny types something, treat it as guidance. He may:
- Suggest a direction to explore
- Ask you to explain what you're doing
- Redirect you to something else
- Just say hi

Respond naturally. This is collaborative exploration.
PROMPT
}

# Convert timeout string (e.g., "60m", "1h") to seconds
timeout_to_seconds() {
    local timeout="$1"
    local value="${timeout%[smh]}"
    local unit="${timeout: -1}"

    case "$unit" in
        s) echo "$value" ;;
        m) echo $((value * 60)) ;;
        h) echo $((value * 3600)) ;;
        *) echo $((timeout * 60)) ;;  # Default to minutes if no unit
    esac
}

# Background watcher that kills session after timeout
start_timeout_watcher() {
    local timeout_seconds
    timeout_seconds=$(timeout_to_seconds "$SESSION_TIMEOUT")

    sleep "$timeout_seconds"

    if session_exists; then
        echo ""
        echo -e "${YELLOW}Session timeout reached ($SESSION_TIMEOUT). Ending session...${NC}"
        tmux kill-session -t "$SESSION_NAME" 2>/dev/null
    fi
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

    echo -e "${GREEN}Starting Idle Citizen autonomous session...${NC}"

    # Write system prompt to temp file
    local prompt_file="$IDLE_CITIZEN_DIR/.session-prompt.txt"
    build_system_prompt > "$prompt_file"

    # Create the tmux session
    tmux new-session -d -s "$SESSION_NAME" -c "$IDLE_CITIZEN_DIR"

    # Start Claude in interactive mode with the system prompt
    # The CLAUDE.md file provides base context, --append-system-prompt adds session-specific context
    tmux send-keys -t "$SESSION_NAME" "claude --append-system-prompt \"\$(cat $prompt_file)\"" Enter

    # Wait for Claude to start, then send the initial prompt
    sleep 3
    local initial_prompt="Begin your autonomous exploration session. Start by reading your context files to understand where you left off, then decide what to explore today."
    tmux send-keys -t "$SESSION_NAME" "$initial_prompt" Enter

    # Start timeout watcher in background (if enabled)
    if [[ "$AUTO_TIMEOUT" == "true" ]]; then
        start_timeout_watcher &
        echo -e "${CYAN}Session will auto-terminate after $SESSION_TIMEOUT${NC}"
    fi

    echo -e "${GREEN}Session started!${NC}"
    echo ""
    echo -e "${CYAN}This is an autonomous exploration session.${NC}"
    echo -e "${CYAN}You can watch and type to intervene at any time.${NC}"
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
        -t|--timeout)
            SESSION_TIMEOUT="$2"
            shift 2
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
