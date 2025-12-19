from dataclasses import dataclass, field
from typing import Any, Callable

from ..types import EpubData, TocItem


@dataclass
class NavPointRef:
    """NavPoint 的文件引用，只有实际章节才有"""
    toc_id: int
    file_name: str
    order: int
    get_chapter: Callable[[], Any]  # 不再允许 None


@dataclass
class NavPoint:
    """目录节点，支持树型结构"""
    title: str  # 章节标题
    ref: NavPointRef | None = None  # 实际文件引用（占位节点为 None）
    children: list["NavPoint"] = field(default_factory=list)  # 子节点

    @property
    def is_placeholder(self) -> bool:
        """是否为占位节点（无对应文件）"""
        return self.ref is None

    @property
    def has_file(self) -> bool:
        """是否有对应的 XHTML 文件"""
        return self.ref is not None


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
    nav_points: list[NavPoint] = []
    for chapters_list in (prefaces, chapters):
        for toc_item in chapters_list:
            nav_point = nav_point_generation.generate(toc_item)
            nav_points.append(nav_point)

    return nav_points


def flatten_nav_points(nav_points: list[NavPoint]) -> list[NavPointRef]:
    """将 NavPoint 树展平为 NavPointRef 列表，按深度优先顺序，只包含有实际文件的节点"""
    result: list[NavPointRef] = []

    def _flatten(nav_point: NavPoint) -> None:
        if nav_point.ref is not None:
            result.append(nav_point.ref)
        for child in nav_point.children:
            _flatten(child)

    for nav_point in nav_points:
        _flatten(nav_point)

    return result


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
        self._next_order: int = 2 if has_cover else 1
        self._next_id: int = 1
        self._digits = len(str(chapters_count))

    def generate(self, toc_item: TocItem) -> NavPoint:
        return self._create_nav_point(toc_item)

    def _create_nav_point(self, toc_item: TocItem) -> NavPoint:
        # 递归处理子节点
        children: list[NavPoint] = []
        for child in toc_item.children:
            child_nav_point = self._create_nav_point(child)
            children.append(child_nav_point)

        # 创建当前节点
        if toc_item.get_chapter is not None:
            # 有实际文件的节点
            toc_id = self._next_id
            self._next_id += 1
            part_id = str(toc_id).zfill(self._digits)

            ref = NavPointRef(
                toc_id=toc_id,
                file_name=f"part{part_id}.xhtml",
                order=self._next_order,
                get_chapter=toc_item.get_chapter,
            )
            self._next_order += 1

            return NavPoint(title=toc_item.title, ref=ref, children=children)
        else:
            # 占位节点
            return NavPoint(title=toc_item.title, ref=None, children=children)
