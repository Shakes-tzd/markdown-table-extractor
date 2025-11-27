import marimo

__generated_with = "0.18.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    # Import from top-level package to avoid micropip issues
    import markdown_table_extractor
    from markdown_table_extractor import extract_tables, extract_markdown_tables
    return extract_markdown_tables, extract_tables, markdown_table_extractor, mo, pd


@app.cell
def _(mo):
    # Helper function to create code blocks with consistent styling
    def code_block(code: str, language: str = "python") -> mo.Html:
        return mo.md(f"```{language}\n{code}\n```")

    # Helper function to create module cards
    def module_card(name: str, description: str, functions: list[str], command: str) -> mo.Html:
        functions_list = "\n".join([f"- `{f}`" for f in functions])
        return mo.md(f"""
        ### {name}

        {description}

        **Key functions:**
        {functions_list}

        **Open interactively:**
        ```bash
        {command}
        ```
        """)
    return code_block, module_card


@app.cell
def _(code_block, mo):
    # Home page content
    home_content = mo.vstack([
        mo.md("""
        # 📊 Markdown Table Extractor

        > A Python library for extracting structured data from markdown tables,
        > designed for processing academic manuscripts and complex documents.
        """),

        mo.callout(
            mo.md("""
            **✨ Each module is an interactive marimo notebook** - you can run
            them as both documentation and executable code!
            """),
            kind="success"
        ),

        mo.md("## Features"),

        mo.accordion({
            "🎯 Smart Table Detection": mo.md("""
            - Handles complex alignment syntax (`:--:`, `---:`, `:---`)
            - Detects separator rows accurately
            - Parses headers and data rows intelligently
            """),

            "🔗 Continuation Tables": mo.md("""
            - Automatically merges tables marked as "(Continued)"
            - Three merge strategies available (NONE, IDENTICAL_HEADERS, COMPATIBLE_COLUMNS)
            - Preserves captions and metadata during merging
            """),

            "🧹 HTML Cleaning": mo.md("""
            - Removes `<br>` tags and other HTML artifacts
            - Normalizes whitespace
            - Cleans column names and cell values
            """),

            "📑 Advanced Features": mo.md("""
            - **Multi-level Headers** - Supports sub-header rows
            - **Caption Detection** - Finds patterns like "Table 3. Results"
            - **Export Formats** - CSV, JSON, Excel via pandas
            - **Type Hints** - Full type annotations for IDE support
            """),
        }, multiple=True),

        mo.md("""
        ## Architecture

        The library uses a **modular pipeline architecture**:

        ```
        Parser → Cleaner → Merger → Extractor
           ↑                            ↓
        Models ←──────────────────────────
        ```

        Each component is independent and testable.
        """),

        mo.md("## Installation"),

        mo.accordion({
            "pip": code_block("pip install markdown-table-extractor", "bash"),
            "uv": code_block("uv pip install markdown-table-extractor", "bash"),
            "poetry": code_block("poetry add markdown-table-extractor", "bash"),
        }),
    ])
    return (home_content,)


@app.cell
def _(extract_tables, mo):
    # Define example markdown text for demos
    _example_markdown = """
| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | New York |
| Bob   | 25  | London   |
"""

    # Simple API demo - extract the table
    _simple_demo_table = extract_tables(_example_markdown)[0]

    return


@app.cell
def _(code_block, extract_tables, mo):
    # Quick Start content
    quickstart_content = mo.vstack([
        mo.md("# ⚡ Quick Start"),

        mo.callout(
            "Get started in under 5 minutes!",
            kind="info"
        ),

        mo.md("## Installation"),
        code_block("pip install markdown-table-extractor", "bash"),

        mo.md("## Basic Usage"),

        mo.md("### Step 1: Import the library"),
        code_block('''import marimo as mo
import pandas as pd
from markdown_table_extractor import extract_tables, extract_markdown_tables'''),

        mo.md("### Step 2: Define a markdown document"),
        code_block('''markdown_text = """
# Employee Directory

Below is our current employee roster with location information:

| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | New York |
| Bob   | 25  | London   |

Updated as of Q4 2025.
"""'''),

        mo.md("### Step 3: See what the document looks like (rendered):"),
        mo.md("""
# Employee Directory

Below is our current employee roster with location information:

| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | New York |
| Bob   | 25  | London   |

Updated as of Q4 2025.
"""),

        mo.md("### Step 4: Extract the table with one line of code:"),
        code_block('''tables = extract_tables(markdown_text)
tables[0]  # Returns a pandas DataFrame'''),

        mo.md("### Result - Clean DataFrame:"),
        mo.ui.table(
            extract_tables("""
| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | New York |
| Bob   | 25  | London   |
""")[0],
            selection=None,
        ),
        mo.callout(
            "✅ Table isolated and extracted as a clean pandas DataFrame - ready for analysis!",
            kind="success"
        ),

        mo.md("## More Examples"),

        mo.ui.tabs({
            "Full API": mo.vstack([
                mo.md("Returns metadata along with DataFrames:"),
                code_block('''from markdown_table_extractor import extract_markdown_tables

result = extract_markdown_tables(markdown_text)

for table in result:
    print(f"Caption: {table.caption}")
    print(f"Rows: {table.row_count}, Cols: {table.column_count}")
    print(table.dataframe)'''),
            ]),

            "Continuation Tables": mo.vstack([
                mo.md("Automatically merges tables marked as continuations:"),
                code_block('''markdown_text = """
Table 1. Results

| Name  | Score |
|-------|-------|
| Alice | 95    |
| Bob   | 87    |

Table 1 (Continued)

| Name  | Score |
|-------|-------|
| Carol | 92    |
| Dave  | 88    |
"""

result = extract_markdown_tables(markdown_text)
print(f"Tables: {len(result)}")  # 1 (auto-merged!)
print(f"Rows: {result[0].row_count}")  # 4'''),
            ]),

            "CLI": mo.vstack([
                mo.md("Command-line interface for quick extractions:"),
                code_block('''# Extract to console
mte extract document.md

# Extract to CSV
mte extract document.md -o output.csv

# Extract to JSON
mte extract document.md -o output.json''', "bash"),
            ]),
        }, lazy=True),

        mo.callout(
            mo.md("**Next:** Explore the Modules tab to see how each component works!"),
            kind="success"
        ),
    ])
    return (quickstart_content,)


@app.cell
def _(mo, module_card):
    # Modules documentation
    modules_content = mo.vstack([
        mo.md("# 📦 Module Documentation"),

        mo.callout(
            mo.md("""
            Each module is an **interactive marimo notebook**. You can:
            - 📖 Read the documentation
            - 🔧 Modify and run the code
            - 🧪 Experiment with live examples
            """),
            kind="info"
        ),

        mo.md("## Core Modules"),

        mo.accordion({
            "🔍 Parser": module_card(
                "parser.py",
                "Detects and parses markdown table structures",
                [
                    "is_separator_row(line) - Detects separator rows",
                    "is_table_row(line) - Checks if line is a table row",
                    "parse_table_row(line) - Extracts cell contents",
                    "detect_caption(lines, start) - Finds table captions",
                ],
                "uv run marimo edit src/markdown_table_extractor/core/parser.py"
            ),

            "🧹 Cleaner": module_card(
                "cleaner.py",
                "Cleans column names and cell values",
                [
                    "clean_column_name(name) - Removes HTML, normalizes whitespace",
                    "clean_value(value) - Cleans cell content",
                    "headers_match(h1, h2) - Fuzzy header comparison",
                    "normalize_headers(headers) - Prepares headers for comparison",
                ],
                "uv run marimo edit src/markdown_table_extractor/core/cleaner.py"
            ),

            "🔗 Merger": module_card(
                "merger.py",
                "Merges continuation tables intelligently",
                [
                    "is_continuation_table(table) - Detects continuation markers",
                    "should_merge_tables(t1, t2) - Determines merge eligibility",
                    "merge_tables(tables, strategy) - Merges all continuations",
                ],
                "uv run marimo edit src/markdown_table_extractor/core/merger.py"
            ),

            "⚙️ Extractor": module_card(
                "extractor.py",
                "Main orchestration - ties everything together",
                [
                    "extract_tables(text) - Simple API returning DataFrames",
                    "extract_markdown_tables(text) - Full API with metadata",
                    "extract_single_table(lines, start) - Extract one table",
                ],
                "uv run marimo edit src/markdown_table_extractor/core/extractor.py"
            ),

            "📋 Models": module_card(
                "models.py",
                "Data classes and enums",
                [
                    "ExtractedTable - Single table with metadata",
                    "ExtractionResult - Collection of tables",
                    "TableMergeStrategy - Enum for merge behavior",
                ],
                "uv run marimo edit src/markdown_table_extractor/core/models.py"
            ),
        }, lazy=True),

        mo.md("""
        ## Module Dependencies

        ```mermaid
        graph TD
            A[models.py] --> B[parser.py]
            B --> C[cleaner.py]
            C --> D[merger.py]
            D --> E[extractor.py]
            A --> E
        ```

        Each module can be used independently or as part of the full pipeline!
        """),
    ])
    return (modules_content,)


@app.cell
def _(code_block, extract_markdown_tables, extract_tables, mo):
    # Academic Paper Table Example
    _academic_table = """
# Clinical Trial Results

This study examined the efficacy of a new treatment protocol across two patient groups.
Baseline demographic characteristics were collected for all participants to ensure
comparable populations.

**Table 1. Patient Demographics**

| Variable | Group A<br>n=50 | Group B<br>n=45 |
|----------|-----------------|-----------------|
| Age (years) | 45.2 ± 3.1 | 47.8 ± 2.9 |
| Male/Female | 28/22 | 25/20 |

The groups showed no significant differences in baseline characteristics (p > 0.05).
Statistical analysis was performed using two-tailed t-tests with α = 0.05.
"""

    _academic_result = extract_markdown_tables(_academic_table)

    # Multi-page Table Example
    _continued_tables = """
# Longitudinal Study Results

We conducted a 6-month study tracking participant outcomes across multiple time points.
The following table presents the complete dataset, which spans multiple pages in the
original manuscript.

Table 2. Results Summary

| ID | Name  | Score |
|----|-------|-------|
| 1  | Alice | 95    |
| 2  | Bob   | 87    |

The table continues on the next page with additional participants.

Table 2 (Continued)

| ID | Name  | Score |
|----|-------|-------|
| 3  | Carol | 92    |
| 4  | Dave  | 88    |

All participants completed the study protocol without adverse events.
"""

    _continued_result = extract_markdown_tables(_continued_tables)

    # Complex Alignment Example
    _aligned_table = """
# Data Formatting Guide

Tables can use different alignment markers for left, center, and right alignment.
This example demonstrates all three:

| Left | Center | Right |
|:-----|:------:|------:|
| L1   | C1     | R1    |
| L2   | C2     | R2    |

Alignment markers (`:---`, `:---:`, `---:`) are detected and handled correctly.
"""

    _aligned_result = extract_tables(_aligned_table)

    # Examples content
    examples_content = mo.vstack([
        mo.md("# 💡 Live Examples"),

        mo.accordion({
            "📄 Academic Paper Tables": mo.vstack([
                mo.md("""
                **Scenario:** Extracting a patient demographics table from a clinical trial manuscript
                that contains HTML artifacts from PDF conversion.
                """),
                mo.md("### Input Document (rendered):"),
                mo.md(_academic_table),
                mo.md("---"),
                mo.md("### Extracted Table:"),
                mo.ui.table(_academic_result[0].dataframe, selection=None),
                mo.callout(
                    f"✅ Caption detected: {_academic_result[0].caption} | HTML tags cleaned automatically!",
                    kind="success"
                ),
            ]),

            "📑 Multi-page Tables": mo.vstack([
                mo.md("""
                **Scenario:** Extracting a dataset that spans multiple pages in a manuscript,
                with a continuation marker on the second page.
                """),
                mo.md("### Input Document (rendered):"),
                mo.md(_continued_tables),
                mo.md("---"),
                mo.md("### Merged Result:"),
                mo.ui.table(_continued_result[0].dataframe, selection=None),
                mo.callout(
                    f"✅ Auto-merged {_continued_result.merged_count} continuation table → {_continued_result[0].row_count} total rows",
                    kind="success"
                ),
            ]),

            "⬅️➡️ Complex Alignment": mo.vstack([
                mo.md("""
                **Scenario:** Parsing a table with mixed alignment markers (left, center, right)
                from a formatting guide.
                """),
                mo.md("### Input Document (rendered):"),
                mo.md(_aligned_table),
                mo.md("---"),
                mo.md("### Extracted Table:"),
                mo.ui.table(_aligned_result[0], selection=None),
                mo.callout(
                    "✅ Alignment markers (:---, :---:, ---:) correctly detected!",
                    kind="success"
                ),
            ]),

            "💾 Export Formats": mo.vstack([
                mo.md("Export to various formats using pandas:"),
                code_block('''result = extract_markdown_tables(markdown_text)

    # CSV
    result[0].dataframe.to_csv('output.csv', index=False)

    # JSON
    result[0].dataframe.to_json('output.json', orient='records')

    # Excel
    result[0].dataframe.to_excel('output.xlsx', index=False)

    # Markdown
    print(result[0].dataframe.to_markdown(index=False))'''),
            ]),

            "⚙️ Custom Merge Strategies": mo.vstack([
                mo.md("Control how continuation tables are merged:"),
                code_block('''from markdown_table_extractor.core.models import TableMergeStrategy

    # Don't merge any tables
    result = extract_markdown_tables(
    text,
    merge_strategy=TableMergeStrategy.NONE
    )

    # Merge tables with identical headers (default)
    result = extract_markdown_tables(
    text,
    merge_strategy=TableMergeStrategy.IDENTICAL_HEADERS
    )

    # Merge tables with compatible column counts (±2)
    result = extract_markdown_tables(
    text,
    merge_strategy=TableMergeStrategy.COMPATIBLE_COLUMNS
    )'''),
            ]),
        }, lazy=True, multiple=True),
    ])
    return (examples_content,)


@app.cell
def _(mo):
    # API Reference content
    api_content = mo.vstack([
        mo.md("# 📖 API Reference"),

        mo.ui.tabs({
            "Main Functions": mo.accordion({
                "extract_tables()": mo.md("""
                ```python
                extract_tables(text: str) -> list[pd.DataFrame]
                ```

                **Simple API**: Extract tables and return DataFrames only.

                **Parameters:**
                - `text` (str): Markdown document text

                **Returns:**
                - `list[pd.DataFrame]`: List of extracted tables

                **Example:**
                ```python
                from markdown_table_extractor import extract_tables
                tables = extract_tables(markdown_text)
                ```
                """),

                "extract_markdown_tables()": mo.md("""
                ```python
                extract_markdown_tables(
                    text: str,
                    merge_strategy: TableMergeStrategy = IDENTICAL_HEADERS,
                    detect_captions: bool = True,
                    skip_sub_headers: bool = True
                ) -> ExtractionResult
                ```

                **Full API**: Extract tables with complete metadata.

                **Parameters:**
                - `text` (str): Markdown document text
                - `merge_strategy`: How to handle continuations
                  - `NONE`: Don't merge
                  - `IDENTICAL_HEADERS`: Merge if headers match (default)
                  - `COMPATIBLE_COLUMNS`: Merge if column counts ±2
                - `detect_captions` (bool): Look for table captions
                - `skip_sub_headers` (bool): Merge sub-header rows

                **Returns:**
                - `ExtractionResult`: Tables, errors, and merge info
                """),
            }, lazy=True),

            "Data Classes": mo.accordion({
                "ExtractedTable": mo.md("""
                A single extracted table with metadata.

                **Attributes:**
                - `dataframe` (pd.DataFrame): The table data
                - `caption` (str | None): Detected caption
                - `start_line` (int): Starting line number
                - `end_line` (int): Ending line number
                - `raw_markdown` (str): Original markdown
                - `is_continuation` (bool): Continuation marker

                **Properties:**
                - `column_count` (int): Number of columns
                - `row_count` (int): Number of rows
                """),

                "ExtractionResult": mo.md("""
                Complete extraction result with iteration support.

                **Attributes:**
                - `tables` (list[ExtractedTable]): Extracted tables
                - `errors` (list[str]): Encountered errors
                - `merged_count` (int): Number of merged tables

                **Methods:**
                - `get_dataframes()` → `list[pd.DataFrame]`

                **Properties:**
                - `has_errors` (bool): True if errors occurred

                **Supports:**
                - Iteration: `for table in result: ...`
                - Indexing: `result[0]`
                - Length: `len(result)`
                """),

                "TableMergeStrategy": mo.md("""
                Strategy for merging adjacent tables (Enum).

                **Values:**
                - `NONE`: Don't merge any tables
                - `IDENTICAL_HEADERS`: Merge identical/similar headers
                - `COMPATIBLE_COLUMNS`: Merge if columns within ±2
                """),
            }, lazy=True),

            "Parser": mo.md("""
            **Core parsing functions:**

            - `is_separator_row(line: str) -> bool`
              - Detects separators: `| --- |`, `| :--: |`, etc.

            - `is_table_row(line: str) -> bool`
              - Checks if line starts/ends with `|`

            - `parse_table_row(line: str) -> list[str]`
              - Extracts cell contents from a row

            - `detect_caption(...) -> tuple`
              - Finds captions like "Table 3. Results"
              - Returns: `(caption, is_continuation, table_number, is_bare)`
            """),

            "Cleaner": mo.md("""
            **Data cleaning functions:**

            - `clean_column_name(name: str) -> str`
              - Removes HTML tags, normalizes whitespace

            - `clean_value(value: str) -> str`
              - Cleans cell values, replaces entities

            - `headers_match(h1, h2, threshold=0.8) -> bool`
              - Fuzzy header comparison for merging

            - `normalize_headers(headers) -> list[str]`
              - Prepares headers for comparison
            """),

            "Merger": mo.md("""
            **Table merging functions:**

            - `merge_tables(tables, strategy) -> list`
              - Merges continuation tables by strategy

            - `should_merge_tables(t1, t2, strategy) -> bool`
              - Determines if two tables should merge

            - `is_continuation_table(table) -> bool`
              - Detects "(Continued)" or similar markers
            """),

            "CLI": mo.md("""
            **Command-line interface:**

            ```bash
            # Extract to stdout
            mte extract input.md

            # Extract to CSV
            mte extract input.md -o output.csv

            # Extract to JSON
            mte extract input.md -o output.json

            # Show help
            mte --help
            ```
            """),
        }, lazy=True),
    ])
    return (api_content,)


@app.cell
def _(
    api_content,
    examples_content,
    home_content,
    mo,
    modules_content,
    quickstart_content,
):
    # Define route handlers for each page
    def render_home():
        return home_content

    def render_quick_start():
        return quickstart_content

    def render_modules():
        return modules_content

    def render_examples():
        return examples_content

    def render_api():
        return api_content

    # Create navigation menu (keys=hrefs, values=labels)
    _nav = mo.nav_menu(
        {
            "#/": f"{mo.icon('lucide:home')} Home",
            "#/quick-start": f"{mo.icon('lucide:zap')} Quick Start",
            "#/modules": f"{mo.icon('lucide:package')} Modules",
            "#/examples": f"{mo.icon('lucide:code')} Examples",
            "#/api": f"{mo.icon('lucide:book-open')} API",
        },
        orientation="horizontal",
    )

    # Set up routes with hash-based navigation
    _routes = mo.routes({
        "#/": render_home,
        "#/quick-start": render_quick_start,
        "#/modules": render_modules,
        "#/examples": render_examples,
        "#/api": render_api,
        mo.routes.CATCH_ALL: render_home,
    })

    # Create and display the final layout
    _layout = mo.vstack([
        mo.md("# 📊 Markdown Table Extractor Documentation"),
        mo.Html("<hr style='margin: 1rem 0; border: none; border-top: 2px solid #e0e0e0;'>"),
        _nav,
        mo.Html("<div style='margin: 2rem 0;'></div>"),
        _routes,
    ])

    # Display the layout by having it as the last expression
    _layout
    return


if __name__ == "__main__":
    app.run()
