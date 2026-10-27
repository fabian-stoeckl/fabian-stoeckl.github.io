# Morgenzeitung – produktive Tageslauf-Abnahme (25.10.2026)

## Entscheidende Trennung

- **Technisch geschützter Veröffentlichungsweg**: GitHub Ruleset und required PR check sind GitHub-Einstellungen, nicht bloß YAML. Der Workflow `Morgenzeitung prepublication gate / prepublication-gate` wurde für sämtliche PRs auf `main` aktiviert. Ohne ein **aktives GitHub-Branch-Ruleset** kann ein direkter Push dennoch veröffentlichen.
- **Echte journalistische Quellen**: Bei Originalartikeln wird die Verlagsseite (kein Archiv-/SMRY-Proxy) per GET auf Metadaten geprüft; `match`, `mismatch`, `conflict` und `inconclusive` werden strikt getrennt. Eine Paywall oder HTTP 403 zählt nicht als Nachweis. CI testet konkret ORF, Der Standard, Die Presse und Handelsblatt; ein Quellendefekt kann den Check rot färben.
- **Produktiver Lernerfolg**: Erst die neue veröffentlichte Artikelauswahl, unveränderte private Vorselektion, ursprüngliches privates Profil, dokumentierte echte Issue-Versionen, ein kontrafaktischer Vergleich und nachgelagerte HTTPS- und Privat-Checks können einen Erfolg belegen. Simulationen und gefälschte Nachweise sind ausgeschlossen.

## Einmalige GitHub-Einstellung (durch Repository-Admin)

In `Settings → Rules → Rulesets → New branch ruleset` für das Repository `fabian-stoeckl/fabian-stoeckl.github.io`:

1. Zielbranch `main`; **Enforcement: Active**.
2. `Require a pull request before merging` einschalten, Force-Pushes und Löschungen blockieren; keine generelle Admin-Bypass-Freigabe. Der tägliche Agent muss weiter über eigene PRs veröffentlichen können.
3. `Require status checks to pass`: `prepublication-gate` aus `Morgenzeitung prepublication gate` auswählen; außerdem `Verify site` als allgemeinen Website-Test, sofern vorhanden. Keinen Status aus einem nur nach Pfad selektiv laufenden Workflow verpflichtend machen.
4. An einem Test-Branch prüfen: ohne grünes Gate kein Merge, direkter Push nach `main` tatsächlich abgewiesen. Die notwendige Freigabe vor dem Merge beibehalten.

**Einschränkung**: Die verbundene GitHub-App kann diese Admin-Änderung nicht selbst vornehmen. Erst nach Sichtprüfung des aktiven Rulesets ist der Branch-Schutz bestätigt.

## Jeder echte Tageslauf

Die folgenden Schritte müssen **vor** bzw. **nach** der Publikation ausgeführt werden; kein Workflow darf Originalbelege aus der fertigen Ausgabe nachbauen:

1. **Vor Auswahl**: Privates unverändertes `candidates/YYYY-MM-DD.json` sowie `snapshots/YYYY-MM-DD-{profile,issues,selection-parameters}.json` schreiben; Inhalt, SHA und private Commit-Zeitpunkte dokumentieren. Alle vier Nachweise müssen vor dem öffentlichen Merge entstanden sein.
2. **Vor Merge**: PR-Gate prüft das reale Tages-JSON gegen die private Selektor-Wiederholung, zugehörigen Index und echte Original-URL-Zeitstempel.
3. **Nach HTTPS-Deployment**: Privaten `runs/YYYY-MM-DD.json`, `audits/YYYY-MM-DD-live-learning.json` und `audits/YYYY-MM-DD-acceptance.json` separat speichern und zurücklesen. `PARTIAL` aus einem Laufbericht ist kein produktiver Erfolg.
4. **Nachgelagerte automatische Kontrolle**: `.github/workflows/morgenzeitung-daily-acceptance.yml` läuft täglich um **12:15 UTC**, nach dem vorhandenen privaten Live-Audit um 09:45 UTC. Prüft HTTPS-Frische, vollständige Originaldateien und Hashes, die geordnete veröffentlichte Auswahl, den privaten Laufabschluss und aktuelle Verlagsmetadaten. Legt für jede Ausführung im privaten Repository `audits/YYYY-MM-DD-daily-acceptance-RUN_ID.json` ab und bestätigt den Byte-für-Byte-Rücklesetest.
5. **Konservative Beurteilung**: Nur wenn jeder Check PASS liefert, ist die Gesamtabnahme PASS. Ein Verlags-Widerspruch ist FAIL, fehlende oder unklare Belege sind PARTIAL. Ein vorhandener Bericht beweist die Speicherung des Prüfresultats, nicht den Erfolg des täglichen Agenten.

Die Check-Routine verändert weder `profile.json` noch echte Bewertungen, führt keinen Merge aus und erzeugt keinen neuen Artikel. Bei gescheiterter Abnahme wird die GitHub Action rot, während der private, unveränderliche Bericht den genauen Teilstatus speichert. Für jeden erneuten Versuch wird eine neue Run-ID verwendet; alte Prüfungen bleiben erhalten.

## Abnahmekriterium für 25.10.2026

Im privaten Repo müssen vor der Auswahl vier Original-Snapshots und nach der Publikation die drei Lauf-/Audit-Dokumente stehen. Öffentliche Live-Artikel-IDs müssen **in exakt derselben Reihenfolge** zur gelernten Auswahl passen und sich gegenüber der Baseline nachweisbar wegen tatsächlich verarbeiteter Bewertungen geändert haben. Sonst **PARTIAL**, selbst wenn alle Unit-Tests grün sind und die neue Ausgabe live erscheint.
