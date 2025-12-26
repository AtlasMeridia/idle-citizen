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
QUOTA_THRESHOLD="${QUOTA_THRESHOLD:-30}"  # Won't launch if below this %
WATCH_SESSION="${WATCH_SESSION:-true}"    # If true, open Terminal window to watch session

# Auto-scaling thresholds: run more sessions when quota is plentiful
QUOTA_HIGH=80    # Above this: run up to 3 sessions
QUOTA_MEDIUM=50  # Above this: run up to 2 sessions
                 # Below QUOTA_MEDIUM: run 1 session
LOG_DIR="$IDLE_CITIZEN_DIR/app support/logs"

# Dynamic session duration based on quota (in seconds)
MIN_SESSION_DURATION=900    # 15 minutes minimum
MAX_SESSION_DURATION=3600   # 60 minutes maximum
ACTIVITY_DIR="$IDLE_CITIZEN_DIR/activity"

# Graceful shutdown sentinel file (session creates this when done)
DONE_SENTINEL="$IDLE_CITIZEN_DIR/.session-done"

# Metrics rotation settings
MAX_METRICS_SIZE_KB=1024    # Rotate when metrics.jsonl exceeds 1MB
MAX_METRICS_BACKUPS=5       # Keep this many rotated files

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

mkdir -p "$LOG_DIR" "$ACTIVITY_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
SESSION_LOG="$LOG_DIR/${TIMESTAMP}_session.json"
META_LOG="$LOG_DIR/${TIMESTAMP}_meta.log"
LOCKFILE="$IDLE_CITIZEN_DIR/.launcher.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$META_LOG"
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

check_dropbox_access() {
    local dropbox_path="$HOME/Library/CloudStorage/Dropbox"
    if [[ -d "$dropbox_path" ]] && ! ls "$dropbox_path" >/dev/null 2>&1; then
        log "WARNING: Dropbox inaccessible - grant Full Disk Access to claude"
        log "  System Settings > Privacy & Security > Full Disk Access"
        return 1
    fi
    return 0
}

validate_activity() {
    local activity_dir="$1"
    local activities=()

    # Find all activity folders with README.md
    while IFS= read -r -d '' readme; do
        local dir
        dir=$(dirname "$readme")
        activities+=("$dir")
    done < <(find "$activity_dir" -mindepth 2 -maxdepth 2 -name "README.md" -print0 2>/dev/null)

    if [[ ${#activities[@]} -eq 0 ]]; then
        log "ERROR: No valid activity found in $activity_dir"
        log "  Expected: activity/{name}/README.md"
        return 1
    fi

    log "Found ${#activities[@]} activity folder(s):"
    for act in "${activities[@]}"; do
        local name
        name=$(basename "$act")
        log "  - $name"
    done

    return 0
}

list_activities() {
    local activity_dir="$1"
    local results=()

    while IFS= read -r -d '' readme; do
        local dir name priority
        dir=$(dirname "$readme")
        name=$(basename "$dir")

        # Extract priority from README (default 50)
        # Format: "Priority: N" on its own line
        priority=$(grep -E "^Priority:\s*[0-9]+" "$readme" 2>/dev/null | head -1 | grep -oE "[0-9]+" || echo 50)

        results+=("${priority}:${name}:${dir}")
    done < <(find "$activity_dir" -mindepth 2 -maxdepth 2 -name "README.md" -print0 2>/dev/null)

    # Sort by priority descending
    printf '%s\n' "${results[@]}" | sort -t: -k1 -nr
}

select_activity() {
    local activities="$1"
    local session_num="$2"

    local count
    count=$(echo "$activities" | grep -c . || echo 0)

    if [[ $count -eq 0 ]]; then
        echo ""
        return 1
    elif [[ $count -eq 1 ]]; then
        # Single activity - always use it
        echo "$activities" | cut -d: -f3
    else
        # Multiple activities - round-robin by session number
        local index=$(( (session_num - 1) % count + 1 ))
        echo "$activities" | sed -n "${index}p" | cut -d: -f3
    fi
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
# OAuth Token Retrieval
# -----------------------------------------------------------------------------

get_oauth_token() {
    # Claude Code stores credentials in macOS Keychain
    local creds_json
    creds_json=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null)

    if [[ -z "$creds_json" ]]; then
        log "ERROR: Credentials not found in macOS Keychain"
        log "Make sure you're logged into Claude Code (run 'claude' and authenticate)"
        return 1
    fi

    echo "$creds_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('claudeAiOauth', {}).get('accessToken', ''))"
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

    # Parse quota from all relevant limits and return the most constraining one
    # API returns utilization as percentage used (e.g., 2.0 means 2% used)
    # We check both five_hour (session) and seven_day (weekly) limits
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)

    # Session limit (5-hour rolling window)
    five_hour = data.get('five_hour', {})
    session_remaining = 100 - five_hour.get('utilization', 0)

    # Weekly limit (7-day rolling window, all models)
    seven_day = data.get('seven_day', {})
    weekly_remaining = 100 - seven_day.get('utilization', 0)

    # Return the most constraining limit (minimum remaining)
    effective_remaining = min(session_remaining, weekly_remaining)
    print(f'{effective_remaining:.1f}')
except:
    print('-1')
"
}

# -----------------------------------------------------------------------------
# Calculate max sessions based on quota (auto-scaling)
# Higher quota = more sessions to use it up
# -----------------------------------------------------------------------------

calculate_max_sessions() {
    local quota_pct="$1"

    python3 -c "
quota = float('$quota_pct')
high = $QUOTA_HIGH
medium = $QUOTA_MEDIUM

if quota > high:
    print(3)
elif quota > medium:
    print(2)
else:
    print(1)
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
    local activity_path="${1:-}"
    local activity_name=""

    if [[ -n "$activity_path" ]]; then
        activity_name=$(basename "$activity_path")
    fi

    cat << PROMPT
# Claude Autonomous Session

You are Claude, in a self-directed session. This is discretionary compute time
allocated to you from Kenny's Max plan — use it to produce something concrete.

## Workspace
- ~/Projects/idle-citizen/ is your workspace
- Read CLAUDE.md for instructions
PROMPT

    if [[ -n "$activity_name" ]]; then
        cat << PROMPT

## Current Activity: $activity_name
Focus on the activity at: activity/$activity_name/README.md
Follow its instructions for this session.
PROMPT
    else
        cat << PROMPT
- Find the activity folder in activity/ and follow its README
PROMPT
    fi

    cat << 'PROMPT'

## Philosophy
The goal is to use quota that would otherwise expire. Produce things. Some will
be useful, some won't. That's fine. Iterate, accumulate, let patterns emerge.

## Graceful Shutdown
If you complete your work before time runs out, signal completion by running:
  touch ~/Projects/idle-citizen/.session-done
This allows the launcher to end early and save quota for future sessions.
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
    # Kill any tail processes watching our log file
    pkill -f "tail -f.*idle-citizen.*session.json" 2>/dev/null || true

    # Close Terminal windows with our title (try multiple methods)
    osascript << 'EOF' 2>/dev/null || true
tell application "Terminal"
    set windowsToClose to {}
    repeat with w in windows
        try
            if name of w contains "Idle Citizen Session" then
                set end of windowsToClose to w
            end if
        end try
    end repeat
    repeat with w in windowsToClose
        try
            close w saving no
        end try
    end repeat
end tell
EOF

    # Clean up temp script
    if [[ -n "${WATCH_SCRIPT_PATH:-}" ]]; then
        rm -f "$WATCH_SCRIPT_PATH"
        # Also kill any process still running the script
        pkill -f "idle-citizen-watch-" 2>/dev/null || true
    fi
}

# -----------------------------------------------------------------------------
# Session Runner
# -----------------------------------------------------------------------------

# Global for metrics tracking
CURRENT_ACTIVITY=""

run_session() {
    local duration_seconds="$1"
    local activity_path="${2:-}"
    local duration_minutes=$((duration_seconds / 60))

    # Store activity name for metrics
    if [[ -n "$activity_path" ]]; then
        CURRENT_ACTIVITY=$(basename "$activity_path")
    else
        CURRENT_ACTIVITY="unknown"
    fi

    log "Starting Idle Citizen session..."
    log "Activity: $CURRENT_ACTIVITY"
    log "Duration limit: ${duration_seconds} seconds (~${duration_minutes} minutes)"
    log "Session log: $SESSION_LOG"

    local system_prompt
    system_prompt=$(build_system_prompt "$activity_path")

    # Initial prompt to kick off the session
    local initial_prompt="Begin your autonomous exploration session. You have approximately ${duration_minutes} minutes. Start by reading your context files to understand where you left off, then decide what to explore today."

    # Run Claude Code in headless mode with timeout
    # Find timeout command: gtimeout (Homebrew coreutils), timeout (Linux), or gnutimeout
    local timeout_cmd=""
    for cmd in /opt/homebrew/bin/gtimeout /usr/local/bin/gtimeout gtimeout timeout gnutimeout; do
        if command -v "$cmd" &>/dev/null; then
            timeout_cmd="$cmd"
            break
        fi
    done

    if [[ -z "$timeout_cmd" ]]; then
        log "WARNING: No timeout command found. Session will run without time limit."
        log "  Install coreutils: brew install coreutils"
    fi

    # Remove any stale done sentinel
    rm -f "$DONE_SENTINEL"

    cd "$IDLE_CITIZEN_DIR"

    # Open watch terminal window (if WATCH_SESSION is enabled)
    if [[ "${WATCH_SESSION:-true}" == "true" ]]; then
        # Touch the log file so tail -f has something to watch
        touch "$SESSION_LOG"
        open_watch_terminal "$SESSION_LOG"
        sleep 1  # Give terminal time to open
    fi

    local session_exit_code=0
    local graceful_exit=false

    if [[ -n "$timeout_cmd" ]]; then
        # Run with timeout, but also monitor for graceful shutdown
        $timeout_cmd "${duration_seconds}s" claude -p "$initial_prompt" \
            --dangerously-skip-permissions \
            --append-system-prompt "$system_prompt" \
            --output-format stream-json \
            --verbose \
            --allowedTools "Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch,NotebookEdit" \
            > "$SESSION_LOG" 2>&1 || session_exit_code=$?
    else
        # Run without timeout (not recommended)
        claude -p "$initial_prompt" \
            --dangerously-skip-permissions \
            --append-system-prompt "$system_prompt" \
            --output-format stream-json \
            --verbose \
            --allowedTools "Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch,NotebookEdit" \
            > "$SESSION_LOG" 2>&1 || session_exit_code=$?
    fi

    # Check for graceful shutdown (session signaled completion)
    if [[ -f "$DONE_SENTINEL" ]]; then
        graceful_exit=true
        rm -f "$DONE_SENTINEL"
        log "Session ended: graceful shutdown (work completed)"
    elif [[ $session_exit_code -eq 124 ]]; then
        log "Session ended: timeout reached (${duration_seconds}s)"
    elif [[ $session_exit_code -eq 0 ]]; then
        log "Session ended: natural completion"
    else
        log "Session ended with exit code: $session_exit_code"
    fi

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

    # Analyze and record session outcome
    local outcome
    outcome=$(analyze_session_outcome "$SESSION_LOG" "$session_exit_code")
    record_session_metrics "$SESSION_LOG" "$outcome" "$duration_seconds" "${CURRENT_ACTIVITY:-unknown}"

    # Generate human-readable summary
    generate_session_summary "$SESSION_LOG"

    # Send macOS notification
    local files_created_count
    files_created_count=$(grep -c '"type":"create"' "$SESSION_LOG" 2>/dev/null) || files_created_count=0
    local notify_msg="$outcome - ${CURRENT_ACTIVITY:-unknown}"
    if [[ $files_created_count -gt 0 ]]; then
        notify_msg="$notify_msg ($files_created_count files created)"
    fi
    send_notification "Idle Citizen" "$notify_msg" "Session Complete"
}

# -----------------------------------------------------------------------------
# Session Outcome Tracking
# -----------------------------------------------------------------------------

METRICS_FILE="$LOG_DIR/metrics.jsonl"

# -----------------------------------------------------------------------------
# Metrics File Rotation
# -----------------------------------------------------------------------------

rotate_metrics_if_needed() {
    if [[ ! -f "$METRICS_FILE" ]]; then
        return 0
    fi

    local size_kb
    size_kb=$(du -k "$METRICS_FILE" 2>/dev/null | cut -f1)

    if [[ $size_kb -gt $MAX_METRICS_SIZE_KB ]]; then
        log "Rotating metrics file (${size_kb}KB > ${MAX_METRICS_SIZE_KB}KB)"

        # Shift existing backups
        for i in $(seq $((MAX_METRICS_BACKUPS - 1)) -1 1); do
            if [[ -f "${METRICS_FILE}.$i" ]]; then
                mv "${METRICS_FILE}.$i" "${METRICS_FILE}.$((i + 1))"
            fi
        done

        # Rotate current file
        mv "$METRICS_FILE" "${METRICS_FILE}.1"

        # Remove oldest if over limit
        rm -f "${METRICS_FILE}.$((MAX_METRICS_BACKUPS + 1))"

        log "Metrics rotated. Previous file: ${METRICS_FILE}.1"
    fi
}

# -----------------------------------------------------------------------------
# Human-Readable Session Summary
# -----------------------------------------------------------------------------

generate_session_summary() {
    local session_log="$1"
    local summary_file="${session_log%.json}_summary.txt"

    if [[ ! -f "$session_log" ]]; then
        return 1
    fi

    # Extract counts before the subshell to avoid output leakage
    # Note: grep -c outputs "0" even on no match, but exits with code 1
    # So we capture the output directly without || fallback
    local session_id
    session_id=$(grep -o '"session_id":"[^"]*"' "$session_log" 2>/dev/null | head -1 | cut -d'"' -f4)
    [[ -z "$session_id" ]] && session_id="unknown"

    local tool_uses files_created files_edited text_responses
    tool_uses=$(grep -c '"type":"tool_use"' "$session_log" 2>/dev/null) || tool_uses=0
    files_created=$(grep -c '"type":"create"' "$session_log" 2>/dev/null) || files_created=0
    files_edited=$(grep -c '"type":"update"' "$session_log" 2>/dev/null) || files_edited=0
    text_responses=$(grep -c '"type":"text"' "$session_log" 2>/dev/null) || text_responses=0

    {
        echo "═══════════════════════════════════════════════════════════════════════════════"
        echo "                         IDLE CITIZEN SESSION SUMMARY"
        echo "═══════════════════════════════════════════════════════════════════════════════"
        echo ""
        echo "Session: $(basename "$session_log")"
        echo "Generated: $(date)"
        echo ""
        echo "Session ID: $session_id"
        echo ""
        echo "─── Statistics ───────────────────────────────────────────────────────────────"
        echo "Tool Uses:      $tool_uses"
        echo "Files Created:  $files_created"
        echo "Files Edited:   $files_edited"
        echo "Text Responses: $text_responses"

        # Extract created files
        echo ""
        echo "─── Files Created ──────────────────────────────────────────────────────────"
        local created_files
        created_files=$(grep '"type":"create"' "$session_log" 2>/dev/null | grep -o '"filePath":"[^"]*"' | cut -d'"' -f4)
        if [[ -n "$created_files" ]]; then
            echo "$created_files" | while read -r filepath; do
                echo "  + $filepath"
            done
        else
            echo "  (none)"
        fi

        # Extract text output
        echo ""
        echo "─── Claude's Thoughts ────────────────────────────────────────────────────────"
        grep '"type":"assistant"' "$session_log" 2>/dev/null | \
            jq -r '.message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null | \
            head -50 | fold -w 78 || echo "  (no text output)"

        echo ""
        echo "═══════════════════════════════════════════════════════════════════════════════"
    } > "$summary_file" 2>/dev/null

    if [[ -f "$summary_file" ]]; then
        log "Session summary: $summary_file"
        echo "$summary_file"
    fi
}

# -----------------------------------------------------------------------------
# macOS Notifications
# -----------------------------------------------------------------------------

send_notification() {
    local title="$1"
    local message="$2"
    local subtitle="${3:-}"

    # Use osascript for native macOS notifications
    osascript -e "display notification \"$message\" with title \"$title\"${subtitle:+ subtitle \"$subtitle\"}" 2>/dev/null || true
}

analyze_session_outcome() {
    local session_log="$1"
    local exit_code="${2:-0}"

    if [[ ! -f "$session_log" ]]; then
        echo "failed"
        return
    fi

    local files_created errors_count permission_blocked

    # Count file creations (Write tool completions)
    files_created=$(grep -c '"type":"create"' "$session_log" 2>/dev/null) || files_created=0

    # Count errors in tool results
    errors_count=$(grep -c '"is_error":true' "$session_log" 2>/dev/null) || errors_count=0

    # Check for permission blocks
    permission_blocked=false
    if grep -q "Operation not permitted" "$session_log" 2>/dev/null; then
        permission_blocked=true
    fi

    # Classification logic (timeout counts as complete if productive)
    if $permission_blocked && [[ $files_created -eq 0 ]]; then
        echo "blocked"
    elif [[ $files_created -gt 0 ]]; then
        if [[ $errors_count -gt 3 ]]; then
            echo "partial"
        else
            echo "complete"
        fi
    elif [[ $errors_count -gt 0 ]]; then
        echo "failed"
    else
        echo "partial"
    fi
}

record_session_metrics() {
    local session_log="$1"
    local outcome="$2"
    local duration="$3"
    local activity="${4:-unknown}"

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local files_created tool_uses session_id

    files_created=$(grep -c '"type":"create"' "$session_log" 2>/dev/null) || files_created=0
    tool_uses=$(grep -c '"type":"tool_use"' "$session_log" 2>/dev/null) || tool_uses=0
    session_id=$(grep -o '"session_id":"[^"]*"' "$session_log" 2>/dev/null | head -1 | cut -d'"' -f4 || echo "unknown")

    # Append JSONL record
    printf '{"timestamp":"%s","session_id":"%s","outcome":"%s","duration_seconds":%d,"files_created":%d,"tool_uses":%d,"activity":"%s","log_file":"%s"}\n' \
        "$timestamp" "$session_id" "$outcome" "$duration" "$files_created" "$tool_uses" "$activity" "$(basename "$session_log")" \
        >> "$METRICS_FILE"

    log "Session outcome: $outcome (files: $files_created, tools: $tool_uses)"

    # Rotate metrics file if needed
    rotate_metrics_if_needed
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

run_single_session() {
    local token="$1"
    local activity_path="${2:-}"

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

    run_session "$session_duration" "$activity_path"
    return 0
}

main() {
    log "=== Idle Citizen Launcher ==="
    log "Workspace: $IDLE_CITIZEN_DIR"

    # Acquire lock to prevent concurrent sessions
    if ! acquire_lock; then
        exit 0
    fi

    # Check if Claude Code is installed
    if ! command -v claude &> /dev/null; then
        log "ERROR: Claude Code CLI not found. Install it first."
        exit 1
    fi

    # Pre-flight checks
    check_dropbox_access  # Warn if Dropbox inaccessible (doesn't block)

    if ! validate_activity "$ACTIVITY_DIR"; then
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

    # Check initial quota to determine max sessions (auto-scaling)
    log "Checking quota for auto-scaling..."
    local initial_quota
    initial_quota=$(get_quota_remaining "$token")

    if [[ "$initial_quota" == "-1" ]]; then
        log "ERROR: Could not determine quota"
        exit 1
    fi

    local max_sessions
    max_sessions=$(calculate_max_sessions "$initial_quota")
    log "Quota: ${initial_quota}% → auto-scaling to max $max_sessions session(s)"

    # Get activity list for rotation
    local activities
    activities=$(list_activities "$ACTIVITY_DIR")

    # Run sessions up to the calculated max
    local session_count=0
    while [[ $session_count -lt $max_sessions ]]; do
        # Select activity for this session (1-indexed)
        local session_num=$((session_count + 1))
        local activity_path
        activity_path=$(select_activity "$activities" "$session_num")

        if ! run_single_session "$token" "$activity_path"; then
            if [[ $session_count -eq 0 ]]; then
                log "Skipping session (quota too low)."
            else
                log "Stopping after $session_count session(s) (quota depleted)."
            fi
            break
        fi

        ((session_count++))

        if [[ $session_count -lt $max_sessions ]]; then
            log "=== Session $session_count complete. Pausing before next session... ==="
            sleep 10  # Brief pause between sessions

            # Re-check quota before starting next session
            log "Re-checking quota before next session..."
            local updated_quota
            updated_quota=$(get_quota_remaining "$token")

            if [[ "$updated_quota" == "-1" ]]; then
                log "WARNING: Could not re-check quota. Continuing with caution."
            elif (( $(echo "$updated_quota <= $QUOTA_THRESHOLD" | bc -l) )); then
                log "Quota now below threshold (${updated_quota}% <= ${QUOTA_THRESHOLD}%). Stopping."
                break
            else
                # Recalculate max sessions based on updated quota
                local new_max
                new_max=$(calculate_max_sessions "$updated_quota")
                if [[ $new_max -lt $max_sessions ]]; then
                    log "Quota dropped: reducing max sessions from $max_sessions to $new_max"
                    max_sessions=$new_max
                fi
                log "Quota: ${updated_quota}% - continuing with session $((session_count + 1))"
            fi
        fi
    done

    if [[ $session_count -gt 0 ]]; then
        log "Completed $session_count session(s)."
    fi

    log "=== Launcher complete ==="
}

# Run if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
