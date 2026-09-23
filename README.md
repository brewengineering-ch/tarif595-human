# Getting started
## Initial setup
```bash
# Requires Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the app
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

After than the app is available under `http://localhost:8000`, OpenAPI docs under `http://localhost:8000/docs` and ReDoc under `http://localhost:8000/redoc`.

# Decisions
- Python because people from different backgrounds can edit it
- Manual HTML form creation because it is easier to maintain and model changes will not be frequent
- HTML/CSS for PDF generation because it is easier to maintain