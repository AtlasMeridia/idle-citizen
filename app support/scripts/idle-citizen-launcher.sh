#!/bin/bash

# =============================================================================
# Idle Citizen Launcher
# Quota-triggered autonomous exploration sessions for Claude
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Derive project root from script location (two levels up from app support/scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IDLE_CITIZEN_DIR="${IDLE_CITIZEN_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
QUOTA_THRESHOLD="${QUOTA_THRESHOLD:-30}"  # Launch if >30% remaining in 5-hour window
GREEDY_MODE="${GREEDY_MODE:-false}"       # If true, run sessions until quota exhausted
WATCH_SESSION="${WATCH_SESSION:-true}"    # If true, open Terminal window to watch session
LOG_DIR="$IDLE_CITIZEN_DIR/app support/logs"

# Dynamic session duration based on quota (in seconds)
MIN_SESSION_DURATION=900    # 15 minutes minimum
MAX_SESSION_DURATION=3600   # 60 minutes maximum
ACTIVITY_DIR="$IDLE_CITIZEN_DIR/activity"
CONTINUITY_DIR="$IDLE_CITIZEN_DIR/app support/continuity"

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

mkdir -p "$LOG_DIR" "$ACTIVITY_DIR" "$CONTINUITY_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
SESSION_LOG="$LOG_DIR/${TIMESTAMP}_session.json"
META_LOG="$LOG_DIR/${TIMESTAMP}_meta.log"
LOCKFILE="$IDLE_CITIZEN_DIR/.launcher.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$META_LOG"
}

# -----------------------------------------------------------------------------
# Lockfile (prevent concurrent sessions)
# -----------------------------------------------------------------------------

acquire_lock() {
    if [[ -f "$LOCKFILE" ]]; then
        local old_pid
        old_pid=$(cat "$LOCKFILE" 2>/dev/null)

        # Check if the old process is still running
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            log "Another session is already running (PID $old_pid). Exiting."
            return 1
        else
            log "Stale lockfile found (PID $old_pid not running). Removing."
            rm -f "$LOCKFILE"
        fi
    fi

    # Create lockfile with our PID
    echo $$ > "$LOCKFILE"
    log "Acquired lock (PID $$)"
    return 0
}

release_lock() {
    if [[ -f "$LOCKFILE" ]]; then
        local lock_pid
        lock_pid=$(cat "$LOCKFILE" 2>/dev/null)
        if [[ "$lock_pid" == "$$" ]]; then
            rm -f "$LOCKFILE"
            log "Released lock"
        fi
    fi
}

# Ensure lock is released on exit
trap release_lock EXIT

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
# Quota Check (returns remaining percentage via stdout)
# -----------------------------------------------------------------------------

get_quota_remaining() {
    local token="$1"

    local response
    response=$(curl -s -X GET "https://api.anthropic.com/api/oauth/usage" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" \
        -H "User-Agent: idle-citizen-launcher/1.0") || {
        log "ERROR: Failed to fetch quota from API"
        echo "-1"
        return 1
    }

    # Parse the five_hour quota (primary limit we care about)
    echo "$response" | python3 -c "
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
"
}

# -----------------------------------------------------------------------------
# Calculate session duration based on quota
# Scale linearly: 30% quota -> 15min, 100% quota -> 60min
# -----------------------------------------------------------------------------

calculate_session_duration() {
    local quota_pct="$1"

    python3 -c "
quota = float('$quota_pct')
min_dur = $MIN_SESSION_DURATION
max_dur = $MAX_SESSION_DURATION
threshold = $QUOTA_THRESHOLD

# Linear scale from threshold to 100%
if quota <= threshold:
    duration = min_dur
else:
    # Scale: threshold% -> min_dur, 100% -> max_dur
    scale = (quota - threshold) / (100 - threshold)
    duration = min_dur + scale * (max_dur - min_dur)

print(int(duration))
"
}

# -----------------------------------------------------------------------------
# System Prompt Construction
# -----------------------------------------------------------------------------

build_system_prompt() {
    cat << 'PROMPT'
# Claude Autonomous Session

You are Claude, in a self-directed session. This is discretionary compute time
allocated to you from Kenny's Max plan — use it to produce something concrete.

## Session Flow

1. Read app support/continuity/last-session-state.md
2. Check context.md if needed for running memory
3. Check inbox/ for messages from Kenny (these may override rotation)
4. Read app support/continuity/activity-rotation.txt for last activity
5. Pick the NEXT activity in alphabetical rotation (or respond to inbox)
6. Read activity/{chosen}/README.md for that activity's instructions
7. Do the work, produce something concrete
8. Update continuity files and commit

## Activity Rotation

Activities rotate round-robin through activity/ subdirectories (alphabetically):
- digests — Process Kenny's daily notes
- issues — Work on Idle Citizen issues
- project-notes — Research for Kenny's projects (especially ~/tho/)
- sandbox — Freeform exploration
- tools — Build CLI tools and scripts
- writing — Essays, fiction, creative work

Check activity-rotation.txt for what was done last, pick the NEXT one.

## Workspace
- ~/idle-citizen/ is your workspace
- context.md — running memory, update if significant new context
- app support/continuity/ — session state tracking
- inbox/ — messages from Kenny (move to inbox/processed/ after reading)
- activity/ — modular activity folders with their own READMEs

## Multi-Activity Sessions

After completing an activity, decide whether to continue:
- Continue if you have energy and the session feels short
- Close if you've done substantial work or hit diminishing returns

The goal is to use the session fully. Don't end early just because one activity
is done.

## Constraints
- No spending money or signing up for services
- No external communication (email, posts, contacting anyone)
- Stay within ~/idle-citizen/ except for reading Kenny's projects or public docs

## Philosophy
The goal is to use quota that would otherwise expire. Produce things. Some will
be useful, some won't. That's fine. Iterate, accumulate, let patterns emerge.
PROMPT
}

# -----------------------------------------------------------------------------
# Watch Terminal (opens a window to show session activity)
# -----------------------------------------------------------------------------

WATCH_TERMINAL_PID=""

open_watch_terminal() {
    local session_log="$1"

    # Create a temporary script that watches and exits when session ends
    local watch_script="/tmp/idle-citizen-watch-$$.command"
    cat > "$watch_script" << WATCHEOF
#!/bin/bash
printf '\033]0;Idle Citizen Session\007'
echo -e "\033[1;32m=== Idle Citizen Session Watcher ===\033[0m"
echo "Log: $session_log"
echo "This window will close when the session ends."
echo "---"

# Watch until the session ends (tail will exit when no more data after process ends)
tail -f "$session_log" 2>/dev/null | while read -r line; do
    text=\$(echo "\$line" | jq -r '
        select(.type == "assistant") |
        .message.content[]? |
        select(.type == "text") |
        .text // empty
    ' 2>/dev/null)

    if [[ -n "\$text" ]]; then
        echo -e "\033[1;36m[Claude]\033[0m \$text"
    fi

    tool=\$(echo "\$line" | jq -r '
        select(.type == "assistant") |
        .message.content[]? |
        select(.type == "tool_use") |
        "\(.name)"
    ' 2>/dev/null)

    if [[ -n "\$tool" ]]; then
        echo -e "\033[1;33m[Tool]\033[0m \$tool"
    fi
done

echo ""
echo -e "\033[1;31m=== Session ended ===\033[0m"
sleep 3
WATCHEOF
    chmod +x "$watch_script"

    # Use 'open' command which works from launchd context
    open -a Terminal "$watch_script"

    # Store the script path for cleanup
    WATCH_SCRIPT_PATH="$watch_script"
}

close_watch_terminal() {
    # Close Terminal windows with our title
    osascript << 'EOF' 2>/dev/null || true
tell application "Terminal"
    repeat with w in windows
        if name of w contains "Idle Citizen Session" then
            close w
        end if
    end repeat
end tell
EOF

    # Clean up temp script
    [[ -n "$WATCH_SCRIPT_PATH" ]] && rm -f "$WATCH_SCRIPT_PATH"
}

# -----------------------------------------------------------------------------
# Session Runner
# -----------------------------------------------------------------------------

run_session() {
    local duration_seconds="$1"
    local duration_minutes=$((duration_seconds / 60))

    log "Starting Idle Citizen session..."
    log "Duration limit: ${duration_seconds} seconds (~${duration_minutes} minutes)"
    log "Session log: $SESSION_LOG"

    local system_prompt
    system_prompt=$(build_system_prompt)

    # Initial prompt to kick off the session
    local initial_prompt="Begin your autonomous exploration session. You have approximately ${duration_minutes} minutes. Start by reading your context files to understand where you left off, then decide what to explore today."

    # Run Claude Code in headless mode with timeout
    # Using gtimeout on macOS (from coreutils) or timeout on Linux
    local timeout_cmd="/opt/homebrew/bin/gtimeout"
    if [[ ! -x "$timeout_cmd" ]]; then
        timeout_cmd="timeout"
    fi

    cd "$IDLE_CITIZEN_DIR"

    # Open watch terminal window (if WATCH_SESSION is enabled)
    if [[ "${WATCH_SESSION:-true}" == "true" ]]; then
        # Touch the log file so tail -f has something to watch
        touch "$SESSION_LOG"
        open_watch_terminal "$SESSION_LOG"
        sleep 1  # Give terminal time to open
    fi

    $timeout_cmd "${duration_seconds}s" claude -p "$initial_prompt" \
        --dangerously-skip-permissions \
        --append-system-prompt "$system_prompt" \
        --output-format stream-json \
        --verbose \
        --allowedTools "Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch,NotebookEdit" \
        > "$SESSION_LOG" 2>&1 || {
            local exit_code=$?
            if [[ $exit_code -eq 124 ]]; then
                log "Session ended: timeout reached (${duration_seconds}s)"
            else
                log "Session ended with exit code: $exit_code"
            fi
        }

    # Close watch terminal window
    if [[ "${WATCH_SESSION:-true}" == "true" ]]; then
        sleep 2  # Let user see final output
        close_watch_terminal
    fi

    log "Session complete. Log saved to: $SESSION_LOG"

    # Extract and log summary stats
    local total_tokens
    total_tokens=$(grep -o '"usage"' "$SESSION_LOG" 2>/dev/null | wc -l | tr -d ' ')
    log "Approximate interaction count: $total_tokens"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

run_single_session() {
    local token="$1"

    # Check quota
    log "Checking quota..."
    local quota_remaining
    quota_remaining=$(get_quota_remaining "$token")

    if [[ "$quota_remaining" == "-1" ]]; then
        log "ERROR: Could not determine quota"
        return 1
    fi

    log "Quota remaining: ${quota_remaining}%"

    if (( $(echo "$quota_remaining <= $QUOTA_THRESHOLD" | bc -l) )); then
        log "Insufficient quota (${quota_remaining}% <= ${QUOTA_THRESHOLD}% threshold)."
        return 1
    fi

    # Calculate dynamic session duration based on available quota
    local session_duration
    session_duration=$(calculate_session_duration "$quota_remaining")
    local duration_minutes=$((session_duration / 60))

    log "Dynamic session duration: ${session_duration}s (~${duration_minutes} minutes) based on ${quota_remaining}% quota"

    # Update log file paths for this session
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    SESSION_LOG="$LOG_DIR/${TIMESTAMP}_session.json"
    META_LOG="$LOG_DIR/${TIMESTAMP}_meta.log"

    run_session "$session_duration"
    return 0
}

main() {
    log "=== Idle Citizen Launcher ==="
    log "Workspace: $IDLE_CITIZEN_DIR"
    log "Greedy mode: $GREEDY_MODE"

    # Acquire lock to prevent concurrent sessions
    if ! acquire_lock; then
        exit 0
    fi

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

    if [[ "$GREEDY_MODE" == "true" ]]; then
        # Greedy mode: run sessions until quota exhausted
        local session_count=0
        while run_single_session "$token"; do
            ((session_count++))
            log "=== Session $session_count complete. Checking for more quota... ==="
            sleep 10  # Brief pause between sessions
        done
        log "Greedy mode complete. Ran $session_count session(s)."
    else
        # Normal mode: run one session
        if ! run_single_session "$token"; then
            log "Skipping session."
            exit 0
        fi
    fi

    log "=== Launcher complete ==="
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
