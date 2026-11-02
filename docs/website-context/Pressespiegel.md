<!-- website-area: {"name": "Pressespiegel", "paths": ["Privat/Pressespiegel/"]} -->
# Bereichsprotokoll: Pressespiegel

**Stand:** 29.10.2026

Eigenständige neue Zeitung: `Privat/Pressespiegel/`. Die vertraute klassische V3-Oberfläche wird bewusst als Grundlage kopiert: Papierfarben, Typografie, die Tabs „Heute wichtig“/„Vertiefungen“, Bewertungen und Schnellgründe, stets offenes Freitextfeedback mit Formulierungsvorschlägen, eigene Präferenzseite.

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

## Ergänzung 02.11.2026 – Rubrik Blogs
- Dritter Reiter **Blogs** ohne Bewertungssystem. Zeigt Blogname und jeweils fünf letzte direkte Beitragslinks mit Datum und kurzer Beschreibung. Bestehende Tagesausgaben, Nachrichten, Vertiefungen und privates Feedback unberührt.
- Erster Blog **Noah Smith · Noahpinion**, `https://www.noahpinion.blog/feed`; Gastbeiträge anderer Autoren ausdrücklich mitzählen; Autor je Beitrag nennen, soweit im Feed angegeben. Entscheidend sind die fünf neuesten Posts des gesamten Blogs, nicht nur Noah Smiths eigene Texte.
- Unabhängige GitHub-Actions-Aktualisierung alle drei Stunden: `scripts/sync_blogs.py` prüft den RSS-Feed und schreibt nur auf den separaten Datenbranch `blogs-live`; keine direkten automatischen Änderungen an `main`, keine weitere ChatGPT-Automation. Reader lädt aktuelle Daten von GitHub Raw und fällt bei Fehlern auf die im Hauptbranch gespeicherte Startliste zurück. Feedtext nicht als redaktionell geprüfte Synthese behandeln.

## Korrektur 02.11.2026 – Gastbeiträge zählen mit
- Nutzer hinterfragte die ohne Auftrag vorgenommene Eingrenzung auf persönlich von Noah Smith verfasste Beiträge. Für **Noahpinion** gelten fortan die letzten fünf Artikel des ganzen Blogs inklusive Gastbeiträgen. Das Feed-Skript filtert nicht nach Autor; Autorzeile im Reader bei vorhandenen RSS-Angaben.

## Ergänzung 02.11.2026 – Ältere Blogbeiträge aufklappen
- Die fünf neuesten Blogbeiträge sind zuerst sichtbar. „Weitere 10 Beiträge anzeigen“ erweitert die **gleiche** Liste pro Klick um zehn (letzter Schritt ggf. weniger); nach Ende der gespeicherten Liste verschwindet der Button. Erweiterten Zustand beim Rubrikwechsel erhalten; **keine Bewertungen**.
- Die bestehende RSS-Automation speichert künftig alle derzeit im RSS angebotenen Beiträge und führt sie mit den bereits gespeicherten älteren Feed-Beiträgen zusammen. Dadurch gehen Beiträge beim Herausfallen aus dem RSS-Zeitfenster nicht wieder verloren. Keine Behauptung, das vollständige historische Blogarchiv vor dem ersten Feedabruf rückwirkend zu besitzen. Die Startliste im Hauptbranch bleibt Notfall-Fallback, nicht ein vorgeblich vollständiges Archiv.

## 02.11.2026 – Öffentlicher Name und neue Adresse
- Die **aktuelle** Zeitung heißt jetzt **Pressespiegel**, auch Kachel, URL, Masthead, Präferenzseite, Links, 404-Seite und RSS-Liste. Ziel `Privat/Pressespiegel/`. Der vorangegangene Stand dieser aktuellen Zeitung unter `Privat/Morgenzeitung-Neu/` bleibt als weiterleitende Adresse erhalten.
- Die früher eigenständige historische Pressespiegel-Variante wurde als `Privat/Pressespiegel-Archiv/` mit Code, Ausgabe und Styles gesichert.
- Das bestehende private Feedback-Repository verwendet weiterhin `morgenzeitung-neu/` und den Marker `MORGENZEITUNG_NEU_FEEDBACK_V1`, damit bestehende Ratings/Präferenzen erhalten bleiben. Neue Feedbacktitel heißen `[Pressespiegel] Feedback`, ältere Titel werden weiter gelesen. Testnamen und redaktionelle Dateipfade bleiben aus technischen Kontinuitätsgründen erhalten.
- Der tägliche Lauf verwendet nur noch die neue öffentliche Adresse; keine zweite Automation. Der RSS-Datenbranch schreibt ebenfalls auf das neue Ziel.

## Bereinigung 02.11.2026 – Ein einziger Pressespiegel, kein Redirect
- Die bisherigen öffentlichen Vorgänger-Verzeichnisse `Privat/Morgenzeitung-Neu/`, `Privat/Persoenliche-Zeitung/`, `Privat/Pressespiegel-Archiv/` sind **entfernt**, da laut Nutzer keine extern verschickten Links weitergeleitet werden müssen. `/Privat/Pressespiegel/` ist die **einzige** Zeitungsadresse.
- Eigenständige historische Datensätze vom 27./28. Oktober unverändert als Original-JSON in `Privat/Pressespiegel/data/historisch/` übernommen, mit Manifest `index.json`; keine vorhandenen Tagesausgaben/IDs geändert oder überschrieben. Gleiche Datumswerte bleiben als **getrennte** Datenquellen erhalten. Nicht mit `data/index.json` mischen oder als echte neu recherchierte Presseausgaben zählen.
- Doppelte Dateikopien und ungenutzte alte Benutzeroberflächen, Regeln und alte CI-Tests entfernt. Die bestehende **aktive** Engine `services/morgenzeitung-neu/` und **private** `morgenzeitung-neu/` Feedbackdaten, Marker und Ratings bleiben absichtlich unverändert; nicht mit alten V3-Bewertungen vermischen. Historischer Quellcode über die Git-Historie auffindbar.
- Im Blogs-Reiter entfällt der beschreibende Text „Wirtschaft, Technologie und Gesellschaft · aktuelle und ältere Beiträge, auch Gastbeiträge.“; Überschrift und einzelne Links bleiben.

## Entscheidung 02.11.2026 – Unbenutzte Archivdateien entfernen
- Auf ausdrücklichen Wunsch wurden die acht Dateien unter `Privat/Pressespiegel/data/historisch/` (vier alte Ausgaben und die damaligen Quellen-/Verzeichnismetadaten) wieder aus der veröffentlichten Website entfernt. Es erfolgt **keine** Verschmelzung dieser alten Daten mit dem aktuellen Ausgabenindex. Der frühere Dateistand bleibt im Git-Verlauf des Repositorys rekonstruierbar (vor dem Entfernen: Commit `b18011ea61b8c2f2f30e9265e3c1c491f2b0919d`).
- Die sechs gültig indexierten aktuellen Ausgabedateien einschließlich der ausdrücklich als `preview:true` markierten Startausgabe vom 28.10.2026 sowie die laufende RSS-/Feedbacktechnik bleiben unverändert. Es gibt nur eine aktive Zeitung: `Privat/Pressespiegel/`.

