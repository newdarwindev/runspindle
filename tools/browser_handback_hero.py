#!/usr/bin/env python3
"""H06 Browser-only lane with synthetic authority, viewer closure and input."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing, contextmanager
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
MANIFEST = ROOT / "scenarios/browser-handback-v1.json"
LEASE_SOURCE = "browser_runtime/control_leases.py"
SOURCES = {
    f"browser_runtime/{name}.py"
    for name in (
        "__init__",
        "control_leases",
        "credentials",
        "effect_schema",
        "effects",
        "guarded_effects",
    )
}
CLOSE_GUARD = "or observed.previous_inputs_closed is not True):"


def require(value: object, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], timeout=15)


def stage_sources(stage: Path, spec: dict[str, Any]) -> dict[str, str]:
    entries = json.loads((ROOT / "composition.lock.json").read_bytes())["components"]
    pins: dict[str, str] = {entry["component"]: entry["commit"] for entry in entries}
    require(
        len(entries) == 7
        and set(pins)
        == {"browser", "console", "core", "host", "platform", "refinery", "tether"},
        "invalid pin inventory",
    )
    for name, commit in pins.items():
        path = f"components/{name}"
        require(
            git(ROOT, "ls-files", "--stage", "--", path).decode().strip()
            == f"160000 {commit} 0\t{path}",
            "composition gitlink mismatch",
        )
    source = ROOT / "components/browser"
    require(pins["browser"] == spec["browser_commit"], "scenario Browser pin mismatch")
    require(
        source.is_dir()
        and not source.is_symlink()
        and git(source, "rev-parse", "--show-toplevel").decode().strip() == str(source)
        and git(source, "rev-parse", "HEAD").decode().strip() == pins["browser"]
        and not git(source, "status", "--porcelain"),
        "clean pinned Browser required",
    )
    require(set(spec["source_sha256"]) == SOURCES, "invalid Browser source closure")
    for relative, digest in spec["source_sha256"].items():
        data = git(source, "show", f"{pins['browser']}:{relative}")
        require(sha(data) == digest, "Browser source digest mismatch")
        destination = stage / relative
        destination.parent.mkdir(exist_ok=True, parents=True)
        destination.write_bytes(data)
    return pins


def worker(source: Path, data: Path, mode: str) -> str:
    def audit(event: str, _: tuple[object, ...]) -> None:
        if event.startswith("socket.") or event in {
            "os.exec",
            "os.fork",
            "os.forkpty",
            "os.posix_spawn",
            "os.system",
            "subprocess.Popen",
        }:
            (data / "forbidden").write_text("external effect attempted\n")
            raise RuntimeError("external effect forbidden")

    sys.addaudithook(audit)
    sys.path.insert(0, str(source))
    leases = import_module("browser_runtime.control_leases")
    credentials = import_module("browser_runtime.credentials")
    guarded = import_module("browser_runtime.guarded_effects")
    effects = import_module("browser_runtime.effects")
    spec = json.loads(MANIFEST.read_bytes())
    now = float(spec["clock"])
    deadline = now + 10
    payload = spec["payload"].encode()
    binding = effects.Binding(**spec["binding"], operation="scope", epoch=1)
    target = credentials.Target(binding, **spec["target"])
    agent, human = (
        leases.Holder("agent", "synthetic-agent"),
        leases.Holder("human", "synthetic-human"),
    )
    ticket = object()

    def at(epoch: int, operation: str) -> Any:
        return replace(
            target, binding=replace(binding, epoch=epoch, operation=operation)
        )

    init = leases.Transfer(at(1, "initialize"), "initialize", None, agent, 0, deadline)
    takeover = leases.Transfer(at(2, "takeover"), "takeover", agent, human, 1, deadline)
    handback = leases.Transfer(at(3, "handback"), "handback", human, agent, 2, deadline)

    def record(call: str) -> None:
        with (data / "helper-ledger").open("a", encoding="utf-8") as log:
            log.write(call + "\n")
            log.flush()
            os.fsync(log.fileno())

    class Adapter:
        grant: Any = None
        held = False
        release = False
        observation = "incomplete"

        @contextmanager
        def acquire(self) -> Iterator[Adapter]:
            require(not self.held, "nested backend fence")
            self.held = True
            try:
                yield self
            finally:
                self.held = False

        def admit(self, presented: object) -> Any:
            return self.grant if self.held and presented is ticket else None

        def current(self, supplied: object) -> bool:
            return self.held and supplied is self.grant

        def observe(self) -> Any:
            return credentials.Observation(target, now)

        def released(self, grant: Any) -> bool:
            return (
                self.held
                and self.release
                and (grant == handback or grant == leases.Recovery(handback, deadline))
            )

        def fence(self, transfer: Any, guard: object) -> Any:
            require(guard is self and self.current(transfer), "unfenced transfer")
            record("fence:" + str(transfer.action))
            if mode == "interrupt":
                os._exit(73)
            return leases.FenceReceipt(transfer, True)

        def inspect(self, recovery: Any, guard: object) -> Any:
            require(guard is self and self.current(recovery), "unfenced readback")
            require(
                "fence:handback" in (data / "helper-ledger").read_text().splitlines(),
                "synthetic backend has no retained handback attempt",
            )
            record("inspect:" + self.observation)
            observed = (
                handback
                if self.observation != "wrong-target"
                else replace(handback, target=at(3, "other-transfer"))
            )
            return leases.FenceObservation(
                observed,
                self.observation != "incomplete",
                now - 2 if self.observation == "stale" else now,
            )

        def submit(self, supplied: Any, value: bytes, guard: Any) -> None:
            require(
                self.held and guard.current(supplied) is True and value == payload,
                "unfenced input",
            )
            record("input:" + str(supplied.target.binding.operation))

        def readback(self, _supplied: object, _guard: object) -> Any:
            record("unexpected-input-readback")
            raise ValueError("unexpected input readback")

    adapter = Adapter()
    with closing(
        leases.LeaseStore(
            data / "leases.sqlite",
            authority=adapter,
            backend=adapter,
            inspector=adapter,
            clock=lambda: now,
        )
    ) as lease:
        with closing(lease.journal(data / "inputs.sqlite", adapter)) as journal:

            def transfer(grant: Any, *, recover: bool = False) -> str:
                adapter.grant = grant
                try:
                    return str(
                        lease.reconcile_transfer(ticket)
                        if recover
                        else lease.transfer(ticket)
                    )
                except effects.Denied:
                    return "denied"

            def command(holder: Any, epoch: int, operation: str) -> str:
                adapter.grant = (
                    None
                    if holder is None
                    else leases.Input(
                        guarded.Grant(
                            at(epoch, operation), sha(payload), "dispatch", deadline
                        ),
                        holder,
                    )
                )
                try:
                    return str(journal.dispatch(ticket, payload))
                except effects.Denied:
                    return "denied"

            recovery = leases.Recovery(handback, deadline)
            if mode == "takeover":
                require(transfer(init) == "active", "initial agent lease missing")
                require(
                    command(None, 1, "observation") == "denied",
                    "observation supplied input authority",
                )
                require(transfer(takeover) == "active", "human takeover failed")
                require(
                    command(agent, 1, "stale-agent") == "denied",
                    "old agent epoch reached input",
                )
                require(
                    command(agent, 2, "wrong-holder") == "denied",
                    "wrong holder reached input",
                )
                require(
                    command(human, 2, "human-input") == "unknown",
                    "human input was not attempted",
                )
                return transfer(handback)
            adapter.release = True
            if mode in {"interrupt", "replay"}:
                return transfer(handback)
            if mode == "recover":
                require(
                    command(agent, 3, "pending-agent") == "denied",
                    "pending agent reached input",
                )
                require(
                    command(human, 2, "pending-human") == "denied",
                    "pending human reached input",
                )
                adapter.release = False
                require(
                    transfer(recovery, recover=True) == "denied",
                    "forged recovery release accepted",
                )
                adapter.release = True
                if transfer(recovery, recover=True) != "unknown":
                    return "incomplete closure accepted"
                adapter.observation = "wrong-target"
                require(
                    transfer(recovery, recover=True) == "unknown",
                    "mismatched closure accepted",
                )
                adapter.observation = "stale"
                require(
                    transfer(recovery, recover=True) == "denied",
                    "stale closure accepted",
                )
                return "unknown"
            require(mode == "resume", "invalid worker mode")
            adapter.observation = "fresh"
            require(
                transfer(recovery, recover=True) == "active",
                "fresh closure could not restore agent",
            )
            require(
                transfer(recovery, recover=True) == "active",
                "exact recovery replay changed",
            )
            require(
                command(human, 2, "stale-human") == "denied",
                "old human lease reached input",
            )
            return command(agent, 3, "agent-resumed")


def invoke(source: Path, data: Path, mode: str, expected_exit: int = 0) -> str:
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
        env={"PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=15,
    )
    require(not (data / "forbidden").exists(), "external call attempted")
    require(
        result.returncode == expected_exit, "unexpected worker termination: " + mode
    )
    return result.stdout.strip()


def rows(path: Path, query: str) -> list[tuple[Any, ...]]:
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as observer:
        return observer.execute(query).fetchall()


def run_once(source: Path, data: Path) -> dict[str, object]:
    data.mkdir()
    require(invoke(source, data, "takeover") == "denied", "forged handback accepted")
    invoke(source, data, "interrupt", 73)
    lease_query = "SELECT epoch,phase,holder FROM leases"
    lease_path = data / "leases.sqlite"
    agent = '{"identity":"synthetic-agent","kind":"agent"}'
    require(
        rows(lease_path, lease_query) == [(3, "pending", agent)],
        "lost pending handback",
    )
    require(
        invoke(source, data, "replay") == "unknown", "interrupted request was repeated"
    )
    require(
        invoke(source, data, "recover") == "unknown", "incomplete closure was accepted"
    )
    require(
        rows(lease_path, lease_query) == [(3, "pending", agent)],
        "unconfirmed handback changed lease",
    )
    require(
        invoke(source, data, "resume") == "unknown", "resumed input was not attempted"
    )
    require(
        rows(lease_path, lease_query) == [(3, "active", agent)],
        "active agent epoch missing",
    )
    calls = (data / "helper-ledger").read_text().splitlines()
    require(
        calls
        == [
            "fence:initialize",
            "fence:takeover",
            "input:human-input",
            "fence:handback",
            "inspect:incomplete",
            "inspect:wrong-target",
            "inspect:stale",
            "inspect:fresh",
            "input:agent-resumed",
        ],
        "independent helper call ledger mismatch",
    )
    require(
        rows(
            data / "inputs.sqlite",
            "SELECT operation,outcome FROM operations ORDER BY operation",
        )
        == [("agent-resumed", "unknown"), ("human-input", "unknown")],
        "independent input journal mismatch",
    )
    return {"calls": calls, "final_epoch": 3, "failed_closed_on_crash": True}


def run() -> dict[str, object]:
    raw = MANIFEST.read_bytes()
    spec = json.loads(raw)
    require(
        spec["version"] == "runspindle.browser-handback-hero.v1"
        and spec["repeat_runs"] == 2,
        "invalid H06 manifest",
    )
    with TemporaryDirectory(prefix="h06-browser-handback-") as directory:
        root = Path(directory)
        source = root / "source"
        pins = stage_sources(source, spec)
        first = run_once(source, root / "first")
        require(
            run_once(source, root / "second") == first, "non-repeatable observations"
        )
        mutant_path = source / LEASE_SOURCE
        code = mutant_path.read_text()
        require(code.count(CLOSE_GUARD) == 1, "closure mutation anchor changed")
        mutant_path.write_text(code.replace(CLOSE_GUARD, "or False):"))
        try:
            run_once(source, root / "mutation")
        except ValueError as error:
            require(
                str(error) == "incomplete closure was accepted",
                "mutation failed outside behavior check",
            )
        else:
            raise ValueError("mutation was not detected")
    return {
        "status": "passed",
        "scenario": "H06",
        "evidence_class": "real_browser_only",
        "system_acceptance": "blocked",
        "python": sys.version.split()[0],
        "real": ["Browser control lease", "Browser input journal", "SQLite"],
        "synthetic": [
            "actor and release authority",
            "viewer fence and readback",
            "site input",
        ],
        "not_run": ["Console viewer", "Core ownership", "PinchTab and KasmVNC"],
        "composition_commit": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "component_pins": pins,
        "manifest_sha256": sha(raw),
        "repeat_runs": 2,
        "incomplete_closure_mutation": "detected",
        "observed": first,
    }


def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]))
        return 0
    if len(sys.argv) != 1:
        return 2
    try:
        print(json.dumps(run(), sort_keys=True))
    except (OSError, ValueError, subprocess.SubprocessError):
        print('{"scenario":"H06","status":"failed","system_acceptance":"blocked"}')
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
