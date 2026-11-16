#!/usr/bin/env python3
"""Fail-closed structural core/host library alignment. Not runtime acceptance."""
import json
import pathlib
import re
import subprocess
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PinError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PinError(message)


def main():
    lock = json.loads((ROOT / "composition.lock.json").read_text())
    require(type(lock["schema_version"]) is int and lock["schema_version"] == 1,
            "unsupported composition lock version")
    by_name = {item["component"]: item for item in lock["components"]}
    require(len(by_name) == len(lock["components"]), "duplicate component")
    for name in ("core", "host"):
        item = by_name[name]
        require(isinstance(item["commit"], str) and re.fullmatch(r"[0-9a-f]{40}", item["commit"]),
                "invalid component pin: " + name)
        require(item["path"] == "components/" + name, "unexpected component path: " + name)
        entry = subprocess.check_output(
            ["git", "ls-files", "--stage", "--", item["path"]], cwd=ROOT, text=True
        )
        require(entry == "160000 " + item["commit"] + " 0\t" + item["path"] + "\n",
                "gitlink/lock mismatch: " + name)
    core = ROOT / by_name["core"]["path"]
    host = by_name["host"]["commit"]
    if not (core / "Cargo.toml").is_file() or not (core / "Cargo.lock").is_file():
        print(json.dumps({
            "status": "blocked",
            "reason": "initialize pinned submodules before library alignment validation",
            "evidence_class": "composition_pin_alignment", "live_acceptance": "not_run",
        }))
        return 78
    manifest = tomllib.loads((core / "Cargo.toml").read_text())
    host_dep = manifest["dependencies"]["runspindle-host"]
    require(isinstance(host_dep, dict), "invalid host dependency")
    require(host_dep.get("package", "runspindle-host") == "runspindle-host",
            "core/host library package mismatch")
    require(host_dep.get("rev") == host, "core/host library pin mismatch")
    require(host_dep.get("git") == "https://github.com/newdarwindev/runspindle-host.git",
            "core/host library source mismatch")
    require(not any(key in host_dep for key in ("path", "branch", "tag")),
            "ambiguous host dependency source")
    cargo_lock = tomllib.loads((core / "Cargo.lock").read_text())
    packages = [p for p in cargo_lock["package"] if p.get("name") == "runspindle-host"]
    require(len(packages) == 1, "ambiguous Cargo.lock host package")
    require(packages[0].get("source") ==
            "git+https://github.com/newdarwindev/runspindle-host.git?rev=" + host + "#" + host,
            "Cargo.lock host pin mismatch")
    print(json.dumps({
        "status": "passed", "evidence_class": "composition_pin_alignment",
        "core": by_name["core"]["commit"], "host_library": host,
        "live_acceptance": "not_run",
    }))
    return 0


if __name__ == "__main__":
    try:
        result = main()
    except (KeyError, ValueError, TypeError, AttributeError, OSError, subprocess.SubprocessError) as error:
        # Malformed config is not permission to expose raw paths or parser input.
        print(json.dumps({
            "status": "failed", "reason": str(error) if isinstance(error, PinError) else "invalid or mismatched composition library pins",
            "evidence_class": "composition_pin_alignment", "live_acceptance": "not_run",
        }))
        result = 1
    raise SystemExit(result)
