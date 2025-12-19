from xml.etree.ElementTree import Element

from ..context import Template
from ..i18n import I18N
from ..types import BookMeta, EpubData
from .gen_toc import TocPoint, iter_toc
from .xml_utils import indent, serialize_element


def gen_nav(
    template: Template,
    i18n: I18N,
    epub_data: EpubData,
    toc_points: list[TocPoint],
    has_cover: bool = False,
) -> str:
    meta: BookMeta | None = epub_data.meta
    has_head_chapter = epub_data.get_head is not None
    toc_body = "\n".join(_render_toc_item(toc_points))
    first_ref = next(iter_toc(toc_points), None)

    first_chapter_file: str = ""
    head_chapter_title: str = ""
    if first_ref:
        first_chapter_file = first_ref.file_name
    if has_head_chapter and epub_data.get_head:
        head_chapter_title = i18n.preface

    return template.render(
        template="nav.xhtml",
        i18n=i18n,
        meta=meta,
        has_cover=has_cover,
        has_head_chapter=has_head_chapter,
        head_chapter_title=head_chapter_title,
        toc_body=toc_body,
        first_chapter_file=first_chapter_file,
    )


def _render_toc_item(toc_points: list[TocPoint]):
    for toc_point in toc_points:
        element = _create_toc_li_element(toc_point)
        element = indent(element)
        yield serialize_element(element)


def _create_toc_li_element(toc_point: TocPoint) -> Element:
    li = Element("li")

    if toc_point.ref is not None:
        file_name = toc_point.ref.file_name
        link = Element("a")
        link.set("href", f"Text/{file_name}")
        link.text = toc_point.title
        li.append(link)
    else:
        span = Element("span")
        span.text = toc_point.title
        li.append(span)

    # 递归处理子节点
    if toc_point.children:
        ol = Element("ol")
        for child in toc_point.children:
            child_li = _create_toc_li_element(child)
            ol.append(child_li)
        li.append(ol)

    return li
