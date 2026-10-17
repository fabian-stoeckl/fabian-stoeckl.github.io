# Bereichsprotokoll: ETF

**Stand:** 18.10.2026. **Status:** ETF-Dashboard und automatische Kursaktualisierung vorhanden; laufende Datenstände sind zeitabhängig.

## Geltungsbereich

- `/Privat/ETFs/`: `Privat/ETFs/index.html`.
- Instrumentenliste: `Privat/ETFs/etfs.json`; gespeicherte Werte/Metadaten: `Privat/ETFs/data/etf_data.json`.
- Abruf und Zeitplanung: `scripts/update_etf_data.py`, `.github/workflows/update-etf-data.yml`.
- Tests: `tests/annual.test.cjs`, `tests/fx.test.cjs`, `tests/data-status.test.cjs`, `tests/charts.test.cjs`, `tests/test_etf_update.py`.

## Aktueller Funktionsumfang und feste Entscheidungen

- Jahresperformance-Ansicht mit **zwei Reglern** für Start-/Endjahr; Fonds, gewichtetes Sparplanportfolio, ATX separat und Wechselkurse.
- Datenquelle **Yahoo Finance / yfinance** mit bereinigten Schlusskursen; kein unabgestimmter Datenprovider-Wechsel.
- Kursdatum und Abrufzeit klar trennen; zentraler Datenstand oben rechts. Keine zusätzlichen grünen „alles in Ordnung“-Felder je Fonds.
- Abgeschlossene **Xetra-Sitzungen** inkl. Feiertage beachten; Verzögerung von **bis zu zwei** abgeschlossenen Sitzungen tolerieren, Warnung bei mehr als zwei verpassten Sitzungen oder fehlenden verwertbaren Daten.
- Beim Abruffehler/regressiven Kursstand letzte gültige Daten behalten, Diagnosen nicht verschweigen; Abendabruf mit zusätzlichen Wiederholungsversuchen.
- Fondsbezogene Renditeannahmen sind Prognoseannahmen, keine zugesicherte Rendite. Die Kennzahlen aus `etfs.json` und dem aktuellen Datenbestand nicht frei rekonstruieren.
- Prüfungen dürfen **nicht** versehentlich `scripts/update_etf_data.py` laufen lassen, da dies Daten umschreibt.

## Relevante publizierte Änderungen

| Datum | Änderung | Nachweis |
| --- | --- | --- |
| 06.10.2026 | Xetra-Datumsvalidierung, Abrufzeit und Kursdatum getrennt, 2-Sitzungen-Toleranz, gültige Daten behalten, geplante Abrufe | [PR #16](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/16), gemergt |
| 06.10.2026 | Jahresrendite ab letztem Kurs des Vorjahres, korrekte Monatsachsen und Kalenderdarstellung | [PR #17](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/17), gemergt |
| 07.10.2026 | Vorübergehende Abruffehler innerhalb des Puffers machen den Updater nicht unnötig fatal | [PR #18](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/18), gemergt |

## Offenes / Prüfregeln

- Automatische Kurs-Commits ändern die Daten regelmäßig; **aktuellen** Zeitstempel und Actions-Lauf immer frisch prüfen, nicht aus diesem Protokoll zitieren.
- Jede neue ETF-Änderung: Vorschau (auch 320/390/550/768/1024/1440 px bei Charts) → Freigabe → Unit-/Daten-/Browser-/Jekyll-Tests → Deployment- und Live-Prüfung.
- Keine weitere konkrete ETF-Produktänderung als offen belegt.

## Protokoll für nächste Änderung

- Datum / Änderungsauftrag:
- Betroffene Daten-/Code-Dateien und Quelle:
- Entscheidungen / Randbedingungen:
- Branch / PR / Commit / Tests:
- Vorschau und Freigabe:
- Deployment / Live-Verifikation / Rücknahme:
- Noch offen:
