"""Phase 7 synthetic fixtures only; no real feedback, tokens or personal data."""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "suggestion_review", ROOT / "scripts/feedback_suggestions_review.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def issue(day, comment="", ratings=None, clicked=None, number=1, edited_at=None):
    body = {
        "version": 1, "date": day, "origin": "website-explicit",
        "ratings": ratings or [], "comment": comment,
        "comment_suggestions": clicked or []
    }
    return {
        "number": number, "title": f"[Pressespiegel] Feedback {day}",
        "updated_at": edited_at or f"{day}T15:00:00Z",
        "body": mod.MARKER + json.dumps(body)
    }


def reason(text, clicked=None):
    return {
        "id": "a" * 16, "section": "Vertiefungen",
        "rating": "Teilweise relevant", "reason": text,
        "suggested_reasons": clicked or []
    }


class FeedbackSuggestionReviewTests(unittest.TestCase):
    def test_independently_written_repeats_from_two_dates_are_only_candidates(self):
        phrase = "Bei wirtschaftlichen Themen bitte stärkere empirische Einordnung."
        rows = [
            issue("2026-11-01", phrase, [reason("Mehr neue Mechanismen bei Steuerfragen erklären.")]),
            issue("2026-11-02", phrase, [reason("Mehr neue Mechanismen bei Steuerfragen erklären.")])
        ]
        before = json.dumps(rows, sort_keys=True)
        report = mod.candidates(rows)
        self.assertTrue(report["review_only"])
        self.assertEqual(report["canonical_feedback_dates"], 2)
        self.assertEqual(report["general_candidates"][0]["text"], phrase)
        self.assertEqual(report["general_candidates"][0]["distinct_feedback_dates"], 2)
        self.assertEqual(report["article_candidates"][0]["distinct_feedback_dates"], 2)
        self.assertEqual(json.dumps(rows, sort_keys=True), before,
                         "Review must NEVER rewrite input or private suggestions")

    def test_suggestion_clicks_and_near_copies_do_not_recommend_themselves(self):
        canned = "Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären."
        rows = [
            issue("2026-11-01", canned, clicked=[canned],
                  ratings=[reason("Zu juristisch für ein Randthema",
                                  clicked=["Zu juristisch für ein Randthema"])]),
            issue("2026-11-02", canned.replace("Tiefe:", "Tiefe -"),
                  ratings=[reason("Zu juristisch für ein Randthema")])
        ]
        report = mod.candidates(rows, {"suggestions": ["Zu juristisch für ein Randthema"]})
        self.assertEqual(report["general_candidates"], [])
        self.assertEqual(report["article_candidates"], [])
        self.assertGreater(report["excluded"]["prompted"], 0)

    def test_repeated_lines_in_one_issue_and_old_edit_versions_are_one_vote(self):
        phrase = "Bitte mehr quantitative Vergleiche zu Industriestrategien."
        first = issue("2026-11-01", phrase + "\n" + phrase, number=1,
                      edited_at="2026-11-01T08:00:00Z")
        edited = issue("2026-11-01", phrase, number=2,
                       edited_at="2026-11-01T09:00:00Z")
        report = mod.candidates([first, edited])
        self.assertEqual(report["canonical_feedback_dates"], 1)
        self.assertEqual(report["general_candidates"], [])
        report = mod.candidates([first, edited, issue("2026-11-02", phrase)])
        self.assertEqual(report["general_candidates"][0]["distinct_feedback_dates"], 2)

    def test_invalid_test_legacy_malformed_and_preview_issues_not_included(self):
        good = issue("2026-11-03", "Mehr belegte Perspektiven zur Digitalregulierung.")
        wrong = issue("2026-11-02", "Mehr belegte Perspektiven zur Digitalregulierung.")
        wrong["title"] = "Test: [Pressespiegel] Feedback 2026-11-02"
        rejected = issue("2026-11-04", "Mehr belegte Perspektiven zur Digitalregulierung.")
        payload = json.loads(rejected["body"][len(mod.MARKER):])
        payload["test"] = True
        rejected["body"] = mod.MARKER + json.dumps(payload)
        self.assertEqual(mod.candidates([good, wrong, rejected])["general_candidates"], [])
        self.assertEqual(mod.candidates([good, wrong, rejected])["canonical_feedback_dates"], 1)

    def test_general_and_article_groups_remain_distinct(self):
        text = "Neue vergleichbare Daten zur Produktivität wären hilfreich."
        rows = [issue("2026-11-01", text),
                issue("2026-11-02", "", [reason(text)])]
        report = mod.candidates(rows)
        self.assertEqual(report["general_candidates"], [])
        self.assertEqual(report["article_candidates"], [])


if __name__ == "__main__":
    unittest.main()
