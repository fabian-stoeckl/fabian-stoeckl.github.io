# Bereichsprotokoll: Allgemeine Website

**Stand:** 18.10.2026. **Status:** bestehende Website; letzte freigegebene Privat-Änderung PR #20 gemergt.  
**Quellen:** tatsächlicher Stand auf `main`, offene PRs, CI-Läufe sowie dokumentierte Nutzerfreigaben.

## Geltungsbereich und Dateien

- Öffentliche Forschungswebsite (`/`): `index.md`, `_layouts/default.html`, `assets/css/style.scss`, `_config.yml`; Publikationen, Referenzen, Profil, Links und visuelles Design.
- Privat-Einstieg (`/Privat/`): `Privat/index.html`. Links zu ETF, Pressespiegel und „Website ändern“.
- Arbeits- und Testanweisungen: `AGENTS.md`, `DEVELOPMENT.md` und `.github/workflows/verify-etf-charts.yml`.
- ETF-Funktionalität und Pressespiegel-Seite haben **eigene** Bereichsprotokolle.

## Bestätigte Gestaltungs- und Arbeitsentscheidungen

- Akademische Hauptseite und Publikationsinformationen erhalten; Änderungen gezielt und nicht durch pauschale Neugestaltung.
- Hoverzustände dezent (dunkleres Blau/Hintergrundfläche statt erzwungener Fettschrift); Linktexte nicht unnötig umbrechen.
- Auf `/Privat/`: ruhiger, heller Hintergrund und Kacheln im bestehenden Stil; **keine** saisonale Animation.
- Vor sichtbarer Veröffentlichung: konkrete Vorschau → ausdrückliche Freigabe → vollständige Prüfungen → Merge → Live-Kontrolle; Änderungen auf separatem Branch/PR, nicht direkt auf `main`.
- „Website ändern“-Kachel führt auf den bestehenden ChatGPT-Skill-Link; nicht ohne ausdrücklichen Auftrag ersetzen.

## Dokumentierte jüngste Änderungen

| Datum | Änderung | Beleg / Status |
| --- | --- | --- |
| 17.10.2026 | Pressespiegel-Kachel im Privatbereich, neue Platzhalterseite, Skill-Link unverändert | [PR #19](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/19), veröffentlicht; Tests erfolgreich |
| 17.–18.10.2026 | Schlusszeile „Weitere Themen finden hier später ihren Platz.“ und ungenutzte CSS-Regel entfernt | [PR #20](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/20), Nutzerfreigabe 17.10.; zwei erfolgreiche PR-Prüfungen; am 18.10. nach `main` gemergt |
| 03.–06.10.2026 | Mehrere bereits umgesetzte Homepage-/Privat-Designkorrekturen (u. a. Hover und Animation) | Bestandsaufnahme aus Repository-Historie; Einzelheiten in zugehörigen historischen PRs/Commits nachschlagen |

## Offenes / künftig zu prüfen

- **Nach PR #20:** Pages-Deployment und `/Privat/` live prüfen; erst danach als „live geprüft“ kennzeichnen.
- Inhaltliche neue Änderungen liegen für diesen Bereich derzeit **nicht als konkreter Auftrag** vor.
- Der Skill selbst liegt nicht im Website-Repository; die Repository-Protokolle ersetzen keine Prüfung der separat installierten Skill-Anweisungen.

## Protokoll für nächste Änderung (ausfüllen, nichts erfinden)

- Datum / Änderungsauftrag:
- Entscheidung und betroffene Dateien:
- Branch / PR / Commit:
- Vorschau und ausdrückliche Freigabe:
- Technische und visuelle Tests:
- Merge, Deployment und Live-Kontrolle:
- Offen / Rücknahmebasis:
