import base64
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from qrcode.image.svg import SvgPathImage
from qrbill.bill import QRBill
from app.schemas import InvoiceData


def _to_svg_uri(svg_string: str | bytes) -> str:
    """Helper to wrap raw SVG in a base64 Data URI."""
    if isinstance(svg_string, str):
        svg_string = svg_string.encode("utf-8")
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_string).decode('utf-8')}"


def generate_qr_svg_uri(payload: str, box_size: int = 10, border: int = 0) -> str:
    """1. Generate standard QR SVG (used for the top-right 2D matrix code)."""
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_M, box_size=box_size, border=border
    )
    qr.add_data(payload)
    qr.make(fit=True)

    buf = io.BytesIO()
    qr.make_image(image_factory=SvgPathImage).save(buf)
    return _to_svg_uri(buf.getvalue())


def generate_qr_bill_svg_uri(data: InvoiceData) -> str:
    """2. Generate official Swiss QR-Bill (bottom slip via 3rd-party qrbill library)."""
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
    buf = io.StringIO()
    bill.as_svg(file_out=buf, full_page=False)
    return _to_svg_uri(buf.getvalue())


def generate_chunked_qr_codes(
    payload: str, max_chunk_size: int = 1200
) -> list[dict[str, str]]:
    """3. Generate chunked QR codes for large machine-readable XML payloads."""
    num_chunks = (len(payload) + max_chunk_size - 1) // max_chunk_size or 1
    codes = []

    for i in range(num_chunks):
        chunk = payload[i * max_chunk_size : (i + 1) * max_chunk_size]
        chunk_data = f"{i + 1}/{num_chunks}:{chunk}" if num_chunks > 1 else chunk
        codes.append(
            {
                "index": i + 1,
                "total": num_chunks,
                "label": f"Teil {i + 1} von {num_chunks}",
                "svg_uri": generate_qr_svg_uri(chunk_data, box_size=8, border=2),
            }
        )

    return codes
