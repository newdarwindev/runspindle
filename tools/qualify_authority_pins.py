#!/usr/bin/env python3
"""Bounded exact-pin composition verification; never a live release gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "core": "18b5d65392b176e1ab6c4b65ac27e941f530956c",
    "tether": "5e5fdb73422926d015657166e9ef60b293c01e50",
    "platform": "398c74766b9ec9f7203256e17dea34f1b15cac4c",
}
FIXTURES = {
    "conformance/intent-v1/vectors.json": "47bc9415404986d25e2ae5ecea2d857d7fe880ae721607ff59da35d3555b7c49",
    "conformance/intent-batch-v1/vectors.json": "43ad0c2957a82d2b794a71b93226eb4f16cd968bada4aa99195b6d0d16a1eb7a",
}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_lock(lock: dict, entries: dict[str, str]) -> None:
    components = lock.get("components", [])
    if len(components) != 7 or len({c["component"] for c in components}) != 7:
        raise ValueError("exact seven distinct component pins required")
    for c in components:
        if c["path"] != "components/" + c["component"]:
            raise ValueError("component path mismatch")
        if entries.get(c["path"]) != "160000 " + c["commit"]:
            raise ValueError("gitlink and lock mismatch")
        if c["component"] in PINS and c["commit"] != PINS[c["component"]]:
            raise ValueError("unqualified component revision")
    if not set(PINS).issubset(c["component"] for c in components):
        raise ValueError("missing qualified component")


def snapshot(root: Path) -> dict:
    if git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--ignore-submodules=none",
    ):
        raise ValueError("source must be clean")
    entries = {}
    for line in git(root, "ls-files", "--stage").splitlines():
        metadata, path = line.split("\t", 1)
        mode, commit, stage = metadata.split()
        if stage != "0":
            raise ValueError("unmerged source")
        if mode == "160000":
            entries[path] = mode + " " + commit
    validate_lock(json.loads((root / "composition.lock.json").read_text()), entries)
    result = {"composition": git(root, "rev-parse", "HEAD")}
    for name, pin in PINS.items():
        component = root / "components" / name
        if git(component, "rev-parse", "HEAD") != pin:
            raise ValueError("checkout differs from qualified gitlink")
        if git(component, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("component source must be clean")
        result[name] = pin
    for relative, expected in FIXTURES.items():
        if digest(root / "components/tether" / relative) != expected:
            raise ValueError("fixture drift")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-prepared", required=True)
    parser.add_argument("--platform-prepared", required=True)
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    report = Path(args.report_dir).resolve()
    if report.exists():
        raise ValueError("report directory must be new; preserve old receipts")
    report.mkdir(parents=True)
    revisions = snapshot(ROOT)
    core, tether, platform = (
        ROOT / "components" / n for n in ("core", "tether", "platform")
    )
    prepared = str(Path(args.core_prepared).resolve())
    platform_prepared = str(Path(args.platform_prepared).resolve())
    manifests = [
        Path(prepared) / "manifest.json",
        Path(platform_prepared) / "prepared.json",
    ]
    before = [digest(p) for p in manifests]
    common = [
        "--platform",
        str(platform),
        "--platform-prepared",
        platform_prepared,
        "--prepared",
        prepared,
        "--tether",
        str(tether),
    ]
    checks = [
        (
            "legacy-component",
            core,
            [
                "tools/qualify_verified_authority.py",
                "--platform",
                str(platform),
                "--platform-prepared",
                platform_prepared,
                "--composition",
                str(ROOT),
                "--prepared",
                prepared,
                "--report-dir",
                str(report / "legacy"),
            ],
        ),
        (
            "composition-optimized",
            ROOT,
            ["-O", "-m", "unittest", "discover", "-s", "tests", "-v"],
        ),
        ("tether", tether, ["-m", "unittest", "discover", "-s", "tests", "-v"]),
        (
            "tether-optimized",
            tether,
            ["-O", "-m", "unittest", "discover", "-s", "tests", "-v"],
        ),
        (
            "intent-conformance",
            core,
            [
                "tools/test_intent_conformance.py",
                "--tether",
                str(tether),
                "--prepared",
                prepared,
                "--report",
                str(report / "conformance.json"),
            ],
        ),
    ]
    for name in ("intent", "intent-repeat"):
        checks.append(
            (
                name,
                core,
                [
                    "tools/test_intent_bridge.py",
                    *common,
                    "--report",
                    str(report / (name + ".json")),
                ],
            )
        )
    summary = {
        "status": "running",
        "revisions": revisions,
        "checks": [],
        "prepared_manifest_sha256": before,
        "live_acceptance": "not_run",
        "scope": "Core-Tether-Platform real components with scripted external peers",
    }
    try:
        for name, cwd, command in checks:
            log = report / (name + ".log")
            with log.open("w") as stream:
                run = subprocess.run(
                    [sys.executable, *command],
                    cwd=cwd,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=2400,
                )
            summary["checks"].append(
                {
                    "name": name,
                    "status": "passed" if run.returncode == 0 else "failed",
                    "log_sha256": digest(log),
                }
            )
            if run.returncode:
                raise RuntimeError("required check failed: " + name)
        if snapshot(ROOT) != revisions or [digest(p) for p in manifests] != before:
            raise RuntimeError("source or prepared manifest changed")
        summary["status"] = "passed"
    finally:
        if summary["status"] != "passed":
            summary["status"] = "failed"
        (report / "qualification.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
