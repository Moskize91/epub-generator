from __future__ import annotations
from json import loads
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree.ElementTree import tostring, Element
from .i18n import I18N
from .context import Template


@dataclass
class NavPoint:
  index_id: int
  file_name: str
  order: int

def gen_index(
    template: Template,
    i18n: I18N,
    meta: dict,
    index_file_path: Path,
    has_cover: bool,
    check_chapter_exits: Callable[[int], bool],
  ) -> tuple[str, list[NavPoint]]:

  nav_elements: list[Element]
  nav_points: list[NavPoint]
  depth: int

  if index_file_path.exists():
    prefaces, chapters = _parse_index(index_file_path)
    nav_point_generation = _NavPointGeneration(
      has_cover=has_cover,
      check_chapter_exits=check_chapter_exits,
      chapters_count=(
        _count_chapters(prefaces) +
        _count_chapters(chapters)
      ),
    )
    nav_elements = []
    for chapters_list in (prefaces, chapters):
      for chapter in chapters_list:
        element = nav_point_generation.generate(chapter)
        nav_elements.append(element)

    depth = max(
      _max_depth(prefaces),
      _max_depth(chapters),
    )
    nav_points = nav_point_generation.nav_points

  else:
    nav_elements = []
    nav_points = []
    depth = 0

  toc_ncx = template.render(
    template="toc.ncx",
    depth=depth,
    i18n=i18n,
    meta=meta,
    has_cover=has_cover,
    nav_points=[tostring(p, encoding="unicode") for p in nav_elements],
  )
  return toc_ncx, nav_points

def _count_chapters(chapters: list[_Chapter]) -> int:
  count: int = 0
  for chapter in chapters:
    count += 1 + _count_chapters(chapter.children)
  return count

def _max_depth(chapters: list[_Chapter]) -> int:
  max_depth: int = 0
  for chapter in chapters:
    max_depth = max(
      max_depth,
      _max_depth(chapter.children) + 1,
    )
  return max_depth

class _NavPointGeneration:
  def __init__(self, has_cover: bool, chapters_count: int, check_chapter_exits: Callable[[int], bool]):
    self._nav_points: list[NavPoint] = []
    self._next_order: int = 2 if has_cover else 1
    self._digits = len(str(chapters_count))
    self._check_chapter_exits: Callable[[int], bool] = check_chapter_exits

  @property
  def nav_points(self) -> list[NavPoint]:
    return self._nav_points

  def generate(self, chapter: _Chapter) -> Element:
    _, nav_point_xml = self._create_nav_point(chapter)
    return nav_point_xml
  
  def _create_nav_point(self, chapter: _Chapter) -> tuple[NavPoint, Element]:
    nav_point: NavPoint | None = None
    if self._check_chapter_exits(chapter.id):
      part_id = str(chapter.id).zfill(self._digits)
      nav_point = NavPoint(
        index_id=chapter.id,
        file_name=f"part{part_id}.xhtml",
        order=self._next_order,
      )
      self._nav_points.append(nav_point)
      self._next_order += 1

    nav_point_xml = Element("navPoint")
    for child in chapter.children:
      child, child_xml = self._create_nav_point(child)
      if child_xml is not None:
        nav_point_xml.append(child_xml)
      if nav_point is None:
        nav_point = child

    assert nav_point is not None, "Nav does not have any valid chapters"

    nav_point_xml.set("id", f"np_{chapter.id}")
    nav_point_xml.set("playOrder", str(nav_point.order))

    label_xml = Element("navLabel")
    label_text_xml = Element("text")
    label_text_xml.text = chapter.headline
    label_xml.append(label_text_xml)

    content_xml = Element("content")
    content_xml.set("src", f"Text/{nav_point.file_name}")

    nav_point_xml.insert(0, label_xml)
    nav_point_xml.insert(1, content_xml)

    return nav_point, nav_point_xml

@dataclass
class _Chapter:
  id: int
  headline: str
  children: list[_Chapter]

def _parse_index(file_path: Path) -> tuple[list[_Chapter], list[_Chapter]]:
  data: dict | list
  with open(file_path, "r", encoding="utf-8") as file:
    data = loads(file.read())
  if isinstance(data, list):
    return [], _transform_chapters(data)
  elif isinstance(data, dict):
    return (
      _transform_chapters(data["prefaces"]),
      _transform_chapters(data["chapters"]),
    )

def _transform_chapters(data_list: list) -> list[_Chapter]:
  chapters: list[_Chapter] = []
  for data in data_list:
    chapters.append(_Chapter(
      id=int(data["id"]),
      headline=data["headline"],
      children=_transform_chapters(data["children"]),
    ))
  return chapters