from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any, Callable

from .context import Template
from .i18n import I18N
from .types import BookMeta, EpubData, TocItem


@dataclass
class NavPoint:
    toc_id: int
    file_name: str
    order: int
    get_chapter: Callable[[], Any] | None = None


def gen_toc(
    template: Template,
    i18n: I18N,
    epub_data: EpubData,
) -> tuple[str, list[NavPoint]]:
    meta: BookMeta | None = epub_data.meta
    has_cover = epub_data.cover_image_path is not None
    prefaces = epub_data.prefaces
    chapters = epub_data.chapters

    nav_point_generation = _NavPointGenerator(
        has_cover=has_cover,
        chapters_count=(
            _count_toc_items(prefaces) +
            _count_toc_items(chapters)
        ),
    )
    nav_xml_strings = []
    for chapters_list in (prefaces, chapters):
        for toc_item in chapters_list:
            xml_string = nav_point_generation.generate(toc_item)
            nav_xml_strings.append(xml_string)

    depth = max(
        _max_depth_toc_items(prefaces),
        _max_depth_toc_items(chapters),
    ) if (prefaces or chapters) else 0

    nav_points = nav_point_generation.nav_points

    toc_ncx = template.render(
        template="toc.ncx",
        depth=depth,
        i18n=i18n,
        meta=meta,
        has_cover=has_cover,
        nav_points=nav_xml_strings,
    )
    return toc_ncx, nav_points


def _count_toc_items(items: list[TocItem]) -> int:
    count: int = 0
    for item in items:
        count += 1 + _count_toc_items(item.children)
    return count


def _max_depth_toc_items(items: list[TocItem]) -> int:
    max_depth: int = 0
    for item in items:
        max_depth = max(
            max_depth,
            _max_depth_toc_items(item.children) + 1,
        )
    return max_depth


class _NavPointGenerator:
    def __init__(self, has_cover: bool, chapters_count: int):
        self._nav_points: list[NavPoint] = []
        self._next_order: int = 2 if has_cover else 1
        self._next_id: int = 1
        self._digits = len(str(chapters_count))

    @property
    def nav_points(self) -> list[NavPoint]:
        return self._nav_points

    def generate(self, toc_item: TocItem) -> str:
        _, xml_string = self._create_nav_point(toc_item)
        return xml_string

    def _create_nav_point(self, toc_item: TocItem) -> tuple[NavPoint, str]:
        nav_point: NavPoint | None = None
        if toc_item.get_chapter is not None:
            toc_id = self._next_id
            self._next_id += 1
            part_id = str(toc_id).zfill(self._digits)
            nav_point = NavPoint(
                toc_id=toc_id,
                file_name=f"part{part_id}.xhtml",
                order=self._next_order,
                get_chapter=toc_item.get_chapter,
            )
            self._nav_points.append(nav_point)
            self._next_order += 1

        children_xml = []
        for child in toc_item.children:
            child_nav_point, child_xml = self._create_nav_point(child)
            children_xml.append(child_xml)
            if nav_point is None:
                nav_point = child_nav_point

        assert nav_point is not None, "TocItem has no chapter and no valid children"

        title_escaped = escape(toc_item.title)
        children_xml_str = "\n        ".join(children_xml)
        xml_parts = [
            f'<navPoint id="np_{nav_point.toc_id}" playOrder="{nav_point.order}">',
            "    <navLabel>",
            f"        <text>{title_escaped}</text>",
            "    </navLabel>",
            f'    <content src="Text/{nav_point.file_name}" />',
        ]
        if children_xml:
            xml_parts.append("    " + children_xml_str)

        xml_parts.append("</navPoint>")

        return nav_point, "\n    ".join(xml_parts)
