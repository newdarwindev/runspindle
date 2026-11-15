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
