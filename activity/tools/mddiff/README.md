# mddiff

Structural markdown comparison tool. Unlike line-by-line diff, focuses on document organization: headings, sections, word counts, links, and code blocks.

## Usage

```bash
# Basic comparison
python3 mddiff.py old.md new.md

# Just statistics
python3 mddiff.py old.md new.md --stats

# Verbose mode (shows link changes)
python3 mddiff.py old.md new.md -v

# JSON output
python3 mddiff.py old.md new.md --json
```

## What It Shows

- **Section changes**: Added, removed, or modified headings
- **Word count deltas**: How much content changed in each section
- **Content similarity**: Percentage similarity for modified sections
- **Heading level changes**: When a section is promoted/demoted
- **Link inventory**: Links added or removed (in verbose mode)
- **Code block counts**: Number of code blocks per section
- **Change intensity**: Overall percentage of sections affected

## Example Output

```
Comparing: draft.md -> final.md
============================================================

Overall:
  Sections:    8 -> 12 (+4)
  Words:       1500 -> 2100 (+600)
  Links:       5 -> 8 (+3)
  Code blocks: 2 -> 3 (+1)

Added sections (4):
  + ## New Feature (+250 words)
  + ### Implementation Details (+150 words)
  ...

Removed sections (1):
  - ## Deprecated Section (-100 words)

Modified sections (2):
  ~ ## Introduction (+50 words, 85% similar)
  ~ ## Conclusion (+25 words, level 2->3)

Unchanged: 4 sections

Change intensity: 58.3% of sections affected
```

## Use Cases

- **Document evolution**: Track how a document changes across versions
- **Review drafts**: See structural changes between drafts
- **Merge preparation**: Understand what changed before merging
- **Content audits**: Compare documents for structural differences
- **Session tracking**: Compare Idle Citizen artifacts across sessions

## Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Show detailed changes including individual links |
| `--json` | Output as JSON for scripting |
| `--stats` | Only show statistics, skip section details |
| `-h, --help` | Show help message |

## How It Works

1. Parses both files into section trees based on headings
2. Matches sections by title (exact match)
3. Computes word counts, link lists, and code block inventories
4. Calculates content similarity using sequence matching
5. Reports structural differences

Sections are matched by their heading text. A section is "modified" if:
- Word count changed
- Content similarity is below 95%
- Heading level changed

## Limitations

- Matches sections by exact title only (no fuzzy matching)
- Doesn't track section moves (shows as add + remove)
- Code blocks counted but content not compared
- Inline formatting changes not detected

## Dependencies

Python 3.9+ (standard library only)
