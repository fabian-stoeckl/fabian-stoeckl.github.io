# Website-Bereichsprotokolle

**Projekt:** [fabian-stoeckl/fabian-stoeckl.github.io](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io) · [www.fabian-stoeckl.com](https://www.fabian-stoeckl.com)  
**Stand der Bestandsaufnahme:** 18.10.2026 (Repository- und PR-Prüfung).  
**Geltungsbereich:** menschlich gepflegte Kurzprotokolle; keine automatische Kopie alter Chats.

## Bereiche

| Auswahl im Skill/Chat | Protokoll | Website |
| --- | --- | --- |
| Allgemeine Website | [Allgemeine-Website.md](Allgemeine-Website.md) | `/` und `/Privat/` |
| ETF | [ETF.md](ETF.md) | `/Privat/ETFs/` |
| Pressespiegel | [Pressespiegel.md](Pressespiegel.md) | `/Privat/Pressespiegel/` |
| Neuer Bereich | Neues Protokoll nach demselben Schema anlegen und hier verlinken | erst nach Abstimmung |

## Verbindlicher Ablauf beim Ändern

1. **Bereich zuerst erfragen oder die ausdrückliche Auswahl übernehmen.** Vor dem Vorschlag einer Änderung `AGENTS.md` und das betreffende Protokoll lesen; letzten dokumentierten Stand knapp bestätigen. Kein erfundener Änderungswunsch.
2. `main`, offene PRs und die aktuellen CI-/Deploy-Läufe prüfen; bei Abweichung zum Protokoll **tatsächlichen GitHub-Stand vorziehen** und Protokoll abgleichen.
3. Vorschlag/Änderung auf **separatem Branch und PR**, passende Desktop-/Mobilvorschau; Freigabe durch den Nutzer abwarten. Bei rein interner Dokumentationspflege kann eine ausdrücklich beauftragte Komplettierung als Freigabe gelten; Änderungen an öffentlich sichtbaren Seiten erfordern deren konkrete Freigabe.
4. Nach Freigabe vollständige Tests (Jekyll, ETF, Browser, responsive Ansicht), erst bei Erfolg mergen/publizieren; anschließende GitHub-Pages- und Live-Kontrolle sowie Rücknahmemöglichkeit.
5. **Bei jedem relevanten PR das betroffene Protokoll im selben PR aktualisieren**: Entscheidung, Änderung, betroffene Dateien, Prüfungen, Freigabe, PR/Commit, Publikationsstatus und konkrete offene Punkte. Andere Bereiche nur aktualisieren, falls tatsächlich betroffen. Keine Behauptung einer Live-Prüfung ohne Nachweis.
6. Bei neuen Bereichen dieses Inhaltsverzeichnis, `AGENTS.md` und den Kontext-Vollständigkeitstest erweitern.

Die Protokolle sind **im Repository versioniert**. Das ChatGPT-Skill selbst wird getrennt verwaltet; es wird durch diese Dateien **nicht automatisch umkonfiguriert**. Der Skill muss zum tatsächlichen Lesen an diese Pfade bzw. an `AGENTS.md` gebunden sein.

## Technik und Grenzen

- Jekyll-Seite: `index.md`, `_layouts/default.html`, `assets/css/style.scss`; Privatbereich: `Privat/`; ETF: `Privat/ETFs/`.
- Vorschau- und Testanweisungen: [DEVELOPMENT.md](../../DEVELOPMENT.md).
- `docs/` ist in `_config.yml` ausgeschlossen; diese Arbeitsprotokolle **nicht** als öffentliche Website-Seiten ausliefern.
- Protokolle dokumentieren bestätigte Entscheidungen und nachprüfbaren Codezustand; unbekannte Altentscheidungen nicht rekonstruieren oder als gesichert ausgeben.

## Abgleich zum 18.10.2026

- PR [#19](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/19): Pressespiegel-Kachel und Platzhalterseite auf `main` übernommen; ursprünglicher Skill-Link bleibt.
- PR [#20](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/20): veralteten Schlusssatz im Privatbereich nach Freigabe und erfolgreichen PR-Tests auf `main` übernommen. Live-Deployment separat nachzuprüfen.
- Veralteter PR [#1](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/1): Screenshot-Ausschlüsse/CI-Artefakte bereits in neuerer Form umgesetzt; kein altes Diff über aktuelle Dateien mergen.
