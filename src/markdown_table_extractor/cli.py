"""Command-line interface for markdown-table-extractor.

Usage:
    mte extract input.md                    # Extract to stdout
    mte extract input.md -o tables.csv      # Save to CSV
    mte extract input.md --format json      # Output as JSON
    mte extract input.md --llm              # Use LLM extraction
    mte extract input.md --hybrid           # Regex + LLM fallback
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def main(args: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="mte",
        description="Extract tables from markdown files",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Extract command
    extract_parser = subparsers.add_parser(
        "extract", 
        help="Extract tables from a markdown file"
    )
    extract_parser.add_argument(
        "input",
        type=Path,
        help="Input markdown file (use - for stdin)",
    )
    extract_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)",
    )
    extract_parser.add_argument(
        "-f", "--format",
        choices=["csv", "json", "markdown", "rich"],
        default=None,
        help="Output format (default: rich for terminal, csv for files)",
    )
    extract_parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Don't merge continuation tables",
    )
    extract_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM-based extraction",
    )
    extract_parser.add_argument(
        "--hybrid",
        action="store_true",
        help="Use regex first, LLM fallback",
    )
    extract_parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model ID (default: gpt-4o-mini)",
    )
    extract_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    parsed = parser.parse_args(args)
    
    if parsed.command == "extract":
        return cmd_extract(parsed)
    else:
        parser.print_help()
        return 0


def cmd_extract(args: argparse.Namespace) -> int:
    """Execute the extract command."""
    from markdown_table_extractor import (
        extract_markdown_tables,
        TableMergeStrategy,
    )
    
    # Read input
    if str(args.input) == "-":
        text = sys.stdin.read()
    else:
        if not args.input.exists():
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            return 1
        text = args.input.read_text()
    
    # Choose extraction method
    if args.llm:
        try:
            from markdown_table_extractor.llm import extract_with_llm
            result = extract_with_llm(text, model_id=args.model)
        except ImportError:
            print(
                "Error: LLM extraction requires 'llm' library. "
                "Install with: pip install 'markdown-table-extractor[llm]'",
                file=sys.stderr
            )
            return 1
    elif args.hybrid:
        try:
            from markdown_table_extractor.llm import extract_tables_hybrid
            result = extract_tables_hybrid(text, llm_model_id=args.model)
        except ImportError:
            print(
                "Error: Hybrid extraction requires 'llm' library. "
                "Install with: pip install 'markdown-table-extractor[llm]'",
                file=sys.stderr
            )
            return 1
    else:
        strategy = (
            TableMergeStrategy.NONE 
            if args.no_merge 
            else TableMergeStrategy.IDENTICAL_HEADERS
        )
        result = extract_markdown_tables(text, merge_strategy=strategy)
    
    # Handle results
    if not result.tables:
        if args.verbose:
            print("No tables found.", file=sys.stderr)
        return 0
    
    if args.verbose:
        print(
            f"Found {len(result.tables)} table(s), "
            f"merged {result.merged_count}",
            file=sys.stderr
        )

    # Auto-detect format if not specified
    fmt = args.format
    if fmt is None:
        # Rich for terminal, CSV for files
        fmt = "csv" if args.output else "rich"

    # Output
    if fmt == "rich" and not args.output:
        # Rich tables go directly to console, not through string
        format_rich_tables(result)
    else:
        output_text = format_output(result, fmt)

        if args.output:
            args.output.write_text(output_text)
            if args.verbose:
                print(f"Wrote to {args.output}", file=sys.stderr)
        else:
            print(output_text)

    return 0


def format_output(result, fmt: str) -> str:
    """Format extraction result for output."""
    from markdown_table_extractor import ExtractionResult
    
    if fmt == "csv":
        # Concatenate all tables with separator
        parts = []
        for i, table in enumerate(result.tables):
            if table.caption:
                parts.append(f"# {table.caption}")
            parts.append(table.dataframe.to_csv(index=False))
            if i < len(result.tables) - 1:
                parts.append("")  # Blank line between tables
        return "\n".join(parts)
    
    elif fmt == "json":
        tables_data = []
        for table in result.tables:
            tables_data.append({
                "caption": table.caption,
                "rows": table.row_count,
                "columns": list(table.dataframe.columns),
                "data": table.dataframe.to_dict(orient="records"),
            })
        return json.dumps(tables_data, indent=2)
    
    elif fmt == "markdown":
        parts = []
        for table in result.tables:
            if table.caption:
                parts.append(f"## {table.caption}\n")
            parts.append(table.dataframe.to_markdown(index=False))
            parts.append("")
        return "\n".join(parts)
    
    else:
        raise ValueError(f"Unknown format: {fmt}")


def format_rich_tables(result) -> None:
    """Display tables using rich formatting to the console."""
    from rich.console import Console
    from rich.table import Table as RichTable
    from rich.panel import Panel
    from rich.text import Text

    console = Console()

    for i, table in enumerate(result.tables):
        # Create rich table
        rich_table = RichTable(
            title=table.caption if table.caption else f"Table {i + 1}",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            title_style="bold magenta",
        )

        # Add columns
        df = table.dataframe
        for col in df.columns:
            rich_table.add_column(str(col), overflow="fold")

        # Add rows
        for _, row in df.iterrows():
            rich_table.add_row(*[str(val) for val in row])

        # Display table
        console.print(rich_table)

        # Add spacing between tables
        if i < len(result.tables) - 1:
            console.print()


if __name__ == "__main__":
    sys.exit(main())