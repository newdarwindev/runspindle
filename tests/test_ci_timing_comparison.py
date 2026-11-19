"""Synthetic Actions job receipts, never real logs."""

import copy
import unittest

from tools.compare_ci_timings import CHECKOUT, compare


def receipt(state, run, checkout_end):
    def interval(start, end):
        return {
            "started_at": f"2026-11-19T12:00:{start:02}Z",
            "completed_at": f"2026-11-19T12:00:{end:02}Z",
            "status": "completed",
            "conclusion": "success",
        }

    return {
        "repository": "newdarwindev/runspindle",
        "runner_recipe_sha256": "e" * 64,
        "cache_state": state,
        "job": {
            **interval(0, checkout_end + 11),
            "id": run + 10,
            "run_id": run,
            "head_sha": "b" * 40,
            "name": "validation / component",
            "steps": [
                {"name": CHECKOUT, **interval(1, checkout_end)},
                {"name": "Run component partition", **interval(checkout_end, checkout_end + 10)},
                {"name": "raw text must never be included", **interval(0, 1)},
            ],
        },
    }


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.cold = receipt("cold", 100, 8)
        self.warm = receipt("warm", 200, 5)

    def test_separates_checkout_from_validation(self):
        result = compare(self.cold, self.warm)
        self.assertEqual(result["job"]["observed_delta_seconds"], 3)
        self.assertEqual(result["phases"]["checkout"]["cold_seconds"], 7)
        self.assertEqual(result["phases"]["component"]["observed_delta_seconds"], 0)
        self.assertNotIn("raw text", str(result))

    def test_fail_closed(self):
        for key, value in (
            ("run_id", 100),
            ("id", 110),
            ("head_sha", "c" * 40),
            ("name", "validation / rust"),
            ("status", "queued"),
            ("conclusion", "cancelled"),
            ("completed_at", "2026-11-19T12:00:00Z"),
        ):
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.warm)
                invalid["job"][key] = value
                with self.assertRaises(ValueError):
                    compare(self.cold, invalid)

    def test_rejects_missing_duplicate_and_changed_phases(self):
        for bad in ([], [self.warm["job"]["steps"][0]] * 2, self.warm["job"]["steps"][:1]):
            with self.subTest(bad=bad):
                invalid = copy.deepcopy(self.warm)
                invalid["job"]["steps"] = bad
                with self.assertRaises(ValueError):
                    compare(self.cold, invalid)

    def test_does_not_clamp_regression(self):
        result = compare(self.cold, receipt("warm", 200, 9))
        self.assertEqual(result["job"]["observed_delta_seconds"], -1)


if __name__ == "__main__":
    unittest.main()
