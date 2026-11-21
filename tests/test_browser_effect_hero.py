import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import browser_effect_hero as hero


class BrowserEffectHeroTests(unittest.TestCase):
    def test_pinned_browser_recovers_without_duplicate_site_effects(self) -> None:
        receipt = hero.run()
        self.assertEqual(receipt["browser_lane"], "passed")
        self.assertEqual(receipt["repeat_runs"], 2)
        self.assertEqual(
            [
                (case["fault"], case["effects"], case["outcome"])
                for case in receipt["cases"]
            ],
            [
                ("lost", 1, "confirmed"),
                ("crash_before", 0, "unknown"),
                ("crash_after", 1, "confirmed"),
            ],
        )
        self.assertEqual(
            receipt["cases"][0]["readback_faults"],
            [
                {"mode": "readback_timeout", "exit_code": 0, "result": "unknown"},
                {"mode": "readback_wrong_digest", "exit_code": 0, "result": "unknown"},
                {
                    "mode": "readback_wrong_revision",
                    "exit_code": 0,
                    "result": "unknown",
                },
                {"mode": "readback_revoked", "exit_code": 0, "result": "denied"},
                {"mode": "readback_crash", "exit_code": 19, "result": "interrupted"},
            ],
        )
        self.assertEqual(
            receipt["cases"][0]["calls"],
            [
                "submit",
                "readback_timeout",
                "readback_wrong_digest",
                "readback_wrong_revision",
                "readback_revoked",
                "readback_crash",
                "readback",
            ],
        )
        self.assertEqual(
            receipt["mutations_detected"],
            ["duplicate_submit", "stale_observation", "readback_digest"],
        )
        self.assertEqual(receipt["core_native_live_and_full_system"], "blocked")

    def test_wrong_source_hash_rejects_before_staging(self) -> None:
        fixture = json.loads(hero.MANIFEST.read_bytes())
        first = next(iter(fixture["source_sha256"]))
        fixture["source_sha256"][first] = "0" * 64
        with TemporaryDirectory() as directory:
            stage = Path(directory) / "staged"
            with self.assertRaisesRegex(
                AssertionError, "Browser source digest mismatch"
            ):
                hero.stage_source(stage, fixture)
            self.assertFalse(stage.exists())
