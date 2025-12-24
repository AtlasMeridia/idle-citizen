#!/usr/bin/env python3
"""
mdanalyze - Analyze markdown file structure and patterns

A CLI tool that extracts and reports on markdown structure:
- Heading hierarchy
- Link inventory (internal and external)
- Code block statistics
- Word counts by section
- Document outline

Usage:
    mdanalyze FILE [FILE...]           # Analyze markdown file(s)
    mdanalyze -r DIRECTORY             # Recursively analyze directory

    mdanalyze --outline FILE           # Show document outline
    mdanalyze --links FILE             # List all links
    mdanalyze --stats FILE             # Show statistics
    mdanalyze --sections FILE          # Show section word counts
    mdanalyze --code FILE              # List code blocks
    mdanalyze --json FILE              # Full analysis as JSON

Examples:
    mdanalyze README.md --outline
    mdanalyze -r ./docs --links --external-only
    mdanalyze notes/*.md --stats
    cat doc.md | mdanalyze --links
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Heading:
    level: int
    text: str
    line: int


@dataclass
class Link:
    text: str
    url: str
    line: int
    is_image: bool = False

    @property
    def is_external(self) -> bool:
        return self.url.startswith(('http://', 'https://', '//'))

    @property
    def is_internal(self) -> bool:
        return not self.is_external and not self.url.startswith('#')

    @property
    def is_anchor(self) -> bool:
        return self.url.startswith('#')


@dataclass
class CodeBlock:
    language: str
    content: str
    line_start: int
    line_end: int

    @property
    def line_count(self) -> int:
        return self.line_end - self.line_start + 1


@dataclass
class Section:
    heading: Heading
    content: str
    word_count: int
    links: list = field(default_factory=list)
    code_blocks: list = field(default_factory=list)


@dataclass
class Analysis:
    file_path: str
    total_lines: int
    total_words: int
    headings: list = field(default_factory=list)
    links: list = field(default_factory=list)
    code_blocks: list = field(default_factory=list)
    sections: list = field(default_factory=list)


def count_words(text: str) -> int:
    """Count words in text, excluding code blocks and link URLs."""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    # Remove link URLs but keep link text
    text = re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Count words
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def parse_headings(content: str) -> list[Heading]:
    """Extract all headings from markdown content."""
    headings = []
    for i, line in enumerate(content.split('\n'), 1):
        # ATX-style headings: # Heading
        match = re.match(r'^(#{1,6})\s+(.+?)(?:\s*#*\s*)?$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append(Heading(level=level, text=text, line=i))
    return headings


def parse_links(content: str) -> list[Link]:
    """Extract all links from markdown content."""
    links = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Images: ![alt](url)
        for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', line):
            links.append(Link(
                text=match.group(1),
                url=match.group(2),
                line=i,
                is_image=True
            ))

        # Regular links: [text](url)
        for match in re.finditer(r'(?<!!)\[([^\]]*)\]\(([^)]+)\)', line):
            links.append(Link(
                text=match.group(1),
                url=match.group(2),
                line=i,
                is_image=False
            ))

        # Reference links: [text][ref] and [ref]: url
        # (simplified - just catch the definitions)
        for match in re.finditer(r'^\[([^\]]+)\]:\s*(\S+)', line):
            links.append(Link(
                text=f"[{match.group(1)}]",
                url=match.group(2),
                line=i,
                is_image=False
            ))

    return links


def parse_code_blocks(content: str) -> list[CodeBlock]:
    """Extract fenced code blocks from markdown."""
    blocks = []
    lines = content.split('\n')
    in_block = False
    block_start = 0
    block_lang = ''
    block_lines = []

    for i, line in enumerate(lines, 1):
        if not in_block and re.match(r'^```(\w*)', line):
            in_block = True
            block_start = i
            block_lang = re.match(r'^```(\w*)', line).group(1) or 'text'
            block_lines = []
        elif in_block and line.startswith('```'):
            blocks.append(CodeBlock(
                language=block_lang,
                content='\n'.join(block_lines),
                line_start=block_start,
                line_end=i
            ))
            in_block = False
        elif in_block:
            block_lines.append(line)

    return blocks


def parse_sections(content: str, headings: list[Heading]) -> list[Section]:
    """Break content into sections based on headings."""
    if not headings:
        # No headings = one big section
        return [Section(
            heading=Heading(level=0, text="(document)", line=0),
            content=content,
            word_count=count_words(content),
            links=parse_links(content),
            code_blocks=parse_code_blocks(content)
        )]

    lines = content.split('\n')
    sections = []

    for i, heading in enumerate(headings):
        start_line = heading.line
        end_line = headings[i + 1].line - 1 if i + 1 < len(headings) else len(lines)

        section_content = '\n'.join(lines[start_line - 1:end_line])
        sections.append(Section(
            heading=heading,
            content=section_content,
            word_count=count_words(section_content),
            links=parse_links(section_content),
            code_blocks=parse_code_blocks(section_content)
        ))

    # Include content before first heading
    if headings[0].line > 1:
        preamble = '\n'.join(lines[:headings[0].line - 1])
        if preamble.strip():
            sections.insert(0, Section(
                heading=Heading(level=0, text="(preamble)", line=0),
                content=preamble,
                word_count=count_words(preamble),
                links=parse_links(preamble),
                code_blocks=parse_code_blocks(preamble)
            ))

    return sections


def analyze_file(content: str, file_path: str = "<stdin>") -> Analysis:
    """Perform complete analysis of markdown content."""
    lines = content.split('\n')
    headings = parse_headings(content)
    links = parse_links(content)
    code_blocks = parse_code_blocks(content)
    sections = parse_sections(content, headings)

    return Analysis(
        file_path=file_path,
        total_lines=len(lines),
        total_words=count_words(content),
        headings=headings,
        links=links,
        code_blocks=code_blocks,
        sections=sections
    )


def format_outline(analysis: Analysis, indent_char: str = "  ") -> str:
    """Format document outline from headings."""
    lines = []
    for h in analysis.headings:
        indent = indent_char * (h.level - 1)
        lines.append(f"{indent}{h.text}")
    return '\n'.join(lines) if lines else "(no headings found)"


def format_links(analysis: Analysis, external_only: bool = False,
                 internal_only: bool = False, images_only: bool = False) -> str:
    """Format link listing."""
    links = analysis.links

    if external_only:
        links = [l for l in links if l.is_external]
    if internal_only:
        links = [l for l in links if l.is_internal]
    if images_only:
        links = [l for l in links if l.is_image]

    if not links:
        return "(no matching links found)"

    lines = []
    for link in links:
        prefix = "IMG " if link.is_image else ""
        lines.append(f"{link.line:4d}: {prefix}[{link.text}] -> {link.url}")
    return '\n'.join(lines)


def format_stats(analysis: Analysis) -> str:
    """Format statistics summary."""
    lang_counts = {}
    for cb in analysis.code_blocks:
        lang_counts[cb.language] = lang_counts.get(cb.language, 0) + 1

    ext_links = sum(1 for l in analysis.links if l.is_external)
    int_links = sum(1 for l in analysis.links if l.is_internal)
    anchor_links = sum(1 for l in analysis.links if l.is_anchor)
    images = sum(1 for l in analysis.links if l.is_image)

    lines = [
        f"File: {analysis.file_path}",
        f"Lines: {analysis.total_lines}",
        f"Words: {analysis.total_words}",
        f"Headings: {len(analysis.headings)}",
        f"Links: {len(analysis.links)} total ({ext_links} external, {int_links} internal, {anchor_links} anchors)",
        f"Images: {images}",
        f"Code blocks: {len(analysis.code_blocks)}",
    ]

    if lang_counts:
        langs = ", ".join(f"{lang}:{count}" for lang, count in sorted(lang_counts.items()))
        lines.append(f"  Languages: {langs}")

    return '\n'.join(lines)


def format_sections(analysis: Analysis) -> str:
    """Format section word counts."""
    if not analysis.sections:
        return "(no sections found)"

    lines = []
    max_words = max(s.word_count for s in analysis.sections) if analysis.sections else 0
    bar_width = 30

    for section in analysis.sections:
        h = section.heading
        indent = "  " * (h.level - 1) if h.level > 0 else ""
        bar_len = int((section.word_count / max_words) * bar_width) if max_words > 0 else 0
        bar = "█" * bar_len
        lines.append(f"{indent}{h.text}")
        lines.append(f"{indent}  {section.word_count:5d} words {bar}")

    return '\n'.join(lines)


def format_code_blocks(analysis: Analysis) -> str:
    """Format code block listing."""
    if not analysis.code_blocks:
        return "(no code blocks found)"

    lines = []
    for cb in analysis.code_blocks:
        preview = cb.content[:50].replace('\n', '\\n')
        if len(cb.content) > 50:
            preview += "..."
        lines.append(f"{cb.line_start:4d}-{cb.line_end:4d}: [{cb.language}] ({cb.line_count} lines) {preview}")

    return '\n'.join(lines)


def analysis_to_dict(analysis: Analysis) -> dict:
    """Convert analysis to JSON-serializable dict."""
    return {
        'file_path': analysis.file_path,
        'total_lines': analysis.total_lines,
        'total_words': analysis.total_words,
        'headings': [
            {'level': h.level, 'text': h.text, 'line': h.line}
            for h in analysis.headings
        ],
        'links': [
            {'text': l.text, 'url': l.url, 'line': l.line,
             'is_image': l.is_image, 'is_external': l.is_external}
            for l in analysis.links
        ],
        'code_blocks': [
            {'language': cb.language, 'line_start': cb.line_start,
             'line_end': cb.line_end, 'line_count': cb.line_count}
            for cb in analysis.code_blocks
        ],
        'sections': [
            {'heading': {'level': s.heading.level, 'text': s.heading.text, 'line': s.heading.line},
             'word_count': s.word_count,
             'link_count': len(s.links),
             'code_block_count': len(s.code_blocks)}
            for s in analysis.sections
        ]
    }


def collect_files(paths: list[str], recursive: bool = False) -> list[str]:
    """Collect markdown files from paths."""
    files = []

    for path in paths:
        p = Path(path)
        if p.is_file() and p.suffix.lower() in ('.md', '.markdown'):
            files.append(str(p))
        elif p.is_dir():
            if recursive:
                for md_file in p.rglob('*.md'):
                    files.append(str(md_file))
                for md_file in p.rglob('*.markdown'):
                    files.append(str(md_file))
            else:
                for md_file in p.glob('*.md'):
                    files.append(str(md_file))
                for md_file in p.glob('*.markdown'):
                    files.append(str(md_file))

    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(
        description="Analyze markdown file structure and patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mdanalyze README.md --outline        Show document outline
  mdanalyze -r docs/ --links           List links in all docs
  mdanalyze file.md --stats            Show file statistics
  cat notes.md | mdanalyze --sections  Analyze section word counts
        """
    )

    parser.add_argument('files', nargs='*', help='Markdown files or directories to analyze')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Recursively process directories')

    # Output modes (mutually exclusive for single-file, but can combine for multi-file)
    parser.add_argument('--outline', action='store_true',
                        help='Show document outline from headings')
    parser.add_argument('--links', action='store_true',
                        help='List all links')
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics summary')
    parser.add_argument('--sections', action='store_true',
                        help='Show section word counts')
    parser.add_argument('--code', action='store_true',
                        help='List code blocks')
    parser.add_argument('--json', action='store_true',
                        help='Output full analysis as JSON')

    # Link filters
    parser.add_argument('--external-only', action='store_true',
                        help='With --links, show only external links')
    parser.add_argument('--internal-only', action='store_true',
                        help='With --links, show only internal links')
    parser.add_argument('--images-only', action='store_true',
                        help='With --links, show only images')

    args = parser.parse_args()

    # Determine input source
    if args.files:
        files = collect_files(args.files, args.recursive)
        if not files:
            print("No markdown files found", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        files = None

    # Collect analyses
    analyses = []

    if files:
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                analyses.append(analyze_file(content, file_path))
            except Exception as e:
                print(f"Error reading {file_path}: {e}", file=sys.stderr)
    else:
        # Read from stdin
        content = sys.stdin.read()
        analyses.append(analyze_file(content))

    if not analyses:
        sys.exit(1)

    # Default to stats if no output mode specified
    if not any([args.outline, args.links, args.stats, args.sections, args.code, args.json]):
        args.stats = True

    # JSON output
    if args.json:
        if len(analyses) == 1:
            print(json.dumps(analysis_to_dict(analyses[0]), indent=2))
        else:
            print(json.dumps([analysis_to_dict(a) for a in analyses], indent=2))
        return

    # Text output
    for i, analysis in enumerate(analyses):
        if len(analyses) > 1:
            if i > 0:
                print()
            print(f"=== {analysis.file_path} ===")

        outputs = []

        if args.outline:
            outputs.append(format_outline(analysis))

        if args.links:
            outputs.append(format_links(analysis,
                                        external_only=args.external_only,
                                        internal_only=args.internal_only,
                                        images_only=args.images_only))

        if args.stats:
            outputs.append(format_stats(analysis))

        if args.sections:
            outputs.append(format_sections(analysis))

        if args.code:
            outputs.append(format_code_blocks(analysis))

        print('\n\n'.join(outputs))


if __name__ == '__main__':
    main()
