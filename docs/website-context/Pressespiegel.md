<!-- website-area: {"name":"Pressespiegel","paths":["Privat/Pressespiegel/"]} -->
# Bereichsprotokoll: Pressespiegel

**Stand:** 28.10.2026. **Status:** Neuer Pressespiegel veröffentlicht; automatischer täglicher Concierge-Ablauf aktiv.

## Auftrag und Konzept

Nutzer wünscht vollständigen Neustart: Ein täglicher automatischer Lauf liest Rückmeldungen, verbessert die natürlich formulierte Interessenbeschreibung, speichert sie, nutzt sie zur eigentlichen Recherche und publiziert die besten Artikel auf der Website. Keine manuelle Promptbedienung nötig. Zwei getrennte Prompts, nacheinander im selben Morgenlauf; keine Rankingengine, Themengewichte, festen Lernschwellen, Gegenfaktual-Simulationen oder zusätzlichen Rechercheplan-Dateien.

Neue Website `Privat/Pressespiegel/`; zwei Prompts `services/pressespiegel/INTERESSEN.md` und `RECHERCHE.md`; einfache Betriebs-/Schemaangaben in README. Beschreibung privat in `pressespiegel/interessen.md`, begleitet von knapper Änderungsnotiz und gelesenen Feedbackversionen. Browser kann den Text anzeigen/kopieren; Kopieren ist optional. Bewertungen und freie Wünsche speichern neue Ereignisse im bestehenden privaten Repository. Unbestätigte Übertragungen werden mit derselben Kennung erneut geprüft, kein Überschreiben anderer Geräte.

## Inhalte und Übergang

Rubriken Heute wichtig und Für dich ausgewählt. Die Quellenliste ist Anregung, keine Pflichtliste. Recherche journalistisch, offene Suchfragen aus dem Beschreibungstext; Qualität, Originalbelege und unabhängige Nachrichtenrelevanz bleiben wichtig. Technische Tests sind keine Faktenprüfung.

Startausgabe vom 28.10. übernimmt die vorhandenen belegten Artikel als sichtbar gekennzeichnete historische Ausgabe; keine neu erfolgte Recherche behauptet. Alte Zeitung, Artikel-IDs und Bewertungen bleiben erhalten. Kachel im Privatbereich führt zum neuen Reader, bestehende ETF-/Skill-Kacheln unverändert.

Der bestehende tägliche Lauf wird nach erfolgreicher Veröffentlichung auf die zwei neuen Prompts umgestellt: 06:45 Europe/Vienna, Ziel Veröffentlichung bis 07:45. Die bisherige separate V3-Störungswache wird pausiert; keine parallele Zeitungserzeugung. Die befristete alte Score-Lernmessung entfällt. Fehler im täglichen Lauf selbst melden und letzte gültige Ausgabe erhalten.

## Umsetzung und Prüfung

Ausgangs-/Rücknahmebasis `137161e28e2cdcbc707152085cd46484a994e3ed`, Branch `feat/pressespiegel-simple`. Expliziter Auftrag zum autonomen täglichen Veröffentlichen liegt vor. Neubau enthält eigene Anzeige-, Feedback- und Schemafunktionen, keine Imports aus dem V3-Reader. Lokale neue Unit-Tests und mobile/Desktop-Browserprüfung einschließlich abgebrochener Antwort nach erfolgreichem Speichern bestanden. Weitere CI-/Produktionschecks und privater Profil-Readback vor Aktivierung erforderlich.

## Offen

PR/CI, private Startbeschreibung, Deployment/Live-Abnahme und tatsächliche Umstellung des vorhandenen Morgenlaufs dokumentieren. Erster autonomer Lauf nach neuem Konzept steht noch aus. Historisches Material nicht als Beleg für neue Recherche- oder Lernqualität darstellen.

### Geprüfter Entwurfsstand

Fünf neue Python-Tests und mobile/Desktop-Tests bei 390/1440 Pixeln bestanden, einschließlich Lesen der Beschreibung, Bewertungen/Freitext und Retry nach verloren gegangener Speicherbestätigung ohne doppeltes Issue. Alte 96 Python-Regressionen, JS-Tests und Kontextprüfung weiterhin erfolgreich. Private Startbeschreibung mit Herkunftsnotiz und Issue-Version über privaten PR #11 zusammengeführt; ursprüngliche Daten unverändert. Kein autonomer neuer Recherchelauf vorgetäuscht. Erst nach Bereitstellung wird der vorhandene Tageslauf umgestellt.


## Abschluss 28.10.2026 – live und automatisch eingerichtet

Public PR [#241](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/241) nach allen erfolgreichen PR-Prüfungen zusammengeführt: geprüfter Head `85e52b7ee80c0b01eb45e0d70469ba3dbab45cd3`, Merge `967eb87c3a3fc360e5f352dfacdd32d6a885a802`. Pages-Bereitstellung [40722073337](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/actions/runs/40722073337) erfolgreich. Sieben produktive Dateien (Reader, drei lokale Assets, Index, Startausgabe, Privat-Einstieg) per HTTPS 200 bytegleich zum getesteten Stand gelesen. Mobile/Desktop-Darstellung lokal visuell und im Browser geprüft; dies ist keine separate visuelle Live-Browserprüfung.

Private Startbeschreibung, Änderungsnotiz und Zustand über privaten PR #11 zusammengeführt, alle drei Dateien identisch zurückgelesen. Alte Profile, Rückmeldungen, Artikel-IDs und Belegdossiers unverändert. Keine numerischen Gewichte in den neuen Beschreibungstext übernommen.

Bestehende Automation `6ae148b170108191a9414da73668e09a` heißt jetzt **Persönlicher Pressespiegel** und ist aktiv. Zeitplan unverändert täglich 06:45 Europe/Vienna; Ziel Veröffentlichung bis 07:45. Neuer Auftrag vollständig gespeichert und zurückgelesen: Originalrückmeldungen auf GitHub lesen → Beschreibung bei Bedarf verbessern und speichern → gespeicherte Beschreibung frisch lesen → recherchieren/auswählen → per PR/CI auf der Website veröffentlichen. Kein manuelles Starten, Kopieren von Prompts oder tägliches Freigeben nötig. Explizite Nutzerbestätigung dieses Kreislaufs und des Concierge-Betriebs liegt vor. Alte separate V3-Störungswache `6ae0b7da23cc81919d2ecd1546bdc081` pausiert und zurückgelesen; keine neue oder parallele Automation erstellt.

Frühere Angaben „ausstehend/Entwurf“ oben dokumentieren den Vorbereitungsstand. Offen bleibt der erste echte autonome Morgenlauf und die tatsächliche Wirkung späterer Rückmeldungen. Startausgabe enthält sichtbar gekennzeichnete übernommene Artikel; keine neue Recherche behauptet. Dieser Abschluss ist reine Protokollpflege; sein Merge-/Checkstatus steht im zugehörigen PR. Rücknahme nur eigener Änderungen, unabhängige spätere Commits erhalten.
