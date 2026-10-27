# Erweiterbare Quellenbelege (27.10.2026)

Die versionierte Datei `publisher-evidence-registry.json` ergänzt die bestehende feste Verlagsliste. Neue Verlage benötigen einen geprüften Registry-Eintrag (Originalhosts, bis zu acht verlagseigene HTTPS-Feeds), keine Änderung am Verifikationsalgorithmus. Kandidaten dürfen die Feedadresse niemals selbst bestimmen. Änderungen laufen über PR, Tests und GitHub-Runner-Smoke; nur tatsächlich geladene und exakt nach URL, Titel und Veröffentlichungsminute passende Originaleinträge zählen als Artikelbeleg. Ein lesbarer Feed allein genügt nicht.

**Der Standard:** Wirtschaft, Inland, International und Gesamtfeed als alternative offizielle Quellen; bisheriger Wirtschaft-Feed bleibt zuerst. **Bloomberg:** Economics, Industries, Markets und Hauptfeed auf bloomberg.com; RSS-Items können nur Identität/Datum belegen, nie Volltext. **POLITICO Europe:** vier verlagseigene `politico.eu`-Feedadressen als überprüfbare Kandidaten eingetragen (Hauptfeed, Energie, Politik, Nachhaltigkeit). Drittanbieter melden ihre Existenz; **das ist noch kein unabhängiger Live-Nachweis aus GitHub Actions**. Ein Feed oder Artikel zählt erst nach erfolgreichem tatsächlichem Abruf und exakter Original-URL-/Titel-/Zeitprüfung. Die US-Seite `politico.com` ist ausdrücklich kein Beleg für `politico.eu`; bei fehlender Identität bleibt `INCONCLUSIVE`.

## Selbstheilung bei neuen Quellen

1. Quellenentdeckung: Verlag und tatsächliche Originaldomain getrennt von Artikelhinweisen erfassen; Feed-Adressen nur aus unabhängiger Recherche und mit PR-Review in die Registry aufnehmen.
2. Zugriffswege: Direkter Originalabruf; bei Zugangshürden sichere verlagseigene Feed-Fallbacks; thematische Suchindizes dienen nur der *Entdeckung*, nie als Ersatz für Originalidentität.
3. Sicherheit: HTTPS, geprüfte Hosts, keine frei steuerbaren Redirects/Proxies, begrenzte XML-Größe, keine DTD, exakte Titel-/URL-/Zeitprüfung. Bei Konflikten oder fehlender Evidenz nicht veröffentlichen.
4. Persistenz: Pro Medium und Ausgabe Suchwege, HTTP-/Feedstatus, Suchzeitpunkt, Originalartikel, Ausschlussgrund und `NO_SUITABLE_ARTICLES`/`NO_VERIFIABLE_ARTICLES`/`AUDIT_GAP` privat unveränderlich archivieren. Feed-Überwachung ist nicht gleich vollständiger S3/S4-Recherchenachweis.
5. Reparatur: Netzwerkfehler mit begrenztem Backoff erneut versuchen, alternative genehmigte Ressortfeeds verwenden und nur betroffene Quelle erneut prüfen. Neue Feeds bei wiederholtem Ausfall ersetzen – nach unabhängigem Nachweis und PR-Test.
6. Abnahme: 22/22 dokumentierte Recherchewege und separat geprüfte ausgewählte Artikel. Kein künstliches PASS bei nicht belegten Artikeln; kein pauschales FAIL allein wegen Paywall. Mehrtägige Quellengesundheit separat ausweisen.

Diese Änderung führt den konfigurierbaren sicheren Feed-Pfad ein, aber implementiert **keinen** autonomen PR-Generator für neue Verlage und bestätigt **noch keinen** neuen Live-RSS-Identitätsbeleg für Bloomberg oder POLITICO.
