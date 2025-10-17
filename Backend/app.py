from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import pytesseract
from PIL import Image
import yfinance as yf
import os
import calendar
import random

# ------------------- Flask Setup -------------------
app = Flask(__name__)
CORS(app)

# ------------------- Constants -------------------
EXPENSES_FILE = "expenses.csv"
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN"]

# ------------------- Helper Functions -------------------
def read_balance():
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        if not df.empty:
            return float(df["Remaining Amount"].iloc[-1])
    return 10000.0  # default principal if CSV empty

def update_expenses(total: float):
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
    else:
        df = pd.DataFrame(columns=["Total Expenses", "Principal Amount", "Remaining Amount"])

    principal = df["Principal Amount"].iloc[-1] if not df.empty else 10000.0
    remaining = principal - total
    df.loc[len(df)] = [total, principal, remaining]
    df.to_csv(EXPENSES_FILE, index=False)
    return remaining

def random_month_expenses(month: int, year: int, seed: int = 42):
    rnd = random.Random(seed)
    days_in_month = calendar.monthrange(year, month)[1]
    categories = ["groceries", "transport", "dining", "utilities", "entertainment", "other"]
    items = []
    for day in range(1, days_in_month + 1):
        for _ in range(rnd.randint(0, 3)):
            amount = round(rnd.uniform(50, 800), 2)
            cat = rnd.choice(categories)
            items.append({"date": f"{year}-{month:02d}-{day:02d}", "category": cat, "amount": amount})
    return items

def week_index(dt):
    # ISO week within month
    first_of_month = pd.Timestamp(dt).replace(day=1)
    offset = first_of_month.weekday()  # 0=Mon..6=Sun
    return (pd.Timestamp(dt).day + offset - 1) // 7  # 0-based week index

# ------------------- Routes -------------------

@app.route("/ocr/receipt", methods=["POST"])
def ocr_receipt():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    try:
        image = Image.open(file.stream)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        return jsonify({"error": f"Failed to read image: {e}"}), 400

    # Extract total (basic)
    total = 0.0
    for line in text.split("\n"):
        if "total" in line.lower():
            for word in line.split():
                if word.replace('.', '', 1).isdigit():
                    total = float(word)
                    break

    remaining = update_expenses(total)

    return jsonify({
        "text": text,
        "parsed": {
            "total": total,
            "remaining": remaining,
            "date": None,
            "items": []
        }
    })

@app.route("/investments/recommend", methods=["GET"])
def recommend_stocks():
    balance = read_balance()
    suggestions = []
    try:
        data = yf.download(STOCKS, period="5d")['Close'].iloc[-1]
        for symbol in STOCKS:
            price = float(data[symbol])
            max_shares = int(balance // len(STOCKS) // price)
            suggestions.append({
                "symbol": symbol,
                "price": round(price, 2),
                "shares": max_shares
            })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch stock data: {e}"}), 500

    return jsonify({"balance": balance, "recommendations": suggestions})

@app.route("/expenses/balance", methods=["GET"])
def get_balance():
    balance = read_balance()
    return jsonify({"balance": balance})

@app.route("/expenses/weekly", methods=["GET"])
def weekly_totals():
    month = request.args.get("month", type=int) or pd.Timestamp.today().month
    year = request.args.get("year", type=int) or pd.Timestamp.today().year
    items = random_month_expenses(month, year)
    # Aggregate per week
    week_buckets = {0: [0]*7, 1: [0]*7}  # two weeks, Mon-Sun
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for it in items:
        w = week_index(it["date"])
        if w in (0, 1):
            weekday = pd.Timestamp(it["date"]).weekday()
            week_buckets[w][weekday] += it["amount"]
    week1 = [{"day": days[i], "expenses": round(week_buckets[0][i], 2)} for i in range(7)]
    week2 = [{"day": days[i], "expenses": round(week_buckets[1][i], 2)} for i in range(7)]
    comparison = [{"day": days[i], "week1": week1[i]["expenses"], "week2": week2[i]["expenses"]} for i in range(7)]
    return jsonify({"week1": week1, "week2": week2, "comparison": comparison})

@app.route("/calendar/month", methods=["GET"])
def calendar_month():
    month = request.args.get("month", type=int) or pd.Timestamp.today().month
    year = request.args.get("year", type=int) or pd.Timestamp.today().year
    items = random_month_expenses(month, year)
    days_in_month = calendar.monthrange(year, month)[1]
    per_day_expense = {d: 0.0 for d in range(1, days_in_month+1)}
    for it in items:
        day = pd.Timestamp(it["date"]).day
        per_day_expense[day] += it["amount"]
    return jsonify({
        "month": month,
        "year": year,
        "days": [{"day": d, "expense": round(per_day_expense[d], 2), "income": 0.0} for d in range(1, days_in_month+1)]
    })

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
