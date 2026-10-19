# Anonymer Feedback-Eingang

Vorbereiteter, nicht bereitgestellter Dienst. Nutzer akzeptiert die fehlende Identitätsprüfung. Die Website braucht keine Anmeldung und keinen Schlüssel.

Start: `python3 services/feedback-relay/server.py`; PORT vom Host. Ausschließlich serverseitig `GITHUB_FEEDBACK_TOKEN` mit Issues read/write für `fabian-stoeckl/morgenzeitung-feedback` setzen; nie im Chat, Repository oder Browser hinterlegen. Der ChatGPT-Connector kann seine interne Berechtigung nicht an diesen Dienst übertragen.

POST /feedback erhält date, ratings (id/value/reason), feedback. CORS begrenzt Browseraufrufe auf https://www.fabian-stoeckl.com; es ist keine Identitätsprüfung. GitHub bleibt dauerhaftes Gedächtnis, kein lokaler Datenspeicher. Alle Antworten sind schreibbezogen; keine privaten Artikelbewertungen abrufbar. Gleiche Inhalte werden nicht mehrfach angelegt. Limit 100 neue Eingänge pro UTC-Tag bleibt durch GitHub-Historie auch nach Neustart erhalten.

Bereitstellung noch blockiert: kein serverseitiger GitHub-Zugang und kein kostenbegrenzt verifizierter Host. Render Free allein garantiert bei hinterlegter Zahlungsmethode keine Nullkosten für Mehrverbrauch. Keine kostenpflichtige Ressource, keine Datenbank und keine Disk erstellen. Keine Aktivierung bis die Nullkostenanforderung erfüllt ist. Nach sicherer Einrichtung config.json feedback_endpoint auf HTTPS-Adresse mit Pfad /feedback setzen und echten Speichern/Rücklesen-Test durchführen.

Tests simulieren GitHub-Schreiben; sie sind kein Live-Nachweis.
