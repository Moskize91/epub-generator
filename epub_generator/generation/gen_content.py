"""Shared content rendering utilities for EPUB generation."""
from xml.etree.ElementTree import Element

from ..context import Context
from ..types import Formula, HTMLTag, Mark


def render_inline_content(
    context: Context,
    parent: Element,
    content: list[str | Mark | Formula | HTMLTag]
) -> None:
    """Render inline content with marks, formulas, and HTML tags.

    This function processes a list of content items and appends them to the parent
    element. It handles:
    - Plain text strings
    - Mark (footnote references)
    - Formula (inline mathematical expressions)
    - HTMLTag (nested HTML elements)

    Args:
        context: The EPUB generation context
        parent: The parent XML element to append content to
        content: List of content items to render
    """
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

        elif isinstance(item, HTMLTag):
            tag_element = Element(item.name)
            for attr, value in item.attributes:
                tag_element.set(attr, value)
            render_inline_content(context, tag_element, item.content)
            parent.append(tag_element)
            current_element = tag_element

        elif isinstance(item, Formula):
            # Import here to avoid circular dependency
            from .gen_asset import process_formula
            formula_element = process_formula(context, item, inline_mode=True)
            if formula_element is not None:
                parent.append(formula_element)
                current_element = formula_element

        elif isinstance(item, Mark):
            from .xml_utils import set_epub_type
            # EPUB 3.0 noteref with semantic attributes
            anchor = Element("a")
            anchor.attrib = {
                "id": f"ref-{item.id}",
                "href": f"#fn-{item.id}",
                "class": "super",
            }
            set_epub_type(anchor, "noteref")
            anchor.text = f"[{item.id}]"
            parent.append(anchor)
            current_element = anchor
