from typing import Generator
from xml.etree.ElementTree import Element

from ..context import Context
from ..i18n import I18N
from ..types import (
    Chapter,
    ContentBlock,
    Formula,
    Image,
    Table,
    TextBlock,
    TextKind,
)
from .gen_asset import render_asset_block
from .gen_content import render_inline_content
from .xml_utils import serialize_element, set_epub_type

_MAX_HEADING_LEVEL = 6 # HTML standard defines heading levels from h1 to h6


def generate_chapter(
    context: Context,
    chapter: Chapter,
    i18n: I18N,
) -> str:
    return context.template.render(
        template="part.xhtml",
        i18n=i18n,
        content=[
            serialize_element(child)
            for child in _render_contents(context, chapter)
        ],
        citations=[
            serialize_element(child)
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

        # Use <aside> with EPUB 3.0 semantic attributes
        citation_aside = Element("aside")
        citation_aside.attrib = {
            "id": f"fn-{footnote.id}",
            "class": "footnote",
        }
        set_epub_type(citation_aside, "footnote")

        for block in footnote.contents:
            layout = _render_content_block(context, block)
            if layout is not None:
                citation_aside.append(layout)

        if len(citation_aside) == 0:
            continue

        # Back-reference link with EPUB 3.0 attributes
        ref = Element("a")
        ref.text = f"[{footnote.id}]"
        ref.attrib = {
            "href": f"#ref-{footnote.id}",
        }
        first_layout = citation_aside[0]
        if first_layout.tag == "p":
            ref.tail = first_layout.text
            first_layout.text = None
            first_layout.insert(0, ref)
        else:
            inject_p = Element("p")
            inject_p.append(ref)
            citation_aside.insert(0, inject_p)

        yield citation_aside


def _render_content_block(context: Context, block: ContentBlock) -> Element | None:
    if isinstance(block, Table | Formula | Image):
        return render_asset_block(context, block)

    elif isinstance(block, TextBlock):
        if block.kind == TextKind.HEADLINE:
            heading_level = min(block.level + 1, _MAX_HEADING_LEVEL)
            container = Element(f"h{heading_level}")
        elif block.kind == TextKind.QUOTE:
            container = Element("p")
        elif block.kind == TextKind.BODY:
            container = Element("p")
        else:
            raise ValueError(f"Unknown TextKind: {block.kind}")

        render_inline_content(
            context=context,
            parent=container,
            content=block.content,
        )
        if block.kind == TextKind.QUOTE:
            blockquote = Element("blockquote")
            blockquote.append(container)
            return blockquote

        return container
    
    else:
        return None
