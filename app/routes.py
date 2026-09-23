from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from app.pdf import (
    create_combined_pdf,
    create_swiss_qr_invoice_pdf,
    create_tarif595_machine_pdf,
    create_tarif595_human_pdf,
    create_combined_pdf,
    pdf_response,
    templates,
)
from app.schemas import InvoiceData, Tarif595Data

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


GENERATORS = {
    "invoice": (create_swiss_qr_invoice_pdf, "invoice-{last_name}.pdf"),
    "tarif595_human": (create_tarif595_human_pdf, "tarif595-human-{last_name}.pdf"),
    "tarif595_machine": (
        create_tarif595_machine_pdf,
        "tarif595-machine-{last_name}.pdf",
    ),
}


@router.post("/form/generate-pdf", include_in_schema=False)
async def generate_pdf_from_form(request: Request):
    form_data = await request.form()
    action = str(form_data.get("action", "all"))
    if action == "invoice":
        data = InvoiceData.model_validate(dict(form_data))
    else:
        data = Tarif595Data.model_validate(dict(form_data))

    generator_func, filename_pattern = GENERATORS.get(
        action, (create_combined_pdf, "combined-{last_name}.pdf")
    )
    pdf = generator_func(data)
    filename = filename_pattern.format(last_name=data.client_last_name)
    return pdf_response(pdf, filename)


@router.post(
    "/api/pdf/invoice",
    response_class=Response,
    summary="Generate Invoice (QR-Bill)",
)
def api_generate_invoice(data: InvoiceData):
    pdf = create_swiss_qr_invoice_pdf(data)
    return pdf_response(pdf, f"invoice-{data.client_last_name}.pdf")


@router.post(
    "/api/pdf/tarif595_human",
    response_class=Response,
    summary="Generate Reimbursement Receipt (Rückforderungsbeleg)",
)
def api_generate_reimbursement(data: Tarif595Data):
    pdf = create_tarif595_human_pdf(data)
    return pdf_response(pdf, f"tarif595-human-{data.client_last_name}.pdf")


@router.post(
    "/api/pdf/tarif595_machine",
    response_class=Response,
    summary="Generate Machine QR-Codes (Tarif 595 XML)",
)
def api_generate_machine(data: Tarif595Data):
    pdf = create_tarif595_machine_pdf(data)
    return pdf_response(pdf, f"tarif595-machine-{data.client_last_name}.pdf")


@router.post(
    "/api/pdf/combined",
    response_class=Response,
    summary="Generate Combined Document (All 3 Documents)",
)
def api_generate_combined(data: Tarif595Data):
    pdf = create_combined_pdf(data)
    return pdf_response(pdf, f"combined-{data.client_last_name}.pdf")
