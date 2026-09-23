from pydantic import BaseModel, ConfigDict
from datetime import date


class InvoiceData(BaseModel):
    # Company / Rechnungssteller
    company_name: str
    company_street: str
    company_zip_code: str
    company_city: str
    company_iban: str
    company_gln: str = "7601000000000"  # 13-digit Swiss Healthcare GLN

    # Client / Patient
    client_first_name: str
    client_last_name: str
    client_street: str
    client_zip_code: str
    client_city: str
    client_birthdate: date = date(1980, 1, 1)
    client_ssn: str = "756.1234.5678.90"  # AHV / NAVS13 number
    client_gender: str = "female"  # male, female, diverse
    canton: str = "ZH"  # 2-letter canton code

    # Service / Tarif 595
    service_date: date
    service_description: str
    service_amount: float
    tariff_code: str = "1001"  # Standard Tarif 595 code

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_name": "Praxis Dr. Muster",
                "company_street": "Bahnhofstrasse 1",
                "company_zip_code": "8001",
                "company_city": "Zürich",
                "company_iban": "CH9300762011623852957",
                "company_gln": "7601000000000",
                "client_first_name": "Hans",
                "client_last_name": "Muster",
                "client_street": "Musterstrasse 10",
                "client_zip_code": "8000",
                "client_city": "Zürich",
                "client_birthdate": "1980-01-01",
                "client_ssn": "756.1234.5678.90",
                "client_gender": "female",
                "canton": "ZH",
                "service_date": "2026-09-22",
                "service_description": "Tarif 595 Consultation",
                "service_amount": 120.00,
                "tariff_code": "1001",
            }
        }
    )
