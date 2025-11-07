from os import PathLike
from pathlib import Path
from typing import Literal
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement
from zipfile import ZipFile

from .context import Context, Template
from .gen_index import NavPoint, gen_index
from .gen_part import generate_part
from .hash import sha256_hash
from .i18n import I18N
from .options import LaTeXRender, TableRender
from .types import (
    BookMeta,
    Chapter,
    ContentBlock,
    EpubData,
    Footnote,
    Formula,
    Headline,
    Image,
    Mark,
    Quote,
    Table,
    Text,
)


def _hash_file(path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    with open(path, "rb") as f:
        return sha256_hash(f.read())


def generate_epub_from_data(
    epub_data: EpubData,
    epub_file_path: PathLike,
    lan: Literal["zh", "en"] = "zh",
    table_render: TableRender = TableRender.HTML,
    latex_render: LaTeXRender = LaTeXRender.MATHML,
) -> None:
    """Generate EPUB file from EpubData dataclass.

    Args:
        epub_data: EpubData containing all book information
        epub_file_path: Path where the EPUB file will be created
        lan: Language for i18n ("zh" or "en")
        table_render: How to render tables (HTML or SVG)
        latex_render: How to render LaTeX formulas (MATHML or SVG)
    """
    i18n = I18N(lan)
    template = Template()
    epub_file_path = Path(epub_file_path)

    toc_ncx, nav_points = gen_index(
        template=template,
        i18n=i18n,
        epub_data=epub_data,
    )

    # Extract metadata for later use
    meta: BookMeta | None = epub_data.meta

    has_head_chapter = epub_data.get_head is not None
    has_cover = epub_data.cover_image_path is not None

    epub_base_path = epub_file_path.parent
    epub_base_path.mkdir(parents=True, exist_ok=True)

    with ZipFile(epub_file_path, "w") as file:
        context = Context(
            file=file,
            template=template,
            table_render=table_render,
            latex_render=latex_render,
        )
        file.writestr(
            zinfo_or_arcname="mimetype",
            data=template.render("mimetype").encode("utf-8"),
        )
        file.writestr(
            zinfo_or_arcname="OEBPS/toc.ncx",
            data=toc_ncx.encode("utf-8"),
        )
        _write_chapters_from_data(
            context=context,
            i18n=i18n,
            nav_points=nav_points,
            epub_data=epub_data,
        )
        _write_basic_files(
            context=context,
            i18n=i18n,
            meta=meta,
            nav_points=nav_points,
            has_cover=has_cover,
            has_head_chapter=has_head_chapter,
        )
        _write_assets_from_data(
            context=context,
            i18n=i18n,
            epub_data=epub_data,
        )


def _chapter_to_element(chapter: Chapter) -> Element:
    """Convert a Chapter dataclass to an XML Element."""
    root = Element("chapter")

    for block in chapter.elements:
        child = _content_block_to_element(block)
        root.append(child)

    for footnote in chapter.footnotes:
        footnote_elem = _footnote_to_element(footnote)
        root.append(footnote_elem)

    return root


def _content_block_to_element(block: ContentBlock) -> Element:
    """Convert a ContentBlock to an XML Element."""
    if isinstance(block, Headline):
        return _headline_to_element(block)
    elif isinstance(block, Text):
        return _text_to_element(block)
    elif isinstance(block, Quote):
        return _quote_to_element(block)
    elif isinstance(block, Table):
        return _table_to_element(block)
    elif isinstance(block, Formula):
        return _formula_to_element(block)
    elif isinstance(block, Image):
        return _image_to_element(block)
    else:
        raise TypeError(f"Unknown ContentBlock type: {type(block)}")


def _set_mixed_content(elem: Element, text: str, marks: list[Mark]) -> None:
    """Set mixed text and Mark content on an element."""
    if not marks:
        elem.text = text
        return

    # Build a list of text segments and marks
    # Marks are inline, so we need to interleave them with text
    # For simplicity, we just append text and then marks
    elem.text = text

    for mark in marks:
        mark_elem = SubElement(elem, "mark")
        mark_elem.set("id", str(mark.id))


def _headline_to_element(headline: Headline) -> Element:
    """Convert a Headline to an XML Element."""
    elem = Element("headline")
    _set_mixed_content(elem, headline.text, headline.marks)
    return elem


def _text_to_element(text: Text) -> Element:
    """Convert a Text to an XML Element."""
    elem = Element("text")
    _set_mixed_content(elem, text.text, text.marks)
    return elem


def _quote_to_element(quote: Quote) -> Element:
    """Convert a Quote to an XML Element."""
    elem = Element("quote")
    _set_mixed_content(elem, quote.text, quote.marks)
    return elem


def _table_to_element(table: Table) -> Element:
    """Convert a Table to an XML Element."""
    elem = Element("table")
    html_elem = SubElement(elem, "html")
    html_elem.text = table.html_content
    return elem


def _formula_to_element(formula: Formula) -> Element:
    """Convert a Formula to an XML Element."""
    elem = Element("formula")
    elem.text = formula.latex_expression
    return elem


def _image_to_element(image: Image) -> Element:
    """Convert an Image to an XML Element."""
    elem = Element("image")

    if image.path.exists():
        file_hash = _hash_file(image.path)
        elem.set("hash", file_hash)
        elem.set("_source_path", str(image.path))
    else:
        raise FileNotFoundError(f"Image file not found: {image.path}")

    elem.text = image.alt_text
    return elem


def _footnote_to_element(footnote: Footnote) -> Element:
    """Convert a Footnote to an XML Element."""
    elem = Element("footnote")
    elem.set("id", str(footnote.id))

    if footnote.has_mark:
        SubElement(elem, "mark")

    for block in footnote.contents:
        child = _content_block_to_element(block)
        elem.append(child)

    return elem


def _write_assets_from_data(
    context: Context,
    i18n: I18N,
    epub_data: EpubData,
):
    """Write assets (CSS, cover, images) from EpubData."""
    context.file.writestr(
        zinfo_or_arcname="OEBPS/styles/style.css",
        data=context.template.render("style.css").encode("utf-8"),
    )

    has_cover = epub_data.cover_image_path is not None

    if has_cover:
        context.file.writestr(
            zinfo_or_arcname="OEBPS/Text/cover.xhtml",
            data=context.template.render(
                template="cover.xhtml",
                i18n=i18n,
            ).encode("utf-8"),
        )
    if has_cover and epub_data.cover_image_path:
        context.file.write(
            filename=epub_data.cover_image_path,
            arcname="OEBPS/assets/cover.png",
        )
    context.add_used_asset_files()


def _write_chapters_from_data(
    context: Context,
    i18n: I18N,
    nav_points: list[NavPoint],
    epub_data: EpubData,
):
    """Write chapter XHTML files from EpubData."""
    if epub_data.get_head is not None:
        chapter = epub_data.get_head()
        chapter_xml = _chapter_to_element(chapter)
        data = generate_part(context, chapter_xml, i18n)
        context.file.writestr(
            zinfo_or_arcname="OEBPS/Text/head.xhtml",
            data=data.encode("utf-8"),
        )

    for nav_point in nav_points:
        if nav_point.get_chapter is not None:
            chapter = nav_point.get_chapter()
            chapter_xml = _chapter_to_element(chapter)
            data = generate_part(context, chapter_xml, i18n)
            context.file.writestr(
                zinfo_or_arcname="OEBPS/Text/" + nav_point.file_name,
                data=data.encode("utf-8"),
            )


def _write_basic_files(
    context: Context,
    i18n: I18N,
    meta: BookMeta | None,
    nav_points: list[NavPoint],
    has_cover: bool,
    has_head_chapter: bool,
):
    context.file.writestr(
        zinfo_or_arcname="META-INF/container.xml",
        data=context.template.render("container.xml").encode("utf-8"),
    )
    isbn = (meta.isbn if meta else None) or str(uuid4())
    content = context.template.render(
        template="content.opf",
        meta=meta,
        i18n=i18n,
        ISBN=isbn,
        nav_points=nav_points,
        has_head_chapter=has_head_chapter,
        has_cover=has_cover,
        asset_files=context.used_files,
    )
    context.file.writestr(
        zinfo_or_arcname="OEBPS/content.opf",
        data=content.encode("utf-8"),
    )
