"""Publisher openness regression – synthetic URLs test structure, NOT article existence."""
import unittest

from scripts.morgenzeitung_editorial import select_articles
from scripts.morgenzeitung_source_evidence import audit_sources
from scripts.morgenzeitung_daily_acceptance import inspect_publisher_pages

# Deliberately include internationally diverse domains beyond the fixed
# four-publisher canary smoke. These test URLs are NOT real published articles.
PUBLISHER_DOMAINS = (
    ("Handelsblatt", "www.handelsblatt.com"),
    ("Der Standard", "www.derstandard.at"),
    ("FAZ", "www.faz.net"),
    ("SZ", "www.sueddeutsche.de"),
    ("Financial Times", "www.ft.com"),
    ("New York Times", "www.nytimes.com"),
    ("Washington Post", "www.washingtonpost.com"),
    ("The Guardian", "www.theguardian.com"),
    ("Reuters", "www.reuters.com"),
    ("Foreign Affairs", "www.foreignaffairs.com"),
    ("Nature", "www.nature.com"),
)


def fixture():
    return [
        {"id": f"publisher-{i}", "source": source, "topic": "Weltwirtschaft",
         "source_url": f"https://{host}/synthetic-url-validation-test",
         "verified": True, "published_at": "2026-10-23T12:00:00Z"}
        for i, (source, host) in enumerate(PUBLISHER_DOMAINS)
    ]


class OpenPublishersTests(unittest.TestCase):
    def test_original_link_validation_has_no_publisher_whitelist(self):
        pool = fixture()
        evidence = audit_sources(pool)
        self.assertTrue(evidence["source_url_structure_verified"])
        self.assertEqual(evidence["candidate_count"], len(PUBLISHER_DOMAINS))

    def test_editorial_selection_accepts_global_publishers(self):
        pool = fixture()
        chosen, audit = select_articles(pool, {}, limit=len(pool), max_per_source=4)
        self.assertEqual([a["id"] for a in chosen], [a["id"] for a in pool])
        self.assertEqual(len(audit), len(pool))

    def test_live_metadata_checker_can_handle_unknown_publishers(self):
        pool = fixture()
        recorded = []
        def fake_fetch(url, declared):
            recorded.append(url)
            return {"status": "match"}
        samples = [{"source": a["source"], "url": a["source_url"],
                    "published_at": a["published_at"]} for a in pool]
        result = inspect_publisher_pages(samples, count=len(samples), fetch=fake_fetch)
        self.assertEqual(len(result), len(PUBLISHER_DOMAINS))
        self.assertEqual(len(recorded), len(PUBLISHER_DOMAINS))

    def test_http_untrusted_sources_still_rejected(self):
        pool = fixture()
        pool[0]["source_url"] = "http://www.handelsblatt.com/insecure"
        self.assertFalse(audit_sources(pool)["source_url_structure_verified"])


if __name__ == "__main__":
    unittest.main()
