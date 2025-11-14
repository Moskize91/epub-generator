from datetime import datetime, timezone
from os import PathLike
from pathlib import Path
from typing import Callable, Literal
from uuid import uuid4
from zipfile import ZipFile

from ..context import Context, Template
from ..i18n import I18N
from ..options import LaTeXRender, TableRender
from ..types import EpubData, Formula
from .gen_chapter import generate_chapter
from .gen_nav import gen_nav
from .gen_toc import NavPoint, gen_toc


def generate_epub(
    epub_data: EpubData,
    epub_file_path: PathLike,
    lan: Literal["zh", "en"] = "zh",
    table_render: TableRender = TableRender.HTML,
    latex_render: LaTeXRender = LaTeXRender.MATHML,
    assert_not_aborted: Callable[[], None] = lambda: None,
) -> None:
    i18n = I18N(lan)
    template = Template()
    epub_file_path = Path(epub_file_path)

    # Generate navigation points from TOC structure
    has_cover = epub_data.cover_image_path is not None
    nav_points = gen_toc(epub_data=epub_data, has_cover=has_cover)

    epub_file_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(epub_file_path, "w") as file:
        context = Context(
            file=file,
            template=template,
            table_render=table_render,
            latex_render=latex_render,
        )
        file.writestr(
            zinfo_or_arcname="mimetype",
            data=template.render("mimetype").encode("utf-8"),
        )
        assert_not_aborted()

        _write_chapters_from_data(
            context=context,
            i18n=i18n,
            nav_points=nav_points,
            epub_data=epub_data,
            latex_render=latex_render,
            assert_not_aborted=assert_not_aborted,
        )
        nav_xhtml = gen_nav(
            template=template,
            i18n=i18n,
            epub_data=epub_data,
            nav_points=nav_points,
            has_cover=has_cover,
        )
        file.writestr(
            zinfo_or_arcname="OEBPS/nav.xhtml",
            data=nav_xhtml.encode("utf-8"),
        )
        assert_not_aborted()

        _write_basic_files(
            context=context,
            i18n=i18n,
            epub_data=epub_data,
            nav_points=nav_points,
        )
        assert_not_aborted()

        _write_assets_from_data(
            context=context,
            i18n=i18n,
            epub_data=epub_data,
        )

def _write_assets_from_data(
    context: Context,
    i18n: I18N,
    epub_data: EpubData,
):
    context.file.writestr(
        zinfo_or_arcname="OEBPS/styles/style.css",
        data=context.template.render("style.css").encode("utf-8"),
    )
    if epub_data.cover_image_path:
        context.file.writestr(
            zinfo_or_arcname="OEBPS/Text/cover.xhtml",
            data=context.template.render(
                template="cover.xhtml",
                i18n=i18n,
            ).encode("utf-8"),
        )
        if epub_data.cover_image_path:
            context.file.write(
                filename=epub_data.cover_image_path,
                arcname="OEBPS/assets/cover.png",
            )

def _write_chapters_from_data(
    context: Context,
    i18n: I18N,
    nav_points: list[NavPoint],
    epub_data: EpubData,
    latex_render: LaTeXRender,
    assert_not_aborted: Callable[[], None],
):
    if epub_data.get_head is not None:
        chapter = epub_data.get_head()
        data = generate_chapter(context, chapter, i18n)
        context.file.writestr(
            zinfo_or_arcname="OEBPS/Text/head.xhtml",
            data=data.encode("utf-8"),
        )
        if latex_render == LaTeXRender.MATHML and _chapter_has_formula(chapter):
            context.mark_chapter_has_mathml("head.xhtml")
        assert_not_aborted()

    for nav_point in nav_points:
        if nav_point.get_chapter is not None:
            chapter = nav_point.get_chapter()
            data = generate_chapter(context, chapter, i18n)
            context.file.writestr(
                zinfo_or_arcname="OEBPS/Text/" + nav_point.file_name,
                data=data.encode("utf-8"),
            )
            if latex_render == LaTeXRender.MATHML and _chapter_has_formula(chapter):
                context.mark_chapter_has_mathml(nav_point.file_name)
            assert_not_aborted()


def _chapter_has_formula(chapter) -> bool:
    for element in chapter.elements:
        if isinstance(element, Formula):
            return True
    return False

def _write_basic_files(
    context: Context,
    i18n: I18N,
    epub_data: EpubData,
    nav_points: list[NavPoint],
):
    meta = epub_data.meta
    has_cover = epub_data.cover_image_path is not None
    has_head_chapter = epub_data.get_head is not None

    context.file.writestr(
        zinfo_or_arcname="META-INF/container.xml",
        data=context.template.render("container.xml").encode("utf-8"),
    )
    isbn = (meta.isbn if meta else None) or str(uuid4())
    if meta and meta.modified:
        modified_timestamp = meta.modified.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        modified_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    chapters_with_mathml = {
        nav_point.file_name
        for nav_point in nav_points
        if context.chapter_has_mathml(nav_point.file_name)
    }
    content = context.template.render(
        template="content.opf",
        meta=meta,
        i18n=i18n,
        ISBN=isbn,
        modified_timestamp=modified_timestamp,
        nav_points=nav_points,
        has_head_chapter=has_head_chapter,
        has_cover=has_cover,
        asset_files=context.used_files,
        chapters_with_mathml=chapters_with_mathml,
    )
    context.file.writestr(
        zinfo_or_arcname="OEBPS/content.opf",
        data=content.encode("utf-8"),
    )
