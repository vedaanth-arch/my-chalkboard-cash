from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io import BytesIO
from typing import List, Dict, Any
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import os

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

app = FastAPI(title="Chalkboard Cash Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Settings --------------------
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN"]
EXPENSES_FILE = "expenses.csv"
DAYS_HISTORY = 60

# -------------------- Models --------------------
class ExpenseItem(BaseModel):
    date: str
    category: str
    description: str
    amount: float

class ReceiptResponse(BaseModel):
    text: str
    parsed: Dict[str, Any]
    recommended_stocks: List[Dict[str, Any]]
    balance: float

# -------------------- Helper Functions --------------------
def read_balance():
    if not os.path.exists(EXPENSES_FILE):
        raise HTTPException(status_code=400, detail=f"{EXPENSES_FILE} not found")
    df = pd.read_csv(EXPENSES_FILE)
    return float(df['Remaining Amount'].iloc[-1])

def stock_recommendation(balance: float):
    all_data = []
    for symbol in STOCKS:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{DAYS_HISTORY}d")
        if hist.empty: continue
        hist['volatility'] = hist['Close'].pct_change().rolling(5).std()
        hist['momentum'] = (hist['Close'] - hist['Close'].shift(5)) / hist['Close'].shift(5)
        hist['price'] = hist['Close']
        hist = hist.dropna(subset=['volatility', 'momentum'])
        # Equal weight allocation
        allocation = balance / len(STOCKS)
        hist['target_shares'] = (allocation / hist['Close']).apply(np.floor)
        hist['symbol'] = symbol
        all_data.append(hist[['symbol','price','volatility','momentum','target_shares']])
    if not all_data: return []
    df = pd.concat(all_data, ignore_index=True)
    df = df[df['target_shares']>0]
    features = ['price','volatility','momentum']
    X = df[features]
    y = df['target_shares']
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    # Latest 5 days prediction
    latest_data=[]
    for symbol in STOCKS:
        ticker=yf.Ticker(symbol)
        hist=ticker.history(period="5d")
        if hist.empty: continue
        price = hist['Close'].iloc[-1]
        volatility = hist['Close'].pct_change().std()
        momentum = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
        latest_data.append({'symbol':symbol,'price':price,'volatility':volatility,'momentum':momentum})
    latest_df=pd.DataFrame(latest_data)
    latest_df['shares_to_buy']=model.predict(latest_df[features]).astype(int)
    latest_df['total_cost']=latest_df['shares_to_buy']*latest_df['price']
    # Scale to balance
    total_allocation=latest_df['total_cost'].sum()
    if total_allocation>balance:
        scale=balance/total_allocation
        latest_df['shares_to_buy']=(latest_df['shares_to_buy']*scale).astype(int)
        latest_df['total_cost']=latest_df['shares_to_buy']*latest_df['price']
    return latest_df[['symbol','price','shares_to_buy','total_cost']].to_dict(orient='records')

# -------------------- OCR + Recommendation Endpoint --------------------
@app.post("/ocr/scan_receipt", response_model=ReceiptResponse)
async def scan_receipt(file: UploadFile = File(...)):
    balance = read_balance()
    text = ""
    parsed = {"date": None,"total": None,"items":[]}
    # OCR extraction
    if Image and pytesseract:
        contents = await file.read()
        img = Image.open(BytesIO(contents))
        # Configure tesseract path for Windows
        if os.name=='nt' and getattr(pytesseract.pytesseract,'tesseract_cmd',None) is None:
            default_path = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd=default_path
        text = pytesseract.image_to_string(img)
        import re
        date_match = re.search(r"\b(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})\b", text)
        total_match = re.search(r"TOTAL[:\s]*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
        items_match = re.findall(r"^([A-Za-z][A-Za-z\s]+)\s+\d+\s+([0-9]+(?:\.[0-9]{1,2})?)$", text, re.MULTILINE)
        parsed["date"]=date_match.group(1) if date_match else None
        parsed["total"]=float(total_match.group(1)) if total_match else None
        parsed["items"]=[{"name":n.strip(),"price":float(p)} for n,p in items_match]

    recommended_stocks = stock_recommendation(balance)
    return {"text": text,"parsed":parsed,"recommended_stocks":recommended_stocks,"balance":balance}

