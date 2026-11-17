"""Negative matrix admission checks with disposable synthetic Git repositories."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tools import qualify_fixture_consumers as matrix

ROOT = Path(__file__).resolve().parents[1]


class ConsumerMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="fixture-matrix-negative-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.lock = json.loads((ROOT / "fixtures/consumer-lock.json").read_text())
        self.checkouts: dict[str, str] = {}
        source = ROOT / "fixtures/v1/fixturekit.py"
        spec = importlib.util.spec_from_file_location("matrix_test_kit", source)
        if spec is None or spec.loader is None:
            self.fail("missing fixture loader")
        kit: Any = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(kit)
        for component, record in self.lock["components"].items():
            root = self.root / component
            (root / "fixtures").mkdir(parents=True)
            kit.export_bundle(component, root / "fixtures/shared-v1")
            manifest = root / "fixtures/shared-v1/manifest.json"
            pin = {
                (
                    "composition_commit" if component == "console" else "source_commit"
                ): self.lock["source_commit"],
                "subset_manifest_sha256": matrix.sha(manifest.read_bytes()),
            }
            (root / "fixtures/shared-v1.pin.json").write_text(json.dumps(pin))
            for name in record["files"]:
                path = root / name
                if path.exists():
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                if name.endswith("origin-manifest.json"):
                    path.write_bytes((ROOT / "fixtures/v1/manifest.json").read_bytes())
                else:
                    path.write_text('"""Synthetic matrix admission test input."""\n')
            self.git(root, "init", "-q")
            self.git(root, "add", ".")
            self.git(
                root,
                "-c",
                "user.name=Synthetic Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "fixture",
            )
            record["commit"] = self.git(root, "rev-parse", "HEAD").strip()
            record["tree"] = self.git(root, "rev-parse", "HEAD^{tree}").strip()
            record["files"] = {
                name: matrix.sha((root / name).read_bytes()) for name in record["files"]
            }
            self.checkouts[component] = str(root)

    @staticmethod
    def git(root: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            timeout=10,
            stderr=subprocess.PIPE,
        )

    def reject(self, lock: dict[str, Any] | None = None) -> None:
        # No consumer Python process may run for rejected admission input.
        actual_run = subprocess.run
        launches = []

        def launch(command: list[str], **kwargs: Any) -> Any:
            if command[0] == "git":
                return actual_run(command, **kwargs)
            launches.append(command)
            raise AssertionError("consumer execution before admission rejection")

        with patch.object(subprocess, "run", side_effect=launch):
            with self.assertRaises(
                (ValueError, KeyError, subprocess.CalledProcessError)
            ):
                matrix.qualify(self.lock if lock is None else lock, self.checkouts)
        self.assertEqual(launches, [])

    def test_exact_synthetic_inputs_reach_only_isolated_child_boundary(self) -> None:
        # This is an admission unit test, not a substitute conformance run.
        actual_run = subprocess.run
        children = []

        def launch(command: list[str], **kwargs: Any) -> Any:
            if command[0] == "git":
                return actual_run(command, **kwargs)
            isolated = Path(kwargs["cwd"])
            self.assertFalse((isolated / ".git").exists())
            self.assertTrue((isolated / "sitecustomize.py").is_file())
            self.assertEqual(kwargs["env"]["PYTHONPATH"], str(isolated))
            children.append(isolated)
            return subprocess.CompletedProcess(
                command, 0, "", "Ran 2 tests in 0.001s\nOK\n"
            )

        with patch.object(subprocess, "run", side_effect=launch):
            result = matrix.qualify(self.lock, self.checkouts)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(len(children), 28)
        self.assertTrue(all(not path.exists() for path in children))

    def test_root_data_must_match_manifest_even_for_unselected_kind(self) -> None:
        root = self.root / "root-source"
        shutil.copytree(ROOT / "fixtures/v1", root / "fixtures/v1")
        path = root / "fixtures/v1/golden.json"
        rows = json.loads(path.read_text())
        rows.append({"kind": "unknown.synthetic.kind"})
        path.write_text(json.dumps(rows))
        actual_output = subprocess.check_output

        def output(command: list[str], **kwargs: Any) -> Any:
            if command[:3] == ["git", "-C", str(root)]:
                command = ["git", "-C", str(ROOT), *command[3:]]
            return actual_output(command, **kwargs)

        with (
            patch.object(matrix, "ROOT", root),
            patch.object(subprocess, "check_output", side_effect=output),
        ):
            self.reject()

    def test_unsuccessful_or_interrupted_child_cleans_isolation(self) -> None:
        actual_run = subprocess.run
        outcomes: list[Any] = [
            (0, "Ran 0 tests in 0.001s\nOK\n"),
            (0, "Ran 2 tests in 0.001s\nOK (skipped=1)\n"),
            (1, "Ran 2 tests in 0.001s\nFAILED\n"),
            "network",
            "timeout",
            "cancel",
            "sigterm",
        ]
        for outcome in outcomes:
            children = []

            def launch(command: list[str], **kwargs: Any) -> Any:
                if command[0] == "git":
                    return actual_run(command, **kwargs)
                children.append(Path(kwargs["cwd"]))
                if outcome == "timeout":
                    raise subprocess.TimeoutExpired(command, 60)
                if outcome == "sigterm":
                    matrix.cancel_on_sigterm(signal.SIGTERM, None)
                if outcome == "cancel":
                    raise KeyboardInterrupt("synthetic cancellation")
                if outcome == "network":
                    Path(kwargs["env"]["FIXTURE_NETWORK_LEDGER"]).touch()
                    code, stderr = 0, "Ran 2 tests in 0.001s\nOK\n"
                else:
                    code, stderr = outcome
                return subprocess.CompletedProcess(command, code, "", stderr)

            with (
                self.subTest(outcome=outcome),
                patch.object(subprocess, "run", side_effect=launch),
            ):
                with self.assertRaises(
                    (
                        ValueError,
                        subprocess.TimeoutExpired,
                        KeyboardInterrupt,
                        SystemExit,
                    )
                ):
                    matrix.qualify(self.lock, self.checkouts)
            self.assertEqual(len(children), 1)
            self.assertFalse(children[0].exists())

    def test_missing_consumer_and_unknown_lock_version_rejected(self) -> None:
        missing = copy.deepcopy(self.lock)
        del missing["components"]["host"]
        self.reject(missing)
        wrong = copy.deepcopy(self.lock)
        wrong["schema"] = "runspindle.fixture-consumer-lock.v99"
        self.reject(wrong)

    def test_unreviewed_source_commit_and_repository_rejected(self) -> None:
        wrong = copy.deepcopy(self.lock)
        wrong["source_commit"] = "0" * 40
        self.reject(wrong)
        wrong = copy.deepcopy(self.lock)
        wrong["components"]["browser"]["repository"] = "unreviewed/browser"
        self.reject(wrong)

    def test_required_test_cannot_be_omitted_from_lock(self) -> None:
        del self.lock["components"]["browser"]["files"][
            "tests/test_shared_fixture_upgrade.py"
        ]
        self.reject()

    def test_worktree_bytes_cannot_masquerade_as_committed_source(self) -> None:
        name = "tests/test_shared_fixture_upgrade.py"
        path = Path(self.checkouts["browser"]) / name
        path.write_text(path.read_text() + "changed = True\n")
        self.lock["components"]["browser"]["files"][name] = matrix.sha(
            path.read_bytes()
        )
        self.reject()

    def test_changed_bytes_and_git_identity_are_rejected(self) -> None:
        name = "tests/test_shared_fixture_upgrade.py"
        path = Path(self.checkouts["browser"]) / name
        path.write_text(path.read_text() + "changed = True\n")
        self.reject()
        wrong = copy.deepcopy(self.lock)
        wrong["components"]["browser"]["commit"] = "0" * 40
        self.reject(wrong)

    def test_linked_or_escaped_selected_source_is_rejected(self) -> None:
        name = "tests/test_shared_fixture_upgrade.py"
        path = Path(self.checkouts["browser"]) / name
        content = path.read_bytes()
        target = self.root / "outside.py"
        target.write_bytes(content)
        path.unlink()
        path.symlink_to(target)
        self.reject()
        wrong = copy.deepcopy(self.lock)
        wrong["components"]["browser"]["files"]["../outside.py"] = matrix.sha(content)
        self.reject(wrong)
