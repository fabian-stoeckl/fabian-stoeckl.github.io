import unittest
from scripts.morgenzeitung_feedback import retry_feedback_ingestion


class FeedbackFullRetryTests(unittest.TestCase):
    def test_recomputes_after_concurrent_profile_update(self):
        observations = []
        def run():
            observations.append(len(observations) + 1)
            if len(observations) == 1:
                raise RuntimeError("Private profile changed concurrently; rerun feedback ingestion")
            return {"ratings": 2, "from_attempt": len(observations)}
        self.assertEqual(retry_feedback_ingestion(run), {"ratings": 2, "from_attempt": 2})
        self.assertEqual(observations, [1, 2])

    def test_write_conflict_retries_but_only_bounded(self):
        calls = []
        def run():
            calls.append(True)
            raise RuntimeError("Concurrent profile write conflict; rerun feedback ingestion")
        with self.assertRaisesRegex(RuntimeError, "exhausted conflict retries"):
            retry_feedback_ingestion(run, attempts=3)
        self.assertEqual(len(calls), 3)

    def test_unrelated_failures_do_not_retry(self):
        calls = []
        def run():
            calls.append(True)
            raise RuntimeError("Private profile readback mismatch")
        with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
            retry_feedback_ingestion(run)
        self.assertEqual(len(calls), 1)

    def test_zero_attempts_rejected(self):
        with self.assertRaises(ValueError):
            retry_feedback_ingestion(lambda: None, attempts=0)


if __name__ == "__main__":
    unittest.main()
