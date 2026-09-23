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


@app.post("/form/generate-pdf")
async def generate_pdf_from_form(request: Request):
    form_data = await request.form()
    action = str(form_data.get("action", "all"))
    data = InvoiceData.model_validate(dict(form_data))

    doc_id = generate_document_id()
    code_2d_uri = generate_qr_svg_uri(doc_id)

    def make_invoice() -> bytes:
        return render_pdf(
            "invoice.html",
            {**data.model_dump(), "qr_svg_uri": generate_qr_bill_svg_uri(data)},
            stylesheets=["app/static/pico.min.css"],
        )

    def make_reimbursement() -> bytes:
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

    def make_machine() -> bytes:
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

    generators = {
        "invoice": (make_invoice, f"rechnung-{data.client_last_name}.pdf"),
        "reimbursement": (
            make_reimbursement,
            f"rueckforderungsbeleg-{data.client_last_name}.pdf",
        ),
        "machine": (make_machine, f"machine-codes-{data.client_last_name}.pdf"),
    }

    if action in generators:
        render_fn, filename = generators[action]
        pdf_bytes = render_fn()
    else:
        pdf_bytes = combine_pdfs([make_invoice(), make_reimbursement(), make_machine()])
        filename = f"tarif595-gesamtdokument-{data.client_last_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
