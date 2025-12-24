# mdextract

A CLI tool that extracts fenced code blocks from markdown files into individual files.

## Installation

No installation required. Just run with Python 3:

```bash
python3 mdextract.py <file.md>
```

Or make it executable:

```bash
chmod +x mdextract.py
./mdextract.py <file.md>
```

## Usage

### Basic extraction

Extract all code blocks to `./snippets/`:

```bash
python3 mdextract.py notes.md
```

### Custom output directory

```bash
python3 mdextract.py notes.md -o ./extracted-code
```

### List blocks without extracting

See what's in the file first:

```bash
python3 mdextract.py notes.md --list
```

### Filter by language

Only extract Python blocks:

```bash
python3 mdextract.py notes.md --lang python
```

### Combine by language

Merge all blocks of the same language into single files:

```bash
python3 mdextract.py notes.md --combine
```

### Multiple files

Process several markdown files at once:

```bash
python3 mdextract.py *.md -o ./all-snippets
```

## Output

Files are named based on the nearest heading above the code block. For example:

```markdown
## Authentication

```python
def login(user, password):
    ...
```

Produces: `authentication.py`

When there are multiple blocks under the same heading, they're numbered: `authentication-1.py`, `authentication-2.py`.

## Supported Languages

Common languages map to their standard extensions:

- `python`, `py` → `.py`
- `javascript`, `js` → `.js`
- `typescript`, `ts` → `.ts`
- `bash`, `sh`, `shell` → `.sh`
- `rust` → `.rs`
- `go` → `.go`
- And many more...

Unknown languages use the language hint as the extension (e.g., `myformat` → `.myformat`).
Blocks without a language hint get `.txt`.

## Examples

Given this markdown:

```markdown
# Setup Guide

## Install dependencies

```bash
npm install
```

## Config file

```json
{"port": 3000}
```
```

Running `mdextract setup.md` produces:

```
snippets/
├── install-dependencies.sh
└── config-file.json
```
