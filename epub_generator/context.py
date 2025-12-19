from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import cast
from zipfile import ZipFile

from jinja2 import Environment
from jinja2 import Template as JinjaTemplate

from .options import LaTeXRender, TableRender
from .template import create_env


@dataclass
class _AssetNode:
    file_name: str
    media_type: str
    content_hash: str

class Context:
    def __init__(
        self,
        file: ZipFile,
        template: "Template",
        table_render: TableRender,
        latex_render: LaTeXRender,
    ) -> None:
        self._file: ZipFile = file
        self._template: Template = template
        self._table_render: TableRender = table_render
        self._latex_render: LaTeXRender = latex_render
        self._path_to_node: dict[Path, _AssetNode] = {}  # source_path -> node
        self._hash_to_node: dict[str, _AssetNode] = {}  # content_hash -> node
        self._chapters_with_mathml: set[str] = set()  # Track chapters containing MathML

    @property
    def file(self) -> ZipFile:
        return self._file

    @property
    def template(self) -> "Template":
        return self._template

    @property
    def table_render(self) -> TableRender:
        return self._table_render

    @property
    def latex_render(self) -> LaTeXRender:
        return self._latex_render

    @property
    def used_files(self) -> list[tuple[str, str]]:
        nodes = list(self._hash_to_node.values())
        nodes.sort(key=lambda node: node.file_name)
        return [(node.file_name, node.media_type) for node in nodes]
    
    @property
    def chapters_with_mathml(self) -> set[str]:
        return self._chapters_with_mathml

    def mark_chapter_has_mathml(self, chapter_file_name: str) -> None:
        self._chapters_with_mathml.add(chapter_file_name)

    def use_asset(
        self,
        source_path: Path,
        media_type: str,
        file_ext: str,
    ) -> str:
        if source_path in self._path_to_node:
            return self._path_to_node[source_path].file_name

        if not source_path.exists():
            raise FileNotFoundError(f"Asset file not found: {source_path}")

        with open(source_path, "rb") as f:
            content = f.read()
        content_hash = _sha256_hash(content)

        if content_hash in self._hash_to_node:
            node = self._hash_to_node[content_hash]
            self._path_to_node[source_path] = node
            return node.file_name

        file_name = f"{content_hash}{file_ext}"
        node = _AssetNode(
            file_name=file_name,
            media_type=media_type,
            content_hash=content_hash,
        )
        self._path_to_node[source_path] = node
        self._hash_to_node[content_hash] = node
        self._file.write(
            filename=source_path,
            arcname="OEBPS/assets/" + file_name,
        )
        return file_name

    def add_asset(self, data: bytes, media_type: str, file_ext: str) -> str:
        content_hash = _sha256_hash(data)
        if content_hash in self._hash_to_node:
            return self._hash_to_node[content_hash].file_name

        file_name = f"{content_hash}{file_ext}"
        node = _AssetNode(
            file_name=file_name,
            media_type=media_type,
            content_hash=content_hash,
        )
        self._hash_to_node[content_hash] = node

        self._file.writestr(
            zinfo_or_arcname="OEBPS/assets/" + file_name,
            data=data,
        )
        return file_name

class Template:
    def __init__(self):
        templates_path = cast(Path, files("epub_generator")) / "data"
        self._env: Environment = create_env(templates_path)
        self._templates: dict[str, JinjaTemplate] = {}

    def render(self, template: str, **params) -> str:
        jinja_template: JinjaTemplate = self._template(template)
        return jinja_template.render(**params)

    def _template(self, name: str) -> JinjaTemplate:
        template = self._templates.get(name, None)
        if template is None:
            template = self._env.get_template(name)
            self._templates[name] = template
        return template

def _sha256_hash(data: bytes) -> str:
    hash256 = sha256()
    hash256.update(data)
    return hash256.hexdigest()