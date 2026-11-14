"""Synthetic oracle checks must survive optimization; no live lane is invoked."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "test_synthetic_oracle_accepts_complete_observations",
    "test_second_launch_and_offline_effect_are_detected",
    "test_binding_session_receipt_and_order_mutations_are_detected",
    "test_unknown_and_acknowledgement_cannot_be_terminal_success",
    "test_replay_cannot_create_external_effect",
)


class ScenarioOptimizationTests(unittest.TestCase):
    def test_positive_and_negative_oracles_in_both_interpreter_modes(self) -> None:
        for flags in ([], ["-O"]):
            with self.subTest(flags=flags):
                result = subprocess.run(
                    [
                        sys.executable,
                        *flags,
                        "-m",
                        "unittest",
                        *[
                            "test_core_temporal_scenario.ScenarioOracle." + name
                            for name in CASES
                        ],
                        "-v",
                    ],
                    cwd=ROOT,
                    env={
                        **os.environ,
                        "PYTHONPATH": str(ROOT / "tests") + os.pathsep + str(ROOT),
                    },
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Ran 5 tests", result.stderr)
                self.assertIn("OK", result.stderr)
                self.assertNotIn("skipped", result.stderr)


if __name__ == "__main__":
    unittest.main()
