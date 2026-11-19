"""Exact pinned fixture-only consumer matrix, with no runtime component upgrades."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {"core", "host", "browser", "tether", "refinery", "console", "platform"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def qualify(lock: dict[str, Any], checkouts: dict[str, str]) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    if set(lock["components"]) != COMPONENTS or set(checkouts) != COMPONENTS:
        raise ValueError("all seven exact consumers required")
    if (
        sha((ROOT / "fixtures/v1/manifest.json").read_bytes())
        != lock["origin_manifest_sha256"]
    ):
        raise ValueError("root fixture source drift")
    if lock.get("schema") != "runspindle.fixture-consumer-lock.v1":
        raise ValueError("invalid fixture consumer lock schema")
    if not re.fullmatch(r"[0-9a-f]{40}", lock["source_commit"]):
        raise ValueError("invalid source commit")
    committed_origin = subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            lock["source_commit"] + ":fixtures/v1/manifest.json",
        ],
        timeout=10,
    )
    if sha(committed_origin) != lock["origin_manifest_sha256"]:
        raise ValueError("committed root fixture source mismatch")
    for name, digest in json.loads(committed_origin)["files"].items():
        path = ROOT / "fixtures/v1" / name
        if Path(name).name != name or path.is_symlink() or not path.is_file():
            raise ValueError("unsafe root fixture source")
        if sha(path.read_bytes()) != digest:
            raise ValueError("root fixture source bytes drift")
    results = {}
    for component in sorted(COMPONENTS):
        record = lock["components"][component]
        root = Path(checkouts[component]).resolve()
        actual = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD", "HEAD^{tree}"],
            text=True,
            timeout=10,
        ).splitlines()
        if actual != [record["commit"], record["tree"]]:
            raise ValueError("consumer commit/tree mismatch: " + component)
        if record["repository"] != "newdarwindev/runspindle-" + component:
            raise ValueError("unexpected consumer repository")
        committed_names = subprocess.check_output(
            ["git", "-C", str(root), "ls-tree", "-r", "--name-only", "HEAD"],
            text=True,
            timeout=10,
        ).splitlines()
        required = {
            name
            for name in committed_names
            if name.startswith("fixtures/shared-v1/")
            or name.startswith("fixtures/shared-v1.")
            or (
                name.startswith("tests/test_shared")
                and "fixture" in name
                and name.endswith(".py")
            )
            or name
            in {
                "tools/check_shared_fixtures.py",
                "tools/shared_fixtures.py",
                "tools/__init__.py",
            }
        }
        if set(record["files"]) != required:
            raise ValueError("incomplete consumer source inventory")
        if len([name for name in required if name.startswith("tests/")]) != 2:
            raise ValueError("unexpected consumer test inventory")
        verified = {}
        for name, expected in record["files"].items():
            relative = Path(name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or relative.as_posix() != name
            ):
                raise ValueError("unsafe consumer source path")
            path = root / name
            if (
                path.is_symlink()
                or not path.is_file()
                or not path.resolve().is_relative_to(root)
            ):
                raise ValueError("unsafe consumer source path")
            data = path.read_bytes()
            if sha(data) != expected:
                raise ValueError("consumer source drift: " + component + "/" + name)
            committed = subprocess.check_output(
                ["git", "-C", str(root), "show", "HEAD:" + name],
                timeout=10,
            )
            if data != committed:
                raise ValueError("consumer differs from committed bytes")
            verified[name] = data
        pin = json.loads(verified["fixtures/shared-v1.pin.json"])
        manifest = json.loads(verified["fixtures/shared-v1/manifest.json"])
        if (
            pin["composition_commit" if component == "console" else "source_commit"]
            != lock["source_commit"]
            or manifest["component"] != component
            or manifest["origin_manifest_sha256"] != lock["origin_manifest_sha256"]
        ):
            raise ValueError("consumer fixture provenance mismatch")
        if (
            sha(verified["fixtures/shared-v1/manifest.json"])
            != pin["subset_manifest_sha256"]
        ):
            raise ValueError("consumer fixture pin mismatch")
        for name, expected in manifest["files"].items():
            if sha(verified["fixtures/shared-v1/" + name]) != expected:
                raise ValueError("consumer fixture artifact mismatch")
        origin = json.loads((ROOT / "fixtures/v1/manifest.json").read_text())
        if set(manifest["files"]) != {
            "fixturekit.py",
            "contract.json",
            "artifact.txt",
            "faults.json",
            "golden.json",
            "vectors.json",
        }:
            raise ValueError("incomplete standalone fixture export")
        for name in ("fixturekit.py", "contract.json", "artifact.txt", "faults.json"):
            if sha(verified["fixtures/shared-v1/" + name]) != origin["files"][name]:
                raise ValueError("consumer differs from exact root source")
        for name in ("golden.json", "vectors.json"):
            rows = json.loads((ROOT / "fixtures/v1" / name).read_text())
            selected = [
                row for row in rows if row["kind"] in origin["components"][component]
            ]
            expected = (json.dumps(selected, indent=2, sort_keys=True) + "\n").encode()
            if verified["fixtures/shared-v1/" + name] != expected:
                raise ValueError("consumer subset differs from root source")
        runs = []
        for optimized in (False, True):
            for repeat in (1, 2):
                with tempfile.TemporaryDirectory(
                    prefix="runspindle-isolated-fixture-"
                ) as directory:
                    isolated = Path(directory)
                    for name, data in verified.items():
                        target = isolated / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                    ledger = isolated / "forbidden-network.jsonl"
                    bootstrap = """import os, socket
from pathlib import Path
READY = True
def denied(*args, **kwargs):
    with Path(os.environ["FIXTURE_NETWORK_LEDGER"]).open("a") as out:
        out.write("forbidden network attempt\\n")
    raise RuntimeError("unexpected fixture network")
class DeniedSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        denied(*args, **kwargs)
socket.socket = DeniedSocket
socket.create_connection = denied
socket.getaddrinfo = denied
"""
                    (isolated / "sitecustomize.py").write_text(bootstrap)
                    env = {
                        **os.environ,
                        "PYTHONPATH": str(isolated),
                        "PYTHONHASHSEED": "90210",
                        "TZ": "UTC",
                        "FIXTURE_NETWORK_LEDGER": str(ledger),
                    }
                    code = 'import sitecustomize, unittest\nif getattr(sitecustomize, "READY", False) is not True: raise RuntimeError("missing network guard")\nresult=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover("tests", pattern="test_shared*fixture*.py")); raise SystemExit(not result.wasSuccessful())'
                    command = (
                        [sys.executable, "-B"]
                        + (["-O"] if optimized else [])
                        + ["-c", code]
                    )
                    child = subprocess.run(
                        command,
                        cwd=isolated,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    match = re.search(r"Ran (\d+) tests? in", child.stderr)
                    if (
                        child.returncode != 0
                        or not match
                        or int(match.group(1)) == 0
                        or "skipped=" in child.stderr
                        or ledger.exists()
                    ):
                        raise ValueError(
                            "isolated fixture lane failed: "
                            + component
                            + ": "
                            + child.stderr[-1200:]
                        )
                    runs.append(
                        {
                            "optimized": optimized,
                            "repeat": repeat,
                            "tests": int(match.group(1)),
                            "status": "passed",
                            "forbidden_network_calls": 0,
                        }
                    )
                if isolated.exists():
                    raise ValueError("isolated fixture cleanup failed")
        if len({r["tests"] for r in runs}) != 1:
            raise ValueError("nondeterministic test inventory")
        results[component] = {
            "commit": record["commit"],
            "tree": record["tree"],
            "runs": runs,
            "cleanup": "passed",
            "runtime": "not_run",
        }
    return {
        "schema": "runspindle.fixture-consumer-evidence.v1",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "tool_sha256": sha(Path(__file__).read_bytes()),
        "lock_sha256": sha(
            (json.dumps(lock, sort_keys=True, separators=(",", ":")) + "\n").encode()
        ),
        "status": "passed",
        "evidence_class": "isolated_synthetic_fixture_conformance",
        "seed": 90210,
        "source_commit": lock["source_commit"],
        "components": results,
        "runtime_integration": "not_run",
        "upstream_compatibility": "provisional-not-qualified",
        "live_acceptance": "not_run",
    }


def cancel_on_sigterm(signum: int, frame: Any) -> None:
    """Unwind subprocess.run and temporary-directory cleanup on graceful stop."""
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, cancel_on_sigterm)
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkouts", type=Path, required=True)
    parser.add_argument(
        "--lock", type=Path, default=ROOT / "fixtures/consumer-lock.json"
    )
    args = parser.parse_args()
    print(
        json.dumps(
            qualify(
                json.loads(args.lock.read_text()),
                json.loads(args.checkouts.read_text()),
            ),
            indent=2,
            sort_keys=True,
        )
    )
