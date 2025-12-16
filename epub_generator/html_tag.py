from typing import Generator

from .types import Formula, HTMLTag, Mark


def search_content(content: list[str | Mark | Formula | HTMLTag]) -> Generator[str | Mark | Formula, None, None]:
    for child in content:
        if isinstance(child, HTMLTag):
            yield from search_content(child.content)
        else:
            yield child