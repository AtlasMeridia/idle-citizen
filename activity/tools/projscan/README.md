# projscan

Quick project structure analyzer. Scans a directory and generates a structural overview including directory tree, file type distribution, language detection, and key file identification.

## Usage

```bash
# Scan current directory
python3 projscan.py

# Scan specific project
python3 projscan.py ~/Projects/myproject

# Limit depth
python3 projscan.py . --depth 2

# Output as JSON
python3 projscan.py . --json
```

## Features

- **Directory tree** with intelligent truncation
- **File type distribution** by extension
- **Language detection** for common programming languages
- **Key file identification** (README, config files, build files)
- **Size statistics** with human-readable output
- **Ignores** common noise directories (node_modules, .git, __pycache__, etc.)

## Output Example

```
============================================================
PROJECT: headless-atlas
============================================================

STRUCTURE
----------------------------------------
headless-atlas/
├── .env.local
├── CLAUDE.md
├── package.json
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── [slug]/
├── components/
└── lib/

STATISTICS
----------------------------------------
  Files:       83
  Directories: 31
  Total size:  890.2 KB

LANGUAGES
----------------------------------------
  TypeScript (React)          37  ██████████████████████████████
  TypeScript                   9  █████████
  JavaScript                   1  █

KEY FILES
----------------------------------------
  CLAUDE.md
  README.md
  package.json
  tsconfig.json
```

## JSON Output

With `--json`, outputs structured data for scripting:

```json
{
  "root": "/path/to/project",
  "total_files": 83,
  "total_dirs": 31,
  "total_size_human": "890.2 KB",
  "languages": [["TypeScript (React)", 37], ["TypeScript", 9]],
  "key_files": ["CLAUDE.md", "package.json"]
}
```

## Options

| Option | Description |
|--------|-------------|
| `path` | Project directory (default: current) |
| `--depth, -d` | Maximum directory depth (default: 5) |
| `--json, -j` | Output as JSON |

## Ignored Directories

- `.git`, `node_modules`, `__pycache__`, `.next`
- `venv`, `.venv`, `env`, `dist`, `build`
- `.cache`, `.turbo`, `coverage`, `target`
- And other common noise directories

## Detected Languages

Python, JavaScript, TypeScript, Rust, Go, Ruby, Java, Kotlin, Swift, C/C++, C#, PHP, Elixir, Erlang, Clojure, Scala, Lua, Shell, SQL, R, Julia, Zig, Nim, OCaml, Haskell, Elm, Vue, Svelte, Astro

## Key Files Detected

- Documentation: README.md, CLAUDE.md, CHANGELOG.md
- Package managers: package.json, Cargo.toml, go.mod, requirements.txt, pyproject.toml
- Build configs: Makefile, CMakeLists.txt, tsconfig.json
- Container: Dockerfile, docker-compose.yml
- Environment: .env, .env.example
