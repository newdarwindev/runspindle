"""Pinned SRC-013 closure, fail-before-write and generator preservation tests."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RefineryMirrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "marketing"
        shutil.copytree(ROOT / "docs/marketing", self.folder)

    def snapshot(self) -> dict[str, bytes]:
        return {
            str(p.relative_to(self.folder)): p.read_bytes()
            for p in self.folder.rglob("*")
            if p.is_file()
        }

    def run_generator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(self.folder / "build_documents.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def reject(self) -> None:
        (self.folder / "index.html").write_text("synthetic sentinel")
        before = self.snapshot()
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SRC-013", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_each_file_is_required(self) -> None:
        manifest = json.loads((self.folder / "artifacts.json").read_text())
        for item in manifest["artifacts"]:
            if (
                item.get("canonical", {}).get("repository")
                != "newdarwindev/runspindle-refinery"
            ):
                continue
            path = self.folder / item["path"].removeprefix("docs/marketing/")
            original = path.read_bytes()
            with self.subTest(path=path.name):
                path.unlink()
                self.reject()
                path.write_bytes(original)

    def test_tampered_pdf_and_manifest_cannot_repin(self) -> None:
        path = self.folder / "workflow-refinery.pdf"
        path.write_bytes(b"synthetic changed PDF")
        manifest_path = self.folder / "artifacts.json"
        manifest = json.loads(manifest_path.read_text())
        for item in manifest["artifacts"]:
            if item["path"].endswith("/workflow-refinery.pdf"):
                item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                item["canonical"]["sha256"] = item["sha256"]
        manifest_path.write_text(json.dumps(manifest))
        self.reject()

    def test_wrapper_and_receipts_cannot_be_repinned(self) -> None:
        manifest_path = self.folder / "artifacts.json"
        original_manifest = manifest_path.read_bytes()
        for name in (
            "build-paper.py",
            "source-wrapper-change-evidence.json",
            "SRC-013-wrapper-mirror.json",
            "SRC-013-integration.json",
            "SRC-013-final-validation.json",
        ):
            path = self.folder / name
            original = path.read_bytes()
            with self.subTest(name=name):
                path.write_bytes(original + b"\n")
                manifest = json.loads(original_manifest)
                item = next(
                    x
                    for x in manifest["artifacts"]
                    if x["path"] == "docs/marketing/" + name
                )
                item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                if "canonical" in item:
                    item["canonical"]["sha256"] = item["sha256"]
                manifest_path.write_text(json.dumps(manifest))
                self.reject()
                path.write_bytes(original)
                manifest_path.write_bytes(original_manifest)

    def test_mirror_receipts_are_required_regular_files(self) -> None:
        for name in (
            "SRC-013-wrapper-mirror.json",
            "SRC-013-integration.json",
            "SRC-013-final-validation.json",
        ):
            path = self.folder / name
            original = path.read_bytes()
            with self.subTest(name=name, mutation="missing"):
                path.unlink()
                self.reject()
                path.write_bytes(original)
            with self.subTest(name=name, mutation="symlink"):
                target = self.folder / "synthetic-receipt-target"
                target.write_bytes(original)
                path.unlink()
                path.symlink_to(target)
                self.reject()
                path.unlink()
                path.write_bytes(original)
                target.unlink()

    def test_receipt_manifest_binding_is_mandatory(self) -> None:
        path = self.folder / "artifacts.json"
        original = path.read_bytes()
        for mutation in ("missing", "duplicate", "source", "canonical"):
            with self.subTest(mutation=mutation):
                manifest = json.loads(original)
                item = next(
                    x
                    for x in manifest["artifacts"]
                    if x["path"].endswith("/SRC-013-wrapper-mirror.json")
                )
                if mutation == "missing":
                    manifest["artifacts"].remove(item)
                elif mutation == "duplicate":
                    manifest["artifacts"].append(item)
                elif mutation == "source":
                    item["source_ids"] = ["SRC-003"]
                else:
                    item["canonical"] = {"commit": "0" * 40}
                path.write_text(json.dumps(manifest))
                self.reject()
        path.write_bytes(original)

    def test_stale_canonical_commit_rejected(self) -> None:
        path = self.folder / "artifacts.json"
        manifest = json.loads(path.read_text())
        for item in manifest["artifacts"]:
            if (
                item.get("canonical", {}).get("repository")
                == "newdarwindev/runspindle-refinery"
            ):
                item["canonical"]["commit"] = "bfa8f760c1d56ec1c2ce07ea49e4d37ce4c01e5b"
        path.write_text(json.dumps(manifest))
        self.reject()

    def test_current_mapping_preserves_historical_identity(self) -> None:
        current = json.loads((self.folder / "SRC-013-wrapper-mirror.json").read_text())
        previous = json.loads((self.folder / "SRC-013-integration.json").read_text())
        self.assertEqual(
            current["canonical_commit"], "1aa0a4b0ed1494f88f9e3137ff1e2b73b7a25209"
        )
        self.assertEqual(
            current["previous_canonical_commit"], previous["canonical_commit"]
        )
        self.assertEqual(
            current["canonical_tree"], "23ac8ce5d5d8f1b53023e640a90ab38a52cff339"
        )
        self.assertEqual(len(current["current_closure_sha256"]), 17)
        for name, digest in current["historical_mirror_receipts"].items():
            self.assertEqual(
                hashlib.sha256((self.folder / name).read_bytes()).hexdigest(), digest
            )

    def test_symlink_figure_directory_rejected(self) -> None:
        figures = self.folder / "figures"
        target = self.folder / "elsewhere"
        figures.rename(target)
        figures.symlink_to(target, target_is_directory=True)
        self.reject()

    def test_wrong_commit_duplicate_or_wrong_source_rejected(self) -> None:
        path = self.folder / "artifacts.json"
        original = path.read_text()
        for mutation in ("commit", "duplicate", "source"):
            with self.subTest(mutation=mutation):
                manifest = json.loads(original)
                item = next(
                    x
                    for x in manifest["artifacts"]
                    if x["path"].endswith("/workflow-refinery.pdf")
                )
                if mutation == "commit":
                    item["canonical"]["commit"] = "0" * 40
                elif mutation == "duplicate":
                    manifest["artifacts"].append(item)
                else:
                    item["source_ids"] = ["SRC-002", "SRC-013"]
                path.write_text(json.dumps(manifest))
                self.reject()
        path.write_text(original)

    def test_generator_preserves_all_bytes_twice(self) -> None:
        before = self.snapshot()
        for _ in range(2):
            result = self.run_generator()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
