"""Reject disabled, duplicated or bypassed source guards and preservation tests."""

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from tools import check_source_registration as audit

ROOT = Path(__file__).resolve().parents[1]


class SourceRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads((ROOT / "hygiene.json").read_text())
        self.partitions = json.loads((ROOT / "validation-partitions.json").read_text())

    def test_all_guards_registered_once(self) -> None:
        self.assertEqual(audit.check(ROOT)["mandatory_source_checks"], 5)

    def test_each_guard_is_mandatory(self) -> None:
        for identifier in audit.SOURCE_CHECKS:
            with self.subTest(identifier=identifier):
                inventory = copy.deepcopy(self.inventory)
                inventory["checks"] = [
                    item for item in inventory["checks"] if item["id"] != identifier
                ]
                with self.assertRaisesRegex(ValueError, "mandatory check identity"):
                    audit.validate(inventory, self.partitions)

    def test_commands_inputs_and_single_registration_are_exact(self) -> None:
        for identifier in audit.SOURCE_CHECKS:
            for mutation in ("command", "required_files", "duplicate", "optional"):
                with self.subTest(identifier=identifier, mutation=mutation):
                    inventory = copy.deepcopy(self.inventory)
                    selected: dict[str, Any] = next(
                        item for item in inventory["checks"] if item["id"] == identifier
                    )
                    if mutation == "duplicate":
                        inventory["checks"].append(copy.deepcopy(selected))
                    elif mutation == "optional":
                        selected["not_applicable"] = "synthetic bypass attempt"
                    else:
                        selected[mutation] = []
                    with self.assertRaisesRegex(ValueError, "mandatory check identity"):
                        audit.validate(inventory, self.partitions)

    def test_partition_assignment_cannot_disappear_move_or_duplicate(self) -> None:
        for identifier in audit.SOURCE_CHECKS:
            for mutation in ("remove", "move", "duplicate"):
                with self.subTest(identifier=identifier, mutation=mutation):
                    partitions = copy.deepcopy(self.partitions)
                    if mutation != "duplicate":
                        partitions["partitions"]["component"].remove(identifier)
                    if mutation != "remove":
                        partitions["partitions"]["quality"].append(identifier)
                    with self.assertRaisesRegex(ValueError, "component assignment"):
                        audit.validate(self.inventory, partitions)

    def test_every_preservation_module_is_required(self) -> None:
        for path in audit.PRESERVATION_TESTS:
            with self.subTest(path=path):
                inventory = copy.deepcopy(self.inventory)
                tests = next(
                    item for item in inventory["checks"] if item["id"] == "python-tests"
                )
                tests["required_files"].remove(path)
                with self.assertRaisesRegex(ValueError, "preservation tests"):
                    audit.validate(inventory, self.partitions)

    def test_focused_suite_cannot_replace_full_discovery(self) -> None:
        tests = next(
            item for item in self.inventory["checks"] if item["id"] == "python-tests"
        )
        tests["command"].extend(["-p", "test_source_registration.py"])
        with self.assertRaisesRegex(ValueError, "full test discovery"):
            audit.validate(self.inventory, self.partitions)


if __name__ == "__main__":
    unittest.main()
