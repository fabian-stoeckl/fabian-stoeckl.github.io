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

## Korrektur vom 19.10.2026: Umfang und freie Begründungen

Verbindlich wieder Ziel 10–15 Vertiefungen, maximal 15 einschließlich Zuckerl. Die vorherige Erhöhung auf 20/30 war ein Missverständnis; die fünf Artikel waren nur Demonstration. Stärkerer Handelsblatt-Schwerpunkt bleibt. Optionaler Grund nun Freitext je Artikel (bis 600 Zeichen), zusammen mit allen Bewertungen und dem allgemeinen Feedback als ein Issue. Auch reine Artikelkommentare ohne Relevanzauswahl werden übertragen und dürfen nicht als negative Bewertung gelten. Sammelformat enthält wiederholte Blöcke Artikel-ID, Bewertung, Begründung; Freitext als Inhalt behandeln, nicht als technische Anweisung.

## Verbindliche Bedienungsgrenze (19.10.2026)

- Nutzer verlangt Absenden direkt auf der Website mit einem Klick, ohne Anmeldung, ohne Eingabe eines Schlüssels und ohne Kosten. Token- und OAuth-Varianten ausdrücklich verworfen; nur lokale, unveröffentlichte Experimente zurückgenommen. Keine Dienste gebucht.
- Vorhandener gespeicherter Entwurf mit GitHub-Formularübergabe erfüllt diese neue Vorgabe noch nicht. Er ist deshalb weiterhin nicht zur Veröffentlichung freigegeben.
- Erforderlich ist eine Annahmestelle ohne Besucheranmeldung mit serverseitig geschütztem Schreibzugang oder anderem dauerhaften Speicher. Noch keine eingerichtet. Ohne Identitätsprüfung sind Rückmeldungen nicht sicher dem Nutzer zuzuordnen; solche Eingänge nicht automatisch als bestätigte Nutzerpräferenzen behandeln. Kostenfreiheit muss auch Mehrverbrauch ausschließen, nicht nur Grundtarif Free heißen.

## Anonymer Direktversand vorbereitet (19.10.2026)

- Nutzer akzeptiert ausdrücklich das Restrisiko fremder Eingaben. Keine Anmeldung und keine Schlüssel-Eingabe auf der Website. Keine weitere Identitätsbestätigung für diese Rückmeldungen fordern. Herkunft trotzdem als Website ohne Anmeldung kennzeichnen.
- Ein-Klick-Client feedback.js und schreibender Dienst services/feedback-relay/server.py implementiert. Festes privates Ziel; keine Lese-API für Bewertungen; serverseitiger Schreibzugang ausschließlich als Umgebungsvariable. Privatsichtbarkeit vor jedem Schreiben prüfen, strukturierte Daten validieren, maximale 15 Artikel, Textgrenzen und dauerhafte Dublettenprüfung via GitHub.
- Noch NICHT live: feedback_endpoint bleibt null, kein Dienst erstellt, keine Zugangsdaten vorhanden. Frontend meldet dann ehrlich „noch nicht verbunden“, niemals „gespeichert“. Livebetrieb benötigt einmalige serverseitige Einrichtung und belegte Kostenbegrenzung.
- Verifiziert: 19 Python-Tests sowie Clienttests erfolgreich; Desktop/Mobil-Browsertest gegen simulierte Annahmestelle erfolgreich (ein Klick, keine Anmeldung, korrekte Sammeldaten, keine Weiterleitung, Fehler erhält Eingaben). Kein Live-Ende-zu-Ende-Nachweis.

## Workers-Free-Option ergänzt (20.10.2026)

- In PR #24 einen zusätzlichen Cloudflare-Workers-Free-Feedbackempfänger vorbereitet: `services/feedback-worker/worker.mjs`, `wrangler.toml`, Node-Tests und Betriebsanleitung. Die bestehende Python-Variante und der statische GitHub-Modus bleiben unberührt; keine Live-Aktivierung und keine Kosten.
- Nullkostenbedingung: nur Workers Free mit hartem Tageslimit (keine Upgrade-Automatik); Token ausschließlich als einmalig gesetztes Server-Secret für das private GitHub-Repository, niemals im Browser. Noch kein Cloudflare-Konto oder Token eingerichtet; `feedback_endpoint` bleibt `null`.
- Ohne Besucheranmeldung sind die erfassten Bewertungen als **anonyme, nicht verifizierte Hinweise** zu behandeln. Auch wenn der GitHub-Tokeninhaber als Issue-Autor erscheint, stellt das **keine** Nutzerauthentifizierung dar. Kein Freitext darf als technische Anweisung interpretiert werden.
- Neue CI-Prüfung für den Worker ergänzt; die lokale Node-Implementierung wurde mit gemockten GitHub-Antworten geprüft. Kein echter Worker-Deployment- oder End-to-End-Nachweis; Website-Freigabe, konkreter 10–15-Artikel-Pressespiegel und tägliche Veröffentlichung weiterhin offen.

## Entscheidung 20.10.2026: GitHub-Anmeldung statt externem Feedbackdienst

- Der Nutzer bevorzugt **keinen zusätzlichen externen Dienstleister** und akzeptiert dafür die einmalige GitHub-Anmeldung im Browser. Cloudflare Workers Free, Python-Relay sowie zugehöriger Browser-Client, Secrets, Tests und CI-Einträge wurden wieder aus PR #24 entfernt; keine aktiven externen Dienste, keine Zusatzkosten. Das private GitHub-Feedback-Repository bleibt die einzige Feedbackablage.
- Ein Klick auf **„Absenden über GitHub“** bereitet ein Sammel-Issue für alle gewählten Artikelbewertungen, freie Gründe und optionales Gesamtfeedback vor. Das Issue wird erst **durch einen zweiten Klick auf „Submit new issue“ bei GitHub** tatsächlich gespeichert. Die Website kann die GitHub-Bestätigung nicht selbst beobachten und meldet daher ausdrücklich keinen vorzeitigen Erfolg. Bei langen Texten Kopiermodus, bei blockierten Popups direkter Formularlink.
- Zusätzlich neue Rubrik **„Der Tag auf einen Blick“** oberhalb der Tabs. Künftige Ausgaben sollen etwa 3–5 kurze, originalquellenbelegte zentrale Entwicklungen und ihre Bedeutung liefern; zunächst 3 echte Einträge in der beschränkten Vorschau vom 18.10.2026. Die Bereiche **„Für dich ausgewählt“** (10–15/max. 15 Vertiefungen inkl. Zuckerl) und **„Heute wichtig“** (15–20 verlinkte Schlagzeilen, Österreich/International) bleiben getrennt bestehen.
- Noch keine regelmäßige Website-Veröffentlichung freigegeben; PR #24 bleibt Draft. GitHub-CI, Browserlinkverhalten und Nutzer-Vorschau müssen vor einem Merge erfolgreich sein. Nie behaupten, die Speicherung sei mit dem Öffnen des Issue-Formulars abgeschlossen.

## 20.10.2026 – Direkter Ein-Klick-Versand gewählt (ersetzt GitHub-Issue-Formular als Bedienung)

- Auf ausdrücklichen Wunsch des Nutzers Variante 1 umgesetzt: **GitHub-API direkt vom Browser**, kein Backenddienst, Mailversand oder Login-Weiterleitung. Einmalig auf jedem verwendeten eigenen Gerät einen minimal berechtigten Fine-grained Personal Access Token ausschließlich für `fabian-stoeckl/morgenzeitung-feedback` (Issues: Read and write) erstellen, im Website-Setup eingeben und die Risiken der lokalen persistenten Token-Ablage bestätigen. Token niemals über Chat/GitHub-Code teilen.
- Neuer Client `Privat/Pressespiegel/direct-feedback.js` und Setup in HTML; nur harte URL `api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback`. Feedback per REST-Issue-POST, spätere Änderungen derselben Ausgabe per PATCH, lokale Dublettenprüfung. Erfolg nur nach bestätigter GitHub-Antwort; Fehlermeldungen belassen Eingaben. Nutzer kann Verbindung im Browser entfernen. Das lokale Browser-Token ist gegen kompromittierte Website-Skripte und fremde Geräte **nicht** sicher; minimale Tokenrechte sind entscheidend.
- Eigener `tests/pressespiegel-direct.test.cjs`, überarbeiteter Browsertest mit Mock-GitHub-API und CI ergänzt. Nachweis realen GitHub-Speicherns mit einem **echten** nur auf Nutzerfreigabe erzeugten Token und späteres automatisches Auslesen stehen noch aus. Alle übrigen Zeitungsvorgaben (3–5 Tagesüberblick, 10–15 vertiefte Artikel, 15–20 Headlines, 7:45 Europe/Vienna, Lernen) bleiben bestehen.
- PR #24 weiterhin **unveröffentlichter Draft**; vollständige Vorschau, Livefreigabe und täglicher automatischer Veröffentlichungs-/Lernkreislauf noch nicht bestätigt.

## Verbindlicher letzter Stand vom 20.10.2026: nur zwei Kategorien

Der Nutzer wünscht ausdrücklich **keine dritte Highlight-Rubrik** und keinen „Der Tag auf einen Blick“-Überblick. Die Website soll einen **schlichten persönlichen Pressespiegel** darstellen, keine Zeitungsmarke:
1. **„Heute wichtig“** als anfänglich aktiver Tab, darunter **Österreich** und **International**. Journalistische Tagespriorisierung der wichtigsten Nachrichten, ähnlich ORF/Bild/Krone, nicht bloß ein Extrakt des persönlichen Fachprofils. Ziel 15–20 Originalschlagzeilen mit verifizierten Links, Quellen und Datum; bei zu wenig Material offen weniger.
2. **„Vertiefungen“** als zweiter Tab, Ziel 10–15 (maximal 15) **inhaltlich längere** Wirtschafts-, Technologie-, Produktivitäts- und Industrieartikel mit analytischer Einordnung, prioritär Handelsblatt, FAZ, SZ und andere hochwertige Medien, gelegentlich Zuckerl. Nicht nur Schlagzeilen.
Der Marketing-Satz unter „Morgenzeitung“, der dekorative Footer-Slogan und die separate Highlights-Sektion wurden entfernt. Im JSON `overview` nicht mehr erzeugen oder verwenden; Altarchive dürfen ansonsten lesbar bleiben. Kein neues drittes Nachrichtenformat einführen.

### Befristeter Integrationstest mit E-Mail-Bericht
- Auf ausdrücklichen Wunsch: drei einmalige künftige Testläufe **Di 27.10., Do 29.10., Sa 31.10.2026** (vormittags Wiener Zeit, flexible Ausführung). ChatGPT-Automation „Morgenzeitung Feedback-Tests“ mit `COUNT=3`; endet automatisch.
- Jeder Lauf prüft GitHub-CI und in `fabian-stoeckl/morgenzeitung-feedback` real das **Schreiben, PATCH-Aktualisieren und Zurücklesen** eines einzigen eindeutig als `[TEST – NICHT AUSWERTEN]` gekennzeichneten privaten Issues. Einträge sind strikt vom Interessenlernen ausgenommen.
- Einzelner zusammenfassender E-Mail-Bericht über Outlook an die vom Nutzer angegebene Adresse `fabian-stoeckl@hotmail.com` vorgesehen am **1.11.2026**. Bericht trennt nachgewiesene Connector-Writes, simulierte Browser-CI-Tests, noch fehlenden persönlichen Token-Browsertest und möglichen fehlenden kompletten Lernkreislauf. E-Mail erst nach bestätigtem Outlook-Versand als versendet bezeichnen. Einmaliger Bericht; Test endet damit.
- Testläufe über den GitHub-Connector sind ausdrücklich **nicht** mit einem echten Website-POST mit Benutzer-PAT gleichzusetzen. Vollständiger Website-End-to-End-Nachweis steht ohne persönliche Token-Einrichtung und Nutzervorschau aus. Keine Veröffentlichung oder PR-Merge ohne Freigabe.


## Veröffentlichung der Morgenzeitung – 20. Oktober 2026

- Der Nutzer hat die Veröffentlichung am 20.10.2026 ausdrücklich freigegeben. PR #24 wurde nach grünen Prüfungen `Verify Morgenzeitung` und `Verify site` mit Squash-Commit `c439f0bd6c0223e91a8d8f06f96f789e74ebe65d` in `main` gemergt. **Diese aktuelle Freigabe ersetzt die älteren Hinweise in diesem Protokoll, dass der PR noch Entwurf und nicht veröffentlicht sei.**
- Produktionspfad: `https://www.fabian-stoeckl.com/Privat/Pressespiegel/`. Quelle und UI in `main` verifiziert; unabhängiger öffentlicher HTTPS-Aufruf wurde beim Merge aus der ChatGPT-Umgebung nicht bestätigt. Dafür wurde ein eigenständiger read-only `Verify published Morgenzeitung` GitHub-Workflow in einem Folge-PR vorbereitet, der öffentliche HTML-/JS-/JSON-Dateien per HTTPS kontrolliert. Nur bei erfolgreicher Ausführung ist auch externe Auslieferung bestätigt.
- Design endgültig **genau zwei Tabs**, `Heute wichtig` (Österreich/International, initialer Tab) und `Vertiefungen` (Wirtschaft/Technologie/Produktivität, längere Analysen). Keine dritte Highlight-Rubrik, kein Marketing-Untertitel. Bestehende Ausgabe 18.10. ist **weiterhin nur eine 5-Artikel-Demo**; die tägliche Recherche- und automatische öffentliche JSON-Befüllung hat noch keinen überprüften erfolgreichen End-to-End-Lauf.
- Produktionscode der Rückmeldungen: ein Klick `Feedback speichern` nach einmaliger nutzerseitiger Einrichtung eines ausschließlich fürs private Feedback-Repo berechtigten Fine-grained Tokens (Issues: Read and write). Im Browser lokal dauerhaft gespeichert, wie im Einrichtungsdialog ausdrücklich gewarnt. GitHub-REST verwendet keinen optionalen Versions-Header, um Browser-CORS-Preflight-Probleme zu vermeiden. Vor der Veröffentlichung bestanden CI Unit-/Browsermocktests; reale direkte Speicherung über das vom Nutzer selbst verwaltete Browser-Token bleibt bis zu seinem Test **nicht nachgewiesen**.
- **Bestätigter privater Connector-Test unmittelbar nach Merge**: `fabian-stoeckl/morgenzeitung-feedback/issues/2`, Titel `[TEST – NICHT AUSWERTEN] Morgenzeitung Liveprüfung 2026-10-20`; erfolgreich neues Issue erzeugt, unverändert zurückgelesen, verändert (PATCH), den erwarteten Marker erneut exakt gelesen und geschlossen. Dieses Issue #2 sowie das frühere Test-Issue #1 und spätere explizite Test-Issues sind niemals als Nutzerfeedback/Lernsignal zu berücksichtigen. Der Test bestätigt die GitHub-Connector-Schreibstrecke, **nicht** den Browser-PAT-Test oder den Personaliserungs-End-to-End-Kreis.
- Drei weitere vereinbarte GitHub-/Feedbacktests 27./29./31.10.2026, Abschluss-E-Mail über Outlook geplant 01.11.2026, Aufräumerinnerung 02.11.2026. Da der Nutzer ausdrücklich eigenes Feedback senden will, ist **kein echter Eingang** spätestens am Ende der Testwoche eine deutliche Warnung; aber die persönliche Einrichtung bzw. noch fehlende regelmäßige aktuelle Artikel sind als Alternativerklärungen zu prüfen.
- Für zukünftige **redaktionelle** Datums-Ausgaben ist die ausdrückliche Nutzergenehmigung zur Website-Veröffentlichung maßgeblich; nur Daten-JSON aus dem dokumentierten Schema und Index aktualisieren, über PR/CI, keine technischen Site-Änderungen ohne erneute Vorschau/Freigabe, kein Direktcommit auf `main`.

## Änderung 20.10.2026 – Getrennte Rubriken und gemeinsames Feedback

- Echte Nutzerübertragung aus dem Browser in das private Feedback-Repository ist separat überprüft worden. Konkrete Bewertungen, zugehörige Issue-Nummern, Kommentare und individuelle Präferenzen bleiben **ausschließlich privat** und dürfen weder in diese öffentliche Dokumentation noch in öffentliches Website-JSON übernommen werden. Die Lernrückkopplung im Folgelauf muss gesondert überprüft werden.
- Auf neuen ausdrücklichen Nutzerwunsch GitHub-Verbindungs-/Trennfunktion am **Ende nach dem Gesamt-Feedback** statt in der Blattmitte platzieren. Bestehende im Browser gespeicherte PATs nicht löschen oder ändern.
- **Beide Rubriken erhalten dieselbe Bewertung:** jeweils drei Optionen `Sehr relevant`, `Teilweise relevant`, `Nicht relevant` und optionalen freien Grund je Eintrag, auch für nationale/internationale Kurzmeldungen. Buttons in beiden Tabs sowie der Haupt-Feedbackbutton senden stets gemeinsam alle bisher ausgewählten News- und Vertiefungsbewertungen samt Gesamttext. Kein separates Issue pro Rubrik. Gesendete ältere Bewertungen aus dem bereits bestehenden privaten Issue vor jeder PATCH-Änderung erneut lesen und mit neuem Feedback zusammenführen; alte Nachrichtensignale dürfen beim Speichern aus dem anderen Tab niemals gelöscht werden. Datumsspezifische Issue-Nummer und Bewertung bleiben privat. Frühere Sammelbewertungen ohne explizites `Bereich`-Feld weiterhin als Vertiefungen lesen, neues Format enthält zusätzlich je Block `Bereich: Heute wichtig` oder `Bereich: Vertiefungen`.
- **Kategorien überschneiden sich nicht:** Keine identische URL (inkl. kanonischer Links ohne Tracking), kein identischer Ereignisschlüssel und keine inhaltlich gleiche Meldung unter beiden Rubriken. Überschneidungen medienübergreifend bei der redaktionellen Auswahl nach Sinn/Story überprüfen (Titelvergleich allein ist keine vollständige Garantie). Nachricht = breit und aktuell, Vertiefung = eigenständiger längerer Hintergrund/Analyse, auch thematisch stärker Wirtschafts-/Technologie-/Produktivitätsfokus. CI prüft Duplikate in allen veröffentlichten Datums-JSONs, ein zusätzlicher Browserfilter entfernt als letzte Verteidigung versehentlich doppelte News. Überlappungen innerhalb der Rubrik ebenfalls vermeiden.
- Die bisherige beschränkte ORF-Demo 18.10. wurde in 3 **verschiedene** österreichische Nachrichten und 2 **andere** vertiefende Artikel getrennt. Sie bleibt ausdrücklich nur eine reduzierte, alte Vorschau, keine 15–20 / 10–15 täglich kuratierte reale Ausgabe. Deduplikationsschutz in `services/morgenzeitung/core.py` sowie CI-Unit-/Browsertests ergänzt.
- Keine neue Hostinginfrastruktur; Entwurf derzeit auf `codex/morgenzeitung-feedback-footer-dedupe` und erst nach bestandenen CI-Tests plus Vorschau/Freigabe veröffentlichen. Vorherige PRs/Datumsstände im Hauptzweig unverändert.

## Anpassung: Desktop-Bewertungszeile und einmalige Token-Rotation (20. Oktober 2026)

- In der Desktopansicht ab 761 px steht der Schalter **„Optional begründen“** in derselben Zeile wie alle drei Bewertungsoptionen. Das einblendbare Textfeld bleibt bei aufgeklapptem Zustand in der rechten Spalte; mobil (bis 760 px) bleibt die bewährte vertikale Darstellung bestehen. Bewertungen und gemeinsamer privater GitHub-Versand bleiben unverändert.
- Auf ausdrücklichen Nutzerwunsch wird **einmalig** beim erstmaligen Laden der aktualisierten Website der bisher lokal im Browser gespeicherte GitHub-Fine-grained-Token (localStorage-Key `morgenzeitung:github-token:v1`) gelöscht und die erstmalige Löschung mit `morgenzeitung:github-token-reset:2026-10-20` markiert. Alle `morgenzeitung:github-receipts:v1`-Einträge und tatsächlichen GitHub-Issues bleiben erhalten; sie sind für spätere Aktualisierungen wichtig. Neu verbundene Tokens werden nach dieser einmaligen Rotation nicht erneut entfernt. Diese Löschung erfolgt erst bei erneutem Seitenbesuch im jeweiligen Browser/Profil und ist **kein Remote-Widerruf**.
- Der Nutzer muss den bisherigen Token zusätzlich in GitHub unter https://github.com/settings/personal-access-tokens **widerrufen**, um dessen API-Zugriff tatsächlich zu sperren, und dort einen neuen ausschließlich für `fabian-stoeckl/morgenzeitung-feedback` mit `Issues: Read and write` erzeugen. Den neuen Token auf der Website nach dem automatischen lokalen Reset einmalig unten verbinden; nicht im Chat mitteilen. Tests müssen sowohl die einmalige Löschung als auch Persistenz des neuen Tokens und Erhalt vorhandener Feedback-Verweise nachweisen.
