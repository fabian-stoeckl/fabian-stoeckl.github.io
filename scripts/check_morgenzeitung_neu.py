"""Static schema/consistency checks for the new paper. NEVER request article URLs."""
import datetime as dt, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1] / "Privat/Pressespiegel-neu/data"

def validate(path):
    e=json.loads(path.read_text(encoding="utf-8"))
    day=path.stem
    assert e["date"]==day, "date/path mismatch"
    dt.date.fromisoformat(day)
    assert isinstance(e.get("preview"), bool)
    for k in ["researched_at","available_at","window_start","window_end"]:
        dt.datetime.fromisoformat(e[k].replace("Z","+00:00"))
    ids=set()
    urls=set()
    for section, lo, hi in [("headlines",15,20),("articles",10,15)]:
        items=e[section]
        if not e["preview"]:
            assert lo<=len(items)<=hi, f"{section} count is {len(items)}"
        assert isinstance(items,list)
        for a in items:
            for key in ["id","title","source","url","summary","published_at"]:
                assert isinstance(a.get(key),str) and a[key].strip(), f"{section}: empty {key}"
            assert len(a["id"])==16 and all(c in "0123456789abcdef" for c in a["id"]), "bad rating ID"
            assert a["id"] not in ids, "duplicate ID"
            assert a["url"].startswith("https://") and " " not in a["url"], "bad URL syntax"
            assert a["url"] not in urls, "duplicate URL"
            dt.datetime.fromisoformat(a["published_at"].replace("Z","+00:00"))
            if section=="articles":assert a.get("topic"), "article without topic"
            if section=="headlines":assert a.get("region") in ("Österreich","International"), "bad region"
            ids.add(a["id"]);urls.add(a["url"])
    return len(e["articles"]),len(e["headlines"])

def main():
    ix=json.loads((ROOT/"index.json").read_text(encoding="utf-8"))["dates"]
    assert isinstance(ix,list) and len(ix)==len(set(ix)) and ix==sorted(ix,reverse=True)
    assert ix, "no editions"
    for day in ix:
        a,n=validate(ROOT/(day+".json"))
        print(f"{day}: {a} Vertiefungen, {n} Nachrichten (format OK)")
    print("Keine Artikel-HTTP-Tests ausgeführt.")

if __name__=="__main__":
    main()
