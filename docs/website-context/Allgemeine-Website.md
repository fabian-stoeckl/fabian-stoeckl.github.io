<!-- website-area: {"name": "Allgemeine Website", "paths": ["index.md", "Privat/index.html"]} -->
# Bereichsprotokoll: Allgemeine Website

**Stand:** 18.10.2026. **Status:** bestehende Website; letzte freigegebene Privat-Änderung PR #20 gemergt.  
**Quellen:** tatsächlicher Stand auf `main`, offene PRs, CI-Läufe sowie dokumentierte Nutzerfreigaben.

## Geltungsbereich und Dateien

- Öffentliche Forschungswebsite (`/`): `index.md`, `_layouts/default.html`, `assets/css/style.scss`, `_config.yml`; Publikationen, Referenzen, Profil, Links und visuelles Design.
- Privat-Einstieg (`/Privat/`): `Privat/index.html`. Links zu ETF, **Persönliche Zeitung** und „Website ändern“.
- Arbeits- und Testanweisungen: `AGENTS.md`, `DEVELOPMENT.md` und `.github/workflows/verify-etf-charts.yml`.
- ETF-Funktionalität und Persönliche Zeitung haben **eigene** Bereichsprotokolle.

## Bestätigte Gestaltungs- und Arbeitsentscheidungen

- Akademische Hauptseite und Publikationsinformationen erhalten; Änderungen gezielt und nicht durch pauschale Neugestaltung.
- Hoverzustände dezent (dunkleres Blau/Hintergrundfläche statt erzwungener Fettschrift); Linktexte nicht unnötig umbrechen.
- Auf `/Privat/`: ruhiger, heller Hintergrund und Kacheln im bestehenden Stil; **keine** saisonale Animation.
- „Website ändern“-Kachel führt auf den bestehenden ChatGPT-Skill-Link; nicht ohne ausdrücklichen Auftrag ersetzen.

## Dokumentierte jüngste Änderungen

| Datum | Änderung | Beleg / Status |
| --- | --- | --- |
| 17.10.2026 | Pressespiegel-Kachel im Privatbereich, neue Platzhalterseite, Skill-Link unverändert | [PR #19](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/19), veröffentlicht; Tests erfolgreich |
| 17.–18.10.2026 | Schlusszeile „Weitere Themen finden hier später ihren Platz.“ und ungenutzte CSS-Regel entfernt | [PR #20](https://github.com/fabian-stoeckl/fabian-stoeckl.github.io/pull/20), Nutzerfreigabe 17.10.; zwei erfolgreiche PR-Prüfungen; am 17.10. um 17:22 UTC gemergt (18.10. in Bangkok) |
| 03.–06.10.2026 | Mehrere bereits umgesetzte Homepage-/Privat-Designkorrekturen (u. a. Hover und Animation) | Bestandsaufnahme aus Repository-Historie; Einzelheiten in zugehörigen historischen PRs/Commits nachschlagen |

## Offenes / künftig zu prüfen

- Inhaltliche neue Änderungen liegen für diesen Bereich derzeit **nicht als konkreter Auftrag** vor.
- Der Skill selbst liegt nicht im Website-Repository; die Repository-Protokolle ersetzen keine Prüfung der separat installierten Skill-Anweisungen.


## Historische Inhaltsentscheidungen, übernommen am 18.10.2026

Quelle: am 17.10. recherchierte Skill-Notizen, damals mit PRs #2–#18 abgeglichen. Kein vollständiges Gesprächsarchiv.

### Öffentliche Homepage
- Link-Hover darf weder Schriftstärke noch Umbrüche/Positionen ändern. Dunkleres Blau und dezenter hellblauer Hintergrund; gleicher Effekt für Abstract-Elemente. PR #7 und #9 zusammengeführt; aktuelles CSS bestätigt `font-weight:inherit`, Blau #069 und rgba(38,124,185,0.10).
- „Substituting Clean for Dirty Energy: A Bottom-Up Analysis“ mit dezenter verlinkter JAERE-Best-Paper-Auszeichnung; AERE-Link unmittelbar beim Titel. PR #7 und aktuelles `index.md` bestätigen dies.
- „Core developer (formerly) of“ entfernen, „(Green) Growth Theory“ ausdrücklich erhalten (#7).
- „Work in progress“ samt zugehörigem Eintrag entfernen (#8); Teaching entfernen (#10). Aktueller Quellcode enthält beide Abschnitte nicht mehr.
- Dr. José Delgado ergänzen (#6). Die zwischenzeitlich gewünschte Reihenfolge Delgado vor Wolf-Peter Schill ist durch die spätere Entfernung Schills aus References überholt (#11). Paper-Koautorenschaft Schills ausdrücklich erhalten. Aktueller Quellcode bestätigt Referenzen Meran, Kemfert und Delgado sowie Schill als Koautor.
- „Email:“ entfernen. Normale Punkte und kompakte `[at]`-Schreibweise ohne umgebende Leerzeichen; keine `[dot]`-Schreibweise. PR #12/#13 und Quellcode bestätigen Referenzadressen in diesem Format. Keine Kontaktadressen im Protokoll duplizieren.
- Domain-Konfiguration/copyright wurden in #3 angepasst; bei späteren Änderungen den aktuellen `_config.yml`/Layout-Stand lesen.


## 18.10.2026: Workflow-Abgleich

- Verbindliche Protokolle liegen jetzt ausschließlich in `docs/website-context/`; der bestehende Skill lädt README und gewähltes Protokoll bei jedem Start frisch aus GitHub.
- Skill steuert Auswahl/Freigabe/Veröffentlichung; AGENTS.md enthält technische Regeln. README wird aus Protokoll-Metadaten erzeugt; neue Bereiche benötigen keine namentlichen Testcode-Änderungen.
- Englischer generischer Starttext bleibt auf Nutzerwunsch bestehen; Bereichsauswahl wurde vom Nutzer am 17.10. damit bestätigt. Link-Test mit q-Parameter änderte den Text nicht, deshalb Original-Link erhalten.
- PR #20 ist veröffentlicht: /Privat/ am 18.10. über HTTPS geprüft, Schlusszeile fehlt. PR #21 etablierte die GitHub-Protokolle; dessen Build und Pages-Bereitstellung waren erfolgreich.
- Dieser Abgleich ändert nur interne Anweisungen, Protokolle und Testautomatisierung. Keine ETF-Daten, Berechnungen oder Website-Seiten geändert. Nutzerauftrag autorisiert diese interne Bereinigung.
- Status: PR #22 zusammengeführt als 26fe733ef3ed34ff7c34cab7a5ede084a22da17e. Vollständige PR-Prüfungen 39084361977 und 39084360337 erfolgreich; Pages-Bereitstellung 39102729346 erfolgreich. Der Workflow ist auf main verfügbar.
- Einschränkung: ChatGPT-Weboberfläche hier abgemeldet; ein tatsächlicher neuer angemeldeter Webchat ist noch nicht geprüft. Agententests getrennt davon ausweisen.
- Rücknahme: eigene Workflow-Dateien anhand der PR-Differenz auf Basis 167ad15fe8ec66bcbf90f65901fbc55b48c54370 zurücksetzen, unabhängige spätere Änderungen erhalten.

## Abschlussprüfung am 18.10.2026

- Bestehenden Skill unter gleicher Identität gespeichert und den gespeicherten Stand erneut geprüft: GitHub-Protokolle als einzige Quelle, keine lokalen Protokollkopien mehr. Relevante Historie vor Entfernung übernommen.
- Zwei unabhängige Agententests ohne Eltern-Chatverlauf: ETF-Protokoll tatsächlich vom GitHub-Commit 167ad15fe8ec66bcbf90f65901fbc55b48c54370 gelesen; allgemeiner englischer Einstieg las nach Merge das README von 26fe733ef3ed34ff7c34cab7a5ede084a22da17e und fragte nach Allgemeine Website, ETF, Pressespiegel oder Neuer Bereich. Keine Beispieländerung ausgeführt.
- Dynamische Tests bestanden: vier Bereiche einschließlich geplanter Bereiche, fehlende Bereichszuordnung, veraltetes Verzeichnis, doppelte Namen, unsichere Pfade und Jekyll-Ausschluss.
- Nach Bereitstellung Homepage, Privat, ETF und Pressespiegel per HTTPS erreichbar (200). Die drei statischen Privat-Seiten sind bytegleich mit der bestehenden geprüften Quelle. Keine Website-Inhalte oder Finanzdaten geändert.
- Offen bleibt nur der echte neue Chat über die angemeldete ChatGPT-Weboberfläche: hier war die Sitzung abgemeldet. Agententests bestätigen das Verhalten der Anweisungen, nicht den vollständigen UI-Aufruf. Der allgemeine Agententest wurde nach einer Nutzungslimit-Unterbrechung erfolgreich wiederholt.
- Dieser Abschlussnachtrag betrifft ausschließlich interne Dokumentation; sein Merge-/Checkstatus ist direkt im zugehörigen Dokumentations-PR nachprüfbar.

## 28.10.2026: Bereinigte Privat-Kacheln

- Drei Kacheln beibehalten: ETF, **Persönliche Zeitung**, **Website ändern**. Die Website-ändern-Skill-Kachel ist ausdrücklich vom Nutzer zum Beibehalten bestimmt; ihr Link und ihr Design bleiben unverändert.
- Frühere Zeitungen sind nicht mehr produktiv. Die einzige Zeitung liegt unter `Privat/Persoenliche-Zeitung/` und wird über diese Adresse direkt geöffnet; für frühere Zeitungs-URLs gibt es keine Umleitungen. Die Produktgeschichte steht im Bereichsprotokoll `Persoenliche-Zeitung.md`.

## Aktueller Farbstil und Ordner – 28.10.2026

Auf `/Privat/` bleiben genau drei Kacheln: ETF (Terrakotta), Persönliche Zeitung (Blau), Website ändern (Violett). Der Skill-Link und die ETF-Funktionalität bleiben unverändert. Zeitungsadresse: `/Privat/Persoenliche-Zeitung/`, keine alten Zeitungsumleitungen.

## 28.10.2026 – keine alten Zeitungsordner mehr

Der alte Zeitungsordner und seine Redirect-Einträge sind entfernt. Nur die direkte aktuelle Zeitung unter `Privat/Persoenliche-Zeitung/` bleibt. Die drei Kacheln und ihre Farben sowie der bestehende Website-ändern-Link bleiben unverändert.
