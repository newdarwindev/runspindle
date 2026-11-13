"""Black-box structural pin negatives in a disposable local clone; no runtime claims."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LibraryPins(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name) / "composition"
        subprocess.run(
            ["git", "clone", "--shared", "--quiet", str(ROOT), str(self.root)],
            check=True,
            capture_output=True,
        )
        shutil.copyfile(
            ROOT / "tools/check_library_pins.py",
            self.root / "tools/check_library_pins.py",
        )

    def tearDown(self):
        self.temp.cleanup()

    def check(self):
        return subprocess.run(
            ["python3", "tools/check_library_pins.py"],
            cwd=self.root,
            text=True,
            capture_output=True,
        )

    def core_files(self):
        core = self.root / "components/core"
        core.mkdir(exist_ok=True)
        for name in ("Cargo.toml", "Cargo.lock"):
            shutil.copyfile(ROOT / "components/core" / name, core / name)
        return core

    def test_missing_submodule_files_fail_closed_with_setup_reason(self):
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("initialize pinned submodules", result.stdout + result.stderr)

    def test_manifest_revision_cannot_disagree_with_gitlink(self):
        core = self.core_files()
        self.assertEqual(self.check().returncode, 0)
        manifest = core / "Cargo.toml"
        text = manifest.read_text()
        import json

        pin = next(
            item["commit"]
            for item in json.loads((self.root / "composition.lock.json").read_text())[
                "components"
            ]
            if item["component"] == "host"
        )
        self.assertIn('rev = "' + pin + '"', text)
        manifest.write_text(
            text.replace('rev = "' + pin + '"', 'rev = "' + "0" * 40 + '"')
        )
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("library pin mismatch", result.stdout + result.stderr)

    def test_cargo_lock_cannot_substitute_another_host_revision(self):
        core = self.core_files()
        lock = core / "Cargo.lock"
        text = lock.read_text()
        import json

        pin = next(
            item["commit"]
            for item in json.loads((self.root / "composition.lock.json").read_text())[
                "components"
            ]
            if item["component"] == "host"
        )
        lock.write_text(
            text.replace("?rev=" + pin + "#" + pin, "?rev=" + "0" * 40 + "#" + "0" * 40)
        )
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cargo.lock host pin mismatch", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
