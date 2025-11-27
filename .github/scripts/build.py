#!/usr/bin/env python3
"""Build script for exporting marimo notebooks to WASM HTML.

This script exports all documentation notebooks to static HTML files
that can be hosted on GitHub Pages.

Usage:
    uv run .github/scripts/build.py
    python -m http.server -d _site  # Serve locally for testing
"""
from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

# Configuration
NOTEBOOKS_DIR = Path("src/markdown_table_extractor/core")
OUTPUT_DIR = Path("_site")
NOTEBOOKS = {
    "index.py": {"output": "index.html", "name": "index"},
    "parser.py": {"output": "parser.html", "name": "parser"},
    "cleaner.py": {"output": "cleaner.html", "name": "cleaner"},
    "merger.py": {"output": "merger.html", "name": "merger"},
    "extractor.py": {"output": "extractor.html", "name": "extractor"},
    "models.py": {"output": "models.html", "name": "models"},
}


def main():
    """Export all notebooks to WASM HTML."""
    print("=" * 60)
    print("Building marimo documentation site")
    print("=" * 60)
    print()

    # Clean output directory
    if OUTPUT_DIR.exists():
        print(f"Cleaning {OUTPUT_DIR}...")
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Export each notebook
    for notebook_file, config in NOTEBOOKS.items():
        notebook_path = NOTEBOOKS_DIR / notebook_file
        output_filename = config["output"]
        output_path = OUTPUT_DIR / output_filename
        name = config["name"]

        print(f"📓 Exporting {name} to static HTML...")

        # Export command - static HTML with pre-rendered outputs, code hidden
        cmd = [
            "uv",
            "run",
            "marimo",
            "export",
            "html",
            str(notebook_path),
            "-o",
            str(output_path),
            "--no-include-code",
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✓ Exported to {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Failed to export {name}")
            print(f"   Error: {e.stderr}")
            raise

    # Create .nojekyll file
    nojekyll = OUTPUT_DIR / ".nojekyll"
    nojekyll.touch()
    print(f"✓ Created {nojekyll}")

    # Create README in output
    readme = OUTPUT_DIR / "README.md"
    readme.write_text("""# Markdown Table Extractor Documentation

This site contains interactive documentation for the markdown-table-extractor library.

## Pages

- [Home](./index.html) - Main documentation hub
- [Parser](./parser.html) - Table parsing functions
- [Cleaner](./cleaner.html) - Data cleaning utilities
- [Merger](./merger.html) - Table merging logic
- [Extractor](./extractor.html) - Main extraction API
- [Models](./models.html) - Data models and types

All documentation is powered by [marimo](https://marimo.io) with pre-rendered static HTML!
""")
    print(f"✓ Created {readme}")

    print()
    print("=" * 60)
    print("Build complete! ✅")
    print("=" * 60)
    print()
    print("To serve locally:")
    print(f"  python -m http.server -d {OUTPUT_DIR}")
    print()
    print("To deploy to GitHub Pages:")
    print("  git add .")
    print("  git commit -m 'Update documentation'")
    print("  git push")
    print()


if __name__ == "__main__":
    main()
