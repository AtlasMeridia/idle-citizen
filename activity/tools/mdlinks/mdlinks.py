#!/usr/bin/env python3
"""
mdlinks - Cross-document markdown link helper

Build an index of headings across markdown files and:
- Search for headings to get correct link syntax
- List all linkable targets in a file or directory
- Validate existing links to check for broken references

Usage:
    mdlinks index [path]           Build/show heading index for path
    mdlinks search <query> [path]  Search headings matching query
    mdlinks check <file>           Validate links in a markdown file
    mdlinks suggest <text> [path]  Suggest link targets for text

Examples:
    mdlinks index .
    mdlinks search "memory" activity/project-notes/
    mdlinks check README.md
    mdlinks suggest "DAEMON personality"
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple, Optional, List, Tuple


class HeadingTarget(NamedTuple):
    """A linkable heading target."""
    file: str
    heading: str
    level: int
    anchor: str
    line_num: int


def slugify(text: str) -> str:
    """Convert heading text to GitHub-style anchor slug."""
    # Lowercase
    slug = text.lower()
    # Remove special characters except spaces, hyphens, underscores
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def extract_headings(file_path: Path) -> List[HeadingTarget]:
    """Extract all headings from a markdown file."""
    headings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Match ATX-style headings: # Heading
                match = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
                if match:
                    level = len(match.group(1))
                    heading = match.group(2)
                    # Remove trailing # characters (some styles use them)
                    heading = re.sub(r'\s*#+\s*$', '', heading)
                    anchor = slugify(heading)

                    headings.append(HeadingTarget(
                        file=str(file_path),
                        heading=heading,
                        level=level,
                        anchor=anchor,
                        line_num=line_num
                    ))
    except (IOError, UnicodeDecodeError):
        pass  # Skip unreadable files

    return headings


def find_markdown_files(path: Path, recursive: bool = True) -> List[Path]:
    """Find all markdown files in a directory."""
    if path.is_file():
        if path.suffix.lower() in ('.md', '.markdown'):
            return [path]
        return []

    if recursive:
        return list(path.rglob('*.md')) + list(path.rglob('*.markdown'))
    else:
        return list(path.glob('*.md')) + list(path.glob('*.markdown'))


def build_index(path: Path, recursive: bool = True) -> List[HeadingTarget]:
    """Build a heading index for all markdown files in path."""
    index = []
    files = find_markdown_files(path, recursive)
    for file_path in files:
        index.extend(extract_headings(file_path))
    return index


def search_headings(query: str, index: List[HeadingTarget]) -> List[HeadingTarget]:
    """Search for headings matching a query (case-insensitive)."""
    query_lower = query.lower()
    words = query_lower.split()

    results = []
    for target in index:
        heading_lower = target.heading.lower()
        # Match if all query words appear in heading
        if all(word in heading_lower for word in words):
            results.append(target)

    return results


def format_link(target: HeadingTarget, relative_to: Optional[Path] = None) -> str:
    """Format a target as a markdown link."""
    file_path = target.file
    if relative_to:
        try:
            file_path = os.path.relpath(target.file, relative_to)
        except ValueError:
            pass  # Different drives on Windows

    return f"[{target.heading}]({file_path}#{target.anchor})"


def extract_links(file_path: Path) -> List[Tuple[int, str, str]]:
    """Extract all markdown links from a file.

    Returns list of (line_num, text, target) tuples.
    """
    links = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Match [text](target) links
                for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                    links.append((line_num, match.group(1), match.group(2)))
    except (IOError, UnicodeDecodeError):
        pass

    return links


def validate_link(link_target: str, source_file: Path, index: List[HeadingTarget]) -> Tuple[bool, str]:
    """Validate a link target.

    Returns (is_valid, reason).
    """
    # Parse the link
    if link_target.startswith(('http://', 'https://', 'mailto:')):
        return True, "external link (not checked)"

    # Split into file and anchor parts
    if '#' in link_target:
        file_part, anchor_part = link_target.split('#', 1)
    else:
        file_part = link_target
        anchor_part = None

    # Resolve relative path
    if file_part:
        target_path = (source_file.parent / file_part).resolve()
    else:
        target_path = source_file.resolve()

    # Check if file exists
    if not target_path.exists():
        return False, f"file not found: {target_path}"

    # If there's an anchor, validate it
    if anchor_part:
        # Find all headings in target file
        file_headings = [t for t in index if Path(t.file).resolve() == target_path]
        if not file_headings:
            # File might not be in index, extract directly
            file_headings = extract_headings(target_path)

        # Check if anchor exists
        anchor_exists = any(h.anchor == anchor_part for h in file_headings)
        if not anchor_exists:
            available = [h.anchor for h in file_headings[:5]]
            available_str = ", ".join(available) if available else "none found"
            return False, f"anchor #{anchor_part} not found (available: {available_str})"

    return True, "valid"


def cmd_index(args):
    """Show heading index for a path."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    index = build_index(path, recursive=not args.no_recursive)

    if args.json:
        output = [
            {
                "file": t.file,
                "heading": t.heading,
                "level": t.level,
                "anchor": t.anchor,
                "line": t.line_num,
                "link": format_link(t, path)
            }
            for t in index
        ]
        print(json.dumps(output, indent=2))
    else:
        current_file = None
        for target in sorted(index, key=lambda t: (t.file, t.line_num)):
            if target.file != current_file:
                current_file = target.file
                rel_path = os.path.relpath(target.file, path)
                print(f"\n{rel_path}")
                print("-" * len(rel_path))

            indent = "  " * (target.level - 1)
            print(f"{indent}L{target.line_num}: {target.heading} → #{target.anchor}")

    if not args.json:
        print(f"\nTotal: {len(index)} headings in {len(set(t.file for t in index))} files")

    return 0


def cmd_search(args):
    """Search for headings matching query."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    index = build_index(path, recursive=not args.no_recursive)
    results = search_headings(args.query, index)

    if args.json:
        output = [
            {
                "file": t.file,
                "heading": t.heading,
                "level": t.level,
                "anchor": t.anchor,
                "line": t.line_num,
                "link": format_link(t, path)
            }
            for t in results
        ]
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f"No headings matching '{args.query}'")
            return 0

        for target in results:
            rel_path = os.path.relpath(target.file, path)
            link = format_link(target, path)
            print(f"{rel_path}:{target.line_num}")
            print(f"  {target.heading}")
            print(f"  {link}")
            print()

    return 0


def cmd_check(args):
    """Validate links in a markdown file."""
    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"Error: {file_path} does not exist", file=sys.stderr)
        return 1

    # Build index from the same directory
    base_path = file_path.parent
    if args.index_path:
        base_path = Path(args.index_path).resolve()

    index = build_index(base_path, recursive=True)
    links = extract_links(file_path)

    errors = []
    warnings = []
    valid_count = 0

    for line_num, text, target in links:
        is_valid, reason = validate_link(target, file_path, index)
        if not is_valid:
            errors.append((line_num, text, target, reason))
        elif "external" in reason:
            warnings.append((line_num, text, target, reason))
            valid_count += 1
        else:
            valid_count += 1

    if args.json:
        output = {
            "file": str(file_path),
            "total_links": len(links),
            "valid": valid_count,
            "errors": [
                {"line": l, "text": t, "target": tgt, "reason": r}
                for l, t, tgt, r in errors
            ],
            "warnings": [
                {"line": l, "text": t, "target": tgt, "reason": r}
                for l, t, tgt, r in warnings
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Checking links in {file_path.name}...")
        print()

        if errors:
            print(f"ERRORS ({len(errors)}):")
            for line_num, text, target, reason in errors:
                print(f"  L{line_num}: [{text}]({target})")
                print(f"        → {reason}")
            print()

        if warnings and args.verbose:
            print(f"WARNINGS ({len(warnings)}):")
            for line_num, text, target, reason in warnings:
                print(f"  L{line_num}: [{text}]({target})")
                print(f"        → {reason}")
            print()

        print(f"Summary: {valid_count} valid, {len(errors)} errors, {len(warnings)} external")

    return 1 if errors else 0


def cmd_suggest(args):
    """Suggest link targets for given text."""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    index = build_index(path, recursive=not args.no_recursive)
    results = search_headings(args.text, index)

    if not results:
        # Try individual words
        words = args.text.split()
        for word in words:
            if len(word) >= 3:
                word_results = search_headings(word, index)
                results.extend(word_results)
        results = list(set(results))  # Deduplicate

    if args.json:
        output = [format_link(t, path) for t in results[:args.limit]]
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f"No suggestions for '{args.text}'")
            return 0

        print(f"Suggested links for '{args.text}':")
        print()
        for target in results[:args.limit]:
            rel_path = os.path.relpath(target.file, path)
            print(f"  {format_link(target, path)}")
            print(f"    from {rel_path}:{target.line_num}")
            print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Cross-document markdown link helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # index command
    p_index = subparsers.add_parser('index', help='Build/show heading index')
    p_index.add_argument('path', nargs='?', default='.', help='Path to index (default: .)')
    p_index.add_argument('--no-recursive', action='store_true', help='Do not recurse into subdirectories')
    p_index.add_argument('--json', action='store_true', help='Output as JSON')
    p_index.set_defaults(func=cmd_index)

    # search command
    p_search = subparsers.add_parser('search', help='Search for headings')
    p_search.add_argument('query', help='Search query')
    p_search.add_argument('path', nargs='?', default='.', help='Path to search (default: .)')
    p_search.add_argument('--no-recursive', action='store_true', help='Do not recurse')
    p_search.add_argument('--json', action='store_true', help='Output as JSON')
    p_search.set_defaults(func=cmd_search)

    # check command
    p_check = subparsers.add_parser('check', help='Validate links in a file')
    p_check.add_argument('file', help='Markdown file to check')
    p_check.add_argument('--index-path', help='Path to build index from (default: file directory)')
    p_check.add_argument('--verbose', '-v', action='store_true', help='Show warnings too')
    p_check.add_argument('--json', action='store_true', help='Output as JSON')
    p_check.set_defaults(func=cmd_check)

    # suggest command
    p_suggest = subparsers.add_parser('suggest', help='Suggest link targets for text')
    p_suggest.add_argument('text', help='Text to find links for')
    p_suggest.add_argument('path', nargs='?', default='.', help='Path to search (default: .)')
    p_suggest.add_argument('--no-recursive', action='store_true', help='Do not recurse')
    p_suggest.add_argument('--limit', '-n', type=int, default=10, help='Max suggestions (default: 10)')
    p_suggest.add_argument('--json', action='store_true', help='Output as JSON')
    p_suggest.set_defaults(func=cmd_suggest)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
