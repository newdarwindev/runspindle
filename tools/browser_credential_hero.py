#!/usr/bin/env python3
"""Run H03 with the pinned Browser resolver and Vault against synthetic peers."""

from __future__ import annotations

import contextlib
import io
import json
import platform
import shutil
import subprocess
import sys
import traceback
from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from tools.browser_effect_hero import git, require, sha, stage_source  # noqa: E402

MANIFEST = ROOT / "scenarios/browser-credential-scope-v1.json"
CASES = {
    "authorized": ("injected", ["data", "metadata", "helper", "metadata", "injection"]),
    "wrong_account": ("denied", []),
    "wrong_origin": ("denied", []),
    "wrong_frame_origin": ("denied", []),
    "wrong_epoch": ("denied", []),
    "wrong_native_session": ("denied", []),
    "old_revision": ("denied", []),
    "stale_observation": ("denied", []),
    "missing_observation": ("denied", []),
    "redirect_at_read": ("denied", ["data"]),
    "redirect_at_version_check": ("denied", ["data", "metadata"]),
    "revoked_at_read": ("denied", ["data"]),
    "expired_at_read": ("denied", ["data"]),
    "rotated_version": ("denied", ["data", "metadata"]),
    "provider_timeout": ("denied", ["data"]),
    "provider_redirect": ("denied", ["data"]),
}


class Peers:
    """Synthetic authority and browser sink around the existing fake OpenBao peer."""

    def __init__(self, mode: str, ledger: Path) -> None:
        self.credentials = import_module("browser_runtime.credentials")
        self.openbao = import_module("browser_runtime.openbao")
        fixtures = import_module("test_openbao")
        self.peer = fixtures.Fixture()
        self.canaries = (str(fixtures.CANARY), str(fixtures.TOKEN))
        self.mode, self.ledger = mode, ledger
        self.ticket = object()
        original = self.peer.g.target
        self.target = replace(original, binding=replace(original.binding, revision=2))
        self.peer.g = replace(self.peer.g, target=self.target)
        self.active = self.used = self.revoked = False
        self.tokens = 0
        self.vault = self.openbao.Vault(
            (self.peer.m,),
            transport=self.transport,
            token=self.token,
            authorize=self.current,
            clock=lambda: self.peer.now,
        )
        if mode == "rotated_version":
            self.peer.current = 2
        if mode == "provider_timeout":
            self.peer.response = TimeoutError(self.canaries[0])
        if mode == "provider_redirect":
            self.peer.response = self.openbao.Response(302, self.canaries[0].encode())

    def record(self, call: str) -> None:
        require(self.active, "effect outside the scoped guard")
        with self.ledger.open("a", encoding="utf-8") as stream:
            stream.write(call + "\n")

    @contextlib.contextmanager
    def acquire(self) -> Iterator[Peers]:
        require(not self.active, "recursive fixture fence")
        self.active = True
        try:
            yield self
        finally:
            self.active = False

    def admit(self, ticket: object) -> Any:
        if self.used or ticket is not self.ticket:
            return None
        self.used = True
        return self.peer.g

    def current(self, grant: object) -> bool:
        return self.active and not self.revoked and grant is self.peer.g

    def observe(self) -> Any:
        if self.mode == "missing_observation":
            return None
        binding, target = self.target.binding, self.target
        if self.mode == "wrong_account":
            target = replace(target, binding=replace(binding, account="other"))
        elif self.mode == "wrong_origin":
            target = replace(
                target, binding=replace(binding, origin="https://wrong.invalid")
            )
        elif self.mode == "wrong_epoch":
            target = replace(target, binding=replace(binding, epoch=binding.epoch + 1))
        elif self.mode == "old_revision":
            target = replace(
                target, binding=replace(binding, revision=binding.revision - 1)
            )
        elif self.mode == "wrong_native_session":
            target = replace(target, native_session="other")
        elif self.mode == "wrong_frame_origin":
            target = replace(target, frame_origin="https://wrong.invalid")
        now = self.peer.now - 2 if self.mode == "stale_observation" else self.peer.now
        return self.credentials.Observation(target, now)

    def token(self) -> str:
        self.tokens += 1
        return self.canaries[1]

    def transport(self, path: str, token: str, timeout: float) -> Any:
        base = "/v1/kv"
        paths = {
            f"{base}/data/accounts/a": "data",
            f"{base}/metadata/accounts/a": "metadata",
        }
        require(
            path in paths and token == self.canaries[1] and 0 < timeout <= 2,
            "wrong vault route",
        )
        call = paths[path]
        self.record(call)
        if (self.mode, call) in (
            ("redirect_at_read", "data"),
            ("redirect_at_version_check", "metadata"),
        ):
            self.target = replace(self.target, frame_origin="https://redirect.invalid")
        if self.mode == "revoked_at_read":
            self.revoked = True
        if self.mode == "expired_at_read":
            self.peer.now = self.peer.g.deadline
        return self.peer.transport(path, token, timeout)

    def inject(self, handle: object, grant: Any, fence: object) -> bool:
        self.record("helper")
        if fence is not self or not self.current(grant) or self.target != grant.target:
            return False
        return self.vault.consume(handle, grant, self.sink) is True

    def sink(self, value: str) -> bool:
        require(value == self.canaries[0], "wrong secret delivered to scoped sink")
        self.record("injection")
        return True

    def attempt(self, resolver: Any) -> str:
        try:
            return str(resolver.resolve_and_inject(self.ticket))
        except self.credentials.Denied as error:
            require(
                error.__cause__ is None and error.__context__ is None,
                "provider error leaked",
            )
            rendered = "".join(traceback.format_exception(error))
            require(
                all(value not in rendered for value in self.canaries),
                "secret leaked in error",
            )
            require(
                str(error) == "credential resolution denied", "unexpected denial detail"
            )
            return "denied"


def worker(source: Path, data: Path, mode: str) -> dict[str, str | int]:
    def audit(event: str, _: tuple[object, ...]) -> None:
        if event.startswith("socket.") or event in {
            "subprocess.Popen",
            "os.exec",
            "os.fork",
            "os.forkpty",
            "os.posix_spawn",
            "os.system",
        }:
            (data / "forbidden").touch()
            raise RuntimeError("external effect forbidden")

    sys.addaudithook(audit)
    sys.path[:0] = [str(source), str(source / "tests")]
    peers = Peers(mode, data / "effects")
    pin = sha(b"runspindle:h03:synthetic-adapters")
    adapters = peers.credentials.AdapterSet(pin, peers, peers.vault, peers)
    resolver = peers.credentials.Resolver(
        adapters, expected_digest=pin, clock=lambda: peers.peer.now
    )
    observed = io.StringIO()
    with contextlib.redirect_stdout(observed), contextlib.redirect_stderr(observed):
        result: dict[str, str | int] = {
            "outcome": peers.attempt(resolver),
            "replay": peers.attempt(resolver),
            "new_resolver_replay": peers.attempt(
                peers.credentials.Resolver(
                    adapters, expected_digest=pin, clock=lambda: peers.peer.now
                )
            ),
            "token_reads": peers.tokens,
        }
    require(
        not peers.active and not peers.vault._entries, "guard or vault handle retained"
    )
    envelope = observed.getvalue() + repr(result) + repr(adapters) + repr(peers.peer.g)
    require(
        all(value not in envelope for value in peers.canaries),
        "secret leaked in outcome",
    )
    require(not observed.getvalue(), "unexpected adapter output")
    return result


def scenario(source: Path, data: Path, mode: str) -> dict[str, object]:
    data.mkdir()
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
    require(not (data / "forbidden").exists(), "unexpected external effect for " + mode)
    require(
        result.returncode == 0 and not result.stderr,
        "credential worker failed: " + mode,
    )
    outcome, expected = CASES[mode]
    ledger = data / "effects"
    calls = ledger.read_text().splitlines() if ledger.exists() else []
    require(calls == expected, "unexpected effect ledger for " + mode)
    require(
        json.loads(result.stdout)
        == {
            "outcome": outcome,
            "replay": "denied",
            "new_resolver_replay": "denied",
            "token_reads": sum(call in ("data", "metadata") for call in expected),
        },
        "wrong credential outcome for " + mode,
    )
    return {"fault": mode, "outcome": outcome, "effects": calls}


def detect_mutation(source: Path, scratch: Path) -> str:
    clone = scratch / "mutated"
    shutil.copytree(source, clone)
    path = clone / "browser_runtime/credentials.py"
    text = path.read_text()
    condition = "not 0 <= now - observed_at <= self._max_age"
    require(text.count(condition) == 1, "freshness mutation anchor differs")
    path.write_text(text.replace(condition, "False"))
    result = scratch / "mutated-result"
    try:
        scenario(clone, result, "stale_observation")
    except AssertionError as error:
        require(
            str(error) == "unexpected effect ledger for stale_observation",
            "mutation failed outside the effect oracle",
        )
        require(
            (result / "effects").read_text().splitlines() == CASES["authorized"][1],
            "mutation did not reach the scoped sink",
        )
        return "ignore_observation_age"
    raise AssertionError("observation age mutation escaped")


def run() -> dict[str, object]:
    raw = MANIFEST.read_bytes()
    spec = json.loads(raw)
    require(
        spec["version"] == "runspindle.browser-credential-hero.v1"
        and spec["cases"] == list(CASES),
        "unknown credential fixture contract",
    )
    with TemporaryDirectory(prefix="runspindle-h03-") as directory:
        scratch = Path(directory).resolve()
        source = scratch / "source"
        pins = stage_source(source, spec)
        runs = [
            [scenario(source, scratch / f"{i}-{mode}", mode) for mode in CASES]
            for i in range(2)
        ]
        require(runs[0] == runs[1], "credential outcomes differ across campaigns")
        return {
            "scenario": "H03",
            "hero_acceptance": "blocked",
            "browser_lane": "passed",
            "repeat_runs": 2,
            "case_results": runs[0],
            "mutation_detected": detect_mutation(source, scratch),
            "scope": spec["scope"],
            "component_pins": pins,
            "composition_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
            "lock_sha256": sha((ROOT / "composition.lock.json").read_bytes()),
            "scenario_sha256": sha(raw),
            "python": platform.python_version(),
            "optimized": sys.flags.optimize,
            "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(
            json.dumps(
                worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]),
                sort_keys=True,
            )
        )
    elif len(sys.argv) == 1:
        print(json.dumps(run(), sort_keys=True))
    else:
        raise SystemExit(
            "run with no arguments and an initialized pinned Browser submodule"
        )
