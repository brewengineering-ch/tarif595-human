import base64
import io
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from qrcode.image.svg import SvgPathImage

from app.schemas import InvoiceData

NS = "http://www.forum-datenaustausch.ch/invoice"
ET.register_namespace("", NS)


def build_general_invoice_xml(data: InvoiceData, doc_id: str) -> str:
    """Build a minimal valid XML document conforming to generalInvoiceRequest_500.xsd."""
    now = datetime.now()
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%S")
    service_date_iso = data.service_date.strftime("%Y-%m-%d")
    service_datetime_iso = f"{service_date_iso}T00:00:00"
    clean_gln = data.company_gln.replace(" ", "")
    clean_iban = data.company_iban.replace(" ", "")
    clean_ssn = data.client_ssn.replace(".", "").replace(" ", "")

    # Root <request>
    req = ET.Element(
        f"{{{NS}}}request",
        {
            "language": "de",
            "modus": "production",
            "guid": uuid.uuid4().hex,
        },
    )

    # 1. <processing>
    proc = ET.SubElement(req, f"{{{NS}}}processing")
    ET.SubElement(
        proc,
        f"{{{NS}}}transport",
        {
            "from": clean_gln,
            "to": "2000000000000",
        },
    )

    # 2. <payload>
    payload = ET.SubElement(
        req,
        f"{{{NS}}}payload",
        {
            "request_type": "invoice",
            "request_subtype": "normal",
        },
    )

    # 2.1 <invoice>
    ET.SubElement(
        payload,
        f"{{{NS}}}invoice",
        {
            "request_timestamp": str(int(time.time())),
            "request_date": now_iso,
            "request_id": doc_id.split("/")[0].strip(),
        },
    )

    # 2.2 <body>
    body = ET.SubElement(
        payload,
        f"{{{NS}}}body",
        {
            "role": "naturopathictherapist",
            "place": "practice",
        },
    )

    # <prolog>
    prolog = ET.SubElement(body, f"{{{NS}}}prolog")
    ET.SubElement(prolog, f"{{{NS}}}generator", {"name": "tarif595-human", "version": "1"})

    # <tiers_garant>
    tg = ET.SubElement(body, f"{{{NS}}}tiers_garant")

    # <billers>
    billers = ET.SubElement(tg, f"{{{NS}}}billers")
    biller_gln = ET.SubElement(billers, f"{{{NS}}}biller_gln", {"gln": clean_gln})
    company = ET.SubElement(biller_gln, f"{{{NS}}}company")
    ET.SubElement(company, f"{{{NS}}}companyname").text = data.company_name
    b_postal = ET.SubElement(company, f"{{{NS}}}postal")
    ET.SubElement(b_postal, f"{{{NS}}}street").text = data.company_street
    ET.SubElement(b_postal, f"{{{NS}}}zip").text = data.company_zip_code
    ET.SubElement(b_postal, f"{{{NS}}}city").text = data.company_city

    # <debitor>
    debitor = ET.SubElement(tg, f"{{{NS}}}debitor", {"gln": clean_gln})
    d_company = ET.SubElement(debitor, f"{{{NS}}}company")
    ET.SubElement(d_company, f"{{{NS}}}companyname").text = data.company_name
    d_postal = ET.SubElement(d_company, f"{{{NS}}}postal")
    ET.SubElement(d_postal, f"{{{NS}}}street").text = data.company_street
    ET.SubElement(d_postal, f"{{{NS}}}zip").text = data.company_zip_code
    ET.SubElement(d_postal, f"{{{NS}}}city").text = data.company_city

    # <providers>
    providers = ET.SubElement(tg, f"{{{NS}}}providers")
    prov_gln = ET.SubElement(providers, f"{{{NS}}}provider_gln", {"gln": clean_gln, "gln_location": clean_gln})
    p_company = ET.SubElement(prov_gln, f"{{{NS}}}company")
    ET.SubElement(p_company, f"{{{NS}}}companyname").text = data.company_name
    p_postal = ET.SubElement(p_company, f"{{{NS}}}postal")
    ET.SubElement(p_postal, f"{{{NS}}}street").text = data.company_street
    ET.SubElement(p_postal, f"{{{NS}}}zip").text = data.company_zip_code
    ET.SubElement(p_postal, f"{{{NS}}}city").text = data.company_city

    # <patient>
    patient = ET.SubElement(
        tg,
        f"{{{NS}}}patient",
        {
            "gender": data.client_gender,
            "sex": "female" if data.client_gender == "female" else "male",
            "birthdate": data.client_birthdate.strftime("%Y-%m-%d"),
            "ssn": clean_ssn,
        },
    )
    person = ET.SubElement(patient, f"{{{NS}}}person")
    ET.SubElement(person, f"{{{NS}}}familyname").text = data.client_last_name
    ET.SubElement(person, f"{{{NS}}}givenname").text = data.client_first_name
    pt_postal = ET.SubElement(person, f"{{{NS}}}postal")
    ET.SubElement(pt_postal, f"{{{NS}}}street").text = data.client_street
    ET.SubElement(pt_postal, f"{{{NS}}}zip").text = data.client_zip_code
    ET.SubElement(pt_postal, f"{{{NS}}}city").text = data.client_city

    # <guarantor>
    guarantor = ET.SubElement(tg, f"{{{NS}}}guarantor")
    g_person = ET.SubElement(guarantor, f"{{{NS}}}person")
    ET.SubElement(g_person, f"{{{NS}}}familyname").text = data.client_last_name
    ET.SubElement(g_person, f"{{{NS}}}givenname").text = data.client_first_name
    g_postal = ET.SubElement(g_person, f"{{{NS}}}postal")
    ET.SubElement(g_postal, f"{{{NS}}}street").text = data.client_street
    ET.SubElement(g_postal, f"{{{NS}}}zip").text = data.client_zip_code
    ET.SubElement(g_postal, f"{{{NS}}}city").text = data.client_city

    # <partners>
    ET.SubElement(tg, f"{{{NS}}}partners")

    # <balance>
    balance = ET.SubElement(
        tg,
        f"{{{NS}}}balance",
        {
            "currency": "CHF",
            "amount": f"{data.service_amount:.2f}",
            "amount_due": f"{data.service_amount:.2f}",
        },
    )
    vat = ET.SubElement(balance, f"{{{NS}}}vat", {"vat": "0.0"})
    ET.SubElement(
        vat,
        f"{{{NS}}}vat_rate",
        {
            "vat_rate": "0",
            "amount": f"{data.service_amount:.2f}",
            "vat": "0.0",
        },
    )

    # <esrQRRed>
    esr = ET.SubElement(body, f"{{{NS}}}esrQRRed", {"iban": clean_iban, "subtype": "esrQRRed"})
    creditor = ET.SubElement(esr, f"{{{NS}}}creditor")
    c_company = ET.SubElement(creditor, f"{{{NS}}}company")
    ET.SubElement(c_company, f"{{{NS}}}companyname").text = data.company_name
    c_postal = ET.SubElement(c_company, f"{{{NS}}}postal")
    ET.SubElement(c_postal, f"{{{NS}}}street").text = data.company_street
    ET.SubElement(c_postal, f"{{{NS}}}zip").text = data.company_zip_code
    ET.SubElement(c_postal, f"{{{NS}}}city").text = data.company_city

    # <law>
    ET.SubElement(body, f"{{{NS}}}law", {"type": "VVG"})

    # <treatment>
    ET.SubElement(
        body,
        f"{{{NS}}}treatment",
        {
            "date_begin": service_date_iso,
            "date_end": service_date_iso,
            "canton": data.canton,
            "treatment": "ambulatory",
            "reason": "disease",
        },
    )

    # <services>
    services = ET.SubElement(body, f"{{{NS}}}services")
    ET.SubElement(
        services,
        f"{{{NS}}}service",
        {
            "record_id": "1",
            "tariff_type": "595",
            "code": data.tariff_code,
            "name": data.service_description,
            "quantity": "1.0",
            "date_begin": service_datetime_iso,
            "provider_id": clean_gln,
            "responsible_id": clean_gln,
            "unit": "1.0",
            "unit_factor": "1.0",
            "amount": f"{data.service_amount:.2f}",
            "vat_rate": "0",
        },
    )

    # Return XML with declaration
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(req, encoding="unicode")


def generate_machine_qr_codes(xml_content: str, max_chunk_size: int = 1200) -> list[dict[str, str]]:
    """Chunk the XML payload if necessary and generate SVG Data URIs for each QR code."""
    total_length = len(xml_content)
    num_chunks = (total_length + max_chunk_size - 1) // max_chunk_size
    codes = []

    for i in range(num_chunks):
        chunk = xml_content[i * max_chunk_size : (i + 1) * max_chunk_size]
        payload = f"{i + 1}/{num_chunks}:{chunk}" if num_chunks > 1 else chunk

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        img = qr.make_image(image_factory=SvgPathImage)
        buf = io.BytesIO()
        img.save(buf)

        uri = f"data:image/svg+xml;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        codes.append(
            {
                "index": i + 1,
                "total": num_chunks,
                "label": f"Teil {i + 1} von {num_chunks}",
                "svg_uri": uri,
            }
        )

    return codes