from .types import (
    BasicAsset,
    Chapter,
    ContentBlock,
    EpubData,
    Footnote,
    Formula,
    HTMLTag,
    Image,
    Mark,
    Table,
    TextBlock,
    TocItem,
)


class InvalidUnicodeError(Exception):
    """Raised when invalid Unicode characters (surrogates) are detected in EPUB data."""

    def __init__(self, field_path: str, invalid_char_info: str):
        """Initialize with field path and character information.

        Args:
            field_path: Dot-separated path to the field containing invalid characters
            invalid_char_info: Information about the invalid character(s)
        """
        self.field_path = field_path
        self.invalid_char_info = invalid_char_info
        super().__init__(
            f"Invalid Unicode character detected in {field_path}: {invalid_char_info}"
        )


def validate_epub_data(epub_data: EpubData) -> None:
    """Validate an EpubData object for invalid Unicode characters.

    This function checks all string fields in the EPUB data structure including:
    - Book metadata (title, description, authors, etc.)
    - Table of contents titles (recursively)
    - Chapter content is NOT validated here (use validate_chapter separately)

    Args:
        epub_data: EPUB data to validate

    Raises:
        InvalidUnicodeError: If surrogate characters are detected in any string field
    """
    # Check metadata
    if epub_data.meta:
        meta = epub_data.meta
        _check_string(meta.title, "EpubData.meta.title")
        _check_string(meta.description, "EpubData.meta.description")
        _check_string(meta.publisher, "EpubData.meta.publisher")
        _check_string(meta.isbn, "EpubData.meta.isbn")

        for i, author in enumerate(meta.authors):
            _check_string(author, f"EpubData.meta.authors[{i}]")

        for i, editor in enumerate(meta.editors):
            _check_string(editor, f"EpubData.meta.editors[{i}]")

        for i, translator in enumerate(meta.translators):
            _check_string(translator, f"EpubData.meta.translators[{i}]")

    # Check prefaces TOC
    for i, preface in enumerate(epub_data.prefaces):
        _check_toc_item(preface, f"EpubData.prefaces[{i}]")

    # Check chapters TOC
    for i, chapter_toc in enumerate(epub_data.chapters):
        _check_toc_item(chapter_toc, f"EpubData.chapters[{i}]")


def validate_chapter(chapter: Chapter, context: str = "Chapter") -> None:
    """Validate a Chapter object for invalid Unicode characters.

    Args:
        chapter: Chapter to validate
        context: Context string for error reporting (e.g., "Chapter", "chapters[0]")

    Raises:
        InvalidUnicodeError: If surrogate characters are detected in any string field
    """
    # Check main content elements
    for i, element in enumerate(chapter.elements):
        _check_content_block(element, f"{context}.elements[{i}]")

    # Check footnotes
    for i, footnote in enumerate(chapter.footnotes):
        _check_footnote(footnote, f"{context}.footnotes[{i}]")


def _check_string(value: str | None, field_path: str) -> None:
    """Check if a string contains surrogate characters.

    Args:
        value: String to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    if value is None:
        return

    for i, char in enumerate(value):
        code_point = ord(char)
        # Check for surrogate pair range (U+D800 to U+DFFF)
        if 0xD800 <= code_point <= 0xDFFF:
            raise InvalidUnicodeError(
                field_path=field_path,
                invalid_char_info=f"surrogate character U+{code_point:04X} at position {i}",
            )


def _check_string_list(values: list[str | Mark | Formula | HTMLTag], field_path: str) -> None:
    """Recursively check a list that may contain strings, marks, formulas, or HTML tags.

    Args:
        values: List to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    for i, item in enumerate(values):
        item_path = f"{field_path}[{i}]"
        if isinstance(item, str):
            _check_string(item, item_path)
        elif isinstance(item, Mark):
            pass  # Mark only contains int ID
        elif isinstance(item, Formula):
            _check_string(item.latex_expression, f"{item_path}.latex_expression")
            _check_string_list(item.title, f"{item_path}.title")
            _check_string_list(item.caption, f"{item_path}.caption")
        elif isinstance(item, HTMLTag):
            _check_html_tag(item, item_path)


def _check_html_tag(tag: HTMLTag, field_path: str) -> None:
    """Check an HTML tag for invalid characters.

    Args:
        tag: HTML tag to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    _check_string(tag.name, f"{field_path}.name")

    for i, (attr_name, attr_value) in enumerate(tag.attributes):
        _check_string(attr_name, f"{field_path}.attributes[{i}][0]")
        _check_string(attr_value, f"{field_path}.attributes[{i}][1]")

    _check_string_list(tag.content, f"{field_path}.content")


def _check_basic_asset(asset: BasicAsset, field_path: str) -> None:
    """Check BasicAsset (and subclasses) for invalid characters.

    Args:
        asset: Asset to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    _check_string_list(asset.title, f"{field_path}.title")
    _check_string_list(asset.caption, f"{field_path}.caption")

    if isinstance(asset, Formula):
        _check_string(asset.latex_expression, f"{field_path}.latex_expression")
    elif isinstance(asset, Table):
        _check_html_tag(asset.html_content, f"{field_path}.html_content")
    elif isinstance(asset, Image):
        pass  # Image only contains Path, no string content to check


def _check_content_block(block: ContentBlock, field_path: str) -> None:
    """Check a content block for invalid characters.

    Args:
        block: Content block to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    if isinstance(block, TextBlock):
        _check_string_list(block.content, f"{field_path}.content")
    elif isinstance(block, (Table, Formula, Image)):
        _check_basic_asset(block, field_path)


def _check_footnote(footnote: Footnote, field_path: str) -> None:
    """Check a footnote for invalid characters.

    Args:
        footnote: Footnote to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    for i, content_block in enumerate(footnote.contents):
        _check_content_block(content_block, f"{field_path}.contents[{i}]")


def _check_toc_item(item: TocItem, field_path: str) -> None:
    """Recursively check a TOC item for invalid characters.

    Args:
        item: TOC item to check
        field_path: Path to the field for error reporting

    Raises:
        InvalidUnicodeError: If surrogate characters are detected
    """
    _check_string(item.title, f"{field_path}.title")

    # Check nested children recursively
    for i, child in enumerate(item.children):
        _check_toc_item(child, f"{field_path}.children[{i}]")
