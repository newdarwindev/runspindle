"""Actual temporary Git stores, synthetic receipts and independent effect observations."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOL = Path(os.environ.get("RUNSPINDLE_RECONCILER", Path(__file__).resolve().parents[1] / "tools/reconcile_evidence.py"))
spec = importlib.util.spec_from_file_location("reconciler", TOOL)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.artifacts = self.base / "artifacts"
        self.artifacts.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "synthetic@example.invalid")
        self.git("config", "user.name", "Synthetic Fixture")
        pins = []
        for name in ("core", "host", "browser", "tether", "refinery", "console", "platform"):
            pin = {"component": name, "commit": "a" * 40, "path": "components/" + name}
            pins.append(pin)
            (self.repo / pin["path"]).mkdir(parents=True)
            self.git("update-index", "--add", "--cacheinfo", "160000," + pin["commit"] + "," + pin["path"])
        self.write(self.repo / "composition.lock.json", {"schema_version": 1, "components": pins})
        self.write(self.repo / "STATUS.json", {"bounded": "passed"})
        (self.repo / "README.md").write_text("Synthetic criterion: passed\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Synthetic fixture")
        self.sha = self.git("rev-parse", "HEAD")
        # The independent observation is produced in a separate process; it reads
        # a separate synthetic effect ledger, never the producer's status field.
        self.write(self.artifacts / "effects.json", {"calls": [], "effects": []})
        subprocess.run([sys.executable, "-c", "import json,sys; from pathlib import Path; "
                        "p=Path(sys.argv[1]); e=json.loads((p/'effects.json').read_text()); "
                        "(p/'observation.json').write_text(json.dumps(dict(source_sha=sys.argv[2], "
                        "criterion='C1', observer='separate-ledger-observer', forbidden_calls=len(e['calls']), "
                        "forbidden_effects=len(e['effects']), expected=[], observed=e['effects'])))",
                        str(self.artifacts), self.sha], check=True)
        (self.artifacts / "output.bin").write_bytes(b"synthetic actual bytes")
        for key in ("toolchain", "config", "fixtures", "dependencies"):
            (self.artifacts / (key + ".json")).write_text("synthetic locked " + key)
        self.receipt = {"source_sha": self.sha, "source_clean": True, "criterion": "C1",
                        "evidence_class": "component", "status": "passed", "producer": "test-producer",
                        "command": ["never-execute-me", "$(touch forbidden)"],
                        "inputs": {key: self.ref(self.artifacts / (key + ".json"))
                                   for key in ("toolchain", "config", "fixtures", "dependencies")},
                        "artifacts": [self.ref(self.artifacts / "output.bin")],
                        "observation": self.ref(self.artifacts / "observation.json")}
        self.manifest = {"version": engine.VERSION, "composition_root": "repo", "artifact_root": "artifacts",
                         "sources": {"composition": {"root": "repo", "main_sha": self.sha, "kind": "current_main"}},
                         "criteria": [{"id": "C1", "issue": "synthetic#44", "source": "composition",
                                       "capability": "bounded", "evidence_class": "component"}],
                         "capabilities": {"bounded": {"source": "composition", "criterion": "C1", "status": "passed"}},
                         "claims": [{"criterion": "C1", "file": self.ref(self.repo / "STATUS.json"), "selector": ["bounded"]},
                                    {"criterion": "C1", "file": self.ref(self.repo / "README.md"),
                                     "marker": "Synthetic criterion: passed", "status": "passed"}]}
        self.save_receipt()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value, sort_keys=True))

    @staticmethod
    def ref(path):
        return {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def save_receipt(self):
        self.write(self.artifacts / "receipt.json", self.receipt)
        self.manifest["capabilities"]["bounded"]["receipt"] = self.ref(self.artifacts / "receipt.json")

    def run_engine(self):
        self.save_receipt()
        return engine.reconcile(self.manifest, self.base)

    def assert_rejected(self, reason):
        result = self.run_engine()
        self.assertNotEqual(result["status"], "passed")
        self.assertIn(reason, result["criteria"][0]["reasons"])

    def test_exact_source_positive_fresh_process_and_no_effects(self):
        # Observe actual process invocations independently: receipt commands are inert.
        original = subprocess.check_output
        calls = []
        def observe(argv, **kwargs):
            calls.append(argv)
            return original(argv, **kwargs)
        with mock.patch.object(engine.subprocess, "check_output", side_effect=observe):
            result = self.run_engine()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(calls)
        self.assertTrue(all(call[0] == "git" and call[1] == "--no-optional-locks" for call in calls))
        self.assertEqual(json.loads((self.artifacts / "effects.json").read_text()), {"calls": [], "effects": []})
        manifest = self.base / "manifest.json"
        self.write(manifest, self.manifest)
        output = subprocess.run([sys.executable, str(TOOL), str(manifest)], capture_output=True, text=True)
        self.assertEqual(output.returncode, 0, output.stdout)
        self.assertEqual(json.loads(output.stdout)["system_acceptance"], "not_inferred")

    def test_stale_sha(self):
        self.receipt["source_sha"] = "c" * 40
        self.assert_rejected("stale_receipt_sha")

    def test_component_pin_positive_and_changed_component_rejected(self):
        core = self.base / "core"
        core.mkdir()
        def core_git(*args):
            return subprocess.check_output(["git", "-C", str(core), *args], text=True).strip()
        core_git("init", "-q")
        core_git("config", "user.email", "synthetic@example.invalid")
        core_git("config", "user.name", "Synthetic Fixture")
        (core / "source.txt").write_text("synthetic component")
        core_git("add", ".")
        core_git("commit", "-qm", "Component fixture")
        core_sha = core_git("rev-parse", "HEAD")
        lock_path = self.repo / "composition.lock.json"
        lock = json.loads(lock_path.read_text())
        lock["components"][0]["commit"] = core_sha
        self.write(lock_path, lock)
        self.git("add", "composition.lock.json")
        self.git("update-index", "--cacheinfo", "160000," + core_sha + ",components/core")
        self.git("commit", "-qm", "Pin fixture component")
        self.manifest["sources"]["composition"]["main_sha"] = self.git("rev-parse", "HEAD")
        self.manifest["sources"]["core"] = {"root": "core", "main_sha": core_sha, "kind": "current_main"}
        self.manifest["criteria"][0]["source"] = "core"
        self.manifest["capabilities"]["bounded"]["source"] = "core"
        self.receipt["source_sha"] = core_sha
        observation_path = self.artifacts / "observation.json"
        observation = json.loads(observation_path.read_text())
        observation["source_sha"] = core_sha
        self.write(observation_path, observation)
        self.receipt["observation"] = self.ref(observation_path)
        self.assertEqual(self.run_engine()["status"], "passed")
        core_git("commit", "--allow-empty", "-qm", "Unqualified newer component")
        core_sha = core_git("rev-parse", "HEAD")
        self.manifest["sources"]["core"]["main_sha"] = core_sha
        self.receipt["source_sha"] = core_sha
        observation["source_sha"] = core_sha
        self.write(observation_path, observation)
        self.receipt["observation"] = self.ref(observation_path)
        self.assert_rejected("not_composition_pin")

    def test_changed_main(self):
        self.manifest["sources"]["composition"]["main_sha"] = "c" * 40
        self.assert_rejected("not_current_main")

    def test_missing_artifact(self):
        (self.artifacts / "output.bin").unlink()
        self.assert_rejected("missing_artifact")

    def test_changed_artifact(self):
        (self.artifacts / "output.bin").write_bytes(b"altered")
        self.assert_rejected("artifact_digest_mismatch")

    def test_missing_receipt(self):
        self.save_receipt()
        (self.artifacts / "receipt.json").unlink()
        result = engine.reconcile(self.manifest, self.base)
        self.assertIn("missing_artifact", result["criteria"][0]["reasons"])

    def test_dirty_source_including_untracked(self):
        (self.repo / "untracked.txt").write_text("synthetic")
        self.assert_rejected("dirty_source")

    def test_dirty_receipt(self):
        self.receipt["source_clean"] = False
        self.assert_rejected("dirty_receipt")

    def test_draft_and_historical(self):
        for kind in ("draft", "historical"):
            with self.subTest(kind=kind):
                self.manifest["sources"]["composition"]["kind"] = kind
                self.assert_rejected(kind + "_source")

    def test_statuses_remain_distinct_and_non_success(self):
        for status in ("failed", "blocked", "not_run", "unknown"):
            with self.subTest(status=status):
                self.receipt["status"] = status
                self.manifest["capabilities"]["bounded"]["status"] = status
                result = self.run_engine()
                self.assertEqual(result["criteria"][0]["status"], status)
                self.assertNotEqual(result["status"], "passed")

    def test_stale_readme_and_status(self):
        for index, field in ((0, "selector"), (1, "status")):
            with self.subTest(index=index):
                old = copy.deepcopy(self.manifest["claims"][index])
                self.manifest["claims"][index][field] = ["missing"] if index == 0 else "blocked"
                result = self.run_engine()
                self.assertEqual(result["claims"][index]["status"], "failed")
                self.assertNotEqual(result["status"], "passed")
                self.manifest["claims"][index] = old

    def test_stale_claim_bytes(self):
        self.manifest["claims"][0]["file"]["sha256"] = "d" * 64
        result = self.run_engine()
        self.assertEqual(result["claims"][0]["reason"], "artifact_digest_mismatch")

    def test_forbidden_call_effect_and_independence(self):
        path = self.artifacts / "observation.json"
        original = json.loads(path.read_text())
        for field, value, reason in (("forbidden_calls", 1, "forbidden_calls_observed"),
                                     ("forbidden_effects", 1, "forbidden_effects_observed"),
                                     ("observer", "test-producer", "not_independent_observer")):
            with self.subTest(field=field):
                observation = dict(original, **{field: value})
                self.write(path, observation)
                self.receipt["observation"] = self.ref(path)
                self.assert_rejected(reason)

    def test_scope_identity_and_input_hashes(self):
        self.receipt["inputs"].pop("fixtures")
        self.assert_rejected("missing_or_malformed_evidence")

    def test_wrong_evidence_class(self):
        self.receipt["evidence_class"] = "synthetic"
        self.assert_rejected("evidence_class_mismatch")

    def test_path_escape(self):
        self.receipt["artifacts"][0]["path"] = "../repo/README.md"
        self.assert_rejected("path_outside_root")

    def test_gitlink_lock_disagreement(self):
        self.git("update-index", "--cacheinfo", "160000," + "c" * 40 + ",components/core")
        with self.assertRaisesRegex(ValueError, "gitlink_lock_mismatch"):
            self.run_engine()

    def test_source_change_during_artifact_scan(self):
        original = engine.digest_file
        def mutate(root, record):
            path = original(root, record)
            if record["path"] == "output.bin":
                (self.repo / "late-untracked.txt").write_text("synthetic concurrent change")
            return path
        with mock.patch.object(engine, "digest_file", side_effect=mutate):
            self.assert_rejected("source_changed_or_dirty_during_check")

    def test_source_change_during_claim_scan(self):
        original = engine.digest_file
        def mutate(root, record):
            data = original(root, record)
            if root.resolve() == self.repo.resolve() and record["path"] == "STATUS.json":
                (self.repo / "late-claim.txt").write_text("synthetic concurrent change")
            return data
        with mock.patch.object(engine, "digest_file", side_effect=mutate):
            self.assert_rejected("source_changed_or_dirty_during_check")

    def test_receipt_parse_uses_verified_bytes(self):
        original = engine.digest_file
        def mutate(root, record):
            data = original(root, record)
            if record["path"] == "receipt.json":
                altered = dict(self.receipt, status="passed")
                self.write(self.artifacts / "receipt.json", altered)
            return data
        self.receipt["status"] = "blocked"
        self.manifest["capabilities"]["bounded"]["status"] = "blocked"
        with mock.patch.object(engine, "digest_file", side_effect=mutate):
            self.assert_rejected("receipt_blocked")

    def test_invalid_seven_component_set(self):
        path = self.repo / "composition.lock.json"
        lock = json.loads(path.read_text())
        lock["components"][0]["component"] = "unknown"
        self.write(path, lock)
        with self.assertRaisesRegex(ValueError, "invalid_pin_set"):
            self.run_engine()

    def test_empty_criteria_and_duplicate_json_fail_closed(self):
        self.manifest["criteria"] = []
        with self.assertRaisesRegex(ValueError, "empty_criteria"):
            self.run_engine()
        path = self.base / "duplicate.json"
        path.write_text('{"status":"blocked","status":"passed"}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            engine.load_json(path)


if __name__ == "__main__":
    unittest.main()
