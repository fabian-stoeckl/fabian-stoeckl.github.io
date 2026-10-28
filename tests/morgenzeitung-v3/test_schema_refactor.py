"""Metadata and repeat-penalty regression tests."""
import unittest
from scripts.morgenzeitung_v3_engine import score
from scripts.morgenzeitung_v3_schema import validate_article_metadata, validate_candidate


def item(i=1):
    return {"id":f"{i:016x}","title":"Article","source":"Journal",
            "url":"https://example.org/story/"+str(i),"topic":"Industrie",
            "fit":4,"novelty":3,"impact":4,"perspective":3}


class SchemaRefactorTests(unittest.TestCase):
    def test_repeat_penalty_exactly_once_for_both_sections(self):
        original=item()
        repeated={**original,"seen_recently":True}
        for section in ("Vertiefungen","Heute wichtig"):
            self.assertEqual(score(original,{},section)-score(repeated,{},section),12)
            self.assertEqual(score({**repeated,"material_update":True},{},section),score(original,{},section))

    def test_explicit_negative_stays_separate_from_repeat(self):
        original=item()
        p={"article_feedback":{original["id"]:{"rating":"Nicht relevant","reason":"Schon bekannt"}}}
        self.assertEqual(score(original,{}, "Vertiefungen")-score(original,p,"Vertiefungen"),20)

    def test_numeric_novelty_explanation_and_legacy_compatibility(self):
        a=item()
        b={**a,"novelty_score":3,"novelty_explanation":"Neue belegte Konsequenz"}
        self.assertEqual(score(a,{}),score(b,{}))
        self.assertEqual(validate_article_metadata(b),[])
        self.assertIn("novelty score must be a number from 0 to 5",
                      validate_article_metadata({**a,"novelty":"Neue Studie"}))
        self.assertIn("novelty and novelty_score conflict",validate_article_metadata({**a,"novelty_score":4}))
        self.assertIn("unknown evidence_level",validate_article_metadata({**a,"evidence_level":"full"}))

    def test_older_editions_keep_optional_fields_optional(self):
        self.assertEqual(validate_article_metadata({"title":"old edition","novelty":None}),[])
        self.assertEqual(validate_candidate(item()),[])
        self.assertTrue(validate_candidate({**item(),"fit":True}))


if __name__=="__main__":
    unittest.main()
