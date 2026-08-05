"""Small deterministic PDF writer for the generated credit memo."""

from __future__ import annotations

from northstar_credit_app.models import AnalysisResult


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_memo_pdf(result: AnalysisResult) -> bytes:
    lines = [
        "NORTHSTAR CREDIT MEMORANDUM",
        result.case.borrower.legal_name,
        f"Decision: {result.decision.outcome}",
        f"Internal grade: {result.scorecard.grade} ({result.scorecard.grade_label})",
        f"Score: {result.scorecard.score}",
        f"Requested minor units: {result.capacity.requested.amount_minor}",
        f"Recommended minor units: {result.capacity.recommended.amount_minor}",
        "",
        "Rationale",
        *result.decision.rationale,
        "",
        "Conditions",
        *result.decision.conditions,
        "",
        f"Input hash: {result.input_hash}",
        f"Policy: {result.policy_version} / {result.policy_hash[:12]}",
    ]
    commands = ["BT", "/F1 10 Tf", "54 750 Td", "13 TL"]
    for index, line in enumerate(lines[:48]):
        if index:
            commands.append("T*")
        commands.append(f"({_escape(line[:105])}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(pdf)
