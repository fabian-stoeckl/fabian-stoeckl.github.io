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
- Das letzte echte Recherchefenster aus bestätigtem `preview:false`-Lauf mit privatem Dossier bestimmen; importierte Vorschauen sind kein Ausgangsdatum. Zeitpunkt des Ereignisses, Veröffentlichungs- und Änderungsdatum auseinanderhalten.
- Pro Aussage tatsächlich sichtbares Originalmaterial, Quellenrolle und Ungewissheit privat dokumentieren. Bei Paywalls strikte Trennung zwischen dem ausgewählten, nur teilweise lesbaren Original und Kontext aus anderen Quellen. Optional `related_article` für klar gesonderte weiterführende Lektüre.
- Ganze Ausgabe nach Nachrichtenwert, österreichischen Themen, Genre-/Perspektivenvielfalt, Mehrwert und echtem Zuckerl durchdenken; keine Quoten, Score-Engine oder individuellen Artikel-Linktests.
- Bestehende eine Morgenautomation früher starten, aber Ziel 07:45 Europe/Vienna behalten. ETF und andere Leseroberflächen bleiben unangetastet.

## Offen
- Erste tatsächlich neu recherchierte Ausgabe nach privatem Belegdossier, Quellenprüfung, erfolgreichem Pull Request und überprüfter Veröffentlichung.
- Späteren realen Lernerfolg an Artikelfeedback beurteilen, nicht an einer Änderung des Beschreibungstextes oder grüner CI.
