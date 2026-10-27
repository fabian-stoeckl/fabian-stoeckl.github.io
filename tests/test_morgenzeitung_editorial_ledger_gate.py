"""Independent, offline checks for strict daily source-ledger acceptance."""
import unittest
from scripts.morgenzeitung_editorial_ledger_gate import verify_ledger
from scripts.morgenzeitung_source_health import REQUIRED_SOURCES


def complete():
    rows = []
    for name in REQUIRED_SOURCES:
        rows.append({
            "publisher": name,
            "outcome": "NO_VERIFIABLE_ARTICLES",
            "verified_original_count": 0,
            "selected_count": 0,
            "attempted_methods": ["direct_original", "independent_index"],
            "attempt_evidence": [
                "Direct original https://example.com/article checked",
                "Independent index https://example.org/search checked"
            ],
        })
    return {"report_type": "source_editorial_research",
            "date": "2026-10-27", "research_complete": True,
            "publisher_count": 22, "publishers": rows}


class LedgerGateTests(unittest.TestCase):
    def test_complete_22_rows_with_negative_evidence_is_coverage_pass(self):
        result = verify_ledger("2026-10-27", {"date": "2026-10-27", "articles": []}, complete())
        self.assertEqual(result["verdict"], "PASS_SOURCE_RESEARCH_COVERAGE")
        self.assertEqual(len(result["no_individual_original_confirmed"]), 22)

    def test_missing_publisher_fails(self):
        ledger = complete()
        ledger["publishers"].pop()
        with self.assertRaises(ValueError):
            verify_ledger("2026-10-27", {"date": "2026-10-27", "articles": []}, ledger)

    def test_missing_second_evidence_fails(self):
        ledger = complete()
        ledger["publishers"][0]["attempt_evidence"].pop()
        with self.assertRaises(ValueError):
            verify_ledger("2026-10-27", {"date": "2026-10-27", "articles": []}, ledger)

    def test_published_source_count_must_match(self):
        ledger = complete()
        with self.assertRaises(ValueError):
            verify_ledger("2026-10-27", {"date": "2026-10-27",
                          "articles": [{"source": "ORF"}]}, ledger)


if __name__ == "__main__":
    unittest.main()
