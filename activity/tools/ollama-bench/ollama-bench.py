#!/usr/bin/env python3
"""
ollama-bench: Benchmark Ollama models for response time and memory usage.

Useful for comparing models when building local AI applications.

Usage:
    ollama-bench list                     # List available models
    ollama-bench run MODEL [PROMPT]       # Benchmark a single model
    ollama-bench compare MODEL1 MODEL2... # Compare multiple models
    ollama-bench --json ...               # Output as JSON
"""

import argparse
import json
import subprocess
import time
import sys
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class BenchmarkResult:
    model: str
    prompt: str
    first_token_ms: Optional[float]
    total_time_ms: float
    tokens_generated: int
    tokens_per_second: float
    response_preview: str
    error: Optional[str] = None


DEFAULT_PROMPTS = [
    "What is 2 + 2?",
    "Write a haiku about programming.",
    "Explain recursion in one sentence.",
]


def list_models() -> list[str]:
    """Get list of available Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return []

        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return []

        models = []
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except Exception:
        return []


def benchmark_model(model: str, prompt: str, verbose: bool = False) -> BenchmarkResult:
    """Benchmark a single model with a prompt."""

    if verbose:
        print(f"  Testing: {prompt[:50]}...", file=sys.stderr)

    try:
        start_time = time.perf_counter()
        first_token_time = None

        # Run ollama with streaming to capture first token time
        process = subprocess.Popen(
            ["ollama", "run", model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send prompt
        process.stdin.write(prompt + "\n")
        process.stdin.close()

        # Read output character by character to detect first token
        output = []
        first_char = process.stdout.read(1)
        if first_char:
            first_token_time = time.perf_counter()
            output.append(first_char)
            output.append(process.stdout.read())  # Read rest

        process.wait(timeout=120)
        end_time = time.perf_counter()

        response = "".join(output).strip()
        total_time_ms = (end_time - start_time) * 1000
        first_token_ms = (first_token_time - start_time) * 1000 if first_token_time else None

        # Estimate tokens (rough: 4 chars per token)
        tokens = len(response) // 4 + 1
        tps = tokens / (total_time_ms / 1000) if total_time_ms > 0 else 0

        return BenchmarkResult(
            model=model,
            prompt=prompt,
            first_token_ms=round(first_token_ms, 1) if first_token_ms else None,
            total_time_ms=round(total_time_ms, 1),
            tokens_generated=tokens,
            tokens_per_second=round(tps, 1),
            response_preview=response[:100] + "..." if len(response) > 100 else response
        )

    except subprocess.TimeoutExpired:
        return BenchmarkResult(
            model=model,
            prompt=prompt,
            first_token_ms=None,
            total_time_ms=120000,
            tokens_generated=0,
            tokens_per_second=0,
            response_preview="",
            error="Timeout after 120s"
        )
    except Exception as e:
        return BenchmarkResult(
            model=model,
            prompt=prompt,
            first_token_ms=None,
            total_time_ms=0,
            tokens_generated=0,
            tokens_per_second=0,
            response_preview="",
            error=str(e)
        )


def run_benchmark(model: str, prompts: list[str], verbose: bool = False) -> list[BenchmarkResult]:
    """Run benchmark on a model with multiple prompts."""
    results = []

    if verbose:
        print(f"\nBenchmarking {model}...", file=sys.stderr)

    # Warm-up run (first run is always slower due to model loading)
    if verbose:
        print("  Warm-up run...", file=sys.stderr)
    benchmark_model(model, "Hi", verbose=False)

    for prompt in prompts:
        result = benchmark_model(model, prompt, verbose=verbose)
        results.append(result)

    return results


def format_results_table(all_results: dict[str, list[BenchmarkResult]]) -> str:
    """Format results as a table."""
    lines = []

    for model, results in all_results.items():
        lines.append(f"\n=== {model} ===")
        lines.append("")

        # Summary stats
        valid_results = [r for r in results if not r.error]
        if valid_results:
            avg_first_token = sum(r.first_token_ms for r in valid_results if r.first_token_ms) / len([r for r in valid_results if r.first_token_ms])
            avg_total = sum(r.total_time_ms for r in valid_results) / len(valid_results)
            avg_tps = sum(r.tokens_per_second for r in valid_results) / len(valid_results)

            lines.append(f"  Avg first token: {avg_first_token:.0f}ms")
            lines.append(f"  Avg total time:  {avg_total:.0f}ms")
            lines.append(f"  Avg tokens/sec:  {avg_tps:.1f}")

        lines.append("")
        lines.append("  Per-prompt results:")

        for r in results:
            if r.error:
                lines.append(f"    ERROR: {r.error}")
                lines.append(f"      Prompt: {r.prompt[:40]}...")
            else:
                lines.append(f"    {r.first_token_ms or '?':>6}ms first | {r.total_time_ms:>6.0f}ms total | {r.tokens_per_second:>5.1f} tok/s")
                lines.append(f"      Prompt: {r.prompt[:40]}...")
                lines.append(f"      Response: {r.response_preview[:60]}...")

    return "\n".join(lines)


def format_comparison_table(all_results: dict[str, list[BenchmarkResult]]) -> str:
    """Format results as a comparison table."""
    lines = []
    lines.append("")
    lines.append("Model Comparison")
    lines.append("=" * 70)
    lines.append(f"{'Model':<30} {'First Token':>12} {'Total':>10} {'Tok/s':>8}")
    lines.append("-" * 70)

    for model, results in all_results.items():
        valid_results = [r for r in results if not r.error]
        if valid_results:
            avg_first = sum(r.first_token_ms for r in valid_results if r.first_token_ms) / max(1, len([r for r in valid_results if r.first_token_ms]))
            avg_total = sum(r.total_time_ms for r in valid_results) / len(valid_results)
            avg_tps = sum(r.tokens_per_second for r in valid_results) / len(valid_results)

            lines.append(f"{model:<30} {avg_first:>10.0f}ms {avg_total:>8.0f}ms {avg_tps:>7.1f}")
        else:
            lines.append(f"{model:<30} {'ERROR':>12} {'-':>10} {'-':>8}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Ollama models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    ollama-bench list
    ollama-bench run qwen2.5:7b
    ollama-bench run qwen2.5:7b "Explain quantum computing"
    ollama-bench compare qwen2.5:7b llama3.2:3b mistral:7b
    ollama-bench compare qwen2.5:7b llama3.2:3b --json
"""
    )

    parser.add_argument("command", choices=["list", "run", "compare"],
                        help="Command to execute")
    parser.add_argument("models", nargs="*", help="Model(s) to benchmark")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-p", "--prompts", nargs="+", help="Custom prompts to use")

    args = parser.parse_args()

    if args.command == "list":
        models = list_models()
        if not models:
            print("No models found. Is Ollama running?", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print("Available models:")
            for m in models:
                print(f"  {m}")
        return

    if args.command == "run":
        if not args.models:
            print("Error: Model name required", file=sys.stderr)
            sys.exit(1)

        model = args.models[0]
        prompts = args.prompts or args.models[1:] or DEFAULT_PROMPTS

        results = run_benchmark(model, prompts, verbose=args.verbose)

        if args.json:
            print(json.dumps([asdict(r) for r in results], indent=2))
        else:
            print(format_results_table({model: results}))
        return

    if args.command == "compare":
        if len(args.models) < 2:
            print("Error: At least 2 models required for comparison", file=sys.stderr)
            sys.exit(1)

        prompts = args.prompts or DEFAULT_PROMPTS
        all_results = {}

        for model in args.models:
            results = run_benchmark(model, prompts, verbose=args.verbose)
            all_results[model] = results

        if args.json:
            output = {m: [asdict(r) for r in rs] for m, rs in all_results.items()}
            print(json.dumps(output, indent=2))
        else:
            print(format_comparison_table(all_results))
            if args.verbose:
                print(format_results_table(all_results))


if __name__ == "__main__":
    main()
