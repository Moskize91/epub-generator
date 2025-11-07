from typing import Generator
from xml.etree.ElementTree import Element, tostring

from .context import Context
from .gen_asset import process_formula, process_image, process_table
from .i18n import I18N
from .types import (
    Chapter,
    ContentBlock,
    Formula,
    Headline,
    Image,
    Quote,
    Table,
    Text,
)


def generate_chapter(
    context: Context,
    chapter: Chapter,
    i18n: I18N,
) -> str:
    return context.template.render(
        template="part.xhtml",
        i18n=i18n,
        content=[
            tostring(child, encoding="unicode")
            for child in _render_contents(context, chapter)
        ],
        citations=[
            tostring(child, encoding="unicode")
            for child in _render_footnotes(context, chapter)
        ],
    )

def _render_contents(
    context: Context,
    chapter: Chapter,
) -> Generator[Element, None, None]:
    for block in chapter.elements:
        layout = _render_content_block(context, block)
        if layout is not None:
            yield layout

def _render_footnotes(
    context: Context,
    chapter: Chapter,
) -> Generator[Element, None, None]:
    for footnote in chapter.footnotes:
        if not footnote.has_mark or not footnote.contents:
            continue

        citation_div = Element("div", attrib={"class": "citation"})
        for block in footnote.contents:
            layout = _render_content_block(context, block)
            if layout is not None:
                citation_div.append(layout)

        if len(citation_div) == 0:
            continue

        ref = Element("a")
        ref.text = f"[{footnote.id}]"
        ref.attrib = {
            "id": f"mark-{footnote.id}",
            "href": f"#ref-{footnote.id}",
            "class": "citation",
        }
        first_layout = citation_div[0]
        if first_layout.tag == "p":
            ref.tail = first_layout.text
            first_layout.text = None
            first_layout.insert(0, ref)
        else:
            inject_p = Element("p")
            inject_p.append(ref)
            citation_div.insert(0, inject_p)

        yield citation_div


def _render_content_block(context: Context, block: ContentBlock) -> Element | None:
    if isinstance(block, Headline):
        h1 = Element("h1")
        h1.text = block.text
        _add_marks(h1, block.marks)
        return h1

    elif isinstance(block, Text):
        p = Element("p")
        p.text = block.text
        _add_marks(p, block.marks)
        return p

    elif isinstance(block, Quote):
        p = Element("p")
        p.text = block.text
        _add_marks(p, block.marks)
        blockquote = Element("blockquote")
        blockquote.append(p)
        return blockquote

    elif isinstance(block, Table):
        return process_table(context, block)

    elif isinstance(block, Formula):
        return process_formula(context, block)

    elif isinstance(block, Image):
        return process_image(context, block)

    else:
        return None


def _add_marks(parent: Element, marks: list) -> None:
    for mark in marks:
        anchor = Element("a")
        anchor.attrib = {
            "id": f"ref-{mark.id}",
            "href": f"#mark-{mark.id}",
            "class": "super",
        }
        anchor.text = f"[{mark.id}]"
        parent.append(anchor)
