import shutil
import subprocess
import unittest
from pathlib import Path

from epub_generator import (
    BookMeta,
    Chapter,
    EpubData,
    Footnote,
    Formula,
    Image,
    LaTeXRender,
    Mark,
    Table,
    TableRender,
    Text,
    TextKind,
    TocItem,
    generate_epub,
)


class TestGenerateEpub(unittest.TestCase):
    """Smoke tests for EPUB 3.0 generation validated with epubcheck."""

    @classmethod
    def setUpClass(cls):
        """Set up test directories."""
        cls.temp_dir = Path(__file__).parent / "temp" / "generate-epub"
        cls.asset_dir = Path(__file__).parent / "asset"

        # Clean and create temp directory
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)
        cls.temp_dir.mkdir(exist_ok=True, parents=True)

        # Create test assets
        cls._create_test_assets()

    @classmethod
    def _create_test_assets(cls):
        """Create test asset files (cover image, test image, etc.)."""
        cls.asset_dir.mkdir(exist_ok=True, parents=True)

        # Minimal 1x1 PNG data
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # Create cover image
        cover_path = cls.asset_dir / "test_cover.png"
        if not cover_path.exists():
            cover_path.write_bytes(png_data)

        # Create test image
        test_image_path = cls.asset_dir / "test_image.png"
        if not test_image_path.exists():
            test_image_path.write_bytes(png_data)

    def _run_epubcheck(self, epub_path: Path) -> tuple[bool, str]:
        """Run epubcheck on generated EPUB file.

        Args:
            epub_path: Path to EPUB file

        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            result = subprocess.run(
                ["epubcheck", str(epub_path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,  # Don't raise exception on non-zero exit code
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
            return success, output
        except subprocess.TimeoutExpired:
            return False, "epubcheck timeout"
        except FileNotFoundError:
            self.fail("epubcheck not found. Please install epubcheck.")
            return False, ""

    def test_minimal_epub(self):
        """Test minimal EPUB with single chapter."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Minimal Test Book",
                authors=["Test Author"],
            ),
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(
                                kind=TextKind.HEADLINE,
                                content=["Chapter 1"],
                            ),
                            Text(
                                kind=TextKind.BODY,
                                content=["This is a test paragraph."],
                            ),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "minimal.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_cover(self):
        """Test EPUB with cover image."""
        cover_path = self.asset_dir / "test_cover.png"

        epub_data = EpubData(
            meta=BookMeta(title="Book with Cover"),
            cover_image_path=cover_path,
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.BODY, content=["Test content"]),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "with_cover.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_nested_chapters(self):
        """Test EPUB with nested chapter structure."""
        epub_data = EpubData(
            meta=BookMeta(title="Book with Nested Chapters"),
            chapters=[
                TocItem(
                    title="Part 1",
                    children=[
                        TocItem(
                            title="Chapter 1.1",
                            get_chapter=lambda: Chapter(
                                elements=[
                                    Text(kind=TextKind.BODY, content=["Content 1.1"]),
                                ]
                            ),
                        ),
                        TocItem(
                            title="Chapter 1.2",
                            get_chapter=lambda: Chapter(
                                elements=[
                                    Text(kind=TextKind.BODY, content=["Content 1.2"]),
                                ]
                            ),
                        ),
                    ],
                ),
            ],
        )

        output_path = self.temp_dir / "nested_chapters.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_footnotes(self):
        """Test EPUB with footnotes (noteref and footnote)."""
        epub_data = EpubData(
            meta=BookMeta(title="Book with Footnotes"),
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(
                                kind=TextKind.BODY,
                                content=[
                                    "This is a paragraph with a footnote",
                                    Mark(id=1),
                                    " reference.",
                                ],
                            ),
                        ],
                        footnotes=[
                            Footnote(
                                id=1,
                                has_mark=True,
                                contents=[
                                    Text(
                                        kind=TextKind.BODY,
                                        content=["This is the footnote content."],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "with_footnotes.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_prefaces_and_chapters(self):
        """Test EPUB with both prefaces and main chapters."""
        epub_data = EpubData(
            meta=BookMeta(
                title="Book with Prefaces",
                authors=["Author Name"],
                editors=["Editor Name"],
            ),
            prefaces=[
                TocItem(
                    title="Preface",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.HEADLINE, content=["Preface"]),
                            Text(kind=TextKind.BODY, content=["Preface content."]),
                        ]
                    ),
                ),
            ],
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.BODY, content=["Chapter 1 content."]),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "with_prefaces.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_tables_html(self):
        """Test EPUB with HTML tables."""
        epub_data = EpubData(
            meta=BookMeta(title="Book with Tables"),
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.BODY, content=["A table:"]),
                            Table(
                                html_content=(
                                    "<table><tr><th>Header</th></tr>"
                                    "<tr><td>Data</td></tr></table>"
                                )
                            ),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "with_tables_html.epub"
        generate_epub(epub_data, output_path, table_render=TableRender.HTML)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_mathml(self):
        """Test EPUB with MathML formulas."""
        epub_data = EpubData(
            meta=BookMeta(title="Book with Math"),
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.BODY, content=["A formula:"]),
                            Formula(latex_expression="x^2 + y^2 = z^2"),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "with_mathml.epub"
        generate_epub(epub_data, output_path, latex_render=LaTeXRender.MATHML)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_with_images(self):
        """Test EPUB with embedded images."""
        test_image_path = self.asset_dir / "test_image.png"

        epub_data = EpubData(
            meta=BookMeta(title="Book with Images"),
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.BODY, content=["An image:"]),
                            Image(path=test_image_path, alt_text="Test image"),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "with_images.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_full_metadata(self):
        """Test EPUB with complete metadata."""
        from datetime import datetime, timezone

        epub_data = EpubData(
            meta=BookMeta(
                title="Complete Metadata Book",
                description="A book with all metadata fields",
                publisher="Test Publisher",
                isbn="978-0-123456-78-9",
                authors=["Author One", "Author Two"],
                editors=["Editor One"],
                translators=["Translator One"],
                modified=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
            ),
            chapters=[
                TocItem(
                    title="Chapter 1",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.BODY, content=["Content."]),
                        ]
                    ),
                ),
            ],
        )

        output_path = self.temp_dir / "full_metadata.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")

    def test_epub_complex_structure(self):
        """Test EPUB with complex structure (everything combined)."""
        cover_path = self.asset_dir / "test_cover.png"
        test_image_path = self.asset_dir / "test_image.png"

        epub_data = EpubData(
            meta=BookMeta(
                title="Complex Structure Book",
                authors=["Test Author"],
            ),
            cover_image_path=cover_path,
            prefaces=[
                TocItem(
                    title="Preface",
                    get_chapter=lambda: Chapter(
                        elements=[
                            Text(kind=TextKind.HEADLINE, content=["Preface"]),
                            Text(kind=TextKind.BODY, content=["Preface text."]),
                        ]
                    ),
                ),
            ],
            chapters=[
                TocItem(
                    title="Part 1",
                    children=[
                        TocItem(
                            title="Chapter 1.1",
                            get_chapter=lambda: Chapter(
                                elements=[
                                    Text(
                                        kind=TextKind.HEADLINE,
                                        content=["Chapter 1.1"],
                                    ),
                                    Text(
                                        kind=TextKind.BODY,
                                        content=[
                                            "Text with footnote",
                                            Mark(id=1),
                                            ".",
                                        ],
                                    ),
                                    Image(path=test_image_path, alt_text="Image"),
                                    Table(
                                        html_content=(
                                            "<table><tr><td>Cell</td></tr></table>"
                                        )
                                    ),
                                ],
                                footnotes=[
                                    Footnote(
                                        id=1,
                                        contents=[
                                            Text(
                                                kind=TextKind.BODY,
                                                content=["Footnote text."],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        )

        output_path = self.temp_dir / "complex_structure.epub"
        generate_epub(epub_data, output_path)

        self.assertTrue(output_path.exists())
        success, output = self._run_epubcheck(output_path)
        self.assertTrue(success, f"epubcheck failed:\n{output}")


if __name__ == "__main__":
    unittest.main()
