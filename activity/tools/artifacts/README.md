# artifacts

Analyze and report on Idle Citizen session artifacts.

## Purpose

Scans the activity folders, extracts metadata from files, and generates reports. Useful for:
- Seeing what's been produced across sessions
- Finding specific artifacts by title or content
- Getting statistics on productivity
- Supporting the artifact feedback/curation workflow

## Usage

```bash
# Get overall statistics
python artifacts.py stats

# List all artifacts (sorted by recent)
python artifacts.py list
python artifacts.py list --limit 20

# Show 10 most recent artifacts
python artifacts.py recent
python artifacts.py recent --count 5

# Show artifacts for a specific activity
python artifacts.py activity writing
python artifacts.py activity sandbox

# Search by title
python artifacts.py search "memory"

# Search title and content
python artifacts.py search "DAEMON" --content
```

## Output Formats

Default output is human-readable text. Add `--json` flag for JSON output:

```bash
python artifacts.py stats --json
python artifacts.py list --json --limit 10
```

## Commands

### `stats`
Overall statistics: total artifacts, word counts, breakdown by activity and file type.

### `list`
All artifacts in a table, sorted by modification time (most recent first).

### `recent`
Detailed view of the N most recently modified artifacts.

### `activity <name>`
All artifacts within a specific activity folder (writing, sandbox, project-notes, tools).

### `search <query>`
Find artifacts matching a search term. By default searches titles only. Use `--content` to also search file contents.

## What It Extracts

From markdown files:
- Title (first H1 heading)
- YAML frontmatter (if present)
- Word count (excluding code blocks)
- File modification time

From all files:
- Path and size
- Modification timestamp

## Examples

```
$ python artifacts.py stats

=== Idle Citizen Artifact Statistics ===

Total artifacts: 47
Total words: 89,234
Total size: 412.3KB
Sessions: 39 (1.2 artifacts/session)

--- By Activity ---
  project-notes: 14 files, 42,103 words
  sandbox: 12 files, 31,456 words
  writing: 15 files, 12,344 words
  tools: 6 files, 3,331 words

--- By Extension ---
  .md: 41
  .py: 6
```

## Dependencies

Python 3.10+ (standard library only)
