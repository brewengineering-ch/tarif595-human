import io
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from weasyprint import HTML
from pypdf import PdfWriter

from app.schemas import InvoiceData
from app.tarif595 import generate_document_id, build_general_invoice_xml
from app.qr import (
    generate_qr_bill_svg_uri,
    generate_qr_svg_uri,
    generate_chunked_qr_codes,
)

app = FastAPI(
    title="Tarif 595 PDF Generator API",
    description="API and UI for generating Swiss Healthcare Tarif 595 invoices, reimbursement receipts, and 2D QR-code documents.",
    version="1.0.0",
)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


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


# --- Reusable PDF Generation Helpers ---

def create_invoice_pdf(data: InvoiceData) -> bytes:
    return render_pdf(
        "invoice.html",
        {**data.model_dump(), "qr_svg_uri": generate_qr_bill_svg_uri(data)},
        stylesheets=["app/static/pico.min.css"],
    )


def create_reimbursement_pdf(data: InvoiceData, doc_id: str | None = None) -> bytes:
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


def create_machine_pdf(data: InvoiceData, doc_id: str | None = None) -> bytes:
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


def create_combined_pdf(data: InvoiceData) -> bytes:
    doc_id = generate_document_id()
    return combine_pdfs([
        create_invoice_pdf(data),
        create_reimbursement_pdf(data, doc_id=doc_id),
        create_machine_pdf(data, doc_id=doc_id),
    ])


def pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- REST API Endpoints ---

PDF_RESPONSES = {
    200: {
        "content": {"application/pdf": {}},
        "description": "Returns the generated PDF file.",
    }
}


@app.post(
    "/api/pdf/invoice",
    response_class=Response,
    responses=PDF_RESPONSES,
    summary="1. Generate Invoice (QR-Bill)",
    tags=["PDF Generation API"],
)
def api_generate_invoice(data: InvoiceData):
    """Generates the patient invoice with Swiss QR-Bill."""
    pdf = create_invoice_pdf(data)
    return pdf_response(pdf, f"rechnung-{data.client_last_name}.pdf")


@app.post(
    "/api/pdf/reimbursement",
    response_class=Response,
    responses=PDF_RESPONSES,
    summary="2. Generate Reimbursement Receipt (Rückforderungsbeleg)",
    tags=["PDF Generation API"],
)
def api_generate_reimbursement(data: InvoiceData):
    """Generates the human-readable Tarif 595 reimbursement receipt."""
    pdf = create_reimbursement_pdf(data)
    return pdf_response(pdf, f"rueckforderungsbeleg-{data.client_last_name}.pdf")


@app.post(
    "/api/pdf/machine",
    response_class=Response,
    responses=PDF_RESPONSES,
    summary="3. Generate Machine QR-Codes (Tarif 595 XML)",
    tags=["PDF Generation API"],
)
def api_generate_machine(data: InvoiceData):
    """Generates the page with chunked 2D QR codes containing generalInvoiceRequest XML."""
    pdf = create_machine_pdf(data)
    return pdf_response(pdf, f"machine-codes-{data.client_last_name}.pdf")


@app.post(
    "/api/pdf/combined",
    response_class=Response,
    responses=PDF_RESPONSES,
    summary="4. Generate Combined Document (All 3 Documents)",
    tags=["PDF Generation API"],
)
def api_generate_combined(data: InvoiceData):
    """Generates a combined PDF containing the invoice, reimbursement receipt, and machine QR codes."""
    pdf = create_combined_pdf(data)
    return pdf_response(pdf, f"tarif595-gesamtdokument-{data.client_last_name}.pdf")


# --- Form Endpoint (HTML UI) ---

@app.post("/form/generate-pdf", include_in_schema=False)
async def generate_pdf_from_form(request: Request):
    form_data = await request.form()
    action = str(form_data.get("action", "all"))
    data = InvoiceData.model_validate(dict(form_data))

    if action == "invoice":
        return pdf_response(create_invoice_pdf(data), f"rechnung-{data.client_last_name}.pdf")
    elif action == "reimbursement":
        return pdf_response(create_reimbursement_pdf(data), f"rueckforderungsbeleg-{data.client_last_name}.pdf")
    elif action == "machine":
        return pdf_response(create_machine_pdf(data), f"machine-codes-{data.client_last_name}.pdf")
    else:
        return pdf_response(create_combined_pdf(data), f"tarif595-gesamtdokument-{data.client_last_name}.pdf")
