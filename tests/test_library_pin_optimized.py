"""Real CLI/index tests with synthetic Cargo metadata, not component qualification."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools/check_library_pins.py"
HOST = "1" * 40
CORE = "2" * 40


class OptimizedPins(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tools").mkdir()
        (self.root / "components/core").mkdir(parents=True)
        self.script = self.root / "tools/check_library_pins.py"
        shutil.copyfile(os.environ.get("PIN_CHECK_MUTANT", SOURCE), self.script)
        self.lock = {"schema_version": 1, "components": [
            {"component": "core", "path": "components/core", "commit": CORE},
            {"component": "host", "path": "components/host", "commit": HOST},
        ]}
        self.write_lock()
        self.manifest = self.root / "components/core/Cargo.toml"
        self.manifest.write_text('[dependencies]\nrunspindle-host = {git = "https://github.com/newdarwindev/runspindle-host.git", rev = "' + HOST + '"}\n')
        self.cargo = self.root / "components/core/Cargo.lock"
        self.cargo.write_text('version = 4\n[[package]]\nname = "runspindle-host"\nsource = "git+https://github.com/newdarwindev/runspindle-host.git?rev=' + HOST + '#' + HOST + '"\n')
        self.git("init", "--quiet")
        for name, pin in [("core", CORE), ("host", HOST)]:
            self.git("update-index", "--add", "--cacheinfo", "160000," + pin + ",components/" + name)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, timeout=10)

    def write_lock(self):
        (self.root / "composition.lock.json").write_text(json.dumps(self.lock))

    def run_check(self, optimized):
        result = subprocess.run([sys.executable, *(["-O"] if optimized else []), str(self.script)],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def reject_both(self):
        for optimized in [False, True]:
            with self.subTest(optimized=optimized):
                code, receipt = self.run_check(optimized)
                self.assertEqual(code, 1)
                self.assertEqual(receipt["status"], "failed")
                self.assertEqual(receipt["live_acceptance"], "not_run")

    def test_valid_synthetic_alignment_both_modes(self):
        for optimized in [False, True]:
            code, receipt = self.run_check(optimized)
            self.assertEqual(code, 0)
            self.assertEqual(receipt["host_library"], HOST)

    def test_wrong_manifest_revision(self):
        self.manifest.write_text(self.manifest.read_text().replace(HOST, "3" * 40))
        self.reject_both()

    def test_wrong_index_pin(self):
        self.git("update-index", "--cacheinfo", "160000," + "3" * 40 + ",components/host")
        self.reject_both()

    def test_versions_duplicates_and_paths(self):
        original = copy.deepcopy(self.lock)
        for value in [True, 2, "1", None]:
            self.lock = copy.deepcopy(original)
            self.lock["schema_version"] = value
            self.write_lock()
            self.reject_both()
        self.lock = copy.deepcopy(original)
        self.lock["components"].append(copy.deepcopy(self.lock["components"][0]))
        self.write_lock()
        self.reject_both()
        self.lock = copy.deepcopy(original)
        self.lock["components"][0]["path"] = "../unselected"
        self.write_lock()
        self.reject_both()

    def test_comment_decoys_cannot_satisfy_manifest_or_lock(self):
        manifest = self.manifest.read_text()
        cargo = self.cargo.read_text()
        self.manifest.write_text(manifest.replace(HOST, "3" * 40) + "# " + manifest.splitlines()[1] + "\n")
        self.reject_both()
        self.manifest.write_text(manifest)
        self.cargo.write_text(cargo.replace(HOST, "3" * 40) + "# ?rev=" + HOST + "#" + HOST + "\n")
        self.reject_both()

    def test_wrong_sources_and_duplicate_packages(self):
        manifest = self.manifest.read_text()
        for replacement in [manifest.replace("newdarwindev", "unrelated"), manifest.replace('rev =', 'branch ='), manifest.replace('rev =', 'path =')]:
            self.manifest.write_text(replacement)
            self.reject_both()
        self.manifest.write_text(manifest)
        self.cargo.write_text(self.cargo.read_text() + '\n[[package]]\nname="runspindle-host"\n')
        self.reject_both()

    def test_dependency_package_alias_must_select_actual_host(self):
        original = self.manifest.read_text()
        self.manifest.write_text(original.replace('{git =', '{package = "different-package", git ='))
        self.reject_both()
        self.manifest.write_text(original.replace('{git =', '{package = "runspindle-host", git ='))
        for optimized in [False, True]:
            self.assertEqual(self.run_check(optimized)[0], 0)

    def test_missing_source_is_blocked_not_passed(self):
        self.manifest.unlink()
        for optimized in [False, True]:
            code, receipt = self.run_check(optimized)
            self.assertEqual(code, 78)
            self.assertEqual(receipt["status"], "blocked")

    def test_malformed_toml_never_exposes_canary(self):
        self.manifest.write_text('invalid = "synthetic-secret-canary\n')
        self.reject_both()
        self.assertNotIn("canary", str(self.run_check(True)))

    def test_removed_revision_guard_mutant_is_detected(self):
        if os.environ.get("PIN_CHECK_MUTANT"):
            self.skipTest("outer mutation driver only")
        anchor = 'require(host_dep.get("rev") == host, "core/host library pin mismatch")'
        source = SOURCE.read_text()
        self.assertEqual(source.count(anchor), 1)
        mutant = self.root / "mutant.py"
        mutant.write_text(source.replace(anchor, 'require(True, "core/host library pin mismatch")'))
        env = {**os.environ, "PIN_CHECK_MUTANT": str(mutant)}
        child = subprocess.run([sys.executable, str(Path(__file__)), "OptimizedPins.test_wrong_manifest_revision"],
                               env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(child.returncode, 1)
        self.assertIn("0 != 1", child.stderr)


if __name__ == "__main__":
    unittest.main()
