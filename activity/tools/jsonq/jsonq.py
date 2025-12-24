#!/usr/bin/env python3
"""
jsonq - Query JSON files with simple path syntax.

A lightweight alternative to jq for common JSON inspection tasks.
Uses dot notation and array indexing that feels natural.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Union


def parse_path(path: str) -> List[Union[str, int]]:
    """
    Parse a dotted path into components.

    Examples:
        "user.name" -> ["user", "name"]
        "items[0].id" -> ["items", 0, "id"]
        "data[*].name" -> ["data", "*", "name"]
        "[0]" -> [0]
    """
    components: List[Union[str, int]] = []
    current = ""
    i = 0

    while i < len(path):
        char = path[i]

        if char == ".":
            if current:
                components.append(current)
                current = ""
            i += 1
        elif char == "[":
            if current:
                components.append(current)
                current = ""
            # Find matching bracket
            j = i + 1
            while j < len(path) and path[j] != "]":
                j += 1
            bracket_content = path[i + 1 : j]
            if bracket_content == "*":
                components.append("*")
            elif bracket_content.lstrip("-").isdigit():
                components.append(int(bracket_content))
            else:
                # Treat as string key (for keys with special chars)
                components.append(bracket_content)
            i = j + 1
        else:
            current += char
            i += 1

    if current:
        components.append(current)

    return components


def resolve_path(data: Any, components: List[Union[str, int]]) -> Any:
    """
    Resolve a path through the data structure.

    Handles:
    - Object property access
    - Array indexing (including negative)
    - Wildcard [*] for mapping over arrays
    """
    if not components:
        return data

    head, *tail = components

    if head == "*":
        # Wildcard: map over array elements
        if not isinstance(data, list):
            raise ValueError(f"Wildcard [*] used on non-array: {type(data).__name__}")
        return [resolve_path(item, tail) for item in data]

    if isinstance(head, int):
        # Array index
        if not isinstance(data, list):
            raise ValueError(f"Array index [{head}] used on non-array: {type(data).__name__}")
        if head >= len(data) or head < -len(data):
            raise IndexError(f"Array index {head} out of range (length {len(data)})")
        return resolve_path(data[head], tail)

    if isinstance(head, str):
        # Object property
        if not isinstance(data, dict):
            raise ValueError(f"Property '{head}' accessed on non-object: {type(data).__name__}")
        if head not in data:
            raise KeyError(f"Property '{head}' not found. Available: {', '.join(data.keys())}")
        return resolve_path(data[head], tail)

    raise ValueError(f"Invalid path component: {head}")


def list_keys(data: Any, prefix: str = "") -> List[str]:
    """List all available paths in the data structure."""
    paths = []

    if isinstance(data, dict):
        for key in data.keys():
            full_path = f"{prefix}.{key}" if prefix else key
            paths.append(full_path)
            paths.extend(list_keys(data[key], full_path))
    elif isinstance(data, list) and len(data) > 0:
        # Show structure of first element
        paths.append(f"{prefix}[0]" if prefix else "[0]")
        paths.append(f"{prefix}[*]" if prefix else "[*]")
        paths.extend(list_keys(data[0], f"{prefix}[0]" if prefix else "[0]"))

    return paths


def format_output(data: Any, compact: bool = False, raw: bool = False) -> str:
    """Format the output data."""
    if raw and isinstance(data, str):
        return data

    if compact:
        return json.dumps(data, separators=(",", ":"))
    else:
        return json.dumps(data, indent=2)


def summarize(data: Any, depth: int = 0, max_depth: int = 3) -> str:
    """Generate a structural summary of the data."""
    indent = "  " * depth

    if isinstance(data, dict):
        if depth >= max_depth:
            return f"{{{len(data)} keys}}"
        lines = ["{"]
        for key, value in list(data.items())[:10]:
            summary = summarize(value, depth + 1, max_depth)
            lines.append(f"{indent}  {key}: {summary}")
        if len(data) > 10:
            lines.append(f"{indent}  ... and {len(data) - 10} more keys")
        lines.append(f"{indent}}}")
        return "\n".join(lines)

    elif isinstance(data, list):
        if len(data) == 0:
            return "[]"
        if depth >= max_depth:
            return f"[{len(data)} items]"
        first = summarize(data[0], depth + 1, max_depth)
        return f"[{len(data)} items] first: {first}"

    elif isinstance(data, str):
        if len(data) > 50:
            return f'"{data[:47]}..."'
        return f'"{data}"'

    elif isinstance(data, bool):
        return str(data).lower()

    elif isinstance(data, (int, float)):
        return str(data)

    elif data is None:
        return "null"

    return str(type(data).__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Query JSON files with simple path syntax",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jsonq file.json user.name           Get a nested property
  jsonq file.json items[0]            Get first array element
  jsonq file.json items[-1].id        Get last element's id
  jsonq file.json items[*].name       Get name from all items
  jsonq file.json --keys              List all available paths
  jsonq file.json --summary           Show structure overview
  cat file.json | jsonq - user.name   Read from stdin
  jsonq file.json . --compact         Output compact JSON
        """
    )

    parser.add_argument("file", help="JSON file to query (use '-' for stdin)")
    parser.add_argument("path", nargs="?", default=".",
                        help="Path to query (default: root)")
    parser.add_argument("-k", "--keys", action="store_true",
                        help="List all available paths")
    parser.add_argument("-s", "--summary", action="store_true",
                        help="Show structural summary")
    parser.add_argument("-c", "--compact", action="store_true",
                        help="Output compact JSON")
    parser.add_argument("-r", "--raw", action="store_true",
                        help="Output raw strings without quotes")
    parser.add_argument("-t", "--type", action="store_true",
                        help="Show type of result instead of value")
    parser.add_argument("-l", "--length", action="store_true",
                        help="Show length (for arrays/strings/objects)")

    args = parser.parse_args()

    # Load JSON
    try:
        if args.file == "-":
            data = json.load(sys.stdin)
        else:
            path = Path(args.file)
            if not path.exists():
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            with open(path) as f:
                data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle special modes
    if args.keys:
        paths = list_keys(data)
        for p in paths[:50]:  # Limit output
            print(p)
        if len(paths) > 50:
            print(f"... and {len(paths) - 50} more paths")
        sys.exit(0)

    if args.summary:
        print(summarize(data))
        sys.exit(0)

    # Query the data
    if args.path == ".":
        result = data
    else:
        try:
            components = parse_path(args.path)
            result = resolve_path(data, components)
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Output the result
    if args.type:
        if isinstance(result, list):
            print(f"array ({len(result)} items)")
        elif isinstance(result, dict):
            print(f"object ({len(result)} keys)")
        elif isinstance(result, str):
            print(f"string ({len(result)} chars)")
        elif isinstance(result, bool):
            print("boolean")
        elif isinstance(result, int):
            print("integer")
        elif isinstance(result, float):
            print("number")
        elif result is None:
            print("null")
    elif args.length:
        if isinstance(result, (list, dict, str)):
            print(len(result))
        else:
            print("Error: --length requires array, object, or string", file=sys.stderr)
            sys.exit(1)
    else:
        print(format_output(result, compact=args.compact, raw=args.raw))


if __name__ == "__main__":
    main()
