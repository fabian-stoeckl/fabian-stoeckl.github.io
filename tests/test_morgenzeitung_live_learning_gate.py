import json
import unittest
from unittest.mock import patch
from scripts.morgenzeitung_live_learning_gate import audit


class LiveGateTests(unittest.TestCase):
    def test_rejects_unverified_candidates_before_network(self):
        candidates = json.dumps([{"id":"a","topic":"Industrie","source":"X","verified":False}]).encode()
        with patch("scripts.morgenzeitung_live_learning_gate.live_json") as live:
            with self.assertRaises(ValueError):
                audit("2026-10-24", candidates, b"{}", [])
            live.assert_not_called()

    def test_rejects_missing_issue_versions(self):
        with self.assertRaises(ValueError):
            audit("2026-10-24", b"[]", b"{}", [{"number":3}])

    @patch("scripts.morgenzeitung_live_learning_gate.live_json")
    def test_matching_live_edition_never_overclaims_learning(self, live):
        live.side_effect = [{"dates":["2026-10-24"]}, {
            "date":"2026-10-24","articles":[{"id":"a"}],"preview":False}]
        candidates = json.dumps([{"id":"a","topic":"Industrie","source":"X","verified":True}]).encode()
        result = audit("2026-10-24", candidates, b"{}", [{"number":3,"updated_at":"2026-10-23T10:00:00Z"}])
        self.assertEqual(result["statuses"]["live_publication"], "PASS")
        self.assertEqual(result["statuses"]["productive_learning"], "PARTIAL")
        self.assertEqual(result["selection_comparison"]["selected_ids"], ["a"])


if __name__ == "__main__":
    unittest.main()
