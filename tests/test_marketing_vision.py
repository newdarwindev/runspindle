"""SRC-010 mirror guard; generator checks are not visual acceptance."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import NotRequired, TypedDict, cast

ROOT = Path(__file__).resolve().parents[1]


class CanonicalPin(TypedDict):
    commit: str
    path: str
    repository: str
    sha256: str


class ArtifactRecord(TypedDict):
    path: str
    sha256: str
    canonical: NotRequired[CanonicalPin]
    verification: NotRequired[dict[str, str]]


class ArtifactManifest(TypedDict):
    artifacts: list[ArtifactRecord]


class MarketingVisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "marketing"
        shutil.copytree(ROOT / "docs/marketing", self.folder)

    def snapshot(self) -> dict[str, bytes]:
        return {p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()}

    def run_generator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(self.folder / "build_documents.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def manifest(self, mutate: Callable[[ArtifactManifest], object]) -> None:
        path = self.folder / "artifacts.json"
        data = cast(ArtifactManifest, json.loads(path.read_text()))
        mutate(data)
        path.write_text(json.dumps(data))

    def item(self, data: ArtifactManifest, name: str = "vision.html") -> ArtifactRecord:
        return next(
            x for x in data["artifacts"] if x["path"] == "docs/marketing/" + name
        )

    def rejected_without_writes(self, expected: str) -> None:
        # Include sentinels in generated pages and PDFs so an accidental early
        # write cannot pass merely by reproducing the previous output bytes.
        for name in (
            "index.html",
            "browser.html",
            "workflow-refinery.pdf",
            "runspindle-paper.tex",
            "THIRD_PARTY_NOTICES.md",
        ):
            path = self.folder / name
            path.write_bytes(path.read_bytes() + b"\nsynthetic preflight sentinel\n")
        before = self.snapshot()
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(expected, result.stderr)
        self.assertEqual(
            self.snapshot(), before, "preflight failure changed generated files"
        )

    def test_missing_vision_does_not_write(self) -> None:
        (self.folder / "vision.html").unlink()
        self.rejected_without_writes("Missing or symlink SRC-010 mirror")

    def test_changed_vision_does_not_write(self) -> None:
        path = self.folder / "vision.html"
        path.write_bytes(path.read_bytes() + b"\n")
        self.rejected_without_writes("canonical mirror mismatch")

    def test_changed_notice_does_not_write(self) -> None:
        (self.folder / "LICENSE-SRC-010.txt").write_text("incomplete MIT")
        self.rejected_without_writes("canonical mirror mismatch")

    def test_notice_hash_update_does_not_bypass_exact_notice(self) -> None:
        path = self.folder / "LICENSE-SRC-010.txt"
        path.write_text("incomplete MIT")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        def mutate(data: ArtifactManifest) -> None:
            item = self.item(data, path.name)
            item["sha256"] = digest
            item["canonical"]["sha256"] = digest

        self.manifest(mutate)
        self.rejected_without_writes("MIT notice changed")

    def test_missing_disposition_does_not_write(self) -> None:
        (self.folder / "SRC-010-lift.json").unlink()
        self.rejected_without_writes("Missing or symlink SRC-010 mirror")

    def test_changed_validation_does_not_write(self) -> None:
        (self.folder / "SRC-010-validation.md").write_text("pretend passed")
        self.rejected_without_writes("canonical mirror mismatch")

    def test_wrong_canonical_path_does_not_write(self) -> None:
        self.manifest(
            lambda d: self.item(d)["canonical"].update(
                {"path": "docs/product/index.html"}
            )
        )
        self.rejected_without_writes("canonical mirror mismatch")

    def test_unpinned_commit_does_not_write(self) -> None:
        self.manifest(lambda d: self.item(d)["canonical"].update({"commit": "main"}))
        self.rejected_without_writes("canonical mirror mismatch")

    def test_mixed_commits_do_not_write(self) -> None:
        self.manifest(lambda d: self.item(d)["canonical"].update({"commit": "0" * 40}))
        self.rejected_without_writes("share one canonical revision")

    def test_duplicate_entry_does_not_write(self) -> None:
        self.manifest(
            lambda d: d["artifacts"].append(cast(ArtifactRecord, dict(self.item(d))))
        )
        self.rejected_without_writes("Missing or duplicate SRC-010 mirror entry")

    def test_fake_visual_acceptance_does_not_write(self) -> None:
        self.manifest(
            lambda d: self.item(d)["verification"].update(visual_keyboard_zoom="passed")
        )
        self.rejected_without_writes("visual acceptance remains blocked")

    def test_missing_manifest_does_not_write(self) -> None:
        (self.folder / "artifacts.json").unlink()
        self.rejected_without_writes("FileNotFoundError")

    def test_generator_preserves_canonical_and_other_outputs(self) -> None:
        self.assertIsNotNone(
            importlib.util.find_spec("reportlab"),
            "ReportLab is required for generator validation; no install or fallback was attempted",
        )
        before = self.snapshot()
        for _ in range(2):
            result = self.run_generator()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
