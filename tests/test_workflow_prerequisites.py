"""Preserve existing acceptance triggers and clean-checkout prerequisites."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class WorkflowPrerequisites(unittest.TestCase):
    def test_existing_acceptance_still_runs_on_main_push(self) -> None:
        workflow = (ROOT / ".github/workflows/system-test.yml").read_text()
        self.assertRegex(workflow, r"(?m)^  push:\n    branches: \[main\]$")
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertIn("tools/acceptance_gate.py system-test", workflow)

    def test_every_validation_partition_initializes_pinned_submodules(self) -> None:
        workflow = (ROOT / ".github/workflows/validation.yml").read_text()
        checkouts = re.findall(
            r"(?ms)^      - uses: actions/checkout@[^\n]+\n(.*?)(?=^      -|\Z)",
            workflow,
        )
        self.assertEqual(len(checkouts), 8)
        for checkout in checkouts:
            self.assertIn("          submodules: recursive", checkout)
            self.assertIn("          persist-credentials: false", checkout)
