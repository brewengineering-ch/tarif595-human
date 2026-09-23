from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict

_INVOICE_EXAMPLE = {
    "company_name": "Muster AG",
    "company_street": "Bahnhofstrasse 1",
    "company_zip_code": "8001",
    "company_city": "Zürich",
    "company_iban": "CH9300762011623852957",
    "client_first_name": "Hans",
    "client_last_name": "Muster",
    "client_street": "Musterstrasse 10",
    "client_zip_code": "8000",
    "client_city": "Zürich",
    "service_date": "2026-09-22",
    "service_description": "Beratung / Dienstleistung",
    "service_amount": 120.00,
}

_TARIF595_EXAMPLE = {
    **_INVOICE_EXAMPLE,
    "company_name": "Praxis Dr. Muster",
    "company_gln": "7601000000000",
    "client_birthdate": "1980-01-01",
    "client_ssn": "756.1234.5678.90",
    "client_gender": "female",
    "canton": "ZH",
    "tariff_code": "1001",
    "service_description": "Tarif 595 Consultation",
}


class InvoiceData(BaseModel):
    # Company / Rechnungssteller
    company_name: str
    company_street: str
    company_zip_code: str
    company_city: str
    company_iban: str

    # Client / Debitor
    client_first_name: str
    client_last_name: str
    client_street: str
    client_zip_code: str
    client_city: str

    # Service / Payment
    service_date: date
    service_description: str
    service_amount: float

    model_config = ConfigDict(
        json_schema_extra={"example": _INVOICE_EXAMPLE}
    )


class Tarif595Data(InvoiceData):
    # Provider Healthcare ID
    company_gln: str = "7601000000000"

    # Patient Healthcare Details
    client_birthdate: date = date(1980, 1, 1)
    client_ssn: str = "756.1234.5678.90"
    client_gender: Literal["male", "female", "diverse"] = "female"
    canton: str = "ZH"

    # Tariff Code
    tariff_code: str = "1001"

    model_config = ConfigDict(
        json_schema_extra={"example": _TARIF595_EXAMPLE}
    )
