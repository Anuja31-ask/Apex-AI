from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    filename: str
    equipment: str
    document_type: str
    revision: str
    trust_status: str
    sha256: str
    page_count: int

    def as_payload(self) -> dict[str, str | int]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as document:
        for block in iter(lambda: document.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def infer_document_type(filename: str) -> str:
    name = filename.lower()
    if "inspection" in name:
        return "inspection"
    if "manual" in name:
        return "manual"
    if "maintenance" in name:
        return "maintenance"
    if "sop" in name:
        return "sop"
    if "safety" in name:
        return "safety"
    if "vibration" in name or "guideline" in name:
        return "standard"
    return "unknown"


def build_metadata(path: Path, page_count: int, trust_status: str = "trusted") -> DocumentMetadata:
    document_type = infer_document_type(path.name)
    prefix = {"inspection": "INS", "manual": "MAN", "maintenance": "MNT", "sop": "SOP", "safety": "SAFE", "standard": "STD"}.get(document_type, "DOC")
    return DocumentMetadata(
        document_id=f"{prefix}-P101-001",
        filename=path.name,
        equipment="P-101",
        document_type=document_type,
        revision="1.0",
        trust_status=trust_status,
        sha256=sha256_file(path),
        page_count=page_count,
    )
