# mdlinks

Cross-document markdown link helper. Builds an index of headings across markdown files to help with:
- Finding correct link syntax for cross-referencing
- Validating existing links
- Suggesting link targets for concepts

## Installation

No dependencies beyond Python 3.6+. Just run directly:

```bash
python3 mdlinks.py <command>
```

Or make it executable:

```bash
chmod +x mdlinks.py
./mdlinks.py <command>
```

## Commands

### `index` — Show all linkable headings

```bash
# Index current directory
mdlinks index

# Index a specific path
mdlinks index activity/project-notes/

# Output as JSON
mdlinks index --json
```

Output shows each file's heading hierarchy with line numbers and anchor slugs:

```
daemon-personality-configuration.md
-----------------------------------
L1: DAEMON Personality Configuration System → #daemon-personality-configuration-system
  L7: Purpose → #purpose
  L15: The Problem → #the-problem
    L17: Why Personality is Hard → #why-personality-is-hard
```

### `search` — Find headings matching a query

```bash
# Search for headings containing "memory"
mdlinks search "memory" activity/

# Multi-word searches match all words
mdlinks search "memory system" activity/
```

Output shows matching headings with ready-to-use markdown link syntax:

```
daemon-phase1-implementation.md:56
  1. Memory Architecture
  [1. Memory Architecture](daemon-phase1-implementation.md#1-memory-architecture)
```

### `check` — Validate links in a markdown file

```bash
# Check all internal links in a file
mdlinks check README.md

# Show external links too (with -v)
mdlinks check README.md -v

# Use a different base path for the index
mdlinks check docs/guide.md --index-path docs/
```

Reports broken links:
- File not found
- Anchor not found (with suggestions for available anchors)

External links (http/https/mailto) are counted but not validated.

### `suggest` — Find link targets for text

```bash
# What could "personality configuration" link to?
mdlinks suggest "personality configuration" activity/

# Limit suggestions
mdlinks suggest "memory" activity/ -n 5
```

Useful when writing documentation and you want to add a link but aren't sure exactly what heading to target.

## Use Cases

### Cross-referencing research notes

When you write "see the memory system research" in one doc and want to link it:

```bash
mdlinks suggest "memory system" activity/project-notes/
```

Copy the suggested link syntax directly into your document.

### Checking for broken links after restructuring

After renaming or reorganizing files:

```bash
mdlinks check activity/project-notes/daemon-phase1-implementation.md
```

### Building a quick index of a documentation folder

```bash
mdlinks index docs/ --json > docs-index.json
```

## Anchor Slug Algorithm

Follows GitHub-style anchor generation:
1. Lowercase the heading text
2. Remove special characters (except spaces, hyphens, underscores)
3. Replace spaces with hyphens
4. Strip leading/trailing hyphens

Example: `## 1. Memory Architecture` → `#1-memory-architecture`

## Limitations

- Only handles ATX-style headings (`# Heading`, not underlined)
- Does not validate external HTTP links
- Duplicate heading anchors (GitHub adds `-1`, `-2` suffixes) are not tracked
- Does not parse markdown link references `[text][ref]`
