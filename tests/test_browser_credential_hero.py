import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools import browser_credential_hero as hero
from tools.browser_effect_hero import stage_source


class BrowserCredentialHeroTests(unittest.TestCase):
    def test_pinned_resolver_and_vault_enforce_scope(self) -> None:
        receipt = hero.run()
        self.assertEqual(receipt["hero_acceptance"], "blocked")
        self.assertEqual(receipt["browser_lane"], "passed")
        self.assertEqual(receipt["repeat_runs"], 2)
        self.assertEqual(receipt["mutation_detected"], "ignore_observation_age")
        self.assertEqual(
            receipt["case_results"],
            [
                {"fault": mode, "outcome": outcome, "effects": effects}
                for mode, (outcome, effects) in hero.CASES.items()
            ],
        )
        scope = receipt["scope"]
        if not isinstance(scope, dict):
            self.fail("scope receipt must be a mapping")
        self.assertEqual(scope["joint_integration"], "blocked")
        self.assertEqual(scope["live"], "not_run")

    def test_changed_browser_pin_is_rejected_before_staging(self) -> None:
        fixture = json.loads(hero.MANIFEST.read_bytes())
        fixture["browser_commit"] = "0" * 40
        with TemporaryDirectory() as directory:
            stage = Path(directory) / "staged"
            with self.assertRaisesRegex(
                AssertionError, "scenario Browser pin mismatch"
            ):
                stage_source(stage, fixture)
            self.assertFalse(stage.exists())
