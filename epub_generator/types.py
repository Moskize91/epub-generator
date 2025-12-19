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
class BasicAsset:
    """Asset as a base class for other assets."""

    title: list["str | Mark | Formula | HTMLTag"] = field(default_factory=list, kw_only=True)
    """Asset title (before content)"""
    caption: list["str | Mark | Formula | HTMLTag"] = field(default_factory=list, kw_only=True)
    """Asset caption (after content)"""

@dataclass
class Table(BasicAsset):
    """Table representation."""

    html_content: "HTMLTag"
    """HTML content of the table"""


@dataclass
class Formula(BasicAsset):
    """Mathematical formula."""

    latex_expression: str
    """LaTeX expression"""


@dataclass
class Image(BasicAsset):
    """Image reference."""

    path: Path
    """Absolute path to the image file"""

@dataclass
class TextBlock:
    """Text block representation."""

    kind: TextKind
    """Kind of text block."""
    level: int
    """Heading level starting from 0 (only for HEADLINE: level 0 → h1, level 1 → h2, max h6; ignored for BODY and QUOTE)."""
    content: list["str | Mark | Formula | HTMLTag"]
    """Text content with optional citation marks."""

@dataclass
class Footnote:
    """Footnote/citation section."""
    id: int
    """Footnote ID"""

    has_mark: bool = True
    """Whether this footnote contains a mark indicator (defaults to True)"""

    contents: "list[ContentBlock]" = field(default_factory=list)
    """Content blocks"""


ContentBlock = TextBlock | Table | Formula | Image
"""Union of all content blocks that appear in main chapter content."""

@dataclass
class Chapter:
    """Complete content of a single chapter."""
    elements: list[ContentBlock] = field(default_factory=list)
    """Main content blocks"""

    footnotes: list[Footnote] = field(default_factory=list)
    """Footnotes"""

ChapterGetter = Callable[[], Chapter]

@dataclass
class HTMLTag:
    """Generic HTML tag representation."""

    name: str
    """Tag name"""

    attributes: list[tuple[str, str]] = field(default_factory=list)
    """List of (attribute, value) pairs"""

    content: list["str | Mark | Formula | HTMLTag"] = field(default_factory=list)
    """Inner HTML content"""