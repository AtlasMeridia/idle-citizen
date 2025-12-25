#!/bin/bash
# Generate metrics and open dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Generating metrics..."
python3 extract-metrics.py > metrics.json

if [ $? -eq 0 ]; then
    echo "Opening dashboard..."
    open dashboard.html
else
    echo "Error generating metrics"
    exit 1
fi
