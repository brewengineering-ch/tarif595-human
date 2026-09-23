import hashlib
import time
import uuid
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from app.schemas import InvoiceData

jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def generate_document_id() -> str:
    """Generate a standard Tarif 595 document identification string:

    <unique_id> / <timestamp> / <hash>
    """
    now = datetime.now()
    ts_str = now.strftime("%d.%m.%Y %H:%M:%S")
    raw_id = f"176{int(time.time())}"
    doc_hash = hashlib.sha256(f"{raw_id}{ts_str}".encode()).hexdigest()[:32]
    return f"{raw_id} / {ts_str} / {doc_hash}"


def build_general_invoice_xml(data: InvoiceData, doc_id: str) -> str:
    """Build a minimal valid XML document conforming to generalInvoiceRequest_500.xsd."""
    now = datetime.now()
    service_date_iso = data.service_date.strftime("%Y-%m-%d")

    template = jinja_env.get_template("tarif595_invoice.xml")
    return template.render(
        data=data,
        guid=uuid.uuid4().hex,
        request_timestamp=str(int(time.time())),
        request_id=doc_id.split("/")[0].strip(),
        now_iso=now.strftime("%Y-%m-%dT%H:%M:%S"),
        service_date_iso=service_date_iso,
        service_datetime_iso=f"{service_date_iso}T00:00:00",
        clean_gln=data.company_gln.replace(" ", ""),
        clean_iban=data.company_iban.replace(" ", ""),
        clean_ssn=data.client_ssn.replace(".", "").replace(" ", ""),
    )
