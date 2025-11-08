import io
import re
from typing import Any, cast
from xml.etree.ElementTree import Element, fromstring

import matplotlib.pyplot as plt
from latex2mathml.converter import convert

from ..context import Context
from ..options import LaTeXRender, TableRender
from ..types import Formula, Image, Table

_MEDIA_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}

def process_table(context: Context, table: Table) -> Element | None:
    if context.table_render == TableRender.CLIPPING:
        return None
    try:
        wrapped_html = f"<div>{table.html_content}</div>"
        parsed = fromstring(wrapped_html)
        wrapper = Element("div", attrib={"class": "alt-wrapper"})

        for child in parsed:
            wrapper.append(child)

        return wrapper if len(wrapper) > 0 else None
    except Exception:
        return None


def process_formula(context: Context, formula: Formula) -> Element | None:
    if context.latex_render == LaTeXRender.CLIPPING:
        return None

    latex_expr = _normalize_expression(formula.latex_expression)
    if not latex_expr:
        return None

    if context.latex_render == LaTeXRender.MATHML:
        return _latex2mathml(latex_expr)

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

        wrapper = Element("div", attrib={"class": "alt-wrapper"})
        wrapper.append(img_element)
        return wrapper

    return None

def process_image(context: Context, image: Image) -> Element | None:
    file_ext = image.path.suffix or ".png"
    file_name = context.use_asset(
        source_path=image.path, 
        media_type=_MEDIA_TYPE_MAP.get(file_ext.lower(), "image/png"), 
        file_ext=file_ext,
    )
    img_element = Element("img")
    img_element.set("src", f"../assets/{file_name}")
    img_element.set("alt", image.alt_text)

    wrapper = Element("div", attrib={"class": "alt-wrapper"})
    wrapper.append(img_element)
    return wrapper


_ESCAPE_UNICODE_PATTERN = re.compile(r"&#x([0-9A-Fa-f]{5});")


def _latex2mathml(latex: str) -> None | Element:
    try:
        html_latex = convert(latex)
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
