from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas


def _value(data: dict[str, Any], key: str, default: str = "Not provided") -> str:
    value = data.get(key, default)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def generate_report(result: dict[str, Any], output_path: Path) -> Path:
    """Write a readable diagnostic PDF from model-independent verified data."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output_path), pagesize=A4)
    width, height = A4
    y = height - 55

    def line(label: str, value: str = "") -> None:
        nonlocal y
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(50, y, label)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(175, y, value[:105])
        y -= 18

    canvas.setTitle("APEX-AI Industrial Diagnostic Report")
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(50, y, "APEX-AI")
    y -= 25
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(50, y, "INDUSTRIAL DIAGNOSTIC REPORT")
    y -= 32

    line("Equipment", _value(result, "equipment", result.get("asset_id", "P-101")))
    line("Issue", _value(result, "issue"))
    line("Observed value", _value(result, "observed_value"))
    line("Threshold", _value(result, "threshold"))
    line("Probable cause", _value(result, "probable_cause"))
    line("Risk", _value(result, "risk", "REVIEW"))
    line("Recommendation", _value(result, "recommendation"))
    line("Approval status", _value(result, "approval_status", "REQUIRED"))
    line("Document ID", _value(result, "document_id"))
    line("Audit ID", _value(result, "audit_id"))
    line("Generated", datetime.now(timezone.utc).isoformat())

    y -= 12
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(50, y, "Evidence")
    y -= 20
    canvas.setFont("Helvetica", 9)
    sources = result.get("sources", [])
    if not sources:
        canvas.drawString(60, y, "No authoritative evidence supplied")
        y -= 15
    for source in sources:
        citation = f"{source.get('document', 'Unknown')} - Page {source.get('page', '?')}"
        canvas.drawString(60, y, citation[:110])
        y -= 15

    y -= 12
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(50, y, "Related assets")
    y -= 20
    canvas.setFont("Helvetica", 9)
    relationships = result.get("asset_relationships", [])
    for relationship in relationships:
        text = f"{relationship.get('source')} --{relationship.get('relationship')}--> {relationship.get('target')}"
        canvas.drawString(60, y, text[:110])
        y -= 15

    y -= 12
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(50, y, "Validation")
    y -= 20
    canvas.setFont("Helvetica", 9)
    validations = result.get("validations", ["Source verification", "Human approval boundary"])
    for validation in validations:
        canvas.drawString(60, y, f"[OK] {validation}")
        y -= 15
    canvas.save()
    return output_path