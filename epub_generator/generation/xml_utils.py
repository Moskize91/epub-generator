import re
from xml.etree.ElementTree import Element, tostring

_EPUB_NS = "http://www.idpf.org/2007/ops"
_MATHML_NS = "http://www.w3.org/1998/Math/MathML"


def set_epub_type(element: Element, epub_type: str) -> None:
    element.set(f"{{{_EPUB_NS}}}type", epub_type)

def serialize_element(element: Element) -> str:
    xml_string = tostring(element, encoding="unicode")
    for prefix, namespace_uri, keep_xmlns in (
        ("epub", _EPUB_NS, False),  # EPUB namespace: remove xmlns (declared at root)
        ("m", _MATHML_NS, True),     # MathML namespace: keep xmlns with clean prefix
    ):
        xml_string = xml_string.replace(f"{{{namespace_uri}}}", f"{prefix}:")
        pattern = r"xmlns:(ns\d+)=\"" + re.escape(namespace_uri) + r"\""
        matches = re.findall(pattern, xml_string)

        for ns_prefix in matches:
            if keep_xmlns:
                xml_string = xml_string.replace(
                    f" xmlns:{ns_prefix}=\"{namespace_uri}\"",
                    f" xmlns:{prefix}=\"{namespace_uri}\""
                )
            else:
                xml_string = xml_string.replace(f" xmlns:{ns_prefix}=\"{namespace_uri}\"", "")
            xml_string = xml_string.replace(f"{ns_prefix}:", f"{prefix}:")

    return xml_string

def indent(elem: Element, level: int = 0) -> Element:
    indent_str = "  " * level
    next_indent_str = "  " * (level + 1)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = "\n" + next_indent_str
        for i, child in enumerate(elem):
            indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                if i == len(elem) - 1:
                    child.tail = "\n" + indent_str
                else:
                    child.tail = "\n" + next_indent_str
    return elem
