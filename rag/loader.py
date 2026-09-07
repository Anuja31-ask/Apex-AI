from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .metadata import DocumentMetadata, build_metadata


@dataclass(frozen=True)
class PageText:
    text: str
    page: int
    metadata: DocumentMetadata


def load_pdf(path: Path, trust_status: str = "trusted") -> list[PageText]:
    reader = PdfReader(str(path))
    metadata = build_metadata(path, len(reader.pages), trust_status)
    pages: list[PageText] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(PageText(text=text, page=page_number, metadata=metadata))
    return pages


def load_directory(directory: Path, trust_statuses: dict[str, str] | None = None) -> list[PageText]:
    statuses = trust_statuses or {}
    pages: list[PageText] = []
    for path in sorted(directory.glob("*.pdf")):
        pages.extend(load_pdf(path, statuses.get(path.name, "trusted")))
    return pages
