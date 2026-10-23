import unittest
from scripts.morgenzeitung_feedback import learn
D="2026-11-01"
A="a000000000000001"
B="a000000000000002"
C="a000000000000003"
ED={D:{"headlines":[{"id":A,"topic":"Industrie"},{"id":B,"topic":"Promi"},{"id":C,"region":"Österreich"}],"articles":[]}}
def issue(n,v,ts="2026-11-01T12:00:00Z"):
    body="Ausgabe: "+D+"\n"
    for aid,rating,reason in v:
        body+=f"Bereich: Heute wichtig\nArtikel-ID: {aid}\nBewertung: {rating}\nBegründung: {reason}\n\n"
    return {"number":n,"title":"[Morgenzeitung] Sammelbewertung "+D,"body":body,"updated_at":ts}
class Adversarial(unittest.TestCase):
    def test_thirty_replays_are_idempotent(self):
        issues=[issue(1,[(A,"Sehr relevant","–"),(B,"Nicht relevant","–")])]
        p={}
        for _ in range(30): p,report=learn(p,issues,ED)
        self.assertEqual(report["ratings"],2)
        self.assertEqual(report["signals"],0)
    def test_correction_replaces_vote(self):
        old=issue(1,[(A,"Sehr relevant","–")])
        new=issue(1,[(A,"Nicht relevant","Correction")],"2026-11-01T13:00:00Z")
        p,report=learn({},[old,new],ED)
        self.assertEqual(report["ratings"],1)
        self.assertEqual(p["topic_evidence"][0]["negative"],1)
    def test_invalid_article_rejected(self):
        with self.assertRaises(ValueError):
            learn({},[issue(1,[("ffffffffffffffff","Sehr relevant","–")])],ED)
    def test_synthetic_issue_excluded(self):
        real=issue(1,[(C,"Nicht relevant","Too narrow")])
        fake=issue(2,[(A,"Sehr relevant","–")])
        fake["body"]+="TEST: true"
        p,report=learn({},[real,fake],ED)
        self.assertEqual(report["ratings"],1)
        self.assertEqual(p["computed_learning_signals"],[])
        self.assertEqual(p["editorial_review_queue"][0]["reason"],"Too narrow")
    def test_conflicting_votes_do_not_create_signal(self):
        edition={D:{"headlines":[{"id":A,"topic":"KI"},{"id":B,"topic":"KI"}],"articles":[]}}
        p,report=learn({},[issue(1,[(A,"Sehr relevant","–"),(B,"Nicht relevant","–")])],edition)
        self.assertEqual(report["signals"],0)
        self.assertEqual(p["topic_evidence"][0]["net_score"],0)
if __name__=="__main__": unittest.main()
