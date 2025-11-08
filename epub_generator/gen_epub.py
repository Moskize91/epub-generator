from os import PathLike
from pathlib import Path
from typing import Literal
from uuid import uuid4
from zipfile import ZipFile

from .context import Context, Template
from .gen_chapter import generate_chapter
from .gen_toc import NavPoint, gen_toc
from .i18n import I18N
from .options import LaTeXRender, TableRender
from .types import BookMeta, EpubData


def generate_epub(
    epub_data: EpubData,
    epub_file_path: PathLike,
    lan: Literal["zh", "en"] = "zh",
    table_render: TableRender = TableRender.HTML,
    latex_render: LaTeXRender = LaTeXRender.MATHML,
) -> None:
    i18n = I18N(lan)
    template = Template()
    epub_file_path = Path(epub_file_path)

    toc_ncx, nav_points = gen_toc(
        template=template,
        i18n=i18n,
        epub_data=epub_data,
    )
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
        file.writestr(
            zinfo_or_arcname="OEBPS/toc.ncx",
            data=toc_ncx.encode("utf-8"),
        )
        _write_chapters_from_data(
            context=context,
            i18n=i18n,
            nav_points=nav_points,
            epub_data=epub_data,
        )
        _write_basic_files(
            context=context,
            i18n=i18n,
            meta=epub_data.meta,
            nav_points=nav_points,
            has_cover=epub_data.cover_image_path is not None,
            has_head_chapter=epub_data.get_head is not None,
        )
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
):
    if epub_data.get_head is not None:
        chapter = epub_data.get_head()
        data = generate_chapter(context, chapter, i18n)
        context.file.writestr(
            zinfo_or_arcname="OEBPS/Text/head.xhtml",
            data=data.encode("utf-8"),
        )

    for nav_point in nav_points:
        if nav_point.get_chapter is not None:
            chapter = nav_point.get_chapter()
            data = generate_chapter(context, chapter, i18n)
            context.file.writestr(
                zinfo_or_arcname="OEBPS/Text/" + nav_point.file_name,
                data=data.encode("utf-8"),
            )

def _write_basic_files(
    context: Context,
    i18n: I18N,
    meta: BookMeta | None,
    nav_points: list[NavPoint],
    has_cover: bool,
    has_head_chapter: bool,
):
    context.file.writestr(
        zinfo_or_arcname="META-INF/container.xml",
        data=context.template.render("container.xml").encode("utf-8"),
    )
    isbn = (meta.isbn if meta else None) or str(uuid4())
    content = context.template.render(
        template="content.opf",
        meta=meta,
        i18n=i18n,
        ISBN=isbn,
        nav_points=nav_points,
        has_head_chapter=has_head_chapter,
        has_cover=has_cover,
        asset_files=context.used_files,
    )
    context.file.writestr(
        zinfo_or_arcname="OEBPS/content.opf",
        data=content.encode("utf-8"),
    )
