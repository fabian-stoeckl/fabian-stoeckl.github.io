<!-- website-area: {"name": "Persönliche Zeitung", "paths": ["Privat/Persoenliche-Zeitung/"]} -->
# Bereichsprotokoll: Persönliche Zeitung

**Stand:** 28.10.2026. **Status:** Die einzige produktive Persönliche Zeitung liegt direkt unter `Privat/Persoenliche-Zeitung/`. Frühere Zeitungsordner und ihre Weiterleitungsregeln sind gelöscht. Redaktionswissen, Präferenzen und private Feedback-IDs wurden in aktuelle Dateien übernommen; keine historischen Bewertungen doppelt gezählt.

## Geltungsbereich
- Auf `Privat/index.html` bleiben **drei Kacheln**: ETF, Persönliche Zeitung, Website ändern. Die Kachel „Website ändern“ sowie ihr Skill-Link und Layout sind ausdrücklich unverändert zu erhalten.
- Leseroberfläche, CSS, GitHub-Feedback, reguläre Ausgabe und Lernausgabe liegen ausschließlich unter `Privat/Persoenliche-Zeitung/`. Einstieg und Automationen verwenden diese Adresse direkt. Alte Lesezeichen müssen auf die aktuelle URL geändert werden.
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

Der einzige produktive GitHub-Ordner ist `Privat/Persoenliche-Zeitung/`, ohne parallele alte Produktordner oder Zeitungsweiterleitungen. Die Kacheln ETF (Terrakotta), Persönliche Zeitung (Blau) und Website ändern (Violett) bleiben einschließlich des Skill-Links unverändert.

## 28.10.2026 – vollständige Entfernung des alten Ordners

Frühere Zeitungsseiten, ihre Weiterleitungsdateien und die bisherige Sonderbehandlung in `404.html` wurden entfernt. Für die Zeitung gilt ausschließlich `Privat/Persoenliche-Zeitung/`. Vorhandene alte Lesezeichen funktionieren nicht mehr automatisch. Historische fachliche Erkenntnisse liegen weiterhin im aktuellen Redaktionsvertrag beziehungsweise privaten Profil.

## 28.10.2026 – Vereinheitlichung der Website-Aufrufe

Die aktuelle Zeitung, ihre Präferenzen und ihre Lernausgabe werden ausschließlich über URLs unter `/Privat/Persoenliche-Zeitung/` geöffnet. Die `404.html` enthält **keine Zeitungssonderregeln** mehr; sie ist nur die reguläre Fehlerseite und bewahrt unabhängig davon bisherige allgemeine Dashboard-/ETF-Groß-/Kleinschreibungs-Korrekturen. Alter Link zur Zeitung: nicht mehr gültig; direkt auf die aktuelle URL aktualisieren. Es gibt nur einen öffentlichen Zeitungsordner, ein Lernprofil und die beiden bestehenden produktiven Automationen.

## 28.10.2026 – Wartbarkeit, Transparenz und Sicherheit

Die Zeitung besteht aus der Python-Auswahl-/Lernlogik, einem optional typgeprüften Artikel-Metadatenschema, einem privaten Belegdossier, einer eindeutigen öffentlichen Ausgabe und den eigenständigen statischen Browsermodulen. Das UI zeigt zusätzliche Artikelkontexte direkt nach `render()`, zugeordnet mit der stabilen Artikel-ID. Es gibt keine V1/V2-Komponenten, keinen alten Login, keine Beobachter zur laufenden Neubearbeitung des DOM und keine gespeicherten Tokens in öffentlichen JSON-Dateien. Die Ausgabe vom 28. Oktober und die 24 echten Bewertungen bleiben unverändert.

Vorher-/Nachher-Vergleiche erfordern jetzt einen unveränderten Snapshot im **privaten Feedback-Repository** (siehe aktueller Redaktionsvertrag). Ohne echten Ausgangssnapshot wird keine Kausalität behauptet. GitHub-Issues-Schreibvorgänge werden kontrolliert und bei erkannten Überschneidungen nachgeführt; technisch vollständig atomare parallele Schreiboperationen benötigen langfristig einen getrennten Server. Die Content-Security-Policy begrenzt Skriptquellen, ersetzt aber keine sichere Server-Authentifizierung. GitHub-Branch-Schutz ist derzeit nicht aktiviert; falls gewünscht, in den Repository-Einstellungen verpflichtende V3- und Website-Checks einrichten, ohne die bestehenden ETF-Funktionen zu verändern.

## 28.10.2026 – vollständige Auditkorrektur (Entwurf)

Auftrag: alle im redaktionellen/technischen Audit gefundenen Probleme beheben; freie Hand einschließlich Veröffentlichung nach erfolgreichen Tests. Ausgangs- und Rücknahmebasis: `4cec26df5135d6bdca5ad1da2fce51062165ca42`. Arbeitsbranch: `fix/newspaper-editorial-integrity`.

Umgesetzt: nur bearbeitete Bewertungen übertragen und echte Konflikte anzeigen; explizite Bewertungsgründe separat speichern; konservative Freitextinterpretation; unabhängige Stilpräferenzen erhalten; vollständige Feldbelege und Registrierung sämtlicher Ausgaben; Quellentiefe in beiden Rubriken; korrigierte Zusammenfassungen und Zuschreibungen bei erhaltenen Artikel-IDs; versionierte private Korrekturdossiers; tatsächliche Auswahlparameter und Code-Prüfsummen in Lern-Snapshots; Recherchehinweise für Kandidatenbreite/Österreich und Ausschluss ungeeigneter Füllartikel. Der aktuelle Redaktionsvertrag beschreibt den verbindlichen täglichen Ablauf.

Historische Angaben oben, die Ausgabe und alle Inhalte blieben unverändert, beziehen sich auf frühere technische Schritte. Dieser Auftrag erlaubt ausdrückliche sachliche Korrekturen; ursprüngliche Belege und 24 historische Bewertungen werden nicht überschrieben oder als neue Stimmen gezählt. Die tatsächliche Qualitätsverbesserung kommender Ausgaben bleibt anhand späterer Bewertungen zu prüfen.

Freigabe: Nutzerauftrag „Bessere alles aus – du hast freie Hand“. Lokale Regressionen, mobile/Desktop-Vorschau, private Rückleseprüfung, GitHub-CI, Merge und Live-Abnahme werden vor Abschluss dokumentiert; Stand dieses Eintrags: Entwurf, noch nicht veröffentlicht.

Prüfung des Entwurfs: 90 Python-Regressionen, JavaScript-Feedback-/UI-Prüfungen und drei Timeline-Tests bestanden; mobiler Browserfall einschließlich Gerätewechsel, Konfliktmeldung und strukturierter Gründe bestanden. Beide Ausgaben bei 390 und 1440 Pixeln ohne Browserfehler/Überlauf geprüft. Private Korrekturdossiers über PR #10 im Feedback-Repository gesichert und identisch zurückgelesen; beide Ausgaben bestehen die echte lokale Dossierprüfung. Lokales Jekyll-Build nicht verfügbar (Ruby/Bundler fehlt); Produktionsbuild wird durch GitHub-CI geprüft. Veröffentlichung noch ausstehend.
