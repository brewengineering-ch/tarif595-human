from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World live"}

@app.get("/health")
def read_health():
    return {"status": "healthy"}