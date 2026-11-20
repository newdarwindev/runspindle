#!/usr/bin/env python3
"""H04 against the pinned Browser Python adapters and synthetic external peers."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
import time
from contextlib import closing, contextmanager
from dataclasses import replace
from importlib import import_module, metadata
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
MANIFEST = ROOT / "scenarios/browser-profile-v1.json"
DIRECTORY = "browser_runtime/profile_directory.py"
TOMBSTONE = (
    "super()._forget(guard, grant)  # Durable permanent tombstone precedes all IO."
)
EXPECTED_COMPONENTS = {
    "core",
    "host",
    "browser",
    "tether",
    "console",
    "refinery",
    "platform",
}


def require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], timeout=15)


def stage_sources(stage: Path, spec: dict[str, Any]) -> dict[str, str]:
    entries = json.loads((ROOT / "composition.lock.json").read_bytes())["components"]
    pins = {entry["component"]: entry["commit"] for entry in entries}
    require(
        len(entries) == 7 and set(pins) == EXPECTED_COMPONENTS,
        "component pin inventory",
    )
    for name, revision in pins.items():
        path = "components/" + name
        require(
            git(ROOT, "ls-files", "-s", "--", path).decode().strip()
            == f"160000 {revision} 0\t{path}",
            "composition gitlink mismatch",
        )
    browser = ROOT / "components/browser"
    require(browser.is_dir() and not browser.is_symlink(), "Browser checkout required")
    require(
        git(browser, "rev-parse", "--show-toplevel").decode().strip() == str(browser)
        and git(browser, "rev-parse", "HEAD").decode().strip() == spec["browser_commit"]
        and pins["browser"] == spec["browser_commit"]
        and not git(browser, "status", "--porcelain"),
        "clean pinned Browser required",
    )
    for relative, expected in spec["source_sha256"].items():
        relative_path = Path(relative)
        require(
            not relative_path.is_absolute() and ".." not in relative_path.parts,
            "invalid staged source path",
        )
        data = git(browser, "show", f"{pins['browser']}:{relative}")
        require(sha(data) == expected, "staged Browser source digest mismatch")
        target = stage / relative_path
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_bytes(data)
    return pins


def no_external_operations(root: Path) -> None:
    def audit(event: str, _: tuple[object, ...]) -> None:
        if event.startswith("socket.") or event in {
            "os.exec",
            "os.fork",
            "os.forkpty",
            "os.posix_spawn",
            "os.system",
            "subprocess.Popen",
        }:
            (root / "forbidden").write_text("operation denied\n")
            raise RuntimeError("worker external operation denied")

    sys.addaudithook(audit)


def wait_for(path: Path) -> None:
    deadline = time.monotonic() + 5
    while not path.is_file():
        require(time.monotonic() < deadline, "worker barrier timed out")
        time.sleep(0.01)


def read_db(path: Path, query: str) -> list[tuple[Any, ...]]:
    with closing(
        sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    ) as db:
        return db.execute(query).fetchall()


def scan(root: Path, values: tuple[bytes, ...]) -> int:
    patterns = (*values, *(base64.b64encode(item) for item in values))
    count = 0
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            data = path.read_bytes()
            count += any(pattern in data for pattern in patterns)
    return count


def credential_case(profile_grant: Any, spec: dict[str, Any]) -> dict[str, Any]:
    auth = import_module("browser_runtime.credentials")
    openbao = import_module("browser_runtime.openbao")
    clock = float(spec["clock"])
    target = profile_grant.target
    binding = target.binding
    ticket = object()
    grant = auth.Grant(target, "h04-credential", clock + 10)
    password = "SYNTHETIC_H04_CREDENTIAL"
    provider_calls: list[str] = []
    writes: list[str] = []
    provider_deleted = False

    class Fence:
        @contextmanager
        def acquire(self) -> Iterator[Fence]:
            yield self

        def admit(self, value: object) -> Any:
            return grant if value is ticket else None

        def observe(self) -> Any:
            return auth.Observation(target, clock)

        def current(self, value: object) -> bool:
            return value is grant

        def inject(self, handle: object, supplied: Any, fence: object) -> bool:
            require(fence is self and supplied is grant, "injection binding changed")
            return bool(vault.consume(handle, supplied, write_once))

    def write_once(secret: str) -> bool:
        require(secret == password, "synthetic credential changed")
        writes.append("injected_under_separate_grant")
        return True

    def provider(path: str, token: str, timeout: float) -> Any:
        require(token == "SYNTHETIC_H04_TOKEN" and 0 < timeout <= 2, "provider scope")
        endpoint = path.split("/")[3]
        provider_calls.append(endpoint)
        if provider_deleted:
            return openbao.Response(404, b"{}")
        version = {"deletion_time": "", "destroyed": False}
        if endpoint == "data":
            data = {
                "metadata": {**version, "version": 1},
                "data": {"password": password},
            }
        else:
            require(endpoint == "metadata", "unexpected provider endpoint")
            data = {"current_version": 1, "versions": {"1": version}}
        return openbao.Response(200, json.dumps({"data": data}).encode())

    scope = openbao.Mapping(
        binding.principal,
        binding.account,
        binding.origin,
        target.frame_origin,
        grant.reference,
        "kv",
        ("h04", "a"),
        "password",
    )
    vault = openbao.Vault(
        (scope,),
        transport=provider,
        token=lambda: "SYNTHETIC_H04_TOKEN",
        authorize=lambda allowed: allowed is grant,
        clock=lambda: clock,
    )
    fence = Fence()
    digest = "a" * 64
    adapters = auth.AdapterSet(digest, fence, vault, fence)

    def resolve(presented: object) -> str:
        resolver = auth.Resolver(adapters, expected_digest=digest, clock=lambda: clock)
        try:
            return str(resolver.resolve_and_inject(presented))
        except auth.Denied:
            return "denied"

    require(
        resolve(profile_grant) == "denied" and not provider_calls and not writes,
        "profile authority reached credential provider or injection",
    )
    require(resolve(ticket) == "injected", "independent credential grant failed")
    provider_deleted = True  # Explicit simulated provider deletion, outside Browser.
    vault.forget()  # Local opaque handles only.
    require(resolve(ticket) == "denied", "deleted credential was injected")
    require(
        writes == ["injected_under_separate_grant"]
        and provider_calls == ["data", "metadata", "metadata", "data"],
        "credential peer ledger changed",
    )
    return {
        "profile_grant": "denied_before_provider",
        "separate_grant": writes[0],
        "after_simulated_provider_delete": "denied",
        "provider_calls": provider_calls,
        "website_session_revocation": "not_run",
    }


class ProfileRun:
    def __init__(self, root: Path, spec: dict[str, Any], *, create: bool) -> None:
        fixtures = import_module("browser_testing.profile_integration_fixtures")
        self.adapters = fixtures
        self.stores = import_module("browser_runtime.profile_store")
        self.credentials = import_module("browser_runtime.credentials")
        self.operation = import_module(
            "browser_testing.profile_keys_fixtures"
        ).operation
        self.canary = import_module("browser_testing.profile_store_fixtures").CANARY
        self.root, self.spec = root, spec
        self.f = fixtures.Fixture(root, create=create)
        now = float(spec["clock"])

        def clock() -> float:
            return now

        self.f.store._clock = self.f.tree._clock = self.f.keys._clock = clock
        self.f.authority.observe = lambda: self.credentials.Observation(
            self.f.authority.grant.target, now
        )

    def grant(self, action: str, operation: str) -> Any:
        return replace(
            self.operation(operation, action), deadline=self.spec["clock"] + 10
        )

    def run(self, action: str, operation: str, **changes: Any) -> str:
        grant = self.grant(action, operation)
        self.f.authority.grant = replace(grant, **changes)
        try:
            return str(self.f.store.run("trusted-ticket"))
        except self.stores.Denied:
            return "denied"

    def seed(self, data: bytes) -> None:
        grant = self.grant("restore", "h04-private-fixture-seed")
        self.f.authority.grant = grant
        require(
            self.f.tree.consume(
                grant, self.f.authority, self.adapters.bundle(grant.scope(), data)
            )
            is True,
            "fixture input setup failed",
        )

    def close(self) -> None:
        self.f.close()


def interrupt(case: ProfileRun) -> None:
    write = case.f.tree._write

    def private_write(fd: int, payload: bytes) -> None:
        write(fd, payload)
        if payload == case.canary:
            case.adapters.marker(case.root, "owner-private-write")
            (case.root / "owner-paused").touch()
            wait_for(case.root / "competing-admission")
            os._exit(73)

    case.f.tree._write = private_write
    case.run("restore", case.spec["operations"]["restore"])
    raise ValueError("restore fault point not reached")


def rival(case: ProfileRun) -> str:
    grant = case.grant("restore", case.spec["operations"]["rival"])
    binding = replace(grant.target.binding, account="h04-other-account")
    admit = case.f.authority.admit

    def record_admit(ticket: object) -> Any:
        require((case.root / "owner-paused").is_file(), "missing owner barrier")
        case.adapters.marker(case.root, "rival-admit")
        (case.root / "competing-admission").touch()
        return admit(ticket)

    case.f.authority.admit = record_admit
    (case.root / "rival-ready").touch()
    wait_for(case.root / "owner-paused")
    return case.run(
        "restore",
        case.spec["operations"]["rival"],
        target=replace(grant.target, binding=binding),
    )


def worker(stage: Path, root: Path, action: str) -> dict[str, Any]:
    no_external_operations(root)
    sys.path.insert(0, str(stage))
    spec = json.loads(MANIFEST.read_bytes())
    operations = spec["operations"]
    case = ProfileRun(root, spec, create=action == "seed")
    try:
        if action in {"scan-interrupted", "scan-recovered", "scan-forgotten"}:
            fixture = import_module("browser_testing.profile_store_fixtures")
            peer = import_module("browser_testing.profile_keys_fixtures")
            values: tuple[bytes, ...] = (
                fixture.CANARY,
                fixture.KEY,
                peer.TOKEN.encode(),
            )
            if action == "scan-forgotten":
                values += (case.adapters.OLD,)
            return {"protected_residue": scan(root, values)}
        if action == "seed":
            case.seed(case.canary)
            saved = case.run("save", operations["save"])
            case.seed(case.adapters.OLD)
            return {"status": saved}
        if action == "interrupt":
            interrupt(case)
        if action == "rival":
            return {"status": rival(case)}
        if action == "credential":
            return credential_case(case.grant("restore", operations["fresh"]), spec)
        if action == "after-forget":
            return {"status": case.run("restore", "h04-after-forget")}
        if action == "expired":
            return {
                "status": case.run("restore", "h04-expired", deadline=spec["clock"])
            }
        if action == "wrong-owner":
            grant = case.grant("restore", "h04-wrong-owner")
            return {
                "status": case.run(
                    "restore",
                    "h04-wrong-owner",
                    target=replace(grant.target, native_session="h04-other-native"),
                )
            }
        if action == "outage":
            case.f.peer.reply = import_module("browser_runtime.openbao").Response(
                503, b"{}"
            )
        status = case.run(
            "forget" if action == "forget" else "restore", operations[action]
        )
        result: dict[str, Any] = {"status": status}
        if action in {"restore", "damaged", "fresh"}:
            current = case.f.current()
            require(
                current in (case.canary, case.adapters.OLD),
                "unexpected generation bytes",
            )
            result["generation"] = (
                "checkpoint" if current == case.canary else "previous"
            )
        if action == "forget":
            result["phase"] = case.f.state()["phase"]
        return result
    finally:
        case.close()


def invoke(
    stage: Path,
    root: Path,
    action: str,
    process: subprocess.Popen[bytes] | None = None,
) -> dict[str, Any]:
    if process is None:
        result = subprocess.run(
            command(stage, root, action),
            capture_output=True,
            timeout=15,
            check=False,
        )
        code, out, err = result.returncode, result.stdout, result.stderr
    else:
        out, err = process.communicate(timeout=15)
        code = process.returncode
    require(code == 0 and not err, f"{action} worker exited unsuccessfully")
    reply = json.loads(out)
    require(type(reply) is dict, "worker receipt shape")
    return dict(reply)


def command(stage: Path, root: Path, action: str) -> list[str]:
    optimize = ["-O"] if sys.flags.optimize else []
    return [
        sys.executable,
        "-I",
        "-B",
        *optimize,
        str(SCRIPT),
        "--worker",
        str(stage),
        str(root),
        action,
    ]


def ledger(root: Path) -> list[str]:
    return (root / "effects").read_text().splitlines()


def competing_restore(stage: Path, root: Path) -> None:
    with subprocess.Popen(
        command(stage, root, "rival"), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as competing:
        try:
            wait_for(root / "rival-ready")
            outcome = subprocess.run(
                command(stage, root, "interrupt"),
                capture_output=True,
                timeout=15,
                check=False,
            )
            require(
                outcome.returncode == 73 and not outcome.stdout and not outcome.stderr,
                "interruption did not occur at the private write",
            )
            require(
                invoke(stage, root, "rival", competing) == {"status": "denied"},
                "competing account admitted",
            )
        finally:
            if competing.poll() is None:
                competing.kill()
                competing.communicate(timeout=5)


def change_ciphertext(path: Path, previous: bytes | None = None) -> bytes:
    with closing(sqlite3.connect(path, timeout=2)) as db, db:
        row = db.execute("SELECT reference,ciphertext FROM checkpoints").fetchall()
        require(
            len(row) == 1 and type(row[0][1]) is bytes, "retained checkpoint missing"
        )
        key, data = row[0]
        alternate = data[:-1] + bytes([data[-1] ^ 1]) if previous is None else previous
        db.execute(
            "UPDATE checkpoints SET ciphertext=? WHERE reference=?", (alternate, key)
        )
        return bytes(data)


def campaign(stage: Path, root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    root.mkdir(mode=0o700)
    db = root / "ciphertext/profiles.sqlite3"
    restores = "SELECT operation,result FROM restores ORDER BY rowid"
    restore_id = spec["operations"]["restore"]
    require(invoke(stage, root, "seed") == {"status": "stored"}, "seed failed")
    first = len(ledger(root))

    competing_restore(stage, root)
    require(
        ledger(root)[first:]
        == [
            "prepare",
            "fetch",
            "issue",
            "consume",
            "owner-private-write",
            "rival-admit",
        ],
        "unexpected restore or competing-account effects",
    )
    require(
        read_db(db, restores) == [(restore_id, "unknown")], "crash reservation lost"
    )
    require(
        list((root / "profile").glob("stage-*")), "fault missed interrupted staging"
    )
    require(
        invoke(stage, root, "scan-interrupted")["protected_residue"] > 0,
        "plaintext scanner missed the interrupted private stage",
    )

    first = len(ledger(root))
    require(
        invoke(stage, root, "restore")
        == {"status": "unknown", "generation": "previous"},
        "restored repeat did not reconcile the previous generation",
    )
    require(
        ledger(root)[first:] == ["prepare"],
        "unknown restore repeated key or plaintext access",
    )
    require(
        not list((root / "profile").glob("stage-*")),
        "recovery did not clear private staging",
    )
    require(
        invoke(stage, root, "scan-recovered") == {"protected_residue": 0},
        "profile canary residue after recovery",
    )
    first = len(ledger(root))
    require(
        invoke(stage, root, "wrong-owner") == {"status": "denied"}
        and ledger(root)[first:] == [],
        "same-epoch competing owner reached profile IO",
    )

    original = change_ciphertext(db)
    first = len(ledger(root))
    require(
        invoke(stage, root, "damaged")
        == {"status": "denied", "generation": "previous"},
        "damaged ciphertext materialized",
    )
    require(
        ledger(root)[first:] == ["prepare", "fetch", "issue"],
        "damaged ciphertext reached the plaintext sink",
    )
    change_ciphertext(db, original)
    first = len(ledger(root))
    require(
        invoke(stage, root, "expired") == {"status": "denied"}
        and ledger(root)[first:] == [],
        "expired admission reached adapters",
    )
    require(
        invoke(stage, root, "outage") == {"status": "denied"}
        and ledger(root)[first:] == ["prepare", "fetch"],
        "provider outage reached custody issue or plaintext consumption",
    )
    first = len(ledger(root))
    require(
        invoke(stage, root, "fresh")
        == {"status": "delivered", "generation": "checkpoint"},
        "fresh authorized restore failed",
    )
    require(
        ledger(root)[first:] == ["prepare", "fetch", "issue", "consume"],
        "fresh restore effect count",
    )

    retained = read_db(db, "SELECT reference,ciphertext FROM checkpoints")
    first = len(ledger(root))
    credential = invoke(stage, root, "credential")
    require(
        read_db(db, "SELECT reference,ciphertext FROM checkpoints") == retained,
        "credential deletion altered the profile checkpoint",
    )
    require(ledger(root)[first:] == [], "credential path reached profile IO")
    require(
        invoke(stage, root, "forget") == {"status": "forgotten", "phase": "forgotten"},
        "profile forget failed",
    )
    require(
        read_db(db, "SELECT forgotten FROM profiles") == [(1,)]
        and not read_db(db, "SELECT reference FROM checkpoints"),
        "durable profile tombstone missing",
    )
    require(
        invoke(stage, root, "after-forget") == {"status": "denied"},
        "forgotten profile restored",
    )
    require(
        ledger(root)[first:] == [],
        "forget or late restore reached key or plaintext adapters",
    )
    require(
        invoke(stage, root, "scan-forgotten") == {"protected_residue": 0},
        "discoverable canary residue remained after forget",
    )
    require(
        not (root / "forbidden").exists(), "forbidden socket or process call occurred"
    )
    return {
        "interrupt": "private_write_then_exit_73",
        "rival": "attempted_admission_during_owner_pause_then_denied",
        "same_epoch_different_owner": "denied_before_profile_io",
        "recovery": "unknown_then_previous_generation_and_no_repeat_custody",
        "damaged_checkpoint": "denied_before_consume",
        "expired_grant": "denied_before_adapters",
        "provider_outage": "no_lease_or_plaintext_consume",
        "fresh_grant": "one_checkpoint_consume",
        "forgotten_profile": "tombstone_no_checkpoint_or_discoverable_canary",
        "credential": credential,
        "durable_outcomes": [list(row) for row in read_db(db, restores)],
        "profile_effect_ledger": ledger(root),
    }


def mutation(stage: Path, root: Path, spec: dict[str, Any]) -> str:
    source = stage / DIRECTORY
    original = source.read_text()
    require(original.count(TOMBSTONE) == 1, "tombstone mutation anchor mismatch")
    source.write_text(
        original.replace(TOMBSTONE, "pass  # Test mutation skips the tombstone.", 1)
    )
    try:
        campaign(stage, root, spec)
    except ValueError as error:
        require(
            str(error) == "durable profile tombstone missing",
            "mutation failed outside the independent durable assertion",
        )
        require(not (root / "forbidden").exists(), "unexpected mutation effects")
        return "skipped_tombstone_detected_by_sqlite_readback"
    finally:
        source.write_text(original)
    raise ValueError("tombstone mutation escaped")


def report() -> dict[str, Any]:
    spec = json.loads(MANIFEST.read_bytes())
    packages = {
        name: metadata.version(name) for name in ("cryptography", "cffi", "pycparser")
    }
    with TemporaryDirectory(prefix="browser-profile-hero-") as directory:
        temporary = Path(directory)
        stage = temporary / "source"
        pins = stage_sources(stage, spec)
        first = campaign(stage, temporary / "first", spec)
        second = campaign(stage, temporary / "second", spec)
        require(first == second, "normalized profile outcome changed")
        detected = mutation(stage, temporary / "mutation", spec)
    return {
        "hero": spec["hero"],
        "evidence_class": "isolated_browser_component",
        "component_result": "passed",
        "system_acceptance": "blocked",
        "core_component": "blocked",
        "cross_component": "blocked",
        "live": "not_run",
        "component_pins": pins,
        "composition_sha": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "composition_lock_sha256": sha((ROOT / "composition.lock.json").read_bytes()),
        "scenario_sha256": sha(MANIFEST.read_bytes()),
        "source_sha256": spec["source_sha256"],
        "harness_sha256": sha(SCRIPT.read_bytes()),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.system() + "-" + platform.machine(),
            "sqlite": sqlite3.sqlite_version,
            "optimized": bool(sys.flags.optimize),
            "packages": packages,
        },
        "repeats": 2,
        "normalized": first,
        "mutation": detected,
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
        try:
            print(json.dumps(report(), indent=2, sort_keys=True))
        except metadata.PackageNotFoundError:
            print(
                json.dumps(
                    {
                        "hero": "H04",
                        "component_result": "blocked",
                        "reason": "profile crypto prerequisites unavailable",
                        "system_acceptance": "blocked",
                    }
                )
            )
            raise SystemExit(2) from None
    else:
        raise SystemExit("unexpected H04 arguments")
