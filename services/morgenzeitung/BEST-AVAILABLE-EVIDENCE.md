# Best Available Evidence – verbindliche redaktionelle Betriebsregel (27.10.2026)

## Vorrang und Zweck
Diese Regel ergänzt AGENT-ABLAUF.md, SOURCE-ROSTER.md und PUBLICATION-INCIDENTS.md. Volltextzugang ist **keine** Voraussetzung für Aufnahme oder Relevanzbewertung. Artikelidentität, sichere Original-URL, belegbarer Titel und Publikationsdatum bleiben Voraussetzung für eine Veröffentlichung. Ein nicht lesbarer Volltext darf nie als erfunden, aber auch nie als inhaltlich geprüft markiert werden.

## Zwei unabhängige Dimensionen
- **Identitätsnachweis:** kanonische Original-URL, zugehöriger Titel, Publisher und Publikationsdatum anhand eines offiziellen Feeds, einer Publisher-Metadatenseite oder anderer belastbarer, dem identischen Artikel zuordenbarer Metadaten. Suchindex-Treffer sind Recherchehinweise und müssen hinsichtlich Artikelidentität abgeglichen werden. Ein bloßer HTTP 403/401 ist weder PASS noch FAIL für die Artikelidentität.
- **Inhaltstiefe:** FULL_TEXT, EXCERPT, DESCRIPTION, HEADLINE_ONLY. Diese Stufe wird intern dokumentiert, beeinflusst nicht automatisch den Relevanzscore und begrenzt strikt die zulässige Zusammenfassung. HEADLINE_ONLY: Überschrift wiedergeben, keine erfundenen Hintergründe, Ursachen, Zahlen oder Aussagen. Keine künstlichen zwei bis drei Sätze erzwingen.

## Fehlertolerante Kandidatenbearbeitung
1. Jeden Fixstarter recherchieren und protokollieren; technische Zugriffssperren führen zu alternativen legalen Metadatenwegen, nicht zum Streichen des Verlags.
2. Das Skript `scripts/morgenzeitung_candidate_triage.py` prüft alle Rohkandidaten und trennt `eligible` von `NEEDS_RESEARCH`; ein fehlender Einzelartikel vernichtet nicht den gesamten untersuchten Pool. Im unveränderlichen privaten Rechercheprotokoll bleiben sämtliche abgewiesenen Kandidaten samt Begründung erhalten.
3. Bei NEEDS_RESEARCH begrenzt alternative Publisher-Metadaten/Feeds/Suchindex prüfen; bei weiterhin fehlender Artikelidentität Kandidaten ausschließen und weitere eigenständige Artikel recherchieren. Keine fremden Artikel als identische Spiegelung ausgeben.
4. Vor S4 den **veröffentlichungsfähigen Teilpool** mit dem UNVERÄNDERTEN strengen `morgenzeitung_source_preflight.preflight` erneut unabhängig prüfen. Die frühere Begrenzung von zwei INCONCLUSIVE-Fällen gilt für ungeklärte Identität innerhalb der ausgewählten Publikation, nicht für verworfene Rohkandidaten. Keine falschen PASS-Marker. Die geforderten Artikelzahlen bleiben Ziel; bei nachweislich kleinerem Pool transparent weniger Artikel statt erfundener Füllung.
5. Relevanzbewertung auf derselben frischen Kandidatenbasis mit und ohne aktuelles Lernprofil durchführen. Fehlender Volltext allein darf keine negative Relevanzgewichtung erzeugen; die belegbare Inhaltstiefe ist separat zu dokumentieren.
6. Unveränderliche private S4/S5-Originale, unabhängige Prüfungen, PR/CI, Merge, HTTPS und S7/S8 bleiben Pflicht. Bestehende CI-Checks nicht umgehen oder abschwächen: Wenn ein bisheriger Check die neuen zulässigen Metadatenbelege noch nicht unterstützt, dessen Implementierung mit Positiv-/Negativtests auf separatem PR korrigieren und erst nach grünen Tests produktiv einsetzen.

## Fortsetzung statt vorzeitigem Abbruch
- Fehlender Volltext, Publisher-403, unbrauchbare Einzelkandidaten und unvollständige Vorspänne sind **normale Recherchefälle**, keine globalen Abbruchgründe.
- Nach jeder Recherchecharge und Phase Checkpoint speichern und bei verfügbaren Ausführungsmöglichkeiten unmittelbar fortsetzen. Kein bloßes PARTIAL wegen einzelner unbrauchbarer Artikel.
- Ein tatsächliches Tool-/Zeitlimit oder eine nicht reparierbare technische Gate-Blockade darf weiterhin zu PARTIAL führen; Ursache exakt benennen und den letzten gesicherten Checkpoint für den bestehenden Ersatzlauf bereitstellen. Nicht behaupten, ein ChatGPT-Lauf arbeite nach seinem Ende weiter.
- Niemals Erfolg behaupten ohne echten S4–S8-Nachweis; historische Daten und ETF unverändert lassen.

## Dauerhafter Quellenkontrollkreis

Der täglich um 03:30 UTC getestete GitHub-Runner prüft die elf bekannten offiziellen RSS/Atom-Feedadapter und schreibt den Status für **alle 22 Pflichtmedien** unter `source-health/feeds/YYYY-MM-DD/run-ID.json` privat und unveränderlich mit Remote-Readback. Für elf andere Pflichtmedien bleibt der Feedstatus ausdrücklich `NO_OFFICIAL_FEED_CONFIGURED` – das ist weder eine Aussage gegen deren Erreichbarkeit noch ein Vorwand, sie bei der Redaktion zu überspringen.

Jeder Haupt-/Ersatzlauf muss nach tatsächlicher Recherche ein vollständiges redaktionelles `source-health/editorial/YYYY-MM-DD/run-ID.json` privat sichern. Für jedes der 22 Pflichtmedien gilt: `publisher`, `outcome` (`VERIFIED_ARTICLES`, `NO_SUITABLE_ARTICLES`, `NO_VERIFIABLE_ARTICLES`), `verified_original_count`, `selected_count`, `attempted_methods` (`direct_original`, `official_publisher_feed`, `publisher_metadata`, `independent_index`) und bei erfolglosen Direkt-/Alternativabrufen mindestens zwei überprüfbare `attempt_evidence`-Belege. `research_complete:true` nur, wenn wirklich **alle 22** abgefragt wurden; keine fiktiven Vollständigkeitsmeldungen. Der Referenzvalidator ist `scripts/morgenzeitung_source_health.py::validate_editorial_report`; Ergebnisse vor dem Schreiben validieren, Append-only schreiben und zurücklesen.

Die unabhängige Tagesabnahme um 12:15 UTC erstellt anhand von drei aufeinanderfolgenden **vollständigen** redaktionellen Tagesprotokollen `source-health/assessments/YYYY-MM-DD/run-ID.json`. Drei echte Tage ohne irgendeinen verifizierbaren Originalartikel trotz dokumentierter Original- und Alternativsuche lösen `CONFIRMED_RESEARCH_ACCESS_GAP` für den betroffenen Verlag aus. Fehlende Protokolle ergeben `AUDIT_GAP`, nicht die falsche Behauptung eines unzugänglichen Verlags. Nur Feed-Fehler, fehlender Volltext oder Nullveröffentlichungen dürfen keine solche Warnung auslösen.

Die aktiven ChatGPT-Haupt- und Ersatzaufgaben prüfen täglich diese private Diagnose und melden erstmalige bestätigte Dreitage-Ausfälle sowie Datenlücken klar und ohne doppelte Benachrichtigungen. Keine festen Verlagsquoten; unterrepräsentierte Quellen müssen gezielt nachrecherchiert werden, ohne Qualität zu simulieren. Während der ersten drei neu aufgebauten Tage ist `AUDIT_GAP` erwartbar, aber kein endgültiger Erfolg.
