from html import escape

from ..context import Template
from ..i18n import I18N
from ..types import BookMeta, EpubData
from .gen_toc import TocPoint


def gen_nav(
    template: Template,
    i18n: I18N,
    epub_data: EpubData,
    toc_points: list[TocPoint],
    has_cover: bool = False,
) -> str:
    meta: BookMeta | None = epub_data.meta
    has_head_chapter = epub_data.get_head is not None
    toc_list = _generate_toc_list(toc_points)
    first_chapter_file = _find_first_file(toc_points)
    head_chapter_title = ""
    if has_head_chapter and epub_data.get_head:
        # Try to extract title from first heading if available
        head_chapter_title = "Preface"  # Default title

    return template.render(
        template="nav.xhtml",
        i18n=i18n,
        meta=meta,
        has_cover=has_cover,
        has_head_chapter=has_head_chapter,
        head_chapter_title=head_chapter_title,
        toc_list=toc_list,
        first_chapter_file=first_chapter_file,
    )


def _generate_toc_list(toc_points: list[TocPoint]) -> str:
    html_parts = []
    for toc_point in toc_points:
        item_html = _generate_toc_item(toc_point)
        html_parts.append(item_html)
    return "\n".join(html_parts)


def _generate_toc_item(toc_point: TocPoint) -> str:
    """递归生成单个 TOC 条目"""
    title_escaped = escape(toc_point.title)

    # 递归生成子节点 HTML
    children_html = []
    for child in toc_point.children:
        child_html = _generate_toc_item(child)
        children_html.append(child_html)

    # 决定链接目标
    if toc_point.ref is not None:
        # 有文件，直接链接
        file_name = toc_point.ref.file_name
    else:
        # 占位节点，链接到第一个子章节（如果有）
        file_name = _find_first_file(toc_point.children)

    # 生成 HTML
    if file_name:
        html_parts = [f'      <li>\n        <a href="Text/{file_name}">{title_escaped}</a>']
    else:
        html_parts = [f'      <li>\n        <span>{title_escaped}</span>']

    if children_html:
        html_parts.append('        <ol>')
        html_parts.extend(children_html)
        html_parts.append('        </ol>')

    html_parts.append('      </li>')

    return "\n".join(html_parts)


def _find_first_file(toc_points: list[TocPoint]) -> str | None:
    """递归查找第一个有实际文件的章节"""
    for toc_point in toc_points:
        if toc_point.ref is not None:
            return toc_point.ref.file_name
        # 递归查找子节点
        result = _find_first_file(toc_point.children)
        if result:
            return result
    return None
