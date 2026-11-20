#!/usr/bin/env python3
"""H05 real pinned Browser journal, with a synthetic non-idempotent site."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing, contextmanager
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scenarios/browser-effect-recovery-v1.json"
FAULTS = {"lost": 0, "crash_before": 17, "crash_after": 18}
WRONG_TARGETS = ("tab", "account", "epoch")
SCRIPT = Path(__file__).resolve()


def require(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], timeout=15)


def stage_source(stage: Path, spec: dict[str, Any]) -> dict[str, str]:
    lock = json.loads((ROOT / "composition.lock.json").read_bytes())["components"]
    pins = {row["component"]: row["commit"] for row in lock}
    require(
        len(lock) == 7
        and set(pins)
        == {"browser", "console", "core", "host", "platform", "refinery", "tether"},
        "invalid composition pin inventory",
    )
    for name, commit in pins.items():
        path = "components/" + name
        require(
            git(ROOT, "ls-files", "--stage", "--", path).decode().strip()
            == f"160000 {commit} 0\t{path}",
            "composition gitlink mismatch",
        )
    source = ROOT / "components/browser"
    require(pins["browser"] == spec["browser_commit"], "scenario Browser pin mismatch")
    require(
        git(source, "rev-parse", "--show-toplevel").decode().strip() == str(source)
        and git(source, "rev-parse", "HEAD").decode().strip() == pins["browser"]
        and not git(source, "status", "--porcelain"),
        "need the clean, pinned Browser checkout",
    )
    for relative, expected in spec["source_sha256"].items():
        path = Path(relative)
        require(
            not path.is_absolute() and ".." not in path.parts and path.suffix == ".py",
            "invalid staged source path",
        )
        data = git(source, "show", f"{pins['browser']}:{relative}")
        require(sha(data) == expected, "Browser source digest mismatch")
        destination = stage / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return pins


def worker(source: Path, data: Path, mode: str) -> str:
    def audit(event: str, _: tuple[object, ...]) -> None:
        if event.startswith("socket.") or event in {
            "subprocess.Popen",
            "os.exec",
            "os.fork",
            "os.forkpty",
            "os.posix_spawn",
            "os.system",
        }:
            (data / "forbidden").write_text("attempted external effect\n")
            raise RuntimeError("external effect forbidden")

    sys.addaudithook(audit)
    sys.path.insert(0, str(source))
    credentials = import_module("browser_runtime.credentials")
    effects = import_module("browser_runtime.effects")
    guarded = import_module("browser_runtime.guarded_effects")
    site_module = import_module("browser_testing.effect_site")
    spec = json.loads(MANIFEST.read_bytes())
    payload = spec["payload"].encode()
    binding = effects.Binding(**spec["binding"])
    target = credentials.Target(binding, **spec["target"])
    observed = target
    if mode in WRONG_TARGETS:
        changed = binding.epoch - 1 if mode == "epoch" else "wrong-synthetic"
        observed = replace(target, binding=replace(binding, **{mode: changed}))
    action = "reconcile" if mode in (*WRONG_TARGETS, "reconcile") else "dispatch"
    grant = guarded.Grant(target, sha(payload), action, 20.0)
    ticket = object()
    site = site_module.Site(data / "site.sqlite", mode)

    class Adapters:
        held = False
        used = False

        @contextmanager
        def acquire(self) -> Iterator[Adapters]:
            self.held = True
            try:
                yield self
            finally:
                self.held = False

        def admit(self, presented: object) -> Any:
            if presented is not ticket or self.used:
                return None
            self.used = True
            return grant

        def observe(self) -> Any:
            return credentials.Observation(observed, 8.0 if mode == "stale" else 10.0)

        def current(self, supplied: object) -> bool:
            return self.held and supplied is grant and mode != "revoked"

        def record(self, supplied: object, guard: object, name: str) -> None:
            require(self.held and guard is self and supplied is grant, "unfenced site")
            with (data / "calls").open("a", encoding="utf-8") as log:
                log.write(name + "\n")

        def submit(self, supplied: Any, value: bytes, guard: object) -> object:
            self.record(supplied, guard, "submit")
            return site.submit(supplied.target.binding, value)

        def readback(self, supplied: Any, guard: object) -> Any:
            self.record(supplied, guard, "readback")
            return site.observe(supplied.target.binding, supplied.payload_digest)

    adapter = Adapters()
    journal = guarded.GuardedJournal(
        data / "journal.sqlite", authority=adapter, site=adapter, clock=lambda: 10.0
    )
    try:
        outcome = (
            journal.reconcile(ticket)
            if action == "reconcile"
            else journal.dispatch(ticket, payload)
        )
        return str(outcome)
    except effects.Denied:
        return "denied"
    finally:
        journal.close()


def invoke(source: Path, data: Path, mode: str, exit_code: int = 0) -> str:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            *("-O" for _ in range(sys.flags.optimize)),
            str(SCRIPT),
            "--worker",
            str(source),
            str(data),
            mode,
        ],
        cwd=data,
        capture_output=True,
        text=True,
        timeout=12,
    )
    require(
        result.returncode == exit_code and not result.stderr, "worker failed: " + mode
    )
    require(not (data / "forbidden").exists(), "external effect attempted")
    return result.stdout.strip()


def rows(path: Path, query: str) -> list[tuple[Any, ...]]:
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as database:
        return database.execute(query).fetchall()


def calls(data: Path) -> list[str]:
    path = data / "calls"
    return path.read_text().splitlines() if path.exists() else []


def site_rows(data: Path) -> list[tuple[Any, ...]]:
    return rows(data / "site.sqlite", "SELECT binding,digest,outcome FROM events")


def scenario(
    source: Path, data: Path, spec: dict[str, Any], fault: str
) -> dict[str, Any]:
    data.mkdir()
    digest = sha(spec["payload"].encode())
    encoded = {
        "binding": spec["binding"],
        "target_digest": sha(canonical({"binding": spec["binding"], **spec["target"]})),
    }
    accepted = fault != "crash_before"
    expected_events = (
        [(json.dumps(spec["binding"], sort_keys=True), digest, "confirmed")]
        if accepted
        else []
    )
    expected_initial = "unknown" if fault == "lost" else ""
    require(
        invoke(source, data, fault, FAULTS[fault]) == expected_initial,
        "submission acknowledged as a result",
    )
    require(site_rows(data) == expected_events, "unexpected initial site effects")

    def journal_rows() -> list[tuple[Any, ...]]:
        return rows(
            data / "journal.sqlite",
            "SELECT operation,binding,digest,outcome,evidence FROM operations",
        )

    operation = (spec["binding"]["operation"], canonical(encoded).decode(), digest)
    require(journal_rows() == [(*operation, "unknown", None)], "missing exact intent")
    require(
        invoke(source, data, "dispatch") == "unknown", "restart inferred an outcome"
    )
    require(
        site_rows(data) == expected_events and calls(data) == ["submit"],
        "duplicate reached site",
    )
    for wrong in WRONG_TARGETS:
        require(invoke(source, data, wrong) == "denied", "wrong target allowed")
    require(calls(data) == ["submit"], "wrong target reached site readback")

    final = "confirmed" if accepted else "unknown"
    require(invoke(source, data, "reconcile") == final, "wrong authoritative outcome")
    require(invoke(source, data, "reconcile") == final, "reopened outcome changed")
    evidence = sha(json.dumps([["confirmed"]]).encode()) if accepted else None
    require(
        journal_rows() == [(*operation, final, evidence)], "wrong retained evidence"
    )
    require(site_rows(data) == expected_events, "readback changed site effects")
    require(
        calls(data) == ["submit"] + ["readback"] * (1 if accepted else 2),
        "unexpected helper calls during reconciliation",
    )
    return {
        "fault": fault,
        "effects": len(expected_events),
        "calls": calls(data),
        "outcome": final,
    }


def authority_negative(source: Path, data: Path, mode: str) -> None:
    data.mkdir()
    result = invoke(source, data, mode)
    require(site_rows(data) == [] and calls(data) == [], "forbidden submit for " + mode)
    require(result == "denied", "stale or revoked authority was admitted")
    require(
        not rows(data / "journal.sqlite", "SELECT operation FROM operations"),
        "forbidden reservation for " + mode,
    )


def mutations(source: Path, scratch: Path, spec: dict[str, Any]) -> list[str]:
    detected = []
    for name, filename, needle, replacement, failure in (
        (
            "duplicate_submit",
            "effects.py",
            "return self._outcome(row[2])",
            "self.submit(binding, payload)\n            return self._outcome(row[2])",
            "duplicate reached site",
        ),
        (
            "stale_observation",
            "guarded_effects.py",
            "or not 0 <= now - observed_at <= self._max_age",
            "",
            "forbidden submit for stale",
        ),
    ):
        clone = scratch / name
        shutil.copytree(source, clone)
        path = clone / "browser_runtime" / filename
        original = path.read_text()
        require(original.count(needle) == 1, "mutation anchor drift")
        path.write_text(original.replace(needle, replacement))
        data = scratch / (name + "-data")
        try:
            if name == "duplicate_submit":
                scenario(clone, data, spec, "lost")
            else:
                authority_negative(clone, data, "stale")
        except AssertionError as error:
            require(str(error) == failure, "mutation failed outside its oracle")
            detected.append(name)
        else:
            raise AssertionError("mutation escaped: " + name)
    return detected


def run() -> dict[str, Any]:
    raw = MANIFEST.read_bytes()
    spec = json.loads(raw)
    require(
        spec["version"] == "runspindle.browser-effect-hero.v1"
        and type(spec["repeat_runs"]) is int
        and spec["repeat_runs"] == 2
        and spec["faults"] == list(FAULTS),
        "unknown scenario contract",
    )
    with TemporaryDirectory(prefix="runspindle-h05-") as directory:
        scratch = Path(directory).resolve()
        source = scratch / "source"
        pins = stage_source(source, spec)
        runs = [
            [
                scenario(source, scratch / f"{i}-{fault}", spec, fault)
                for fault in FAULTS
            ]
            for i in range(spec["repeat_runs"])
        ]
        require(runs[0] == runs[1], "repeat observations changed")
        for mode in ("stale", "revoked"):
            authority_negative(source, scratch / mode, mode)
        return {
            "scenario": "H05",
            "browser_lane": "passed",
            "browser_journal": "pinned_real_sqlite",
            "external_site": "synthetic_sqlite",
            "authority": "synthetic_guard",
            "composition_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
            "component_pins": pins,
            "manifest_sha256": sha(raw),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "repeat_runs": len(runs),
            "cases": runs[0],
            "mutations_detected": mutations(source, scratch, spec),
            "core_native_live_and_full_system": "blocked",
        }


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]))
    elif len(sys.argv) == 1:
        print(json.dumps(run(), sort_keys=True))
    else:
        raise SystemExit("unexpected H05 arguments")
