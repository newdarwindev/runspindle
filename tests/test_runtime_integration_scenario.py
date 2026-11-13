"""Synthetic mutations of independent ledger oracles; not runtime acceptance."""

import copy
import hashlib
import json
import pathlib
import py_compile
import os
import sqlite3
import tempfile
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
source = ROOT / "tools/runtime_integration_scenario.py"
scenario = types.ModuleType("integration_scenario")
scenario.__file__ = str(source)
exec(compile(source.read_bytes(), str(source), "exec"), scenario.__dict__)
B = {
    "task_id": "task",
    "revision": 1,
    "operation_id": "operation",
    "policy_revision": "policy",
    "host_id": "host",
    "workspace_id": "workspace",
    "lease_epoch": 1,
}


def execute(root, name, sql, rows=()):
    with sqlite3.connect(root / name) as db:
        db.executescript(sql)
        for statement, values in rows:
            db.execute(statement, values)


def delivery_fixture(root, before=False):
    data = b"original synthetic bytes\x00\xff"
    ref = {
        "binding": B,
        "artifact_id": "artifact",
        "artifact_revision": 1,
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    validation = {
        "artifact": ref,
        "validator_revision": "validator",
        "policy_revision": "policy",
        "passed": True,
    }
    accepted = {"validation": validation}
    request = {
        "version": "runspindle.integration.v1",
        "accepted": accepted,
        "account_id": "account",
        "destination_id": "destination",
        "delivery_operation_id": "delivery-operation",
    }
    receipt = {"request": request, "receipt_id": "receipt"}
    rows = [
        ("INSERT INTO artifacts VALUES(?,?)", (json.dumps(ref), data)),
        ("INSERT INTO validations VALUES(?)", (json.dumps(validation),)),
        ("INSERT INTO acceptances VALUES(?)", (json.dumps(accepted),)),
        (
            "INSERT INTO outbox VALUES(?,?,?,?)",
            (
                json.dumps(request),
                "unknown" if before else "delivered",
                None if before else json.dumps(receipt),
                0 if before else 1,
            ),
        ),
    ]
    execute(
        root,
        "core.sqlite",
        "CREATE TABLE artifacts(reference TEXT,bytes BLOB);CREATE TABLE validations(record TEXT);CREATE TABLE acceptances(record TEXT);CREATE TABLE outbox(request TEXT,state TEXT,receipt TEXT,conflict INTEGER);",
        rows,
    )
    rows = (
        [("INSERT INTO calls VALUES(?,?)", ("lookup", json.dumps(request)))]
        if before
        else [
            ("INSERT INTO calls VALUES(?,?)", (a, json.dumps(request)))
            for a in ("send", "lookup")
        ]
        + [("INSERT INTO receipts VALUES(?,?)", (json.dumps(receipt), data))]
    )
    execute(
        root,
        "destination.sqlite",
        "CREATE TABLE calls(id INTEGER PRIMARY KEY,action TEXT,request TEXT);CREATE TABLE receipts(receipt TEXT,bytes BLOB);",
        [
            (
                statement.replace(
                    "INSERT INTO calls VALUES(?,?)",
                    "INSERT INTO calls(action,request) VALUES(?,?)",
                ),
                values,
            )
            for statement, values in rows
        ],
    )
    return {"request": request, "before": before}


def host_fixture(root, before=False):
    race_binding = dict(B, operation_id="race-operation")
    snap = {
        "binding": B,
        "execution": "Unknown" if before else {"Terminal": "Completed"},
        "cancellation": "None" if before else "ObservedTerminal",
        "native_session_id": None if before else "native",
        "last_sequence": 0 if before else 2,
        "observed_at_ms": None if before else 101,
    }
    held = {
        "binding": race_binding,
        "execution": {"Terminal": "Completed"},
        "cancellation": "None",
        "native_session_id": "race-native",
        "last_sequence": 2,
        "observed_at_ms": 101,
    }
    core = dict(held, cancellation="ObservedTerminal")
    state = {"entries": {"operation": snap, "race-operation": held}}
    execute(
        root,
        "host.sqlite",
        "CREATE TABLE host_state(id INTEGER PRIMARY KEY,state BLOB);",
        [("INSERT INTO host_state VALUES(1,?)", (json.dumps(state),))],
    )
    calls = [(a, B) for a in ("launch", "discover") if before] + (
        []
        if before
        else [(a, B) for a in ("launch", "discover", "cancel")]
        + [(a, race_binding) for a in ("launch", "discover")]
    )
    rows = [
        ("INSERT INTO calls(action,binding) VALUES(?,?)", (a, json.dumps(b)))
        for a, b in calls
    ]
    if not before:
        rows.append(
            (
                "INSERT INTO sessions VALUES(?)",
                (
                    json.dumps(
                        {
                            "binding": B,
                            "native_session_id": "native",
                            "sequence": 2,
                            "terminal": "Completed",
                            "observed_at_ms": 101,
                        }
                    ),
                ),
            )
        )
    if not before:
        rows.append(
            (
                "INSERT INTO sessions VALUES(?)",
                (
                    json.dumps(
                        {
                            "binding": race_binding,
                            "native_session_id": "race-native",
                            "sequence": 2,
                            "terminal": "Completed",
                            "observed_at_ms": 101,
                        }
                    ),
                ),
            )
        )
    execute(
        root,
        "native-peer.sqlite",
        "CREATE TABLE calls(id INTEGER PRIMARY KEY,action TEXT,binding TEXT);CREATE TABLE sessions(observation TEXT);",
        rows,
    )
    for prefix in ("reconcile-ready", "reconcile-returned"):
        (root / (prefix + "-race-operation.json")).write_text(json.dumps(held))
    return {
        "request": {"admission": B},
        "before": before,
        "terminal_race": {
            "request": {"admission": race_binding},
            "held": held,
            "core": core,
            "accepted_events": [10],
            "completed_events": [12],
        },
    }


class Oracles(unittest.TestCase):
    def test_required_unexercised_gates_and_unknown_versions_never_pass(self):
        value = json.loads(scenario.MANIFEST.read_text())
        self.assertEqual(scenario.validate_manifest(value), value)
        for mutate in (
            lambda x: x["required_system_gates"].update(native_wire="passed"),
            lambda x: x.update(version="future"),
            lambda x: x["lanes"]["H02"].update(scripted=[]),
            lambda x: x.update(seed=True),
        ):
            changed = copy.deepcopy(value)
            mutate(changed)
            with self.assertRaises(scenario.Blocked):
                scenario.validate_manifest(changed)
        self.assertEqual(scenario.aggregate("passed"), "blocked")
        self.assertEqual(scenario.aggregate("failed"), "failed")

    def test_independent_host_ledger_accepts_exact_identity_and_detects_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            context = host_fixture(root)
            self.assertEqual(scenario.observe_host(root, context)["launch_calls"], 1)
            with sqlite3.connect(root / "native-peer.sqlite") as db:
                db.execute(
                    "INSERT INTO calls(action,binding) VALUES(?,?)",
                    ("launch", json.dumps(B)),
                )
            with self.assertRaisesRegex(AssertionError, "dispatch"):
                scenario.observe_host(root, context)

    def test_before_effect_uncertainty_never_becomes_terminal_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            context = host_fixture(root, True)
            self.assertEqual(scenario.observe_host(root, context)["state"], "unknown")
            with sqlite3.connect(root / "native-peer.sqlite") as db:
                db.execute(
                    "INSERT INTO sessions VALUES(?)",
                    (
                        json.dumps(
                            {
                                "binding": B,
                                "native_session_id": "fabricated",
                                "sequence": 1,
                            }
                        ),
                    ),
                )
            with self.assertRaises(AssertionError):
                scenario.observe_host(root, context)

    def test_session_rebinding_and_dropped_cancellation_are_detected(self):
        for field in ("native_session_id", "cancellation"):
            with tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                context = host_fixture(root)
                if field == "cancellation":
                    context["terminal_race"]["core"][field] = "None"
                else:
                    with sqlite3.connect(root / "native-peer.sqlite") as db:
                        db.execute(
                            "UPDATE sessions SET observation=?",
                            (
                                json.dumps(
                                    {
                                        "binding": B,
                                        "native_session_id": "rebound",
                                        "sequence": 2,
                                        "terminal": "Completed",
                                        "observed_at_ms": 101,
                                    }
                                ),
                            ),
                        )
                with self.assertRaises(AssertionError):
                    scenario.observe_host(root, context)

    def test_delivery_ledger_rejects_skipped_validation_changed_bytes_and_fabricated_receipts(
        self,
    ):
        mutations = [
            "DELETE FROM validations",
            "UPDATE artifacts SET bytes=x'00'",
            "DELETE FROM receipts",
            "UPDATE outbox SET conflict=0",
        ]
        for sql in mutations:
            with tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                context = delivery_fixture(root)
                self.assertEqual(
                    scenario.observe_delivery(root, context)["send_calls"], 1
                )
                target = (
                    "destination.sqlite"
                    if sql == "DELETE FROM receipts"
                    else "core.sqlite"
                )
                with sqlite3.connect(root / target) as db:
                    db.execute(sql)
                with self.assertRaises(AssertionError):
                    scenario.observe_delivery(root, context)

    def test_reserved_before_send_is_unknown_without_delivery_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            context = delivery_fixture(root, True)
            self.assertEqual(scenario.observe_delivery(root, context)["send_calls"], 0)

    def test_observer_cannot_mutate_existing_ledger_or_create_missing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            delivery_fixture(root)
            with self.assertRaisesRegex(AssertionError, "readback failed"):
                scenario.records(root, "core.sqlite", "DELETE FROM acceptances")
            self.assertEqual(
                len(
                    scenario.records(
                        root, "core.sqlite", "SELECT record FROM acceptances"
                    )
                ),
                1,
            )
            with self.assertRaisesRegex(AssertionError, "missing independent ledger"):
                scenario.records(root, "missing.sqlite", "SELECT 1")
            self.assertFalse((root / "missing.sqlite").exists())

    def test_source_loading_ignores_untracked_bytecode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "module.py"
            path.write_text("VALUE='evil'\n")
            metadata = path.stat()
            py_compile.compile(str(path), doraise=True)
            path.write_text("VALUE='safe'\n")
            os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
            self.assertEqual(
                scenario.load_exact(path, "verified_integration_fixture").VALUE, "safe"
            )


if __name__ == "__main__":
    unittest.main()
