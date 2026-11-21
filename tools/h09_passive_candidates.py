"""Verify passive Core and Browser candidate APIs together in an offline H09 replay."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import signal
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from contextlib import closing
from pathlib import Path
from types import FrameType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scenarios/h09-passive-candidates-v1.json"
DENIED: dict[str, Any] = {"status": "denied"}
READ_CALLS = ["acquire", "admit", "current", "observe", "current", "close"]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any, *, ascii_only: bool = True) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=ascii_only, separators=(",", ":")
    ).encode()


def scope(target: dict[str, Any]) -> dict[str, Any]:
    excluded = {"intent", "revision", "operation", "epoch"}
    return target | {
        "binding": {k: v for k, v in target["binding"].items() if k not in excluded}
    }


def git(directory: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", *args], cwd=directory, timeout=30
    )


def stage(name: str, checkout: Path, revision: str, output: Path) -> dict[str, str]:
    check(
        git(checkout, "rev-parse", "HEAD").decode().strip() == revision,
        f"{name}: candidate revision mismatch",
    )
    members = (
        ("Cargo.toml", "Cargo.lock", "src", "tests/fixtures")
        if name == "core"
        else ("browser_runtime",)
    )
    archive = git(checkout, "archive", revision, *members)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(output, filter="data")
    hashes = {"commit": revision, "source_archive_sha256": digest(archive)}
    if name == "core":
        hashes["cargo_lock_sha256"] = digest((output / "Cargo.lock").read_bytes())
    return hashes


def sources(
    directory: Path, checkouts: dict[str, Path], manifest: dict[str, Any]
) -> dict[str, Any]:
    lock = (ROOT / "composition.lock.json").read_bytes()
    actual = {row["component"]: row["commit"] for row in json.loads(lock)["components"]}
    check(actual == manifest["composition_pins"], "fixture and composition lock differ")
    for name, rev in actual.items():
        path = f"components/{name}"
        check(
            git(ROOT, "ls-files", "--stage", "--", path).decode().strip()
            == f"160000 {rev} 0\t{path}",
            f"composition gitlink mismatch: {name}",
        )
    return {
        "composition": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "composition_lock_sha256": digest(lock),
        "composition_pins": actual,
        "candidates": {
            name: stage(name, checkout, manifest["candidates"][name], directory / name)
            for name, checkout in checkouts.items()
        },
    }


def build(core: Path, target: Path) -> Path:
    harness = ROOT / "tools/h09_passive_core_worker.rs"
    (core / "src/bin/h09-passive-worker.rs").write_bytes(harness.read_bytes())
    with (core / "Cargo.toml").open("a") as stream:
        stream.write(
            '\n[[bin]]\nname = "h09-passive-worker"\npath = "src/bin/h09-passive-worker.rs"\n'
        )
    result = subprocess.run(
        [
            "cargo",
            "build",
            "--offline",
            "--locked",
            "--features",
            "artifact-store",
            "--bin",
            "h09-passive-worker",
            "--target-dir",
            str(target),
        ],
        cwd=core,
        text=True,
        capture_output=True,
        timeout=300,
    )
    check(result.returncode == 0, f"candidate Core build failed:\n{result.stderr}")
    return target / "debug/h09-passive-worker"


def worker(command: list[str], request: dict[str, Any], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(
        command,
        input=json.dumps(request),
        cwd=cwd,
        env={"LC_ALL": "C"},
        text=True,
        capture_output=True,
        timeout=15,
    )
    check(result.returncode == 0, f"passive worker failed: {result.stderr.strip()}")
    return dict(json.loads(result.stdout))


def inspect(db: Path) -> dict[str, Any]:
    with closing(
        sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as connection:
        schema = "\n".join(
            sql
            for (sql,) in connection.execute(
                "SELECT sql FROM sqlite_schema WHERE sql IS NOT NULL ORDER BY name"
            )
        )
        return {
            "operations": connection.execute(
                "SELECT operation, target, observation, conflict, generation FROM browser_operations ORDER BY operation"
            ).fetchall(),
            "heads": connection.execute(
                "SELECT browser, scope, operation FROM browser_control_heads ORDER BY browser"
            ).fetchall(),
            "schema_sha256": digest(schema.encode()),
            "store_sha256": digest(db.read_bytes()),
        }


def observe_browser(
    browser: Path, cwd: Path, request: dict[str, Any]
) -> dict[str, Any]:
    return worker(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            *(["-O"] if sys.flags.optimize else []),
            str(ROOT / "tools/h09_passive_browser_worker.py"),
            str(browser),
        ],
        request,
        cwd,
    )


def project(
    active: dict[str, Any],
    core: dict[str, Any],
    browser: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    if core == DENIED:
        return {"view": "unknown"}
    if core["selection"] != active:
        return {"view": "discarded"}
    head = core["head"]
    prior = previous.get("head") if previous else None
    if prior and (
        head is None
        or (head["epoch"], head["generation"]) < (prior["epoch"], prior["generation"])
    ):
        return {"view": "discarded"}
    if browser == DENIED:
        return {"view": "retained_only", "head": head}
    if browser["selection_sha256"] != digest(canonical(active)):
        return {"view": "discarded"}
    check(
        browser["scope_sha256"] == digest(canonical(scope(active), ascii_only=False)),
        "Core and Browser physical scopes differ",
    )
    if (
        previous
        and previous["view"] == "observed"
        and browser["observed_at"] < previous["physical_observed_at"]
    ):
        return {"view": "discarded"}
    return {
        "view": "observed",
        "head": head,
        "physical_observed_at": browser["observed_at"],
    }


def run_matrix(
    executable: Path, browser: Path, scratch: Path, fixture: dict[str, Any]
) -> list[dict[str, Any]]:
    scratch.mkdir()
    db, ledger = scratch / "core.sqlite", scratch / "native.jsonl"
    ledger.touch()
    command = [str(executable), str(db), str(ledger)]
    target = fixture["target"]
    selections = {
        name: target
        | {
            "binding": target["binding"]
            | {"intent": name, "operation": "open-" + name, "revision": revision}
        }
        for name, revision in (("task-a", 1), ("task-b", 2))
    }
    initial = worker(command, {"action": "seed", "selection": target}, scratch)[
        "setup_target"
    ]
    receipts = []
    now = fixture["clock"]
    confirmed = False
    previous: dict[str, Any] | None = None
    active_selection = None
    core_receipts: dict[str, dict[str, Any]] = {}
    for case in fixture["cases"]:
        label = case["id"]
        if case.get("confirm") and not confirmed:
            worker(command, {"action": "confirm", "selection": target}, scratch)
            confirmed = True
        before = inspect(db)
        expected_head = {
            "epoch": 1,
            "generation": int(confirmed),
            "phase": "confirmed" if confirmed else "pending",
            "holder": {"kind": "agent", "identity": "fixture-agent"}
            if confirmed
            else None,
        }
        operations = [
            (operation, json.loads(bound), phase, conflict, generation)
            for operation, bound, phase, conflict, generation in before["operations"]
        ]
        check(
            operations
            == [
                (
                    "fixture-initialize",
                    initial,
                    "confirmed" if confirmed else "unknown",
                    0,
                    int(confirmed),
                )
            ],
            f"{label}: unexpected Core operation",
        )
        check(
            before["heads"]
            == [
                (
                    target["binding"]["browser"],
                    canonical(scope(initial), ascii_only=False).decode(),
                    "fixture-initialize",
                )
            ],
            f"{label}: unexpected Core head",
        )
        selection = selections[case["selection"]]
        current = selections[case.get("active", case["selection"])]
        core = worker(
            command,
            {
                "action": "status",
                "selection": selection,
                "grant": selections[case.get("grant", case["selection"])],
            },
            scratch,
        )
        physical = target
        if case.get("wrong_account"):
            physical = target | {
                "binding": target["binding"] | {"account": "other-account"}
            }
        seen = case.get("observed_at", now - 1)
        deadline = case.get("deadline", now + 2)
        probe = observe_browser(
            browser,
            scratch,
            {
                "selection": selection,
                "physical": physical,
                "observed_at": seen,
                "now": now,
                "deadline": deadline,
            },
        )
        expected_browser = (
            DENIED
            if case.get("browser_denied")
            else {
                "selection_sha256": digest(canonical(selection)),
                "scope_sha256": digest(canonical(scope(target), ascii_only=False)),
                "observed_at": seen,
                "checked_at": now,
            }
        )
        check(probe["result"] == expected_browser, f"{label}: Browser result mismatch")
        expected_calls = READ_CALLS
        if deadline <= now:
            expected_calls = READ_CALLS[:3] + ["close"]
        elif seen is None or case.get("wrong_account"):
            expected_calls = READ_CALLS[:4] + ["close"]
        check(
            probe["forbidden"] == [] and probe["calls"] == expected_calls,
            f"{label}: unexpected passive calls",
        )
        check(
            core
            == (
                DENIED
                if case.get("grant")
                else {"selection": selection, "head": expected_head}
            ),
            f"{label}: Core result mismatch",
        )
        if active_selection != current:
            active_selection, previous = current, None
        core_receipts[label] = core
        projected_core = core_receipts[case.get("replay_core", label)]
        view = project(current, projected_core, probe["result"], previous)
        check(view["view"] == case["view"], f"{label}: unexpected view disposition")
        if case.get("duplicate"):
            check(view == previous, f"{label}: duplicate changed the view")
        if view["view"] != "discarded":
            previous = view
        check(inspect(db) == before, f"{label}: passive read changed SQLite")
        calls = [json.loads(line) for line in ledger.read_text().splitlines()]
        check(
            calls
            == [
                {"action": action, "target": initial}
                for action in (
                    ("dispatch", "reconcile") if confirmed else ("dispatch",)
                )
            ],
            f"{label}: unexpected native calls",
        )
        receipts.append(
            {
                "case": label,
                "view": view,
                "retained_view": previous,
                "browser": probe,
                "core": core,
                "projected_core": projected_core,
                "native_setup_calls": calls,
                "schema_sha256": before["schema_sha256"],
                "durable_changes": 0,
            }
        )
    return receipts


def run(checkouts: dict[str, Path], target: Path | None = None) -> dict[str, Any]:
    raw = FIXTURE.read_bytes()
    manifest = json.loads(raw)
    check(
        manifest["version"] == "runspindle.h09-passive-candidates.v1",
        "unknown fixture version",
    )
    with tempfile.TemporaryDirectory(prefix="runspindle-h09-passive-") as directory:
        scratch = Path(directory).resolve()
        inventory = sources(scratch, checkouts, manifest)
        executable = build(scratch / "core", target or scratch / "target")
        browser = scratch / "browser"
        first = run_matrix(executable, browser, scratch / "first", manifest)
        second = run_matrix(executable, browser, scratch / "second", manifest)
        check(first == second, "normalized candidate receipts differ")
        path = browser / "browser_runtime/passive_peer.py"
        original = path.read_text()
        anchor = "scope != expected_scope"
        check(original.count(anchor) == 1, "Browser scope mutation target changed")
        path.write_text(original.replace(anchor, "False", 1))
        try:
            run_matrix(executable, browser, scratch / "mutant", manifest)
        except ValueError as error:
            check(
                str(error) == "other-account: Browser result mismatch",
                f"unexpected mutation failure: {error}",
            )
        else:
            raise ValueError("Browser scope mutant survived")
    return inventory | {
        "version": manifest["version"],
        "fixture_sha256": digest(raw),
        "harness_sha256": {
            name: digest((ROOT / "tools" / name).read_bytes())
            for name in (
                "h09_passive_candidates.py",
                "h09_passive_core_worker.rs",
                "h09_passive_browser_worker.py",
            )
        },
        "toolchain": {
            "python": sys.version.split()[0],
            "sqlite": sqlite3.sqlite_version,
            "rustc": subprocess.check_output(
                ["rustc", "--version"], text=True, timeout=15
            ).strip(),
        },
        "clock": manifest["clock"],
        "repeat_runs": 2,
        "observations": first,
        "mutation": "wrong_account_detected",
        "candidate_lane": "passed",
        "system_aggregate": "blocked",
    }


def terminate(signum: int, frame: FrameType | None) -> None:
    raise SystemExit(128 + signum)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--browser", required=True, type=Path)
    parser.add_argument(
        "--target-dir",
        type=Path,
        help="reuse an explicitly prepared local Cargo build cache",
    )
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, terminate)
    try:
        report = run(
            {"core": args.core.resolve(), "browser": args.browser.resolve()},
            args.target_dir.resolve() if args.target_dir else None,
        )
    except (ValueError, OSError, sqlite3.Error, subprocess.SubprocessError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
