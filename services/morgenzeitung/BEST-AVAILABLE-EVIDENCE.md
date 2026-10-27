# Best Available Evidence – Integration nach PR #193 (27.10.2026)

## Grundsatz
**Kein Volltextzwang.** Die unabhängig belegte Identität eines konkreten Originalartikels (Publisher, sichere Original-URL, Titel, Veröffentlichungsdatum/-zeit) und die tatsächlich verfügbare Inhaltstiefe sind getrennte Eigenschaften. Offizielle Verlagsfeeds dürfen die Artikelidentität bestätigen, nicht den Volltext. Bei bloßer Überschrift nur die Überschrift bzw. eine entsprechend gekennzeichnete Leseempfehlung ausgeben; keine zusätzlichen Tatsachen, Zahlen, Motive oder Schlussfolgerungen erfinden. Verifizierte Artikel mit Paywall dürfen keinen Relevanznachteil erhalten.

## Bestehende produktive Implementierung wiederverwenden – nicht duplizieren
- `scripts/morgenzeitung_official_feeds.py`: unabhängige offizielle Publisher-Feed-Identitätsbelege; `scripts/morgenzeitung_live_source_check.py`: eigentliche unabhängige Artikelprüfung.
- `scripts/morgenzeitung_candidate_triage.py`: Rohkandidaten einzeln als `eligible` oder `NEEDS_RESEARCH` trennen; die vollständigen echten Diagnosen privat aufbewahren.
- `scripts/morgenzeitung_source_preflight.py`: **unveränderte strenge** Prüfung ausschließlich des zuvor bereinigten `eligible`-Pools, mindestens 15 unabhängig bestätigte Artikel und Quellenvielfalt. `not blocked` ist dort korrekt: Unbestätigte Rohkandidaten gehören nicht in diesen Pool.
- Vorhandene zugriffsneutrale Auswahl-/Profil-Regression, private 22-Quellen-Rechercheprotokolle, S0–S5-Checkpoints, Ersatzlauf, unveränderliche S4/S5/S7-Belege und CI-Gates bleiben verbindlich.

## Verbindlicher Ablauf
1. Alle 22 Pflichtquellen sowie weitere geeignete Quellen tatsächlich recherchieren. Artikel auch bei Paywall entdecken und zunächst auf vergleichbarer, überprüfbarer Titel-/Vorspann-/Metadatenbasis priorisieren. Zusätzlicher Volltext liefert nur Material für präzisere Zusammenfassungen, **keinen** Relevanzbonus.
2. Für den echten Rohkandidatenpool `python3 -m scripts.morgenzeitung_candidate_triage --date YYYY-MM-DD --candidates RAW.json --eligible VERIFIED.json --diagnostics PRIVATE_DIAGNOSTICS.json` ausführen. `NEEDS_RESEARCH`-Artikel nachprüfen, gegebenenfalls durch **echte andere** Artikel ersetzen. Fehlerhafte Einzelartikel nicht in `VERIFIED.json` aufnehmen; keine fiktiven Verifikationsflags.
3. Erst den bereinigten Pool unabhängig mit `python3 -m scripts.morgenzeitung_source_preflight --candidates VERIFIED.json --date YYYY-MM-DD --minimum 15` erneut prüfen. Bei weniger als 15 oder ungenügender Quellenvielfalt gezielt weiter recherchieren; **nicht** durch Absenkung der Sicherheitsgrenzen oder Erfindung von Kandidaten publizieren.
4. Nur nach PASS private unveränderliche S4-Archivierung, redaktionelle Auswahl, S5-Audit, PR, unabhängige Prepublication-Checks, Merge, HTTPS und S7/S8 durchführen. Alle 22 Quellen und erfolglose Alternativprüfungen im echten privaten Redaktionsprotokoll erfassen; fehlende Protokolle als `AUDIT_GAP`, nicht als Verlagssperre behandeln.
5. Die Inhaltstiefe **separat** je Artikel als `FULL_TEXT`, `EXCERPT`, `DESCRIPTION` oder `HEADLINE_ONLY` dokumentieren. Eine Überschrift allein berechtigt nicht zu einer ausformulierten Analyse. Keine automatische Zwei-bis-drei-Satz-Pflicht bei unzureichender Evidenz.

## Fehler- und Wiederaufnahmestrategie
- HTTP 401/403, Paywall oder fehlender Volltext sind **keine globalen Abbruchgründe**. Bei blockierter Originalseite zulässige offizielle Metadatenwege versuchen; unbestätigte Artikel isolieren und gezielt nachrecherchieren.
- Nach jeder abgeschlossenen Recherchecharge und jeder Phase den tatsächlich erreichten Stand im privaten append-only Checkpoint sichern und zurücklesen. Bei Laufabbruch den vorhandenen Ersatzlauf am letzten unabhängig bestätigten Checkpoint fortsetzen; keine doppelte Tages-PR und keine erfundene Weiterarbeit nach Ende einer ChatGPT-Ausführung.
- Bei echter Zeit-/Toolgrenze oder nicht erfüllbarem Gate `PARTIAL` mit genauer Ursache und Checkpoint melden. Niemals `DONE` ohne S4–S8-Nachweise.

## Verbindliche Abnahmeszenarien für PR #190
1. 20 echte oder im Unit-Test kontrolliert simulierte Rohkandidaten, fünf ohne Identitätsbeleg: Triage liefert 15 `eligible` und fünf `NEEDS_RESEARCH`; nur die 15 passieren bei gültiger Quellenvielfalt den **separaten** Preflight. Keine falschen PASS für die fünf.
2. Derselbe Pool mit weniger als 15 bestätigten Artikeln oder unzureichender Quellenvielfalt: **kein** S4/PUBLISH; weitere Recherche oder echtes PARTIAL.
3. Gleiche Artikelidentität bei `full`, `teaser`, `metadata`: identische Relevanzreihenfolge; unterschiedliche, ehrlich begrenzte Zusammenfassungstiefe.
4. Gefälschter RSS-Beleg, falsche URL, Titel oder Veröffentlichungszeit: keine Freigabe. Paywall allein: kein Identitäts-FAIL und kein Relevanzmalus.
5. Abbruch nach S3 bzw. S4: privater Checkpoint ist lesbar, Ersatzlauf setzt ohne Duplikate fort; vollständiger Ende-zu-Ende-Nachweis bis HTTPS und S7/S8.
6. ETF, historische Ausgaben, private unveränderliche Belege und alle bestehenden Sicherheitsgates bleiben unberührt.

**Abnahmegrenze:** Dokumentation und Unit-Tests allein beweisen noch keinen erfolgreichen Live-Ersatzlauf. Erst ein tatsächlich durchlaufener GitHub-/ChatGPT-Produktions- oder isolierter Ende-zu-Ende-Test mit verifizierbaren privaten Belegen bestätigt die Betriebsrobustheit.
