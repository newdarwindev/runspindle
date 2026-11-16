"""Actual temporary Git stores, synthetic receipts and independent effect observations."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

TOOL = Path(
    os.environ.get(
        "RUNSPINDLE_RECONCILER",
        Path(__file__).resolve().parents[1] / "tools/reconcile_evidence.py",
    )
)
spec = importlib.util.spec_from_file_location("reconciler", TOOL)
assert spec is not None and spec.loader is not None
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class ReconciliationTests(unittest.TestCase):
    def run(
        self, result: unittest.TestResult | None = None
    ) -> unittest.TestResult | None:
        try:
            return super().run(result)
        except KeyboardInterrupt as primary:
            # unittest skips registered cleanups when KeyboardInterrupt escapes.
            # Ordinary success/failure cleanup remains under unittest's ownership.
            owned = getattr(self, "temp", None)
            if owned is not None:
                try:
                    owned.cleanup()
                except Exception as error:
                    primary.add_note(
                        f"Owned fixture cleanup failed: {type(error).__name__}"
                    )
            raise

    def setUp(self) -> None:
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
        for name in (
            "core",
            "host",
            "browser",
            "tether",
            "refinery",
            "console",
            "platform",
        ):
            pin = {"component": name, "commit": "a" * 40, "path": "components/" + name}
            pins.append(pin)
            (self.repo / pin["path"]).mkdir(parents=True)
            self.git(
                "update-index",
                "--add",
                "--cacheinfo",
                "160000," + pin["commit"] + "," + pin["path"],
            )
        self.write(
            self.repo / "composition.lock.json",
            {"schema_version": 1, "components": pins},
        )
        self.write(self.repo / "STATUS.json", {"bounded": "passed"})
        (self.repo / "README.md").write_text("Synthetic criterion: passed\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Synthetic fixture")
        self.sha = self.git("rev-parse", "HEAD")
        # The independent observation is produced in a separate process; it reads
        # a separate synthetic effect ledger, never the producer's status field.
        self.write(self.artifacts / "effects.json", {"calls": [], "effects": []})
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import json,sys; from pathlib import Path; "
                "p=Path(sys.argv[1]); e=json.loads((p/'effects.json').read_text()); "
                "(p/'observation.json').write_text(json.dumps(dict(source_sha=sys.argv[2], "
                "criterion='C1', observer='separate-ledger-observer', forbidden_calls=len(e['calls']), "
                "forbidden_effects=len(e['effects']), expected=[], observed=e['effects'])))",
                str(self.artifacts),
                self.sha,
            ],
            check=True,
        )
        (self.artifacts / "output.bin").write_bytes(b"synthetic actual bytes")
        for key in ("toolchain", "config", "fixtures", "dependencies"):
            (self.artifacts / (key + ".json")).write_text("synthetic locked " + key)
        self.receipt: dict[str, Any] = {
            "source_sha": self.sha,
            "source_clean": True,
            "criterion": "C1",
            "evidence_class": "component",
            "status": "passed",
            "producer": "test-producer",
            "command": ["never-execute-me", "$(touch forbidden)"],
            "inputs": {
                key: self.ref(self.artifacts / (key + ".json"))
                for key in ("toolchain", "config", "fixtures", "dependencies")
            },
            "artifacts": [self.ref(self.artifacts / "output.bin")],
            "observation": self.ref(self.artifacts / "observation.json"),
        }
        self.manifest: dict[str, Any] = {
            "version": engine.VERSION,
            "composition_root": "repo",
            "artifact_root": "artifacts",
            "sources": {
                "composition": {
                    "root": "repo",
                    "main_sha": self.sha,
                    "kind": "current_main",
                }
            },
            "criteria": [
                {
                    "id": "C1",
                    "issue": "synthetic#44",
                    "source": "composition",
                    "capability": "bounded",
                    "evidence_class": "component",
                }
            ],
            "capabilities": {
                "bounded": {
                    "source": "composition",
                    "criterion": "C1",
                    "status": "passed",
                }
            },
            "claims": [
                {
                    "criterion": "C1",
                    "file": self.ref(self.repo / "STATUS.json"),
                    "selector": ["bounded"],
                },
                {
                    "criterion": "C1",
                    "file": self.ref(self.repo / "README.md"),
                    "marker": "Synthetic criterion: passed",
                    "status": "passed",
                },
            ],
        }
        self.save_receipt()

    def git(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True
        ).strip()

    @staticmethod
    def write(path: Path, value: Any) -> None:
        path.write_text(json.dumps(value, sort_keys=True))

    @staticmethod
    def ref(path: Path) -> dict[str, str]:
        return {
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    def save_receipt(self) -> None:
        self.write(self.artifacts / "receipt.json", self.receipt)
        self.manifest["capabilities"]["bounded"]["receipt"] = self.ref(
            self.artifacts / "receipt.json"
        )

    def run_engine(self) -> Any:
        self.save_receipt()
        return engine.reconcile(self.manifest, self.base)

    def assert_rejected(self, reason: str) -> None:
        result = self.run_engine()
        self.assertNotEqual(result["status"], "passed")
        self.assertIn(reason, result["criteria"][0]["reasons"])

    def test_exact_source_positive_fresh_process_and_no_effects(self) -> None:
        # Observe actual process invocations independently: receipt commands are inert.
        original = subprocess.check_output
        calls = []

        def observe(argv: Any, **kwargs: Any) -> Any:
            calls.append(argv)
            return original(argv, **kwargs)

        with mock.patch.object(engine.subprocess, "check_output", side_effect=observe):
            result = self.run_engine()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(calls)
        self.assertTrue(
            all(call[0] == "git" and call[1] == "--no-optional-locks" for call in calls)
        )
        self.assertEqual(
            json.loads((self.artifacts / "effects.json").read_text()),
            {"calls": [], "effects": []},
        )
        manifest = self.base / "manifest.json"
        self.write(manifest, self.manifest)
        output = subprocess.run(
            [sys.executable, str(TOOL), str(manifest)], capture_output=True, text=True
        )
        self.assertEqual(output.returncode, 0, output.stdout)
        self.assertEqual(json.loads(output.stdout)["system_acceptance"], "not_inferred")

    def test_stale_sha(self) -> None:
        self.receipt["source_sha"] = "c" * 40
        self.assert_rejected("stale_receipt_sha")

    def test_component_pin_positive_and_changed_component_rejected(self) -> None:
        core = self.base / "core"
        core.mkdir()

        def core_git(*args: str) -> str:
            return subprocess.check_output(
                ["git", "-C", str(core), *args], text=True
            ).strip()

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
        self.git(
            "update-index", "--cacheinfo", "160000," + core_sha + ",components/core"
        )
        self.git("commit", "-qm", "Pin fixture component")
        self.manifest["sources"]["composition"]["main_sha"] = self.git(
            "rev-parse", "HEAD"
        )
        self.manifest["sources"]["core"] = {
            "root": "core",
            "main_sha": core_sha,
            "kind": "current_main",
        }
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

    def test_changed_main(self) -> None:
        self.manifest["sources"]["composition"]["main_sha"] = "c" * 40
        self.assert_rejected("not_current_main")

    def test_missing_artifact(self) -> None:
        (self.artifacts / "output.bin").unlink()
        self.assert_rejected("missing_artifact")

    def test_changed_artifact(self) -> None:
        (self.artifacts / "output.bin").write_bytes(b"altered")
        self.assert_rejected("artifact_digest_mismatch")

    def test_missing_receipt(self) -> None:
        self.save_receipt()
        (self.artifacts / "receipt.json").unlink()
        result = engine.reconcile(self.manifest, self.base)
        self.assertIn("missing_artifact", result["criteria"][0]["reasons"])

    def test_dirty_source_including_untracked(self) -> None:
        (self.repo / "untracked.txt").write_text("synthetic")
        self.assert_rejected("dirty_source")

    def test_dirty_receipt(self) -> None:
        self.receipt["source_clean"] = False
        self.assert_rejected("dirty_receipt")

    def test_draft_and_historical(self) -> None:
        for kind in ("draft", "historical"):
            with self.subTest(kind=kind):
                self.manifest["sources"]["composition"]["kind"] = kind
                self.assert_rejected(kind + "_source")

    def test_statuses_remain_distinct_and_non_success(self) -> None:
        for status in ("failed", "blocked", "not_run", "unknown"):
            with self.subTest(status=status):
                self.receipt["status"] = status
                self.manifest["capabilities"]["bounded"]["status"] = status
                result = self.run_engine()
                self.assertEqual(result["criteria"][0]["status"], status)
                self.assertNotEqual(result["status"], "passed")

    def test_stale_readme_and_status(self) -> None:
        for index, field in ((0, "selector"), (1, "status")):
            with self.subTest(index=index):
                old = copy.deepcopy(self.manifest["claims"][index])
                self.manifest["claims"][index][field] = (
                    ["missing"] if index == 0 else "blocked"
                )
                result = self.run_engine()
                self.assertEqual(result["claims"][index]["status"], "failed")
                self.assertNotEqual(result["status"], "passed")
                self.manifest["claims"][index] = old

    def test_stale_claim_bytes(self) -> None:
        self.manifest["claims"][0]["file"]["sha256"] = "d" * 64
        result = self.run_engine()
        self.assertEqual(result["claims"][0]["reason"], "artifact_digest_mismatch")

    def test_forbidden_call_effect_and_independence(self) -> None:
        path = self.artifacts / "observation.json"
        original = json.loads(path.read_text())
        for field, value, reason in (
            ("forbidden_calls", 1, "forbidden_calls_observed"),
            ("forbidden_effects", 1, "forbidden_effects_observed"),
            ("observer", "test-producer", "not_independent_observer"),
        ):
            with self.subTest(field=field):
                observation = dict(original, **{field: value})
                self.write(path, observation)
                self.receipt["observation"] = self.ref(path)
                self.assert_rejected(reason)

    def set_observation_values(self, expected: Any, observed: Any) -> None:
        path = self.artifacts / "observation.json"
        observation = json.loads(path.read_text())
        observation.update(expected=expected, observed=observed)
        self.write(path, observation)
        self.receipt["observation"] = self.ref(path)

    def test_boolean_number_observations_rejected(self) -> None:
        for expected, observed in (
            (False, 0),
            (0, False),
            (True, 1),
            (1.0, True),
            ({"accepted": False}, {"accepted": 0}),
            ([{"effects": [True]}], [{"effects": [1]}]),
        ):
            with self.subTest(expected=expected, observed=observed):
                self.set_observation_values(expected, observed)
                self.assert_rejected("effect_observation_mismatch")

    def test_matching_json_observation_semantics(self) -> None:
        for expected, observed in (
            (False, False),
            (True, True),
            (None, None),
            (1, 1.0),
            ({"effects": [True, 1, None]}, {"effects": [True, 1.0, None]}),
            ({"a": 1, "b": 2}, {"b": 2, "a": 1}),
        ):
            with self.subTest(expected=expected, observed=observed):
                self.set_observation_values(expected, observed)
                self.assertEqual(self.run_engine()["status"], "passed")

    def test_python_equality_mutation_detected(self) -> None:
        self.set_observation_values({"accepted": False}, {"accepted": 0})
        self.assert_rejected("effect_observation_mismatch")
        with mock.patch.object(
            engine, "observations_equal", side_effect=lambda left, right: left == right
        ):
            # Reintroducing the original equality bug defeats the rejection
            # assertion. This check requires that deliberate mutation to fail.
            with self.assertRaises(AssertionError):
                self.assert_rejected("effect_observation_mismatch")

    def test_non_finite_json_numbers_rejected(self) -> None:
        for number in ("NaN", "Infinity", "-Infinity", "1e9999", "-1e9999"):
            with self.subTest(number=number):
                for data in (number, '{"nested": [' + number + "]}"):
                    with self.assertRaisesRegex(ValueError, "non_finite_json_number"):
                        engine.decode_json(data.encode())
                path = self.artifacts / "observation.json"
                observation = json.loads(path.read_text())
                observation.update(expected="NUMBER", observed="NUMBER")
                path.write_text(json.dumps(observation).replace('"NUMBER"', number))
                self.receipt["observation"] = self.ref(path)
                self.assert_rejected("non_finite_json_number")
                # Restore valid bytes before constructing the next case.
                self.write(path, dict(observation, expected=[], observed=[]))

    def set_raw_observation(self, expected: str, observed: str) -> None:
        # Construct from literal JSON, not already-rounded Python floats.
        path = self.artifacts / "observation.json"
        value = {
            "source_sha": self.sha,
            "criterion": "C1",
            "observer": "separate-ledger-observer",
            "forbidden_calls": 0,
            "forbidden_effects": 0,
            "expected": "EXPECTED_TOKEN",
            "observed": "OBSERVED_TOKEN",
        }
        path.write_text(
            json.dumps(value)
            .replace('"EXPECTED_TOKEN"', expected)
            .replace('"OBSERVED_TOKEN"', observed)
        )
        self.receipt["observation"] = self.ref(path)

    def test_exact_numeric_observation_mismatches(self) -> None:
        for expected, observed in (
            ("9007199254740992.0", "9007199254740993.0"),
            ("9007199254740993", "9007199254740992.0"),
            ("0.1", "0.10000000000000001"),
            ("0", "1e-400"),
            ("-1e-400", "0.0"),
            ("1e-400", "2e-400"),
            ('{"effects": [0.1]}', '{"effects": [0.10000000000000001]}'),
            ("true", "1e0"),
            ("false", "0.0"),
        ):
            with self.subTest(expected=expected, observed=observed):
                self.set_raw_observation(expected, observed)
                self.assert_rejected("effect_observation_mismatch")

    def test_exact_numeric_equivalent_representations(self) -> None:
        for expected, observed in (
            ("1", "1.0"),
            ("100", "1e2"),
            ("0.1", "0.10000000000000000"),
            ("9007199254740993", "9007199254740993.0"),
            ("1e-400", "10e-401"),
            ("-0.0", "0"),
            ('{"effects": [1, 1e-400]}', '{"effects": [1.0, 10e-401]}'),
            ("1e-999999999", "10e-1000000000"),
        ):
            with self.subTest(expected=expected, observed=observed):
                self.set_raw_observation(expected, observed)
                result = self.run_engine()
                self.assertEqual(result["status"], "passed")
                json.dumps(result)  # Exact observation values never leak into reports.

    def test_exact_numeric_parser_boundaries_and_compatibility(self) -> None:
        self.assertIs(type(engine.decode_json(b"1.25")), float)
        self.assertIs(type(engine.decode_json(b"1", exact_numbers=True)), int)
        for number in ("NaN", "Infinity", "-Infinity", "1e9999", "-1e9999"):
            with self.subTest(number=number):
                self.set_raw_observation("0", '{"nested": [' + number + "]}")
                self.assert_rejected("non_finite_json_number")
        # A huge negative exponent stays compact, never expanding to a giant int.
        self.set_raw_observation("0", "1e-999999999")
        self.assert_rejected("effect_observation_mismatch")
        # Beyond Decimal's representable exponent range fails closed, not a crash.
        self.set_raw_observation("0", "1e-999999999999999999999999999999")
        self.assert_rejected("invalid_json_number")
        # Keep the standard JSON integer conversion guard; do not replace parse_int.
        with self.assertRaises(ValueError):
            engine.decode_json(("9" * 5000).encode(), exact_numbers=True)

    def test_float_decoder_mutation_detected(self) -> None:
        self.set_raw_observation("0.1", "0.10000000000000001")
        self.assert_rejected("effect_observation_mismatch")
        original = engine.decode_json

        def rounded(data: bytes, *, exact_numbers: bool = False) -> Any:
            return original(data)

        with mock.patch.object(engine, "decode_json", side_effect=rounded):
            self.assertEqual(self.run_engine()["status"], "passed")
            with self.assertRaises(AssertionError):
                self.assert_rejected("effect_observation_mismatch")

    def test_invalid_producer_identity_rejected(self) -> None:
        producer: Any
        for producer in (None, False, True, 0, 1, 1.0, [], {}, ""):
            with self.subTest(producer=producer):
                self.receipt["producer"] = producer
                self.assert_rejected("invalid_producer_identity")
        self.receipt.pop("producer")
        self.assert_rejected("missing_or_malformed_evidence")

    def test_valid_distinct_and_equal_producer_identity(self) -> None:
        self.receipt["producer"] = "separate-producer"
        self.assertEqual(self.run_engine()["status"], "passed")
        self.receipt["producer"] = "separate-ledger-observer"
        self.assert_rejected("not_independent_observer")

    def test_producer_identity_guard_mutation_detected(self) -> None:
        self.receipt["producer"] = None
        self.assert_rejected("invalid_producer_identity")
        source = TOOL.read_text()
        guard = 'isinstance(receipt["producer"], str) and bool(receipt["producer"])'
        self.assertEqual(source.count(guard), 1)
        mutant = types.ModuleType("invalid_producer_mutant")
        exec(
            compile(source.replace(guard, "True"), "synthetic-mutant", "exec"),
            mutant.__dict__,
        )
        result = mutant.reconcile(self.manifest, self.base)
        # Removing producer identity validation reproduces the original false pass.
        self.assertEqual(result["status"], "passed")
        with self.assertRaises(AssertionError):
            self.assertNotEqual(result["status"], "passed")

    def test_scope_identity_and_input_hashes(self) -> None:
        self.receipt["inputs"].pop("fixtures")
        self.assert_rejected("missing_or_malformed_evidence")

    def test_wrong_evidence_class(self) -> None:
        self.receipt["evidence_class"] = "synthetic"
        self.assert_rejected("evidence_class_mismatch")

    def test_path_escape(self) -> None:
        self.receipt["artifacts"][0]["path"] = "../repo/README.md"
        self.assert_rejected("path_outside_root")

    def test_gitlink_lock_disagreement(self) -> None:
        self.git(
            "update-index", "--cacheinfo", "160000," + "c" * 40 + ",components/core"
        )
        with self.assertRaisesRegex(ValueError, "gitlink_lock_mismatch"):
            self.run_engine()

    def test_source_change_during_artifact_scan(self) -> None:
        original = engine.digest_file

        def mutate(root: Path, record: dict[str, Any]) -> Any:
            path = original(root, record)
            if record["path"] == "output.bin":
                (self.repo / "late-untracked.txt").write_text(
                    "synthetic concurrent change"
                )
            return path

        with mock.patch.object(engine, "digest_file", side_effect=mutate):
            self.assert_rejected("source_changed_or_dirty_during_check")

    def test_source_change_during_claim_scan(self) -> None:
        original = engine.digest_file

        def mutate(root: Path, record: dict[str, Any]) -> Any:
            data = original(root, record)
            if (
                root.resolve() == self.repo.resolve()
                and record["path"] == "STATUS.json"
            ):
                (self.repo / "late-claim.txt").write_text("synthetic concurrent change")
            return data

        with mock.patch.object(engine, "digest_file", side_effect=mutate):
            self.assert_rejected("source_changed_or_dirty_during_check")

    def test_receipt_parse_uses_verified_bytes(self) -> None:
        original = engine.digest_file

        def mutate(root: Path, record: dict[str, Any]) -> Any:
            data = original(root, record)
            if record["path"] == "receipt.json":
                altered = dict(self.receipt, status="passed")
                self.write(self.artifacts / "receipt.json", altered)
            return data

        self.receipt["status"] = "blocked"
        self.manifest["capabilities"]["bounded"]["status"] = "blocked"
        with mock.patch.object(engine, "digest_file", side_effect=mutate):
            self.assert_rejected("receipt_blocked")

    def test_invalid_seven_component_set(self) -> None:
        path = self.repo / "composition.lock.json"
        lock = json.loads(path.read_text())
        lock["components"][0]["component"] = "unknown"
        self.write(path, lock)
        with self.assertRaisesRegex(ValueError, "invalid_pin_set"):
            self.run_engine()

    def test_empty_criteria_and_duplicate_json_fail_closed(self) -> None:
        self.manifest["criteria"] = []
        with self.assertRaisesRegex(ValueError, "empty_criteria"):
            self.run_engine()
        path = self.base / "duplicate.json"
        path.write_text('{"status":"blocked","status":"passed"}')
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            engine.load_json(path)


class FixtureLifecycleTests(unittest.TestCase):
    def exercise(self, phase: str) -> None:
        class RecordingResult(unittest.TestResult):
            def __init__(self) -> None:
                super().__init__()
                self.successes = 0

            def addSuccess(self, test: unittest.TestCase) -> None:
                self.successes += 1
                super().addSuccess(test)

        interruption = KeyboardInterrupt("scan cancelled")

        class Probe(ReconciliationTests):
            def git(self, *args: str) -> str:
                if phase == "setup_cancel":
                    raise KeyboardInterrupt("setup cancelled")
                return super().git(*args)

            def runTest(self) -> None:
                if phase == "assertion_failure":
                    self.fail("deliberate assertion failure")
                if phase in {"reconcile_cancel", "cleanup_failure"}:
                    with mock.patch.object(
                        engine,
                        "digest_file",
                        side_effect=interruption,
                    ):
                        self.run_engine()
                else:
                    self.assertEqual(self.run_engine()["status"], "passed")

        probe = Probe("runTest")
        result = RecordingResult()
        try:
            if phase in {"setup_cancel", "reconcile_cancel", "cleanup_failure"}:
                if phase == "cleanup_failure":
                    original_setup = probe.setUp

                    def setup_with_failed_cleanup() -> None:
                        original_setup()
                        self.patch_cleanup = mock.patch.object(
                            probe.temp, "cleanup", side_effect=OSError("cleanup failed")
                        )
                        self.patch_cleanup.start()

                    with mock.patch.object(
                        probe, "setUp", side_effect=setup_with_failed_cleanup
                    ):
                        with self.assertRaisesRegex(
                            KeyboardInterrupt, "scan cancelled"
                        ) as caught:
                            probe.run(result)
                    self.patch_cleanup.stop()
                    self.assertIn(
                        "Owned fixture cleanup failed: OSError",
                        caught.exception.__notes__,
                    )
                    self.assertIs(caught.exception, interruption)
                    self.assertTrue(probe.base.exists())
                    probe.temp.cleanup()
                else:
                    with self.assertRaises(KeyboardInterrupt):
                        probe.run(result)
                self.assertEqual(result.successes, 0)
            else:
                probe.run(result)
                self.assertEqual(result.successes, int(phase == "success"))
                self.assertEqual(
                    len(result.failures), int(phase == "assertion_failure")
                )
            self.assertFalse(probe.base.exists())
        finally:
            # Test-oracle safety net also cleans a deliberately broken implementation.
            if hasattr(self, "patch_cleanup"):
                self.patch_cleanup.stop()
            if hasattr(probe, "temp"):
                probe.temp.cleanup()

    def test_success_cleanup(self) -> None:
        self.exercise("success")

    def test_failure_cleanup(self) -> None:
        self.exercise("assertion_failure")

    def test_setup_cancellation_cleanup(self) -> None:
        self.exercise("setup_cancel")

    def test_reconciliation_cancellation_cleanup(self) -> None:
        self.exercise("reconcile_cancel")

    def test_cleanup_failure_preserves_cancellation(self) -> None:
        self.exercise("cleanup_failure")


if __name__ == "__main__":
    unittest.main()
