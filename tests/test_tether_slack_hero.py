"""Pinned H01 Tether execution and source admission."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import tether_slack_hero as hero
from tools.browser_effect_hero import stage_source


class TetherSlackHeroTests(unittest.TestCase):
    def test_pinned_tether_reconciles_lost_ack_without_duplicate_delivery(self) -> None:
        report = hero.run()
        self.assertEqual(report["repeat_runs"], 2)
        for phase, initial in (("dispatch", "unknown"), ("crash_after", "interrupted")):
            with self.subTest(phase=phase):
                observed = report["observed"][phase]
                self.assertEqual(observed["revisions"], [1, 2])
                self.assertEqual(
                    observed["calls"], ["send", "readback", "readback", "readback"]
                )
                self.assertEqual(
                    observed["delivery"],
                    [initial, "unknown", "unknown", "destination_confirmed"],
                )
        self.assertEqual(report["mutations"], ["blind_resend"])
        self.assertGreater(report["mutant_provider_sends"], 1)
        self.assertEqual(report["system_aggregate"], "blocked")

    def test_wrong_source_digest_is_rejected_before_loading_tether(self) -> None:
        spec = json.loads(hero.MANIFEST.read_bytes())
        first = next(iter(spec["source_sha256"]))
        spec["source_sha256"][first] = "0" * 64
        with TemporaryDirectory() as directory:
            stage = Path(directory) / "source"
            with self.assertRaisesRegex(
                AssertionError, "Tether source digest mismatch"
            ):
                stage_source(stage, spec, component="tether")
            self.assertFalse(stage.exists())
