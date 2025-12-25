# Idle Citizen Dashboard

A local web dashboard for reviewing autonomous session activity.

## Features

- Session count and duration tracking
- Quota utilization metrics
- Daily activity visualization
- Issue tracker statistics
- Recent git commits
- Artifacts by activity type

## Quick Start

```bash
# Generate metrics and open dashboard
./view.sh
```

Or manually:

```bash
# 1. Generate metrics
python3 extract-metrics.py > metrics.json

# 2. Open dashboard
open dashboard.html
```

## Files

- `extract-metrics.py` — Parses session logs, git history, and artifacts
- `dashboard.html` — Single-file web dashboard (no server needed)
- `metrics.json` — Generated data file (git-ignored)
- `view.sh` — Convenience script to refresh and open

## Data Sources

- Session logs: `app support/logs/*_meta.log`
- Git commits: Project git history
- Artifacts: `activity/*/*.md` files (excluding READMEs)
- Issues: `activity/issues/open/` and `activity/issues/closed/`

## Customization

Edit `extract-metrics.py` to adjust:
- Time range (default: 14 days)
- Weekly quota budget (default: 420 minutes)

Edit `dashboard.html` to customize styling or add charts.

## Notes

- Dashboard is fully local (no external dependencies except Chart.js CDN)
- Auto-refreshes data on page load
- Works offline after first load (Chart.js gets cached)
