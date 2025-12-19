from dataclasses import dataclass
from typing import Any, Callable, Generator

from ..types import EpubData, TocItem


@dataclass
class TocPoint:
    title: str
    order: int
    ref: "TocPointRef | None"
    children: list["TocPoint"]

    @property
    def is_placeholder(self) -> bool:
        """是否为占位节点（无对应文件）"""
        return self.ref is None

    @property
    def has_file(self) -> bool:
        """是否有对应的 XHTML 文件"""
        return self.ref is not None

@dataclass
class TocPointRef:
    part_id: str
    file_name: str
    get_chapter: Callable[[], Any]


def iter_toc(toc_points: list[TocPoint]) -> Generator[TocPointRef, None, None]:
    for toc_point in toc_points:
        if toc_point.ref:
            yield toc_point.ref
        yield from iter_toc(toc_point.children)


def gen_toc(epub_data: EpubData) -> list[TocPoint]:
    prefaces = epub_data.prefaces
    chapters = epub_data.chapters

    toc_point_generation = _TocPointGenerator(
        chapters_count=(
            _count_toc_items(prefaces) +
            _count_toc_items(chapters)
        ),
    )
    toc_points: list[TocPoint] = []
    for chapters_list in (prefaces, chapters):
        for toc_item in chapters_list:
            toc_point = toc_point_generation.generate(toc_item)
            toc_points.append(toc_point)

    return toc_points


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


class _TocPointGenerator:
    def __init__(self, chapters_count: int):
        self._next_order: int = 0
        self._next_id: int = 1
        self._digits = len(str(chapters_count))

    def generate(self, toc_item: TocItem) -> TocPoint:
        return self._create_toc_point(toc_item)

    def _create_toc_point(self, toc_item: TocItem) -> TocPoint:
        ref: TocPointRef | None = None
        if toc_item.get_chapter is not None:
            part_id = self._next_id
            self._next_id += 1
            part_id = str(part_id).zfill(self._digits)
            ref = TocPointRef(
                part_id=part_id,
                file_name=f"part{part_id}.xhtml",
                get_chapter=toc_item.get_chapter,
            )
        order = self._next_order # 确保 order 以中序遍历为顺序
        self._next_order += 1

        return TocPoint(
            title=toc_item.title, 
            order=order,
            ref=ref, 
            children=[
                self._create_toc_point(child)
                for child in toc_item.children
            ],
        )
