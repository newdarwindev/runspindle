"""SRC-005 consistency and fail-closed scope checks with synthetic mutations."""

import json
import shutil
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.check_economics_source import check

ROOT = Path(__file__).resolve().parents[1]


class EconomicsSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "docs/marketing", self.root / "docs/marketing")
        shutil.copyfile(ROOT / "provenance.json", self.root / "provenance.json")

    def mutate(self, fn: Callable[[dict[str, Any]], None]) -> None:
        path = self.root / "docs/marketing/SRC-005-disposition.json"
        data = json.loads(path.read_text())
        fn(data)
        path.write_text(json.dumps(data))

    def test_current_documents_and_scope_agree(self) -> None:
        self.assertEqual(check(self.root)["status"], "passed")

    def test_each_published_narrative_cannot_drift(self) -> None:
        for name in ("economics.md", "runspindle-paper.tex", "overview.md"):
            with self.subTest(name=name):
                path = self.root / "docs/marketing" / name
                original = path.read_text()
                path.write_text(original.replace("U = C / A", "U = C / attempts"))
                with self.assertRaisesRegex(ValueError, "drift"):
                    check(self.root)
                path.write_text(original)

    def test_wrong_note_source_id_rejected(self) -> None:
        path = self.root / "docs/marketing/economics.md"
        path.write_text(
            path.read_text().replace(
                "Source concept: SRC-005", "Source concept: SRC-002"
            )
        )
        with self.assertRaisesRegex(ValueError, "note drift"):
            check(self.root)

    def test_missing_paragraph_equation_diagram_or_citation_rejected(self) -> None:
        path = self.root / "docs/marketing/SRC-005-disposition.json"
        original = path.read_text()
        for unit in ("P01", "P06", "E01", "D01", "D02", "C03"):
            with self.subTest(unit=unit):
                self.mutate(
                    lambda d: d.update(units=[u for u in d["units"] if u["id"] != unit])
                )
                with self.assertRaisesRegex(ValueError, "disposition"):
                    check(self.root)
                path.write_text(original)

    def test_duplicate_disposition_rejected(self) -> None:
        self.mutate(lambda d: d["units"].append(d["units"][0]))
        with self.assertRaisesRegex(ValueError, "disposition"):
            check(self.root)

    def test_unlicensed_diagram_cannot_be_declared_imported(self) -> None:
        self.mutate(
            lambda d: next(u for u in d["units"] if u["id"] == "D01").update(
                source_expression_copied=True
            )
        )
        with self.assertRaisesRegex(ValueError, "expression"):
            check(self.root)

    def test_migration_and_measurement_cannot_be_promoted(self) -> None:
        path = self.root / "docs/marketing/SRC-005-disposition.json"
        original = path.read_text()
        for field, value in (
            ("migration_status", "complete"),
            ("verified_behavior", "measured_savings"),
        ):
            with self.subTest(field=field):
                self.mutate(lambda d: d.update({field: value}))
                with self.assertRaises(ValueError):
                    check(self.root)
                path.write_text(original)

    def test_unreviewed_citation_destination_rejected(self) -> None:
        self.mutate(lambda d: d["citations"][0].update(url="https://example.invalid"))
        with self.assertRaisesRegex(ValueError, "citation closure"):
            check(self.root)

    def test_stale_result_hash_rejected(self) -> None:
        self.mutate(
            lambda d: d["result_files"].update(
                {"docs/marketing/economics.md": "0" * 64}
            )
        )
        with self.assertRaisesRegex(ValueError, "result hash"):
            check(self.root)

    def test_artifact_source_association_rejected(self) -> None:
        path = self.root / "docs/marketing/artifacts.json"
        data = json.loads(path.read_text())
        next(
            a for a in data["artifacts"] if a["path"] == "docs/marketing/economics.md"
        )["source_ids"] = ["SRC-002"]
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "artifact association"):
            check(self.root)


if __name__ == "__main__":
    unittest.main()
