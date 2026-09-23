import io
from fastapi import Response
from fastapi.templating import Jinja2Templates
from pypdf import PdfWriter
from weasyprint import HTML

from app.qr import (
    generate_chunked_qr_codes,
    generate_qr_bill_svg_uri,
    generate_qr_svg_uri,
)
from app.schemas import InvoiceData, Tarif595Data
from app.tarif595 import build_general_invoice_xml, generate_document_id

templates = Jinja2Templates(directory="app/templates")


def render_pdf(
    template_name: str, context: dict, stylesheets: list[str] | None = None
) -> bytes:
    html_text = templates.get_template(template_name).render(context)
    pdf_bytes = HTML(string=html_text).write_pdf(stylesheets=stylesheets)
    assert pdf_bytes is not None
    return pdf_bytes


def combine_pdfs(pdf_list: list[bytes]) -> bytes:
    writer = PdfWriter()
    for pdf_data in pdf_list:
        writer.append(io.BytesIO(pdf_data))
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def create_swiss_qr_invoice_pdf(data: InvoiceData) -> bytes:
    return render_pdf(
        "invoice.html",
        {**data.model_dump(), "qr_svg_uri": generate_qr_bill_svg_uri(data)},
        stylesheets=["app/static/pico.min.css"],
    )


def create_tarif595_human_pdf(data: Tarif595Data, doc_id: str | None = None) -> bytes:
    if doc_id is None:
        doc_id = generate_document_id()
    code_2d_uri = generate_qr_svg_uri(doc_id)
    services = [
        {
            "date": data.service_date.strftime("%d.%m.%Y"),
            "code": data.tariff_code,
            "quantity": 1,
            "amount": data.service_amount,
            "description": data.service_description,
        }
    ]
    return render_pdf(
        "tarif595_human.html",
        {
            **data.model_dump(),
            "doc_id": doc_id,
            "code_2d_uri": code_2d_uri,
            "services": services,
            "total_amount": data.service_amount,
        },
    )


def create_tarif595_machine_pdf(data: Tarif595Data, doc_id: str | None = None) -> bytes:
    if doc_id is None:
        doc_id = generate_document_id()
    code_2d_uri = generate_qr_svg_uri(doc_id)
    xml_content = build_general_invoice_xml(data, doc_id)
    return render_pdf(
        "tarif595_machine.html",
        {
            **data.model_dump(),
            "doc_id": doc_id,
            "code_2d_uri": code_2d_uri,
            "qr_codes": generate_chunked_qr_codes(xml_content),
        },
    )


def create_combined_pdf(data: Tarif595Data) -> bytes:
    doc_id = generate_document_id()
    return combine_pdfs([
        create_swiss_qr_invoice_pdf(data),
        create_tarif595_human_pdf(data, doc_id=doc_id),
        create_tarif595_machine_pdf(data, doc_id=doc_id),
    ])


def pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )