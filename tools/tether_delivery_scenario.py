#!/usr/bin/env python3
"""Run the pinned Core–Tether wire delivery and resolution qualification."""

import argparse
import datetime
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile
from types import FrameType
from typing import Any

from tools.runtime_integration_scenario import ROOT, Blocked, git, inventory, sha

CASES = (
    "actual_tether_concurrent_same_resolution_retains_one_decision",
    "actual_tether_journals_wire_readback_and_lost_ack",
    "actual_tether_resolution_restarts_lost_replies_and_retained_conflicts",
    "actual_tether_resolution_revocation_and_changed_bytes_fail_closed",
    "actual_tether_revocation_after_lost_ack_cannot_deliver_or_retry",
    "actual_tether_wrong_thread_and_conflict_never_retarget",
)
MUTATION_CASE = "test_input_cannot_broaden_independent_expected_authority"
VERSION = "runspindle.tether-delivery-scenario.v1"
MANIFEST = "specs/tether-delivery-scenario-v1.json"
CORE_INPUTS = (
    "Cargo.lock",
    "temporal/toolchain.json",
    "tests/outbox.rs",
    "tests/fixtures/tether_wire_peer.py",
    "tests/test_tether_wire_fixture.py",
)


def source_inventory(root: pathlib.Path, core: pathlib.Path) -> dict[str, Any]:
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise Blocked("composition checkout must match its committed tree")
    sources: dict[str, Any] = inventory(root)
    manifest = json.loads((root / MANIFEST).read_bytes())
    candidate = manifest["core_candidate"]
    tether = sources["components"]["tether"]
    if (
        manifest["version"] != VERSION
        or manifest["composition_tether"] != tether["commit"]
        or candidate["repository"] != "newdarwindev/runspindle-core"
        or not re.fullmatch(r"[0-9a-f]{40}", candidate["commit"])
    ):
        raise Blocked("delivery scenario pins differ from their manifest")
    if (
        core.is_relative_to(root)
        or not (core / ".git").exists()
        or pathlib.Path(git(core, "rev-parse", "--show-toplevel")).resolve() != core
        or git(core, "rev-parse", "HEAD") != candidate["commit"]
        or git(core, "status", "--porcelain", "--untracked-files=all")
        or git(core, "ls-files", "--others", "--", "src", "tests", ".cargo", "build.rs")
    ):
        raise Blocked("Core candidate must be a separate clean exact-pinned checkout")
    tether_path = root / tether["path"]
    if git(tether_path, "ls-files", "--others", "--", "tether", "tests"):
        raise Blocked("inexact Tether fixture source")
    sources["core_candidate"] = candidate
    inputs = {
        MANIFEST: root / MANIFEST,
        "composition.lock.json": root / "composition.lock.json",
        "tools/tether_delivery_scenario.py": root / "tools/tether_delivery_scenario.py",
        "tools/runtime_integration_scenario.py": root
        / "tools/runtime_integration_scenario.py",
        "tether/tests/test_slack_upload.py": tether_path / "tests/test_slack_upload.py",
        **{f"core_candidate/{name}": core / name for name in CORE_INPUTS},
    }
    try:
        sources["inputs"] = {
            name: sha(path.read_bytes()) for name, path in inputs.items()
        }
    except FileNotFoundError as error:
        raise Blocked("pinned delivery fixtures unavailable") from error
    return sources


def command(
    args: list[str], cwd: pathlib.Path, env: dict[str, str], timeout: float, step: str
) -> str:
    with subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    ) as child:
        try:
            output, _ = child.communicate(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.communicate()
            raise
    if child.returncode:
        if (
            b"no matching package named" in output
            or b"attempting to make an HTTP request, but --offline" in output
        ):
            raise Blocked("locked offline Cargo inputs unavailable")
        sys.stderr.buffer.write(output)
        raise RuntimeError(f"{step} exited with status {child.returncode}")
    return output.decode("utf-8")


def observations(rust_output: str, python_output: str) -> dict[str, list[str] | str]:
    actual = re.findall(r"^test (actual_tether_\w+) \.\.\. ok$", rust_output, re.M)
    cases = sorted(actual)
    if cases != list(CASES):
        raise RuntimeError("delivery integration tests missing, skipped or repeated")
    if not re.search(rf"^{MUTATION_CASE} \([^\n]+\) \.\.\. ok$", python_output, re.M):
        raise RuntimeError("independent expected-binding mutations did not run")
    return {"durable_cases": cases, "expected_binding_mutations": MUTATION_CASE}


def qualify(
    root: pathlib.Path,
    core: pathlib.Path,
    protoc: pathlib.Path,
    protoc_include: pathlib.Path,
) -> dict[str, Any]:
    sources = source_inventory(root, core)
    tether = root / sources["components"]["tether"]["path"]
    protoc = protoc.resolve(strict=True)
    protoc_include = protoc_include.resolve(strict=True)
    headers = sorted(protoc_include.rglob("*.proto"))
    if not headers:
        raise Blocked("protobuf includes unavailable")
    with tempfile.TemporaryDirectory(prefix="runspindle-h07-tether-") as directory:
        scratch = pathlib.Path(directory)
        (scratch / "python3").symlink_to(sys.executable)
        env = {
            "HOME": os.environ["HOME"],
            "PATH": f"{scratch}{os.pathsep}{os.defpath}{os.pathsep}{os.environ['PATH']}",
            "TMPDIR": directory,
            "LC_ALL": "C",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(scratch / "pycache"),
            "CARGO_TARGET_DIR": str(scratch / "cargo-target"),
            "CARGO_PROFILE_DEV_DEBUG": "0",
            "CARGO_INCREMENTAL": "0",
            "CARGO_TERM_COLOR": "never",
            "PROTOC": str(protoc),
            "PROTOC_INCLUDE": str(protoc_include),
            "RUNSPINDLE_TETHER_WIRE_SOURCE": str(tether),
        }
        if "CARGO_HOME" in os.environ:
            env["CARGO_HOME"] = os.environ["CARGO_HOME"]
        toolchain = {
            tool: command([tool, "--version"], core, env, 15, tool).strip()
            for tool in ("cargo", "rustc", "python3", str(protoc))
        }
        toolchain["protoc"] = toolchain.pop(str(protoc))
        toolchain["protoc_sha256"] = sha(protoc.read_bytes())
        toolchain["protobuf_include_sha256"] = sha(
            json.dumps(
                {
                    str(path.relative_to(protoc_include)): sha(path.read_bytes())
                    for path in headers
                },
                sort_keys=True,
            ).encode()
        )
        cargo = [
            "cargo",
            "test",
            "--offline",
            "--locked",
            "--jobs",
            "4",
            "--features",
            "authenticated-artifacts,verified-authority",
            "--test",
            "outbox",
            "--",
            "--ignored",
            "actual_tether",
            "--test-threads=1",
        ]
        runs = []
        for optimize in ("0", "1"):
            env["PYTHONOPTIMIZE"] = optimize
            rust = command(cargo, core, env, 900, "Core/Tether integration")
            python = command(
                [
                    "python3",
                    "-m",
                    "unittest",
                    "discover",
                    "-v",
                    "-s",
                    "tests",
                    "-p",
                    "test_tether_wire_fixture.py",
                ],
                core,
                env,
                90,
                "expected-binding mutations",
            )
            runs.append(observations(rust, python))
        if runs[0] != runs[1] or source_inventory(root, core) != sources:
            raise RuntimeError(
                "source inventory or normalized observations changed across runs"
            )
    return {
        "sources": sources,
        "toolchain": toolchain,
        "real": [
            "Core accepted artifact and outbox SQLite stores",
            "Tether wire and resolution journals",
        ],
        "scripted": [
            "authority and routing",
            "Slack HTTP peer with independent SQLite effect ledger",
        ],
        "lane_status": "passed",
        "observations": runs[0],
        "normalized_observation_sha256": sha(
            json.dumps(runs[0], sort_keys=True).encode()
        ),
        "repeat_modes": ["normal_python", "optimized_python"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-source", type=pathlib.Path, required=True)
    parser.add_argument("--protoc", type=pathlib.Path, required=True)
    parser.add_argument("--protoc-include", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report_path = args.report.resolve()
    core = args.core_source.resolve()
    if report_path.is_relative_to(ROOT) or report_path.is_relative_to(core):
        parser.error("write the report outside both source checkouts")

    def cancelled(_signal: int, _frame: FrameType | None) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, cancelled)
    try:
        report = qualify(ROOT, core, args.protoc, args.protoc_include)
    except Blocked as error:
        report = {"lane_status": "blocked", "reason": str(error)}
    except FileNotFoundError:
        report = {
            "lane_status": "blocked",
            "reason": "required local input unavailable",
        }
    except subprocess.TimeoutExpired:
        report = {
            "lane_status": "unknown",
            "reason": "bounded subprocess deadline exceeded",
        }
    except KeyboardInterrupt:
        report = {"lane_status": "unknown", "reason": "qualification interrupted"}
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
    ) as error:
        report = {"lane_status": "failed", "reason": str(error)}
    report.update(
        schema_version=VERSION,
        lane="H07.tether_delivery_and_resolution",
        aggregate="failed" if report["lane_status"] == "failed" else "blocked",
        prepared_temporal="not_run",
        live_acceptance="not_run",
        observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps({key: report[key] for key in ("lane", "lane_status", "aggregate")})
    )
    return 1 if report["aggregate"] == "failed" else 78


if __name__ == "__main__":
    raise SystemExit(main())
