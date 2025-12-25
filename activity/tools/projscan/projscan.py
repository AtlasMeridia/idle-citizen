#!/usr/bin/env python3
"""
projscan - Quick project structure analyzer

Scans a project directory and generates a structural overview including:
- Directory tree with counts
- File type distribution
- Key files (README, config files, etc.)
- Language detection
- Size statistics

Usage:
    projscan [path] [options]
    projscan ~/Projects/myproject
    projscan . --depth 3
    projscan . --json
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Common ignore patterns
IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.next', '.venv', 'venv',
    'env', '.tox', '.mypy_cache', '.pytest_cache', 'dist', 'build',
    '.cache', '.turbo', 'coverage', '.nyc_output', 'target', '.idea',
    '.vscode', '.DS_Store', 'vendor', 'deps', '_build', '.elixir_ls'
}

IGNORE_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitkeep'
}

# Language detection by extension
LANG_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript (React)',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript (React)',
    '.rs': 'Rust',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.swift': 'Swift',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.php': 'PHP',
    '.ex': 'Elixir',
    '.exs': 'Elixir Script',
    '.erl': 'Erlang',
    '.clj': 'Clojure',
    '.scala': 'Scala',
    '.lua': 'Lua',
    '.vim': 'Vim Script',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.zsh': 'Zsh',
    '.fish': 'Fish',
    '.ps1': 'PowerShell',
    '.sql': 'SQL',
    '.r': 'R',
    '.R': 'R',
    '.jl': 'Julia',
    '.zig': 'Zig',
    '.nim': 'Nim',
    '.ml': 'OCaml',
    '.hs': 'Haskell',
    '.elm': 'Elm',
    '.vue': 'Vue',
    '.svelte': 'Svelte',
    '.astro': 'Astro',
}

# Config/key files to highlight
KEY_FILES = {
    'README.md', 'README', 'readme.md',
    'CLAUDE.md', 'AGENTS.md', 'CURSORRULES', '.cursorrules',
    'package.json', 'Cargo.toml', 'go.mod', 'requirements.txt',
    'pyproject.toml', 'setup.py', 'setup.cfg', 'Pipfile',
    'Gemfile', 'composer.json', 'build.gradle', 'pom.xml',
    'Makefile', 'CMakeLists.txt', 'meson.build',
    'tsconfig.json', 'jsconfig.json', 'next.config.js', 'next.config.mjs',
    'tailwind.config.js', 'tailwind.config.ts', 'postcss.config.js',
    'vite.config.js', 'vite.config.ts', 'webpack.config.js',
    'docker-compose.yml', 'docker-compose.yaml', 'Dockerfile',
    '.env', '.env.example', '.env.local',
    '.gitignore', '.dockerignore', '.npmrc',
    'LICENSE', 'LICENSE.md', 'CHANGELOG.md', 'CONTRIBUTING.md',
}


class ProjectScanner:
    def __init__(self, path: str, max_depth: int = 5):
        self.root = Path(path).resolve()
        self.max_depth = max_depth
        self.files: List[Path] = []
        self.dirs: List[Path] = []
        self.extension_counts: Dict[str, int] = defaultdict(int)
        self.language_counts: Dict[str, int] = defaultdict(int)
        self.total_size: int = 0
        self.key_files_found: List[Path] = []

    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        name = path.name
        if path.is_dir():
            return name in IGNORE_DIRS or name.startswith('.')
        return name in IGNORE_FILES

    def scan(self) -> None:
        """Scan the project directory."""
        self._scan_recursive(self.root, 0)

    def _scan_recursive(self, path: Path, depth: int) -> None:
        """Recursively scan directories."""
        if depth > self.max_depth:
            return

        try:
            items = sorted(path.iterdir())
        except PermissionError:
            return

        for item in items:
            if self.should_ignore(item):
                continue

            if item.is_dir():
                self.dirs.append(item)
                self._scan_recursive(item, depth + 1)
            elif item.is_file():
                self.files.append(item)
                ext = item.suffix.lower()
                self.extension_counts[ext if ext else '(no ext)'] += 1

                if ext in LANG_MAP:
                    self.language_counts[LANG_MAP[ext]] += 1

                if item.name in KEY_FILES:
                    self.key_files_found.append(item)

                try:
                    self.total_size += item.stat().st_size
                except (OSError, PermissionError):
                    pass

    def get_tree(self, max_items: int = 50) -> str:
        """Generate a directory tree representation."""
        lines = [f"{self.root.name}/"]
        self._tree_recursive(self.root, "", lines, 0, max_items)
        if len(lines) > max_items:
            lines.append(f"... and {len(lines) - max_items} more items")
            lines = lines[:max_items + 1]
        return "\n".join(lines)

    def _tree_recursive(self, path: Path, prefix: str, lines: List[str],
                        depth: int, max_items: int) -> None:
        """Recursively build tree lines."""
        if len(lines) >= max_items or depth >= self.max_depth:
            return

        try:
            items = sorted(path.iterdir())
        except PermissionError:
            return

        items = [i for i in items if not self.should_ignore(i)]
        dirs = [i for i in items if i.is_dir()]
        files = [i for i in items if i.is_file()]

        # Show files first, limited
        for i, f in enumerate(files[:10]):
            is_last = (i == len(files) - 1) and not dirs
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{f.name}")

        if len(files) > 10:
            lines.append(f"{prefix}├── ... ({len(files) - 10} more files)")

        # Then directories
        for i, d in enumerate(dirs):
            is_last = i == len(dirs) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{d.name}/")

            new_prefix = prefix + ("    " if is_last else "│   ")
            self._tree_recursive(d, new_prefix, lines, depth + 1, max_items)

    def get_stats(self) -> Dict:
        """Get project statistics."""
        # Top extensions
        top_ext = sorted(self.extension_counts.items(),
                         key=lambda x: x[1], reverse=True)[:10]

        # Top languages
        top_lang = sorted(self.language_counts.items(),
                          key=lambda x: x[1], reverse=True)

        return {
            'root': str(self.root),
            'total_files': len(self.files),
            'total_dirs': len(self.dirs),
            'total_size_bytes': self.total_size,
            'total_size_human': self._human_size(self.total_size),
            'top_extensions': top_ext,
            'languages': top_lang,
            'key_files': [str(f.relative_to(self.root))
                          for f in self.key_files_found],
        }

    def _human_size(self, size: int) -> str:
        """Convert bytes to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def print_report(self) -> None:
        """Print a formatted report."""
        stats = self.get_stats()

        print(f"\n{'=' * 60}")
        print(f"PROJECT: {self.root.name}")
        print(f"{'=' * 60}\n")

        print("STRUCTURE")
        print("-" * 40)
        print(self.get_tree())
        print()

        print("STATISTICS")
        print("-" * 40)
        print(f"  Files:       {stats['total_files']}")
        print(f"  Directories: {stats['total_dirs']}")
        print(f"  Total size:  {stats['total_size_human']}")
        print()

        if stats['languages']:
            print("LANGUAGES")
            print("-" * 40)
            for lang, count in stats['languages']:
                bar = "█" * min(count, 30)
                print(f"  {lang:25} {count:4}  {bar}")
            print()

        if stats['top_extensions']:
            print("FILE TYPES")
            print("-" * 40)
            for ext, count in stats['top_extensions']:
                print(f"  {ext:15} {count:4}")
            print()

        if stats['key_files']:
            print("KEY FILES")
            print("-" * 40)
            for f in stats['key_files'][:20]:
                print(f"  {f}")
            if len(stats['key_files']) > 20:
                print(f"  ... and {len(stats['key_files']) - 20} more")
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Quick project structure analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('path', nargs='?', default='.',
                        help='Path to project directory (default: current)')
    parser.add_argument('--depth', '-d', type=int, default=5,
                        help='Maximum directory depth (default: 5)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output as JSON')

    args = parser.parse_args()

    path = args.path
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    scanner = ProjectScanner(path, max_depth=args.depth)
    scanner.scan()

    if args.json:
        stats = scanner.get_stats()
        print(json.dumps(stats, indent=2))
    else:
        scanner.print_report()


if __name__ == '__main__':
    main()
