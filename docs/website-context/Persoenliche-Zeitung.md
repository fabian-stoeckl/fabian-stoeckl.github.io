<!-- website-area: {"name": "Persönliche Zeitung", "paths": ["Privat/Persoenliche-Zeitung/"]} -->
# Bereichsprotokoll: Persönliche Zeitung

**Stand:** 28.10.2026. **Status:** eine einzige produktive Persönliche Zeitung. Die früheren Versionen wurden aus Website und Prozessen entfernt; ihre wichtigen redaktionellen Erkenntnisse sind im aktuellen Vertrag zusammengeführt. Der produktive GitHub- und Website-Ordner heißt `Privat/Persoenliche-Zeitung/`. Die Weiterleitungsregeln für frühere Lesezeichen zu Hauptseite, Präferenzen und Lernausgabe sind in der zentralen `404.html` integriert. Der alte GitHub-Ordner ist vollständig gelöscht. Die privaten Feedback-IDs und Issue-Marker bleiben unverändert.

## Geltungsbereich
- Auf `Privat/index.html` bleiben **drei Kacheln**: ETF, Persönliche Zeitung, Website ändern. Die Kachel „Website ändern“ sowie ihr Skill-Link und Layout sind ausdrücklich unverändert zu erhalten.
- Leseroberfläche, CSS, GitHub-Feedback und Präferenzanzeige eigenständig in `Privat/Persoenliche-Zeitung/`; die separat veröffentlichte Lernausgabe vom 28.10. liegt vollständig im aktuellen Ordner. Alte Lesezeichen werden über die zentrale `404.html` weitergeleitet (mit aktiviertem JavaScript).
- Verbindliche redaktionelle Anweisung: `services/morgenzeitung-v3/REDAKTION.md`; Quellen: `services/morgenzeitung-v3/sources.json`; Tests und Redaktion ausschließlich V3. Eigenes privates Profil: `fabian-stoeckl/morgenzeitung-feedback:morgenzeitung-v3/profile.json`.
- Bestehende Issue-Titel `[Morgenzeitung 3] Feedback YYYY-MM-DD`, Marker `MORGENZEITUNG_V3_FEEDBACK_V1` und lokale technische Token-/Feedback-IDs dürfen nicht umbenannt werden, damit alle Bewertungen erhalten bleiben.
- Nur der tägliche V3-Lauf (06:45 Europe/Vienna) und die V3-Störungswache bleiben aktiviert; die ehemaligen V1/V2-Aufgaben sind deaktiviert.

## Getroffene Entscheidungen
- Die Rubrik „Heute wichtig“ bildet gesellschaftliche Bedeutung unabhängig von persönlichen Interessen ab. „Vertiefungen“ setzt auf persönlichen Erkenntnisgewinn, analytische Tiefe, Neuigkeitswert, wirtschaftliche Mechanismen, Zahlen und Zielkonflikte.
- Originaltitel, Datum, URL und jede Tatsachenaussage nur mit privatem Belegdossier; kein Rückschluss auf Volltextlektüre aus technischem Zugriff, keine künstlichen Zusammenfassungen.
- Keine Paywall-/HTTP-Linktests und keine Quellenmarken-Boni. Neue Publikationen auf Probe, österreichische und internationale Recherche mit offener Themenentdeckung.
- Ein negatives Artikelurteil ist keine generelle Themenablehnung. `Teilweise relevant` ohne Erklärung und fehlende Stimmen bleiben neutral. Gründe für Themenfit, Neuigkeitswert, Tiefe und Perspektive getrennt auswerten.
- Der V3-Eintrag vom 27.10. ist `preview:true` (keine eigenständige produktive Recherche). Die reguläre Ausgabe und separate Lern-Sonderausgabe vom 28.10. ergeben zusammen 24 echte Ratings an einem einzigen Kalendertag. Ein historischer V1-Datensatz bleibt als interne V3-Testreferenz; alte Bewertungen werden nie als neue V3-Stimmen gezählt.

## Veröffentlichungs- und Lernkontrolle
- Privates Dossier und echte redaktionelle Freigabe vor PR; danach vorhandene V3-Prüfungen und Pages-Merge. Bei echten Störungen letzte gültige Ausgabe bewahren. Keine falschen Erfolgsbestätigungen.
- Vom 29.10.–11.11.2026 14 Tage zwischen Feedbackverarbeitung, Veränderung der Auswahl auf identischem Kandidatenpool und tatsächlich später besser bewerteten Ausgaben unterscheiden. Zwischenbilanz am 04.11., Gesamtbilanz am 11.11.
- „Website ändern“ bleibt auch nach der Umbenennung sichtbar und direkt als Skill geöffnet.

## Offen / nächste Verifikation
- Öffentliche Darstellung auf Desktop/Mobilgeräten und freiwilliges privates Feedback im aktuellen Branding prüfen.
- Qualitätsentwicklung nach dem nächsten echten produktiven Tageslauf weiter mit Nutzerbewertungen messen, nicht mit bloßem grünem CI belegen.

## 28.10.2026 – Ordner und Kachelgestaltung

Der produktive GitHub-Ordner wurde auf `Privat/Persoenliche-Zeitung/` umgestellt. Der alte Ordner wurde vollständig entfernt. Seine drei Weiterleitungsregeln sind jetzt Teil der zentralen `404.html`; es gibt keine doppelten Seiten, Datensätze oder Produktordner. Die drei Kacheln ETF, Persönliche Zeitung und Website ändern behalten ihre Form und Funktion und unterscheiden sich nun in Terrakotta, Blau und Violett. ETF-Finanzdaten, die Website-ändern-Skill-Adresse sowie private Feedback-Kennungen sind unverändert.

## 28.10.2026 – vollständige Entfernung des alten Ordners

Die drei alten HTML-Weiterleitungsseiten sind vollständig entfernt. Ihre festen früheren Adressen sowie V1/V2-Startseiten werden bei GitHub Pages durch die zentrale `404.html` zur aktuellen Persönlichen Zeitung weitergeleitet; Query-Parameter und Fragment bleiben erhalten. GitHub Pages liefert für diese fehlenden URLs zunächst einen HTTP-404-Status, die Browserweiterleitung erfolgt per JavaScript (kein serverseitiger HTTP-301-Redirect). Das aktuelle `Privat/Persoenliche-Zeitung/` ist der **einzige produktive Ordner**. Frühere redaktionelle Regeln und die sinnvolle V1-Lernhistorie sind im aktuellen Redaktionsvertrag beziehungsweise privaten V3-Profil integriert, ohne historische Bewertungen doppelt zu zählen.
