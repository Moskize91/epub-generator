import io
import re
from typing import Any, cast
from xml.etree.ElementTree import Element, fromstring

import matplotlib.pyplot as plt
from latex2mathml.converter import convert

from ..context import Context
from ..options import LaTeXRender, TableRender
from ..types import BasicAsset, Formula, HTMLTag, Image, Mark, Table

_MEDIA_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}

def _render_inline_content(
    context: Context,
    parent: Element,
    content: list[str | Mark | Formula | HTMLTag]
) -> None:
    """Render inline content (for title/caption) with marks and formulas."""
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
            _render_inline_content(context, tag_element, item.content)
            parent.append(tag_element)
            current_element = tag_element

        elif isinstance(item, Formula):
            formula_element = process_formula(context, item, inline_mode=True)
            if formula_element is not None:
                parent.append(formula_element)
                current_element = formula_element

        elif isinstance(item, Mark):
            from .xml_utils import set_epub_type
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

def _wrap_asset_with_title_caption(
    context: Context,
    asset: BasicAsset,
    content_element: Element | None,
) -> Element | None:
    """Wrap asset content with title and caption if present."""
    if content_element is None:
        return None

    # If no title and no caption, return content as-is
    if not asset.title and not asset.caption:
        return content_element

    # Create container
    container = Element("div", attrib={"class": "asset-container"})

    # Add title if present
    if asset.title:
        title_div = Element("div", attrib={"class": "asset-title"})
        _render_inline_content(context, title_div, asset.title)
        container.append(title_div)

    # Add content
    container.append(content_element)

    # Add caption if present
    if asset.caption:
        caption_div = Element("div", attrib={"class": "asset-caption"})
        _render_inline_content(context, caption_div, asset.caption)
        container.append(caption_div)

    return container

def process_table(context: Context, table: Table) -> Element | None:
    if context.table_render == TableRender.CLIPPING:
        return None

    # Convert HTMLTag to actual HTML element
    try:
        # Render the HTMLTag to an Element
        if isinstance(table.html_content, HTMLTag):
            table_element = _render_html_tag(table.html_content)
        else:
            # Fallback for backward compatibility (shouldn't happen with new types)
            wrapped_html = f"<div>{table.html_content}</div>"
            parsed = fromstring(wrapped_html)
            table_element = parsed[0] if len(parsed) > 0 else None

        if table_element is None:
            return None

        wrapper = Element("div", attrib={"class": "alt-wrapper"})
        wrapper.append(table_element)

        # Wrap with title/caption if present
        return _wrap_asset_with_title_caption(context, table, wrapper)
    except Exception:
        return None

def _render_html_tag(tag: HTMLTag) -> Element:
    """Convert HTMLTag to XML Element."""
    element = Element(tag.name)
    for attr, value in tag.attributes:
        element.set(attr, value)

    # Render content
    current_element = element
    for item in tag.content:
        if isinstance(item, str):
            if current_element is element:
                if element.text is None:
                    element.text = item
                else:
                    element.text += item
            else:
                if current_element.tail is None:
                    current_element.tail = item
                else:
                    current_element.tail += item
        elif isinstance(item, HTMLTag):
            child = _render_html_tag(item)
            element.append(child)
            current_element = child
        # Note: Formula and Mark in table content are not supported yet

    return element


def process_formula(
        context: Context,
        formula: Formula,
        inline_mode: bool,
    ) -> Element | None:

    if context.latex_render == LaTeXRender.CLIPPING:
        return None

    latex_expr = _normalize_expression(formula.latex_expression)
    if not latex_expr:
        return None

    content_element = None
    if context.latex_render == LaTeXRender.MATHML:
        content_element = _latex2mathml(
            latex=latex_expr,
            inline_mode=inline_mode,
        )
    elif context.latex_render == LaTeXRender.SVG:
        svg_image = _latex_formula2svg(latex_expr)
        if svg_image is None:
            return None
        file_name = context.add_asset(
            data=svg_image,
            media_type="image/svg+xml",
            file_ext=".svg",
        )
        img_element = Element("img")
        img_element.set("src", f"../assets/{file_name}")
        img_element.set("alt", "formula")

        if inline_mode:
            wrapper = Element("span", attrib={"class": "formula-inline"})
        else:
            wrapper = Element("div", attrib={"class": "alt-wrapper"})

        wrapper.append(img_element)
        content_element = wrapper

    # For inline formulas, don't wrap with title/caption
    if inline_mode or content_element is None:
        return content_element

    # For block formulas, wrap with title/caption if present
    return _wrap_asset_with_title_caption(context, formula, content_element)

def process_image(context: Context, image: Image) -> Element | None:
    file_ext = image.path.suffix or ".png"
    file_name = context.use_asset(
        source_path=image.path,
        media_type=_MEDIA_TYPE_MAP.get(file_ext.lower(), "image/png"),
        file_ext=file_ext,
    )
    img_element = Element("img")
    img_element.set("src", f"../assets/{file_name}")
    img_element.set("alt", "")  # Empty alt text, use caption instead

    wrapper = Element("div", attrib={"class": "alt-wrapper"})
    wrapper.append(img_element)

    # Wrap with title/caption if present
    return _wrap_asset_with_title_caption(context, image, wrapper)


_ESCAPE_UNICODE_PATTERN = re.compile(r"&#x([0-9A-Fa-f]{5});")


def _latex2mathml(latex: str, inline_mode: bool) -> None | Element:
    try:
        html_latex = convert(
            latex=latex,
            display="inline" if inline_mode else "block",
        )
    except Exception:
        return None

    # latex2mathml 转义会带上一个奇怪的 `&` 前缀，这显然是多余的
    # 不得已，在这里用正则表达式处理以修正这个错误
    def repl(match):
        hex_code = match.group(1)
        char = chr(int(hex_code, 16))
        if char == "<":
            return "&lt;"
        elif char == ">":
            return "&gt;"
        else:
            return char

    mathml = re.sub(
        pattern=_ESCAPE_UNICODE_PATTERN,
        repl=repl,
        string=html_latex,
    )
    try:
        return fromstring(mathml)
    except Exception:
        return None


def _latex_formula2svg(latex: str, font_size: int = 12):
    # from https://www.cnblogs.com/qizhou/p/18170083
    try:
        output = io.BytesIO()
        plt.rc("text", usetex=True)
        plt.rc("font", size=font_size)
        fig, ax = plt.subplots()
        txt = ax.text(0.5, 0.5, f"${latex}$", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        fig.canvas.draw()
        bbox = txt.get_window_extent(cast(Any, fig.canvas).get_renderer())
        fig.set_size_inches(bbox.width / fig.dpi, bbox.height / fig.dpi)
        plt.savefig(
            output,
            format="svg",
            transparent=True,
            bbox_inches="tight",
            pad_inches=0,
        )
        return output.getvalue()
    except Exception:
        return None


def _normalize_expression(expression: str) -> str:
    expression = expression.replace("\n", "")
    expression = expression.strip()
    return expression
