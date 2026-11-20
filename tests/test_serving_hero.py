import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import serving_hero as hero


class ServingHeroTests(unittest.TestCase):
    def test_pinned_refinery_serving_recovers_and_rolls_back(self) -> None:
        result = hero.run()
        self.assertEqual(result["refinery_lane"], "passed")
        self.assertEqual(result["provider"], "scripted")
        self.assertEqual(result["repeat_runs"], 2)
        self.assertEqual(result["dspy"], "not_run")
        self.assertEqual(result["full_system"], "blocked")
        self.assertEqual(result["mutations_detected"], ["false_acknowledgement"])
        observed = result["observed"]
        self.assertEqual(
            observed["load_order"], ["candidate-0", "candidate-1", "rollback"]
        )
        self.assertEqual(
            (observed["heldout_cases"], observed["global_budget_attempts"]), (2, 8)
        )
        self.assertEqual(observed["forged_approval_loads"], 0)
        self.assertEqual(observed["rejected_rollback_loads"], 0)
        self.assertEqual(observed["historical"]["output"], "second")
        self.assertEqual(observed["rollback"]["output"], "first")
        self.assertNotEqual(
            observed["historical"]["candidate_sha256"],
            observed["rollback"]["candidate_sha256"],
        )

    def test_wrong_pinned_source_tree_is_rejected_before_extraction(self) -> None:
        spec = json.loads(hero.MANIFEST.read_bytes())
        spec["refinery_tree"] = "0" * 40
        with TemporaryDirectory() as temporary:
            destination = Path(temporary) / "source"
            with self.assertRaisesRegex(
                AssertionError, "Refinery source tree mismatch"
            ):
                hero.stage_source(destination, spec)
            self.assertFalse(destination.exists())
