from pydantic import BaseModel
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
    client_gender: str = "female"         # male, female, diverse
    canton: str = "ZH"                    # 2-letter canton code

    # Service / Tarif 595
    service_date: date
    service_description: str
    service_amount: float
    tariff_code: str = "1001"             # Standard Tarif 595 code