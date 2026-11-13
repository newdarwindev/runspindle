#!/usr/bin/env python3
"""Fail-closed structural core/host library alignment. Not runtime acceptance."""
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    lock = json.loads((ROOT / "composition.lock.json").read_text())
    assert lock["schema_version"] == 1, "unsupported composition lock version"
    by_name = {item["component"]: item for item in lock["components"]}
    for name in ("core", "host"):
        item = by_name[name]
        entry = subprocess.check_output(
            ["git", "ls-files", "--stage", "--", item["path"]], cwd=ROOT, text=True
        )
        assert entry.startswith("160000 " + item["commit"] + " 0\t"), (
            "gitlink/lock mismatch: " + name
        )
    core = ROOT / by_name["core"]["path"]
    host = by_name["host"]["commit"]
    if not (core / "Cargo.toml").is_file() or not (core / "Cargo.lock").is_file():
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "initialize pinned submodules before library alignment validation",
                    "evidence_class": "composition_pin_alignment",
                    "live_acceptance": "not_run",
                }
            )
        )
        return 78
    assert re.search(
        r'runspindle-host\s*=\s*\{[^\n]*rev\s*=\s*"' + host + '"',
        (core / "Cargo.toml").read_text(),
    ), "core/host library pin mismatch"
    assert (
        "?rev=" + host + "#" + host in (core / "Cargo.lock").read_text()
    ), "Cargo.lock host pin mismatch"
    print(
        json.dumps(
            {
                "status": "passed",
                "evidence_class": "composition_pin_alignment",
                "core": by_name["core"]["commit"],
                "host_library": host,
                "live_acceptance": "not_run",
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        result = main()
    except (
        AssertionError,
        KeyError,
        ValueError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "reason": str(error),
                    "evidence_class": "composition_pin_alignment",
                    "live_acceptance": "not_run",
                }
            )
        )
        result = 1
    raise SystemExit(result)
