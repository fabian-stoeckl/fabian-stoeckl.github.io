"""Private source-health records are append-only, read-back verified and non-fabricated."""
import json
import unittest
import urllib.error

from scripts.morgenzeitung_official_feeds import FEEDS
from scripts.morgenzeitung_source_health import REQUIRED_SOURCES
from scripts.morgenzeitung_source_health_archive import archive_feed_smoke, archive_review, archive_editorial


class PrivateMock:
    def __init__(self):
        self.files = {}
    def put_immutable(self, path, data):
        if path in self.files and self.files[path] != data:
            raise ValueError("Conflicting immutable private snapshot")
        self.files[path] = data
    def read(self, path):
        item = self.files.get(path)
        return (item, "a"*40) if item is not None else None
    def api(self, path):
        if not path.startswith("/contents/"):
            raise ValueError("Unexpected API")
        prefix=path[len("/contents/"):].rstrip("/")+"/"
        matches = [
            {"type":"file","name":p[len(prefix):],"path":p}
            for p in self.files if p.startswith(prefix) and "/" not in p[len(prefix):]
        ]
        if not matches:
            raise urllib.error.HTTPError(path,404,"not found",{},None)
        return matches


def smoke():
    return {"report_type": "real_publisher_first_party_feed_smoke",
            "results": [
                {"publisher": name,"status":"FEED_READABLE",
                 "identity_status":"LIVE_IDENTITY_MATCH", "items":3,
                 "working_feed":feeds[0][0]}
                for name,feeds in FEEDS.items()]}


def editorial(day, all_blocked=False):
    return {
        "report_type":"source_editorial_research",
        "date":day, "research_complete":True,
        "publishers":[{
            "publisher":name,
            "outcome":"NO_VERIFIABLE_ARTICLES" if all_blocked and name=="NZZ" else "VERIFIED_ARTICLES",
            "verified_original_count":0 if all_blocked and name=="NZZ" else 1,
            "attempted_methods":["direct_original","official_publisher_feed"],
            "attempt_evidence":["Original 403 / source hash","Publisher original feed no match"],
        } for name in REQUIRED_SOURCES]
    }


class ArchiveTests(unittest.TestCase):
    def test_live_feed_archived_privately_and_verified_again(self):
        repo=PrivateMock()
        out=archive_feed_smoke(smoke(),"2026-10-27","40500000001",repo=repo)
        self.assertTrue(out["readback"])
        self.assertIn("source-health/feeds/2026-10-27/run-40500000001.json",repo.files)
        raw=repo.files[out["path"]]
        saved=json.loads(raw)
        self.assertEqual(saved["feed_adapters"],len(FEEDS))
        self.assertEqual(saved["publisher_count"],len(REQUIRED_SOURCES))
        self.assertEqual(saved["live_identity_sample_confirmed"],len(FEEDS))
        self.assertNotIn("token",raw.decode().lower())
        self.assertEqual(archive_feed_smoke(smoke(),"2026-10-27","40500000001",repo=repo)["path"],out["path"])

    def test_different_payload_cannot_overwrite_immutable_daily_run(self):
        repo=PrivateMock()
        archive_feed_smoke(smoke(),"2026-10-27","40500000001",repo=repo)
        next_smoke=smoke()
        next_smoke["results"][0]["status"]="ACCESS_BLOCKED"
        with self.assertRaisesRegex(ValueError,"Conflicting immutable"):
            archive_feed_smoke(next_smoke,"2026-10-27","40500000001",repo=repo)
        # A new retry is still permitted at its own unique path.
        out=archive_feed_smoke(next_smoke,"2026-10-27","40500000002",repo=repo)
        self.assertIn("run-40500000002",out["path"])

    def test_missing_editorial_history_is_reported_as_gap(self):
        repo=PrivateMock()
        r=archive_review("2026-10-27","40500000001",repo=repo)
        self.assertEqual(r["verdict"],"AUDIT_GAP")
        self.assertEqual(len(r["missing_editorial_dates"]),3)
        self.assertEqual(r["missing_dates"], r["missing_editorial_dates"])
        self.assertFalse(r["confirmed_blackouts"])
        self.assertTrue(r["readback"])

    def test_latest_daily_editorial_research_replaces_no_historical_version(self):
        repo=PrivateMock()
        for day in ("2026-10-25","2026-10-26","2026-10-27"):
            old=editorial(day,all_blocked=False)
            new=editorial(day,all_blocked=True)
            repo.put_immutable("source-health/editorial/"+day+"/run-400.json",json.dumps(old).encode())
            repo.put_immutable("source-health/editorial/"+day+"/run-401.json",json.dumps(new).encode())
        r=archive_review("2026-10-27","40500000001",repo=repo)
        self.assertEqual(r["verdict"],"ACCESS_GAPS")
        self.assertEqual(r["confirmed_blackouts"],["NZZ"])
        self.assertTrue(r["readback"])

    def test_completed_real_editorial_ledger_archived_privately_with_readback(self):
        repo=PrivateMock()
        record=editorial("2026-10-27",all_blocked=True)
        saved=archive_editorial(record,"2026-10-27","40500000011",repo=repo)
        self.assertTrue(saved["research_complete"])
        self.assertTrue(saved["readback"])
        self.assertEqual(saved["publishers"],len(REQUIRED_SOURCES))
        self.assertEqual(json.loads(repo.files[saved["path"]]),record)
        self.assertEqual(archive_editorial(record,"2026-10-27","40500000011",repo=repo)["path"],saved["path"])
        changed=editorial("2026-10-27",all_blocked=False)
        with self.assertRaisesRegex(ValueError,"Conflicting immutable"):
            archive_editorial(changed,"2026-10-27","40500000011",repo=repo)
        newer=archive_editorial(changed,"2026-10-27","40500000012",repo=repo)
        self.assertNotEqual(newer["path"],saved["path"])

    def test_incomplete_or_unverified_ledger_cannot_be_saved(self):
        repo=PrivateMock()
        incomplete=editorial("2026-10-27")
        incomplete["publishers"]=incomplete["publishers"][:-1]
        with self.assertRaisesRegex(ValueError,"Missing mandatory"):
            archive_editorial(incomplete,"2026-10-27","40500000013",repo=repo)
        fake=editorial("2026-10-27",all_blocked=True)
        fake["publishers"][0]["outcome"]="NOT_CHECKED"
        with self.assertRaisesRegex(ValueError,"unexamined"):
            archive_editorial(fake,"2026-10-27","40500000013",repo=repo)
        valid=editorial("2026-10-27")
        with self.assertRaisesRegex(ValueError,"date"):
            archive_editorial(valid,"2026-10-26","40500000013",repo=repo)
        self.assertEqual(repo.files,{})

    def test_run_ids_validated_against_path_traversal(self):
        repo=PrivateMock()
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            archive_feed_smoke(smoke(),"2026-10-27","../private",repo=repo)


if __name__=="__main__":
    unittest.main()
