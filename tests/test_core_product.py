"""Negative artifact checks; these tests never exercise a runtime provider."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools import check_core_product as audit

ROOT = Path(__file__).resolve().parents[1]


class CoreProductCoverage(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = audit.document(ROOT, audit.COVERAGE)
        names = audit.FILES | {
            audit.MANIFEST,
            "STATUS.json",
            "provenance.json",
            "composition.lock.json",
            "AGENTS.md",
        }
        names |= {target for row in self.data["records"] for target in row["targets"]}
        for name in names:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def save(self, name: str, value: dict[str, Any]) -> None:
        (self.root / name).write_text(json.dumps(value, indent=2) + "\n")

    def refresh(self, data: dict[str, Any] | None = None) -> None:
        if data is not None:
            self.save(audit.COVERAGE, data)
            (self.root / "specs/system.md").write_text(audit.render_system(data))
        manifest = audit.document(self.root, audit.MANIFEST)
        manifest["file_sha256"] = {
            name: audit.digest(self.root / name) for name in audit.FILES
        }
        manifest["provenance_record_sha256"] = audit.provenance_digest(self.root)
        self.save(audit.MANIFEST, manifest)

    def unit(self, data: dict[str, Any], unit: str) -> dict[str, Any]:
        return next(
            audit.mapping(value, "record")
            for value in data["records"]
            if value["id"] == unit
        )

    def test_complete_inventory_with_unchanged_runtime_claims(self) -> None:
        receipt = audit.validate(self.root)
        self.assertEqual(receipt["source_units"], 46)
        self.assertEqual(receipt["resolved_navigation_exclusions"], 6)
        self.assertEqual(receipt["runtime_acceptance"], "not_run")
        self.assertEqual(
            len([r for r in self.data["records"] if r["id"].startswith("P")]), 10
        )

    def test_each_source_unit_is_required_even_after_rehash(self) -> None:
        for unit in audit.REQUIRED_OBLIGATIONS:
            with self.subTest(unit=unit):
                altered = copy.deepcopy(self.data)
                altered["records"] = [r for r in altered["records"] if r["id"] != unit]
                self.refresh(altered)
                with self.assertRaisesRegex(audit.CoverageError, "source unit"):
                    audit.validate(self.root)

    def test_duplicate_and_misclassified_units_fail(self) -> None:
        for change in ("duplicate", "section", "swapped_sections", "disposition"):
            with self.subTest(change=change):
                altered = copy.deepcopy(self.data)
                if change == "duplicate":
                    altered["records"].append(copy.deepcopy(altered["records"][0]))
                elif change == "section":
                    altered["records"][0]["source_section"] = "boundary"
                elif change == "swapped_sections":
                    altered["records"][0]["source_section"] = "boundary"
                    altered["records"][1]["source_section"] = "scope"
                else:
                    self.unit(altered, "X06")["disposition"] = "adapted"
                self.refresh(altered)
                with self.assertRaises(audit.CoverageError):
                    audit.validate(self.root)

    def test_every_obligation_is_required(self) -> None:
        for unit, obligations in audit.REQUIRED_OBLIGATIONS.items():
            for obligation in obligations:
                with self.subTest(unit=unit, obligation=obligation):
                    altered = copy.deepcopy(self.data)
                    del self.unit(altered, unit)["obligations"][obligation]
                    self.refresh(altered)
                    with self.assertRaisesRegex(audit.CoverageError, "obligations"):
                        audit.validate(self.root)

    def test_changed_owner_target_or_missing_text_fails(self) -> None:
        cases: list[tuple[str, object]] = [
            ("owners", ["refinery"]),
            ("targets", ["specs/system.md"]),
            ("reason", ""),
            ("title", ""),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                altered = copy.deepcopy(self.data)
                self.unit(altered, "P01")[field] = value
                self.refresh(altered)
                with self.assertRaises(audit.CoverageError):
                    audit.validate(self.root)
        altered = copy.deepcopy(self.data)
        self.unit(altered, "P01")["obligations"]["scope"] = ""
        self.save(audit.COVERAGE, altered)
        self.refresh()
        with self.assertRaisesRegex(audit.CoverageError, "nonempty"):
            audit.validate(self.root)

    def test_all_full_slice_gates_fail_closed(self) -> None:
        changes = {
            "full_slice_status": "passed",
            "evidence_class": "live_acceptance",
            "composition_issue": "https://github.com/newdarwindev/runspindle/issues/3",
            "existing_lane": "invented_lane",
            "requirements": ["P01"],
            "related_evidence": "Historical tests qualify every newer source revision.",
        }
        for unit in audit.GATE_LANES:
            for field, value in changes.items():
                with self.subTest(unit=unit, field=field):
                    altered = copy.deepcopy(self.data)
                    self.unit(altered, unit)["gate"][field] = value
                    self.refresh(altered)
                    with self.assertRaises(audit.CoverageError):
                        audit.validate(self.root)

    def test_source_import_and_implementation_claims_cannot_be_rehashed(self) -> None:
        for field, value in {
            "source_expression_imported": True,
            "executable_implementation": "complete",
            "verified_runtime_behavior": "passed",
            "historical_source": "original_hash_replaced",
            "rights": "Blanket relicense granted",
        }.items():
            with self.subTest(field=field):
                altered = copy.deepcopy(self.data)
                altered[field] = value
                self.refresh(altered)
                with self.assertRaises(audit.CoverageError):
                    audit.validate(self.root)

    def test_hash_inventory_and_rendering_are_exact(self) -> None:
        path = self.root / "specs/system.md"
        path.write_text(path.read_text() + "\nChanged artifact.\n")
        with self.assertRaisesRegex(audit.CoverageError, "disagree"):
            audit.validate(self.root)
        self.refresh(self.data)
        path = self.root / audit.README
        path.write_text(path.read_text() + "\nChanged artifact.\n")
        with self.assertRaisesRegex(audit.CoverageError, "hash mismatch"):
            audit.validate(self.root)
        self.refresh()
        manifest = audit.document(self.root, audit.MANIFEST)
        del manifest["file_sha256"][audit.README]
        self.save(audit.MANIFEST, manifest)
        with self.assertRaisesRegex(audit.CoverageError, "file inventory"):
            audit.validate(self.root)

    def test_pinned_component_specs_cannot_silently_change_or_disappear(self) -> None:
        target = next(iter(self.data["component_spec_hashes"]))
        path = self.root / target
        path.write_text(path.read_text() + "\nDrift.\n")
        with self.assertRaisesRegex(audit.CoverageError, "component spec drift"):
            audit.validate(self.root)
        path.unlink()
        with self.assertRaisesRegex(audit.CoverageError, "missing regular file"):
            audit.validate(self.root)

    def test_global_and_artifact_statuses_remain_separate(self) -> None:
        for field, value in {
            "selected_source_migration": "complete",
            "implementation": "implemented",
            "live_acceptance": "passed",
        }.items():
            with self.subTest(field=field):
                status = audit.document(ROOT, "STATUS.json")
                status[field] = value
                self.save("STATUS.json", status)
                with self.assertRaises(audit.CoverageError):
                    audit.validate(self.root)
        self.save("STATUS.json", audit.document(ROOT, "STATUS.json"))
        source = audit.document(self.root, "provenance.json")
        source["sources"][0]["migration_status"] = "complete"
        self.save("provenance.json", source)
        self.refresh()
        with self.assertRaisesRegex(audit.CoverageError, "migration scope"):
            audit.validate(self.root)

    def test_public_privacy_guards_survive_hash_refresh(self) -> None:
        examples = [
            "/workspace/private-input/source.md",
            "/home/example/profile",
            "https://github.com/example/private-source/blob/main/README.md",
            "xoxb-" + "s" * 24,
            "-----BEGIN PRIVATE KEY-----",
        ]
        original = (self.root / audit.README).read_text()
        for example in examples:
            with self.subTest(example=example[:20]):
                (self.root / audit.README).write_text(original + "\n" + example)
                self.refresh()
                with self.assertRaises(audit.CoverageError):
                    audit.validate(self.root)

    def test_missing_mandatory_aggregate_registration_fails_after_rehash(self) -> None:
        manifest = audit.document(self.root, "hygiene.json")
        manifest["checks"] = [
            row for row in manifest["checks"] if row["id"] != "check-core-product"
        ]
        self.save("hygiene.json", manifest)
        self.refresh()
        with self.assertRaisesRegex(audit.CoverageError, "mandatory"):
            audit.validate(self.root)

    def test_artifact_checker_must_have_exact_command_and_partition(self) -> None:
        for mutation in (
            "command",
            "not_applicable",
            "missing_partition",
            "duplicate_partition",
        ):
            with self.subTest(mutation=mutation):
                checks = audit.document(ROOT, "hygiene.json")
                partitions = audit.document(ROOT, "validation-partitions.json")
                entry = next(
                    row for row in checks["checks"] if row["id"] == "check-core-product"
                )
                if mutation == "command":
                    entry["command"] = ["python3", "-c", "pass"]
                elif mutation == "not_applicable":
                    entry.clear()
                    entry.update(
                        id="check-core-product", not_applicable="Skipped artifact"
                    )
                elif mutation == "missing_partition":
                    partitions["partitions"]["component"].remove("check-core-product")
                else:
                    partitions["partitions"]["quality"].append("check-core-product")
                self.save("hygiene.json", checks)
                self.save("validation-partitions.json", partitions)
                self.refresh()
                with self.assertRaisesRegex(audit.CoverageError, "mandatory"):
                    audit.validate(self.root)

    def test_historical_manifest_cannot_be_rehashed_as_current_evidence(self) -> None:
        path = self.root / audit.HISTORICAL_MANIFEST
        path.write_text(path.read_text() + "\n")
        self.refresh()
        with self.assertRaisesRegex(audit.CoverageError, "historical original hash"):
            audit.validate(self.root)
        shutil.copyfile(ROOT / audit.HISTORICAL_MANIFEST, path)
        self.refresh()
        manifest = audit.document(self.root, audit.MANIFEST)
        manifest["historical_original"]["result_transfer"] = True
        self.save(audit.MANIFEST, manifest)
        with self.assertRaisesRegex(
            audit.CoverageError, "historical original identity"
        ):
            audit.validate(self.root)

    def test_target_path_cannot_escape_or_be_symlinked(self) -> None:
        for target in ("../outside", "/tmp/outside"):
            with self.assertRaisesRegex(audit.CoverageError, "unsafe target"):
                audit.safe_file(self.root, target)
        path = self.root / audit.README
        path.unlink()
        path.symlink_to(ROOT / audit.README)
        with self.assertRaisesRegex(audit.CoverageError, "missing regular file"):
            audit.validate(self.root)

    def test_optimized_interpreter_enforces_semantic_not_just_hash_guards(self) -> None:
        altered = copy.deepcopy(self.data)
        self.unit(altered, "G04")["gate"]["full_slice_status"] = "passed"
        self.refresh(altered)
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                "-c",
                "from pathlib import Path; "
                "from tools.check_core_product import validate; validate(Path('.'))",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("full-slice claim", result.stderr)

    def test_malformed_document_shapes_fail(self) -> None:
        mutations: list[Callable[[dict[str, Any]], None]] = [
            lambda d: d.update(records=None),
            lambda d: d.update(component_spec_hashes=[]),
            lambda d: d.update(component_pins={}),
        ]
        for mutate in mutations:
            altered = copy.deepcopy(self.data)
            mutate(altered)
            self.save(audit.COVERAGE, altered)
            self.refresh()
            with self.assertRaises(audit.CoverageError):
                audit.validate(self.root)


if __name__ == "__main__":
    unittest.main()
