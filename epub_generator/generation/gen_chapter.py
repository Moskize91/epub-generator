from typing import Generator
from xml.etree.ElementTree import Element

from ..context import Context
from ..i18n import I18N
from ..types import (
    Chapter,
    ContentBlock,
    Formula,
    Image,
    Mark,
    Table,
    Text,
    TextKind,
)
from .xml_utils import serialize_element, set_epub_type
from .gen_asset import process_formula, process_image, process_table


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
    if isinstance(block, Text):
        if block.kind == TextKind.HEADLINE:
            container = Element("h1")
        elif block.kind == TextKind.QUOTE:
            container = Element("p")
        elif block.kind == TextKind.BODY:
            container = Element("p")
        else:
            raise ValueError(f"Unknown TextKind: {block.kind}")

        _render_text_content(container, block.content)

        if block.kind == TextKind.QUOTE:
            blockquote = Element("blockquote")
            blockquote.append(container)
            return blockquote

        return container

    elif isinstance(block, Table):
        return process_table(context, block)

    elif isinstance(block, Formula):
        return process_formula(context, block)

    elif isinstance(block, Image):
        return process_image(context, block)

    else:
        return None


def _render_text_content(parent: Element, content: list[str | Mark]) -> None:
    """Render text content with inline citation marks."""
    current_element = parent
    for item in content:
        if isinstance(item, str):
            if current_element is parent:
                if parent.text is None:
                    parent.text = item
                else:
                    parent.text += item
            else:
                if current_element.tail is None:
                    current_element.tail = item
                else:
                    current_element.tail += item
        elif isinstance(item, Mark):
            # EPUB 3.0 noteref with semantic attributes
            anchor = Element("a")
            anchor.attrib = {
                "id": f"ref-{item.id}",
                "href": f"#fn-{item.id}",
                "class": "super",
            }
            # Set epub:type using utility function (avoids global namespace pollution)
            set_epub_type(anchor, "noteref")
            anchor.text = f"[{item.id}]"
            parent.append(anchor)
            current_element = anchor
