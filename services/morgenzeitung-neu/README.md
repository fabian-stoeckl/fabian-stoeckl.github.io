# Pressespiegel – Architektur und Betrieb

Der einzige aktive Pressespiegel unter `Privat/Pressespiegel/` übernimmt bewusst das **klassische** Design mit „Heute wichtig“, „Vertiefungen“, drei Relevanzstufen, optionalen Begründungen, freiem Feedback und separater Präferenzseite. Unbenutzte historische Einzelausgaben sind aus dem aktuellen Website-Baum entfernt; die Git-Historie bewahrt frühere Entwicklungsstände. Andere Website-Bereiche, besonders ETFs, bleiben unberührt.

## Eine Quelle pro Verantwortung

1. **`INTERESSEN.md` – lernende Redaktion:** Neue/geänderte echte private Feedback-Issues im Artikelkontext lesen und das natürlichsprachliche `morgenzeitung-neu/interessen.md` nur bei belegbarem Erkenntnisgewinn vorsichtig verändern. Vorlagenprovenienz beachten (`suggested_reasons` und `comment_suggestions`); „Heute wichtig“ bleibt nach allgemeinem Nachrichtenwert kuratiert. Private Änderungen, Versionen und Gründe in `aenderungen.md` und `state.json` sichern und nach PR-Merge zurücklesen.
2. **`RECHERCHE.md` – journalistische Redaktion:** Bestätigtes privates Profil neu lesen, umfassend recherchieren, unabhängig wichtige Nachrichten und persönlich lohnende Vertiefungen auswählen, belegtreu formulieren, redaktionell gegen Dopplungen und übersehene wesentliche Geschichten prüfen. Nachrichten seit letzter bestätigter Veröffentlichung; ältere, bislang übersehene gute Vertiefungen ohne Altersgrenze. Kein Ranking-Score, Verlagsbonus oder Paywall-Zugangsbonus.
3. **Privates Tagesdossier:** `fabian-stoeckl/morgenzeitung-feedback/morgenzeitung-neu/recherche/YYYY-MM-DD.md` hält echte Originalbelege und `## Tatsächlich vermittelt` als dokumentierten **Zeitungsinhalt**, nie als behauptete Leserlektüre. Für die **ersten drei echten publizierten Ausgaben** jeweils eine kurze journalistische Qualitätsabnahme; nach der dritten eine zusammenfassende, belegte Musterprüfung. Nicht die importierte Vorschau mitzählen.
4. **Öffentliche Ausgabe:** `Privat/Pressespiegel/data/YYYY-MM-DD.json` und Index, V3-kompatibel, für echte Ausgaben `preview:false`. Die importierte Vorschau vom 28.10.2026 ist auf Nutzerwunsch gelöscht; sie war keine echte Recherche. Die ersten im Index enthaltenen Ausgaben sind vom 29.10.2026. Private Profile/Kommentare gehören **nicht** in öffentliches JSON.

## Qualitative Lernbilanz – ohne zusätzliche Automation

`INTERESSEN.md` pflegt im bestehenden Morgenlauf die private `morgenzeitung-neu/lernmonitoring.md`; `Meine Präferenzen` zeigt sie nach authentifiziertem Contents-Read an. Ausgangsbilanz nach drei echten Veröffentlichungen; danach etwa zweiwöchig prüfen, nach etwa zwei Monaten längerfristig rückblicken. Nur echter nachfolgender Feedback-Kontext kann einen Lerneffekt belegen; bei wenig Rückmeldungen ausdrücklich **noch nicht beurteilbar**. Redaktionelle Qualität und persönliche Lernwirkung sind getrennt. Keine numerische Erfolgspunktzahl oder zusätzliche Aufgabe.

## Integrität und nachträgliche Berichtigungen

`scripts/morgenzeitung_neu.py verify` testet ausschließlich Datenstruktur, URL-/ID-Eindeutigkeit und strukturierte Korrekturen – **keine** journalistische Wahrheit. `event_key` gruppiert optionale Nachrichtenanlässe; mehrere unterschiedliche Originalartikel dürfen bleiben, wenn `distinct_contribution` echten Zusatzwert begründet (nur redaktionelle Hinweise, keine automatische Löschung). `related_article` bezeichnet ausdrücklich einen separaten Originalbeitrag, keinen erfundenen Zugang zum ungelesenen Paywall-Text.

Bei einem echten **nachträglich erkannten Fehler** den betreffenden Artikel im selben Ausgabe-JSON berichtigen und `correction` mit `corrected_at`, `previous_summary`, `note`, `source_url` versehen. Im Reader erscheint der Hinweis direkt beim Artikel und der frühere Wortlaut bleibt nachvollziehbar. **Artikel-ID, Original-URL, Rubrik und Ratings erhalten**, keine künstliche neue Stimme erzeugen; im privaten Dossier die Tatsache berichtigen und ältere Bewertungen ggf. als Bewertungen der früheren Darstellung interpretieren. Allgemeiner `correction_note` bleibt für editionsübergreifende Hinweise unterstützt. Keine rückwirkende stille Faktenänderung.

## Veröffentlichungsweg

Der **eine bereits existierende** tägliche Automationsauftrag lädt den aktuellen Hauptbranch und führt `INTERESSEN.md` gefolgt von `RECHERCHE.md` aus. Er beginnt um 04:45 Uhr Europe/Vienna mit Ziel-Veröffentlichung 07:45 Uhr. Private Belege vor öffentlichem PR sichern; passende Struktur-, Unit- und Browser-Tests/CI prüfen, mergen, Pages-Deployment kontrollieren und nach Möglichkeit öffentliche HTTPS-Ausgabe zurücklesen. Scheitert ein Schritt, letzte gültige Ausgabe behalten und Hindernis ehrlich melden. Keine zweite parallele Produktion, Link-Test-Wache oder automatisch erfundene Erfolgsanalyse.

## Fehlertoleranz und Wiederaufnahme (verbindlich seit 06.11.2026)

Ein einzelner fehlgeschlagener Quellenabruf (403/404, Paywall, Timeout, Parser-/Netzfehler) ist **kein** Grund, die gesamte Recherche oder Produktion abzubrechen. Erst den konkreten Abruf mit einer begrenzten Anzahl neuer Versuche (in der Regel bis zu drei, kurze Abstände), kanonischem Verlagslink, Verlagssuche/RSS, und bei Bedarf neuen Suchanfragen prüfen. Keine endlose Wiederholung derselben Fehlermeldung. Fehlende Zugänglichkeit nicht mit einem widerlegten Sachverhalt verwechseln.

Lässt sich ein Original nach diesen Versuchen nicht ausreichend belegen, nur dessen tatsächlich sichtbare Überschrift bzw. Vorschau mit zutreffendem \`evidence_level\` verwenden oder den **einzelnen** Kandidaten durch einen eigenständig belegten anderen Beitrag ersetzen; ungesicherte Inhalte streichen. Unabhängige Sekundärquellen dürfen Fakten zum Anlass bestätigen, jedoch niemals ungelesenen Originaltext vortäuschen. Den **übrigen** Nachrichten-/Vertiefungsprozess aktiv fortsetzen, auch wenn einzelne Artikel entfallen. Richtzahlen sind keine Füllpflicht.

Bei technischen GitHub-/Netzwerk-/CI-/HTTPS-Problemen ebenfalls erst begrenzt erneut versuchen, Stand und Rechte überprüfen, alternative zulässige Abrufwege und GitHub-Actions-Details auswerten und danach bei weiterhin **tatsächlich blockierter** Datensicherung/Publikation den letzten gültigen Stand unverändert belassen. Fehlgeschlagene Sicherheits-/Strukturtests niemals umgehen oder Tests als bestanden melden. Bei erneuten Versuchen bereits gesicherte echte Belege, Feedbackstände und Artikel-IDs erhalten; keine doppelten Updates, keine Scheinveröffentlichung. Am Ende offen zwischen echtem Blocker, nur teilweise zugänglichen Quellen, bestandenem CI und separat bestätigtem HTTPS-Readback unterscheiden.

## Prüfen

`python3 scripts/morgenzeitung_neu.py verify`, `python3 tests/morgenzeitung-neu-editorial.py`, `node tests/morgenzeitung-neu.test.cjs`, `node tests/morgenzeitung-neu-feedback.cjs` sowie die vorhandenen GitHub-Browser- und allgemeinen Website-Prüfungen. Diese Tests bestätigen Struktur und Abläufe, **nicht** die Qualität der journalistischen Auswahl.
## Öffentliche Umbenennung 02.11.2026
Die Zeitung heißt öffentlich **Pressespiegel** und liegt auf `Privat/Pressespiegel/`. Die alten Verzeichnisse und Weiterleitungen sind entfernt. Unbenutzte historische Einzelausgaben aus früheren Zeitungsvarianten wurden nach Nutzerentscheidung entfernt; sie lassen sich bei Bedarf aus dem Git-Verlauf wiederherstellen. Die private Feedback- und Profilspeicherung bleibt unberührt. Private GitHub-Ordner `morgenzeitung-neu/`, Marker und Artikel-IDs bleiben stabil, damit frühere Bewertungen nicht verloren gehen.
