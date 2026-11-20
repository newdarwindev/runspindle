#!/usr/bin/env python3
"""H08 pinned Platform spool and readback against an independent synthetic peer."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from tools.browser_effect_hero import (  # noqa: E402
    canonical,
    git,
    require,
    rows,
    sha,
    stage_source,
)

MANIFEST = ROOT / "scenarios/platform-telemetry-recovery-v1.json"
PHASES = ["outage", "lost_ack", "replay", "observe", "privacy"]
CANARY = "SYNTHETIC_PRIVACY_CANARY_17"
LOST_ACK_EXIT = 17


def attrs(values: dict[str, str]) -> list[dict[str, object]]:
    return [
        {"key": key, "value": {"stringValue": value}} for key, value in values.items()
    ]


def expected_envelope(seed: int, number: int, policy: str) -> dict[str, Any]:
    context = {
        "task_id": f"task-{seed}",
        "session_id": f"session-{seed}",
        "producer": "synthetic-otlp",
        "config_sha256": sha(b"synthetic-config-v1"),
        "policy_sha256": policy,
        "producer_version": "synthetic-v1",
    }
    span = {
        "traceId": sha(f"trace-{seed}".encode())[:32],
        "spanId": sha(f"span-{seed}-{number}".encode())[:16],
        "name": "synthetic-work",
        "attributes": attrs({"event_id": f"event-{seed}-{number}"}),
    }
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": attrs(context)},
                "scopeSpans": [
                    {"scope": {"name": "synthetic", "version": "1"}, "spans": [span]}
                ],
            }
        ]
    }


def backend_request(
    db: sqlite3.Connection,
    payload: bytes,
    mode: str,
    spec: dict[str, Any],
) -> tuple[int, bytes]:
    number = next(
        (
            int(index)
            for index in spec["units"]
            if payload
            == canonical(
                expected_envelope(spec["seed"], int(index), spec["policy_sha256"])
            )
        ),
        None,
    )
    if number is None:
        raise ValueError("backend received a noncanonical or unscoped envelope")
    db.execute(
        "INSERT INTO calls(phase,event,body_sha256) VALUES(?,?,?)",
        (mode, number, sha(payload)),
    )
    db.commit()
    if mode == "outage":
        if number % 2:
            raise ConnectionError("fixture receiver unavailable")
        raise TimeoutError("fixture receiver timed out")
    if mode not in ("lost_ack", "replay"):
        raise ValueError("readback phase attempted transport")
    if number == 3:
        return 403, b"{}"
    if number == 4:
        foreign = expected_envelope(spec["seed"], number, "f" * 64)
        db.execute("INSERT INTO records VALUES(?)", (canonical(foreign),))
    if number == 1:
        db.execute("INSERT INTO records VALUES(?)", (payload,))
    db.commit()
    return 200, b"{}"


def worker(source: Path, data: Path, mode: str) -> dict[str, Any]:
    def audit(event: str, _: tuple[object, ...]) -> None:
        if event.startswith("socket.") or event in {
            "subprocess.Popen",
            "os.exec",
            "os.posix_spawn",
            "os.fork",
            "os.forkpty",
            "os.system",
        }:
            (data / "forbidden-effect").touch()
            raise RuntimeError("external effect forbidden")

    sys.addaudithook(audit)
    sys.path.insert(0, str(source))
    telemetry = import_module("tools.disposable_harness.telemetry")
    runtime = import_module("tools.disposable_harness.runtime")
    spec = json.loads(MANIFEST.read_bytes())
    backend = data / "backend.sqlite"
    if mode in ("observe", "privacy"):
        uri = backend.as_uri() + "?mode=ro"
    else:
        uri = backend.as_uri() + "?mode=rw"
    with closing(sqlite3.connect(uri, uri=True)) as receiver:
        with runtime.DisposableRun(
            "telemetry", runtime.Clock(), parent=data
        ) as harness:
            endpoint = harness.register(
                "backend", lambda body: backend_request(receiver, body, mode, spec)
            )
            with closing(
                telemetry.Pipeline(harness, endpoint, data / "spool.sqlite")
            ) as pipeline:
                if mode == "outage":
                    for index, units in reversed(list(spec["units"].items())):
                        value = telemetry.produce(spec["seed"], int(index))
                        pipeline.emit(value, units=units)
                        pipeline.emit(value, units=units)
                    pipeline.flush()
                elif mode == "lost_ack":
                    try:
                        pipeline.flush(interrupt_after_accept=True)
                    except InterruptedError:
                        os._exit(LOST_ACK_EXIT)  # Parent reopens both SQLite files.
                    raise ValueError("lost acknowledgment was not injected")
                elif mode == "replay":
                    pipeline.flush()
                receipt = pipeline.receipt(backend)
                require(
                    CANARY not in json.dumps(receipt),
                    "privacy canary leaked to receipt",
                )
                require(harness.outbound_denied == 0, "unexpected transport")
                if not isinstance(receipt, dict):
                    raise ValueError("invalid telemetry receipt")
                return receipt


def invoke(
    source: Path, data: Path, mode: str, *, exit_code: int = 0
) -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            *("-O" for _ in range(sys.flags.optimize)),
            str(Path(__file__).resolve()),
            "--worker",
            str(source),
            str(data),
            mode,
        ],
        cwd=data,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    require(not (data / "forbidden-effect").exists(), "unexpected external effect")
    require(
        result.returncode == exit_code and not result.stderr, "worker failed: " + mode
    )
    if exit_code:
        require(not result.stdout, "interrupted worker reported success")
        return {}
    receipt = json.loads(result.stdout)
    if not isinstance(receipt, dict):
        raise ValueError("invalid worker receipt")
    return receipt


def check_before_replay(
    source: Path,
    data: Path,
    spec: dict[str, Any],
    clean: dict[int, bytes],
) -> dict[str, Any]:
    backend = data / "backend.sqlite"
    expected = [
        (f"event-{spec['seed']}-{index}", payload, "queued", spec["units"][str(index)])
        for index, payload in clean.items()
    ]
    spool = data / "spool.sqlite"
    queued = invoke(source, data, "outage")
    require(
        queued["emitted"] == 4
        and queued["queued"] == 4
        and queued["persisted"] == 0
        and queued["usage_units"] == 0
        and queued["rejected"] == 0,
        "outage lost or invented work",
    )
    require(
        rows(spool, "SELECT * FROM events ORDER BY id") == expected,
        "spool identity differs",
    )
    invoke(source, data, "lost_ack", exit_code=LOST_ACK_EXIT)
    require(
        rows(spool, "SELECT * FROM events ORDER BY id") == expected,
        "lost ack settled local work",
    )
    require(
        rows(backend, "SELECT body FROM records") == [(clean[1],)],
        "commit before exit not observed",
    )
    interrupted = invoke(source, data, "observe")
    require(
        interrupted["queued"] == 4
        and interrupted["persisted"] == 1
        and interrupted["usage_units"] == spec["units"]["1"],
        "restart inferred transport acceptance or missed durable readback",
    )
    return interrupted


def check_replay(
    source: Path,
    data: Path,
    spec: dict[str, Any],
    clean: dict[int, bytes],
) -> dict[str, Any]:
    backend = data / "backend.sqlite"
    receipt = invoke(source, data, "replay")
    require(
        (
            receipt["queued"],
            receipt["accepted"],
            receipt["rejected"],
            receipt["persisted"],
            receipt["usage_units"],
            receipt["privacy"],
        )
        == (0, 3, 1, 1, spec["units"]["1"], "passed_synthetic_only"),
        "readback conflated partial correlation, rejection, or acceptance",
    )
    events = receipt["events"]
    require(
        [
            (event["delivery"], event["copies"], event["duplicates"], event["loss"])
            for event in events
        ]
        == [
            ("accepted", 2, 1, "not_observed"),
            ("accepted", 0, 0, "accepted_without_readback"),
            ("rejected", 0, 0, "not_observed"),
            ("accepted", 0, 0, "accepted_without_readback"),
        ],
        "duplicate and loss observations differ",
    )
    foreign = canonical(expected_envelope(spec["seed"], 4, "f" * 64))
    require(
        rows(backend, "SELECT body FROM records ORDER BY rowid")
        == [(clean[1],), (clean[1],), (foreign,)],
        "unexpected backend effects",
    )
    order = (
        [("outage", index) for index in clean]
        + [("lost_ack", 1)]
        + [("replay", index) for index in clean]
    )
    require(
        invoke(source, data, "observe") == receipt, "fresh readback changed evidence"
    )
    altered = json.loads(foreign)
    resource = altered["resourceSpans"][0]
    resource["schemaUrl"] = "https://schema.invalid/" + CANARY
    resource["scopeSpans"][0]["schemaUrl"] = "https://schema.invalid/" + CANARY
    with closing(sqlite3.connect(backend)) as db, db:
        db.execute("INSERT INTO records VALUES(?)", (canonical(altered),))
    privacy = invoke(source, data, "privacy")
    require(
        privacy == dict(receipt, privacy="blocked"),
        "unmatched schema URLs did not block whole-envelope privacy",
    )
    calls = rows(backend, "SELECT phase,event,body_sha256 FROM calls ORDER BY seq")
    require(
        calls == [(phase, number, sha(clean[number])) for phase, number in order],
        "unexpected transport call or envelope digest",
    )
    return {"readback": receipt, "privacy_negative": privacy["privacy"], "calls": calls}


def campaign(source: Path, data: Path, spec: dict[str, Any]) -> dict[str, Any]:
    data.mkdir()
    with closing(sqlite3.connect(data / "backend.sqlite")) as db, db:
        db.execute("CREATE TABLE records(body BLOB NOT NULL)")
        db.execute(
            "CREATE TABLE calls(seq INTEGER PRIMARY KEY,phase TEXT,event INTEGER,body_sha256 TEXT)"
        )
    clean = {
        int(index): canonical(
            expected_envelope(spec["seed"], int(index), spec["policy_sha256"])
        )
        for index in spec["units"]
    }
    interrupted = check_before_replay(source, data, spec, clean)
    return dict(check_replay(source, data, spec, clean), interrupted=interrupted)


def mutation(source: Path, scratch: Path, spec: dict[str, Any]) -> str:
    clone = scratch / "mutated"
    shutil.copytree(source, clone)
    path = clone / "tools/disposable_harness/telemetry.py"
    text = path.read_text()
    exact = "canonical(record) == body"
    require(text.count(exact) == 1, "readback mutation anchor drift")
    path.write_text(text.replace(exact, "event_id(record) == identity"))
    try:
        campaign(clone, scratch / "mutated-result", spec)
    except AssertionError as error:
        require(
            str(error)
            == "readback conflated partial correlation, rejection, or acceptance",
            "mutation failed outside the readback oracle",
        )
        return "match_event_id_without_bound_context"
    raise AssertionError("readback mutation escaped")


def run() -> dict[str, Any]:
    raw = MANIFEST.read_bytes()
    spec = json.loads(raw)
    require(
        spec["version"] == "runspindle.platform-telemetry-hero.v1"
        and spec["phases"] == PHASES
        and list(spec["units"]) == ["1", "2", "3", "4"],
        "invalid H08 schedule",
    )
    with TemporaryDirectory(prefix="runspindle-h08-") as directory:
        scratch = Path(directory).resolve()
        source = scratch / "platform"
        pins = stage_source(source, spec, component="platform")
        observed = campaign(source, scratch / "first", spec)
        require(
            observed == campaign(source, scratch / "second", spec),
            "campaign outcomes changed",
        )
        return {
            "scenario": "H08",
            "hero_acceptance": "blocked",
            "platform_lane": "passed",
            "repeat_runs": 2,
            "observed": observed,
            "scope": spec["scope"],
            "mutation_detected": mutation(source, scratch, spec),
            "composition_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
            "component_pins": pins,
            "scenario_sha256": sha(raw),
            "lock_sha256": sha((ROOT / "composition.lock.json").read_bytes()),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "optimized": sys.flags.optimize,
            "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        value = worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
    elif len(sys.argv) == 1:
        value = run()
    else:
        raise SystemExit(
            "run with no arguments and the pinned Platform submodule initialized"
        )
    print(json.dumps(value, sort_keys=True))
