import json
import unittest

from tools import console_freshness_hero as hero


class ConsoleFreshnessHeroTests(unittest.TestCase):
    def test_pinned_projection_tracks_task_and_passive_lifetime(self) -> None:
        receipt = hero.run()
        self.assertEqual(receipt["console_lane"], "passed")
        self.assertEqual(receipt["repeat_runs"], 2)
        self.assertEqual(
            receipt["observations"],
            {
                "reads": 7,
                "closed": ["pending", "offline"],
                "control_requests": 0,
                "current_after_reconnect": "task-b",
                "passive_calls": 2,
                "stale_after_expiry": True,
            },
        )
        self.assertEqual(len(receipt["mutations_detected"]), 2)
        self.assertEqual(receipt["live_stream_and_full_system"], "blocked")

    def test_console_source_digest_drift_is_rejected(self) -> None:
        fixture = json.loads(hero.MANIFEST.read_bytes())
        fixture["projection_sha256"] = "0" * 64
        with self.assertRaisesRegex(AssertionError, "Console source digest mismatch"):
            hero.pinned_projection(fixture)
