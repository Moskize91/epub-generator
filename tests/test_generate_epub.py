"""Smoke tests for generate_epub function."""
import shutil
import unittest
from pathlib import Path
from zipfile import ZipFile

from epub_generator.gen_epub import generate_epub
from epub_generator.types import BookMeta, Chapter, EpubData, Text, TextKind, TocItem


class TestGenerateEpub(unittest.TestCase):
    """Basic smoke tests for EPUB generation."""

    @classmethod
    def setUpClass(cls):
        """Set up test directories."""
        cls.temp_dir = Path(__file__).parent / "temp"
        cls.asset_dir = Path(__file__).parent / "asset"

        # Clean and create temp directory
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)
        cls.temp_dir.mkdir(exist_ok=True)

    def test_generate_minimal_epub(self):
        """Test generating a minimal EPUB with basic content."""
        # Prepare test data
        epub_data = EpubData(
            meta=BookMeta(
                title="Test Book",
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

        # Generate EPUB
        output_path = self.temp_dir / "test_minimal.epub"
        generate_epub(epub_data, output_path)

        # Verify EPUB was created
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)

        # Verify EPUB structure
        with ZipFile(output_path, "r") as epub_file:
            namelist = epub_file.namelist()

            # Check essential files exist
            self.assertIn("mimetype", namelist)
            self.assertIn("META-INF/container.xml", namelist)
            self.assertIn("OEBPS/content.opf", namelist)
            self.assertIn("OEBPS/toc.ncx", namelist)

            # Verify mimetype content
            mimetype = epub_file.read("mimetype").decode("utf-8")
            self.assertEqual(mimetype, "application/epub+zip")

    def test_generate_epub_with_cover(self):
        """Test generating EPUB with cover image."""
        # Create a dummy cover image
        cover_path = self.asset_dir / "test_cover.png"
        cover_path.parent.mkdir(exist_ok=True, parents=True)

        # Create a minimal 1x1 PNG (if not exists)
        if not cover_path.exists():
            # Minimal valid PNG file (1x1 transparent pixel)
            png_data = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )
            cover_path.write_bytes(png_data)

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

        output_path = self.temp_dir / "test_with_cover.epub"
        generate_epub(epub_data, output_path)

        # Verify cover files exist in EPUB
        with ZipFile(output_path, "r") as epub_file:
            namelist = epub_file.namelist()
            self.assertIn("OEBPS/Text/cover.xhtml", namelist)
            self.assertIn("OEBPS/assets/cover.png", namelist)

    def test_generate_epub_with_nested_chapters(self):
        """Test generating EPUB with nested chapter structure."""
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

        output_path = self.temp_dir / "test_nested.epub"
        generate_epub(epub_data, output_path)

        # Verify EPUB was created successfully
        self.assertTrue(output_path.exists())

        with ZipFile(output_path, "r") as epub_file:
            # Verify TOC file exists
            self.assertIn("OEBPS/toc.ncx", epub_file.namelist())


if __name__ == "__main__":
    unittest.main()
