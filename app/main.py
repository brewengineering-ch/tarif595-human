from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(
    title="Tarif 595 PDF generator",
    description="API for generating Swiss Healthcare Tarif 595 reimbursement receipts and QR bills",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)
