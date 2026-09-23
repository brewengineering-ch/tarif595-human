import io
from typing import Annotated
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from weasyprint import HTML
from pypdf import PdfWriter

from app.schemas import InvoiceData
from app.qrbill import generate_qr_bill_svg_data_uri
from app.reimbursement import generate_document_id, generate_reimbursement_2d_code_svg
from app.xml import build_general_invoice_xml, generate_machine_qr_codes

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )

@app.get("/health")
def read_health():
    return {"status": "healthy"}

# --- PDF Rendering Helpers ---

def render_invoice_pdf(data: InvoiceData) -> bytes:
    qr_svg_uri = generate_qr_bill_svg_data_uri(data)
    html_text = templates.get_template("invoice.html").render(
        **data.model_dump(),
        qr_svg_uri=qr_svg_uri,
    )
    pdf_bytes = HTML(string=html_text).write_pdf(
        stylesheets=["app/static/pico.min.css"]
    )
    assert pdf_bytes is not None
    return pdf_bytes

def render_reimbursement_pdf(data: InvoiceData) -> bytes:
    doc_id = generate_document_id()
    code_2d_uri = generate_reimbursement_2d_code_svg(doc_id)
    
    services = [
        {
            "date": data.service_date.strftime("%d.%m.%Y"),
            "code": "1001",
            "quantity": 1,
            "amount": data.service_amount,
            "description": data.service_description,
        }
    ]
    
    html_text = templates.get_template("reimbursement.html").render(
        **data.model_dump(),
        doc_id=doc_id,
        code_2d_uri=code_2d_uri,
        services=services,
        total_amount=data.service_amount,
    )
    pdf_bytes = HTML(string=html_text).write_pdf()
    assert pdf_bytes is not None
    return pdf_bytes

def render_machine_pdf(data: InvoiceData) -> bytes:
    doc_id = generate_document_id()
    code_2d_uri = generate_reimbursement_2d_code_svg(doc_id)

    # 1. Build standard-compliant XML conforming to generalInvoiceRequest_500.xsd
    xml_content = build_general_invoice_xml(data, doc_id)

    # 2. Chunk XML into high-density 2D barcodes
    qr_codes = generate_machine_qr_codes(xml_content)

    # 3. Render HTML template to PDF
    html_text = templates.get_template("machine.html").render(
        **data.model_dump(),
        doc_id=doc_id,
        code_2d_uri=code_2d_uri,
        qr_codes=qr_codes,
    )
    pdf_bytes = HTML(string=html_text).write_pdf()
    assert pdf_bytes is not None
    return pdf_bytes

def combine_pdfs(pdf_list: list[bytes]) -> bytes:
    writer = PdfWriter()
    for pdf_data in pdf_list:
        writer.append(io.BytesIO(pdf_data))
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


# --- Form Handler ---

@app.post("/form/generate-pdf")
async def generate_pdf_from_form(
    request: Request,
):
    form_data = await request.form()
    action = form_data.get("action", "all")
    data = InvoiceData.model_validate(dict(form_data))
    
    if action == "invoice":
        pdf_bytes = render_invoice_pdf(data)
        filename = f"rechnung-{data.client_last_name}.pdf"
    elif action == "reimbursement":
        pdf_bytes = render_reimbursement_pdf(data)
        filename = f"rueckforderungsbeleg-{data.client_last_name}.pdf"
    elif action == "machine":
        pdf_bytes = render_machine_pdf(data)
        filename = f"machine-codes-{data.client_last_name}.pdf"
    else:
        inv_pdf = render_invoice_pdf(data)
        reimb_pdf = render_reimbursement_pdf(data)
        mach_pdf = render_machine_pdf(data)
        pdf_bytes = combine_pdfs([inv_pdf, reimb_pdf, mach_pdf])
        filename = f"tarif595-gesamtdokument-{data.client_last_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )