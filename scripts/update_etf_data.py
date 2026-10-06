from pathlib import Path
from datetime import datetime, timezone
import json, math, sys
import exchange_calendars as xcals
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "Privat" / "ETFs" / "etfs.json"
OUT = ROOT / "Privat" / "ETFs" / "data" / "etf_data.json"
STALE_TOLERANCE_SESSIONS = 2
FIRST_YEAR = 2025
FIRST_PURCHASE_DATE = "2025-11-03"
CURRENT_YEAR = datetime.now().year
YEARS = list(range(FIRST_YEAR, CURRENT_YEAR + 1))

def clean(x):
    x=float(x)
    return x if math.isfinite(x) else None

def fetch(ticker, is_fx=False):
    df=yf.download(ticker,start=FIRST_PURCHASE_DATE,end=(pd.Timestamp.now('UTC')+pd.Timedelta(days=2)).strftime("%Y-%m-%d"),auto_adjust=True,progress=False,actions=False,threads=False,timeout=15)
    if df.empty: raise RuntimeError(f"No data for {ticker}")
    close=df["Close"]
    if isinstance(close,pd.DataFrame): close=close.iloc[:,0]
    close=close.dropna()
    if is_fx:
        today = pd.Timestamp.now('UTC').strftime("%Y-%m-%d")
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

def latest_date(series):
    return max((p["date"] for points in series.values() for p in points), default="")

def expected_etf_date(now):
    # Only completed Xetra sessions; includes exchange holidays and DST.
    calendar = xcals.get_calendar("XETR")
    schedule = calendar.schedule.loc[(now - pd.Timedelta(days=20)).strftime("%Y-%m-%d"):now.strftime("%Y-%m-%d")]
    completed = schedule[schedule["close"] <= now]
    return completed.index[-1].strftime("%Y-%m-%d")

def lag_sessions(last, expected, is_fx=False):
    if not last:
        return None
    if last >= expected:
        return 0
    if is_fx:
        sessions = pd.bdate_range(last, expected)
    else:
        sessions = xcals.get_calendar("XETR").sessions_in_range(last, expected)
    return sum(day.strftime("%Y-%m-%d") > last for day in sessions)

def xetra_session_closes(now):
    # Include future sessions so a saved page can detect aging without a new fetch.
    schedule = xcals.get_calendar("XETR").schedule.loc[
        (now - pd.Timedelta(days=40)).strftime("%Y-%m-%d"):
        (now + pd.Timedelta(days=370)).strftime("%Y-%m-%d")]
    return [{"date":day.strftime("%Y-%m-%d"), "close":row["close"].isoformat()}
            for day, row in schedule.iterrows()]

def refresh_item(item, previous, expected, is_fx=False):
    x = dict(item)
    try:
        series = fetch(item["ticker"], is_fx=is_fx)
        if not latest_date(series):
            raise RuntimeError("Keine gültigen Kurse geliefert")
        if previous and latest_date(series) < latest_date(previous.get("series", {})):
            raise RuntimeError("Quelle liefert ältere Daten als der gespeicherte Stand")
        x.update(series=series, status="ok")
    except Exception as exc:
        x["series"] = previous.get("series", {}) if previous else {str(y): [] for y in YEARS}
        x["status"] = "ok" if latest_date(x["series"]) else "error"
        x["update_error"] = str(exc)
    x["last_price_date"] = latest_date(x["series"])
    x["expected_price_date"] = expected
    x["lag_sessions"] = lag_sessions(x["last_price_date"], expected, is_fx)
    x["stale"] = x["lag_sessions"] is None or x["lag_sessions"] > STALE_TOLERANCE_SESSIONS
    return x

def main():
    now = pd.Timestamp.now("UTC")
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    items = json.loads(CONFIG.read_text(encoding="utf-8"))
    expected = expected_etf_date(now)
    # FX daily bars can remain provisional until the UTC day ends.
    day = (now - pd.Timedelta(days=1)).date()
    while day.weekday() >= 5:
        day -= pd.Timedelta(days=1)
    expected_fx = day.isoformat()
    payload = {"generated_at": now.isoformat(), "last_successful_update_at": previous.get("last_successful_update_at", previous.get("generated_at")),
               "first_year": FIRST_YEAR, "years": YEARS, "source": "Yahoo Finance via yfinance", "etfs": [], "fx": [],
               "expected_etf_date": expected, "stale_tolerance_sessions": STALE_TOLERANCE_SESSIONS,
               "xetra_session_closes": xetra_session_closes(now)}
    for group, configs, is_fx, target in [
        ("etfs", items, False, expected),
        ("fx", [{"code": c, "name": n, "ticker": t, "quote_units": "foreign_per_eur", "performance_units": "eur_per_foreign"} for c,n,t in FX_PAIRS], True, expected_fx),
    ]:
        old = {e["ticker"]: e for e in previous.get(group, [])}
        payload[group] = [refresh_item(e, old.get(e["ticker"]), target, is_fx) for e in configs]
    issues = [e for e in payload["etfs"] + payload["fx"] if e["stale"] or e.get("update_error")]
    payload["update_status"] = "warning" if issues else "ok"
    if not issues and all(e["lag_sessions"] == 0 for e in payload["etfs"] + payload["fx"]):
        payload["last_successful_update_at"] = now.isoformat()
    temp = OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(OUT)
    for e in issues:
        print(f"::warning::{e['ticker']}: Kursstand {e['last_price_date'] or 'fehlt'}, erwartet {e['expected_price_date']}; {e.get('update_error', 'Quelle noch nicht aktuell')}")
    return 1 if issues else 0

if __name__ == "__main__":
    sys.exit(main())
