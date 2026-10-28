<!-- website-area: {"name": "Morgenzeitung 3", "paths": ["Privat/Morgenzeitung-3/"]} -->
# Bereichsprotokoll: Morgenzeitung 3

**Stand:** 28.10.2026. **Status:** eigenständige Version 3 in PR #206; Live-Betrieb, erster voll recherchierter Tageslauf und echter Lerneffekt sind erst nach Merge/Automation bestätigt.

## Geltungsbereich
- Kachel: `Privat/index.html`, Ziel `Privat/Morgenzeitung-3/`.
- Identische Leseroberfläche über gemeinsam genutzte alte UI-Dateien; die Dateien der bisherigen beiden Pressespiegel und ETFs bleiben unverändert.
- Eigene Daten: `Privat/Morgenzeitung-3/data/`; eigenes privates Issue-Format und privates Profil unter `morgenzeitung-v3/profile.json` in `fabian-stoeckl/morgenzeitung-feedback`.
- Redaktioneller Vertrag `services/morgenzeitung-v3/REDAKTION.md`, veränderbare Quellenliste `services/morgenzeitung-v3/sources.json`; Ranking/Audit `scripts/morgenzeitung_v3_engine.py`. Minimale Tests nur in `.github/workflows/verify-morgenzeitung-v3.yml`.

## Getroffene Entscheidungen
- Inhaltlicher Fit, Erkenntnisgewinn, Quellenvielfalt und tatsächliches Lernen wichtiger als Erreichbarkeit einzelner Artikel-URLs. **Keine individuellen HTTP-Linktests**; Volltextzugang hat Gewicht 0 in Auswahl und Ranking.
- Volltext, Vorspann und Titel unterscheiden sich nur in der **Belegtiefe** der späteren Zusammenfassung. Nicht belegte Zahlen, Zitate oder Kausalbehauptungen müssen korrigiert werden; Faktenwarnung plus redaktionelle Prüfung, keine behauptete automatische Wahrheitserkennung.
- Interesse aus echten V3-Bewertungen vorsichtig ableiten; Grund `Schon bekannt` nicht als Themenablehnung werten. Gleiche Kandidaten vor/nach Feedback für echten Auswahländerungs-Nachweis; ohne Effekt nicht als gelernt bezeichnen. Begrenzter Entdeckungsanteil vermeidet Filterblase.
- Tägliches Ziel 07:45 Europe/Vienna. Vorherige Ausgaben erhalten; technische Fehler begrenzt reparieren statt Kaskaden. Archivvorschau 27.10. ausdrücklich `preview:true` und nicht unabhängig recherchiert.

## Offen / nächste Verifikation
- PR #206 CI, Merge, Pages und Live-Website prüfen; eigene tägliche Aufgabe konfigurieren und ihren vollständigen Produktionslauf abnehmen.
- Erste eigene V3-Recherche, private Belegprüfung und tatsächlich angewendetes Feedback getrennt nachweisen; vorerst keine entsprechende Erfolgsmeldung.
- Tagesbetrieb auf redaktionelle Vielfalt, tatsächliche Lernwirkung und veröffentlichte Belege vergleichen; ohne echte Bewertungen keine gemessene Verbesserung behaupten.
