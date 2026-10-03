from pathlib import Path
from datetime import datetime, timezone
import json, math
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Privat" / "ETFs" / "etfs.json"
OUT = ROOT / "Privat" / "ETFs" / "data" / "etf_data.json"
FIRST_YEAR = 2025
FIRST_PURCHASE_DATE = "2025-11-03"
CURRENT_YEAR = datetime.now().year
YEARS = list(range(FIRST_YEAR, CURRENT_YEAR + 1))

def clean(x):
    x=float(x)
    return x if math.isfinite(x) else None

def fetch(ticker, is_fx=False):
    df=yf.download(ticker,start=FIRST_PURCHASE_DATE,end=(pd.Timestamp.utcnow()+pd.Timedelta(days=2)).strftime("%Y-%m-%d"),auto_adjust=True,progress=False,actions=False,threads=False)
    if df.empty: raise RuntimeError(f"No data for {ticker}")
    close=df["Close"]
    if isinstance(close,pd.DataFrame): close=close.iloc[:,0]
    close=close.dropna()
    if is_fx:
        today = pd.Timestamp.utcnow().strftime("%Y-%m-%d")
        close = close[(close.index.dayofweek < 5) & (close.index.strftime("%Y-%m-%d") <= today)]
        close = close[(close > 0) & close.map(math.isfinite)]
    out={}
    for year in YEARS:
        s=close[close.index.year==year]
        if year == FIRST_YEAR:
            s=s[s.index >= pd.Timestamp(FIRST_PURCHASE_DATE)]
        if s.empty: out[str(year)]=[]; continue
        first=float(s.iloc[0]); pts=[]
        for idx,v in s.items():
            v=float(v); pts.append({"date":idx.strftime("%Y-%m-%d"),"day":int(idx.dayofyear),"price":clean(v),"performance":clean(((first/v if is_fx else v/first)-1)*100)})
        out[str(year)]=pts
    return out

FX_PAIRS = [
    ("USD", "US-Dollar", "EURUSD=X"),
    ("JPY", "Japanischer Yen", "EURJPY=X"),
    ("GBP", "Britisches Pfund", "EURGBP=X"),
    ("CHF", "Schweizer Franken", "EURCHF=X"),
    ("AUD", "Australischer Dollar", "EURAUD=X"),
    ("CNY", "Chinesischer Yuan", "EURCNY=X"),
    ("KRW", "Südkoreanischer Won", "EURKRW=X"),
    ("TWD", "Taiwan-Dollar", "EURTWD=X"),
]

def main():
    items=json.loads(CONFIG.read_text(encoding="utf-8"))
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"first_year":FIRST_YEAR,"years":YEARS,"source":"Yahoo Finance via yfinance","etfs":[],"fx":[]}
    for e in items:
        x=dict(e)
        try: x["series"]=fetch(e["ticker"]);x["status"]="ok"
        except Exception as exc: x["series"]={str(y):[] for y in YEARS};x["status"]="error";x["error"]=str(exc)
        payload["etfs"].append(x)
    for code, name, ticker in FX_PAIRS:
        x={"code":code,"name":name,"ticker":ticker,"quote_units":"foreign_per_eur","performance_units":"eur_per_foreign"}
        try: x["series"]=fetch(ticker, is_fx=True);x["status"]="ok"
        except Exception as exc: x["series"]={str(y):[] for y in YEARS};x["status"]="error";x["error"]=str(exc)
        payload["fx"].append(x)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
