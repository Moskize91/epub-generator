from html import escape

from ..context import Template
from ..i18n import I18N
from ..types import BookMeta, EpubData, TocItem
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
    toc_list = _generate_toc_list(epub_data.prefaces, epub_data.chapters, nav_points)
    first_chapter_file = nav_points[0].file_name if nav_points else None
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


def _generate_toc_list(
    prefaces: list[TocItem],
    chapters: list[TocItem],
    nav_points: list[NavPoint],
) -> str:
    nav_point_index = 0

    html_parts = []
    for chapters_list in (prefaces, chapters):
        for toc_item in chapters_list:
            nav_point_index, item_html = _generate_toc_item(
                toc_item, nav_points, nav_point_index
            )
            html_parts.append(item_html)

    return "\n".join(html_parts)


def _generate_toc_item(
    toc_item: TocItem,
    nav_points: list[NavPoint],
    nav_point_index: int,
) -> tuple[int, str]:
    title_escaped = escape(toc_item.title)
    file_name = None
    if toc_item.get_chapter is not None and nav_point_index < len(nav_points):
        file_name = nav_points[nav_point_index].file_name
        nav_point_index += 1

    children_html = []
    for child in toc_item.children:
        nav_point_index, child_html = _generate_toc_item(
            child, nav_points, nav_point_index
        )
        children_html.append(child_html)

    if file_name is None and children_html:
        if nav_point_index > 0:
            for i in range(nav_point_index - len(toc_item.children), nav_point_index):
                if i < len(nav_points):
                    file_name = nav_points[i].file_name
                    break

    if file_name:
        html_parts = [f'      <li>\n        <a href="Text/{file_name}">{title_escaped}</a>']
    else:
        html_parts = [f'      <li>\n        <span>{title_escaped}</span>']

    if children_html:
        html_parts.append('        <ol>')
        html_parts.extend(children_html)
        html_parts.append('        </ol>')

    html_parts.append('      </li>')

    return nav_point_index, "\n".join(html_parts)
