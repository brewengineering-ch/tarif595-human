import base64
import io
from qrbill.bill import QRBill
from app.schemas import InvoiceData


def generate_qr_bill_svg_data_uri(data: InvoiceData) -> str:
    bill = QRBill(
        account=data.company_iban.replace(" ", ""),
        creditor={
            "name": data.company_name,
            "line1": data.company_street,
            "line2": f"{data.company_zip_code} {data.company_city}",
            "country": "CH",
        },
        debtor={
            "name": f"{data.client_first_name} {data.client_last_name}",
            "line1": data.client_street,
            "line2": f"{data.client_zip_code} {data.client_city}",
            "country": "CH",
        },
        amount=f"{data.service_amount:.2f}",
        currency="CHF",
        additional_information=data.service_description,
    )

    buffer = io.StringIO()
    # full_page=False generates exactly the 210x105mm bottom slip with standard fonts and layout
    bill.as_svg(file_out=buffer, full_page=False)
    encoded = base64.b64encode(buffer.getvalue().encode("utf-8")).decode("utf-8")

    return f"data:image/svg+xml;base64,{encoded}"