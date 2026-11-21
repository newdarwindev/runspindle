"""Qualify H09 Host freshness with the pinned Rust adapter and its SQLite store."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path
from types import FrameType
from typing import Any

import tomllib

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scenarios/host-session-freshness-v1.json"
WORKER = Path(__file__).with_suffix(".rs")
VERSION = "runspindle.host-session-freshness.v1"
FILES = ("Cargo.toml", "Cargo.lock", "src/lib.rs", "src/lifecycle.rs", "src/storage.rs")
MUTATION = "|| observation.sequence <= value.last_sequence"


class InvariantError(ValueError):
    """An independently observed outcome differs from the fixture."""


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise InvariantError(detail)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(directory: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", *args], cwd=directory, timeout=15
    )


def stage_source(directory: Path, expected: dict[str, str]) -> dict[str, Any]:
    lock_bytes = (ROOT / "composition.lock.json").read_bytes()
    components = {
        item["component"]: item["commit"]
        for item in json.loads(lock_bytes)["components"]
    }
    require(components == expected, "composition lock differs from the fixture")
    for name, commit in components.items():
        link = f"components/{name}"
        expected_link = f"160000 {commit} 0\t{link}"
        actual = git(ROOT, "ls-files", "--stage", "--", link).decode().strip()
        require(actual == expected_link, f"gitlink mismatch: {name}")

    host = ROOT / "components/host"
    pin = components["host"]
    require(
        git(host, "rev-parse", "HEAD").decode().strip() == pin, "wrong Host checkout"
    )
    hashes = {}
    for filename in FILES:
        blob = git(host, "cat-file", "blob", f"{pin}:{filename}")
        path = directory / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        hashes[filename] = digest(blob)
    closure_bytes = git(
        ROOT / "components/platform",
        "cat-file",
        "blob",
        components["platform"] + ":fleet/rust-closure.json",
    )
    closure = json.loads(closure_bytes)
    require(
        closure["host"]["commit"] == pin
        and closure["host"]["lock_sha256"] == hashes["Cargo.lock"],
        "prepared Rust closure differs from the reviewed Host pin",
    )
    with (directory / "Cargo.lock").open("rb") as handle:
        packages = tomllib.load(handle)["package"]
    for package in packages:
        if "source" in package:
            archive = f"{package['name']}-{package['version']}.crate"
            require(
                package["source"]
                == "registry+https://github.com/rust-lang/crates.io-index"
                and package["checksum"] == closure["crate_archives"].get(archive),
                f"dependency outside prepared closure: {archive}",
            )
    harness = WORKER.read_bytes()
    worker_target = directory / "src/bin/h09-host-session.rs"
    worker_target.parent.mkdir()
    worker_target.write_bytes(harness)
    return {
        "composition_commit": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "composition_lock_sha256": digest(lock_bytes),
        "components": components,
        "host_files_sha256": hashes,
        "prepared_rust_closure_sha256": digest(closure_bytes),
        "rust_worker_sha256": digest(harness),
        "harness_sha256": digest(Path(__file__).read_bytes()),
    }


def build(source: Path) -> Path:
    # Resolve only the staged Cargo.lock using an already prepared registry.
    result = subprocess.run(
        ["cargo", "build", "--offline", "--locked", "--bin", "h09-host-session"],
        cwd=source,
        env=os.environ | {"CARGO_TARGET_DIR": str(source / "target")},
        text=True,
        capture_output=True,
        timeout=180,
    )
    require(result.returncode == 0, f"offline Host build failed:\n{result.stderr}")
    return source / "target/debug/h09-host-session"


def binding(identity: str) -> dict[str, Any]:
    return {
        "task_id": "task-" + identity,
        "revision": 1,
        "operation_id": "operation-" + identity,
        "policy_revision": "policy-1",
        "host_id": "fixture-host",
        "workspace_id": "workspace-" + identity,
        "lease_epoch": 2,
    }


def observation(identity: str, payload: dict[str, Any]) -> dict[str, Any]:
    # Separate the selected task, the source binding, and the native peer ID.
    origin = payload.get("origin", identity)
    return {
        "binding": binding(origin) | payload.get("binding_override", {}),
        "native_session_id": "native-" + payload.get("native", origin),
        "sequence": payload["sequence"],
        "observed_at_ms": payload["at"],
        "terminal": None,
    }


def request(step: dict[str, Any]) -> dict[str, Any]:
    identity, now, operation = step["identity"], step["now"], step["operation"]
    selected = binding(identity)
    result = {"binding": selected, "now": now, "operation": operation}
    payload = step.get("observation")
    if operation == "submit":
        result["presence"] = {
            "host_id": selected["host_id"],
            "workspace_id": selected["workspace_id"],
            "reachability": "Online" if payload else "Unknown",
            "observed_at_ms": now - 1,
            "valid_until_ms": now + 5,
        }
        result["reply"] = observation(identity, payload) if payload else None
    if operation == "event":
        result["event"] = {
            "version": "runspindle.runtime.v1",
            "observation": observation(identity, step["observation"]),
            "kind": "Progress",
            "encoded_size": 128,
        }
    if operation == "reconcile":
        result["observations"] = [observation(identity, payload)] if payload else []
    return result


def snapshot(identity: str, expected: list[Any]) -> dict[str, Any]:
    execution, sequence, timestamp = expected
    return {
        "binding": binding(identity),
        "execution": execution,
        "cancellation": "None",
        "native_session_id": "native-" + identity if timestamp is not None else None,
        "last_sequence": sequence,
        "observed_at_ms": timestamp,
        "cancel_dispatched": False,
    }


def inspect(store: Path) -> tuple[int, dict[str, Any], str]:
    with closing(
        sqlite3.connect(store.as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as db:
        version, generation, encoded = db.execute(
            "SELECT version, generation, state FROM host_state WHERE id=1"
        ).fetchone()
        schema = db.execute(
            "SELECT sql FROM sqlite_schema WHERE name='host_state'"
        ).fetchone()[0]
    require(version == 1, "unexpected Host storage version")
    return generation, json.loads(encoded), digest(schema.encode())


def freshness(snap: dict[str, Any], step: dict[str, Any], max_age: int) -> str:
    timestamp = snap["observed_at_ms"]
    if timestamp is None or snap["execution"] == "Unknown":
        return "unknown"
    if step["now"] - timestamp > max_age:
        return "stale_retained"
    return "recent_retained"


def run_matrix(
    executable: Path, directory: Path, manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    directory.mkdir()
    store = directory / "host.sqlite"
    ledger = directory / "peer.jsonl"
    ledger.touch()
    expected_entries: dict[str, Any] = {}
    expected_receipts: list[dict[str, Any]] = []
    expected_ledger: list[dict[str, Any]] = []
    generation = 1  # First Adapter::with_storage persists its configuration.
    max_age = manifest["max_age_ms"]
    reports = []
    for step in manifest["steps"]:
        label = step["id"]
        identity = step["identity"]
        operation = "operation-" + identity
        answer = subprocess.run(
            [str(executable), str(store), str(ledger)],
            input=json.dumps(request(step)),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=directory,
            env={"H09_MAX_AGE_MS": str(max_age), "LC_ALL": "C"},
        )
        require(answer.returncode == 0, f"{label}: Host worker failed: {answer.stderr}")
        result = json.loads(answer.stdout)
        if "persist" in step:
            entry = snapshot(identity, step["persist"])
            expected_entries[operation] = entry
            expected_receipts.append(
                {"version": "runspindle.runtime.v1", "snapshot": entry}
            )
            generation += step["writes"]
        stored_generation, stored, schema = inspect(store)
        expected_store = {
            "config": [8, 32, max_age],
            "entries": expected_entries,
            "receipts": expected_receipts,
        }
        require(
            stored_generation == generation and stored == expected_store,
            f"{label}: durable state mismatch",
        )

        previous_calls = len(expected_ledger)
        if "call" in step:
            call = step["call"]
            expected_ledger.append(
                {
                    "call": call,
                    "binding": binding(identity),
                    "effect": "native-" + identity if call == "launch" else None,
                }
            )
        calls = [json.loads(line) for line in ledger.read_text().splitlines()]
        require(calls == expected_ledger, f"{label}: peer ledger mismatch")

        if "error" in step:
            expected = {"error": step["error"]}
        elif step["operation"] == "capabilities":
            expected = {"capabilities": manifest["scripted_capabilities"]}
        else:
            snap = expected_entries[operation]
            expected = {"snapshot": snap}
            require(
                freshness(snap, step, max_age) == step["freshness"],
                f"{label}: retained freshness mismatch",
            )
        require(result == expected, f"{label}: Host result mismatch")
        report = {
            "step": label,
            "now_ms": step["now"],
            "result": result,
            "generation": generation,
            "receipt_count": len(expected_receipts),
            "peer_calls": calls[previous_calls:],
            "schema_sha256": schema,
        }
        if "freshness" in step:
            report["retained_freshness"] = step["freshness"]
        reports.append(report)
    return reports


def run(*, check_mutation: bool) -> dict[str, Any]:
    fixture_bytes = FIXTURE.read_bytes()
    manifest = json.loads(fixture_bytes)
    require(manifest["version"] == VERSION, "unsupported Host scenario fixture")
    with tempfile.TemporaryDirectory(prefix="runspindle-h09-host-") as temporary:
        directory = Path(temporary).resolve()
        source = directory / "source"
        evidence = stage_source(source, manifest["components"])
        executable = build(source)
        first = run_matrix(executable, directory / "first", manifest)
        second = run_matrix(executable, directory / "second", manifest)
        require(first == second, "normalized Host observations differ")
        mutation = "not_run"
        if check_mutation:
            lifecycle = source / "src/lifecycle.rs"
            original = lifecycle.read_text()
            require(original.count(MUTATION) == 1, "sequence mutation target changed")
            lifecycle.write_text(original.replace(MUTATION, "", 1))
            try:
                run_matrix(build(source), directory / "mutation", manifest)
            except InvariantError as error:
                require(
                    str(error) == "reordered-sequence: durable state mismatch",
                    f"unexpected mutation failure: {error}",
                )
                mutation = "rejected_at_reordered_sequence"
            else:
                raise InvariantError("reordered sequence mutant survived")
    toolchain = {
        name: subprocess.check_output(
            [name, "--version"], text=True, timeout=15
        ).strip()
        for name in ("rustc", "cargo")
    }
    return evidence | {
        "version": VERSION,
        "fixture_sha256": digest(fixture_bytes),
        "toolchain": toolchain | {"readback_sqlite": sqlite3.sqlite_version},
        "observations": first,
        "repeat_runs": 2,
        "mutation": mutation,
        "real_component": "host",
        "sibling_components": "synthetic",
        "lane": "passed",
        "system_aggregate": "blocked",
    }


def terminate(signum: int, frame: FrameType | None) -> None:
    raise SystemExit(128 + signum)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-mutation", action="store_true")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, terminate)
    try:
        report = run(check_mutation=args.check_mutation)
    except (ValueError, OSError, sqlite3.Error, subprocess.SubprocessError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
