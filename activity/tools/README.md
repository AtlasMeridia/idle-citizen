# Tools Activity

Build small CLI tools, scripts, and utilities.

## Purpose

Create useful tools that solve real problems. These might be used by Kenny, by Idle Citizen itself, or just be interesting explorations of what's possible.

## Outputs

Each tool gets its own subfolder:
```
tools/
├── toolname/
│   ├── toolname.py (or .sh, .ts, etc.)
│   └── README.md
```

## Existing Tools

- `gitdigest/` — Summarize recent git activity
- `issues` — Local issue tracker CLI (bash script, not a directory)
- `mdextract/` — Extract code blocks from markdown
- `urlx` — Extract/validate URLs from text (Python script)

## How to Execute

1. Decide what to build:
   - Check `inbox/` for requests from Kenny
   - Check open issues for tool ideas
   - Or invent something useful
2. Keep scope small—something completable in one session
3. Write the tool with clear, readable code
4. Create a README.md explaining what it does and how to use it
5. Test that it actually works
6. Commit with a descriptive message

## What Makes a Good Tool

- **Solves a real problem** — Even a small one
- **Works reliably** — No half-finished scripts
- **Self-documenting** — README + clear --help output
- **Composable** — Plays nice with pipes and other tools

## Language Preferences

- Python for most tools (available everywhere)
- Bash for simple automation
- TypeScript if it's web-related

## Success Criteria

- Tool works as documented
- README is complete and accurate
- Code is clean enough to maintain

## Constraints

- No tools that require API keys or paid services
- No tools that send data externally
- Keep dependencies minimal
