<div align="center">
  <h1>EPUB Generator</h1>
  <p>A simple Python EPUB 3.0 generator with a single API call.</p>
  <p>
    <a href="https://github.com/moskize91/epub-generator/actions/workflows/build.yml" target="_blank"><img src="https://img.shields.io/github/actions/workflow/status/moskize91/epub-generator/build.yml" alt="ci" /></a>
    <a href="https://pypi.org/project/epub-generator/" target="_blank"><img src="https://img.shields.io/badge/pip_install-epub--generator-blue" alt="pip install epub-generator" /></a>
    <a href="https://pypi.org/project/epub-generator/" target="_blank"><img src="https://img.shields.io/pypi/v/epub-generator.svg" alt="pypi epub-generator" /></a>
    <a href="https://pypi.org/project/epub-generator/" target="_blank"><img src="https://img.shields.io/pypi/pyversions/epub-generator.svg" alt="python versions" /></a>
    <a href="https://github.com/moskize91/epub-generator/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/moskize91/epub-generator" alt="license" /></a>
  </p>
</div>

## Quick Start

### Installation

```bash
pip install epub-generator
```

### Generate Your First Book in 5 Minutes

```python
from epub_generator import generate_epub, EpubData, BookMeta, TocItem, Chapter, TextBlock, TextKind

# Prepare book data
epub_data = EpubData(
    meta=BookMeta(
        title="My First Book",
        authors=["John Doe"],
    ),
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.HEADLINE, level=0, content=["Chapter 1"]),
                    TextBlock(kind=TextKind.BODY, level=0, content=["This is the first paragraph."]),
                    TextBlock(kind=TextKind.BODY, level=0, content=["This is the second paragraph."]),
                ]
            ),
        ),
    ],
)

# Generate EPUB file
generate_epub(epub_data, "my_book.epub")
```

That's it! You now have a valid EPUB 3.0 ebook file.

## Features

- **Minimal API**: Just one function call `generate_epub()`
- **EPUB 3.0**: Generates standards-compliant EPUB 3.0 format
- **Rich Content**: Supports text, images, tables, math formulas (block-level and inline), footnotes, custom HTML tags
- **Flexible Structure**: Nested chapters, prefaces, cover images
- **Math Support**: LaTeX to MathML/SVG conversion with inline formula support
- **Type Safe**: Full type annotations included

## Advanced Usage

### Add Cover and Complete Metadata

```python
from datetime import datetime, timezone
from pathlib import Path
from epub_generator import generate_epub, EpubData, BookMeta, TocItem, Chapter, TextBlock, TextKind

epub_data = EpubData(
    meta=BookMeta(
        title="Complete Example",
        description="A book with full metadata",
        publisher="Example Publisher",
        isbn="978-0-123456-78-9",
        authors=["Author One", "Author Two"],
        editors=["Editor"],
        translators=["Translator"],
        modified=datetime.now(timezone.utc),
    ),
    cover_image_path=Path("cover.png"),  # Cover image
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.HEADLINE, level=0, content=["Chapter 1"]),
                    TextBlock(kind=TextKind.BODY, level=0, content=["Main content..."]),
                ]
            ),
        ),
    ],
)

generate_epub(epub_data, "book_with_cover.epub")
```

### Nested Chapter Structure

```python
from epub_generator import generate_epub, EpubData, TocItem, Chapter, TextBlock, TextKind

epub_data = EpubData(
    chapters=[
        TocItem(
            title="Part 1",
            children=[  # Nested sub-chapters
                TocItem(
                    title="Chapter 1.1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            TextBlock(kind=TextKind.BODY, level=0, content=["Content 1.1..."]),
                        ]
                    ),
                ),
                TocItem(
                    title="Chapter 1.2",
                    get_chapter=lambda: Chapter(
                        elements=[
                            TextBlock(kind=TextKind.BODY, level=0, content=["Content 1.2..."]),
                        ]
                    ),
                ),
            ],
        ),
    ],
)

generate_epub(epub_data, "book_with_nested_chapters.epub")
```

### Add Images

```python
from pathlib import Path
from epub_generator import generate_epub, EpubData, TocItem, Chapter, TextBlock, TextKind, Image

epub_data = EpubData(
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.BODY, level=0, content=["Here's an image:"]),
                    Image(
                        path=Path("image.png"),  # Image path
                        alt_text="Image description",
                    ),
                ]
            ),
        ),
    ],
)

generate_epub(epub_data, "book_with_images.epub")
```

### Add Footnotes

```python
from epub_generator import generate_epub, EpubData, TocItem, Chapter, TextBlock, TextKind, Mark, Footnote

epub_data = EpubData(
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(
                        kind=TextKind.BODY,
                        level=0,
                        content=[
                            "This is text with a footnote",
                            Mark(id=1),  # Footnote marker
                            ".",
                        ],
                    ),
                ],
                footnotes=[
                    Footnote(
                        id=1,
                        contents=[
                            TextBlock(kind=TextKind.BODY, level=0, content=["This is the footnote content."]),
                        ],
                    ),
                ],
            ),
        ),
    ],
)

generate_epub(epub_data, "book_with_footnotes.epub")
```

### Add Tables

```python
from epub_generator import generate_epub, EpubData, TocItem, Chapter, TextBlock, TextKind, Table

epub_data = EpubData(
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.BODY, level=0, content=["Here's a table:"]),
                    Table(
                        html_content="""
                        <table>
                            <tr><th>Name</th><th>Age</th></tr>
                            <tr><td>Alice</td><td>25</td></tr>
                            <tr><td>Bob</td><td>30</td></tr>
                        </table>
                        """
                    ),
                ]
            ),
        ),
    ],
)

generate_epub(epub_data, "book_with_tables.epub")
```

### Add Math Formulas

Block-level formulas:

```python
from epub_generator import generate_epub, EpubData, TocItem, Chapter, TextBlock, TextKind, Formula, LaTeXRender

epub_data = EpubData(
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.BODY, level=0, content=["Pythagorean theorem:"]),
                    Formula(latex_expression="x^2 + y^2 = z^2"),  # Block-level formula
                ]
            ),
        ),
    ],
)

# Render math formulas using MathML
generate_epub(epub_data, "book_with_math.epub", latex_render=LaTeXRender.MATHML)
```

Inline formulas embedded in text:

```python
epub_data = EpubData(
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(
                        kind=TextKind.BODY,
                        level=0,
                        content=[
                            "The Pythagorean theorem ",
                            Formula(latex_expression="a^2 + b^2 = c^2"),  # Inline formula
                            " is fundamental. Einstein's equation ",
                            Formula(latex_expression="E = mc^2"),
                            " shows mass-energy equivalence.",
                        ],
                    ),
                ]
            ),
        ),
    ],
)

generate_epub(epub_data, "book_with_inline_math.epub", latex_render=LaTeXRender.MATHML)
```

### Add Custom HTML Tags

You can embed custom HTML tags within text content:

```python
from epub_generator import generate_epub, EpubData, TocItem, Chapter, TextBlock, TextKind, HTMLTag

epub_data = EpubData(
    chapters=[
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(elements=[TextBlock(
                kind=TextKind.BODY,
                level=0,
                content=[
                    "This is normal text with ",
                    HTMLTag(
                        name="span",
                        attributes=[("class", "highlight"), ("style", "color: red;")],
                        content=["highlighted content"],
                    ),
                    " and more text with ",
                    HTMLTag(
                        name="strong",
                        content=["bold text"],
                    ),
                    ".",
                ],
            )]),
        ),
    ],
)

generate_epub(epub_data, "book_with_html_tags.epub")
```

### Add Prefaces

```python
from epub_generator import generate_epub, EpubData, BookMeta, TocItem, Chapter, TextBlock, TextKind

epub_data = EpubData(
    meta=BookMeta(title="Book with Prefaces"),
    prefaces=[  # Preface chapters
        TocItem(
            title="Preface",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.HEADLINE, level=0, content=["Preface"]),
                    TextBlock(kind=TextKind.BODY, level=0, content=["This is the preface content..."]),
                ]
            ),
        ),
    ],
    chapters=[  # Main chapters
        TocItem(
            title="Chapter 1",
            get_chapter=lambda: Chapter(
                elements=[
                    TextBlock(kind=TextKind.BODY, level=0, content=["Main content..."]),
                ]
            ),
        ),
    ],
)

generate_epub(epub_data, "book_with_prefaces.epub")
```

## API Reference

### Core Function

#### `generate_epub()`

```python
def generate_epub(
    epub_data: EpubData,
    epub_file_path: PathLike,
    lan: Literal["zh", "en"] = "zh",
    table_render: TableRender = TableRender.HTML,
    latex_render: LaTeXRender = LaTeXRender.MATHML,
) -> None:
```

**Parameters:**
- `epub_data`: Complete ebook data
- `epub_file_path`: Output file path
- `lan`: Language (`"zh"` or `"en"`, defaults to `"zh"`)
- `table_render`: Table rendering mode (defaults to `TableRender.HTML`)
- `latex_render`: Math formula rendering mode (defaults to `LaTeXRender.MATHML`)

### Data Types

#### `EpubData`

Complete EPUB book data structure.

```python
@dataclass
class EpubData:
    meta: BookMeta | None = None                # Book metadata
    get_head: ChapterGetter | None = None       # Head chapter without TOC entry
    prefaces: list[TocItem] = []                # Preface chapters
    chapters: list[TocItem] = []                # Main chapters
    cover_image_path: Path | None = None        # Cover image path
```

#### `BookMeta`

Book metadata information.

```python
@dataclass
class BookMeta:
    title: str | None = None                    # Book title
    description: str | None = None              # Description
    publisher: str | None = None                # Publisher
    isbn: str | None = None                     # ISBN
    authors: list[str] = []                     # Authors list
    editors: list[str] = []                     # Editors list
    translators: list[str] = []                 # Translators list
    modified: datetime | None = None            # Modification timestamp
```

#### `TocItem`

Table of contents item with title, content, and optional nested children.

```python
@dataclass
class TocItem:
    title: str                                  # Chapter title
    get_chapter: ChapterGetter | None = None    # Chapter content getter
    children: list[TocItem] = []                # Nested sub-chapters
```

#### `Chapter`

Complete content of a single chapter.

```python
@dataclass
class Chapter:
    elements: list[ContentBlock] = []           # Main content blocks
    footnotes: list[Footnote] = []              # Footnotes
```

#### Content Block Types

`ContentBlock` is a union of:

- **`TextBlock`**: Text paragraph
  ```python
  @dataclass
  class TextBlock:
      kind: TextKind                                # BODY | HEADLINE | QUOTE
      level: int                                    # Heading level (0→h1, 1→h2, max h6; only for HEADLINE)
      content: list[str | Mark | Formula | HTMLTag] # Text with optional marks, inline formulas, and HTML tags
  ```

- **`Image`**: Image reference
  ```python
  @dataclass
  class Image:
      path: Path                                # Image file path (absolute)
      alt_text: str = "image"                   # Alt text
  ```

- **`Table`**: HTML table
  ```python
  @dataclass
  class Table:
      html_content: str                         # HTML table markup
  ```

- **`Formula`**: Mathematical formula
  ```python
  @dataclass
  class Formula:
      latex_expression: str                     # LaTeX expression
  ```

- **`HTMLTag`**: HTML tag
  ```python
  @dataclass
  class HTMLTag:
      name: str                                 # Tag name (e.g., "span", "div")
      attributes: list[tuple[str, str]] = []    # List of (attribute, value) pairs
      content: list[str | Mark | Formula | HTMLTag] = [] # Inner HTML content
  ```

#### `Footnote`

Footnote/citation.

```python
@dataclass
class Footnote:
    id: int                                     # Footnote ID
    has_mark: bool = True                       # Whether contains mark indicator
    contents: list[ContentBlock] = []           # Content blocks
```

#### `Mark`

Footnote reference marker.

```python
@dataclass
class Mark:
    id: int                                     # Reference ID, matches Footnote.id
```

### Configuration Options

#### `TextKind`

Text type enumeration.

```python
class TextKind(Enum):
    BODY = "body"                               # Regular paragraph
    HEADLINE = "headline"                       # Chapter heading
    QUOTE = "quote"                             # Quoted text
```

#### `TableRender`

Table rendering mode.

```python
class TableRender(Enum):
    HTML = "html"                               # HTML rendering
```

#### `LaTeXRender`

Math formula rendering mode.

```python
class LaTeXRender(Enum):
    MATHML = "mathml"                           # MathML rendering
```

## Development

### Install Development Dependencies

```bash
poetry install
```

### Run Tests

```bash
python -m pytest tests/
```

Requires [epubcheck](https://github.com/w3c/epubcheck) to validate generated EPUB files.

## License

MIT License

## Author

Tao Zeyu <i@taozeyu.com>
