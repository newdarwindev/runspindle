"""SRC-009 canonical transform, link closure and fail-before-write checks."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from tools.check_browser_mirror import check

ROOT = Path(__file__).resolve().parents[1]


class BrowserMirrorTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.folder = self.root / "docs/marketing"
        shutil.copytree(ROOT / "docs/marketing", self.folder)
        (self.root / "tools").mkdir()
        shutil.copyfile(
            ROOT / "tools/check_browser_mirror.py",
            self.root / "tools/check_browser_mirror.py",
        )

    def snapshot(self) -> dict[str, bytes]:
        return {
            str(path.relative_to(self.folder)): path.read_bytes()
            for path in self.folder.rglob("*")
            if path.is_file()
        }

    def read(self, name: str) -> dict[str, Any]:
        data: dict[str, Any] = json.loads((self.folder / name).read_text())
        return data

    def write(self, name: str, data: dict[str, Any]) -> None:
        (self.folder / name).write_text(json.dumps(data, indent=2) + "\n")

    def rehash(self, name: str) -> None:
        data = self.read("artifacts.json")
        row = next(
            item
            for item in data["artifacts"]
            if item["path"] == "docs/marketing/" + name
        )
        row["sha256"] = hashlib.sha256((self.folder / name).read_bytes()).hexdigest()
        self.write("artifacts.json", data)

    def run_generator(self) -> subprocess.CompletedProcess[str]:
        flags = ["-O"] if sys.flags.optimize else []
        return subprocess.run(
            [
                sys.executable,
                *flags,
                "-B",
                "-S",
                str(self.folder / "build_documents.py"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def rejected_without_writes(self) -> None:
        index = self.folder / "index.html"
        if index.exists():
            index.write_bytes(b"synthetic generated-output sentinel")
        before = self.snapshot()
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_mapping_is_explicit_and_canonical_bytes_are_reconstructable(self) -> None:
        result = check(self.root)
        self.assertEqual(result["transformations"], 10)
        self.assertEqual(result["external_navigation_targets"], 9)
        self.assertNotEqual(result["canonical_sha256"], result["derivative_sha256"])
        self.assertEqual(
            result["canonical_commit"], "dfc9ac3e51abba8e84ab217a5eec5358b2088a3f"
        )
        self.assertEqual(
            result["verification"],
            {
                "source_mapping": "checked_separately",
                "rendered_desktop_mobile": "not_run",
                "keyboard_navigation": "not_run",
                "root_independent_review": "required_before_publication",
                "runtime": "not_run",
            },
        )

    def test_generator_preserves_every_marketing_byte_twice(self) -> None:
        before = self.snapshot()
        for _ in range(2):
            result = self.run_generator()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.snapshot(), before)

    def test_each_canonical_mapping_file_is_required(self) -> None:
        for name in ("browser.html", "SRC-009-mirror.json", "SRC-009-mirror.md"):
            path = self.folder / name
            original = path.read_bytes()
            with self.subTest(name=name):
                path.unlink()
                self.rejected_without_writes()
                path.write_bytes(original)

    def test_each_mapping_file_must_be_regular(self) -> None:
        for name in ("browser.html", "SRC-009-mirror.json", "SRC-009-mirror.md"):
            path = self.folder / name
            original = path.read_bytes()
            target = self.folder / "synthetic-symlink-target"
            with self.subTest(name=name):
                target.write_bytes(original)
                path.unlink()
                path.symlink_to(target)
                self.rejected_without_writes()
                path.unlink()
                path.write_bytes(original)
                target.unlink()

    def test_missing_local_navigation_target_fails_before_output_repair(self) -> None:
        (self.folder / "index.html").unlink()
        self.rejected_without_writes()

    def test_symlink_local_navigation_is_not_followed(self) -> None:
        path = self.folder / "index.html"
        path.unlink()
        path.symlink_to(self.folder / "SRC-009-mirror.md")
        # Do not write the sentinel through the deliberate symlink.
        before = self.snapshot()
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_changed_prose_css_or_links_cannot_be_approved_by_rehash(self) -> None:
        path = self.folder / "browser.html"
        original = path.read_text()
        manifest = (self.folder / "artifacts.json").read_bytes()
        for body in (
            original.replace("one headed browser", "synthetic changed browser"),
            original.replace(
                "</style>",
                '.map { background-image: image-set("//example.invalid/CANARY.png" 1x); }</style>',
            ),
            original.replace('href="index.html"', 'href="missing.html"'),
            original.replace('/specs/credentials-handoff.md"', '/specs/system.md"'),
            original.replace(
                "root-derivative rendering and keyboard acceptance remain pending",
                "root-derivative rendering and keyboard acceptance passed",
            ),
        ):
            with self.subTest(body=body[-80:]):
                path.write_text(body)
                self.rehash("browser.html")
                self.rejected_without_writes()
                (self.folder / "artifacts.json").write_bytes(manifest)
        path.write_text(original)

    def test_receipt_cannot_repin_canonical_source_or_rewrite_transform(self) -> None:
        path = self.folder / "SRC-009-mirror.json"
        original = path.read_bytes()
        for mutation in ("commit", "hash", "transform", "status", "relationship"):
            data = json.loads(original)
            if mutation == "commit":
                data["canonical"]["commit"] = "0" * 40
            elif mutation == "hash":
                data["destination_sha256"] = "0" * 64
            elif mutation == "transform":
                data["transforms"][0]["new"] = 'href="index.html"'
            elif mutation == "status":
                data["verification"]["keyboard_navigation"] = "passed"
            else:
                data["relationship"] = "byte_identical"
            with self.subTest(mutation=mutation):
                self.write(path.name, data)
                self.rehash(path.name)
                self.rejected_without_writes()
        path.write_bytes(original)

    def test_manifest_binding_is_mandatory_and_cannot_claim_byte_identity(self) -> None:
        path = self.folder / "artifacts.json"
        original = path.read_bytes()
        for mutation in (
            "missing",
            "duplicate",
            "source",
            "canonical",
            "transform",
            "status",
            "kind",
        ):
            data = json.loads(original)
            row = next(
                item
                for item in data["artifacts"]
                if item["path"] == "docs/marketing/browser.html"
            )
            if mutation == "missing":
                data["artifacts"].remove(row)
            elif mutation == "duplicate":
                data["artifacts"].append(dict(row))
            elif mutation == "source":
                row["source_ids"] = ["SRC-010"]
            elif mutation == "canonical":
                row["canonical"]["sha256"] = row["sha256"]
            elif mutation == "transform":
                row["transformation"] = "none"
            elif mutation == "status":
                row["verification"]["runtime"] = "passed"
            else:
                row["kind"] = "byte_preserved_mirror"
            with self.subTest(mutation=mutation):
                self.write(path.name, data)
                self.rejected_without_writes()
        path.write_bytes(original)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        path = self.folder / "artifacts.json"
        original = path.read_text()
        path.write_text(
            original.replace('"artifacts": [', '"artifacts": [], "artifacts": [', 1)
        )
        self.rejected_without_writes()

    def test_reintroduced_obsolete_browser_writer_fails_before_any_write(self) -> None:
        path = self.folder / "build_documents.py"
        path.write_text(path.read_text() + '\npage("browser.html", "obsolete", [])\n')
        self.rejected_without_writes()

    def test_all_existing_source_guards_still_precede_browser_guard(self) -> None:
        path = self.folder / "build_documents.py"
        original = path.read_text()
        for name in (
            "verify_vision_mirror",
            "verify_refinery_mirror",
            "verify_paper_source",
            "verify_presentation_source",
        ):
            with self.subTest(name=name):
                path.write_text(original.replace(name + "(P)", "# removed guard"))
                self.rejected_without_writes()
        path.write_text(original)

    def test_missing_browser_guard_is_rejected_by_standalone_checker(self) -> None:
        path = self.folder / "build_documents.py"
        path.write_text(
            path.read_text().replace("verify_browser_mirror(P)", "# removed guard")
        )
        with self.assertRaises(ValueError):
            check(self.root)

    def test_failure_is_sanitized_in_normal_and_optimized_cli(self) -> None:
        path = self.folder / "SRC-009-mirror.json"
        path.write_text('{"CANARY-PRIVATE": "not a receipt"}')
        self.rehash(path.name)
        for flags in ([], ["-O"]):
            result = subprocess.run(
                [sys.executable, *flags, "-B", "-S", "tools/check_browser_mirror.py"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "failed")
            self.assertNotIn("CANARY-PRIVATE", result.stdout)
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
