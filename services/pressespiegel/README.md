# Pressespiegel: zwei Prompts, ein Beschreibungstext

Neuaufbau vom 28.10.2026. Keine V3-Auswahlengine, numerischen Profile, Ranking-Snapshots, Quoten oder verpflichtenden Suchplan-Dateien. Der Code zeigt Artikel an, speichert Rückmeldungen und prüft das Ausgabeformat. ChatGPT liest, versteht, sucht und wählt aus.

## Ablauf

Im bestehenden Morgenlauf zuerst `INTERESSEN.md` ausführen, danach `RECHERCHE.md`. Zwei logisch getrennte Prompts laufen bewusst nacheinander, damit die Suche den frisch gespeicherten Text erhält. Die Beschreibung bleibt ohne neue Erkenntnisse unverändert. Kein separater Lern-Timer. Recherche darf mit dem letzten tatsächlich verfügbaren Text fortfahren, falls die Aktualisierung scheitert; den alten Stand klar benennen.

Privates Repository: `fabian-stoeckl/morgenzeitung-feedback`. Neuer Ordner `pressespiegel/` mit `interessen.md`, `aenderungen.md`, `state.json` und kurzen Recherchebelegen. Bestehende Rückmeldungen/Profile bleiben erhalten. Anfangsbeschreibung basiert auf ausdrücklich bekannten Wünschen und vorsichtig eingeordneten historischen Beispielen, nicht auf numerischen Gewichten.

Rückmeldungen aus dem neuen Reader sind separate, unveränderliche Ereignisse: Issue-Titel `[Pressespiegel] Feedback YYYY-MM-DD`, Marker `PRESSESPIEGEL_FEEDBACK_V1`, JSON `{version:1, submission_id, date, origin:"website-explicit", ratings:[{id,title,url,section,rating,reason}], comment}`. Pro Sendevorgang ein Issue; Wiederholung desselben unbestätigten Sendevorgangs hat dieselbe submission_id. Bei einer Korrektur ist die jüngste explizite Rückmeldung zum Artikel maßgeblich, kein Stimmenzählen. Allgemeine Kommentare sind eigenständiger Kontext. Editierte Issues/Kommentare frisch lesen. Tests/PRs ignorieren. Der Reader überschreibt keine alten Issues.

Alle Issues paginiert auslesen; `python3 scripts/pressespiegel.py feedback --issues ISSUES.json --state STATE.json` liefert neue/geänderte Originalrückmeldungen und einen Zustand-Vorschlag ohne Interpretation. Bei Issues mit Kommentaren diese zusätzlich paginiert lesen und deren Versions-Hashes in `state.json` führen. Erst nach tatsächlicher Lektüre und erfolgreichem Speichern der Beschreibung den Zustand übernehmen. Alte V3-Rückmeldungen nur lesen, falls seit dem Start verändert; nicht als neue Stimmen zählen.

## Öffentliche Ausgabe

`data/index.json`: `{"dates":["YYYY-MM-DD", ...]}` absteigend, nur existierende Ausgaben.

`data/YYYY-MM-DD.json`:

```json
{"date":"YYYY-MM-DD","researched_at":"ISO timestamp with timezone","kind":"researched","note":"Kurzer redaktioneller Hinweis","articles":[{"id":"stable-id","title":"Originaltitel","source":"Medium","url":"https://...","published_at":"YYYY-MM-DD","summary":"Belegte Zusammenfassung","basis":"teaser","why":"Belegter Erkenntnisgewinn"}],"headlines":[]}
```

Mindestens ein Artikel insgesamt, maximal 15 Vertiefungen und 20 Meldungen, keine Mindestfüllmenge. Beide Listen vorhanden. `why` optional. Für übernommene historische Artikel `kind:"imported"`, eine klare Herkunftsnotiz und `source_edition` verwenden; nie als frische Recherche darstellen. IDs bei Übernahme beibehalten. Keine Leserkommentare/Profilkopien ins öffentliche Tages-JSON.

Prüfen: `python3 scripts/pressespiegel.py verify` und `node tests/pressespiegel-browser.cjs` mit lokalem Server auf Port 8766. Keine Verlags-Linktests. Der Browser lädt Interessen nur mit dem verbundenen privaten Zugang. Beschreibung wird als einfacher Text dargestellt und kann kopiert werden.

## Übergang

Neue Oberfläche `/Privat/Pressespiegel/`, bisherige `/Privat/Persoenliche-Zeitung/` als lesbares Archiv. Nach erfolgreicher Bereitstellung den bestehenden Morgenlauf auf diese zwei Prompts umstellen, die alte separate Störungswache pausieren. Keine parallelen Zeitungsproduktionen. Die alte befristete Rankingmessung entfällt für das neue Konzept; tatsächliche Leserreaktionen zählen. Rücknahme: Morgenlauf auf den archivierten alten Auftrag zurückstellen, Kachel zurücksetzen; Originaldaten bleiben erhalten.
