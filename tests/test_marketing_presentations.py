"""Presentation source accounting and fail-before-write checks; never run TeX."""

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

from tools.check_presentation_source import check

ROOT = Path(__file__).resolve().parents[1]


class PresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/marketing"
        shutil.copytree(ROOT / "docs/marketing", self.folder)

    def snapshot(self) -> dict[str, bytes]:
        return {
            str(p.relative_to(self.folder)): p.read_bytes()
            for p in self.folder.rglob("*")
            if p.is_file()
        }

    def generator(self, optimized: bool = False) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                "-S",
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
        self.mutate(
            "SRC-003-004-source-receipt.json",
            lambda d: d["source_files"].update({name: value}),
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
        result = self.generator(optimized)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SRC-003/004", result.stderr)
        self.assertEqual(before, self.snapshot())
        return result.stderr

    def test_static_scope_never_claims_compile(self) -> None:
        result = check(self.root)
        self.assertEqual(result["original_slide_instances"], 20)
        self.assertEqual(result["retained_bundle_units"], 28)
        self.assertEqual(result["authored_frames"], {"argument": 12, "fleet": 14})
        self.assertEqual(result["native_compile"], "not_run")
        self.assertFalse(result["pdf_matches_authored_source"])

    def test_two_run_preservation_without_site_packages_or_reportlab(self) -> None:
        # Any attempted dependency import fails instead of silently using a fallback.
        (self.folder / "reportlab.py").write_text(
            'raise RuntimeError("ReportLab must never be imported")\n'
        )
        before = self.snapshot()
        for optimized in (False, True):
            for _ in range(2):
                result = self.generator(optimized)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_every_new_source_file_is_required(self) -> None:
        receipt = json.loads(
            (self.folder / "SRC-003-004-source-receipt.json").read_text()
        )
        for name in receipt["source_files"]:
            path = self.folder / name
            original = path.read_bytes()
            with self.subTest(name=name):
                path.unlink()
                self.reject_without_writes()
                path.write_bytes(original)

    def test_tampered_shared_source_rejected(self) -> None:
        path = self.folder / "presentations/shared/effort.tex"
        path.write_text(path.read_text() + "Changed\n")
        self.reject_without_writes()

    def test_old_pdf_and_source_cannot_be_repinned(self) -> None:
        for name in (
            "argument.pdf",
            "fleet.pdf",
            "presentations/legacy/argument-reportlab.tex",
            "presentations/legacy/fleet-reportlab.tex",
        ):
            path = self.folder / name
            original = path.read_bytes()
            receipt = (self.folder / "SRC-003-004-source-receipt.json").read_bytes()
            with self.subTest(name=name):
                path.write_bytes(b"synthetic changed legacy asset")
                value = hashlib.sha256(path.read_bytes()).hexdigest()
                self.mutate(
                    "SRC-003-004-source-receipt.json",
                    lambda d: d["preserved_files"].update({name: value}),
                )
                self.reject_without_writes()
                path.write_bytes(original)
                (self.folder / "SRC-003-004-source-receipt.json").write_bytes(receipt)

    def test_false_completion_and_parent_claims_fail(self) -> None:
        p = self.folder / "SRC-003-004-source-receipt.json"
        original = p.read_bytes()
        for key, value in [
            ("native_compile", "passed"),
            ("pdf_matches_authored_source", True),
            ("migration_status", "complete"),
            ("live_acceptance", "passed"),
            ("base_commit", "0" * 40),
            ("base_tree", "0" * 40),
        ]:
            with self.subTest(key=key):
                self.mutate(p.name, lambda d: d.update({key: value}))
                self.reject_without_writes(optimized=True)
                p.write_bytes(original)

    def test_missing_duplicate_and_unlicensed_dispositions_fail(self) -> None:
        name = "SRC-003-004-disposition.json"
        p = self.folder / name
        original = p.read_text()
        changes: list[Callable[[dict[str, Any]], None]] = [
            lambda d: d.update(source_slides=d["source_slides"][:-1]),
            lambda d: d["source_slides"].append(d["source_slides"][0]),
            lambda d: d["source_slides"][0].update(frame_labels=["absent"]),
            lambda d: d["source_slides"][0].update(frame_labels=["economics"]),
            lambda d: d["source_slides"][0].update(source_expression_copied=True),
            lambda d: d.update(source_bundle_units=d["source_bundle_units"][:-1]),
            lambda d: d["source_bundle_units"][0].update(source_expression_copied=True),
            lambda d: d["source_bundle_units"][0].update(destinations=["missing.tex"]),
            lambda d: d.update(migration_status="complete"),
        ]
        for change in changes:
            p.write_text(original)
            self.mutate(name, change)
            self.repin(name)
            self.reject_without_writes()

    def test_unbraced_and_nested_inputs_fail_in_both_modes(self) -> None:
        cases = [
            ("argument.tex", r"\input1"),
            ("fleet.tex", r"\input synthetic-review-only.tex"),
            (
                "presentations/shared/effort.tex",
                r"\input{presentations/shared/diagnosis.tex}",
            ),
        ]
        for name, mutation in cases:
            p = self.folder / name
            original = p.read_text()
            for optimized in (False, True):
                with self.subTest(name=name, optimized=optimized):
                    p.write_text(original + "\n" + mutation + "\n")
                    self.repin(name)
                    self.reject_without_writes(optimized)
            p.write_text(original)
            self.repin(name)

    def test_digit_suffixed_tex_primitives_fail_in_both_modes(self) -> None:
        p = self.folder / "presentations/shared/effort.tex"
        name = str(p.relative_to(self.folder))
        original = p.read_text()
        for text in (
            r"\write18{synthetic}",
            r"\immediate\write18{synthetic}",
            r"\openout1=synthetic.txt",
            r"\read0 to \synthetic",
            r"\openin0=synthetic.txt",
            r"\directlua{synthetic}",
            r"\special{synthetic}",
        ):
            for optimized in (False, True):
                with self.subTest(text=text, optimized=optimized):
                    p.write_text(original + "\n" + text + "\n")
                    self.repin(name)
                    self.assertIn(
                        "unexpected TeX primitive",
                        self.reject_without_writes(optimized),
                    )

    def test_new_package_or_reordered_source_fails(self) -> None:
        p = self.folder / "argument.tex"
        original = p.read_text()
        for text in (
            original + "\n\\usepackage{unreviewed}\n",
            original.replace("shared/diagnosis.tex", "shared/effort.tex"),
            original.replace("{beamer}", "{article}"),
        ):
            p.write_text(text)
            self.repin(p.name)
            self.reject_without_writes()

    def test_duplicate_frame_and_missing_environment_fail(self) -> None:
        p = self.folder / "presentations/shared/effort.tex"
        original = p.read_text()
        for text in (original + original, original.replace(r"\end{tabular}", "")):
            p.write_text(text)
            self.repin(str(p.relative_to(self.folder)))
            self.reject_without_writes()

    def test_unknown_links_or_changed_citation_fail(self) -> None:
        p = self.folder / "SRC-003-004-citations.json"
        self.mutate(
            p.name, lambda d: d["citations"][0].update(url="https://example.invalid")
        )
        self.repin(p.name)
        self.reject_without_writes()

    def test_economics_invariant_cannot_be_repinned(self) -> None:
        p = self.folder / "presentations/shared/economics.tex"
        p.write_text(p.read_text().replace("U=C/A", "U=C/attempts"))
        self.repin(str(p.relative_to(self.folder)))
        self.reject_without_writes()

    def test_build_inventory_cannot_claim_unobserved_closure(self) -> None:
        name = "SRC-003-004-build-plan.json"
        self.mutate(name, lambda d: d.update(dependency_closure_complete=True))
        self.repin(name)
        self.reject_without_writes()

    def test_directory_symlink_rejected(self) -> None:
        path = self.folder / "presentations/shared"
        dest = self.folder / "moved-shared"
        path.rename(dest)
        path.symlink_to(dest, target_is_directory=True)
        self.reject_without_writes()

    def test_manifest_cannot_pair_old_pdf_with_new_source(self) -> None:
        self.mutate(
            "artifacts.json",
            lambda d: next(
                a for a in d["artifacts"] if a["path"] == "docs/marketing/argument.pdf"
            ).update(kind="compiled_pdf"),
        )
        self.reject_without_writes()


if __name__ == "__main__":
    unittest.main()
