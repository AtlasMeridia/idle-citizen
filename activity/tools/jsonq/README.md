# jsonq

Query JSON files with simple path syntax.

A lightweight alternative to `jq` for common JSON inspection tasks. Uses familiar dot notation and array indexing.

## Installation

```bash
# Copy to a directory in PATH
cp jsonq.py ~/.local/bin/jsonq
chmod +x ~/.local/bin/jsonq
```

## Usage

```bash
# Get a nested property
jsonq file.json user.name

# Get first array element
jsonq file.json items[0]

# Get last element's id
jsonq file.json items[-1].id

# Get name from all items (wildcard)
jsonq file.json 'items[*].name'

# List all available paths
jsonq file.json --keys

# Show structure overview
jsonq file.json --summary

# Read from stdin
cat file.json | jsonq - user.name

# Output compact JSON
jsonq file.json . --compact

# Output raw strings without quotes
jsonq file.json user.name --raw

# Show type of result
jsonq file.json items --type

# Show length of array/object/string
jsonq file.json items --length
```

## Path Syntax

| Syntax | Meaning |
|--------|---------|
| `user.name` | Access object property |
| `items[0]` | Access array element by index |
| `items[-1]` | Access from end (last element) |
| `items[*].id` | Map over all elements |
| `[key with spaces]` | Access property with special characters |

## Options

| Flag | Description |
|------|-------------|
| `-k, --keys` | List all available paths in the JSON |
| `-s, --summary` | Show structural overview |
| `-c, --compact` | Output compact JSON (no whitespace) |
| `-r, --raw` | Output raw strings without quotes |
| `-t, --type` | Show type instead of value |
| `-l, --length` | Show length of arrays/objects/strings |

## Examples

### Exploring unknown JSON

```bash
# Get structure overview
$ jsonq response.json --summary
{
  data: {
    users: [3 items] first: {...}
  }
  meta: {
    page: 1
    total: 42
  }
}

# List available paths
$ jsonq response.json --keys
data
data.users
data.users[0]
data.users[*]
data.users[0].id
data.users[0].name
meta
meta.page
meta.total
```

### Extracting data

```bash
# Get all user names as JSON array
$ jsonq response.json 'data.users[*].name'
["Alice", "Bob", "Charlie"]

# Get raw string (useful in scripts)
$ jsonq config.json database.host --raw
localhost

# Check array length
$ jsonq response.json data.users --length
3
```

### Working with Claude Code history

```bash
# Explore a session file
$ head -2 ~/.claude/projects/myproject/session.jsonl | tail -1 | jsonq - --summary

# Extract message content
$ head -2 session.jsonl | tail -1 | jsonq - message.content --raw
```

## When to Use This vs jq

Use `jsonq` when:
- You want familiar dot notation
- You need a quick structural overview
- You're exploring unknown JSON
- You want simple array mapping with `[*]`

Use `jq` when:
- You need complex transformations
- You need filtering/conditionals
- You're doing JSON-to-JSON transformations
- You need full JSON query language power

## Requirements

- Python 3.6+
- No external dependencies
