<!-- website-area: {"name": "Morgenzeitung Neu", "paths": ["Privat/Morgenzeitung-Neu/"]} -->
# Bereichsprotokoll: Morgenzeitung Neu

**Stand:** 29.10.2026

Eigenständige neue Zeitung: `Privat/Morgenzeitung-Neu/`. Die vertraute klassische V3-Oberfläche wird bewusst als Grundlage kopiert: Papierfarben, Typografie, die Tabs „Heute wichtig“/„Vertiefungen“, Bewertungen und Schnellgründe, stets offenes Freitextfeedback mit Formulierungsvorschlägen, eigene Präferenzseite.

## Entscheidungen
- Die neue Engine besteht aus einem qualitätsorientierten, im privaten Repository wachsenden Interessenbeschreibungstext und anschließender langer, journalistisch eigenständiger Recherche. Der Text ist das zentrale Gedächtnis, keine numerischen Gewichte.
- Aus nicht begründeten positiven und negativen Klicks vorsichtige, reversible Musterhypothesen bilden, gegen positive Gegenbeispiele halten und in späteren Ausgaben prüfen; Einzelablehnung nicht als ganze Themenablehnung deuten.
- Identität, Originaltitel, Datum, Zeitbezug und jede Tatsachenaussage aus tatsächlich gesichtetem Titel/Vorspann/Text belegen. Redaktionsbelege privat, keine erdachten Inhalte. Nachrichtenwert und individuelle Passung trennen.
- Keine technischen Artikel-Linktests, Paywall-Abwertung, Markenboni, künstliche Platzquoten, erneuten Doppeleintrag historischer Ratings oder Scheinsicherheit.
- Neuer privater Ordner `morgenzeitung-neu/`, neuer Issue-Marker, bereits vorhandene alte Versionsarchive bleiben erhalten. Die alte Ausgabe 28.10. wird nur als `preview:true` übernommen; sie wurde nicht mit der neuen Engine recherchiert.
- Vertraute Kachel „Website ändern“ und ETF vollständig erhalten. Nur die Zeitungskachel führt zur neuen Seite.

## Ergänzungen 29.10.2026 – journalistisches Qualitätsaudit
- Mehrfachberichte nicht nach Wortähnlichkeit löschen, sondern bei gemeinsamen Ereignissen mit `event_key` gruppieren und einen anderen Erkenntnisbeitrag ggf. durch `distinct_contribution` begründen; informierende CLI-Meldungen statt harter Inhaltsblockade.
- **Heute wichtig:** Neuigkeiten seit der letzten nachweislich erfolgreichen Veröffentlichung einer echten Ausgabe, mit kurzer Überschneidung, Nachholung ausgefallener Tage und abschließendem Nachrichten-Check. Importierte Vorschauen und Tests sind kein Ausgangsdatum. **Vertiefungen:** ausdrücklich keine starre Altersgrenze; auch vor einer Woche oder länger veröffentlichte, bisher übersehene Originalanalysen bei erheblichem Erkenntniswert aufnehmen. Ereignis-, Veröffentlichungs-, Änderungs- und Publikationszeitpunkt auseinanderhalten.
- Pro Aussage tatsächlich sichtbares Originalmaterial, Quellenrolle und Ungewissheit privat dokumentieren. Bei Paywalls strikte Trennung zwischen dem ausgewählten, nur teilweise lesbaren Original und Kontext aus anderen Quellen. Optional `related_article` für klar gesonderte weiterführende Lektüre.
- Ganze Ausgabe nach Nachrichtenwert, österreichischen Themen, Genre-/Perspektivenvielfalt, Mehrwert und echtem Zuckerl durchdenken; keine Quoten, Score-Engine oder individuellen Artikel-Linktests.
- Bestehende eine Morgenautomation früher starten, aber Ziel 07:45 Europe/Vienna behalten. ETF und andere Leseroberflächen bleiben unangetastet.

## Ergänzungen 29.10.2026 – Lernen, redaktioneller Gedächtnisstand und Codepflege
- Allgemeine vorgefertigte Textantworten in beiden Feedbackfeldern werden als `comment_suggestions` getrennt von unabhängig getipptem Text im bestehenden privaten Feedback-Issue gekennzeichnet. Keine retroaktive falsche Kennzeichnung alter Antworten, Herkunft beim Ändern/Ausgabenwechsel/Anhängen erhalten.
- „Heute wichtig“-Urteile nicht als Urteil über objektiven Nachrichtenwert deuten; persönliche Passung vor allem in „Vertiefungen“ lernen. Unerwünschte Filterblasen und Selbstbestätigung durch vorgeschlagene Formulierungen vermeiden.
- Pro echter Ausgabe privat wenige belegte Kernaussagen unter `## Tatsächlich vermittelt` dokumentieren und mit Folgetagen vergleichen; keine weitere Datei/Datenbank oder automatische Semantik-Löschroutine. Erste echte Ausgabe journalistisch abnehmen, nicht nur technische CI.
- Doppelte Regressionserwartungen vereinfachen, Berechtigungen und Verhalten alter Ausgaben erhalten; ETF/alte Zeitungen nicht ändern.

## Ergänzungen 29.10.2026 – Vereinfachung, Praxisabnahme und Korrekturen
- Ausführliche Dopplungen über drei Prompts beseitigt: `INTERESSEN.md` ist allein für das Lernen und `RECHERCHE.md` allein für Auswahl, Belege, Korrekturen und Veröffentlichung zuständig. `README.md` erklärt kurz die Schnittstellen; die einzige tägliche Automation orchestriert und verweist auf die aktuelle Hauptbranch-Version.
- Statt bloß erster echter Ausgabe: **erste drei** tatsächlich veröffentlichte `preview:false`-Ausgaben anhand überprüfbarer Beispiele journalistisch abnehmen (übersehene wesentliche Meldungen und bessere Alternativen, Quellenvielfalt, Erkenntniswert, Paywall-Neutralität, Belegtreue, Dopplungen), dritte Ausgabe mit kurzer Musterbilanz. Kein synthetisches Nutzerfeedback, keine weitere Automation oder Score-Tabelle.
- Korrigierte falsche Artikelzusammenfassungen erhalten öffentlich `correction` (`corrected_at`, `previous_summary`, `note`, `source_url`) und eine sichtbare Berichtigung beim **gleichen Artikel**. Ursprüngliche Artikel-ID, URL, Rubrik, Datum und bestehende private Bewertungen bleiben erhalten. Im privaten Tagesdossier Falschaussagen ausdrücklich berichtigen; bei Feedback vor der Korrektur den damaligen sichtbaren Stand berücksichtigen bzw. Unsicherheit markieren.
- Schema-/Browser-/Regressionstests für Berichtigungen; keine Änderungen am ETF oder am alten Zeitungsarchiv.

## Ergänzung 29.10.2026 – Schlankes Monitoring des Lernerfolgs
- Unter `Meine Präferenzen` eigener Bereich „Wie gut lernt meine Morgenzeitung?“ mit privatem, über das bestehende GitHub-Contents-Recht gelesenem Klartext aus `morgenzeitung-neu/lernmonitoring.md`. Keine eigenen Ratings, Analytics-Tracker oder öffentliche Profile.
- `INTERESSEN.md` ist alleinige fachliche Quelle für die qualitative Lernprüfung: erste Ausgangsbilanz nach drei echten Veröffentlichungen; danach ungefähr alle 14 Tage und nach etwa zwei Monaten eine längere Rückschau im schon bestehenden Tageslauf. Klare Trennung von redaktioneller Drei-Ausgaben-Abnahme.
- Zu jeder Behauptung über Lernen gehören ursprünglich beobachtetes echtes Feedback, mögliche alternative Erklärung, konkrete Auswahländerung, spätere unabhängige echte Artikelreaktion samt Gegenbeispielen. Unbewertet neutral; Vorlagenklicks/alte Issue-Versionen nicht als zusätzlichen Beweis zählen. Ohne genügend Reaktionen „noch nicht beurteilbar“ statt erfundener positiver Trend.
- Private Initialdatei beginnt ohne erfundene Hypothesen oder Erfolge; klares UI für fehlenden GitHub-Zugang und 404-Fallback. Keine neue Automation, unveränderte ETF- und V3-Teile.

## Offen
- Erste drei tatsächlich neu recherchierte und veröffentlichte Ausgaben, mit dokumentierter journalistischer Praxisabnahme und Musterbilanz nach der dritten.
- Späteren realen Lernerfolg an Artikelfeedback beurteilen, nicht an einer Änderung des Beschreibungstextes oder grüner CI.
