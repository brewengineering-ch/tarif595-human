from pydantic import BaseModel
from datetime import date

class InvoiceData(BaseModel):
    company_name: str
    company_city: str
    company_zip_code: str
    company_street: str
    company_iban: str
    client_first_name: str
    client_last_name: str
    client_city: str
    client_zip_code: str
    client_street: str
    service_date: date
    service_description: str
    service_amount: float