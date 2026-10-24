import base64
import json
import unittest
import urllib.error
from scripts.morgenzeitung_feedback import write_profile_if_unchanged


def entry(value, sha):
    return {"sha": sha, "content": base64.b64encode(json.dumps(value).encode()).decode()}


class ProfileCASTests(unittest.TestCase):
    def test_successful_write_and_readback(self):
        original, updated = {"v": 1}, {"v": 2}
        state = [entry(original, "a")]
        def api(path, method="GET", body=None):
            if method == "PUT":
                self.assertEqual(body["sha"], "a")
                state[0] = entry(updated, "b")
            return state[0]
        self.assertTrue(write_profile_if_unchanged(api, "a", original, updated, True))

    def test_concurrent_change_rejected_without_write(self):
        calls = []
        def api(path, method="GET", body=None):
            calls.append(method)
            return entry({"v": 99}, "new")
        with self.assertRaisesRegex(RuntimeError, "concurrently"):
            write_profile_if_unchanged(api, "old", {"v": 1}, {"v": 2}, True)
        self.assertEqual(calls, ["GET"])

    def test_conflict_during_write_fails_closed(self):
        def api(path, method="GET", body=None):
            if method == "PUT":
                raise urllib.error.HTTPError("url", 409, "Conflict", {}, None)
            return entry({"v": 1}, "a")
        with self.assertRaisesRegex(RuntimeError, "conflict"):
            write_profile_if_unchanged(api, "a", {"v": 1}, {"v": 2}, True)

    def test_dry_run_never_writes(self):
        methods = []
        def api(path, method="GET", body=None):
            methods.append(method)
            return entry({"v": 1}, "a")
        self.assertFalse(write_profile_if_unchanged(api, "a", {"v": 1}, {"v": 2}, False))
        self.assertEqual(methods, ["GET"])


if __name__ == "__main__":
    unittest.main()
