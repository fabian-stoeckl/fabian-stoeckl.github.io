<!-- website-area: {"name": "Morgenzeitung neu", "paths": ["Privat/Pressespiegel-neu/"]} -->
# Bereichsprotokoll: Morgenzeitung neu

**Stand:** 28.10.2026. **Status:** Erstimplementierung. **Auftrag:** eigenständige parallele Morgenzeitung mit identischer Oberfläche, redaktionell schlankem Backend und eigenständigem Lernen.

- Kachel in `Privat/index.html` zeigt auf `/Privat/Pressespiegel-neu/`.
- Oberfläche verwendet unverändert CSS/Darstellungs-JavaScript der bisherigen Morgenzeitung; `index.html` und `praeferenzen.html` sind gestalterisch gleich.
- Eigene Ausgabe-JSONs unter `Privat/Pressespiegel-neu/data/`.
- Eigenes Feedback im bestehenden privaten Repository durch Ausgabe-Issues mit Präfix `[Morgenzeitung neu]`; keine Vermischung mit der bisherigen Zeitung. Gleicher eingeschränkter Browser-GitHub-Token nutzbar, eigenes Quittungs-Storage.
- Eigenes privates `morgenzeitung-neu/profile.json` als Lernspeicher. Ursprüngliches `profile.json` nur einmalig als Startwissen gelesen.
- Redaktionelle Minimalarchitektur und Tagesablauf in `services/morgenzeitung-neu/REDAKTION.md`. Prüfung: JSON-Schema, belegte redaktionelle Fakten, Lerngegenprobe statt Artikel-Linktests. Geplante ChatGPT-Ausführung mit Ziel 07:45 Wien.
- Pilot 27.10.2026 ausdrücklich aus alter Ausgabe übernommen und als Vorschau markiert, keine unabhängige Recherche behauptet.
- ETF und bisherige Zeitung unangetastet.

## Offen / Betriebsnachweise

- Erster **eigenständig recherchierter** Tageslauf am 28.10.2026 mit getrenntem Profil, echter Auswahl und erfolgreicher HTTPS-Veröffentlichung; Vergleichsvorschau ist hierfür kein Beleg.
- Nach tatsächlich abgegebenem neuen Feedback nachfolgende Ausgabe auf dokumentierte Auswahländerungen kontrollieren, statt Lernen vorab zu behaupten.
- Ein Browser-End-to-End-Test mit neuem Feedback-Issue ohne Veröffentlichung privater Inhalte ist nach Inbetriebnahme zu prüfen; bisher nur reine Format-/Integrationsprüfungen.

**Rücknahme:** Nur neue `Privat/Pressespiegel-neu/`-Dateien, neue Kachel, neue Skripte/Workflows/Protokoll entfernen. Bisherige Website-Dateien und alter Pressespiegel bleiben erhalten.
