<!-- website-area: {"name": "Pressespiegel", "paths": ["Privat/Pressespiegel/"]} -->
# Bereichsprotokoll: Pressespiegel

**Stand:** 18.10.2026. **Status:** absichtlich als Platzhalter veröffentlichter neuer Website-Bereich.

## Bestehende Implementierung

- Einstiegskachel: `Privat/index.html`, Beschriftung „Pressespiegel“, Link `./Pressespiegel/`.
- Zielseite: `Privat/Pressespiegel/index.html`, Pfad `/Privat/Pressespiegel/`.
- Die Seite enthält aktuell nur eine Überschrift, einen Platzhaltertext und den Rücklink „← Privat“; `noindex,nofollow` ist gesetzt.
- [PR #19](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/19) wurde am 17.10.2026 gemergt. Jekyll-, ETF-, Chart- und responsive Vorschauprüfungen erfolgreich; bestehende „Website ändern“-Kachel/Skill-Link bleiben erhalten.

## Getroffene Entscheidungen

- Die neue Kachel folgt dem visuellen Stil der bestehenden Privat-Kacheln.
- Keine zusätzlichen „Bereich ändern“-Buttons auf der Website; Einstieg in den Website-Workflow weiterhin über die ursprüngliche „Website ändern“-Kachel.
- **Kein** automatischer Artikelimport, keine Datenbank und keine Zusammenfassungslogik im aktuellen Repository dokumentiert. Diese Funktionen nicht als bereits implementiert darstellen.

## Offen / ausdrücklich noch nicht beauftragt

- Inhalt, Datenquelle, Speicherung, Zugriffsregeln, Gestaltung und mögliche Automatisierung eines späteren echten Pressespiegels müssen **vor Implementierung** festgelegt und freigegeben werden.
- Der aktuelle Platzhalter ist der vereinbarte veröffentlichte Stand, kein fehlgeschlagener Funktionsstart.


## Ergänzte Veröffentlichungsbelege (18.10.2026)

- PR #19: Merge 36779c79944a9dc833b62c536393e918b6292bb8; Pages-Lauf 39042426812 und Verify site 39042426985 erfolgreich.
- Damalige Desktop-/Mobilprüfung bei 390/700/1440 px, keine Überläufe oder JS-Seitenfehler. Per HTTPS abgerufene HTML-Seiten entsprachen der geprüften Vorschau; direkter Browser-Netzabruf in der damaligen Umgebung nicht möglich.
- Rücknahme nur der eigenen PR-19-Änderungen an Privat/index.html und Privat/Pressespiegel/index.html; vorherige Basis 1e1d8e63b8af2660318a8a46338497e0363a371a. Spätere unabhängige Änderungen erhalten.

## Morgenzeitung: Implementierungsentwurf vom 18.10.2026

**Status: Entwurf auf `codex/pressespiegel-morgenzeitung`, nicht veröffentlicht, Automatik deaktiviert.** Der neue konkrete Auftrag ersetzt die frühere Offen-Notiz „noch nicht beauftragt“. Ausgangsbasis und Rücknahmebasis: `a6ae4026c7bdfeafc5f68744f9b5252156761172`; keine fremden offenen PRs beim Arbeitsbeginn. Bisherige Website bleibt bis Freigabe unverändert.

- Beauftragt: persönliche Morgenzeitung 07:45 Europe/Vienna täglich; Ziel 10/maximal 15 Vertiefungen inklusive Zuckerl; 15–20 Headlines Österreich/International; Archiv, drei Relevanzstufen, Feedback, korrigierbares Profil, private geräteübergreifende Speicherung und Wiederholungsvermeidung. Veröffentlichung und danach automatischer Betrieb brauchen die explizite Freigabe der konkreten Vorschau.
- Dateien: `Privat/Pressespiegel/{index.html,style.css,app.js,config.json}`, privater Dienst in `services/morgenzeitung/`, Tests in `tests/pressespiegel/`, `.github/workflows/verify-pressespiegel.yml`; Ausschluss `services` in Jekyll, Datenbank-/Env-Ausschluss in `.gitignore`, zusätzlicher npm-Testbefehl. ETF-Daten und Updater nicht geändert/ausgeführt.
- Architektur: statisches bestehendes Pages-Frontend plus privater Python/SQLite-Dienst mit Bearer-Zugang; HTTPS über Host. Rechercheadapter für OpenAI Responses mit Websuche. Profil/Feedback/Inhaltsgedächtnis ausschließlich im privaten Speicher. Konfiguration noch ohne API-Host. Keine API-Schlüssel, privaten Chattexte oder echten Nutzerbewertungen im Repository.
- Planung: Recherche ab 07:15, Freigabe der Ausgabe frühestens 07:45 Ortszeit; DST mit `zoneinfo`. Nach Ausfällen Recherche ab Ende der letzten erfolgreichen Ausgabe. Atomare Veröffentlichung, Tages-ID, drei Versuche/Tag und 30-Minuten-Abstand; letzte erfolgreiche Ausgabe bleibt sichtbar mit wahrem Datum. Pünktlichkeit abhängig von externem Dienst, keine garantierte SLA.
- Lernen: explizite Prioritäten vor gedämpften Bewertungssignalen. Gründe separat; „Schon bekannt“/„Zu oberflächlich“ keine Themenabwertung. Feedback und ausgelieferte Aussagen werden dem nächsten Lauf übergeben; Auslieferung niemals als gelesen gewertet. Echtes semantisches Lernen/Quellenqualität mangels freigegebenem API-Lauf noch nicht nachgewiesen.
- Vorschau: lokale, eingeschränkte Funktionsvorschau mit fünf manuell anhand der Originalquellen gelesenen ORF-Artikeln vom 16.–18.10.2026. Erweitertes Zeitfenster und nur vier Headlines ausdrücklich sichtbar markiert. Noch keine vollständige 24h-Ausgabe oder Abnahme der gewünschten Medienvielfalt. Keine erfundenen Beispielnachrichten. Screenshots 1440 und 390 px; lokal interaktive API geprüft, kein dauerhaft erreichbarer privater Vorschauhost vorhanden.
- Prüfungen lokal: 10 Kernlogiktests erfolgreich (DST, dauerhafte/änderbare Bewertungen, Konflikte, Feedbackübergabe, Dubletten/Fortsetzungen, Fehler/Retry, Zeitfenster); Browserprüfung mit zweitem unabhängigen Browser, Bewertungsänderung, Feedback, Profil, Speicherfehlern und Reitern erfolgreich; kein horizontaler Überlauf oder JS-Seitenfehler bei 1440/390 px. Kontext- und bestehende ETF-Mathematiktests erfolgreich. Weitere fünf Authentifizierungs-/CORS-/Eingabeprüfungen erfolgreich (insgesamt 15 Python-Tests). Vollständiger lokaler Jekyll-Build durch fehlendes Ruby/Bundler blockiert; bestehende GitHub-CI prüft Build separat. Externer KI-Recherchelauf nicht ausgeführt, keine Kosten ausgelöst.
- SMRY-Präfix anhand Anbieter-Dokumentation und HTTP-Weitergabe geprüft; Artikel-Endabrufe von SMRY/Archive teilweise blockiert. Archivlink ausdrücklich „Archivsuche“, keine Verfügbarkeitsbehauptung. End-to-End-Nachweis bei echten Paywall-Artikeln offen.
- Historischer kostenpflichtiger Entwurf (am 19.10.2026 verworfen): Betrieb und Kostenoptionen: `services/morgenzeitung/README.md`. Kein Hosting gebucht. Render verbunden; verfügbarer Arbeitsbereich „My Workspace“, dessen Auswahl noch vom Nutzer zu bestätigen ist. Ein dauerhafter Dienst mit persistentem Speicher plus freigegebener Recherche-API erforderlich. API-Projektbudget/Modellwahl, externe Backups und Alarmierung noch offen.

## Historische offene Punkte des kostenpflichtigen Entwurfs (überholt)

Die folgenden Punkte sind durch die Entscheidung vom 19.10.2026 ersetzt; keine Kostenfreigabe oder Render-Auswahl mehr anfordern.

### Ursprüngliche Liste

1. Hosting verbinden und konkreten Kostenrahmen freigeben; Zugangsschlüssel nur über sichere Host-Konfiguration hinterlegen.
2. Geschützte Remote-Vorschau, echte 24h-Recherche aus der gewünschten Medienmischung, erfolgreiche Folgeausgabe nach Feedback und Link-Endtests; Produktionssicherung/Monitoring einrichten.
3. Entwurfs-PR und CI prüfen; erst danach konkrete Veröffentlichungs- und Betriebsfreigabe einholen, zusammenführen, Pages und privaten Dienst bereitstellen und live prüfen.
4. Nachweise über PR/Commit/CI und Freigabe nach tatsächlichem Erfolg nachtragen. Gegenwärtig **nicht veröffentlicht und nicht täglich aktiviert**.

## Kostenentscheidung und ChatGPT-Aufgabe (19.10.2026)

- Nutzerentscheidung: keine zusätzlichen Ausgaben; stattdessen ausdrücklich geplante GPT-Analyse beauftragt. Kein Render-Dienst und keine kostenpflichtige Recherche-API gebucht oder aktiviert. Bestehendes Hosting und Domain bleiben erhalten.
- Aktiviert: geplante ChatGPT-Aufgabe „Fabians Morgenzeitung“, täglich 07:15 Europe/Vienna einschließlich Sommer-/Winterzeit und Wochenenden. Ziel Fertigstellung bis 07:45, keine garantierte Fertigstellungszeit. Sie nutzt ausschließlich vorhandene ChatGPT-Funktionen und das bestehende Nutzungskontingent.
- Aufgabenprompt enthält Interessen, Quellenprioritäten, 24h-Zeitfenster, Ziel 10/max. 15 Vertiefungen inklusive Zuckerl, 15–20 Headlines Österreich/International, Quellen-/Zeitangaben, ehrliche Teaserkennzeichnung, Archivsuche und drei Relevanzbewertungen. Fehlende Recherche oder Historie muss ausdrücklich benannt werden.
- Ergebnisse vorerst ausschließlich in ChatGPT. Keine automatische Website-Veröffentlichung und kein Merge autorisiert. Website-Entwurf bleibt in PR #24; API-Konfiguration bleibt leer. Der Python/API-Entwurf ist kein aktivierter oder freigegebener Betriebsweg.
- Noch offen: Übertragung der Ausgaben auf die Website und privater geräteübergreifender Rückfluss von Website-Bewertungen ohne zusätzliche Kosten. Dauerhafte Lernwirkung und erste reale Ausgabe sind noch nicht nachgewiesen. Die Aufgabe darf nur tatsächlich zugängliche frühere Ausgaben und Rückmeldungen verwenden.

## Präzisierung: vollständiger Rückkopplungskreislauf (19.10.2026)

- ChatGPT-Ausgabe allein erfüllt den Auftrag ausdrücklich nicht. Ziel: vor Recherche dauerhaftes Artikelprotokoll und Website-Feedback lesen; Interessen und bereits vermittelte Inhalte auswerten; Webrecherche durchführen; neue Auswahl protokollieren und Website aktualisieren; am Folgetag wiederholen.
- Artikelprotokoll benötigt stabile IDs, Original-URL, Ausgabe/Datum und vermittelte Kernaussagen. Feedback benötigt Artikel-ID, eine der drei Relevanzstufen, optionalen Grund/Freitext sowie Änderungszeit. Ausgeliefert und gelesen bleiben getrennt.
- Scheduled-Aufgabe um diesen Ablauf und verpflichtendes Lesen des Betriebsprotokolls ergänzt. Übergangsausgabe in ChatGPT bleibt bis tatsächlich eingerichteter und geprüfter Brücke; kein fertiger Kreislauf behauptet.
- Technisch offen: dauerhafter privater Schreibzugang für Website-Feedback und entsprechender Lesezugang der Aufgabe; Veröffentlichung neuer Ausgaben mit identischer Tages-ID und prüfbarem Erfolg. GitHub Pages allein bietet keinen serverseitigen Feedbackspeicher. Kostenlose Speicheroption ist vor Einrichtung auf Zugriff beider Seiten zu prüfen. Keine geheimen Zugangsschlüssel in Website-Dateien.

## GitHub als Speicher vorbereitet (19.10.2026)

- Nutzer bevorzugt Bewertungen und Protokolle auf GitHub. Entwurf um statischen GitHub-Modus ergänzt: `github.js`, `data/index.json`, datierte Ausgabedateien als Artikelprotokoll; kein Python-Server oder bezahlte Recherche-API für diesen Weg nötig.
- Bewertungslinks öffnen vorausgefüllte GitHub-Issues. Erst Absenden dort speichert; keine falsche Erfolgsmeldung auf der Website. Feedback-Formular erzeugt ebenfalls einen GitHub-Link. Private Bewertungen bleiben auf GitHub, werden nicht öffentlich in der Website gespiegelt.
- Nur öffentliches Website-Repository über Connector sichtbar. Vorgesehenes separates privates Feedback-Repository noch nicht erstellt/verbunden; config `feedback_repository: null`, Buttons daher deaktiviert. Keine echten Bewertungen öffentlich gespeichert.
- Betriebsvertrag und tägliche Lese-/Analyse-/Schreibfolge in `services/morgenzeitung/GITHUB-BETRIEB.md`. Freigabe der konkreten Oberfläche, privater Zugriff, echter Feedback-Folgelauf und unbeaufsichtigte Veröffentlichung weiterhin ausstehend. Vorschau enthält nur die bisherigen fünf ORF-Artikel.
- Prüfungen dieses GitHub-Entwurfs: Node-Linktests, Kontextprüfung und 15 bestehende Python-Tests erfolgreich; Browserprüfung 1440/390 px erfolgreich, fünf Vorschauartikel, kein Überlauf oder JavaScript-Fehler, drei korrekt vorausgefüllte Bewertungslinks und Freitext-Übergabe geprüft. Testziel nur lokal simuliert; kein Issue abgesendet und kein privater Zugriff behauptet. Mobile Screenshotkontrolle erfolgreich. CI auf neuem Remote-Commit noch ausstehend.

## Privates Feedback verbunden (19.10.2026)

- Nutzer hat morgenzeitung-feedback erstellt und verbunden. Sichtbarkeit private sowie Schreib-/Lesezugriff geprüft. Initiales profile.json liegt ausschließlich dort. Synthetisches Issue #1 angelegt, unverändert zurückgelesen und geschlossen; ausdrücklich vom Lernen ausgeschlossen. Kein echter Feedback-Folgelauf behauptet.
- config.json des Entwurfs zeigt nun auf fabian-stoeckl/morgenzeitung-feedback. Bewertungslinks aktiviert; Speicherung erfolgt nach GitHub-Anmeldung durch Absenden des vorausgefüllten Formulars.
- Weiterhin offen: Freigabe der konkreten Vorschau und wiederkehrenden Ausgaben, Merge/Pages/Live-Prüfung sowie unbeaufsichtigter Lauf mit echtem Feedback.

## Vereinfachung und redaktioneller Mehrwert (19.10.2026)

- Nutzer wünscht auch Desktop einspaltig; alle Artikel stehen untereinander. Drei beschriftete Radio-Auswahlpunkte pro Artikel, optionaler Grund. Keine Vorauswahl; nicht bewertete Artikel neutral.
- Bewertungen der gewählten Ausgabe und Freitext werden als eine Sammelbewertung in einem privaten GitHub-Issue übermittelt; Absenden auf GitHub erforderlich. Auswahl bleibt nur im geöffneten Tab, noch keine dauerhafte Speicherung vor Absenden. Bei sehr langem Link wird der Gesamttext kopiert und auf GitHub eingefügt.
- Redaktioneller Auftrag erhöht: Ziel 20, maximal 30 Vertiefungen, Handelsblatt deutlich stärker berücksichtigen. Qualität und neuer Erkenntnisgewinn wichtiger als Ausschöpfen der Zahl; Headlines unverändert 15–20. Geplante Aufgabe und privates Profil aktualisiert. Ältere 10/15-Vorgaben überholt. Inhalt der reduzierten Vorschau noch unverändert, keine neue recherchierte Ausgabe behauptet.
