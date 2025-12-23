#!/bin/bash
# Watch the current autonomous session in real-time
# Shows Claude's text output and tool calls

LOG_DIR="$HOME/claude-space/logs"

# Find the most recent session log
LATEST_LOG=$(ls -t "$LOG_DIR"/*.json 2>/dev/null | head -1)

if [[ -z "$LATEST_LOG" ]]; then
    echo "No session logs found in $LOG_DIR"
    exit 1
fi

echo "Watching: $LATEST_LOG"
echo "Press Ctrl+C to stop"
echo "---"

tail -f "$LATEST_LOG" 2>/dev/null | while read -r line; do
    # Extract text content from assistant messages
    text=$(echo "$line" | jq -r '
        select(.type == "assistant") |
        .message.content[]? |
        select(.type == "text") |
        .text // empty
    ' 2>/dev/null)

    if [[ -n "$text" ]]; then
        echo -e "\033[1;36m[Claude]\033[0m $text"
    fi

    # Extract tool calls
    tool=$(echo "$line" | jq -r '
        select(.type == "assistant") |
        .message.content[]? |
        select(.type == "tool_use") |
        "\(.name): \(.input | tostring | .[0:100])"
    ' 2>/dev/null)

    if [[ -n "$tool" ]]; then
        echo -e "\033[1;33m[Tool]\033[0m $tool"
    fi
done
