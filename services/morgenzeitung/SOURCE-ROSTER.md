## Zugriffsneutralität (27.10.2026)

Verbindlicher zusätzlicher Schutz: **Volltext verfügbar = 0 Relevanzbonus; Volltext blockiert = 0 Relevanzmalus.** Kandidaten aller Fixstarter zunächst nur anhand derselben unabhängig bestätigbaren Felder (Titel, Original-URL, Datum/Zeit, Verlag/Ressort, öffentlich publizierter Vorspann, Thema, Neuigkeit, dokumentiertes Nutzerfeedback) priorisieren; danach für die **Darstellung** und Faktendichte zwischen `full`, `teaser` und `metadata` unterscheiden. Ein fehlender Zugang zum Volltext darf nicht in eine niedrigere redaktionelle Priorität übersetzt werden. Die Redaktion muss zugleich vermeiden, unbelegte Sachbehauptungen über den ungelesenen Volltext zu machen. Der harte Identitätsnachweis bleibt Pflicht; wenn offizielle Feeds oder Originalmetadaten noch nicht vom GitHub-Gate akzeptiert werden, diese strukturelle Prüflücke separat erfassen, nie stillschweigend den Verlag ersetzen.

**Handelsblatt als Fixstarter**: Hauptseite und Originalartikel können direkt zugänglich sein, einzelne Beiträge jedoch nur mit Einleitung. Offizielle Verlags-RSS-Übersicht: `https://www.handelsblatt.com/rss-feeds/`; Wirtschafts-Feed `https://www.handelsblatt.com/contentexport/feed/wirtschaft` (XML; im normalen HTML-Webleser nicht direkt darstellbar). Offizielle RSS-Entdeckung als zusätzlichen Weg prüfen, ohne daraus pauschal Volltextzugang oder automatisches GitHub-Preflight-PASS abzuleiten.

# Morgenzeitung – verbindlicher Quellenpool und offene Entdeckung (26.10.2026)

## Grundsatz
Der Recherchepool besteht aus (A) **Fixstartern**, die **an jedem Erscheinungstag aktiv abgefragt** und mit einem überprüfbaren Rechercheergebnis protokolliert werden, (B) **dauerhaft aufgenommenen Erweiterungen** und (C) **täglich neu entdeckten Quellen**. Fixstarter sind Suchpflicht, **keine Veröffentlichungsquote**. Auch wenn eine Quelle heute keinen geeigneten Artikel liefert, muss ihre Abfrage dokumentiert werden. Reuters ist eine Quelle unter vielen, kein primärer oder exklusiver Eingangskanal. Paywalls und Sprachen sind kein Ausschlussgrund.

## A – Fixstarter (jeden Tag einzeln durchsuchen)
- Österreich: ORF, Der Standard, Die Presse, Kronen Zeitung.
- Deutschland: Handelsblatt, Frankfurter Allgemeine Zeitung (FAZ), Süddeutsche Zeitung (SZ), DIE ZEIT, DER SPIEGEL, BILD, WirtschaftsWoche.
- International: Financial Times, The New York Times, The Washington Post, The Guardian (UK), Neue Zürcher Zeitung (NZZ), Reuters, Associated Press (AP), Bloomberg, Euronews.

## B – dauerhaft erweiterbarer Bestand
Weitere verlässlich recherchierte Publikationen werden in dieser Datei mit Name, Ressort-/Regionalstärken, Qualitätsnotiz und Aufnahmedatum ergänzt.

- **BBC News** (dauerhaft aufgenommen am **26.10.2026**): eigenständige Wirtschafts-, Energie-, Technologie- und internationale Berichte; offizielle World-/Business-RSS-Feeds lieferten am 26.10. mehrere überprüfbare Original-URLs mit exakten Publikationszeiten, darunter Rechenzentrums-Infrastruktur, britische Budgetpolitik und Energiewende. Redaktionelle Vielfalt ergänzend zu deutschsprachigen Medien; RSS-Metadaten allein sind keine Volltext-Verifikation.
- **POLITICO Europe** (dauerhaft aufgenommen am **26.10.2026**): EU-Politik, Handel, Sanktionen und europäische Innenpolitik; offizieller Feed belegte am 26.10. Beiträge zu EU-Kanada, französischer Politik und Russlands Schattenflotte. Podcasts als solche kennzeichnen; Originalartikel und Datumsbelege vor Auswahl gesondert prüfen.

Weitere geeignete Kandidaten für systematische Sichtung: The Economist, EUobserver, Nikkei Asia, Rest of World, Nature, Science, Carbon Brief, IEA, Eurostat, Europäische Kommission, OECD, IWF. Primärquellen ergänzen Journalismus; sie ersetzen keine unabhängige Einordnung.

## C – tägliche offene Entdeckung
1. **Zuerst** alle Fixstarter und alle dauerhaft aufgenommenen Medien einzeln durchsuchen: aktuelle Hauptseiten, Ressorts, offizielle RSS/Feeds, Suchfunktionen bzw. indexierte Originalartikel. Jede Quelle mit Abfragezeit, Suchweg, gefundenen Kandidaten oder begründetem Nulltreffer sowie Zugriffsproblemen privat protokollieren. Ein HTTP 401/403 ist kein Nulltreffer.
2. **Danach immer zusätzlich** themen- und ereignisorientiert ohne Domain-Whitelist weltweit recherchieren. Neue Medien, Fachpublikationen, lokale Originalberichte, investigative Quellen und relevante Primärdokumente berücksichtigen. Mindestens mehrere unabhängige Suchrichtungen über unterschiedliche Themen/Regionen nutzen; nicht nur Reuters-Meldungen umschreiben.
3. Für jeden gefundenen Artikel Quelle, Original-URL, Titel, Zeitpunkt, Inhalt und unabhängige Verifikation prüfen. Mehrere Berichte zum selben Ereignis unterscheiden; Quellenidentität niemals vortäuschen. Ungeprüfte Treffer nicht als verifiziert archivieren.
4. **Lernen und Ausbau:** Nach jedem Lauf privat festhalten, welche neuen Quellen hochwertige, eigenständige, relevante Beiträge geliefert haben, welche schwach oder technisch blockiert waren und welche Themen/Regionen unterrepräsentiert blieben. Bewährte neue Quellen als zusätzliche Dauerquellen mit Begründung und Datum in diese Datei übernehmen (separater PR mit Tests), nie Fixstarter stillschweigend streichen. Echtes Leserfeedback beeinflusst Relevanz, nicht die Pflicht zur breiten Suche.
5. **Kontrolle vor Archivierung:** Rechercheprotokoll muss alle Fixstarter enthalten; darüber hinaus durchgeführte offene Entdeckung und neue Kandidaten müssen sichtbar sein. Quellenkonzentration (z.B. 15/16 Reuters) ist ein ausdrückliches Qualitätswarnsignal und Anlass für weitere Recherche **vor** privatem unveränderlichem Capture. Keine künstlichen Quoten oder erfundenen Treffer. Bei Zugriffsproblemen andere Quellen und offizielle Belege suchen; keine nachträgliche Änderung archivierter Pools.
6. Nur nach echten Prüfungen Auswahl, privater Snapshot, Prepublication-Gate, CI, Veröffentlichung, HTTPS-Abnahme und privater Lern-Audit gemäß AGENT-ABLAUF.md. Fehlende Abfragen oder Belege offen als PARTIAL/FAIL ausweisen, nicht stillschweigend PASS.

Diese Regeln gelten für Hauptlauf und Ersatzlauf gleichermaßen. Keine neuen kostenpflichtigen Dienste, keine ETF-Änderungen.
