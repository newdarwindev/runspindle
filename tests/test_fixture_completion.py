"""Full fixture-only fault oracle, compatibility and cancellation contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tools.fixture_compatibility import compare

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "fixtures/v1"
SPEC = importlib.util.spec_from_file_location(
    "completion_fixturekit", BUNDLE / "fixturekit.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("missing fixture loader")
kit: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)


class CompletionTests(unittest.TestCase):
    def test_fault_traces_from_separate_model_effect_spy(self) -> None:
        # Executes a deliberately small in-memory model. No durable recovery claim.
        cases = kit.load_json(BUNDLE / "faults.json")["cases"]
        labels = {
            "duplicate": "same-task-and-operation",
            "reorder": "older-observation-cannot-replace-newer",
            "timeout": "unknown-no-blind-retry",
            "partial-response": "unknown-no-delivered-state",
            "retry": "new-attempt-same-operation",
            "restart": "blocked-until-real-durable-adapter",
            "uncertain-effect": "unknown-no-resubmit",
        }
        for case in cases:
            for defect in (
                None,
                "extra-effect",
                "wrong-order",
                "regress-sequence",
                "unauthorized-retry",
                "wrong-effect-identity",
            ):
                spy = kit.Spy(["send", "commit"])
                identity = {
                    "task_id": "synthetic-task",
                    "operation_id": "synthetic-operation",
                }
                calls: list[dict[str, Any]] = []
                steps: list[dict[str, Any]] = []
                state, attempt, sequence = "new", 1, 0
                seen: set[str] = set()

                def effect(operation: str) -> None:
                    actual_identity = (
                        {**identity, "operation_id": "wrong-operation"}
                        if defect == "wrong-effect-identity"
                        else identity
                    )
                    spy.call(operation, actual_identity)
                    observed_operation, observed_identity = spy.calls[-1]
                    calls.append(
                        {
                            "operation": observed_operation,
                            "attempt": attempt,
                            "identity": observed_identity,
                        }
                    )

                for instruction in case["schedule"]:
                    if instruction.startswith("deliver:"):
                        if instruction not in seen or defect == "extra-effect":
                            effect("send")
                            seen.add(instruction)
                        state = "admitted"
                    elif instruction.startswith("sequence:"):
                        value = int(instruction.split(":")[1])
                        sequence = (
                            value
                            if defect == "regress-sequence"
                            else max(sequence, value)
                        )
                        state = "observed"
                    elif instruction == "send":
                        effect("send")
                        state = "sent"
                    elif instruction == "explicit-rejection":
                        state = "rejected"
                        if defect == "unauthorized-retry":
                            effect("send")
                    elif instruction == "retry-authorized":
                        self.assertEqual(state, "rejected")
                        attempt += 1
                        effect("send")
                        state = "sent"
                    elif instruction == "commit":
                        effect("commit")
                        state = "committed"
                    elif instruction == "stop":
                        state = "stopped"
                    elif instruction == "fresh-process-read":
                        state = "blocked"  # Model has no durable recovery adapter.
                    else:
                        state = "unknown"
                    steps.append(
                        {
                            "input": instruction,
                            "state": state,
                            "effect_calls": len(spy.calls),
                            "attempt": attempt,
                            "sequence": sequence,
                        }
                    )
                order_changed = steps != list(reversed(steps))
                if defect == "wrong-order":
                    steps.reverse()
                trace: dict[str, Any] = {
                    "case": case["id"],
                    "classification": "model_schedule_not_runtime_recovery",
                    "effect_calls": len(spy.calls),
                    "observation": labels[case["id"]],
                    "identity": identity,
                    "steps": steps,
                    "calls": calls,
                }
                relevant = (
                    (defect == "wrong-effect-identity" and bool(calls))
                    or (defect == "wrong-order" and order_changed)
                    or (
                        defect,
                        case["id"],
                    )
                    in {
                        ("extra-effect", "duplicate"),
                        ("regress-sequence", "reorder"),
                        ("unauthorized-retry", "retry"),
                    }
                )
                if relevant:
                    with self.assertRaises(kit.ContractError):
                        kit.assert_fault_trace(case["id"], trace)
                else:
                    self.assertTrue(kit.assert_fault_trace(case["id"], trace))
                    for field, malformed in (
                        ("effect_calls", True),
                        ("classification", "runtime_passed"),
                    ):
                        with self.assertRaises(kit.ContractError):
                            kit.assert_fault_trace(
                                case["id"], {**trace, field: malformed}
                            )
                    wrong = copy.deepcopy(trace)
                    wrong["identity"]["operation_id"] = "other-operation"
                    with self.assertRaises(kit.ContractError):
                        kit.assert_fault_trace(case["id"], wrong)

    def test_compatibility_reports_change_without_executing_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old, new = Path(directory) / "old", Path(directory) / "new"
            kit.export_bundle("core", old)
            kit.export_bundle("core", new)
            self.assertFalse(compare(old, new)["review_required"])
            path = new / "fixturekit.py"
            path.write_text('raise AssertionError("candidate code must not run")\n')
            import hashlib

            manifest_path = new / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["fixturekit.py"] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            a, b = compare(old, new), compare(old, new)
            self.assertEqual(a, b)
            self.assertTrue(a["review_required"])
            self.assertEqual([x["file"] for x in a["changes"]], ["fixturekit.py"])
            self.assertFalse(a["automatic_pin_upgrade"])
            path.write_text("tampered")
            with self.assertRaisesRegex(ValueError, "digest"):
                compare(old, new)

    def test_compatibility_metadata_inventory_and_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old, new = Path(directory) / "old", Path(directory) / "new"
            kit.export_bundle("core", old)
            kit.export_bundle("core", new)
            path = new / "manifest.json"
            original = path.read_text()
            for field, value in (
                ("component", "host"),
                ("origin_manifest_sha256", "0" * 64),
                ("components", {"host": []}),
                ("new_nullable_field", None),
            ):
                manifest = json.loads(original)
                manifest[field] = value
                path.write_text(json.dumps(manifest))
                result = compare(old, new)
                self.assertTrue(result["review_required"])
                self.assertEqual(result["metadata_changes"][0]["field"], field)
            path.write_text(original)
            (new / "extra").write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "inventory"):
                compare(old, new)
            (new / "extra").unlink()
            path.unlink()
            path.symlink_to(old / "manifest.json")
            with self.assertRaisesRegex(ValueError, "manifest"):
                compare(old, new)

    def test_export_cancel_removes_partial_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "cancelled"
            original = shutil.copyfile

            def interrupt(source: Any, target: Any) -> Any:
                original(source, target)
                raise KeyboardInterrupt("synthetic cancellation")

            with patch.object(kit.shutil, "copyfile", side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    kit.export_bundle("host", destination)
            self.assertFalse(destination.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX graceful SIGTERM contract")
    def test_fresh_process_graceful_cancellation_cleans_temporary_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "ready"
            code = """import importlib.util, pathlib, signal, sys, time
spec=importlib.util.spec_from_file_location("kit",sys.argv[1]); kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
def cancel(*args): raise SystemExit(143)
signal.signal(signal.SIGTERM,cancel)
with kit.temporary_store() as path:
 pathlib.Path(sys.argv[2]).write_text(str(path))
 while True: time.sleep(.01)
"""
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    code,
                    str(BUNDLE / "fixturekit.py"),
                    str(marker),
                ],
                env={**os.environ, "TMPDIR": directory},
            )
            try:
                deadline = time.monotonic() + 5
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(), "child readiness timeout")
                owned = Path(marker.read_text())
                self.assertTrue(owned.is_dir())
                process.send_signal(signal.SIGTERM)
                self.assertEqual(process.wait(timeout=5), 143)
                self.assertFalse(owned.exists())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
