#!/usr/bin/env python3
"""
researchscan - R&D research aggregator for AI/ML developments

Collects and stores data from:
- arXiv (papers in cs.CL, cs.LG, cs.AI, cs.CV)
- HuggingFace (trending models by task)

Data is stored in SQLite for browsing/querying via Datasette or CLI.

Usage:
    python researchscan.py collect              # Run all collectors
    python researchscan.py collect arxiv        # Run specific collector
    python researchscan.py collect hf           # HuggingFace only
    python researchscan.py papers [--limit N]   # List recent papers
    python researchscan.py models [--limit N]   # List trending models
    python researchscan.py search <query>       # Search papers by title/summary
    python researchscan.py stats                # Show collection stats
    python researchscan.py new                  # Show papers since last check
    python researchscan.py digest [--days N]    # Generate markdown digest
"""

import argparse
import sqlite3
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import json
import re
import textwrap

# Optional: huggingface_hub for model data
try:
    from huggingface_hub import HfApi
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

# Default database location
DEFAULT_DB = Path(__file__).parent / "researchscan.db"

# arXiv categories relevant to DAEMON/local AI
ARXIV_CATEGORIES = [
    "cs.CL",  # Computation and Language (NLP, LLMs)
    "cs.LG",  # Machine Learning
    "cs.AI",  # Artificial Intelligence
    "cs.CV",  # Computer Vision (multimodal)
]

# HuggingFace tasks relevant to local AI development
HF_TASKS = [
    "text-generation",
    "automatic-speech-recognition",
    "text-to-speech",
    "image-to-text",
]

# Keywords that indicate relevance to local/personal AI
RELEVANCE_KEYWORDS = [
    "local", "efficient", "quantization", "quantized", "gguf", "ggml",
    "apple silicon", "mlx", "m1", "m2", "m3", "m4",
    "memory", "retrieval", "rag", "agent", "agents",
    "personalization", "personal", "private", "privacy",
    "small", "tiny", "compact", "lightweight", "mobile",
    "ollama", "llama", "mistral", "phi", "qwen", "gemma",
    "fine-tuning", "lora", "qlora", "adapter",
    "embedding", "embeddings", "vector", "semantic",
    "voice", "speech", "whisper", "tts", "stt",
]


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize database with schema."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS arxiv_papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT,
            categories TEXT,
            authors TEXT,
            published TEXT,
            updated TEXT,
            pdf_url TEXT,
            relevance_score REAL DEFAULT 0,
            collected_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hf_models (
            model_id TEXT PRIMARY KEY,
            task TEXT,
            downloads INTEGER,
            likes INTEGER,
            last_modified TEXT,
            tags TEXT,
            pipeline_tag TEXT,
            collected_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_arxiv_published ON arxiv_papers(published);
        CREATE INDEX IF NOT EXISTS idx_arxiv_relevance ON arxiv_papers(relevance_score);
        CREATE INDEX IF NOT EXISTS idx_arxiv_collected ON arxiv_papers(collected_at);
        CREATE INDEX IF NOT EXISTS idx_hf_downloads ON hf_models(downloads);
        CREATE INDEX IF NOT EXISTS idx_hf_task ON hf_models(task);
        CREATE INDEX IF NOT EXISTS idx_hf_collected ON hf_models(collected_at);
    """)

    conn.commit()
    return conn


def calculate_relevance(title: str, summary: str) -> float:
    """Calculate relevance score based on keyword matches."""
    text = (title + " " + summary).lower()
    score = 0.0

    for keyword in RELEVANCE_KEYWORDS:
        if keyword.lower() in text:
            # Title matches worth more
            if keyword.lower() in title.lower():
                score += 2.0
            else:
                score += 1.0

    return score


def collect_arxiv(conn: sqlite3.Connection, verbose: bool = True) -> int:
    """Collect recent papers from arXiv."""
    # Build query for multiple categories
    category_query = "+OR+".join([f"cat:{cat}" for cat in ARXIV_CATEGORIES])
    url = f"http://export.arxiv.org/api/query?search_query={category_query}&start=0&max_results=200&sortBy=submittedDate&sortOrder=descending"

    if verbose:
        print(f"Fetching arXiv papers...")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
    except Exception as e:
        print(f"Error fetching arXiv: {e}", file=sys.stderr)
        return 0

    # Parse Atom feed
    root = ET.fromstring(content)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    count = 0
    now = datetime.now().isoformat()

    for entry in root.findall("atom:entry", ns):
        paper_id = entry.find("atom:id", ns).text
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        published = entry.find("atom:published", ns).text
        updated = entry.find("atom:updated", ns).text

        # Get authors
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.find("atom:name", ns)
            if name is not None:
                authors.append(name.text)

        # Get categories
        categories = []
        for cat in entry.findall("atom:category", ns):
            term = cat.get("term")
            if term:
                categories.append(term)

        # Get PDF link
        pdf_url = None
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break

        # Calculate relevance
        relevance = calculate_relevance(title, summary)

        conn.execute("""
            INSERT OR REPLACE INTO arxiv_papers
            (id, title, summary, categories, authors, published, updated, pdf_url, relevance_score, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id,
            title,
            summary,
            ",".join(categories),
            ",".join(authors),
            published,
            updated,
            pdf_url,
            relevance,
            now
        ))
        count += 1

    conn.commit()
    if verbose:
        print(f"  Collected {count} papers from arXiv")
    return count


def collect_hf_models(conn: sqlite3.Connection, verbose: bool = True) -> int:
    """Collect trending models from HuggingFace."""
    if not HF_AVAILABLE:
        if verbose:
            print("  Skipping HuggingFace (huggingface_hub not installed)")
            print("  Install with: pip install huggingface_hub")
        return 0

    if verbose:
        print(f"Fetching HuggingFace models...")

    api = HfApi()
    count = 0
    now = datetime.now().isoformat()

    for task in HF_TASKS:
        try:
            models = api.list_models(
                sort="downloads",
                direction=-1,
                limit=30,
                filter=task
            )

            for m in models:
                tags = ",".join(m.tags) if m.tags else ""

                conn.execute("""
                    INSERT OR REPLACE INTO hf_models
                    (model_id, task, downloads, likes, last_modified, tags, pipeline_tag, collected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m.modelId,
                    task,
                    m.downloads,
                    m.likes,
                    str(m.lastModified) if m.lastModified else None,
                    tags,
                    m.pipeline_tag,
                    now
                ))
                count += 1

        except Exception as e:
            print(f"  Error fetching {task} models: {e}", file=sys.stderr)

    conn.commit()
    if verbose:
        print(f"  Collected {count} models from HuggingFace")
    return count


def cmd_collect(args, conn):
    """Run collectors."""
    if args.source in ("all", "arxiv"):
        collect_arxiv(conn)

    if args.source in ("all", "hf"):
        collect_hf_models(conn)

    print("Collection complete.")


def cmd_papers(args, conn):
    """List recent papers."""
    order = "relevance_score DESC, published DESC" if args.relevant else "published DESC"

    cursor = conn.execute(f"""
        SELECT id, title, categories, published, relevance_score
        FROM arxiv_papers
        ORDER BY {order}
        LIMIT ?
    """, (args.limit,))

    for row in cursor:
        # Truncate title if needed
        title = row["title"][:80] + "..." if len(row["title"]) > 80 else row["title"]
        cats = row["categories"].split(",")[:2]  # First 2 categories
        score = f"[{row['relevance_score']:.1f}]" if row["relevance_score"] > 0 else ""

        print(f"{score:6} {','.join(cats):12} {title}")


def cmd_models(args, conn):
    """List trending models."""
    query = """
        SELECT model_id, task, downloads, likes
        FROM hf_models
        ORDER BY downloads DESC
        LIMIT ?
    """

    if args.task:
        query = """
            SELECT model_id, task, downloads, likes
            FROM hf_models
            WHERE task = ?
            ORDER BY downloads DESC
            LIMIT ?
        """
        cursor = conn.execute(query, (args.task, args.limit))
    else:
        cursor = conn.execute(query, (args.limit,))

    for row in cursor:
        downloads = f"{row['downloads']:,}" if row["downloads"] else "?"
        likes = row["likes"] or 0
        print(f"{row['task']:30} {row['model_id']:50} {downloads:>15} ↓  {likes:>6} ♥")


def cmd_search(args, conn):
    """Search papers by title or summary."""
    query = f"%{args.query}%"

    cursor = conn.execute("""
        SELECT id, title, summary, categories, published, relevance_score
        FROM arxiv_papers
        WHERE title LIKE ? OR summary LIKE ?
        ORDER BY relevance_score DESC, published DESC
        LIMIT ?
    """, (query, query, args.limit))

    results = cursor.fetchall()

    if not results:
        print(f"No papers found matching '{args.query}'")
        return

    print(f"Found {len(results)} papers matching '{args.query}':\n")

    for row in results:
        score = f"[{row['relevance_score']:.1f}]" if row["relevance_score"] > 0 else "[0.0]"
        print(f"{score} {row['title'][:100]}")

        # Show snippet of summary with highlighted match
        summary = row["summary"][:200] + "..." if len(row["summary"]) > 200 else row["summary"]
        print(f"    {summary}\n")


def cmd_new(args, conn):
    """Show papers added since last check."""
    db_path = args.db
    state_file = db_path.parent / ".researchscan_last_check"

    # Get last check time
    last_check = None
    if state_file.exists():
        try:
            last_check = state_file.read_text().strip()
        except Exception:
            pass

    # Build query
    if last_check:
        cursor = conn.execute("""
            SELECT id, title, categories, relevance_score, pdf_url
            FROM arxiv_papers
            WHERE collected_at > ?
            ORDER BY relevance_score DESC, published DESC
        """, (last_check,))
    else:
        # First run — show high-relevance papers from today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = conn.execute("""
            SELECT id, title, categories, relevance_score, pdf_url
            FROM arxiv_papers
            WHERE collected_at >= ? AND relevance_score >= 2
            ORDER BY relevance_score DESC, published DESC
            LIMIT 20
        """, (today,))

    papers = cursor.fetchall()

    if not papers:
        if last_check:
            print(f"No new papers since {last_check[:19]}")
        else:
            print("No papers found. Run 'collect' first.")
        return

    print(f"=== New papers since {last_check[:19] if last_check else 'today'} ===\n")

    for row in papers:
        score = f"[{row['relevance_score']:.1f}]" if row["relevance_score"] > 0 else ""
        cats = row["categories"].split(",")[:2]
        title = row["title"][:75] + "..." if len(row["title"]) > 75 else row["title"]
        print(f"{score:6} {','.join(cats):12} {title}")

    print(f"\n{len(papers)} new papers")

    # Update last check time
    if not args.no_mark:
        state_file.write_text(datetime.now().isoformat())
        print(f"(marked as read)")


def cmd_stats(args, conn):
    """Show collection statistics."""
    print("=== researchscan statistics ===\n")

    # Paper stats
    cursor = conn.execute("SELECT COUNT(*) as count FROM arxiv_papers")
    paper_count = cursor.fetchone()["count"]

    cursor = conn.execute("""
        SELECT categories, COUNT(*) as count
        FROM arxiv_papers
        GROUP BY categories
        ORDER BY count DESC
        LIMIT 10
    """)

    print(f"arXiv Papers: {paper_count}")
    print("  By primary category:")
    for row in cursor:
        print(f"    {row['categories'][:30]:30} {row['count']:5}")

    # High relevance papers
    cursor = conn.execute("""
        SELECT COUNT(*) as count FROM arxiv_papers WHERE relevance_score >= 2
    """)
    high_rel = cursor.fetchone()["count"]
    print(f"  High relevance (≥2.0): {high_rel}")

    # Model stats
    cursor = conn.execute("SELECT COUNT(*) as count FROM hf_models")
    model_count = cursor.fetchone()["count"]

    print(f"\nHuggingFace Models: {model_count}")

    cursor = conn.execute("""
        SELECT task, COUNT(*) as count
        FROM hf_models
        GROUP BY task
        ORDER BY count DESC
    """)

    print("  By task:")
    for row in cursor:
        print(f"    {row['task']:35} {row['count']:5}")

    # Collection freshness
    cursor = conn.execute("SELECT MAX(collected_at) as latest FROM arxiv_papers")
    latest = cursor.fetchone()["latest"]
    if latest:
        print(f"\nLast collection: {latest}")


def cmd_digest(args, conn):
    """Generate markdown digest of recent findings."""
    days_ago = datetime.now() - timedelta(days=args.days)
    cutoff = days_ago.isoformat()

    print(f"# Research Digest — {datetime.now().strftime('%Y-%m-%d')}\n")
    print(f"*Papers and models from the last {args.days} days*\n")

    # High-relevance papers
    print("## 🔥 High-Relevance Papers\n")
    print("*Papers matching keywords: local, efficient, quantization, agents, memory, etc.*\n")

    cursor = conn.execute("""
        SELECT id, title, summary, categories, relevance_score, pdf_url
        FROM arxiv_papers
        WHERE relevance_score >= 2 AND collected_at >= ?
        ORDER BY relevance_score DESC, published DESC
        LIMIT 15
    """, (cutoff,))

    papers = cursor.fetchall()
    if papers:
        for row in papers:
            cats = row["categories"].split(",")[:2]
            cat_str = ", ".join(cats)
            print(f"### [{row['title'][:100]}]({row['pdf_url'] or row['id']})")
            print(f"*{cat_str}* — Relevance: {row['relevance_score']:.1f}\n")

            # Truncate summary
            summary = row["summary"][:400]
            if len(row["summary"]) > 400:
                summary += "..."
            print(f"> {summary}\n")
    else:
        print("*No high-relevance papers found in this period.*\n")

    # Recent papers by category
    print("\n## 📄 Recent Papers by Category\n")

    for cat in ARXIV_CATEGORIES:
        cursor = conn.execute("""
            SELECT title, pdf_url, id
            FROM arxiv_papers
            WHERE categories LIKE ? AND collected_at >= ?
            ORDER BY published DESC
            LIMIT 5
        """, (f"%{cat}%", cutoff))

        cat_papers = cursor.fetchall()
        if cat_papers:
            print(f"### {cat}\n")
            for row in cat_papers:
                url = row["pdf_url"] or row["id"]
                print(f"- [{row['title'][:80]}...]({url})")
            print()

    # Top models
    print("\n## 🤖 Top Models\n")

    for task in HF_TASKS:
        cursor = conn.execute("""
            SELECT model_id, downloads, likes
            FROM hf_models
            WHERE task = ?
            ORDER BY downloads DESC
            LIMIT 5
        """, (task,))

        models = cursor.fetchall()
        if models:
            task_name = task.replace("-", " ").title()
            print(f"### {task_name}\n")
            for row in models:
                downloads = f"{row['downloads']:,}" if row["downloads"] else "?"
                print(f"- [{row['model_id']}](https://huggingface.co/{row['model_id']}) — {downloads} downloads")
            print()

    print("\n---\n*Generated by researchscan*")


def main():
    parser = argparse.ArgumentParser(
        description="R&D research aggregator for AI/ML developments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python researchscan.py collect              # Collect from all sources
              python researchscan.py papers --relevant    # Show papers sorted by relevance
              python researchscan.py search "quantization"
              python researchscan.py digest --days 7      # Weekly digest
        """)
    )

    parser.add_argument("--db", type=Path, default=DEFAULT_DB,
                        help="Path to SQLite database")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # collect command
    collect_parser = subparsers.add_parser("collect", help="Run collectors")
    collect_parser.add_argument("source", nargs="?", default="all",
                                choices=["all", "arxiv", "hf"],
                                help="Data source to collect from")

    # papers command
    papers_parser = subparsers.add_parser("papers", help="List recent papers")
    papers_parser.add_argument("--limit", "-n", type=int, default=20,
                              help="Number of papers to show")
    papers_parser.add_argument("--relevant", "-r", action="store_true",
                              help="Sort by relevance instead of date")

    # models command
    models_parser = subparsers.add_parser("models", help="List trending models")
    models_parser.add_argument("--limit", "-n", type=int, default=20,
                              help="Number of models to show")
    models_parser.add_argument("--task", "-t", choices=HF_TASKS,
                              help="Filter by task")

    # search command
    search_parser = subparsers.add_parser("search", help="Search papers")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", "-n", type=int, default=10,
                              help="Max results to show")

    # stats command
    subparsers.add_parser("stats", help="Show collection statistics")

    # new command
    new_parser = subparsers.add_parser("new", help="Show papers since last check")
    new_parser.add_argument("--no-mark", action="store_true",
                           help="Don't mark papers as read")

    # digest command
    digest_parser = subparsers.add_parser("digest", help="Generate markdown digest")
    digest_parser.add_argument("--days", "-d", type=int, default=7,
                              help="Number of days to include")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize database
    conn = init_db(args.db)

    # Dispatch command
    commands = {
        "collect": cmd_collect,
        "papers": cmd_papers,
        "models": cmd_models,
        "search": cmd_search,
        "stats": cmd_stats,
        "new": cmd_new,
        "digest": cmd_digest,
    }

    commands[args.command](args, conn)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
