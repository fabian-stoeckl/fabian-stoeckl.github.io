"""Private snapshot: replay actual selection, never fabricate quality outcomes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.morgenzeitung_v3_audit import before_snapshot, learning_result, private_target


def candidate(n, topic):
    return {"id":f"{n:016x}","title":"Report "+str(n),"source":"Reporter",
            "url":"https://example.org/"+str(n),"topic":topic,
            "fit":4,"novelty":3,"impact":4,"perspective":3}


class LearningSnapshotTests(unittest.TestCase):
    def test_frozen_pool_is_replayed_without_inference(self):
        rows={"articles":[candidate(1,"Industrie"),candidate(2,"Klima")],"headlines":[]}
        before={"topic_priorities":{"Industrie":4,"Klima":4}}
        after={"topic_priorities":{"Industrie":4,"Klima":4},
               "feedback_topic_deltas":{"Industrie":-2,"Klima":2}}
        frozen=before_snapshot(rows,before,"2026-10-28")
        after_report=learning_result(frozen,after)
        self.assertTrue(after_report["comparison"]["Vertiefungen"]["selection_changed"])
        self.assertFalse(after_report["feedback_quality_improvement_proven"])
        self.assertEqual(after_report["snapshot_sha256"],frozen["snapshot_sha256"])
        changed=copy.deepcopy(frozen)
        changed["original_candidates"]["articles"][0]["fit"]=0
        with self.assertRaisesRegex(ValueError,"snapshot has changed"):
            learning_result(changed,after)

    def test_private_repo_directory_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            with self.assertRaisesRegex(ValueError,"private"):
                private_target(home,"morgenzeitung-v3/snapshots/test.json")
            (home/".git").mkdir()
            (home/".git/config").write_text('[remote "origin"]\n url = https://github.com/fabian-stoeckl/morgenzeitung-feedback.git\n')
            target=private_target(home,"morgenzeitung-v3/snapshots/test.json")
            self.assertTrue(target.is_relative_to(home))
            with self.assertRaisesRegex(ValueError,"private"):
                private_target(home,"../../Public/issue.json")


if __name__=="__main__":
    unittest.main()
