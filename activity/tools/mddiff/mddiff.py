#!/usr/bin/env python3
"""
mddiff - Structural markdown comparison tool

Compares two markdown files and shows structural differences:
- Heading changes (added/removed/modified)
- Section content changes (word count deltas)
- Link differences
- Code block changes
- Overall statistics

Unlike line-by-line diff, this focuses on document structure.
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from difflib import SequenceMatcher


@dataclass
class Section:
    """Represents a section of a markdown document."""
    level: int
    title: str
    content: str
    line_start: int
    word_count: int
    code_blocks: list[str]
    links: list[str]

    def __hash__(self):
        return hash((self.level, self.title))


def extract_links(text: str) -> list[str]:
    """Extract markdown links from text."""
    # [text](url) format
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return [url for _, url in re.findall(link_pattern, text)]


def extract_code_blocks(text: str) -> list[str]:
    """Extract fenced code block languages."""
    pattern = r'```(\w*)'
    return [lang if lang else 'plain' for lang in re.findall(pattern, text)]


def count_words(text: str) -> int:
    """Count words in text, excluding code blocks and links."""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Count remaining words
    return len(text.split())


def parse_markdown(content: str) -> list[Section]:
    """Parse markdown into sections based on headings."""
    lines = content.split('\n')
    sections = []
    current_level = 0
    current_title = "(document root)"
    current_content = []
    current_line_start = 0

    for i, line in enumerate(lines):
        # Check for heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if heading_match:
            # Save previous section
            if current_content or sections:  # Always save if we have content or prior sections
                content_text = '\n'.join(current_content)
                sections.append(Section(
                    level=current_level,
                    title=current_title,
                    content=content_text,
                    line_start=current_line_start,
                    word_count=count_words(content_text),
                    code_blocks=extract_code_blocks(content_text),
                    links=extract_links(content_text)
                ))

            # Start new section
            current_level = len(heading_match.group(1))
            current_title = heading_match.group(2).strip()
            current_content = []
            current_line_start = i + 1
        else:
            current_content.append(line)

    # Don't forget the last section
    content_text = '\n'.join(current_content)
    sections.append(Section(
        level=current_level,
        title=current_title,
        content=content_text,
        line_start=current_line_start,
        word_count=count_words(content_text),
        code_blocks=extract_code_blocks(content_text),
        links=extract_links(content_text)
    ))

    return sections


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def compare_sections(old_sections: list[Section], new_sections: list[Section]) -> dict:
    """Compare two lists of sections and return differences."""
    old_by_title = {s.title: s for s in old_sections}
    new_by_title = {s.title: s for s in new_sections}

    old_titles = set(old_by_title.keys())
    new_titles = set(new_by_title.keys())

    added = new_titles - old_titles
    removed = old_titles - new_titles
    common = old_titles & new_titles

    modified = []
    unchanged = []

    for title in common:
        old_s = old_by_title[title]
        new_s = new_by_title[title]

        word_delta = new_s.word_count - old_s.word_count
        content_similarity = similarity(old_s.content, new_s.content)
        level_changed = old_s.level != new_s.level

        if word_delta != 0 or content_similarity < 0.95 or level_changed:
            modified.append({
                'title': title,
                'old': old_s,
                'new': new_s,
                'word_delta': word_delta,
                'similarity': content_similarity,
                'level_changed': level_changed
            })
        else:
            unchanged.append(title)

    return {
        'added': [(t, new_by_title[t]) for t in added],
        'removed': [(t, old_by_title[t]) for t in removed],
        'modified': modified,
        'unchanged': unchanged
    }


def format_delta(n: int) -> str:
    """Format a number as +N or -N."""
    if n > 0:
        return f"+{n}"
    elif n < 0:
        return str(n)
    else:
        return "0"


def print_comparison(old_file: str, new_file: str, diff: dict,
                    old_sections: list[Section], new_sections: list[Section],
                    verbose: bool = False):
    """Print the comparison results."""
    # Header
    print(f"Comparing: {old_file} -> {new_file}")
    print("=" * 60)

    # Overall stats
    old_total_words = sum(s.word_count for s in old_sections)
    new_total_words = sum(s.word_count for s in new_sections)
    old_total_links = sum(len(s.links) for s in old_sections)
    new_total_links = sum(len(s.links) for s in new_sections)
    old_total_code = sum(len(s.code_blocks) for s in old_sections)
    new_total_code = sum(len(s.code_blocks) for s in new_sections)

    print("\nOverall:")
    print(f"  Sections:    {len(old_sections)} -> {len(new_sections)} ({format_delta(len(new_sections) - len(old_sections))})")
    print(f"  Words:       {old_total_words} -> {new_total_words} ({format_delta(new_total_words - old_total_words)})")
    print(f"  Links:       {old_total_links} -> {new_total_links} ({format_delta(new_total_links - old_total_links)})")
    print(f"  Code blocks: {old_total_code} -> {new_total_code} ({format_delta(new_total_code - old_total_code)})")

    # Added sections
    if diff['added']:
        print(f"\nAdded sections ({len(diff['added'])}):")
        for title, section in diff['added']:
            prefix = "#" * section.level + " " if section.level > 0 else ""
            print(f"  + {prefix}{title} ({section.word_count} words)")
            if verbose and section.links:
                for link in section.links[:3]:
                    print(f"      link: {link[:60]}...")

    # Removed sections
    if diff['removed']:
        print(f"\nRemoved sections ({len(diff['removed'])}):")
        for title, section in diff['removed']:
            prefix = "#" * section.level + " " if section.level > 0 else ""
            print(f"  - {prefix}{title} ({section.word_count} words)")

    # Modified sections
    if diff['modified']:
        print(f"\nModified sections ({len(diff['modified'])}):")
        for mod in diff['modified']:
            title = mod['title']
            old_s = mod['old']
            new_s = mod['new']

            prefix = "#" * new_s.level + " " if new_s.level > 0 else ""
            word_delta = format_delta(mod['word_delta'])
            sim_pct = int(mod['similarity'] * 100)

            changes = []
            if mod['word_delta'] != 0:
                changes.append(f"{word_delta} words")
            if mod['similarity'] < 0.95:
                changes.append(f"{sim_pct}% similar")
            if mod['level_changed']:
                changes.append(f"level {old_s.level}->{new_s.level}")

            print(f"  ~ {prefix}{title} ({', '.join(changes)})")

            if verbose:
                # Show link changes
                old_links = set(old_s.links)
                new_links = set(new_s.links)
                for link in new_links - old_links:
                    print(f"      + link: {link[:60]}")
                for link in old_links - new_links:
                    print(f"      - link: {link[:60]}")

    # Summary
    if diff['unchanged']:
        print(f"\nUnchanged: {len(diff['unchanged'])} sections")

    # Score
    total_sections = len(old_sections) + len(diff['added'])
    changed = len(diff['added']) + len(diff['removed']) + len(diff['modified'])
    if total_sections > 0:
        change_pct = (changed / total_sections) * 100
        print(f"\nChange intensity: {change_pct:.1f}% of sections affected")


def output_json(old_file: str, new_file: str, diff: dict,
               old_sections: list[Section], new_sections: list[Section]):
    """Output comparison as JSON."""
    import json

    def section_to_dict(s: Section) -> dict:
        return {
            'level': s.level,
            'title': s.title,
            'word_count': s.word_count,
            'line_start': s.line_start,
            'links': s.links,
            'code_blocks': s.code_blocks
        }

    result = {
        'old_file': old_file,
        'new_file': new_file,
        'stats': {
            'old_sections': len(old_sections),
            'new_sections': len(new_sections),
            'old_words': sum(s.word_count for s in old_sections),
            'new_words': sum(s.word_count for s in new_sections),
            'added': len(diff['added']),
            'removed': len(diff['removed']),
            'modified': len(diff['modified']),
            'unchanged': len(diff['unchanged'])
        },
        'added': [{'title': t, 'section': section_to_dict(s)} for t, s in diff['added']],
        'removed': [{'title': t, 'section': section_to_dict(s)} for t, s in diff['removed']],
        'modified': [
            {
                'title': m['title'],
                'word_delta': m['word_delta'],
                'similarity': m['similarity'],
                'level_changed': m['level_changed'],
                'old': section_to_dict(m['old']),
                'new': section_to_dict(m['new'])
            }
            for m in diff['modified']
        ],
        'unchanged': diff['unchanged']
    }

    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description='Compare markdown files structurally',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mddiff old.md new.md              # Compare two files
  mddiff old.md new.md --json       # Output as JSON
  mddiff old.md new.md -v           # Verbose output with link details
  mddiff draft.md final.md --stats  # Just show statistics

Unlike line-by-line diff, mddiff focuses on document structure:
headings, sections, word counts, links, and code blocks.
        """
    )
    parser.add_argument('old_file', help='Original markdown file')
    parser.add_argument('new_file', help='New markdown file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed changes including links')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--stats', action='store_true',
                       help='Only show statistics, not section details')

    args = parser.parse_args()

    # Read files
    try:
        old_content = Path(args.old_file).read_text()
    except FileNotFoundError:
        print(f"Error: Cannot find {args.old_file}", file=sys.stderr)
        sys.exit(1)

    try:
        new_content = Path(args.new_file).read_text()
    except FileNotFoundError:
        print(f"Error: Cannot find {args.new_file}", file=sys.stderr)
        sys.exit(1)

    # Parse both files
    old_sections = parse_markdown(old_content)
    new_sections = parse_markdown(new_content)

    # Compare
    diff = compare_sections(old_sections, new_sections)

    # Output
    if args.json:
        output_json(args.old_file, args.new_file, diff, old_sections, new_sections)
    elif args.stats:
        # Just stats
        old_words = sum(s.word_count for s in old_sections)
        new_words = sum(s.word_count for s in new_sections)
        print(f"Sections: {len(old_sections)} -> {len(new_sections)}")
        print(f"Words: {old_words} -> {new_words} ({format_delta(new_words - old_words)})")
        print(f"Added: {len(diff['added'])}, Removed: {len(diff['removed'])}, Modified: {len(diff['modified'])}")
    else:
        print_comparison(args.old_file, args.new_file, diff,
                        old_sections, new_sections, args.verbose)


if __name__ == '__main__':
    main()
