from dataclasses import dataclass
from typing import Any, Callable

from ..types import EpubData, TocItem


@dataclass
class NavPoint:
    toc_id: int
    file_name: str
    order: int
    get_chapter: Callable[[], Any] | None = None


def gen_toc(
    epub_data: EpubData,
    has_cover: bool = False,
) -> list[NavPoint]:
    prefaces = epub_data.prefaces
    chapters = epub_data.chapters

    nav_point_generation = _NavPointGenerator(
        has_cover=has_cover,
        chapters_count=(
            _count_toc_items(prefaces) +
            _count_toc_items(chapters)
        ),
    )
    for chapters_list in (prefaces, chapters):
        for toc_item in chapters_list:
            nav_point_generation.generate(toc_item)

    return nav_point_generation.nav_points


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

    def generate(self, toc_item: TocItem) -> None:
        self._create_nav_point(toc_item)

    def _create_nav_point(self, toc_item: TocItem) -> NavPoint:
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

        for child in toc_item.children:
            child_nav_point = self._create_nav_point(child)
            if nav_point is None:
                nav_point = child_nav_point

        assert nav_point is not None, "TocItem has no chapter and no valid children"
        return nav_point
