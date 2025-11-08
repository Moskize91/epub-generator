import re
from xml.etree.ElementTree import Element, tostring

_EPUB_NS = "http://www.idpf.org/2007/ops"


def set_epub_type(element: Element, epub_type: str) -> None:
    element.set(f"{{{_EPUB_NS}}}type", epub_type)

def serialize_element(element: Element) -> str:
    xml_string = tostring(element, encoding="unicode")
    xml_string = xml_string.replace(f"{{{_EPUB_NS}}}", "epub:")
    ns_pattern = r'xmlns:(ns\d+)="' + re.escape(_EPUB_NS) + r'"'
    matches = re.findall(ns_pattern, xml_string)
    for ns_prefix in matches:
        xml_string = xml_string.replace(f' xmlns:{ns_prefix}="{_EPUB_NS}"', "")
        xml_string = xml_string.replace(f"{ns_prefix}:", "epub:")
    return xml_string
