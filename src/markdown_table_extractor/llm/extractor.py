"""LLM-powered table extraction using datasette/llm.

This module provides AI-powered table extraction for edge cases
that regex-based parsing can't handle reliably.

Uses Simon Willison's `llm` library which provides:
- Unified API across OpenAI, Anthropic, Ollama, and more
- Built-in logging and conversation tracking (SQLite)
- Structured output via Pydantic schemas

Install providers:
    pip install llm              # Core library
    llm install llm-claude-3     # Anthropic models
    llm install llm-ollama       # Local Ollama models

Import directly:
    from markdown_table_extractor.llm import extract_with_llm
"""

from __future__ import annotations

import marimo
import json
from typing import Optional
from dataclasses import dataclass
import pandas as pd

# Core imports
from markdown_table_extractor.core.models import (
    ExtractedTable,
    ExtractionResult,
)

# Pydantic for structured output schemas
from pydantic import BaseModel, Field

__generated_with = "0.18.0"
app = marimo.App(width="medium")


# =============================================================================
# SETUP CELL
# =============================================================================
with app.setup:
    import marimo as mo


# =============================================================================
# DOCUMENTATION
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # 🤖 LLM-Powered Table Extraction
    
    This module uses Simon Willison's [`llm`](https://llm.datasette.io/) library
    for AI-powered table extraction.
    
    ## Why use LLM extraction?
    
    | Regex Extraction | LLM Extraction |
    |------------------|----------------|
    | Fast, deterministic | Slower, costs money |
    | Handles standard markdown | Handles malformed tables |
    | Fails on edge cases | Robust to variations |
    | No dependencies | Requires API keys |
    
    **Best approach:** Use regex first, fall back to LLM for failures.
    
    ## Setup
    
    ```bash
    # Install core library
    pip install llm
    
    # Set up API key (stored securely)
    llm keys set openai
    # or
    llm keys set anthropic
    
    # Install additional providers
    llm install llm-claude-3     # Anthropic
    llm install llm-ollama       # Local models
    llm install llm-gemini       # Google
    ```
    
    ## Built-in Logging
    
    Every LLM call is automatically logged to SQLite:
    
    ```bash
    # View recent prompts
    llm logs
    
    # Open in Datasette
    datasette "$(llm logs path)"
    ```
    """)
    return


# =============================================================================
# Pydantic Schemas for Structured Output
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Output Schemas
    
    We define Pydantic models that the LLM will populate.
    The `llm` library converts these to JSON Schema automatically.
    """)
    return


@app.class_definition
class LLMTableRow(BaseModel):
    """A single row of table data."""
    cells: list[str] = Field(description="Cell values in order")


@app.class_definition  
class LLMExtractedTable(BaseModel):
    """A single extracted table."""
    caption: Optional[str] = Field(
        None, 
        description="Table caption if found (e.g., 'Table 1. Results')"
    )
    headers: list[str] = Field(
        description="Column headers in order"
    )
    rows: list[LLMTableRow] = Field(
        description="Data rows (excluding header and separator)"
    )


@app.class_definition
class LLMExtractionResponse(BaseModel):
    """Complete extraction response."""
    tables: list[LLMExtractedTable] = Field(
        description="All tables found in the text"
    )
    notes: Optional[str] = Field(
        None,
        description="Any issues or notes about the extraction"
    )


# =============================================================================
# System Prompt
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## System Prompt
    
    The prompt instructs the LLM on how to extract tables.
    """)
    return


SYSTEM_PROMPT = """You are a precise data extraction assistant specializing in markdown tables.

Your task is to extract ALL tables from the provided text into structured JSON.

Rules:
1. Extract EVERY table, even if malformed or incomplete
2. Preserve exact cell values - do not modify or interpret data
3. Skip separator rows (like |---|---|)
4. Detect captions that appear before tables (e.g., "Table 1. Results")
5. Handle multi-level headers by combining them (e.g., "Outcome (Early)")
6. Clean HTML artifacts like <br> from headers
7. If a table is marked "(Continued)", note this in the caption

Common issues to handle:
- Tables split across pages with "(Continued)" markers
- Alignment syntax like :--: or ---: in separators  
- Missing cells (pad with empty strings)
- HTML tags in headers (<br>, <span>, etc.)
"""


# =============================================================================
# extract_with_llm
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## `extract_with_llm(text, model_id)`
    
    Main extraction function using the `llm` library.
    
    ```python
    from markdown_table_extractor.llm import extract_with_llm
    
    result = extract_with_llm(markdown_text, model_id="gpt-4o-mini")
    for table in result:
        print(table.dataframe)
    ```
    
    **Supported models** (depends on installed plugins):
    - `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo` (OpenAI)
    - `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest` (Anthropic)
    - `gemini-1.5-flash`, `gemini-1.5-pro` (Google)
    - Any Ollama model (local)
    """)
    return


@app.function
def extract_with_llm(
    text: str,
    model_id: str = "gpt-4o-mini",
    system_prompt: Optional[str] = None,
) -> ExtractionResult:
    """Extract tables from text using an LLM.
    
    Uses Simon Willison's `llm` library for unified access to
    multiple LLM providers with built-in logging.
    
    Args:
        text: The markdown/text containing tables
        model_id: Model identifier (e.g., "gpt-4o-mini", "claude-3-5-sonnet-latest")
        system_prompt: Custom system prompt (uses default if None)
        
    Returns:
        ExtractionResult with extracted tables
        
    Raises:
        ImportError: If `llm` library is not installed
        
    Examples:
        >>> result = extract_with_llm(markdown_text)
        >>> for table in result:
        ...     print(table.caption)
    """
    try:
        import llm
    except ImportError:
        raise ImportError(
            "The 'llm' library is required for LLM extraction. "
            "Install it with: pip install llm"
        )
    
    result = ExtractionResult()
    prompt_text = system_prompt or SYSTEM_PROMPT
    
    try:
        model = llm.get_model(model_id)
        
        response = model.prompt(
            f"{prompt_text}\n\n---\n\nExtract tables from:\n\n{text}",
            schema=LLMExtractionResponse
        )
        
        # Parse the structured response
        response_data = json.loads(response.text())
        llm_result = LLMExtractionResponse(**response_data)
        
        # Convert to our internal format
        for llm_table in llm_result.tables:
            df = _llm_table_to_dataframe(llm_table)
            if df is not None:
                table = ExtractedTable(
                    dataframe=df,
                    caption=llm_table.caption,
                    is_continuation="continued" in (llm_table.caption or "").lower()
                )
                result.tables.append(table)
        
        if llm_result.notes:
            result.errors.append(f"LLM note: {llm_result.notes}")
            
    except Exception as e:
        result.errors.append(f"LLM extraction error: {e}")
    
    return result


@app.function
def _llm_table_to_dataframe(llm_table: LLMExtractedTable) -> Optional[pd.DataFrame]:
    """Convert LLM extracted table to DataFrame."""
    if not llm_table.headers or not llm_table.rows:
        return None
    
    # Normalize row lengths to match headers
    num_cols = len(llm_table.headers)
    data = []
    
    for row in llm_table.rows:
        cells = row.cells[:num_cols]  # Truncate if too long
        cells.extend([''] * (num_cols - len(cells)))  # Pad if too short
        data.append(cells)
    
    return pd.DataFrame(data, columns=llm_table.headers)


# =============================================================================
# llm_extract (Simple API)
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## `llm_extract(text, model_id)` - Simple API
    
    Returns just the DataFrames for quick usage.
    """)
    return


@app.function
def llm_extract(
    text: str,
    model_id: str = "gpt-4o-mini"
) -> list[pd.DataFrame]:
    """Extract tables using LLM - simple API returning DataFrames.
    
    Args:
        text: Text containing tables
        model_id: Model to use
        
    Returns:
        List of pandas DataFrames
    """
    result = extract_with_llm(text, model_id)
    return result.get_dataframes()


# =============================================================================
# Hybrid Extraction
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## `extract_tables_hybrid(text, llm_model_id)`
    
    **Recommended approach:** Try regex first, fall back to LLM.
    
    This gives you:
    - Speed for well-formed tables
    - Robustness for edge cases
    - Cost savings (only uses LLM when needed)
    """)
    return


@app.function
def extract_tables_hybrid(
    text: str,
    llm_model_id: str = "gpt-4o-mini",
    llm_on_empty: bool = True,
    llm_on_error: bool = True,
) -> ExtractionResult:
    """Extract tables with regex first, LLM fallback.
    
    Args:
        text: Text containing tables
        llm_model_id: Model to use for LLM fallback
        llm_on_empty: Use LLM if regex finds no tables
        llm_on_error: Use LLM if regex extraction has errors
        
    Returns:
        ExtractionResult from regex or LLM
    """
    from markdown_table_extractor.core.extractor import extract_markdown_tables
    
    # Try regex first
    result = extract_markdown_tables(text)
    
    # Check if we should fall back to LLM
    use_llm = False
    
    if llm_on_empty and len(result.tables) == 0:
        use_llm = True
    
    if llm_on_error and result.has_errors:
        use_llm = True
    
    if use_llm:
        llm_result = extract_with_llm(text, llm_model_id)
        # Prefer LLM result if it found more tables
        if len(llm_result.tables) >= len(result.tables):
            return llm_result
    
    return result


# =============================================================================
# INTERACTIVE DEMO
# =============================================================================
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ---
    ## 🧪 Interactive Demo
    
    Test LLM extraction (requires `llm` library and API key):
    """)
    return


@app.cell
def _():
    # Check if llm is available
    try:
        import llm
        available_models = [m.model_id for m in llm.get_models()]
        llm_available = True
    except ImportError:
        available_models = []
        llm_available = False
    
    if llm_available:
        mo.md(f"""
        ✅ **`llm` library installed**
        
        Available models: {', '.join(available_models[:5])}{'...' if len(available_models) > 5 else ''}
        
        To add more models:
        ```bash
        llm install llm-claude-3
        llm install llm-ollama
        ```
        """)
    else:
        mo.md("""
        ⚠️ **`llm` library not installed**
        
        Install with:
        ```bash
        pip install llm
        llm keys set openai  # or anthropic
        ```
        """)
    return (available_models, llm_available)


@app.cell
def _(available_models, llm_available):
    # Model selector
    if llm_available and available_models:
        model_selector = mo.ui.dropdown(
            options=available_models,
            value=available_models[0],
            label="Select model:"
        )
    else:
        model_selector = mo.ui.text(
            value="gpt-4o-mini",
            label="Model ID (llm not available):",
            disabled=True
        )
    model_selector
    return (model_selector,)


@app.cell
def _():
    sample_text = """
Table 5. Patient Outcomes at 6 Months

| Patient ID | Treatment | Outcome | Score |
| :--: | :--: | :--: | :--: |
| P001 | Drug A | Improved | 85 |
| P002 | Placebo | Stable | 72 |
| P003 | Drug A | Improved | 91 |
"""
    
    demo_input = mo.ui.text_area(
        value=sample_text,
        label="**Text to extract from:**",
        rows=12,
        full_width=True
    )
    demo_input
    return (demo_input, sample_text)


@app.cell
def _(demo_input, llm_available, model_selector):
    if llm_available:
        extract_btn = mo.ui.run_button(label="🚀 Extract with LLM")
        mo.hstack([extract_btn, mo.md(f"Using model: **{model_selector.value}**")])
    else:
        mo.callout(
            "Install `llm` library to test extraction",
            kind="warn"
        )
    return


@app.cell
def _(demo_input, extract_btn, llm_available, model_selector):
    if llm_available and extract_btn.value:
        mo.md("*Extracting...*")
        result = extract_with_llm(demo_input.value, model_selector.value)
        
        if result.tables:
            table = result.tables[0]
            mo.vstack([
                mo.md(f"""
                ### Extraction Result
                
                - **Tables found:** {len(result.tables)}
                - **Caption:** {table.caption}
                - **Rows:** {table.row_count}
                """),
                mo.ui.table(table.dataframe)
            ])
        else:
            mo.callout(
                f"No tables extracted. Errors: {result.errors}",
                kind="warn"
            )
    return


if __name__ == "__main__":
    app.run()
