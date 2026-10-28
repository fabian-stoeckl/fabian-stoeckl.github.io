# Morgenzeitung Neu – neues Produkt, vertraute Oberfläche

Der Neubau liegt **eigenständig** unter `Privat/Morgenzeitung-Neu/`. Er kopiert bewusst die vertraute klassische Zeitung (Design, zwei Tabs, Artikel, drei Ratings, Schnellgründe, offenes Feedback, eigene Präferenzseite), nicht die neue Pressespiegel-Oberfläche. Ältere Projekte bleiben lesbar und unverändert; ETF-Dateien bleiben unberührt.

## Der zentrale Lernkreislauf

1. `INTERESSEN.md` zuerst: Alle echten neuen/geänderten Rückmeldungen lesen, im Kontext der tatsächlich bewerteten Artikel interpretieren und die **fortlaufende natürlichsprachige Interessenbeschreibung** verbessern, soweit die Erkenntnisse dies rechtfertigen. Auch Muster aus unbegründeten positiven oder negativen Bewertungen prüfen, mit mehreren möglichen Erklärungen und Unsicherheit; nicht aus einer Ablehnung ein ganzes Thema streichen. Das Profil darf gleich bleiben, wenn kein sinnvolles neues Signal da ist. Jede Änderung wird kurz mit Begründung privat protokolliert. Das Profil ist das langfristige Lernen, keine Rating-Summe.
2. `RECHERCHE.md` danach: Den **tatsächlich gespeicherten** Text frisch lesen, lange und gründlich suchen und journalistisch auswählen. Kein Score oder Verlagsbonus; Quellenbelege und verantwortungsvolle Zusammenfassungen. Beide Rubriken bleiben „Heute wichtig“ und „Vertiefungen“. Der neue Redaktionsauftrag besteht aus genau diesen beiden sequentiellen Prompts.
3. Privates Redaktionsgedächtnis: `fabian-stoeckl/morgenzeitung-feedback: morgenzeitung-neu/` mit `interessen.md`, `aenderungen.md`, `state.json`, `recherche/YYYY-MM-DD.md`. Privates Lernprofil und öffentliches Ausgabe-JSON niemals vermischen.
4. Ausgabe und Index nur nach tatsächlich erfolgter Recherche unter `Privat/Morgenzeitung-Neu/data/` als V3-kompatibles Format, `preview:false`, und nach Quellenprüfung, Codeprüfungen, PR/CI, Merge, Pages und HTTPS-Readback. Die importierte Ausgabe vom 28.10.2026 ist `preview:true` und **keine recherchierte Ausgabe** der neuen Version.

## Feedbacksicherheit und historische Kontinuität

Neue Issues: Präfix `[Morgenzeitung Neu] Feedback YYYY-MM-DD`, Marker `MORGENZEITUNG_NEU_FEEDBACK_V1`, bestehendes V3-kompatibles Ratingschema mit `value`, `reason`, `reason_codes`. Das Frontend benutzt denselben bewährten GitHub-Schreibmechanismus, aber einen **neuen Issue-Namensraum** und neue lokale Receipts. Vorherige V3- und Pressespiegelbewertungen bleiben im Archiv und sind nur Startkontext – nie neue Stimmen. Latest edited state wins. Kein Lernprofil aus synthetischem Feedback.

Die Website zeigt das neue Profil ausschließlich nach authentifizierter privater Abfrage mit Contents: Read; die bisherige GitHub-Verbindung kann genutzt werden, falls sie diese Berechtigung besitzt. Token niemals im öffentlichen Code oder Daten ablegen. Präferenzänderungen sind keine automatische Zusicherung besserer Artikel; spätere echte Bewertungen zeigen, ob die Qualität steigt.

## Prüfungen
`python3 scripts/morgenzeitung_neu.py verify`; `node tests/morgenzeitung-neu.test.cjs`; bestehende Website-/V3-Prüfungen für die unveränderten alten Bereiche. Keine journalistische Wahrheit aus bestandenen Schema-Tests ableiten.

## Betrieb
Beim Wechsel nur **die bestehende** Morgenautomation auf die neue Version umstellen, keine zweite konkurrierende tägliche Recherche anlegen. Vor Livewechsel erfolgreiche Bereitstellung prüfen; bei Fehlern bleibt der bisherige Tagesstand unverändert.
