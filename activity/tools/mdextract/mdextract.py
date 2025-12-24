#!/usr/bin/env python3
"""
mdextract - Extract code snippets from markdown files

A CLI tool that finds fenced code blocks in markdown files and extracts them
to individual files, organized by language.

Usage:
    mdextract file.md                    # Extract to ./snippets/
    mdextract file.md -o ./output        # Extract to custom directory
    mdextract file.md --lang python      # Only extract Python blocks
    mdextract file.md --list             # List blocks without extracting
    mdextract *.md --combine             # Combine all blocks by language

Features:
    - Extracts fenced code blocks (```language ... ```)
    - Preserves language hints for proper file extensions
    - Handles multiple blocks of the same language
    - Can filter by specific language
    - Can combine all blocks of same language into one file
    - Generates meaningful filenames from context
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class CodeBlock:
    """Represents a fenced code block extracted from markdown."""
    language: str
    code: str
    line_number: int
    context: str  # Nearby heading or text for naming
    source_file: str


# Map language identifiers to file extensions
LANG_EXTENSIONS = {
    'python': '.py',
    'py': '.py',
    'javascript': '.js',
    'js': '.js',
    'typescript': '.ts',
    'ts': '.ts',
    'tsx': '.tsx',
    'jsx': '.jsx',
    'rust': '.rs',
    'go': '.go',
    'ruby': '.rb',
    'bash': '.sh',
    'sh': '.sh',
    'shell': '.sh',
    'zsh': '.sh',
    'sql': '.sql',
    'json': '.json',
    'yaml': '.yaml',
    'yml': '.yaml',
    'toml': '.toml',
    'html': '.html',
    'css': '.css',
    'scss': '.scss',
    'c': '.c',
    'cpp': '.cpp',
    'c++': '.cpp',
    'java': '.java',
    'kotlin': '.kt',
    'swift': '.swift',
    'php': '.php',
    'lua': '.lua',
    'perl': '.pl',
    'r': '.r',
    'dockerfile': '.dockerfile',
    'make': '.makefile',
    'makefile': '.makefile',
    'nginx': '.conf',
    'apache': '.conf',
    'graphql': '.graphql',
    'markdown': '.md',
    'md': '.md',
    'text': '.txt',
    'txt': '.txt',
    'xml': '.xml',
}


def get_extension(language: str) -> str:
    """Get file extension for a language identifier."""
    lang_lower = language.lower().strip()
    return LANG_EXTENSIONS.get(lang_lower, f'.{lang_lower}' if lang_lower else '.txt')


def slugify(text: str, max_length: int = 40) -> str:
    """Convert text to a filename-safe slug."""
    # Remove special characters, keep alphanumeric and spaces
    clean = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace whitespace with hyphens
    clean = re.sub(r'[\s_]+', '-', clean)
    # Remove leading/trailing hyphens
    clean = clean.strip('-')
    # Truncate
    if len(clean) > max_length:
        clean = clean[:max_length].rsplit('-', 1)[0]
    return clean or 'snippet'


def find_context(lines: list[str], block_start: int) -> str:
    """Find contextual text near a code block for naming."""
    # Look for the nearest heading above the code block
    for i in range(block_start - 1, max(0, block_start - 20), -1):
        line = lines[i].strip()
        if line.startswith('#'):
            # Extract heading text
            heading = re.sub(r'^#+\s*', '', line)
            return heading

    # Look for preceding paragraph text
    for i in range(block_start - 1, max(0, block_start - 5), -1):
        line = lines[i].strip()
        if line and not line.startswith('```'):
            # Use first few words
            words = line.split()[:5]
            return ' '.join(words)

    return ''


def extract_code_blocks(content: str, source_file: str = 'input.md') -> list[CodeBlock]:
    """Extract all fenced code blocks from markdown content."""
    blocks = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for opening fence
        match = re.match(r'^```(\w*)\s*$', line.strip())
        if match:
            language = match.group(1) or 'text'
            start_line = i + 1
            code_lines = []

            # Find closing fence
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1

            code = '\n'.join(code_lines)
            context = find_context(lines, start_line - 1)

            blocks.append(CodeBlock(
                language=language,
                code=code,
                line_number=start_line,
                context=context,
                source_file=source_file
            ))

        i += 1

    return blocks


def generate_filename(block: CodeBlock, index: int, total_same_lang: int) -> str:
    """Generate a meaningful filename for a code block."""
    ext = get_extension(block.language)

    if block.context:
        base = slugify(block.context)
    else:
        base = f'snippet-{block.line_number}'

    # Add index if there are multiple blocks with same context/language
    if total_same_lang > 1:
        base = f'{base}-{index + 1}'

    return f'{base}{ext}'


def list_blocks(blocks: list[CodeBlock]) -> None:
    """Print a summary of found code blocks."""
    if not blocks:
        print("No code blocks found.")
        return

    print(f"Found {len(blocks)} code block(s):\n")

    for i, block in enumerate(blocks, 1):
        preview = block.code[:60].replace('\n', ' ')
        if len(block.code) > 60:
            preview += '...'

        context_str = f' ({block.context})' if block.context else ''
        print(f"  {i}. [{block.language}] line {block.line_number}{context_str}")
        print(f"     {preview}\n")


def extract_to_files(
    blocks: list[CodeBlock],
    output_dir: Path,
    lang_filter: Optional[str] = None,
    combine: bool = False
) -> list[Path]:
    """Extract code blocks to files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = []

    # Filter by language if specified
    if lang_filter:
        blocks = [b for b in blocks if b.language.lower() == lang_filter.lower()]

    if not blocks:
        return written_files

    if combine:
        # Group by language and combine
        by_lang: dict[str, list[CodeBlock]] = {}
        for block in blocks:
            lang = block.language.lower()
            if lang not in by_lang:
                by_lang[lang] = []
            by_lang[lang].append(block)

        for lang, lang_blocks in by_lang.items():
            ext = get_extension(lang)
            filename = f'combined{ext}'
            filepath = output_dir / filename

            combined_code = []
            for block in lang_blocks:
                header = f"# From: {block.source_file}, line {block.line_number}"
                if block.context:
                    header += f" ({block.context})"
                combined_code.append(header)
                combined_code.append(block.code)
                combined_code.append('')

            filepath.write_text('\n'.join(combined_code))
            written_files.append(filepath)
            print(f"  Created: {filepath} ({len(lang_blocks)} blocks)")
    else:
        # Count blocks per language for numbering
        lang_counts: dict[str, int] = {}
        for block in blocks:
            lang = block.language.lower()
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        lang_indices: dict[str, int] = {}

        for block in blocks:
            lang = block.language.lower()
            idx = lang_indices.get(lang, 0)
            lang_indices[lang] = idx + 1

            filename = generate_filename(block, idx, lang_counts[lang])
            filepath = output_dir / filename

            # Avoid overwriting
            if filepath.exists():
                stem = filepath.stem
                suffix = filepath.suffix
                counter = 1
                while filepath.exists():
                    filepath = output_dir / f'{stem}-{counter}{suffix}'
                    counter += 1

            filepath.write_text(block.code)
            written_files.append(filepath)
            print(f"  Created: {filepath}")

    return written_files


def main():
    parser = argparse.ArgumentParser(
        description='Extract code snippets from markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    mdextract notes.md                    Extract to ./snippets/
    mdextract notes.md -o ./code          Extract to ./code/
    mdextract notes.md --lang python      Only Python blocks
    mdextract notes.md --list             List without extracting
    mdextract *.md --combine              Combine by language
        """
    )

    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Markdown file(s) to process'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('./snippets'),
        help='Output directory (default: ./snippets)'
    )

    parser.add_argument(
        '-l', '--lang', '--language',
        type=str,
        default=None,
        help='Only extract blocks of this language'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List code blocks without extracting'
    )

    parser.add_argument(
        '--combine',
        action='store_true',
        help='Combine all blocks of same language into one file'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output except errors'
    )

    args = parser.parse_args()

    # Collect all blocks from all files
    all_blocks = []

    for filepath in args.files:
        if not filepath.exists():
            print(f"Warning: File not found: {filepath}", file=sys.stderr)
            continue

        if not filepath.is_file():
            continue

        content = filepath.read_text()
        blocks = extract_code_blocks(content, str(filepath))
        all_blocks.extend(blocks)

    if not all_blocks:
        if not args.quiet:
            print("No code blocks found in the specified file(s).")
        return 0

    if args.list:
        list_blocks(all_blocks)
        return 0

    # Extract to files
    if not args.quiet:
        print(f"Extracting {len(all_blocks)} code block(s) to {args.output}/\n")

    written = extract_to_files(
        all_blocks,
        args.output,
        lang_filter=args.lang,
        combine=args.combine
    )

    if not args.quiet:
        print(f"\nDone. Created {len(written)} file(s).")

    return 0


if __name__ == '__main__':
    sys.exit(main())
