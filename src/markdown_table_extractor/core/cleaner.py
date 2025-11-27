"""Data cleaning utilities for extracted tables.

Functions for cleaning column names, values, and normalizing data.
"""
from __future__ import annotations

import marimo
import re
from typing import Optional


# ============================================================================
# MODULE-LEVEL CODE (importable)
# ============================================================================


def clean_column_name(name: str) -> str:
    """Clean a column name for consistency.
    
    - Strips whitespace
    - Removes HTML tags like <br>
    - Normalizes multiple spaces
    - Converts to lowercase for comparison
    
    Args:
        name: Raw column name
        
    Returns:
        Cleaned column name
    """
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", name)
    
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    
    return cleaned.strip()


def clean_value(value: str) -> str:
    """Clean a cell value.
    
    - Strips whitespace
    - Removes HTML tags
    - Handles common artifacts
    
    Args:
        value: Raw cell value
        
    Returns:
        Cleaned value
    """
    if not value:
        return ""
    
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", value)
    
    # Replace HTML entities
    cleaned = cleaned.replace("&nbsp;", " ")
    cleaned = cleaned.replace("&amp;", "&")
    cleaned = cleaned.replace("&lt;", "<")
    cleaned = cleaned.replace("&gt;", ">")
    
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    
    return cleaned.strip()


def normalize_headers(headers: list[str]) -> list[str]:
    """Normalize headers for comparison.
    
    Creates lowercase, cleaned versions for matching.
    
    Args:
        headers: List of header strings
        
    Returns:
        List of normalized headers
    """
    return [clean_column_name(h).lower() for h in headers]


def headers_match(
    headers1: list[str], 
    headers2: list[str],
    threshold: float = 0.8,
) -> bool:
    """Check if two header lists are similar enough to merge.
    
    Args:
        headers1: First header list
        headers2: Second header list
        threshold: Fraction of headers that must match (default 0.8)
        
    Returns:
        True if headers are similar enough
    """
    if len(headers1) != len(headers2):
        return False
    
    if not headers1:
        return True
    
    norm1 = normalize_headers(headers1)
    norm2 = normalize_headers(headers2)
    
    matches = sum(1 for h1, h2 in zip(norm1, norm2) if h1 == h2)
    
    return matches / len(headers1) >= threshold


def merge_sub_header(headers: list[str], sub_header: list[str]) -> list[str]:
    """Merge a sub-header row into the main headers.
    
    For tables with multi-level headers, this combines them:
    ["Name", "Age", ""] + ["", "", "Years"] -> ["Name", "Age", "Years"]
    
    Args:
        headers: Main header row
        sub_header: Sub-header row
        
    Returns:
        Merged headers
    """
    result = []
    for h, sh in zip(headers, sub_header):
        if sh.strip() and not h.strip():
            result.append(sh.strip())
        elif sh.strip() and h.strip():
            result.append(f"{h.strip()} {sh.strip()}")
        else:
            result.append(h.strip())
    
    return result


# ============================================================================
# MARIMO NOTEBOOK (interactive documentation)
# ============================================================================

app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from markdown_table_extractor.core.cleaner import (
        clean_column_name,
        clean_value,
        headers_match,
        normalize_headers,
        merge_sub_header,
    )
    return (mo, clean_column_name, clean_value, headers_match, normalize_headers, merge_sub_header)


@app.cell
def _(mo):
    mo.md(
        """
        # Data Cleaning Utilities

        Functions for normalizing column names and cell values.

        ## Key Functions

        - `clean_column_name(name)` - Clean a single header
        - `clean_value(value)` - Clean a cell value
        - `headers_match(h1, h2)` - Check if headers are similar
        - `normalize_headers(headers)` - Normalize for comparison
        """
    )
    return


@app.cell
def _(mo):
    mo.md("## 🧹 HTML Cleaning Demo")
    return


@app.cell
def _(mo, clean_column_name, clean_value):
    # Test HTML cleaning with before/after visualization
    _dirty_examples = [
        ("Column<br>Name", "Column header with line break"),
        ("Patient&nbsp;ID", "Header with non-breaking space"),
        ("Age<br>(years)", "Header with parenthetical"),
        ("Group&nbsp;A<br>n=50", "Complex header with HTML entities"),
    ]

    _results = []
    for dirty_text, description in _dirty_examples:
        _cleaned = clean_column_name(dirty_text)
        _results.append({
            "Input": dirty_text,
            "Output": _cleaned,
            "Description": description
        })

    mo.vstack([
        mo.md("### Before & After Cleaning"),
        mo.accordion({
            example["Description"]: mo.vstack([
                mo.md(f"**Input (with HTML):** `{example['Input']}`"),
                mo.md(f"**Output (cleaned):** `{example['Output']}`"),
                mo.callout(
                    f"Removed: {set(example['Input']) - set(example['Output']) if example['Input'] != example['Output'] else 'nothing'}",
                    kind="neutral"
                ) if example['Input'] != example['Output'] else mo.md("")
            ])
            for example in _results
        }, multiple=True)
    ])
    return


@app.cell
def _(mo):
    mo.md("## 🔀 Header Matching Demo")
    return


@app.cell
def _(mo, headers_match):
    # Test header matching with visual comparison
    _header_tests = [
        (["Name", "Age", "City"], ["name", "age", "city"], "Same headers, different case"),
        (["Name", "Age", "City"], ["Name", "Age", "Location"], "One column different"),
        (["ID", "Patient Name", "Score"], ["ID", "Patient Name", "Score"], "Exact match"),
        (["Column A", "Column B"], ["Column A", "Column C"], "50% match"),
    ]

    _comparison_results = []
    for h1, h2, desc in _header_tests:
        _match = headers_match(h1, h2)
        _emoji = "✅" if _match else "❌"
        _comparison_results.append(mo.vstack([
            mo.md(f"### {desc}"),
            mo.md(f"**Headers 1:** `{h1}`"),
            mo.md(f"**Headers 2:** `{h2}`"),
            mo.callout(
                f"{_emoji} Match result: **{_match}**",
                kind="success" if _match else "warn"
            ),
        ]))

    mo.vstack(_comparison_results)
    return


if __name__ == "__main__":
    app.run()
