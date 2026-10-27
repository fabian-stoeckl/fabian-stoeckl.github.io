import unittest
from scripts.morgenzeitung_neu_learning import select

def item(letter,topic="KI",fit=3,novelty=3,access="full",event=None):
    return {"id":letter*16,"title":"Titel "+letter,"source":"Handelsblatt",
        "url":"https://example.org/"+letter,"topic":topic,"fit":fit,
        "novelty_score":novelty,"access":access,**({"event":event} if event else {})}

class SelectionTests(unittest.TestCase):
    def test_feedback_moves_order(self):
        pool=[item("a","KI"),item("b","Industrie")]
        base={"topics":{"KI":3,"Industrie":3}}
        self.assertEqual(select(pool,base)[0][0]["id"],"a"*16)
        learned={**base,"feedback_topic_deltas":{"KI":-2,"Industrie":2}}
        self.assertEqual(select(pool,learned)[0][0]["id"],"b"*16)
    def test_fulltext_does_not_change_rank(self):
        x=[item("a",access="full"),item("b","Industrie",access="metadata")]
        y=[dict(o,access="metadata" if o["access"]=="full" else "full") for o in x]
        self.assertEqual([o["id"] for o in select(x,{})[0]],[o["id"] for o in select(y,{})[0]])
    def test_duplicate_event(self):
        self.assertEqual(len(select([item("a",event="same"),item("b",event="same")],{})[0]),1)
    def test_weak_fit_cannot_be_solved_with_access(self):
        self.assertEqual(select([item("a",fit=5,access="teaser"),item("b",fit=1,access="full")],{})[0][0]["id"],"a"*16)
    def test_missing_metadata_skips(self):
        self.assertEqual(select([{"title":"x"}],{})[0],[])
if __name__=="__main__": unittest.main()
