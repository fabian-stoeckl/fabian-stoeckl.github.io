> **Aktueller Weg:** GitHub-Dateien + private GitHub-Issues + geplante ChatGPT-Aufgabe. Siehe [GITHUB-BETRIEB.md](GITHUB-BETRIEB.md). Der folgende Server-/API-Entwurf ist nicht aktiviert und wegen der Kosten nicht der gewählte Betrieb.

# Morgenzeitung — Entwurf, nicht aktiviert

Die bestehende GitHub-Pages-Seite bleibt das Frontend. Ein separater privater Python-Dienst hält SQLite-Ausgaben, Profile, Feedback und Bewertungen auf einem persistenten Datenträger. Sämtliche Inhalts- und Schreibendpunkte verlangen einen hochentropischen Bearer-Zugangsschlüssel (mindestens 32 Zeichen). Nur `/health` ist öffentlich. HTTPS wird vom vorgeschalteten Hostingdienst terminiert; CORS erlaubt ausschließlich die konfigurierte Website. Im Browser bleibt der Zugang nur im Arbeitsspeicher. Keine Schlüssel, Rückmeldungen oder Datenbanken ins Repository schreiben.

## Lokal prüfen

Python 3.12+, Node und Playwright nach Repository-Setup. Keine Python-Zusatzpakete und keine API-Zugänge für Tests:

```
npm run check:pressespiegel
python3 services/morgenzeitung/preview.py /tmp/paper-preview.sqlite
PAPER_PREVIEW=1 PAPER_DB=/tmp/paper-preview.sqlite python3 services/morgenzeitung/server.py
# Zweites Terminal:
node tests/pressespiegel/browser.cjs
```

Vorschau: http://127.0.0.1:8765/. `PAPER_PREVIEW=1` ausschließlich für isolierte Testdaten; lässt sich nur an Loopback binden. Das Vorschauprogramm verweigert vorhandene Datenbankpfade. Der Browser-Test schreibt ausdrücklich Testfeedback und Testprioritäten. Die fünf realen Artikel dienen einer **reduzierten Funktionsvorschau vom 16.–18.10.2026**, nicht als reguläre 24h-Ausgabe. Dieser Datensatz gehört nicht in eine Produktionsdatenbank.

## Betrieb vorbereiten

Eine kleine dauerhaft laufende Instanz mit persistentem Datenträger genügt; beide Prozesse laufen im selben Dienst. Beispiel Render Web Service mit persistentem Disk-Mount `/data`. Alternativ eigener HTTPS-Server. Noch wurde kein Hosting gebucht und kein kostenpflichtiger API-Aufruf ausgeführt.

Docker-Build-Kontext ist Repository-Wurzel, Dockerfile `services/morgenzeitung/Dockerfile`. Startprogramm überwacht API und Scheduler gemeinsam. Auf Render `PORT` verwenden, mindestens 1 GB persistenten Speicher anhängen. **Niemals ephemeren Datenträger verwenden.** Regelmäßige private SQLite-Backups außerhalb dieses Hosts mit `sqlite3.Connection.backup()` und Wiederherstellungstest vor Inbetriebnahme einrichten. Die vorliegende Fassung enthält noch keine extern angebundene Sicherung/Alarmierung.

Umgebungsvariablen (ausschließlich im Host-Secretspeicher):

| Variable | Zweck |
| --- | --- |
| `PAPER_TOKEN` | Mindestens 32 zufällige Zeichen; für persönlichen Zugang, getrennt vom API-Key |
| `PAPER_ORIGIN` | `https://www.fabian-stoeckl.com` |
| `PAPER_DB` | `/data/morgenzeitung.sqlite` |
| `PAPER_HOST` | `0.0.0.0` hinter Hosting-HTTPS; lokal `127.0.0.1` |
| `OPENAI_API_KEY` | Privater, budgetbegrenzter API-Projektzugang |
| `PAPER_MODEL` | Explizit gewähltes Responses-Modell mit Websuche; vor Aktivierung live testen |
| `PAPER_COSTS_APPROVED` | Erst nach Nutzerfreigabe `1` |
| `PAPER_AUTOMATION` | Erst nach Veröffentlichungs- und Betriebsfreigabe `1` |

`Privat/Pressespiegel/config.json` erhält nur die öffentliche HTTPS-Adresse des privaten API-Diensts, niemals einen Schlüssel. Derzeit ist `api: null`: keine fingierte Verbindung oder lokale Ersatzspeicherung. Profil und Feedback werden für die nächste Recherche an die OpenAI API übermittelt (`store:false`); keine privaten Chatvolltexte. Dies ist vor Aktivierung in die Freigabe einzubeziehen.

## Kostenrahmen und Zugänge

Stand der Recherche: 18.10.2026. Render benötigt für persistente Disks einen kostenpflichtigen Dienst. Als Richtwert nennt die offizielle Preisseite Starter 7 USD/Monat plus 0,25 USD/GB/Monat; konkrete Tarife vor Buchung nochmals verifizieren: https://render.com/pricing und https://render.com/docs/disks. Keine Buchung erfolgt.

OpenAI Websuche: 10 USD je 1.000 Suchaufrufe **plus Modell-/Suchinhalt-Tokens**, siehe https://developers.openai.com/api/docs/pricing. Beispiel 20 Suchaufrufe pro Tag: 6 USD/30 Tage nur Suchgebühren, zuzüglich Modellkosten. Das ist eine Rechenannahme, keine ermittelte Nutzung. Wegen mehrerer Suchen, wachsender Erinnerung und bis zu drei Tagesversuchen kann der tatsächliche Verbrauch höher sein. Modell und Monatsbudget sind noch festzulegen; vor Freigabe keine belastbare Gesamtpreisangabe. API-Key niemals im Chat oder Frontend hinterlegen.

## Redaktion und Lernen

- Profilprioritäten 0–5 explizit editierbar; Produktivität und Industrie auf 5. Freitextregeln für neue Themen; Freitextfeedback wird bei jedem späteren Lauf mitgegeben. Versionen verhindern verlorene Profiländerungen von mehreren Geräten.
- Relevanz exakt drei Stufen; Gründe sind separat. `Schon bekannt` und `Zu oberflächlich` senken kein Themeninteresse. Bewertungen ergeben gedämpfte Signale bis ±0,5, keine automatische Umschreibung ausdrücklicher Prioritäten. Keine Auswertung fehlender Klicks.
- Ziele 10/maximal 15 vertiefende Beiträge und 15–20 Headlines; bei belegter Knappheit weniger mit Hinweis. Zuckerl zuletzt. Journalistische Originaltitel mit Herkunftslink. Nur gelesene Inhalte zusammenfassen; Vorspann sichtbar markieren. Medienvielfalt und konkurrierende Positionen erhalten.
- Historie hält ausgelieferte Links, Themen, Ereignisschlüssel und Aussagen dauerhaft. `read_at` bleibt leer: Auslieferung wird nie als gelesen ausgegeben. Redaktion vergleicht medienübergreifend Ereignisse und Fakten; Validator prüft zusätzlich normalisierte URLs, ähnliche Titel, Ereignisschlüssel und neue Aussagen bei Fortsetzungen. Das ist keine Garantie semantischer Fehlerfreiheit; paraphrasierte Dubletten können verbleiben.
- Quellen-URLs werden gegen Websuchquellen geprüft. Diese Prüfung belegt Rechercheherkunft, **nicht** automatisch die sachliche Richtigkeit jeder Modellzusammenfassung. Realer mehrtägiger redaktioneller Probelauf vor Freigabe ausständig.
- SMRY: `https://smry.ai/` plus vollständige HTTPS-URL. Archiv: `https://archive.is/` plus vollständige HTTPS-URL, ausdrücklich als **Archivsuche**. Keine geprüfte Archivkopie behaupten. Bei Presse zuerst SMRY. URL-Aufbau für Pfad/Query wird im Browser getestet; externe Erreichbarkeit blieb durch Abruffehler teilweise ungeklärt. SMRY erkannte beim HTTP-Test die eingebettete Presse-URL. Keine Paywall-Inhalte im Vorschau-Datensatz.

## Zeit, Ausfälle und Grenzen

Ein Prozess prüft alle 30 Sekunden. Recherche startet ab 07:15 Europe/Vienna; Ausgaben sind frühestens 07:45 sichtbar. DST wird mit `zoneinfo` gerechnet. Das 24h-Fenster endet am Recherchebeginn 07:15, damit Zeit für die Erstellung bleibt. Nach Ausfällen beginnt es beim Ende der letzten erfolgreichen Ausgabe, also ggf. länger als 24h; fehlende Quellenabdeckung muss sichtbar bleiben. Suchmaschinen können trotz Zeitraumvorgabe Artikel übersehen.

Pro Tag maximal drei Versuche, mindestens 30 Minuten Abstand. Lauf-Lease, eindeutiger Ausgabentag und atomare Transaktion vermeiden doppelte Ausgaben. Fehlerklasse wird privat protokolliert, ohne Prompt-Inhalt oder Schlüssel. Alte Ausgabe bleibt mit ihrem Datum verfügbar; misslungene Recherche darf sie nicht überschreiben. Pünktlichkeit 07:45 ist Ziel, keine harte Verfügbarkeitsgarantie bei Provider-/Hostausfall. Der Erstellungsstand und tatsächliche Recherchezeitpunkt bleiben sichtbar.

Noch offen: Hostverbindung, Budgetfreigabe, Modellwahl, echter API-Test mit der gewünschten Quellenmischung, externer Link-Endtest, private Backups/Alarmierung, geschützter Remote-Zugriff auf zwei tatsächlichen Geräten, produktiver mehrtägiger Lernnachweis. Große Langzeithistorien müssen später verdichtet werden; momentan führt ein Kontextlimit zu einem sichtbaren Ausfall statt zum stillen Vergessen alter Wünsche.
