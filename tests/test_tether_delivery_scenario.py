"""Composition report gates for the opt-in Core/Tether integration cases."""

import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import tether_delivery_scenario as scenario  # noqa: E402


class DeliveryQualification(unittest.TestCase):
    def setUp(self):
        self.rust = "".join(f"test {case} ... ok\n" for case in scenario.CASES)
        self.python = (
            f"{scenario.MUTATION_CASE} (fixture.ExpectedBinding.test) ... ok\n"
        )

    def test_requires_every_exact_case_and_the_binding_mutations(self):
        result = scenario.observations(self.rust, self.python)
        self.assertEqual(result["durable_cases"], list(scenario.CASES))
        self.assertEqual(result["expected_binding_mutations"], scenario.MUTATION_CASE)

    def test_missing_ignored_and_duplicate_cases_fail(self):
        first = self.rust.splitlines(keepends=True)[0]
        for report in (
            "",
            self.rust.removeprefix(first),
            self.rust.replace(first, first.replace("ok", "ignored")),
            self.rust + first,
        ):
            with (
                self.subTest(report=report),
                self.assertRaisesRegex(RuntimeError, "missing, skipped or repeated"),
            ):
                scenario.observations(report, self.python)

    def test_skipped_mutation_gate_fails(self):
        with self.assertRaisesRegex(RuntimeError, "mutations did not run"):
            scenario.observations(self.rust, self.python.replace("ok", "skipped"))

    def test_dirty_composition_is_blocked_before_component_load(self):
        with (
            patch.object(scenario, "git", return_value=" M composition.lock.json"),
            patch.object(scenario, "inventory") as inventory,
            self.assertRaisesRegex(scenario.Blocked, "committed tree"),
        ):
            scenario.source_inventory(pathlib.Path("."), pathlib.Path("../core"))
        inventory.assert_not_called()
