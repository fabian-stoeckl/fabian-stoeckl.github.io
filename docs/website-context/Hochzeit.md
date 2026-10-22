<!-- website-area: {"name": "Hochzeit", "paths": ["Hochzeit/", "hochzeit/"]} -->
# Bereichsprotokoll: Hochzeit

**Stand:** 22.10.2026. **Status:** Hochzeitswebsite veröffentlicht; Vereinfachung und Originalmotiv in Überarbeitung.

## Geltungsbereich
- `Hochzeit/index.html`: öffentliche Hochzeitsstartseite und Gästerückmeldung
- `Hochzeit/danke.html`: Rückmeldungs-Bestätigung
- `Hochzeit/einladung.svg`: Originalmotiv der Einladung aus der vom Nutzer bereitgestellten PDF, ohne eigene Schriftdateien
- `hochzeit/index.html`: Kleinschreibungs-Weiterleitung zur zentralen Startseite
- Unabhängig von Forschungswebsite, Privat/ETF und Morgenzeitung

## Bestätigte Entscheidungen
- Einheitlicher QR-Code führt zur Startseite `https://www.fabian-stoeckl.com/Hochzeit/`; auch `/hochzeit/` ist erreichbar.
- Hochzeitsdaten laut Einladung: Fabian & Melanie, 14. August 2027, Kavalierhaus Klessheim, Salzburg, Trauung 15 Uhr.
- Die Titelseite nutzt das **Originalmotiv aus der PDF**, einschließlich Namen, Konturschrift und der zwei Ringe. Responsive und mit einem darüber platzierten RSVP-Button.
- Rückmeldung mit Namen, Teilnahme, Namenslisten: Erwachsene / Jugendliche U14 / Kinder U3. Keine vorgegebenen Beispieltexte in den Feldern.
- Rückmeldefrist: 14. Februar 2027, sichtbar im Einleitungstext.
- Essenswahl vollständig entfernt; keine dazugehörigen Hinweise auf der Seite.
- Keine Gastkonten, kein individueller QR-Code. Änderungswünsche: erneute Rückmeldung per Formular; jüngste Mail gilt, keine serverseitige automatische Zusammenführung. Optionales Speichern auf demselben Gerät für bequemes Nachbearbeiten.
- Statische GitHub-Pages-Seite. E-Mail-Versand über FormSubmit.co: Hauptempfänger `fabian-stoeckl@hotmail.com`, Kopie (_cc) an `Melanie.Koch@hotmail.com`. Der Hauptempfänger muss das Formular einmalig aktivieren; eine erfolgreiche Zustellung an beide Adressen muss vor dem realen Einsatz getestet werden.
- Kein Backend und kein GitHub Token für Gäste. Website sollte von Suchmaschinen nicht indexiert werden.
- Hochzeitsgästendaten nicht im öffentlichen GitHub-Repository ablegen.

## Offene Aufgaben vor endgültigem Produktivbetrieb
- PR-Prüfungen und responsives Layout testen, anschließend veröffentlichen und HTTPS prüfen.
- Einmalige FormSubmit-Empfängeraktivierung, echte Testübermittlung und Prüfung des E-Mail-Eingangs durch den Nutzer.
- Änderungen am Gästefragebogen nur nach erneuter Abstimmung; Rückmeldeschluss 14.02.2027 ist bereits sichtbar.
- Optional: geschützter Datenbestand, falls automatische geräteübergreifende Korrekturen statt aktualisierter E-Mails gewünscht werden.

## 22.10.2026: Vereinfachung auf Nutzerwunsch
- Sichtbare QR-Code-Anleitung und FormSubmit-Erklärung entfernt.
- Essenswünsche und zugehörige Hinweise entfernt; ebenso die Vortexte (Placeholder) der Eingabefelder und der Hinweis zu einem Namen pro Zeile.
- Direktes Rendering der Einladungsvorderseite statt CSS-Nachzeichnung.
- Lowercase-URL `/hochzeit/` ergänzt.

## 22.10.2026: Beide Eltern erhalten Rückmeldungen
- Jede neue Rückmeldung soll per E-Mail gleichzeitig an Fabian (Hauptempfänger) und Melanie (CC) gehen. Technisch über FormSubmits offizielles `_cc`-Feld umgesetzt, ohne Änderung der sichtbaren Website.
