from xml.etree.ElementTree import Element

from ..context import Context
from ..types import Formula, HTMLTag, Mark
from .xml_utils import set_epub_type


def render_inline_content(
    context: Context,
    parent: Element,
    content: list[str | Mark | Formula | HTMLTag]
) -> None:
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
            tag_element = render_html_tag(context, item)
            parent.append(tag_element)
            current_element = tag_element

        elif isinstance(item, Formula):
            from .gen_asset import render_inline_formula  # avoid circular import
            formula_element = render_inline_formula(context, item)
            if formula_element is not None:
                parent.append(formula_element)
                current_element = formula_element

        elif isinstance(item, Mark):
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


def render_html_tag(context: Context, tag: HTMLTag) -> Element:
    """Convert HTMLTag to XML Element with full inline content support."""
    element = Element(tag.name)
    for attr, value in tag.attributes:
        element.set(attr, value)
    render_inline_content(context, element, tag.content)
    return element