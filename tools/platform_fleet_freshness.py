"""Exercise the exact pinned Platform fleet observer with scripted external ports."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scenarios/platform-fleet-freshness-v1.json"
VERSION = "runspindle.platform-fleet-freshness.v1"
UNIT_QUERY = [
    "systemctl",
    "show",
    "runspindle-fleet.service",
    "--property=ActiveState,SubState,UnitFileState,MainPID",
]
CALLS = [
    ["service", UNIT_QUERY, False],
    ["guest", "observe", 0],
    ["guest", "observe", 1],
]
IDENTITY = "0" * 31 + "1"
JOB = {"repository": "synthetic/fleet", "id": 41}
SOURCE_MODULES = (
    "__init__",
    "backend",
    "identity",
    "lifecycle",
    "manager",
    "model",
    "quality",
    "retention",
    "service",
    "state",
)


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(directory: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", *args],
        cwd=directory,
        timeout=15,
        stderr=subprocess.PIPE,
    )


def stage_source(stage: Path, expected: dict[str, str]) -> dict[str, Any]:
    lock_bytes = (ROOT / "composition.lock.json").read_bytes()
    lock = json.loads(lock_bytes)
    actual = {entry["component"]: entry["commit"] for entry in lock["components"]}
    require(actual == expected, "composition lock differs from the reviewed fixture")
    for component, commit in expected.items():
        path = f"components/{component}"
        link = git(ROOT, "ls-files", "--stage", "--", path).decode().strip()
        require(link == f"160000 {commit} 0\t{path}", f"gitlink mismatch: {component}")

    platform = ROOT / "components/platform"
    pin = expected["platform"]
    require(
        git(platform, "rev-parse", "HEAD").decode().strip() == pin,
        "wrong Platform checkout",
    )
    hashes = {}
    for name in SOURCE_MODULES:
        relative = PurePosixPath("tools/runner_fleet", name + ".py")
        source = f"{pin}:{relative}"
        require(
            git(platform, "cat-file", "-t", source).strip() == b"blob",
            f"missing blob: {relative}",
        )
        data = git(platform, "cat-file", "blob", source)
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[str(relative)] = sha(data)
    return {
        "composition_commit": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "composition_lock_sha256": sha(lock_bytes),
        "harness_sha256": sha(Path(__file__).read_bytes()),
        "components": actual,
        "platform_files_sha256": hashes,
    }


def guests(case: dict[str, Any]) -> list[dict[str, Any]]:
    active = {"slot": 0, "ActiveState": "active", "MainPID": "271"}
    idle = {"slot": 0, "ActiveState": "inactive", "MainPID": "0"}
    slot_zero = {
        "idle": idle,
        "owned": active | {"resource_id": IDENTITY},
        "old_owner": active | {"resource_id": "0" * 31 + "2"},
    }[case["guest"]]
    slot_one = (
        {"slot": 1, "ActiveState": "unknown"}
        if case.get("missing_guest")
        else idle | {"slot": 1}
    )
    return [slot_zero, slot_one]


def worker(stage: Path, directory: Path, request: dict[str, Any]) -> dict[str, Any]:
    escapes: list[str] = []
    observing = request["action"] == "observe"

    def deny_external(event: str, args: tuple[Any, ...]) -> None:
        network_or_process = (
            event.startswith(
                ("socket.", "subprocess.", "os.exec", "os.spawn", "os.posix_spawn")
            )
            or event == "os.system"
        )
        filesystem_change = (
            event
            in {
                "os.chmod",
                "os.chown",
                "os.link",
                "os.mkdir",
                "os.remove",
                "os.rename",
                "os.rmdir",
                "os.symlink",
                "os.truncate",
            }
            or event == "open"
            and bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        )
        if network_or_process or observing and filesystem_change:
            escapes.append(event)
            raise PermissionError(event)

    sys.addaudithook(deny_external)
    sys.path.insert(0, str(stage))
    state = importlib.import_module("tools.runner_fleet.state")
    case = request["case"]
    now = request["now"]
    if request["action"] == "seed":
        with patch.multiple(
            state,
            time=SimpleNamespace(time=lambda: now),
            uuid=SimpleNamespace(uuid4=lambda: SimpleNamespace(hex=IDENTITY)),
        ):
            seed = state.State(directory)
            try:
                seed.set("drained", case.get("drained", False))
                for field in ("heartbeat", "poll_at"):
                    offset = case.get(field, 1)
                    if offset is not None:
                        seed.set(field, now - offset)
                if case.get("reserved"):
                    seed.update(seed.reserve(JOB), "running")
            finally:
                seed.db.close()
        return {"forbidden": escapes}

    service = importlib.import_module("tools.runner_fleet.service")
    calls: list[list[Any]] = []
    inputs = guests(case)

    def execute(argv: list[str], *, check: bool) -> SimpleNamespace:
        calls.append(["service", argv, check])
        require(argv == UNIT_QUERY and check is False, "unexpected service command")
        return SimpleNamespace(
            stdout=""
            if case.get("manager_outage")
            else "ActiveState=active\nSubState=running\nUnitFileState=enabled\nMainPID=170\n"
        )

    def helper(action: str, slot: int) -> dict[str, Any]:
        calls.append(["guest", action, slot])
        require(
            action == "observe" and type(slot) is int and slot in (0, 1),
            "unexpected guest command",
        )
        return inputs[slot].copy()

    def authorize_sql(
        action: int,
        first: str | None,
        second: str | None,
        schema: str | None,
        trigger: str | None,
    ) -> int:
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ):
            return sqlite3.SQLITE_OK
        escapes.append(f"sqlite:{action}")
        return sqlite3.SQLITE_DENY

    # Exercise State reads against SQLite's read-only mode while keeping its
    # schema-initializing constructor in the fixture setup process.
    uri = (directory / "fleet.sqlite").as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as database:
        database.row_factory = sqlite3.Row
        database.set_authorizer(authorize_sql)
        reader = state.State.__new__(state.State)
        reader.directory, reader.db = directory, database

        def open_state(requested: Path) -> Any:
            require(requested == directory, "unexpected fleet database")
            calls.append(["store", "read", "fleet.sqlite"])
            return reader

        with patch.multiple(
            service,
            State=open_state,
            execute=execute,
            helper=helper,
            time=SimpleNamespace(time=lambda: now),
        ):
            result = service.observed(directory)
    return {"calls": calls, "forbidden": escapes, "result": result}


def invoke(stage: Path, directory: Path, **request: Any) -> dict[str, Any]:
    optimized = ["-O"] if sys.flags.optimize else []
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            *optimized,
            str(Path(__file__).resolve()),
            "--worker",
            str(stage),
            str(directory),
        ],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=15,
        cwd=stage,
        env={"LC_ALL": "C", "TZ": "UTC"},
    )
    require(result.returncode == 0, f"fleet worker failed: {result.stderr.strip()}")
    return dict(json.loads(result.stdout))


def inspect(directory: Path) -> dict[str, Any]:
    path = directory / "fleet.sqlite"
    # Read the seed evidence independently of Platform's State and observer.
    with closing(
        sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as database:
        return {
            "control": {
                key: json.loads(value)
                for key, value in database.execute(
                    "SELECT key, value FROM control ORDER BY key"
                )
            },
            "reservations": database.execute(
                "SELECT id, slot, repository, requested_job, runner_name, phase FROM resources ORDER BY id"
            ).fetchall(),
            "events": database.execute(
                "SELECT resource, kind FROM events ORDER BY id"
            ).fetchall(),
            "mac_jobs": database.execute(
                "SELECT count(*) FROM mac_job_observations"
            ).fetchone()[0],
            "schema_sha256": sha(
                "\n".join(
                    row[0]
                    for row in database.execute(
                        "SELECT sql FROM sqlite_schema WHERE sql IS NOT NULL ORDER BY name"
                    )
                ).encode()
            ),
            "store_sha256": sha(path.read_bytes()),
        }


def observe(
    stage: Path, directory: Path, case: dict[str, Any], now: int
) -> dict[str, Any]:
    label = case["id"]
    before = inspect(directory)
    expected_resources = (
        [
            (
                IDENTITY,
                0,
                JOB["repository"],
                JOB["id"],
                "runspindle-fleet-" + IDENTITY,
                "running",
            )
        ]
        if case.get("reserved")
        else []
    )
    expected_events = (
        [(IDENTITY, "reserved"), (IDENTITY, "running")] if expected_resources else []
    )
    expected_control = {"drained": case.get("drained", False)}
    for field in ("heartbeat", "poll_at"):
        offset = case.get(field, 1)
        if offset is not None:
            expected_control[field] = now - offset
    require(
        before["control"] == expected_control
        and before["reservations"] == expected_resources
        and before["events"] == expected_events
        and before["mac_jobs"] == 0,
        f"{label}: fixture identity or events differ",
    )

    receipt = invoke(stage, directory, action="observe", case=case, now=now)
    require(
        receipt["calls"] == [["store", "read", "fleet.sqlite"], *CALLS]
        and receipt["forbidden"] == [],
        f"{label}: unexpected external calls",
    )
    after = inspect(directory)
    require(after == before, f"{label}: observer changed durable state")
    projection = receipt["result"]
    expected = case["expected"]
    capacity = projection["capacity"]
    require(
        capacity
        == expected
        | {
            "evidence_class": "capacity_observation",
            "configured_slots": 2,
            "drained": case.get("drained", False),
            "lifecycle_qualification": "not_run",
        }
        and projection["status"] == expected["status"],
        f"{label}: capacity mismatch",
    )
    identity = [
        (
            row["id"],
            row["slot"],
            row["repository"],
            row["requested_job"],
            row["runner_name"],
            row["phase"],
        )
        for row in projection["resources"]
    ]
    observed_heartbeat = before["control"].get("heartbeat")
    require(
        identity == expected_resources
        and projection["guests"] == guests(case)
        and projection["heartbeat"] == observed_heartbeat,
        f"{label}: observed identity or heartbeat differs from input",
    )
    return {
        "case": label,
        "capacity": capacity,
        "guests": projection["guests"],
        "heartbeat": observed_heartbeat,
        "inventory_polled_at": before["control"].get("poll_at"),
        "reservations": identity,
        "events": expected_events,
        "calls": receipt["calls"],
        "forbidden": receipt["forbidden"],
        "durable_changes": 0,
        "schema_sha256": before["schema_sha256"],
    }


def run(*, mutation: bool = False) -> dict[str, Any]:
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    require(manifest["version"] == VERSION, "unsupported fleet freshness fixture")
    with tempfile.TemporaryDirectory(prefix="runspindle-h09-platform-") as temporary:
        scratch = Path(temporary).resolve()
        stage = scratch / "source"
        source = stage_source(stage, manifest["components"])
        if mutation:
            path = stage / "tools/runner_fleet/lifecycle.py"
            data = path.read_text()
            check = 'guest.get("resource_id") != owners[0]["id"]'
            require(data.count(check) == 1, "ownership mutation target changed")
            path.write_text(data.replace(check, "False", 1))
        runs = []
        now = manifest["clock"]
        for repeat in range(2):
            results = []
            for case in manifest["cases"]:
                directory = scratch / str(repeat) / case["id"]
                seed = invoke(stage, directory, action="seed", case=case, now=now)
                require(
                    seed["forbidden"] == [], "unexpected fixture setup external calls"
                )
                results.append(observe(stage, directory, case, now))
                if case["id"] == "old-owner":
                    fresh = next(
                        c for c in manifest["cases"] if c["id"] == "fresh-owned"
                    )
                    results.append(
                        observe(
                            stage, directory, fresh | {"id": "owner-recovered"}, now
                        )
                    )
            runs.append(results)
        require(runs[0] == runs[1], "normalized observations differed between repeats")
    return source | {
        "version": VERSION,
        "fixture_sha256": sha(manifest_bytes),
        "toolchain": {
            "python": sys.version.split()[0],
            "sqlite": sqlite3.sqlite_version,
        },
        "clock": now,
        "repeat_runs": len(runs),
        "observations": runs[0],
        "real_component": "platform",
        "sibling_components": "synthetic",
        "lane": "passed",
        "system_aggregate": "blocked",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worker", nargs=2, metavar=("SOURCE", "STORE"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    try:
        output = (
            worker(Path(args.worker[0]), Path(args.worker[1]), json.load(sys.stdin))
            if args.worker
            else run()
        )
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
