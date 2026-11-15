"""Require source guards and preservation tests in the strict validation inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CHECKS = {
    "check-browser-mirror": [
        "tools/check_browser_mirror.py",
        "docs/marketing/browser_mirror.py",
        "docs/marketing/browser.html",
        "docs/marketing/SRC-009-mirror.json",
        "docs/marketing/SRC-009-mirror.md",
    ],
    "check-economics-source": [
        "tools/check_economics_source.py",
        "docs/marketing/SRC-005-disposition.json",
    ],
    "check-paper-source": [
        "tools/check_paper_source.py",
        "docs/marketing/paper_source.py",
        "docs/marketing/SRC-002-source-receipt.json",
    ],
    "check-presentation-source": [
        "tools/check_presentation_source.py",
        "docs/marketing/presentation_source.py",
        "docs/marketing/SRC-003-004-source-receipt.json",
    ],
    "check-source-registration": [
        "tools/check_source_registration.py",
        "tests/test_source_registration.py",
        "hygiene.json",
        "validation-partitions.json",
    ],
}
PRESERVATION_TESTS = [
    "tests/test_marketing_browser.py",
    "tests/test_marketing_economics.py",
    "tests/test_marketing_paper.py",
    "tests/test_marketing_presentations.py",
    "tests/test_marketing_refinery.py",
    "tests/test_marketing_vision.py",
    "tests/test_source_registration.py",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("Source registration: " + message)


def validate(inventory: dict[str, Any], partitions: dict[str, Any]) -> None:
    checks = inventory["checks"]
    lanes = partitions["partitions"]
    for identifier, paths in SOURCE_CHECKS.items():
        selected = [item for item in checks if item.get("id") == identifier]
        expected = {
            "id": identifier,
            "command": ["python3", "-B", "-S", paths[0]],
            "required_files": paths,
            "timeout_seconds": 300,
        }
        require(selected == [expected], "mandatory check identity: " + identifier)
        require(
            sum(lane.count(identifier) for lane in lanes.values()) == 1
            and identifier in lanes["component"],
            "exactly one component assignment: " + identifier,
        )
    tests = [item for item in checks if item.get("id") == "python-tests"]
    require(len(tests) == 1, "one full test suite")
    require(
        tests[0].get("command")
        == ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
        "full test discovery cannot be replaced by a focused suite",
    )
    require(
        tests[0].get("required_files") == ["tests", *PRESERVATION_TESTS],
        "preservation tests must be required, not optional discovery",
    )


def check(root: Path) -> dict[str, object]:
    validate(
        json.loads((root / "hygiene.json").read_text()),
        json.loads((root / "validation-partitions.json").read_text()),
    )
    return {
        "status": "passed",
        "evidence_class": "source_guard_registration",
        "mandatory_source_checks": len(SOURCE_CHECKS),
        "runtime_acceptance": "not_run",
        "native_build": "not_run",
    }


if __name__ == "__main__":
    print(json.dumps(check(ROOT), sort_keys=True))
