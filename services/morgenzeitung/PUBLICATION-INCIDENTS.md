# Morgenzeitung – verbindliche Fehlerbehandlung im Produktivbetrieb (25.10.2026)

## Ziel und Grundsatz

Eine Tagesausgabe darf nicht endlos an normalen, wechselnden Publisher-Antworten
(Consent, HTTP 401/403, RSS-Fenster, HEAD-/GET-Unterschied, Weiterleitung)
scheitern. **Technischer Nichtzugriff ist weder Beweis für einen erfundenen Artikel
noch positiver Beleg für dessen Existenz.** Falsche Metadaten, 404, manipulierte
Originaldaten, falsche Artikelidentität oder unsichere Weiterleitungen bleiben
harte Fehler. **Kein Verlags-Whitelist und kein Paywall-Ausschluss bei Recherche.**

## Automatische Prüfkette

1. Recherche themenoffen (auch fremdsprachige/pflichtige Verlage), Kandidaten
   nach Titel, offizieller Original-HTTPS-URL, exaktem Erscheinungszeitpunkt,
   Quelle und `verified:true` prüfen. Vor der Auswahl echten vollständigen
   Kandidatenpool, Profile, vollständige Issue-Versionen und Selektorparameter
   unveränderlich PRIVAT speichern, SHA und Remote-Readback prüfen. Hier nicht
   ersatzweise angebliche Beweise nach Publikation rekonstruieren.
2. Baseline und personalisierte Auswahl mit den *identischen* archivierten
   Daten berechnen, Reihenfolge und IDs exakt gegen den PR-Entwurf prüfen.
   Das ist die notwendige, **verbindliche** Prepublication-Schranke.
3. Für jeden veröffentlichten Artikel zuerst offiziellen Artikel aufrufen:
   HEAD, bei Verweigerung GET, begrenzte Retries. Nur kanonische sichere,
   identische Verlagsartikel-Weiterleitungen und tatsächlich geprüfte
   offizielle Verlagsalternativen akzeptieren; keine Login-/Consent-Seite
   und keine 401 als HTTP-PASS behandeln.
4. Metadatenkonflikt (Datum/Uhrzeit), falsche Artikelidentität,
   fremde Publisher-Ziele, kaputte URL und HTTP 404 = **FAIL**,
   Publikation nicht mergen. Automatisch Diagnose im CI-Log
   (betroffene Artikel-URL und Fehlerkategorie) ausgeben.
5. Ein auf der Originaldomain durch Consent blockierter Artikel kann
   ggf. durch einen *aktuell vorhandenen* offiziellen, exakten
   RSS-Eintrag (Storypfad, Titel und Veröffentlichungsminute) bestätigt
   werden. **Ein älterer Beitrag, der aus dem rollierenden Feed
   herausgefallen ist, ist dadurch nicht widerlegt.** Ausschließlich
   dieser eng überprüfte Zustand (oder vorübergehend nicht abrufbarer
   Publisher-Feed nach bestätigter Consent-Schranke) wird vom Gate mit
   `INCONCLUSIVE` ausgewiesen; niemals als Quellenverifikation.
6. Maximal **zwei** solche unabgeschlossenen Quellen je Ausgabe erlaubt.
   Bei drei oder mehr: FAIL und inhaltliche Alternativen prüfen,
   ohne archivierte Kandidatendaten unbemerkt auszutauschen.
   Das Gate kann bei einer oder zwei Ausnahmen **nur den unabhängigen
   Auswahl-Replay als PASS**, aber **Quellenabnahme als PARTIAL** melden;
   die dauerhafte Gesamt-/Lernabnahme bleibt bis zur tatsächlichen
   Verifizierung ebenfalls PARTIAL. Echte Quellenhinweise oder bewusste
   Zugriffsbeschränkung nicht aus UI/Logs entfernen.
7. PR nur nach grünen technischen Tests inklusive Gate,
   keine roten Checks mergen. Danach echten main-Commit,
   Pages-Veröffentlichung und öffentliches HTTPS
   (Index, Tagesdatum, IDs und Reihenfolge) prüfen.
   Privat `runs/YYYY-MM-DD.json` mit Profil-SHA, Original-Snapshot-
   Commit, Issue-Versionen, PR/Merge/HTTPS und kausalem Vergleich
   anlegen, zurücklesen und eigenständig auditieren.
8. Fehlerbehandlung im täglichen Haupt-/Ersatzlauf in dieser
   Reihenfolge: (a) GitHub Actions-Logs bis zum ersten tatsächlichen
   Ausnahmefehler lesen; (b) Quellen- vs. Token-/Snapshot-/Auswahl- vs.
   Web-/CI-Fehler unterscheiden; (c) zugängliches Publisheroriginal
   gegenprüfen; (d) minimalen Regressionstest mit Positiv- UND
   Negativfall hinzufügen; (e) Fix auf Branch, PR, alle CI grün,
   Merge; (f) ursprünglichen Ausgabe-PR erneut gegen aktuelles main
   testen; (g) HTTPS + private Provenienz/Acceptance rückprüfen.
   Keine blinden Workarounds, keine neue Aufgabe pro Fehlversuch.
   Bei dauerhaftem Problem genau die Blockade und die nötige
   Entscheidung ausweisen.
9. Zugang: Fehlt in der ChatGPT-Laufzeit der
   `MORGENZEITUNG_FEEDBACK_TOKEN`, aber ist der bereits authentifizierte
   GitHub-Connector verfügbar, den geprüften Connector-Capture nutzen.
   Secrets niemals aus GitHub Actions exportieren oder vom Nutzer im
   Chat anfordern. Fehlende private Originale = **FAIL**.
10. **ETF-Dateien und ETF-Update-Automatik dürfen bei keiner Reparatur
    verändert werden.** Kein genereller `main`-Schreibschutz, der
    bestehende ETF-Pushes blockiert.

## Kontrollstatus

- **PASS**: private Originale/Feedback/Profil, reproduzierbare kausale
  Auswahländerung, PR-Gate, erfolgreiches Merge, öffentliches HTTPS
  und private S7-Persistenz/Readback belegt; Quellenstatus separat.
- **PARTIAL**: notwendige Auswahl- und Publikationsmerkmale belegt,
  aber einzelne Publisher vom GitHub-Runnner nicht unabhängig abrufbar
  oder Gesamtprovenienz noch nicht vollständig.
- **FAIL**: fehlende Originale, gegensätzliche Verlagsmetadaten,
  andere Artikel-ID, tote URL, zu viele unbestätigte Quellen,
  nicht veröffentlichte Ausgabe oder rote Pflichtprüfungen.

## Wiederkehrende Kontrolle

Bestehende tägliche ChatGPT-Morgenzeitung, Ersatzlauf und Feedback-Lerntest
verwenden diesen Ablauf; keine zusätzliche kostenpflichtige Infrastruktur
und keine weitere Scheduled Task. Nur der schon vorhandene tägliche
Kontrolllauf prüft Folgeausgaben, Ursachen und Verbesserungen.

## Nachträgliche unabhängige Abnahme – append only

Die erste `audits/YYYY-MM-DD-acceptance.json` ist unveränderliche
historische Evidenz (auch wenn sie wegen noch ausstehender Verifikation
`PARTIAL` meldet). Eine spätere erfolgreiche Nachprüfung darf diese Datei
**niemals überschreiben**. Stattdessen:

- Die echten Original-Feedback-Issues, sämtliche Betroffenen-Artikel-IDs
  aus älteren **öffentlichen** Editionen, profilierte Metadaten und die
  gesonderten Test-Issues unabhängig abgleichen. Familien-Lernsignal
  deterministisch neu berechnen und mit originalem Profil-Snapshot vergleichen.
  Ergebnis privat unter
  `audits/YYYY-MM-DD-real-feedback-and-profile-verification.json`
  unveränderlich speichern und zurücklesen.
- Die Original-Snapshots, vor der Auswahl gespeicherten Versionen, publizierten
  geordneten IDs und GitHub-Commit-Chronologie mit der echten HTTPS-Ausgabe
  abgleichen. `runs/YYYY-MM-DD.json` nach der Veröffentlichung als S7-Report
  **mit erhaltener Fehlversuch-Historie** aktualisieren und per Remote-Readback
  ausdrücklich bestätigen; fehlende unabhängige Beweise nie durch Behauptungen
  ersetzen.
- Nur wenn alle Komponenten tatsächlich nachgewiesen wurden, eine gesonderte
  `audits/YYYY-MM-DD-acceptance-final.json` anlegen. Diese ergänzt die
  historische `PARTIAL`-Abnahme. Der tägliche unabhängige
  `morgenzeitung_daily_acceptance.py` kann diese Ergänzung ausschließlich
  bei übereinstimmendem echtem S7-Commit, Feedback-Provenienz,
  deterministischem Profil und HTTPS-Lernwirkung berücksichtigen.
  Keine synthetischen Akzeptanzbelege. Die journalismusbezogene
  Publisher-HTTP-Unsicherheit bleibt separat `PARTIAL`, falls GitHub
  Zugriffsbeschränkungen nicht unabhängig beheben kann.

## Unveränderliche Tagesabnahme auch nach fehlgeschlagenen GitHub-Reruns

Die automatische Tagesabnahme archiviert ihren unabhängigen Bericht unter
`audits/YYYY-MM-DD-daily-acceptance-RUNID-attempt-ATTEMPT.json`.
GitHub vergibt bei einem erneuten Versuch dieselbe `GITHUB_RUN_ID`, aber eine
höhere `GITHUB_RUN_ATTEMPT`: deshalb bekommt jeder Versuch eine neue Datei,
statt durch einen Konflikt mit einem unveränderlichen früheren Ergebnis
zu scheitern. Aufbewahrung/Readback und echtes PARTIAL/FAIL bleiben erhalten.
Manuelle Ausführung kann `--run-id` mit eigener numerischer Kennung verwenden.
