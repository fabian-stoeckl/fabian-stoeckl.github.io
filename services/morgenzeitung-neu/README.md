# Morgenzeitung Neu – neues Produkt, vertraute Oberfläche

Der Neubau liegt **eigenständig** unter `Privat/Morgenzeitung-Neu/`. Er kopiert bewusst die vertraute klassische Zeitung (Design, zwei Tabs, Artikel, drei Ratings, Schnellgründe, offenes Feedback, eigene Präferenzseite), nicht die neue Pressespiegel-Oberfläche. Ältere Projekte bleiben lesbar und unverändert; ETF-Dateien bleiben unberührt.

## Der zentrale Lernkreislauf

1. `INTERESSEN.md` zuerst: Alle echten neuen/geänderten Rückmeldungen lesen, im Kontext der tatsächlich bewerteten Artikel interpretieren und die **fortlaufende natürlichsprachige Interessenbeschreibung** verbessern, soweit die Erkenntnisse dies rechtfertigen. Auch Muster aus unbegründeten positiven oder negativen Bewertungen prüfen, mit mehreren möglichen Erklärungen und Unsicherheit; nicht aus einer Ablehnung ein ganzes Thema streichen. Das Profil darf gleich bleiben, wenn kein sinnvolles neues Signal da ist. Jede Änderung wird kurz mit Begründung privat protokolliert. Das Profil ist das langfristige Lernen, keine Rating-Summe.
2. `RECHERCHE.md` danach: Den **tatsächlich gespeicherten** Text frisch lesen, lange und gründlich suchen und journalistisch auswählen. Kein Score oder Verlagsbonus; Quellenbelege und verantwortungsvolle Zusammenfassungen. Beide Rubriken bleiben „Heute wichtig“ und „Vertiefungen“. Der neue Redaktionsauftrag besteht aus genau diesen beiden sequentiellen Prompts.
3. Privates Redaktionsgedächtnis: `fabian-stoeckl/morgenzeitung-feedback: morgenzeitung-neu/` mit `interessen.md`, `aenderungen.md`, `state.json`, `recherche/YYYY-MM-DD.md`. Privates Lernprofil und öffentliches Ausgabe-JSON niemals vermischen.
4. Ausgabe und Index nur nach tatsächlich erfolgter Recherche unter `Privat/Morgenzeitung-Neu/data/` als V3-kompatibles Format, `preview:false`, und nach Quellenprüfung, Codeprüfungen, PR/CI, Merge, Pages und HTTPS-Readback. Die importierte Ausgabe vom 28.10.2026 ist `preview:true` und **keine recherchierte Ausgabe** der neuen Version.


## Redaktioneller Qualitätskreislauf (ohne zusätzliche Score-Engine)

Der Rechercheprompt führt vor der Veröffentlichung eine **inhaltliche Schlussredaktion** durch: unabhängige Beiträge zum selben Nachrichtenanlass vergleichen, nicht aus Agenturabschriften mehrere Bestätigungen ableiten, Zeit- und Rechtsstatus (Ankündigung/Beschluss/Umsetzung) richtig benennen, Informationen exakt dem gesichteten Original zuordnen und die Mischung der Gesamtausgabe auf übersehene Entwicklungen überprüfen. Eine ältere Publikation kann sehr wertvoll sein, wenn sie einen wirklich neuen Erklärwert bietet; Veröffentlichungsdatum, Ereignisdatum und Erkenntnisgewinn sind verschieden.

Das neue optionale `event_key`-Feld gruppiert unterschiedliche Originalartikel zu demselben Ereignis. Das optionale `distinct_contribution` dokumentiert, warum ein weiterer Artikel darüber trotzdem lesenswert ist. Der Python-Test meldet fehlende oder mehrfach vorkommende Schlüssel als **redaktionellen Hinweis**, aber bewertet den Inhalt nicht automatisch, entfernt keine Artikel und erschwert nicht künstlich eine Veröffentlichung. Genaue URL-/ID-Dopplungen bleiben dagegen strukturelle Fehler.

`evidence_level` beschreibt nur das tatsächlich gesichtete Originalmaterial, nicht die vermutete Qualität eines verlinkten Beitrags. Zu jedem öffentlichen Fakt gehört ein zuordnungsfähiger Beleg im **privaten** Tagesdossier; eine zweite Quelle ergänzt Kontext, beweist aber keinen ungelesenen Paywall-Volltext. Optional können geprüfte andere Originalbeiträge unter `related_article` als gesonderte Lektüre erscheinen. Keine unbestätigten Paywall-Bypass-Links und keine Linktest-Hürden.

Eine gute ungewöhnliche Vertiefung kann als `treat:true` das vertraute **Zuckerl** sein; keine Pflicht, keine Füllmeldung. Vorherige `preview:true`-Ausgaben sind historisch und gelten nie als erfolgreicher Forschungs- oder Publikationslauf. Für **Heute wichtig** beginnt das Neuigkeitenfenster bei der letzten **nachweislich erfolgreichen Veröffentlichung** einer echten Ausgabe; mit kurzer Überlappung, Nachholung ausgefallener Tage und abschließendem Aktualitätsdurchgang. Für **Vertiefungen** gibt es keine Altersgrenze: bisher übersehene, auch eine Woche oder länger alte hochwertige Analysen können aufgenommen werden, wenn ihr heutiger Erkenntniswert überzeugt. Das echte Veröffentlichungsdatum des Originalartikels wird nicht als aktuelle Nachricht ausgegeben. Die Personalisierung bleibt vorsichtig und bewertet nicht automatisch, ob die Nutzerin oder der Nutzer veröffentlichte Beiträge gelesen hat.

**Betriebsziel:** ein bestehender einzelner täglicher Lauf mit ausreichend Vorlauf bis 07:45 Europe/Vienna, nicht mehrere Zeitungen oder separate Dauertests. Die redaktionelle Wahrheit wird nicht durch bestandene Schema- oder CI-Tests behauptet.

## Feedbacksicherheit und historische Kontinuität

Neue Issues: Präfix `[Morgenzeitung Neu] Feedback YYYY-MM-DD`, Marker `MORGENZEITUNG_NEU_FEEDBACK_V1`, bestehendes V3-kompatibles Ratingschema mit `value`, `reason`, `reason_codes`. Das Frontend benutzt denselben bewährten GitHub-Schreibmechanismus, aber einen **neuen Issue-Namensraum** und neue lokale Receipts. Vorherige V3- und Pressespiegelbewertungen bleiben im Archiv und sind nur Startkontext – nie neue Stimmen. Latest edited state wins. Kein Lernprofil aus synthetischem Feedback.

Die Website zeigt das neue Profil ausschließlich nach authentifizierter privater Abfrage mit Contents: Read; die bisherige GitHub-Verbindung kann genutzt werden, falls sie diese Berechtigung besitzt. Token niemals im öffentlichen Code oder Daten ablegen. Präferenzänderungen sind keine automatische Zusicherung besserer Artikel; spätere echte Bewertungen zeigen, ob die Qualität steigt.

## Prüfungen
`python3 scripts/morgenzeitung_neu.py verify`; `node tests/morgenzeitung-neu.test.cjs`; bestehende Website-/V3-Prüfungen für die unveränderten alten Bereiche. Keine journalistische Wahrheit aus bestandenen Schema-Tests ableiten.

## Betrieb
Beim Wechsel nur **die bestehende** Morgenautomation auf die neue Version umstellen, keine zweite konkurrierende tägliche Recherche anlegen. Vor Livewechsel erfolgreiche Bereitstellung prüfen; bei Fehlern bleibt der bisherige Tagesstand unverändert.
