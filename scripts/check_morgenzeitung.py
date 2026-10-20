#!/usr/bin/env python3
"""Check editions and the public morning-paper release without paid services."""
import argparse
import json
import re
import sys
from datetime import datetime, time, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
VIENNA = ZoneInfo("Europe/Vienna")
BASE = "https://www.fabian-stoeckl.com/Privat/Pressespiegel/"
sys.path.insert(0, str(ROOT / "services" / "morgenzeitung"))
from core import canonical, similar  # noqa: E402

def validate(edition):
    day=edition["date"]
    preview=edition.get("preview",False)
    articles,headlines=edition["articles"],edition["headlines"]
    if not 1<=len(articles)<=15 or not 1<=len(headlines)<=20:
        raise ValueError(f"{day}: Ungültige Rubrikgröße")
    if not preview and (len(articles)<10 or len(headlines)<15) and not edition.get("limitations"):
        raise ValueError(f"{day}: Bei weniger als 10 Vertiefungen oder 15 Headlines muss ein Grund genannt werden")
    seen_urls=set()
    seen_events=set()
    seen_titles=[]
    for section,entries in [("headlines",headlines),("articles",articles)]:
        for item in entries:
            url=canonical(item["url"])
            title=item.get("title","")
            event=item.get("event","")
            if len(title)<10 or not item.get("source") or not event:
                raise ValueError(f"{day}: Fehlende Quellen-/Ereignisangabe")
            if url in seen_urls or event in seen_events or any(similar(title,t) for t in seen_titles):
                raise ValueError(f"{day}: Doppelte Story über Rubriken: {title}")
            seen_urls.add(url);seen_events.add(event);seen_titles.append(title)
            if item.get("region") not in ("Österreich","International"):
                raise ValueError(f"{day}: Ungültige Nachrichtenregion")
            pub=datetime.fromisoformat(item["published_at"].replace("Z","+00:00"))
            if pub.tzinfo is None:
                raise ValueError(f"{day}: Datum ohne Zeitzone")
            if section=="headlines":
                continue
            if not item.get("topic") or not item.get("kind") or item.get("kind")=="Nachricht":
                raise ValueError(f"{day}: Vertiefung ist keine substanzielle Analyse: {title}")
            summary=item.get("summary","")
            facts=item.get("facts",[])
            if not isinstance(summary,str) or len(summary)<130 or not isinstance(facts,list) or len(facts)<2:
                raise ValueError(f"{day}: Vertiefung ohne ausreichenden Inhalt oder zwei belegte Sachverhalte: {title}")
            if item.get("access") not in ("full","teaser") or not isinstance(item.get("paywall"),bool):
                raise ValueError(f"{day}: Kein transparenter Zugangs-/Paywallstatus: {title}")
            # Every new (non-demo) feature must make its actual reading basis auditable.
            if not preview:
                basis=item.get("research_access")
                if basis not in ("original_full","original_teaser","verified_archive","verified_smry"):
                    raise ValueError(f"{day}: Recherchezugsbasis fehlt: {title}")
                if basis=="original_teaser" and item["access"]!="teaser":
                    raise ValueError(f"{day}: Vorspann darf nicht als Volltext bezeichnet werden")
                if basis in ("verified_archive","verified_smry"):
                    reference=item.get("research_reference","")
                    host=urlparse(reference).hostname
                    expected={"verified_archive":{"archive.is","archive.ph","archive.today"},
                              "verified_smry":{"smry.ai","www.smry.ai"}}[basis]
                    if urlparse(reference).scheme!="https" or host not in expected:
                        raise ValueError(f"{day}: Bestätigte Alternativquelle ohne überprüfbare URL")
                if not item.get("research_checked_at"):
                    raise ValueError(f"{day}: Recherchierzeitpunkt fehlt")
    return True

def fetch_json(relative):
    req=Request(BASE+relative,headers={"User-Agent":"Morgenzeitung-AvailabilityCheck/1.0","Cache-Control":"no-cache"})
    with urlopen(req,timeout=25) as r:
        if r.status!=200:
            raise RuntimeError(f"HTTP {r.status}: {relative}")
        return json.loads(r.read().decode("utf-8"))

def check_local():
    index=json.loads((ROOT/"Privat/Pressespiegel/data/index.json").read_text())
    dates=index["dates"]
    if not dates or dates!=sorted(set(dates),reverse=True):
        raise ValueError("Datumsindex nicht absteigend oder doppelt")
    for d in dates:
        data=json.loads((ROOT/f"Privat/Pressespiegel/data/{d}.json").read_text())
        if data["date"]!=d:
            raise ValueError("Dateiname und Ausgabedatum weichen ab")
        validate(data)
    print(f"Lokal geprüft: {len(dates)} Ausgabe(n), jüngste {dates[0]}")

def check_live(require_today=False):
    with urlopen(Request(BASE,headers={"User-Agent":"Morgenzeitung-AvailabilityCheck/1.0"}),timeout=25) as response:
        html=response.read().decode("utf-8")
    if 'id="tab-headlines"' not in html or 'id="tab-articles"' not in html:
        raise ValueError("Öffentliche Website liefert nicht die erwarteten beiden Rubriken")
    index=fetch_json("data/index.json")
    if not index.get("dates"):
        raise ValueError("Öffentlich kein Datumsindex")
    data=fetch_json("data/"+index["dates"][0]+".json")
    if data.get("date")!=index["dates"][0]:
        raise ValueError("Öffentliche Ausgabe und Datumsindex widersprechen sich")
    validate(data)
    print("Öffentlich überprüft:",data["date"],"Vertiefungen:",len(data["articles"]),
          "Nachrichten:",len(data["headlines"]),"Vorschau:",bool(data.get("preview")))
    if require_today:
        now=datetime.now(VIENNA)
        # Scheduled run occurs after 07:45 Vienna time even in summer.
        if now.time()<time(7,45):
            raise RuntimeError("Frischeprüfung zu früh angesetzt")
        if data.get("preview") or data["date"]!=now.date().isoformat():
            raise RuntimeError("WARNUNG: heutige Ausgabe fehlt, zuletzt online "+data["date"]+
                               "; GitHub-Actions-Lauf ist absichtlich FEHLGESCHLAGEN")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--live",action="store_true")
    parser.add_argument("--require-today",action="store_true")
    options=parser.parse_args()
    try:
        if options.live:check_live(options.require_today)
        else:check_local()
    except Exception as ex:
        print("MORGENZEITUNG PRÜFFEHlER:",ex,file=sys.stderr)
        sys.exit(1)
