<!-- website-area: {"name":"Pressespiegel","paths":["Privat/Pressespiegel/"]} -->
# Bereichsprotokoll: Pressespiegel

**Stand:** 28.10.2026. **Status:** Neubau, getesteter Entwurf; Veröffentlichung und automatische Umstellung ausstehend.

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
