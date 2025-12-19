from html import escape

from ..context import Template
from ..i18n import I18N
from ..types import BookMeta, EpubData
from .gen_toc import NavPoint


def gen_nav(
    template: Template,
    i18n: I18N,
    epub_data: EpubData,
    nav_points: list[NavPoint],
    has_cover: bool = False,
) -> str:
    meta: BookMeta | None = epub_data.meta
    has_head_chapter = epub_data.get_head is not None
    toc_list = _generate_toc_from_nav_points(nav_points)
    first_chapter_file = _find_first_file(nav_points)
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


def _generate_toc_from_nav_points(nav_points: list[NavPoint]) -> str:
    """直接从 NavPoint 树生成 TOC HTML"""
    html_parts = []
    for nav_point in nav_points:
        item_html = _generate_toc_item(nav_point)
        html_parts.append(item_html)
    return "\n".join(html_parts)


def _generate_toc_item(nav_point: NavPoint) -> str:
    """递归生成单个 TOC 条目"""
    title_escaped = escape(nav_point.title)

    # 递归生成子节点 HTML
    children_html = []
    for child in nav_point.children:
        child_html = _generate_toc_item(child)
        children_html.append(child_html)

    # 决定链接目标
    if nav_point.ref is not None:
        # 有文件，直接链接
        file_name = nav_point.ref.file_name
    else:
        # 占位节点，链接到第一个子章节（如果有）
        file_name = _find_first_file(nav_point.children)

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


def _find_first_file(nav_points: list[NavPoint]) -> str | None:
    """递归查找第一个有实际文件的章节"""
    for nav_point in nav_points:
        if nav_point.ref is not None:
            return nav_point.ref.file_name
        # 递归查找子节点
        result = _find_first_file(nav_point.children)
        if result:
            return result
    return None
