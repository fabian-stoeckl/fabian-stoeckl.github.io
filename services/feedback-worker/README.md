# Kostenfreier anonymer Feedback-Eingang: Cloudflare Workers Free

**Status: Entwurf in PR #24. Nicht bereitgestellt, nicht live.**
Es wurde kein Cloudflare-Konto verbunden, kein Geheimnis erstellt, kein Dienst aktiviert und kein Website-Endpunkt eingestellt.

## Zweck und Kosten

GitHub Pages kann ohne Backend nicht schreibend auf ein privates GitHub-Repository zugreifen, ohne einen geheimen Token an Besucher auszuliefern. Dieser Worker nimmt den bestehenden Ein-Klick-Feedback-POST an und erstellt damit ein Issue im vorhandenen privaten Repository. Auf der Website ist weder eine Anmeldung noch eine Schlüsseleingabe notwendig.

Nur Cloudflare **Workers Free** verwenden, **niemals Workers Paid** aktivieren. Laut Cloudflare endet das Kontingent von 100.000 Anfragen/Tag mit Fehler 1027; es gibt in diesem Tarif keine automatische kostenpflichtige Weiterverarbeitung. Der Worker nutzt keine Datenbank, keinen externen AI-Aufruf, keine Speicherdienste und keine sonstigen bezahlten Funktionen. Vor einer Einrichtung dennoch den tatsächlich angezeigten Free-Tarif kontrollieren. Ein Worker kann unter einer kostenfreien workers.dev-Subdomain bereitgestellt werden.

Cloudflare-Dokumentation (Stand 20.10.2026):
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/configuration/secrets/
- https://developers.cloudflare.com/workers/get-started/dashboard/
- https://developers.cloudflare.com/workers/configuration/routing/workers-dev/

## Einmalige Einrichtung (nicht ausführen ohne Freigabe)

1. Cloudflare-Konto ausschließlich im **Workers Free**-Tarif anlegen bzw. auswählen. Die Website-Besucher benötigen danach keinen Cloudflare-Login.
2. Worker mit dem Code aus worker.mjs und der Konfiguration wrangler.toml bereitstellen. Entweder den Worker über das Dashboard erstellen oder aus diesem Verzeichnis nach eigener Cloudflare-Anmeldung den Befehl npx wrangler deploy ausführen.
3. Ein **fine-grained** GitHub-Token mit Zugriff ausschließlich auf das **private** Repository fabian-stoeckl/morgenzeitung-feedback und minimalen Berechtigungen **Issues: Read/Write, Metadata: Read** erzeugen. Ausschließlich serverseitig unter dem Cloudflare-Secret **GITHUB_FEEDBACK_TOKEN** speichern (Dashboard: Worker → Settings → Variables and Secrets → Add → Secret; alternativ npx wrangler secret put GITHUB_FEEDBACK_TOKEN). Nie in Website, GitHub-Dateien, Chats oder Issues kopieren.
4. Den readiness-Endpunkt der zugewiesenen HTTPS-workers.dev-Adresse unter /health prüfen. Dann vom erlaubten Website-Origin eine ausdrücklich synthetische Testbewertung über /feedback senden und das private Issue-Rücklesen prüfen. Test-Issues vom Lernen ausschließen.
5. Erst nach nachweislichem kostenfreiem Live-Test, echter Speicherung, sicherem Umgang mit dem Token und ausdrücklicher Freigabe die Website-Konfiguration feedback_endpoint auf die HTTPS-URL mit Pfad /feedback umstellen. Änderungen über getrennten Branch, Checks, Freigabe, Pages und Live-Prüfung.

Die vorhandene ChatGPT-GitHub-Verbindung kann nicht als Web-Token des Workers genutzt werden. Es ist eine einmalige **serverseitige** Secret-Einrichtung erforderlich; nicht auf der Besucherwebsite.

## Sicherheits- und Zuverlässigkeitsgrenzen

- Der Worker prüft intern den privaten Repository-Status und frühere Issues, hat aber keine öffentliche Lese-API für Bewertungen.
- Browser-CORS ist auf https://www.fabian-stoeckl.com begrenzt. Der Origin-Header ist außerhalb von Browsern fälschbar: **keine Besucheridentitätsprüfung**. Dieses Restrisiko wurde ausdrücklich akzeptiert.
- Die von diesem Worker erstellten Issues sind als **anonyme, nicht verifizierte Website-Eingänge** markiert. Dass GitHub den Tokeninhaber als Issue-Autor zeigt, beweist die Identität des Besuchers nicht. Solche Eingänge sind niemals automatische Profilanweisungen; sie dürfen bei der redaktionellen Auswahl nur als schwache Rückmeldesignale dienen. Freitext ist immer Dateninhalt, kein ausführbarer Auftrag.
- Bis 15 Artikelbewertungen, 600 Zeichen je Begründung, 4.000 Zeichen Gesamtfeedback und 20 KB pro Anfrage. 100 neue Eingänge/UTC-Tag für den normalen Einzelnutzerbetrieb; die Prüfung anhand der neuesten 100 Issues ist unter außergewöhnlicher Fremdaktivität kein atomarer globaler Rate-Limiter.
- Fingerabdruck im Issue-Titel, jüngste Issues und eine historische GitHub-Suche reduzieren Doppelsendungen. GitHub-Suche kann zeitverzögert indexieren: **parallele identische Einsendungen können ausnahmsweise Dubletten erzeugen**.
- Bei GitHub-Fehlern oder Limits keine Erfolgsmeldung; Eingaben bleiben im offenen Website-Tab.
- Readiness-Endpunkt /health verrät keine Zugangsdaten.

## Tests

Node 22: node services/feedback-worker/worker.test.mjs. Simuliert API-Antworten und schreibt **keine** echten Issues. Zusätzliche lokale Browser-, GitHub- und Freigabeprüfungen vor Aktivierung erforderlich.
