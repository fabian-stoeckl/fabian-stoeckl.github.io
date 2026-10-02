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

def fetch(ticker):
    df=yf.download(ticker,start=FIRST_PURCHASE_DATE,end=(pd.Timestamp.utcnow()+pd.Timedelta(days=2)).strftime("%Y-%m-%d"),auto_adjust=True,progress=False,actions=False,threads=False)
    if df.empty: raise RuntimeError(f"No data for {ticker}")
    close=df["Close"]
    if isinstance(close,pd.DataFrame): close=close.iloc[:,0]
    close=close.dropna()
    out={}
    for year in YEARS:
        s=close[close.index.year==year]
        if year == FIRST_YEAR:
            s=s[s.index >= pd.Timestamp(FIRST_PURCHASE_DATE)]
        if s.empty: out[str(year)]=[]; continue
        first=float(s.iloc[0]); pts=[]
        for idx,v in s.items():
            v=float(v); pts.append({"date":idx.strftime("%Y-%m-%d"),"day":int(idx.dayofyear),"price":clean(v),"performance":clean((v/first-1)*100)})
        out[str(year)]=pts
    return out

def main():
    items=json.loads(CONFIG.read_text(encoding="utf-8"))
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"first_year":FIRST_YEAR,"years":YEARS,"source":"Yahoo Finance via yfinance","etfs":[]}
    for e in items:
        x=dict(e)
        try: x["series"]=fetch(e["ticker"]);x["status"]="ok"
        except Exception as exc: x["series"]={str(y):[] for y in YEARS};x["status"]="error";x["error"]=str(exc)
        payload["etfs"].append(x)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
