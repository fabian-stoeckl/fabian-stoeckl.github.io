<!-- website-area: {"name": "Morgenzeitung neu", "paths": ["Privat/Morgenzeitung-neu/"]} -->
# Bereichsprotokoll: Morgenzeitung neu

**Stand:** 27.10.2026. **Status:** eigenständiger neuer Bereich für tägliche, lernende Presseschau. Bestehende Morgenzeitung und ETF bleiben unverändert.

## Auftrag und vereinbarte Grundsätze
- Separater Einstieg unter /Privat/Morgenzeitung-neu/, unveränderte Alt-Kachel.
- Ziel täglich ab 07:45 Europe/Vienna: 10–15 Vertiefungen, 15–20 Headlines, einspaltig, Archiv und 3-Punkt-Bewertung.
- Breite Recherche (vorhandene Fixstarter und offene internationale Quellensuche); **inhaltlicher Fit, Vielfalt und Neuigkeitswert vor Zugänglichkeit**.
- Keine HTTP-/HEAD-/GET-Artikel-Linktests als redaktionelles Ranking-Gate. Paywall, 403 oder nur Teaser beeinflussen das Ranking nicht. Keine über die verfügbaren Belege hinausgehenden Behauptungen.
- Feedback privat in fabian-stoeckl/morgenzeitung-feedback, ausschließlich gekennzeichnete Issues "[Morgenzeitung neu] Feedback YYYY-MM-DD"; eigenes Lernprofil "morgenzeitung-neu/profile.json"; nichts davon in das öffentliche Repository übernehmen.
- Für einen Klick auf "Feedback speichern" wird wie in der bisherigen Morgenzeitung ein vorher lokal verbundener, eingeschränkter GitHub-Token benötigt. Dieser wird niemals öffentlich gespeichert.
- Keine zusätzlichen Kosten, kein eigener Server, keine Änderung der bestehenden täglichen Aufgabe.

## Architektur
- Neue statische Seite unter Privat/Morgenzeitung-neu/; datierte JSON-Ausgaben und einfacher Index.
- GitHub-Pages-Jekyll übernimmt die Veröffentlichung nach PR, normalen CI-Checks und Merge.
- Redaktionsablauf: services/morgenzeitung-neu/REDAKTION.md. Separater ChatGPT-Tagesauftrag; keine neue komplexe Capture- oder Feed-Pipeline.
- Startausgabe vom 27.10. ist **transparent aus der bereits recherchierten Alt-Ausgabe kuratiert**, keine unabhängige Neurecherche behaupten. Ab der nächsten Ausgabe unabhängiger Redaktionslauf.
- Einfache statische Strukturprüfungen: tests/morgenzeitung-neu.test.cjs und eigener GitHub-Workflow.

## Offen / künftig zu prüfen
- Echtes privates Feedback aus der **neuen** Kachel und dessen Einfluss auf die **darauffolgende** Ausgabe lassen sich erst nach mindestens einer echten neuen Nutzerbewertung und dem nächsten produktiven Lauf nachweisen.
- Tägliche pünktliche Veröffentlichung hängt weiterhin von der Ausführung und GitHub Pages ab; Zielzeit 07:45 ist kein garantierter Fertigstellungstermin.

## Vereinheitlichung der Oberfläche am 28.10.2026
Die neue Kachel `/Privat/Morgenzeitung-neu/` verwendet künftig dieselbe sichtbare Oberfläche und Präferenzseite wie die alte Morgenzeitung. Die Texte und CSS/JS werden gemeinsam wiederverwendet, sodass spätere UI-Korrekturen beiden zugutekommen. Der **Backend-Unterschied** bleibt bestehen: eigenes Tagesarchiv, das bisher eingerichtete neue Feedback-Issueformat, eigenes Profil und eigene Tagesautomation. Keine zweite neue Kachel oder Parallel-URL.
