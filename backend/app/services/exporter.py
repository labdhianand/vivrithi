from __future__ import annotations

from io import BytesIO

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_cam_docx(company_name: str, sections: list[dict]) -> bytes:
    document = Document()
    document.add_heading("Credit Appraisal Memo", level=0)
    document.add_heading(company_name, level=1)
    for section in sections:
        document.add_heading(section["title"], level=2)
        for line in section["content_markdown"].splitlines():
            document.add_paragraph(line)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def export_cam_pdf(company_name: str, sections: list[dict]) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, f"Credit Appraisal Memo - {company_name}")
    y -= 30
    pdf.setFont("Helvetica", 10)
    for section in sections:
        if y < 100:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, section["title"])
        y -= 18
        pdf.setFont("Helvetica", 10)
        for line in section["content_markdown"].splitlines():
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y, line[:120])
            y -= 14
        y -= 10
    pdf.save()
    return buffer.getvalue()

