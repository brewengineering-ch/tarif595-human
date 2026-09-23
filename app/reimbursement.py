import base64
import hashlib
import io
import time
from datetime import datetime
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from qrcode.image.svg import SvgPathImage


def generate_document_id() -> str:
    """Generate a standard Tarif 595 document identification string:

    <unique_id> / <timestamp> / <hash>
    """
    now = datetime.now()
    ts_str = now.strftime("%d.%m.%Y %H:%M:%S")
    raw_id = f"176{int(time.time())}"
    doc_hash = hashlib.sha256(f"{raw_id}{ts_str}".encode()).hexdigest()[:32]
    return f"{raw_id} / {ts_str} / {doc_hash}"


def generate_reimbursement_2d_code_svg(doc_id: str) -> str:
    """Generate the 2D matrix code (in top right corner) as SVG data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=0,
    )
    qr.add_data(doc_id)
    qr.make(fit=True)

    img = qr.make_image(image_factory=SvgPathImage)
    buffer = io.BytesIO()
    img.save(buffer)

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"