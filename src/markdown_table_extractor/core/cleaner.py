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
    import pandas as pd
    from markdown_table_extractor.core.cleaner import (
        clean_column_name,
        clean_value,
        headers_match,
        normalize_headers,
        merge_sub_header,
    )
    return (mo, pd, clean_column_name, clean_value, headers_match, normalize_headers, merge_sub_header)


@app.cell
def _(mo):
    mo.md("# Data Cleaning Utilities")
    return


@app.cell
def _(mo):
    mo.md("""
    ## `clean_column_name(name: str) -> str`

    Remove HTML tags and normalize whitespace in column names.
    """)
    return


@app.cell
def _(mo, clean_column_name):
    # Examples showing HTML cleaning
    _examples = [
        "Column<br>Name",
        "Patient&nbsp;ID",
        "Age<br>(years)",
    ]

    _cleaned = [clean_column_name(ex) for ex in _examples]

    mo.vstack([
        mo.md("**Before → After:**"),
        *[mo.md(f"- `{before}` → `{after}`") for before, after in zip(_examples, _cleaned)],
        mo.callout(f"Cleaned {len(_examples)} column names", kind="success")
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## `clean_value(value: str) -> str`

    Clean cell values by removing HTML and normalizing whitespace.
    """)
    return


@app.cell
def _(mo, clean_value):
    _value = "Data<br>with&nbsp;HTML"
    _cleaned_val = clean_value(_value)

    mo.vstack([
        mo.md(f"**Input:** `{_value}`"),
        mo.md(f"**Output:** `{_cleaned_val}`"),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## `headers_match(h1, h2, threshold=0.8) -> bool`

    Check if two header lists are similar enough to merge.
    """)
    return


@app.cell
def _(mo, headers_match):
    # Test cases
    _h1 = ["Name", "Age", "City"]
    _h2_same = ["name", "age", "city"]  # Case different
    _h3_diff = ["Name", "Age", "Location"]  # One column different

    _match1 = headers_match(_h1, _h2_same)
    _match2 = headers_match(_h1, _h3_diff)

    mo.vstack([
        mo.md(f"`{_h1}` vs `{_h2_same}` → **{_match1}** (case-insensitive match)"),
        mo.md(f"`{_h1}` vs `{_h3_diff}` → **{_match2}** (one column different)"),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---

    ## 🧹 Comprehensive Cleaning Demo
    """)
    return


@app.cell
def _(mo, clean_column_name, clean_value, pd):
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
            "Description": description,
            "Before": dirty_text,
            "After": _cleaned,
            "Cleaned": "✅" if dirty_text != _cleaned else "—"
        })

    _clean_df = pd.DataFrame(_results)

    mo.vstack([
        mo.md("### Before & After Cleaning"),
        mo.ui.table(_clean_df, selection=None),
        mo.callout(
            f"Cleaned {len([r for r in _results if r['Cleaned'] == '✅'])} out of {len(_results)} examples",
            kind="success"
        )
    ])
    return


@app.cell
def _(mo):
    mo.md("## 🔀 Header Matching Demo")
    return


@app.cell
def _(mo, headers_match, pd):
    # Test header matching with visual comparison
    _header_tests = [
        (["Name", "Age", "City"], ["name", "age", "city"], "Case-insensitive", True),
        (["Name", "Age", "City"], ["Name", "Age", "Location"], "One different", False),
        (["ID", "Patient Name", "Score"], ["ID", "Patient Name", "Score"], "Exact match", True),
        (["Column A", "Column B"], ["Column A", "Column C"], "50% match", False),
    ]

    _comparison_data = []
    for h1, h2, desc, expected in _header_tests:
        _match = headers_match(h1, h2)
        _emoji = "✅" if _match else "❌"
        _comparison_data.append({
            "Test": desc,
            "Headers 1": str(h1),
            "Headers 2": str(h2),
            "Match": _emoji + (" Yes" if _match else " No"),
            "Expected": "✅" if _match == expected else "⚠️"
        })

    _match_df = pd.DataFrame(_comparison_data)

    mo.vstack([
        mo.md("### Header Comparison Results"),
        mo.ui.table(_match_df, selection=None),
        mo.callout(
            "Headers are matched using normalized comparison (case-insensitive, cleaned)",
            kind="info"
        )
    ])
    return


if __name__ == "__main__":
    app.run()
