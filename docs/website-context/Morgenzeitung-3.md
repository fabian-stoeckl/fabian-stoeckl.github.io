<!-- website-area: {"name": "Morgenzeitung 3", "paths": ["Privat/Morgenzeitung-3/"]} -->
# Bereichsprotokoll: Morgenzeitung 3

**Stand:** 28.10.2026. **Status:** eigenständige Version 3 mit PR #206 (Merge 232fd9d1e941240aaa03b56f3ab75d3f08043120) veröffentlicht; erster unabhängig recherchierter Tageslauf und echter Lerneffekt sind noch separat produktiv nachzuweisen.

## Geltungsbereich
- Kachel: `Privat/index.html`, Ziel `Privat/Morgenzeitung-3/`.
- Vollständig eigenständige Leseroberfläche, CSS, GitHub-Feedback, Bewertungsverlauf und Präferenzanzeige im V3-Verzeichnis. Version 1 und 2 aus Website und Produktionsabläufen entfernt; ETF und sonstige Website unverändert.
- Eigene Daten: `Privat/Morgenzeitung-3/data/`; eigenes privates Issue-Format und privates Profil unter `morgenzeitung-v3/profile.json` in `fabian-stoeckl/morgenzeitung-feedback`.
- Redaktioneller Vertrag `services/morgenzeitung-v3/REDAKTION.md`, veränderbare Quellenliste `services/morgenzeitung-v3/sources.json`; Ranking/Audit `scripts/morgenzeitung_v3_engine.py`. Minimale Tests nur in `.github/workflows/verify-morgenzeitung-v3.yml`.

## Getroffene Entscheidungen
- Inhaltlicher Fit, Erkenntnisgewinn, Quellenvielfalt und tatsächliches Lernen wichtiger als Erreichbarkeit einzelner Artikel-URLs. **Keine individuellen HTTP-Linktests**; Volltextzugang hat Gewicht 0 in Auswahl und Ranking.
- Volltext, Vorspann und Titel unterscheiden sich nur in der **Belegtiefe** der späteren Zusammenfassung. Nicht belegte Zahlen, Zitate oder Kausalbehauptungen müssen korrigiert werden; Faktenwarnung plus redaktionelle Prüfung, keine behauptete automatische Wahrheitserkennung.
- Interesse aus echten V3-Bewertungen vorsichtig ableiten; Grund `Schon bekannt` nicht als Themenablehnung werten. Gleiche Kandidaten vor/nach Feedback für echten Auswahländerungs-Nachweis; ohne Effekt nicht als gelernt bezeichnen. Begrenzter Entdeckungsanteil vermeidet Filterblase.
- Tägliches Ziel 07:45 Europe/Vienna. Vorherige Ausgaben erhalten; technische Fehler begrenzt reparieren statt Kaskaden. Archivvorschau 27.10. ausdrücklich `preview:true` und nicht unabhängig recherchiert.

## Offen / nächste Verifikation
- PR #206 und alle V3-spezifischen CI bestanden, Merge erfolgt; eigene tägliche Aufgabe seit 28.10.2026 um 06:45 Europe/Vienna aktiv. Pages-Publikation und vollständigen Tageslauf separat kontrollieren.
- Erste eigene V3-Recherche, private Belegprüfung und tatsächlich angewendetes Feedback getrennt nachweisen; vorerst keine entsprechende Erfolgsmeldung.
- Tagesbetrieb auf redaktionelle Vielfalt, tatsächliche Lernwirkung und veröffentlichte Belege vergleichen; ohne echte Bewertungen keine gemessene Verbesserung behaupten.

## 28.10.2026: Konsolidierung auf eine einzige Morgenzeitung

- Die alten Seiten `/Privat/Pressespiegel/` (V1) und `/Privat/Morgenzeitung-neu/` (V2) sowie deren Produktionsskripte, Workflows, Tests und Automationen wurden stillgelegt. Nur die V3-Ausgabe bleibt produktiv.
- Die von V3 benötigten Skripte `app.js`, `github.js`, `preferences.js`, `preference-timeline.js`, `style.css` wurden in das V3-Verzeichnis übernommen; kein Runtime-Import aus entfernten Pfaden.
- Ein einzelner historischer V1-Referenz-Datensatz wurde unter `services/morgenzeitung-v3/fixtures/` als ausdrücklich nicht produktive Qualitätsvergleichsdatei bewahrt. Alte V1/V2-Ausgaben sind nicht mehr öffentlich verfügbar; private historische Nutzerbewertungen wurden nicht als V3-Stimmen dupliziert.
- Alte Kacheln im Dashboard durch eine Kachel „Morgenzeitung“ ersetzt, ETF- und Website-Skill-Kachel erhalten. Der V3-Redaktionsvertrag bleibt einzig verbindlich.
