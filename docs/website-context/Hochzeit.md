<!-- website-area: {"name": "Hochzeit", "paths": ["Hochzeit/"]} -->
# Bereichsprotokoll: Hochzeit

**Stand:** 22.10.2026. **Status:** Erstentwurf der Hochzeitswebsite auf separatem Feature-Branch.

## Geltungsbereich
- `Hochzeit/index.html`: öffentliche Hochzeitsstartseite und Gästerückmeldung
- `Hochzeit/danke.html`: Rückmeldungs-Bestätigung
- Unabhängig von Forschungswebsite, Privat/ETF und Morgenzeitung

## Bestätigte Entscheidungen
- Einheitlicher QR-Code führt zur Startseite `https://www.fabian-stoeckl.com/Hochzeit/`.
- Hochzeitsdaten laut Einladung: Fabian & Melanie, 14. August 2027, Kavalierhaus Klessheim, Salzburg, Trauung 15 Uhr.
- Gestaltung nimmt die farbige Vorderseite der Einladung auf: Koralle, Mintgrün, Apricot, Gelb, bordeauxrote Konturschrift und ineinanderliegende Ringe.
- Rückmeldung mit Namen, Teilnahme, namensweisen Listen Erwachsene ab 14 Jahren / Jugendliche 3 bis 13 Jahre / Kinder unter 3 Jahren.
- Essenswünsche vorerst als Freitext, bis Menüoptionen abgestimmt sind.
- Keine Gastkonten, kein individueller QR-Code. Änderungswünsche: erneute Rückmeldung per Formular; jüngste Mail gilt, keine serverseitige automatische Zusammenführung. Optionales Speichern auf demselben Gerät für bequemes Nachbearbeiten.
- Statische GitHub-Pages-Seite. E-Mail-Versand über Drittanbieter FormSubmit.co an die bereits bekannte private Empfängeradresse; dieser Dienst benötigt **eine einmalige Empfängerbestätigung**. Nicht als zugestellten Versand ausgeben, bevor Aktivierung und Test erfolgreich sind.
- Kein Backend und kein GitHub Token für Gäste. Website sollte von Suchmaschinen nicht indexiert werden.
- Hochzeitsgästendaten nicht im öffentlichen GitHub-Repository ablegen.

## Aufgaben vor endgültigem Produktivbetrieb
- PR-Prüfungen und responsives Layout testen, anschließend veröffentlichen und HTTPS prüfen.
- Einmalige FormSubmit-Empfängeraktivierung, echte Testübermittlung und Prüfung des E-Mail-Eingangs durch den Nutzer.
- Gegebenenfalls echte Menüwahloptionen ergänzen und Rückmeldeschluss kommunizieren.
- Optional: geschützter Datenbestand, falls automatische geräteübergreifende Korrekturen statt aktualisierter E-Mails gewünscht werden.
