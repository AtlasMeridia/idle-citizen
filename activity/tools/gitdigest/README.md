# gitdigest

Summarize recent git activity in a repository. Useful for catching up on a project after time away, or getting a quick overview of what's been happening.

## Usage

```bash
# Basic usage - last 7 days in current repo
python3 gitdigest.py

# Last 30 days
python3 gitdigest.py -d 30

# Different repository
python3 gitdigest.py ~/projects/myapp

# Filter by author
python3 gitdigest.py -a "John"

# Date range
python3 gitdigest.py --since 2025-12-01 --until 2025-12-15

# JSON output (for scripting)
python3 gitdigest.py --json

# Faster (skip file statistics)
python3 gitdigest.py --no-stats
```

## Options

| Option | Description |
|--------|-------------|
| `-d, --days N` | Look back N days (default: 7) |
| `-n, --commits N` | Show top N commits (default: 10) |
| `-a, --author NAME` | Filter by author name or email |
| `--since DATE` | Start date (YYYY-MM-DD) |
| `--until DATE` | End date (YYYY-MM-DD) |
| `--json` | Output as JSON |
| `--no-stats` | Skip file change statistics (faster) |

## Output

The default output includes:

- **Summary stats**: Total commits, authors, lines added/removed
- **Contributors**: List of authors with commit counts
- **Recent commits**: Latest commits with hash, date, author, subject
- **Most changed files**: Files that were modified most frequently
- **Activity by day**: Commit distribution across days of the week

## Example Output

```
============================================================
  Git Digest: idle-citizen
  Branch: master | Period: 2025-11-23 to 2025-12-23
============================================================

  Commits: 22
  Authors: 1
  Lines:   +3967 / -560
  Files touched: 37

  Contributors:
    ellis isles                22 ████████████████████

  Recent Commits (showing 10):
    882ae7e 2025-12-23 ellis isles     Research: Speech recognition options for Tho
    bd33283 2025-12-22 ellis isles     Essay: The Illegible Substrate
    ...

  Most Changed Files:
    context.md                                    10 ██████████
    idle-citizen-launcher.sh                       8 ████████
    ...

  Activity by Day:
    Monday      21 ████████████████████
    Tuesday      1 █
    ...
```

## Requirements

- Python 3.6+
- Git (accessible via command line)

## Installation

No installation required. Just run the script:

```bash
chmod +x gitdigest.py
./gitdigest.py
```

Or create an alias:

```bash
alias gitdigest='python3 /path/to/gitdigest.py'
```
