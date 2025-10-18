# Chalkboard Cash Backend

FastAPI service providing expense data and simple OCR receipt parsing for the my-chalkboard-cash frontend.

## Endpoints

- GET /health — service health
- GET /expenses/random?month=10&year=2025&seed=42 — random expenses for a month
- GET /expenses/weekly?month=10&year=2025&seed=42 — weekly aggregates and comparison (week1/2)
- GET /calendar/month?month=10&year=2025&seed=42 — daily expense/income for the calendar
- POST /ocr/receipt — multipart/form-data image upload for OCR

## Run locally (Windows PowerShell)

```powershell
# From Backend folder
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open http://127.0.0.1:8000/docs for interactive API docs.

## Notes
- OCR requires Tesseract to be installed. On Windows the default path is `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`.
- The random data uses a `seed` query param for reproducible results.