"""The candidate hero is mandatory even when optional local tests lack sources."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import hygiene

ROOT = Path(__file__).resolve().parents[1]


class FeedbackInventoryTests(unittest.TestCase):
    def test_hero_has_one_mandatory_partition_assignment(self) -> None:
        inventory = json.loads((ROOT / "hygiene.json").read_bytes())
        checks = [
            entry for entry in inventory["checks"] if entry["id"] == "feedback-hero"
        ]
        self.assertEqual(len(checks), 1)
        entry = checks[0]
        self.assertNotIn("not_applicable", entry)
        self.assertEqual(
            entry["command"],
            [
                "python3",
                "tools/feedback_hero.py",
                "--tether",
                "local/feedback-sources/tether",
                "--refinery",
                "local/feedback-sources/refinery",
            ],
        )
        partitions = json.loads((ROOT / "validation-partitions.json").read_bytes())[
            "partitions"
        ]
        self.assertEqual(
            [
                name
                for name, ids in partitions.items()
                for identity in ids
                if identity == "feedback-hero"
            ],
            ["component"],
        )

    def test_missing_candidate_sources_fail_before_child_execution(self) -> None:
        entry = next(
            entry
            for entry in json.loads((ROOT / "hygiene.json").read_bytes())["checks"]
            if entry["id"] == "feedback-hero"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in entry["required_files"]:
                if name.startswith("local/"):
                    continue
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic")
            with patch.object(subprocess, "Popen") as child:
                receipt = hygiene.run_entry(root, entry)
            child.assert_not_called()
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(receipt["reason"], "required_file_missing")

    def test_ci_prepares_exact_sources_for_component_and_quality(self) -> None:
        workflow = (ROOT / ".github/workflows/validation.yml").read_text()
        for job, following in (("quality", "component"), ("component", "rust")):
            section = workflow.split("  " + job + ":\n", 1)[1].split(
                "  " + following + ":\n", 1
            )[0]
            self.assertEqual(section.count("fetch-depth: 0"), 3)
            self.assertIn("ref: 670989839a0fccbcf2014d01609778ae6e4df424", section)
            self.assertIn("ref: b68ba9d77d51ca453b3f0fa3a9fa31573d065250", section)
            self.assertIn("RUNSPINDLE_FEEDBACK_HERO_TETHER:", section)
            self.assertIn("RUNSPINDLE_FEEDBACK_HERO_REFINERY:", section)
            self.assertIn("MYPYPATH:", section)
            self.assertNotIn("continue-on-error", section)
