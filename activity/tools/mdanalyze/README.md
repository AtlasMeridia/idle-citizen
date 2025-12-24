# mdanalyze

Analyze markdown file structure and patterns.

## Usage

```bash
# Analyze a single file (shows stats by default)
python3 mdanalyze.py README.md

# Analyze multiple files
python3 mdanalyze.py *.md

# Recursively analyze a directory
python3 mdanalyze.py -r docs/
```

## Output Modes

### Outline

Show document structure from headings:

```bash
$ python3 mdanalyze.py file.md --outline
Introduction
  Getting Started
  Installation
Usage
  Basic Commands
  Advanced Options
```

### Links

List all links with line numbers:

```bash
$ python3 mdanalyze.py file.md --links
  12: [Claude Code] -> https://claude.ai/
  45: IMG [screenshot] -> ./images/screen.png
  67: [see below] -> #installation
```

Filter options:
- `--external-only` — Only http(s) links
- `--internal-only` — Only relative file links
- `--images-only` — Only images

### Statistics

Show file metrics:

```bash
$ python3 mdanalyze.py file.md --stats
File: file.md
Lines: 245
Words: 1847
Headings: 12
Links: 8 total (5 external, 2 internal, 1 anchors)
Images: 2
Code blocks: 4
  Languages: python:2, bash:1, json:1
```

### Sections

Show word counts by section with visual bars:

```bash
$ python3 mdanalyze.py file.md --sections
Introduction
     45 words ██
Getting Started
    312 words ████████████████
Installation
    128 words ███████
```

### Code Blocks

List all fenced code blocks:

```bash
$ python3 mdanalyze.py file.md --code
  15-  22: [python] (8 lines) def hello():\n    print("Hello")...
  45-  52: [bash] (8 lines) npm install\nnpm run build...
```

### JSON

Full analysis as JSON (useful for scripting):

```bash
$ python3 mdanalyze.py file.md --json | jq '.total_words'
1847
```

## Combining Modes

Multiple modes can be combined:

```bash
$ python3 mdanalyze.py file.md --stats --outline
```

## Stdin Support

Read from stdin:

```bash
$ cat doc.md | python3 mdanalyze.py --links
```

## Use Cases

- **Document auditing** — Check word counts, find broken links
- **Content inventory** — Scan entire docs folders for structure
- **Writing analysis** — See how content is distributed across sections
- **Link checking** — Extract all external links for validation
- **Code inventory** — Find all code examples in documentation
