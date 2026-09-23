from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from weasyprint import HTML
from app.schemas import InvoiceData

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

@app.post("/form/generate-pdf")
def generate_pdf_from_form(
    data: Annotated[InvoiceData, Form()]
):
    # Render the HTML template with the form values
    rendered_html = templates.get_template("invoice.html").render(
        **data.model_dump()
    )

    # Convert the rendered HTML to PDF bytes
    pdf_bytes = HTML(string=rendered_html).write_pdf(
        stylesheets=["app/static/pico.min.css"]
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="tarif595-invoice.pdf"'
        },
    )