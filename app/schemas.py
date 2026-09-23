from pydantic import BaseModel
from datetime import date

class InvoiceData(BaseModel):
    company_name: str
    company_address: str
    company_iban: str
    client_first_name: str
    client_last_name: str
    service_date: date
    service_description: str
    service_amount: float