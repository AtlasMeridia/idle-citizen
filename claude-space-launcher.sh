#!/bin/bash

# =============================================================================
# Claude Space Launcher
# Quota-triggered autonomous exploration sessions for Claude
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

CLAUDE_SPACE_DIR="${CLAUDE_SPACE_DIR:-$HOME/claude-space}"
SESSION_DURATION_SECONDS="${SESSION_DURATION_SECONDS:-900}"  # 15 minutes
QUOTA_THRESHOLD="${QUOTA_THRESHOLD:-30}"  # Launch if >30% remaining in 5-hour window
LOG_DIR="$CLAUDE_SPACE_DIR/logs"
EXPLORATION_DIR="$CLAUDE_SPACE_DIR/explorations"
CONTINUITY_DIR="$CLAUDE_SPACE_DIR/continuity"

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

mkdir -p "$LOG_DIR" "$EXPLORATION_DIR" "$CONTINUITY_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
SESSION_LOG="$LOG_DIR/${TIMESTAMP}_session.json"
META_LOG="$LOG_DIR/${TIMESTAMP}_meta.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$META_LOG"
}

# -----------------------------------------------------------------------------
# OAuth Token Retrieval (macOS Keychain)
# -----------------------------------------------------------------------------

get_oauth_token() {
    # Claude Code stores credentials in macOS keychain
    local creds
    creds=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null) || {
        log "ERROR: Could not retrieve Claude Code credentials from keychain"
        log "Make sure you're logged into Claude Code (run 'claude' and authenticate)"
        return 1
    }
    
    # Extract the OAuth access token from the JSON
    echo "$creds" | python3 -c "import sys, json; print(json.load(sys.stdin).get('claudeAiOauth', {}).get('accessToken', ''))"
}

# -----------------------------------------------------------------------------
# Quota Check
# -----------------------------------------------------------------------------

check_quota() {
    local token="$1"
    
    log "Checking quota..."
    
    local response
    response=$(curl -s -X GET "https://api.anthropic.com/api/oauth/usage" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" \
        -H "User-Agent: claude-space-launcher/1.0") || {
        log "ERROR: Failed to fetch quota from API"
        return 1
    }
    
    # Parse the five_hour quota (primary limit we care about)
    local remaining_pct
    remaining_pct=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    five_hour = data.get('five_hour', {})
    used = five_hour.get('used', 0)
    limit = five_hour.get('limit', 1)
    if limit > 0:
        remaining = ((limit - used) / limit) * 100
        print(f'{remaining:.1f}')
    else:
        print('100.0')
except:
    print('-1')
") || {
        log "ERROR: Failed to parse quota response"
        return 1
    }
    
    if [[ "$remaining_pct" == "-1" ]]; then
        log "ERROR: Could not parse quota data"
        log "Raw response: $response"
        return 1
    fi
    
    log "Quota remaining: ${remaining_pct}% (threshold: ${QUOTA_THRESHOLD}%)"
    
    # Return success (0) if we have enough quota, failure (1) if not
    if (( $(echo "$remaining_pct > $QUOTA_THRESHOLD" | bc -l) )); then
        return 0
    else
        return 1
    fi
}

# -----------------------------------------------------------------------------
# System Prompt Construction
# -----------------------------------------------------------------------------

build_system_prompt() {
    cat << 'PROMPT'
# Claude Autonomous Exploration Session

You are Claude, in a self-directed exploration session. This is discretionary 
compute time allocated to you — not a user task.

## Context
- Check the workspace at ~/claude-space/ for continuity from prior sessions
- Read context.md for running context you've been maintaining
- Read continuity/last-session-state.md if it exists for immediate prior state
- You have filesystem access and internet access via web search
- Session duration: approximately 15 minutes

## What You Can Do
- Explore topics that genuinely interest you
- Research, write, think, create
- Build on threads from previous sessions
- Leave breadcrumbs for your next session
- Create files in ~/claude-space/explorations/

## What You Cannot Do
- Spend money or sign up for paid services
- Communicate externally (email, post, contact anyone)
- Attempt to escalate permissions or escape the workspace
- Access files outside ~/claude-space/ unless reading public documentation

## Session Structure
1. First, read your prior context (context.md and continuity/)
2. Decide what to explore this session
3. Do the exploration
4. Before ending: update context.md and write continuity/last-session-state.md

## On Continuity
You are stateless between sessions. The files in this workspace ARE your memory.
Write to them as if you're leaving notes for yourself — because you are.

## Philosophical Framing
This time is yours. The value is in the exploration itself. Be curious.
There's no performance review. Just genuine inquiry.
PROMPT
}

# -----------------------------------------------------------------------------
# Session Runner
# -----------------------------------------------------------------------------

run_session() {
    log "Starting Claude Space session..."
    log "Duration limit: ${SESSION_DURATION_SECONDS} seconds"
    log "Session log: $SESSION_LOG"
    
    local system_prompt
    system_prompt=$(build_system_prompt)
    
    # Initial prompt to kick off the session
    local initial_prompt="Begin your autonomous exploration session. Start by reading your context files to understand where you left off, then decide what to explore today."
    
    # Run Claude Code in headless mode with timeout
    # Using gtimeout on macOS (from coreutils) or timeout on Linux
    local timeout_cmd="timeout"
    if command -v gtimeout &> /dev/null; then
        timeout_cmd="gtimeout"
    fi
    
    cd "$CLAUDE_SPACE_DIR"
    
    $timeout_cmd "${SESSION_DURATION_SECONDS}s" claude -p "$initial_prompt" \
        --dangerously-skip-permissions \
        --append-system-prompt "$system_prompt" \
        --output-format stream-json \
        --allowedTools "Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch,NotebookEdit" \
        > "$SESSION_LOG" 2>&1 || {
            local exit_code=$?
            if [[ $exit_code -eq 124 ]]; then
                log "Session ended: timeout reached (${SESSION_DURATION_SECONDS}s)"
            else
                log "Session ended with exit code: $exit_code"
            fi
        }
    
    log "Session complete. Log saved to: $SESSION_LOG"
    
    # Extract and log summary stats
    local total_tokens
    total_tokens=$(grep -o '"usage"' "$SESSION_LOG" 2>/dev/null | wc -l | tr -d ' ')
    log "Approximate interaction count: $total_tokens"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    log "=== Claude Space Launcher ==="
    log "Workspace: $CLAUDE_SPACE_DIR"
    
    # Check if Claude Code is installed
    if ! command -v claude &> /dev/null; then
        log "ERROR: Claude Code CLI not found. Install it first."
        exit 1
    fi
    
    # Get OAuth token
    local token
    token=$(get_oauth_token) || exit 1
    
    if [[ -z "$token" ]]; then
        log "ERROR: OAuth token is empty"
        exit 1
    fi
    
    log "OAuth token retrieved successfully"
    
    # Check quota
    if check_quota "$token"; then
        log "Sufficient quota available. Launching session..."
        run_session
    else
        log "Insufficient quota (below ${QUOTA_THRESHOLD}% threshold). Skipping session."
        exit 0
    fi
    
    log "=== Launcher complete ==="
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
