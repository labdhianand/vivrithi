from __future__ import annotations

from .types import ParsedPage


def build_document_markdown(pages: list[ParsedPage]) -> str:
    sections: list[str] = []
    for page in pages:
        sections.append(f"<!-- PAGE {page.page_number} -->")
        sections.append(f"## Page {page.page_number}")
        sections.append(page.markdown.strip())
        sections.append("")
    return "\n".join(section for section in sections if section is not None)

