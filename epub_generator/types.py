from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable


@dataclass
class EpubData:
    """Complete EPUB book data structure."""

    meta: "BookMeta | None" = None
    """Book metadata (optional)"""

    get_head: "ChapterGetter | None" = None
    """Lazy getter for head chapter without TOC entry (optional)"""

    prefaces: "list[TocItem]" = field(default_factory=list)
    """Preface chapters (optional)"""

    chapters: "list[TocItem]" = field(default_factory=list)
    """Main chapters"""

    cover_image_path: Path | None = None
    """Cover image file path (optional, absolute path)"""

@dataclass
class BookMeta:
    """Book metadata information."""

    title: str | None = None
    """Book title (optional)"""

    description: str | None = None
    """Book description (optional)"""

    publisher: str | None = None
    """Publisher name (optional)"""

    isbn: str | None = None
    """ISBN (optional)"""

    authors: list[str] = field(default_factory=list)
    """Authors (optional)"""

    editors: list[str] = field(default_factory=list)
    """Editors (optional)"""

    translators: list[str] = field(default_factory=list)
    """Translators (optional)"""

    modified: datetime | None = None
    """Last modification timestamp for EPUB 3.0 dcterms:modified (optional, defaults to current time)"""


# ============================================================================
# Table of Contents structure
# ============================================================================

@dataclass
class TocItem:
    """Table of contents item with title, content, and optional nested children."""
    title: str
    """Chapter title displayed in table of contents"""

    get_chapter: "ChapterGetter | None" = None
    """Lazy getter for chapter content (optional for navigation-only entries)"""

    children: "list[TocItem]" = field(default_factory=list)
    """Nested sub-chapters (recursive, optional)"""

class TextKind(Enum):
    BODY = "body"
    """Regular paragraph."""
    HEADLINE = "headline"
    """Chapter heading."""
    QUOTE = "quote"
    """Quoted text."""

@dataclass
class Mark:
    """Citation reference marker."""
    id: int
    """Citation ID, matches Footnote.id"""

@dataclass
class Text:
    kind: TextKind
    """Kind of text block."""
    content: list[str | Mark]
    """Text content with optional citation marks."""
    
@dataclass
class Table:
    """HTML table."""
    html_content: str
    """HTML table markup"""


@dataclass
class Formula:
    """Mathematical formula."""
    latex_expression: str
    """LaTeX expression"""


@dataclass
class Image:
    """Image reference."""
    path: Path
    """Absolute path to the image file"""

    alt_text: str = "image"
    """Alt text (defaults to "image")"""


@dataclass
class Footnote:
    """Footnote/citation section."""
    id: int
    """Footnote ID"""

    has_mark: bool = True
    """Whether this footnote contains a mark indicator (defaults to True)"""

    contents: "list[ContentBlock]" = field(default_factory=list)
    """Content blocks"""


ContentBlock = Text | Table | Formula | Image
"""Union of all content blocks that appear in main chapter content."""

@dataclass
class Chapter:
    """Complete content of a single chapter."""
    elements: list[ContentBlock] = field(default_factory=list)
    """Main content blocks"""

    footnotes: list[Footnote] = field(default_factory=list)
    """Footnotes"""

ChapterGetter = Callable[[], Chapter]