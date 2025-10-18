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

def update_expenses(total: float, increment_count: int = 0):
    """Append a snapshot with cumulative total; derive delta and timestamp.
    Columns: Total Expenses, Principal Amount, Remaining Amount, Expense Count, Timestamp, Delta
    """
    cols = [
        "Total Expenses",
        "Principal Amount",
        "Remaining Amount",
        "Expense Count",
        "Timestamp",
        "Delta",
    ]

    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
    else:
        df = pd.DataFrame(columns=cols)

    # Ensure all columns exist
    for c in cols:
        if c not in df.columns:
            df[c] = []

    principal = (
        float(df["Principal Amount"].iloc[-1]) if not df.empty and "Principal Amount" in df.columns else 10000.0
    )
    prev_total = float(df["Total Expenses"].iloc[-1]) if not df.empty else 0.0
    prev_count = int(df["Expense Count"].iloc[-1]) if not df.empty else 0
    new_count = prev_count + int(increment_count)

    total = float(total)
    delta = total - prev_total
    remaining = principal - total
    ts = pd.Timestamp.now().date().isoformat()

    row = {
        "Total Expenses": total,
        "Principal Amount": principal,
        "Remaining Amount": remaining,
        "Expense Count": new_count,
        "Timestamp": ts,
        "Delta": delta,
    }

    # Append row in the canonical column order
    df = df.reindex(columns=cols, fill_value=None)
    df.loc[len(df)] = [row[c] for c in cols]
    df.to_csv(EXPENSES_FILE, index=False)
    return remaining, new_count

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
    first_of_month = pd.Timestamp(dt).replace(day=1)
    offset = first_of_month.weekday()
    return (pd.Timestamp(dt).day + offset - 1) // 7

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

    total = 0.0
    for line in text.split("\n"):
        if "total" in line.lower():
            for word in line.split():
                if word.replace('.', '', 1).isdigit():
                    total = float(word)
                    break

    # Combine with existing cumulative total (only append when valid total found)
    if total > 0 and os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        last_total = float(df["Total Expenses"].iloc[-1]) if not df.empty else 0.0
    else:
        last_total = 0.0

    if total > 0:
        new_total = last_total + total
        remaining, count = update_expenses(new_total, increment_count=1)
    else:
        # No change; report current balance and count
        if os.path.exists(EXPENSES_FILE):
            df = pd.read_csv(EXPENSES_FILE)
            count = int(df["Expense Count"].iloc[-1]) if (not df.empty and "Expense Count" in df.columns) else 0
            remaining = float(df["Remaining Amount"].iloc[-1]) if not df.empty else read_balance()
        else:
            count = 0
            remaining = read_balance()

    return jsonify({
        "text": text,
        "parsed": {
            "total": total,
            "remaining": remaining,
            "date": None,
            "items": []
        },
        "balance": remaining,
        "count": count
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

    # Build using per-entry deltas grouped by day
    week_buckets = {0: [0]*7, 1: [0]*7}
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        if not df.empty and "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df = df.dropna(subset=["Timestamp"]) 
            df = df[(df["Timestamp"].dt.month == month) & (df["Timestamp"].dt.year == year)]
            # derive delta if missing
            if "Delta" not in df.columns:
                df = df.sort_values("Timestamp")
                df["Delta"] = df["Total Expenses"].diff().fillna(df["Total Expenses"]).astype(float)
            for _, row in df.iterrows():
                d = row["Timestamp"].date().isoformat()
                w = week_index(d)
                if w in (0, 1):
                    weekday = pd.Timestamp(d).weekday()
                    try:
                        amt = float(row.get("Delta", 0.0))
                    except Exception:
                        amt = 0.0
                    week_buckets[w][weekday] += max(0.0, amt)

    week1 = [{"day": days[i], "expenses": round(week_buckets[0][i], 2)} for i in range(7)]
    week2 = [{"day": days[i], "expenses": round(week_buckets[1][i], 2)} for i in range(7)]
    comparison = [{"day": days[i], "week1": week1[i]["expenses"], "week2": week2[i]["expenses"]} for i in range(7)]
    return jsonify({"week1": week1, "week2": week2, "comparison": comparison})

@app.route("/calendar/month", methods=["GET"])
def calendar_month():
    month = request.args.get("month", type=int) or pd.Timestamp.today().month
    year = request.args.get("year", type=int) or pd.Timestamp.today().year
    days_in_month = calendar.monthrange(year, month)[1]
    per_day_expense = {d: 0.0 for d in range(1, days_in_month + 1)}

    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        if not df.empty and "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            df = df.dropna(subset=["Timestamp"]) 
            df = df[(df["Timestamp"].dt.month == month) & (df["Timestamp"].dt.year == year)]
            if "Delta" not in df.columns:
                df = df.sort_values("Timestamp")
                df["Delta"] = df["Total Expenses"].diff().fillna(df["Total Expenses"]).astype(float)
            for _, row in df.iterrows():
                day = int(row["Timestamp"].day)
                try:
                    amt = float(row.get("Delta", 0.0))
                except Exception:
                    amt = 0.0
                if 1 <= day <= days_in_month:
                    per_day_expense[day] += max(0.0, amt)

    return jsonify({
        "month": month,
        "year": year,
        "days": [{"day": d, "expense": round(per_day_expense[d], 2), "income": 0.0} for d in range(1, days_in_month + 1)]
    })

# ------------------- Manual Expense Add -------------------
@app.route("/expenses/add", methods=["POST"])
def add_expense():
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    # Determine last total expenses
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
    else:
        df = pd.DataFrame(columns=["Total Expenses", "Principal Amount", "Remaining Amount", "Expense Count"])

    last_total = float(df["Total Expenses"].iloc[-1]) if not df.empty else 0.0
    new_total = last_total + amount

    remaining, count = update_expenses(new_total, increment_count=1)

    return jsonify({
        "total": new_total,
        "balance": remaining,
        "count": count,
    })

@app.route("/expenses/count", methods=["GET"])
def get_expense_count():
    if os.path.exists(EXPENSES_FILE):
        df = pd.read_csv(EXPENSES_FILE)
        if not df.empty:
            count = int(df["Expense Count"].iloc[-1]) if "Expense Count" in df.columns else int(len(df))
            return jsonify({"count": count})
    return jsonify({"count": 0})

# ------------------- ✅ NEW ROUTE for Total Balance -------------------
@app.route("/api/total-balance", methods=["GET"])
def total_balance_api():
    balance = read_balance()
    return jsonify({"balance": balance})

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
