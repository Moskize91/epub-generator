"""
Data structures for EPUB generation.

This module defines dataclasses that represent the complete structure
of an EPUB book, providing an alternative to the folder-based input format.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ============================================================================
# Top-level EPUB Data Structure
# ============================================================================

@dataclass
class EpubData:
    """
    Complete EPUB book data structure.

    This is the top-level data structure that replaces the entire
    input folder structure. Pass this to the generation function
    instead of a folder path.

    Origin mapping:
    - Replaces the entire input folder structure
    - Combines meta.json, index.json, cover.png, and chapter files

    Fields origin:
    - meta: from meta.json
    - get_head: lazy getter for chapters/chapter.xml (head chapter without TOC entry)
    - prefaces: from index.json["prefaces"] (combined with chapter file getters)
    - chapters: from index.json["chapters"] (combined with chapter file getters)
    - cover_image_path: from cover.png

    Constraints:
    - Each Image.path should be an absolute path to the image file
    - Each Mark.id should match a Footnote.id
    - At least one chapter with content should exist
    """
    meta: "BookMeta | None" = None
    """Book metadata from meta.json (optional)"""

    get_head: "ChapterGetter | None" = None
    """Lazy getter for head chapter from chapters/chapter.xml (optional)"""

    prefaces: "list[TocItem]" = field(default_factory=list)
    """Preface chapters from index.json["prefaces"] + chapter files (optional)"""

    chapters: "list[TocItem]" = field(default_factory=list)
    """Main chapters from index.json["chapters"] + chapter files"""

    cover_image_path: Path | None = None
    """Cover image file path from cover.png (optional, absolute path)"""


# ============================================================================
# Book Metadata
# ============================================================================

@dataclass
class BookMeta:
    """
    Book metadata information.

    Origin: meta.json file

    All fields are optional. Missing fields will use defaults or be omitted
    from the EPUB metadata.

    Original structure:
    {
      "title": "string",
      "description": "string",
      "publisher": "string",
      "ISBN": "string",
      "authors": ["string", ...],
      "editors": ["string", ...],
      "translators": ["string", ...]
    }
    """
    title: str | None = None
    """Book title (optional, defaults to "Unnamed")"""

    description: str | None = None
    """Book description (optional)"""

    publisher: str | None = None
    """Publisher name (optional)"""

    isbn: str | None = None
    """ISBN (optional, defaults to generated UUID)"""

    authors: list[str] = field(default_factory=list)
    """List of authors (optional)"""

    editors: list[str] = field(default_factory=list)
    """List of editors (optional)"""

    translators: list[str] = field(default_factory=list)
    """List of translators (optional)"""

    def to_dict(self) -> dict:
        """Convert BookMeta to dictionary format used in templates.

        Returns:
            Dictionary with keys: title, description, publisher, ISBN,
            authors, editors, translators
        """
        return {
            "title": self.title,
            "description": self.description,
            "publisher": self.publisher,
            "ISBN": self.isbn,
            "authors": self.authors,
            "editors": self.editors,
            "translators": self.translators,
        }


# ============================================================================
# Table of Contents structure
# ============================================================================

@dataclass
class TocItem:
    """
    A table of contents item with title, content, and optional nested children.

    Origin: Combines index.json entries with chapter files
    - title: from "headline" field
    - get_chapter: lazy getter for chapter file content
    - children: from "children" array (recursive)

    Original structure in index.json:
    {
      "id": integer,           // Used to map to chapter file, removed in dataclass
      "headline": "string",    // Mapped to TocItem.title
      "children": [...]        // Mapped to TocItem.children (recursive)
    }

    The id field is removed because we now use lazy getters for Chapter objects
    instead of referencing them via id mapping.

    A TocItem without get_chapter but with children serves as a section heading.

    Note: Using getter functions enables lazy loading - chapters are only loaded
    from disk when accessed, reducing memory usage for large books.
    """
    title: str
    """Chapter title displayed in table of contents"""

    get_chapter: "ChapterGetter | None" = None
    """Lazy getter for chapter content (optional for navigation-only entries)"""

    children: "list[TocItem]" = field(default_factory=list)
    """Nested sub-chapters (recursive, optional)"""


# ============================================================================
# Chapter Content Blocks
# ============================================================================

@dataclass
class Headline:
    """
    Chapter heading.

    Origin: <headline> tag
    Example: <headline>Chapter Title<mark id="1"/></headline>

    Renders as <h1> in HTML.
    """
    text: str
    """Text content"""

    marks: "list[Mark]" = field(default_factory=list)
    """Citation markers (optional)"""


@dataclass
class Text:
    """
    Regular paragraph.

    Origin: <text> tag
    Example: <text>Paragraph content<mark id="1"/></text>

    Renders as <p> in HTML.
    """
    text: str
    """Text content"""

    marks: "list[Mark]" = field(default_factory=list)
    """Citation markers (optional)"""


@dataclass
class Quote:
    """
    Quoted text.

    Origin: <quote> tag
    Example: <quote>Quoted text<mark id="1"/></quote>

    Renders as <blockquote><p> in HTML.
    """
    text: str
    """Text content"""

    marks: "list[Mark]" = field(default_factory=list)
    """Citation markers (optional)"""


@dataclass
class Table:
    """
    HTML table.

    Origin: <table> tag with nested <html> child
    Example:
    <table>
      <html>
        <table>
          <tr><td>...</td></tr>
        </table>
      </html>
    </table>

    Contains complete HTML table markup as a string.
    Rendering behavior depends on the table_render parameter.
    """
    html_content: str
    """HTML table markup"""


@dataclass
class Formula:
    """
    Mathematical formula.

    Origin: <formula> tag
    Example: <formula>E = mc^2</formula>

    Contains LaTeX expression as a string.
    Rendering behavior depends on the latex_render parameter:
    - MATHML: converts to MathML
    - SVG: renders to SVG image
    - CLIPPING: skipped
    """
    latex_expression: str
    """LaTeX expression"""


@dataclass
class Image:
    """
    Image reference.

    Origin: <image> tag
    Example: <image hash="abc123def456">Image description</image>

    In the original format, hash maps to assets/<hash>.png.
    In this dataclass, we use absolute path directly instead.
    """
    path: Path
    """Absolute path to the image file"""

    alt_text: str = "image"
    """Alt text (defaults to "image")"""


@dataclass
class Footnote:
    """
    Footnote/citation section.

    Origin: <footnote> tag
    Example:
    <footnote id="1">
      <mark/>
      <text>Footnote content</text>
    </footnote>

    Must contain a <mark/> indicator (without id) to show where the footnote
    reference appears in the rendered output. Can contain any content blocks
    except other footnotes.

    Creates bidirectional links with Marks in the main content:
    - Mark with id="N" links to Footnote with id="N"
    - Footnote creates a back-reference link to the Mark
    """
    id: int
    """Footnote ID"""

    has_mark: bool = True
    """Whether this footnote contains a <mark/> indicator (required, defaults to True)"""

    contents: "list[ContentBlock]" = field(default_factory=list)
    """Content blocks (excluding the <mark/> indicator)"""


@dataclass
class Mark:
    """
    Citation reference marker.

    Origin: <mark> tag
    Example: <mark id="1"/> (inline in text/quote/headline)

    Appears inline within text content to mark citation points.
    Links to a corresponding Footnote with the same id.
    Renders as a superscript link [N] in HTML.
    """
    id: int
    """Citation ID, matches Footnote.id"""


ContentBlock = Headline | Text | Quote | Table | Formula | Image
"""
Union of all content blocks that appear in main chapter content.
Note: Footnote is excluded as it's stored separately in Chapter.footnotes
"""


# ============================================================================
# Chapter Content
# ============================================================================

@dataclass
class Chapter:
    """
    Complete content of a single chapter.

    Origin: chapter files (chapter_<id>.xml or chapter.xml for head)

    Original structure:
    <chapter>
      <headline>...</headline>
      <text>...</text>
      <quote>...</quote>
      <table>...</table>
      <formula>...</formula>
      <image>...</image>
      <footnote>...</footnote>
    </chapter>

    Note: Footnotes are rendered separately at the bottom of the chapter
    with a "References" heading, not mixed with main content.
    """
    elements: list[ContentBlock] = field(default_factory=list)
    """Main content blocks (headline, text, quote, table, formula, image)"""

    footnotes: list[Footnote] = field(default_factory=list)
    """Footnotes rendered at bottom with "References" heading"""

ChapterGetter = Callable[[], Chapter]