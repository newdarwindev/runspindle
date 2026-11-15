"""Original paper/source separation and fail-before-write negative checks."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.check_paper_source import check

ROOT = Path(__file__).resolve().parents[1]


class PaperSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/marketing"
        shutil.copytree(ROOT / "docs/marketing", self.folder)

    def snapshot(self) -> dict[str, bytes]:
        return {
            str(path.relative_to(self.folder)): path.read_bytes()
            for path in self.folder.rglob("*")
            if path.is_file()
        }

    def generator(self, optimized: bool = False) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                *(["-O"] if optimized else []),
                str(self.folder / "build_documents.py"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def mutate(self, name: str, fn: Callable[[dict[str, Any]], None]) -> None:
        path = self.folder / name
        data = json.loads(path.read_text())
        fn(data)
        path.write_text(json.dumps(data))

    def repin(self, name: str) -> None:
        value = hashlib.sha256((self.folder / name).read_bytes()).hexdigest()

        def update_receipt(data: dict[str, Any]) -> None:
            data["source_files"][name] = value
            if name.endswith(".tex"):
                data["authored_tex_inputs"][name] = value
            if name == "runspindle-paper.tex":
                data["economics_integration"]["new_container_sha256"] = value

        self.mutate(
            "SRC-002-source-receipt.json",
            update_receipt,
        )
        self.mutate(
            "artifacts.json",
            lambda d: next(
                a for a in d["artifacts"] if a["path"] == "docs/marketing/" + name
            ).update(sha256=value),
        )

    def reject_without_writes(self, optimized: bool = False) -> str:
        (self.folder / "index.html").write_text("synthetic early-write sentinel")
        before = self.snapshot()
        result = self.generator(optimized=optimized)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SRC-002", result.stderr)
        self.assertEqual(before, self.snapshot())
        return result.stderr

    def test_compiled_check_binds_evidence_without_executing(self) -> None:
        result = check(self.root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["native_compile"], "passed")
        self.assertTrue(result["pdf_matches_authored_source"])
        self.assertEqual(result["historical_paper_dependencies"], 18)
        self.assertEqual(result["authored_tex_inputs"], 6)

    def test_compiled_pdf_and_evidence_cannot_be_repinned_in_both_modes(self) -> None:
        manifest = self.folder / "artifacts.json"
        manifest_bytes = manifest.read_bytes()
        for name in (
            "runspindle-paper.pdf",
            "SRC-002-build-evidence.json",
            "SRC-002-toolchain.json",
            "SRC-002-NOTICES.md",
            "SRC-002-COMPILED.md",
        ):
            path = self.folder / name
            original = path.read_bytes()
            for optimized in (False, True):
                with self.subTest(name=name, optimized=optimized):
                    path.write_bytes(original + b"\nsynthetic unreviewed change")
                    self.mutate(
                        "artifacts.json",
                        lambda d: next(
                            row
                            for row in d["artifacts"]
                            if row["path"] == "docs/marketing/" + name
                        ).update(sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
                    )
                    self.reject_without_writes(optimized)
                    manifest.write_bytes(manifest_bytes)
            path.write_bytes(original)

    def test_old_pdf_is_history_not_a_current_fallback(self) -> None:
        old = self.folder / "paper/legacy/reportlab-paper.pdf"
        current = self.folder / "runspindle-paper.pdf"
        self.assertNotEqual(old.read_bytes(), current.read_bytes())
        current.write_bytes(old.read_bytes())
        for optimized in (False, True):
            error = self.reject_without_writes(optimized)
            self.assertIn("unreviewed compiled PDF bytes", error)

    def test_source_only_receipt_is_preserved_as_history(self) -> None:
        historical = json.loads(
            (self.folder / "paper/history/source-receipt-9844e5a.json").read_text()
        )
        current = json.loads((self.folder / "SRC-002-source-receipt.json").read_text())
        self.assertEqual(historical["native_compile"], "not_run")
        self.assertFalse(historical["pdf_matches_authored_source"])
        self.assertEqual(current["native_compile"], "passed")
        self.assertEqual(
            historical["authored_tex_inputs"], current["authored_tex_inputs"]
        )

    def test_single_wrapping_change_retains_historical_evidence(self) -> None:
        change = json.loads((self.folder / "SRC-002-wrap-correction.json").read_text())
        master = (self.folder / "runspindle-paper.tex").read_text()
        original = master.replace(change["new_phrase"], change["old_phrase"])
        self.assertEqual(master.count(change["new_phrase"]), 1)
        self.assertEqual(
            hashlib.sha256(original.encode()).hexdigest(), change["prior_source_sha256"]
        )
        self.assertFalse(change["prior_diagnostic_output"]["accepted"])
        self.assertEqual(change["corrected_source_native_compile"], "not_run")
        historical = json.loads(
            (self.folder / "paper/history/source-receipt-2f37dc9.json").read_text()
        )
        self.assertEqual(
            historical["source_files"]["runspindle-paper.tex"],
            change["prior_source_sha256"],
        )

    def test_wrap_receipt_mutation_rejected_in_both_generator_modes(self) -> None:
        target = self.folder / "SRC-002-wrap-correction.json"
        original = target.read_bytes()
        for optimized in (False, True):
            self.mutate(
                target.name,
                lambda data: data.update(corrected_source_native_compile="passed"),
            )
            error = self.reject_without_writes(optimized)
            self.assertIn("wrapping transition receipt changed", error)
            target.write_bytes(original)

    def test_extra_rehashed_prose_change_is_not_the_reviewed_wrap_fix(self) -> None:
        target = self.folder / "runspindle-paper.tex"
        target.write_text(target.read_text() + "\n% synthetic unreviewed comment\n")
        self.repin(target.name)
        for optimized in (False, True):
            error = self.reject_without_writes(optimized)
            self.assertIn("single reviewed wrapping correction", error)

    def test_generator_preserves_all_files_twice(self) -> None:
        before = self.snapshot()
        for _ in range(2):
            result = self.generator()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, self.snapshot())

    def test_every_source_and_preserved_file_is_required(self) -> None:
        data = json.loads((self.folder / "SRC-002-source-receipt.json").read_text())
        for name in data["source_files"] | data["preserved_files"]:
            path = self.folder / name
            original = path.read_bytes()
            with self.subTest(name=name):
                path.unlink()
                self.reject_without_writes()
                path.write_bytes(original)

    def test_tampered_source_cannot_write(self) -> None:
        path = self.folder / "runspindle-paper.tex"
        path.write_text(path.read_text() + "\nchanged\n")
        self.reject_without_writes()

    def test_old_pdf_cannot_be_replaced_or_repinned(self) -> None:
        path = self.folder / "runspindle-paper.pdf"
        path.write_bytes(b"%PDF-synthetic-unreviewed")
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        self.mutate(
            "SRC-002-source-receipt.json",
            lambda d: d["preserved_files"].update({path.name: value}),
        )
        self.reject_without_writes()

    def test_fake_build_and_pairing_states_rejected(self) -> None:
        path = self.folder / "SRC-002-source-receipt.json"
        original = path.read_text()
        for key, value in [
            ("native_compile", "not_run"),
            ("pdf_matches_authored_source", False),
            ("migration_status", "complete"),
            ("live_acceptance", "passed"),
            ("base_commit", "0" * 40),
        ]:
            with self.subTest(key=key):
                self.mutate(path.name, lambda d: d.update({key: value}))
                self.reject_without_writes()
                path.write_text(original)

    def test_economics_cannot_be_changed_even_with_new_source_hash(self) -> None:
        path = self.folder / "runspindle-paper.tex"
        path.write_text(path.read_text().replace("U = C / A", "U = C / attempts"))
        self.repin(path.name)
        self.reject_without_writes()

    def test_generator_economics_cannot_drift(self) -> None:
        path = self.folder / "build_documents.py"
        path.write_text(path.read_text().replace("U = C / A", "U = C / attempts"))
        self.reject_without_writes()

    def test_missing_duplicate_or_imported_disposition_rejected(self) -> None:
        path = self.folder / "SRC-002-disposition.json"
        original = path.read_text()
        changes: list[Callable[[dict[str, Any]], None]] = [
            lambda d: d.update(units=d["units"][:-1]),
            lambda d: d["units"].append(d["units"][0]),
            lambda d: d["units"][0].update(source_expression_copied=True),
            lambda d: next(u for u in d["units"] if u["id"] == "F05").update(
                disposition="imported"
            ),
            lambda d: d.update(migration_status="complete"),
        ]
        for change in changes:
            with self.subTest(change=change):
                path.write_text(original)
                self.mutate(path.name, change)
                self.repin(path.name)
                self.reject_without_writes()

    def test_wrong_citation_order_or_url_rejected(self) -> None:
        path = self.folder / "SRC-002-citations.json"
        original = path.read_text()
        for field, value in [
            ("number", 2),
            ("url", "https://example.invalid"),
            ("source_expression_imported", True),
        ]:
            with self.subTest(field=field):
                path.write_text(original)
                self.mutate(
                    path.name, lambda d: d["citations"][0].update({field: value})
                )
                self.repin(path.name)
                self.reject_without_writes()

    def test_new_package_dependency_or_missing_citation_rejected(self) -> None:
        path = self.folder / "runspindle-paper.tex"
        original = path.read_text()
        for text in [
            original.replace(
                "{lmodern,amsmath,amssymb,graphicx}",
                "{lmodern,amsmath,amssymb,graphicx,tikz}",
            ),
            original + "\n\\input{outside.tex}\n",
            original.replace("\\bibitem{agentsmatter}", "\\bibitem{wrong}"),
        ]:
            with self.subTest(text=text[-50:]):
                path.write_text(text)
                self.repin(path.name)
                self.reject_without_writes()

    def test_symlink_diagram_directory_rejected(self) -> None:
        path = self.folder / "paper/diagrams"
        destination = self.folder / "elsewhere"
        path.rename(destination)
        path.symlink_to(destination, target_is_directory=True)
        self.reject_without_writes()

    def test_unperformed_build_plan_cannot_be_promoted(self) -> None:
        self.mutate(
            "SRC-002-build-plan.json",
            lambda d: d.update(dependency_closure_complete=True),
        )
        self.repin("SRC-002-build-plan.json")
        self.reject_without_writes()

    def test_economics_receipt_cannot_claim_changed_narrative(self) -> None:
        self.mutate(
            "SRC-002-source-receipt.json",
            lambda d: d["economics_integration"].update(narrative_changed=True),
        )
        self.reject_without_writes()

    def test_native_proposal_cannot_enable_automatic_generation(self) -> None:
        self.mutate(
            "SRC-002-build-plan.json",
            lambda d: d["proposed_environment"].update(MKTEXFMT="1"),
        )
        self.repin("SRC-002-build-plan.json")
        self.reject_without_writes()

    def test_digit_suffixed_tex_primitives_fail_before_writes_in_both_modes(
        self,
    ) -> None:
        path = self.folder / "runspindle-paper.tex"
        original = path.read_text()
        mutations = (
            r"\write18{echo synthetic-review-only}",
            r"\immediate\write18{echo synthetic-review-only}",
            r"\openout1=synthetic-review-only.txt",
            r"\read0 to \synthetic",
            r"\openin0=synthetic-review-only.txt",
            r"\directlua{synthetic_review_only}",
            r"\special{synthetic-review-only}",
        )
        for mutation in mutations:
            for optimized in (False, True):
                with self.subTest(mutation=mutation, optimized=optimized):
                    # This is text scanned by Python, never input to a TeX engine.
                    path.write_text(original + "\n" + mutation + "\n")
                    self.repin(path.name)
                    stderr = self.reject_without_writes(optimized=optimized)
                    self.assertIn("unexpected TeX primitive or dependency", stderr)

    def test_unbraced_and_nested_inputs_fail_before_writes_in_both_modes(self) -> None:
        cases = (
            ("runspindle-paper.tex", r"\input synthetic-review-only.tex"),
            ("runspindle-paper.tex", r"\input1"),
            (
                "paper/diagrams/stop-triage.tex",
                r"\input{paper/diagrams/effort-ledger.tex}",
            ),
        )
        for name, mutation in cases:
            path = self.folder / name
            original = path.read_text()
            for optimized in (False, True):
                with self.subTest(name=name, mutation=mutation, optimized=optimized):
                    path.write_text(original + "\n" + mutation + "\n")
                    self.repin(name)
                    stderr = self.reject_without_writes(optimized=optimized)
                    self.assertIn("nested or undeclared TeX input", stderr)
            path.write_text(original)
            self.repin(name)


if __name__ == "__main__":
    unittest.main()
