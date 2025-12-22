import unittest
from pathlib import Path

from epub_generator import (
    BookMeta,
    Chapter,
    EpubData,
    Footnote,
    Formula,
    HTMLTag,
    Image,
    InvalidUnicodeError,
    Mark,
    Table,
    TextBlock,
    TextKind,
    TocItem,
)
from epub_generator.validate import validate_chapter, validate_epub_data


class TestValidateUnicode(unittest.TestCase):
    """Test validation of invalid Unicode characters (surrogates) in EPUB data."""

    def setUp(self):
        """Set up test data."""
        # Create a surrogate character (invalid in UTF-8)
        self.surrogate_char = "\ud800"  # U+D800 is a surrogate character
        self.valid_string = "Valid text"

        # Create a test image path for asset tests
        self.test_image_path = Path(__file__).parent / "asset" / "test_image.png"

    def test_valid_epub_data_passes(self):
        """Test that valid EpubData passes validation."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                description="Valid description",
                publisher="Valid Publisher",
                isbn="978-0-123456-78-9",
                authors=["Author One", "Author Two"],
                editors=["Editor One"],
                translators=["Translator One"],
            ),
            prefaces=[
                TocItem(title="Valid Preface"),
            ],
            chapters=[
                TocItem(
                    title="Valid Chapter",
                    children=[
                        TocItem(title="Valid Subchapter"),
                    ],
                ),
            ],
        )

        # Should not raise any exception
        try:
            validate_epub_data(epub_data)
        except InvalidUnicodeError:
            self.fail("validate_epub_data raised InvalidUnicodeError for valid data")

    def test_invalid_meta_title(self):
        """Test detection of surrogate in meta title."""
        epub_data = EpubData(
            meta=BookMeta(title=f"Invalid{self.surrogate_char}Title"),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.title", str(cm.exception))
        self.assertIn("U+D800", str(cm.exception))

    def test_invalid_meta_description(self):
        """Test detection of surrogate in meta description."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                description=f"Invalid{self.surrogate_char}Description",
            ),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.description", str(cm.exception))

    def test_invalid_meta_publisher(self):
        """Test detection of surrogate in meta publisher."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                publisher=f"Invalid{self.surrogate_char}Publisher",
            ),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.publisher", str(cm.exception))

    def test_invalid_meta_isbn(self):
        """Test detection of surrogate in meta ISBN."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                isbn=f"978{self.surrogate_char}123",
            ),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.isbn", str(cm.exception))

    def test_invalid_meta_author(self):
        """Test detection of surrogate in author list."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                authors=["Valid Author", f"Invalid{self.surrogate_char}Author"],
            ),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.authors[1]", str(cm.exception))

    def test_invalid_meta_editor(self):
        """Test detection of surrogate in editor list."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                editors=[f"Invalid{self.surrogate_char}Editor"],
            ),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.editors[0]", str(cm.exception))

    def test_invalid_meta_translator(self):
        """Test detection of surrogate in translator list."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Valid Title",
                translators=[f"Invalid{self.surrogate_char}Translator"],
            ),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.meta.translators[0]", str(cm.exception))

    def test_invalid_preface_title(self):
        """Test detection of surrogate in preface title."""
        epub_data = EpubData(
            meta=BookMeta(title="Valid Title"),
            prefaces=[TocItem(title=f"Invalid{self.surrogate_char}Preface")],
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.prefaces[0].title", str(cm.exception))

    def test_invalid_chapter_title(self):
        """Test detection of surrogate in chapter title."""
        epub_data = EpubData(
            meta=BookMeta(title="Valid Title"),
            chapters=[TocItem(title=f"Invalid{self.surrogate_char}Chapter")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.chapters[0].title", str(cm.exception))

    def test_invalid_nested_chapter_title(self):
        """Test detection of surrogate in nested chapter title."""
        epub_data = EpubData(
            meta=BookMeta(title="Valid Title"),
            chapters=[
                TocItem(
                    title="Valid Part",
                    children=[
                        TocItem(title=f"Invalid{self.surrogate_char}Subchapter"),
                    ],
                ),
            ],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        self.assertIn("EpubData.chapters[0].children[0].title", str(cm.exception))

    def test_valid_chapter_passes(self):
        """Test that valid Chapter passes validation."""
        chapter = Chapter(
            elements=[
                TextBlock(
                    kind=TextKind.BODY,
                    level=0,
                    content=["Valid text content"],
                ),
            ],
            footnotes=[
                Footnote(
                    id=1,
                    contents=[
                        TextBlock(
                            kind=TextKind.BODY,
                            level=0,
                            content=["Valid footnote"],
                        ),
                    ],
                ),
            ],
        )

        # Should not raise any exception
        try:
            validate_chapter(chapter)
        except InvalidUnicodeError:
            self.fail("validate_chapter raised InvalidUnicodeError for valid data")

    def test_invalid_textblock_content(self):
        """Test detection of surrogate in TextBlock content."""
        chapter = Chapter(
            elements=[
                TextBlock(
                    kind=TextKind.BODY,
                    level=0,
                    content=[f"Invalid{self.surrogate_char}content"],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].content[0]", str(cm.exception))

    def test_invalid_formula_latex(self):
        """Test detection of surrogate in Formula LaTeX expression."""
        chapter = Chapter(
            elements=[
                Formula(latex_expression=f"x^2{self.surrogate_char}+y^2"),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].latex_expression", str(cm.exception))

    def test_invalid_formula_title(self):
        """Test detection of surrogate in Formula title."""
        chapter = Chapter(
            elements=[
                Formula(
                    latex_expression="x^2",
                    title=[f"Invalid{self.surrogate_char}Title"],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].title[0]", str(cm.exception))

    def test_invalid_formula_caption(self):
        """Test detection of surrogate in Formula caption."""
        chapter = Chapter(
            elements=[
                Formula(
                    latex_expression="x^2",
                    caption=[f"Invalid{self.surrogate_char}Caption"],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].caption[0]", str(cm.exception))

    def test_invalid_table_caption(self):
        """Test detection of surrogate in Table caption."""
        chapter = Chapter(
            elements=[
                Table(
                    html_content=HTMLTag(name="table"),
                    caption=[f"Invalid{self.surrogate_char}Caption"],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].caption[0]", str(cm.exception))

    def test_invalid_image_title(self):
        """Test detection of surrogate in Image title."""
        chapter = Chapter(
            elements=[
                Image(
                    path=self.test_image_path,
                    title=[f"Invalid{self.surrogate_char}Title"],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].title[0]", str(cm.exception))

    def test_invalid_htmltag_name(self):
        """Test detection of surrogate in HTMLTag name."""
        chapter = Chapter(
            elements=[
                Table(
                    html_content=HTMLTag(name=f"div{self.surrogate_char}"),
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("html_content.name", str(cm.exception))

    def test_invalid_htmltag_attribute_name(self):
        """Test detection of surrogate in HTMLTag attribute name."""
        chapter = Chapter(
            elements=[
                Table(
                    html_content=HTMLTag(
                        name="div",
                        attributes=[(f"attr{self.surrogate_char}", "value")],
                    ),
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("html_content.attributes[0][0]", str(cm.exception))

    def test_invalid_htmltag_attribute_value(self):
        """Test detection of surrogate in HTMLTag attribute value."""
        chapter = Chapter(
            elements=[
                Table(
                    html_content=HTMLTag(
                        name="div",
                        attributes=[("class", f"value{self.surrogate_char}")],
                    ),
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("html_content.attributes[0][1]", str(cm.exception))

    def test_invalid_htmltag_content(self):
        """Test detection of surrogate in HTMLTag content."""
        chapter = Chapter(
            elements=[
                Table(
                    html_content=HTMLTag(
                        name="div",
                        content=[f"Invalid{self.surrogate_char}Content"],
                    ),
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("html_content.content[0]", str(cm.exception))

    def test_invalid_nested_htmltag(self):
        """Test detection of surrogate in nested HTMLTag."""
        chapter = Chapter(
            elements=[
                Table(
                    html_content=HTMLTag(
                        name="div",
                        content=[
                            HTMLTag(
                                name="span",
                                content=[f"Invalid{self.surrogate_char}Text"],
                            ),
                        ],
                    ),
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("html_content.content[0].content[0]", str(cm.exception))

    def test_invalid_footnote_content(self):
        """Test detection of surrogate in Footnote content."""
        chapter = Chapter(
            elements=[
                TextBlock(
                    kind=TextKind.BODY,
                    level=0,
                    content=["Text with footnote", Mark(id=1)],
                ),
            ],
            footnotes=[
                Footnote(
                    id=1,
                    contents=[
                        TextBlock(
                            kind=TextKind.BODY,
                            level=0,
                            content=[f"Invalid{self.surrogate_char}Footnote"],
                        ),
                    ],
                ),
            ],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.footnotes[0].contents[0].content[0]", str(cm.exception))

    def test_invalid_inline_formula_in_textblock(self):
        """Test detection of surrogate in inline Formula within TextBlock."""
        chapter = Chapter(
            elements=[
                TextBlock(
                    kind=TextKind.BODY,
                    level=0,
                    content=[
                        "Some text ",
                        Formula(latex_expression=f"x{self.surrogate_char}^2"),
                        " more text",
                    ],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].content[1].latex_expression", str(cm.exception))

    def test_invalid_mixed_content_in_asset(self):
        """Test detection of surrogate in mixed content (string, Formula, HTMLTag) in asset caption."""
        chapter = Chapter(
            elements=[
                Image(
                    path=self.test_image_path,
                    caption=[
                        "Caption with ",
                        Formula(latex_expression="E=mc^2"),
                        f" and invalid{self.surrogate_char}text",
                    ],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter)

        self.assertIn("Chapter.elements[0].caption[2]", str(cm.exception))

    def test_multiple_surrogate_characters(self):
        """Test detection reports first surrogate character."""
        # Create string with multiple surrogates
        invalid_string = f"Start{self.surrogate_char}middle\udbffend"

        epub_data = EpubData(
            meta=BookMeta(title=invalid_string),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        # Should report the first surrogate
        self.assertIn("U+D800", str(cm.exception))
        self.assertIn("position 5", str(cm.exception))  # Position of first surrogate

    def test_position_reporting(self):
        """Test that error message includes correct character position."""
        invalid_string = f"0123456789{self.surrogate_char}rest"

        epub_data = EpubData(
            meta=BookMeta(title=invalid_string),
            chapters=[TocItem(title="Chapter 1")],
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_epub_data(epub_data)

        # Surrogate is at position 10
        self.assertIn("position 10", str(cm.exception))

    def test_custom_context_in_chapter_validation(self):
        """Test that custom context appears in error message."""
        chapter = Chapter(
            elements=[
                TextBlock(
                    kind=TextKind.BODY,
                    level=0,
                    content=[f"Invalid{self.surrogate_char}"],
                ),
            ]
        )

        with self.assertRaises(InvalidUnicodeError) as cm:
            validate_chapter(chapter, context="CustomContext")

        self.assertIn("CustomContext.elements[0].content[0]", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
