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

After than the app is available under `http://localhost:8000` and the API docs under `http://localhost:8000/docs`.

# Information
- 
- Manual HTML form creation over automated form creation was choosen for readability