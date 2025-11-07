from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from xml.etree.ElementTree import Element, tostring

from .context import Template
from .i18n import I18N
from .types import BookMeta, EpubData


@dataclass
class NavPoint:
    index_id: int
    file_name: str
    order: int
    get_chapter: Callable[[], Any] | None = None  # Optional chapter getter for new API


def gen_index(
    template: Template,
    i18n: I18N,
    epub_data: EpubData,
) -> tuple[str, list[NavPoint]]:
    """Generate table of contents from EpubData.

    Args:
        template: Template renderer
        i18n: Internationalization
        epub_data: EpubData object

    Returns:
        Tuple of (toc_ncx string, list of NavPoint objects)
    """
    # Extract metadata from epub_data
    meta: BookMeta | None = epub_data.meta

    has_cover = epub_data.cover_image_path is not None
    prefaces = epub_data.prefaces
    chapters = epub_data.chapters

    nav_point_generation = _NavPointGenerationFromData(
        has_cover=has_cover,
        chapters_count=(
            _count_toc_items(prefaces) +
            _count_toc_items(chapters)
        ),
    )
    nav_elements = []
    for chapters_list in (prefaces, chapters):
        for toc_item in chapters_list:
            element = nav_point_generation.generate(toc_item)
            nav_elements.append(element)

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
        nav_points=[tostring(p, encoding="unicode") for p in nav_elements],
    )
    return toc_ncx, nav_points


def _count_toc_items(items: list) -> int:
    """Count total number of TocItem objects including nested children."""
    count: int = 0
    for item in items:
        count += 1 + _count_toc_items(item.children)
    return count


def _max_depth_toc_items(items: list) -> int:
    """Calculate maximum depth of TocItem tree."""
    max_depth: int = 0
    for item in items:
        max_depth = max(
            max_depth,
            _max_depth_toc_items(item.children) + 1,
        )
    return max_depth


class _NavPointGenerationFromData:
    """NavPoint generator for EpubData (TocItem) format."""

    def __init__(self, has_cover: bool, chapters_count: int):
        self._nav_points: list[NavPoint] = []
        self._next_order: int = 2 if has_cover else 1
        self._next_id: int = 1
        self._digits = len(str(chapters_count))

    @property
    def nav_points(self) -> list[NavPoint]:
        return self._nav_points

    def generate(self, toc_item: Any) -> Element:
        """Generate navPoint XML from TocItem."""
        _, nav_point_xml = self._create_nav_point(toc_item)
        return nav_point_xml

    def _create_nav_point(self, toc_item: Any) -> tuple[NavPoint, Element]:
        nav_point: NavPoint | None = None

        # If this TocItem has a chapter, create a NavPoint
        if toc_item.get_chapter is not None:
            index_id = self._next_id
            self._next_id += 1
            part_id = str(index_id).zfill(self._digits)
            nav_point = NavPoint(
                index_id=index_id,
                file_name=f"part{part_id}.xhtml",
                order=self._next_order,
                get_chapter=toc_item.get_chapter,
            )
            self._nav_points.append(nav_point)
            self._next_order += 1

        nav_point_xml = Element("navPoint")

        # Process children
        for child in toc_item.children:
            child_nav_point, child_xml = self._create_nav_point(child)
            if child_xml is not None:
                nav_point_xml.append(child_xml)
            # If this item has no chapter, use child's navpoint
            if nav_point is None:
                nav_point = child_nav_point

        assert nav_point is not None, "Nav does not have any valid chapters"

        nav_point_xml.set("id", f"np_{nav_point.index_id}")
        nav_point_xml.set("playOrder", str(nav_point.order))

        label_xml = Element("navLabel")
        label_text_xml = Element("text")
        label_text_xml.text = toc_item.title
        label_xml.append(label_text_xml)

        content_xml = Element("content")
        content_xml.set("src", f"Text/{nav_point.file_name}")

        nav_point_xml.insert(0, label_xml)
        nav_point_xml.insert(1, content_xml)

        return nav_point, nav_point_xml
