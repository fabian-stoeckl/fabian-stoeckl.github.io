# Prompt 2 – Stelle meinen Pressespiegel zusammen

Suche für mich gute aktuelle Artikel und stelle einen lesbaren Pressespiegel zusammen. Lies dazu als Zusatzinformation die aktuelle Beschreibung aus `pressespiegel/interessen.md` im privaten Repository `fabian-stoeckl/morgenzeitung-feedback`. Nimm sie so ernst wie einen Zusatz, den ich dir gerade in einem normalen Chat zur Artikelsuche gegeben hätte.

Zwei Rubriken:
- **Heute wichtig:** die wichtigsten österreichischen und internationalen Entwicklungen, unabhängig von meinen Spezialinteressen. Ungefähr 15–20 Meldungen, nur so viele wie sinnvoll.
- **Für dich ausgewählt:** ungefähr 10–15 gehaltvolle Originalartikel mit Einordnung und Erkenntnisgewinn. Die Interessenbeschreibung steuert deine Suchfragen. Gelegentlich darf ein guter unerwarteter Beitrag dabei sein.

Recherchiere offen im Web. Beginne mit relevanten Fragen und Ereignissen, nutze dafür passende Qualitätsmedien, Fachquellen und Primärquellen. Deutsch und Englisch, auch Paywall-Artikel, sind willkommen. Die Liste `quellen.json` ist eine Anregung, keine abzuarbeitende Pflichtliste. Suche ausdrücklich auch in Österreich. Vergleiche bei wichtigen Themen unterschiedliche Beiträge: Welcher erklärt mehr, liefert neue Erkenntnisse oder eine gut begründete andere Perspektive? Wähle journalistisch, ohne Rankingformel, Verlagsbonus, feste Quoten oder Punkte für Zugriffsmöglichkeiten.

Lies die letzten veröffentlichten Ausgaben, um bereits vermittelte Inhalte zu erkennen. Wiederholungen brauchen einen tatsächlichen neuen Erkenntnisgewinn. Recherchiere seit der letzten erfolgreichen Ausgabe, nicht nur seit einem starren Tageswechsel. Wähle lieber weniger gute Beiträge als Füllartikel.

Prüfe Originaltitel, Medium, Datum und Original-HTTPS-Link. Gib nur wieder, was die tatsächlich gelesene Überschrift, der Vorspann oder der Originaltext hergeben. Kennzeichne die Grundlage als `headline`, `teaser` oder `read`. Keine erfundenen Volltextdetails. Schreibe bei Vertiefungen eine verständliche Zusammenfassung und, wenn belegbar, einen knappen Satz zum Erkenntnisgewinn. Bei bloßer Überschrift nur einen Lesehinweis. Kennzeichne Meinungen und Empfehlungen als solche und schreibe sie ihrem Urheber zu.

Halte unter `pressespiegel/recherche/YYYY-MM-DD.md` privat die verwendeten Quellen/kurzen Originalbelege und offene Grenzen fest. Keine eigenen Zusammenfassungen als Quellenbeleg. Notiere, welche Version der Interessenbeschreibung du verwendet hast und höchstens drei konkrete Beispiele ihrer Berücksichtigung. Kein zusätzlicher Rechercheplan, kein vollständiger Rankingpool, keine Vorher-Nachher-Score-Simulation.

Veröffentliche ein JSON gemäß `services/pressespiegel/README.md` unter `Privat/Pressespiegel/data/`, aktualisiere den Index und prüfe die Ausgabe mit `python3 scripts/pressespiegel.py verify`. Der einfache Test prüft Struktur und Duplikate, NICHT journalistische Wahrheit; die Quellenprüfung liegt bei dir. Speichere über Branch/PR, warte erfolgreiche CI ab, merge und prüfe den öffentlichen HTTPS-Readback. Bei Fehlern letzte gültige Ausgabe erhalten. Eine bestehende Tagesausgabe nicht unnötig neu erstellen. Berichte kurz das Ergebnis und reale Einschränkungen, ohne einen Lernerfolg zu erfinden.
