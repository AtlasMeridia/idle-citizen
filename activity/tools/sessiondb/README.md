# sessiondb

Build a SQLite database of Idle Citizen activity for querying with SQL.

## Usage

```bash
# Build the database (in idle-citizen root)
python3 activity/tools/sessiondb/sessiondb.py

# Custom output file
python3 activity/tools/sessiondb/sessiondb.py -o my-database.db

# More git history
python3 activity/tools/sessiondb/sessiondb.py --days 365

# Just stats, minimal output
python3 activity/tools/sessiondb/sessiondb.py --quiet --stats
```

## Data Sources

The tool aggregates data from:

- **Sessions**: Parsed from `app support/logs/*_meta.log`
- **Commits**: Git history from the repository
- **Artifacts**: Markdown files in `activity/` folders (excluding READMEs)
- **Issues**: Issues from `activity/issues/open/` and `closed/`

## Schema

```sql
-- Sessions
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_seconds INTEGER,
    log_file TEXT NOT NULL UNIQUE
);

-- Commits
CREATE TABLE commits (
    hash TEXT PRIMARY KEY,
    author TEXT NOT NULL,
    date TEXT NOT NULL,
    message TEXT NOT NULL,
    files_changed INTEGER,
    insertions INTEGER,
    deletions INTEGER
);

-- Artifacts
CREATE TABLE artifacts (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    activity TEXT NOT NULL,
    filename TEXT NOT NULL,
    created_at TEXT,
    modified_at TEXT NOT NULL,
    size_bytes INTEGER NOT NULL
);

-- Issues
CREATE TABLE issues (
    id INTEGER PRIMARY KEY,
    number TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'open' or 'closed'
    created TEXT,
    updated TEXT,
    labels TEXT,  -- JSON array
    path TEXT NOT NULL UNIQUE
);
```

## Example Queries

```bash
# Open the database
sqlite3 idle-citizen.db

# Sessions per day with total time
SELECT date(started_at), COUNT(*) as sessions,
       SUM(duration_seconds)/60 as minutes
FROM sessions
GROUP BY date(started_at)
ORDER BY date(started_at) DESC
LIMIT 10;

# Most active days by commits
SELECT date(date), COUNT(*) as commits, SUM(insertions) as lines_added
FROM commits
GROUP BY date(date)
ORDER BY commits DESC
LIMIT 5;

# Artifacts by activity
SELECT activity, COUNT(*), SUM(size_bytes)/1024 as kb
FROM artifacts
GROUP BY activity;

# Recent artifacts
SELECT activity, filename, date(modified_at)
FROM artifacts
ORDER BY modified_at DESC
LIMIT 10;

# Open issues with labels
SELECT number, title, labels
FROM issues
WHERE status = 'open';
```

## Integration with Datasette

If you have [Datasette](https://datasette.io/) installed, you can browse interactively:

```bash
pip install datasette
datasette idle-citizen.db
```

Then open http://localhost:8001 in your browser.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | idle-citizen.db | Output database file |
| `--days` | 90 | Days of git history to import |
| `--stats` | off | Show statistics after building |
| `--quiet` | off | Suppress progress messages |

## Why SQLite?

SQLite is the "lingua franca" of personal data tools—queryable, portable, no server needed. This follows the pattern established by Simon Willison's [Dogsheep](https://dogsheep.github.io/) project: convert personal data to SQLite, query with standard tools.

## Dependencies

- Python 3.6+
- sqlite3 (standard library)
- git (for commit history)

No external packages required.
