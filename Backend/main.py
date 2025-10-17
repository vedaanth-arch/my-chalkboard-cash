from datetime import date, datetime, timedelta
from io import BytesIO
from typing import List, Optional, Dict, Any
import calendar
import random

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    # Optional imports; OCR endpoint will guard usage
    from PIL import Image
    import pytesseract
except Exception:  # pragma: no cover - optional at runtime
    Image = None
    pytesseract = None


app = FastAPI(title="Chalkboard Cash Backend", version="0.1.0")

# Allow local dev frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to specific origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExpenseItem(BaseModel):
    date: date
    category: str
    description: str
    amount: float


class MonthExpenses(BaseModel):
    month: int  # 1..12
    year: int
    currency: str = "INR"
    items: List[ExpenseItem]


class WeeklySeriesPoint(BaseModel):
    day: str  # Mon..Sun
    expenses: float


def _random_month_expenses(month: int, year: int, seed: Optional[int] = None) -> List[ExpenseItem]:
    rnd = random.Random(seed)
    days_in_month = calendar.monthrange(year, month)[1]

    categories = ["groceries", "transport", "dining", "utilities", "entertainment", "other"]
    items: List[ExpenseItem] = []

    # Simulate 0-3 expenses per day
    for day in range(1, days_in_month + 1):
        num = rnd.randint(0, 3)
        for _ in range(num):
            amount = round(rnd.uniform(50, 800), 2)
            cat = rnd.choice(categories)
            items.append(
                ExpenseItem(
                    date=date(year, month, day),
                    category=cat,
                    description=f"{cat} expense",
                    amount=amount,
                )
            )
    return items


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/expenses/random", response_model=MonthExpenses)
def get_random_expenses(month: Optional[int] = None, year: Optional[int] = None, seed: Optional[int] = 42):
    today = datetime.today()
    m = month or today.month
    y = year or today.year
    items = _random_month_expenses(m, y, seed)
    return MonthExpenses(month=m, year=y, items=items)


def _week_index(dt: date) -> int:
    # ISO week within month: week starts on Monday
    first_of_month = date(dt.year, dt.month, 1)
    offset = (first_of_month.weekday())  # 0=Mon..6=Sun
    return (dt.day + offset - 1) // 7  # 0-based week index in month


@app.get("/expenses/weekly")
def weekly_totals(month: Optional[int] = None, year: Optional[int] = None, seed: Optional[int] = 42) -> Dict[str, Any]:
    today = datetime.today()
    m = month or today.month
    y = year or today.year
    items = _random_month_expenses(m, y, seed)

    # Aggregate per week (Mon..Sun) for two first weeks to match frontend mock
    week_buckets: Dict[int, Dict[int, float]] = {0: {i: 0.0 for i in range(7)}, 1: {i: 0.0 for i in range(7)}}
    for it in items:
        if it.date.month != m:
            continue
        w = _week_index(it.date)
        if w in (0, 1):
            weekday = it.date.weekday()  # 0=Mon..6=Sun
            week_buckets[w][weekday] += it.amount

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    week1 = [{"day": days[d], "expenses": round(week_buckets[0][d], 2)} for d in range(7)]
    week2 = [{"day": days[d], "expenses": round(week_buckets[1][d], 2)} for d in range(7)]

    comparison = [
        {"day": days[d], "week1": week1[d]["expenses"], "week2": week2[d]["expenses"]}
        for d in range(7)
    ]

    return {"week1": week1, "week2": week2, "comparison": comparison}


@app.get("/calendar/month")
def calendar_month(month: Optional[int] = None, year: Optional[int] = None, seed: Optional[int] = 42) -> Dict[str, Any]:
    today = datetime.today()
    m = month or today.month
    y = year or today.year
    items = _random_month_expenses(m, y, seed)

    # Simple calendar totals per day for expense and an arbitrary income simulation
    days_in_month = calendar.monthrange(y, m)[1]
    per_day_expense = {d: 0.0 for d in range(1, days_in_month + 1)}
    for it in items:
        per_day_expense[it.date.day] += it.amount

    rnd = random.Random(seed)
    per_day_income = {d: (round(rnd.uniform(0, 400), 2) if rnd.random() < 0.25 else 0.0) for d in range(1, days_in_month + 1)}

    days_data = [
        {"day": d, "expense": round(per_day_expense[d], 2), "income": per_day_income[d]}
        for d in range(1, days_in_month + 1)
    ]

    return {"month": m, "year": y, "days": days_data}


@app.post("/ocr/receipt")
async def ocr_receipt(file: UploadFile = File(...)) -> Dict[str, Any]:
    # Basic guard: if libs missing, return stub
    if Image is None or pytesseract is None:
        return {
            "text": "",
            "parsed": {
                "date": None,
                "total": None,
                "items": []
            },
            "note": "OCR libraries not available on server; returning empty result."
        }

    # Load image from upload
    try:
        contents = await file.read()
        img = Image.open(BytesIO(contents))  # type: ignore[name-defined]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # Configure tesseract path on Windows if installed in default location
    try:
        import os
        if os.name == 'nt' and getattr(pytesseract.pytesseract, 'tesseract_cmd', None) is None:
            default_path = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
    except Exception:
        pass

    text = pytesseract.image_to_string(img)

    # Very light parsing (date, total, item lines like "Name qty price")
    import re
    date_match = re.search(r"\b(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})\b", text)
    total_match = re.search(r"TOTAL[:\s]*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
    items = re.findall(r"^([A-Za-z][A-Za-z\s]+)\s+\d+\s+([0-9]+(?:\.[0-9]{1,2})?)$", text, re.MULTILINE)

    return {
        "text": text,
        "parsed": {
            "date": date_match.group(1) if date_match else None,
            "total": float(total_match.group(1)) if total_match else None,
            "items": [{"name": name.strip(), "price": float(price)} for name, price in items],
        },
    }


# For running via: uvicorn main:app --reload