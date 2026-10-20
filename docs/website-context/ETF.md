<!-- website-area: {"name": "ETF", "paths": ["Privat/ETFs/", "Privat/etfs/"]} -->
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
- Keine weitere konkrete ETF-Produktänderung als offen belegt.


## Historischer Detailstand, übernommen am 18.10.2026

### Historische Anforderungen, recherchiert am 17.10.2026
Quelle: ältere Chats insbesondere 02.–07.10.2026 über Personal Context; technische Umsetzung anhand der zusammengeführten PRs #16–#18 und des aktuellen Repositorys geprüft. Kein vollständiges Gesprächsarchiv; damalige Chatberichte ohne Codebeleg sind unten als solche gekennzeichnet.

### Darstellung / Bedienung
- Einbindung in bestehende Website unter `/Privat/ETFs/`; Privat als erweiterbares Kachel-Dashboard.
- Jahresbereich ausschließlich mit Doppel-Schieberegler auswählen; alle Jahreslinien zwischen Start und Ende zeigen (Nutzerwunsch 02.10.). Jahreslinien 2025/2026; keine pauschale Umstellung auf andere Auswahltechnik.
- Normale grüne Kursstand-/Gesund-Felder pro Fonds entfernen; Abrufzeit und ältestes ETF-Kursdatum oben rechts reichen. Warnungen bei fehlenden/veralteten Daten bleiben sichtbar (Nutzerwunsch 06.10., Umsetzung #16).
- ETF-, gewichtete Sparplan- und Währungsauswertung; konkrete aktuelle Anzeige/Annahmen vor späteren Änderungen im Code lesen.

### Datenquelle / Frische / Fehler
- Yahoo Finance via yfinance bleibt im am 17.10. geprüften Updater die Quelle. EODHD war nur Vergleichskandidat; kein bestätigter Anbieterwechsel und kein bezahlter Plan beschlossen (#16 bestätigt keine Migration).
- Kursdatum klar von tatsächlicher Abrufzeit und letztem erfolgreichen aktuellen Abruf trennen. Einen erfolgreichen HTTP-Abruf nicht als aktuellen Kursstand ausgeben.
- Abgeschlossene Xetra-Handelssitzungen inklusive Feiertage und Sommerzeit berücksichtigen. Warnung erst bei mehr als zwei abgeschlossenen fehlenden Sitzungen; Wochenende/Feiertage zählen nicht. Fehlende nutzbare Daten sofort als Fehler.
- Bei Fehler, leerer Antwort oder rückläufigem Kursdatum letzte gültige Reihen erhalten; ältere Antworten dürfen neuere Daten nicht überschreiben.
- Browser kann Datenalter auch ohne neuen Serverabruf anhand mitgelieferter zukünftiger Xetra-Schlusszeiten erkennen. Portfolio/FX verwenden die dokumentierte Toleranz; konkrete FX-Kalenderlogik vor Anpassung lesen.
- Abrufprobleme innerhalb der Toleranz als Diagnose erhalten, aber keinen sichtbaren Fehlalarm oder roten Workflow allein deshalb auslösen. Fehlende Daten oder dritte versäumte Sitzung bleiben Fehler (#18).
- `last_successful_update_at` nur bei fehlerfreiem aktuellem Abruf fortschreiben, nicht bei toleriertem Fehler.
- Plan laut aktuellem Workflow: 21:37 UTC Mo–Fr; Wiederholung 06:37 UTC Di–Sa; zusätzlich Samstag 10:15 UTC. UTC-Zeiten nicht mit fixer österreichischer Ortszeit verwechseln.
- Getestete direkte und transitive Python-Abhängigkeiten fixieren. Updater niemals nur für einen Test ausführen; erst bewusst bei einem konkreten Datenauftrag.

### Rendite-/Diagrammgrundlagen
- Jahresrendite und ausgewählter Zeitraum ab letztem gültigen Schlusskurs des Vorjahres, damit die Bewegung am ersten Handelstag nicht verloren geht (#17).
- Sonderfall 2025: Startbasis 03.11.2025 erhalten. Falls Vorjahresbasis fehlt, verfügbare Basis verwenden und Teilzeitraum samt Referenzdatum sichtbar kennzeichnen.
- Gewichtetes Portfolio nur über gemeinsame gültige Datenpunkte rechnen; erwartete Rendite auf denselben Zeitraum beziehen.
- Monats-/Tagesvergleich auf Schaltjahr-Referenzkalender abbilden, 29. Februar erhalten; tatsächliche Monatsanfänge als Achsenticks statt pauschaler 31-Tage-Schritte. Originaldatum im Tooltip erhalten; schmale Ansichten dürfen Labels auslassen, aber keine Monate doppeln.
- Währungsdarstellung aus EUR-Sicht: steigende Linie = mehr EUR je Fremdwährungseinheit. Im Datenformat `foreign_per_eur` und in der Performance `eur_per_foreign` unterscheiden; Reziprozität und Einheiten prüfen.

### Technischer Ausgangspunkt (17.10.2026)
- `Privat/ETFs/index.html`, `Privat/ETFs/etfs.json`, `Privat/ETFs/data/etf_data.json`, `scripts/update_etf_data.py`, `.github/workflows/update-etf-data.yml`.
- Aktuelle 8 angezeigte ETFs: SXR8.DE, VWCG.DE, DBXJ.DE, IS3N.DE, SXR1.DE, 2B76.DE, G1CE.DE, XB4A.DE. Der ATX ist angezeigt, aber kein Bestandteil der im Quellcode gewichteten Sparplan-Reihe.
- Sparplan-Gewichte laut aktuellem Code: SXR8 35%, VWCG 20%, DBXJ 10%, IS3N 10%, SXR1 10%, G1CE 7,5%, 2B76 7,5%. Diese technische Dashboard-Konfiguration ist maßgeblich, ältere Strategiediskussionen mit anderen Tickern nicht ungeprüft übertragen. Keine Aussage über tatsächlichen Depotbestand.
- Relevante Tests: fx.test.cjs, data-status.test.cjs, annual.test.cjs, charts.test.cjs, preview.test.cjs und Python-Updater-Tests. Keine Finanzdatenänderung während dieser Protokollrecherche.


### Verbindliches Design nach Nutzerkorrektur (20.10.2026)

- Der Nutzer hat klargestellt: **Nur** die Kacheln der Privat-Übersicht sollen auf ihren ursprünglichen gestalterischen Stand vor den Neon-Experimenten zurückgesetzt werden. Das ETF-Dashboard soll **nicht** auf das alte hellgraue Farbschema zurückgestellt werden.
- Deshalb bleibt `Privat/index.html` unverändert im Originalstand (SVG-Kacheln in Blau, Braunorange und Dunkelgrün), während `Privat/ETFs/index.html` exakt das in PR #41 freigegebene und veröffentlichte warme ETF-Design erhält. ETF-CSS-Token und Diagrammfarben kommen aus Merge-Commit `a58a68788616b5969f1ad3f9899b1ebbc6c18f9c`.
- Auch `tests/charts.test.cjs` entspricht wieder PR #41 und prüft die warmen ETF-Farben gegen die Morgenzeitung. Andere Website-Bereiche, Ausgaben und ETF-Daten bleiben unverändert.
- PR #46 setzte zwischenzeitlich irrtümlich **auch** die ETF-Farben zurück; diese Fehlinterpretation ist korrigiert. Für spätere Wünsche gelten die beiden getrennten Entscheidungen: alte Kunst-Kacheln auf `/Privat/`, warme ETF-Farben auf `/Privat/ETFs/`.
