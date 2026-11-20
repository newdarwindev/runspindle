import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import platform_telemetry_hero as hero
from tools.browser_effect_hero import stage_source


class PlatformTelemetryHeroTests(unittest.TestCase):
    def test_pinned_platform_restart_separates_delivery_from_persistence(self) -> None:
        receipt = hero.run()
        self.assertEqual(receipt["hero_acceptance"], "blocked")
        self.assertEqual(receipt["platform_lane"], "passed")
        self.assertEqual(receipt["repeat_runs"], 2)
        self.assertEqual(
            receipt["mutation_detected"], "match_event_id_without_bound_context"
        )
        observed = receipt["observed"]
        interrupted = observed["interrupted"]
        self.assertEqual((interrupted["queued"], interrupted["persisted"]), (4, 1))
        readback = observed["readback"]
        self.assertEqual(
            (readback["accepted"], readback["rejected"], readback["persisted"]),
            (3, 1, 1),
        )
        self.assertEqual(readback["usage_units"], 7)
        self.assertEqual(
            [event["duplicates"] for event in readback["events"]], [1, 0, 0, 0]
        )
        self.assertEqual(observed["privacy_negative"], "blocked")
        self.assertEqual(len(observed["calls"]), 9)

    def test_changed_platform_source_digest_blocks_staging(self) -> None:
        fixture = json.loads(hero.MANIFEST.read_bytes())
        first = next(iter(fixture["source_sha256"]))
        fixture["source_sha256"][first] = "0" * 64
        with TemporaryDirectory() as directory:
            stage = Path(directory) / "staged"
            with self.assertRaisesRegex(
                AssertionError, "Platform source digest mismatch"
            ):
                stage_source(stage, fixture, component="platform")
            self.assertFalse(stage.exists())
