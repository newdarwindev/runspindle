"""Rehearse release evidence review using invented text artifacts only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import unittest


SCRIPT = Path(__file__).resolve()
FIXTURE = SCRIPT.with_name("fixtures") / "synthetic-visual-release.json"
CASES = {
    "matched": {},
    "changed-bytes": {"mock-image": "bytes_changed"},
    "missing-notice": {"deck": "required_notice_missing"},
    "wrong-class": {"storyboard": "evidence_class_mismatch"},
}


def decision(pin: dict[str, str], observed: dict[str, str]) -> str:
    if observed.get("evidence_class") != pin["evidence_class"]:
        return "evidence_class_mismatch"
    if hashlib.sha256(observed.get("bytes", "").encode("utf-8")).hexdigest() != pin["digest"]:
        return "bytes_changed"
    if not observed.get("notice"):
        return "required_notice_missing"
    if observed["notice"] != pin["notice"]:
        return "notice_mismatch"
    return "mock_allowed"


def review(baseline: dict[str, Any], presented: list[dict[str, Any]]) -> dict[str, str]:
    results: dict[str, str] = {}
    for row in presented:
        key = row["key"]
        if key in results:
            results[key] = "duplicate_artifact"
        elif key not in baseline:
            results[key] = "unrecognized_artifact"
        else:
            results[key] = decision(baseline[key], row)
    for missing in baseline.keys() - results.keys():
        results[missing] = "artifact_missing"
    return results


def rehearse(scenario: str) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rows = fixture["artifacts"]
    if scenario == "changed-bytes":
        next(row for row in rows if row["key"] == "mock-image")["bytes"] += "changed"
    elif scenario == "missing-notice":
        del next(row for row in rows if row["key"] == "deck")["notice"]
    elif scenario == "wrong-class":
        next(row for row in rows if row["key"] == "storyboard")["evidence_class"] = "actual_application_evidence"

    results = review(fixture["baseline"], rows)
    rejected = {key: reason for key, reason in results.items() if reason != "mock_allowed"}
    allow = sorted(key for key, reason in results.items() if reason == "mock_allowed")
    return {
        "synthetic_only": True,
        "actual_ui_evidence_verified": False,
        "publication_authorized": False,
        "scenario": scenario,
        "mock_allowlist": allow,
        "decisions": results,
        "passed": rejected == CASES[scenario] and len(allow) + len(rejected) == len(fixture["baseline"]),
    }


class SyntheticVisualReleaseTests(unittest.TestCase):
    def test_cli_repeats_exact_artifact_decisions(self) -> None:
        for case, expected in CASES.items():
            with self.subTest(case=case):
                cmd = [sys.executable, str(SCRIPT), case]
                stdout = subprocess.check_output(cmd, text=True)
                self.assertEqual(stdout, subprocess.check_output(cmd, text=True))
                result = json.loads(stdout)
                self.assertTrue(result["passed"])
                self.assertTrue(result["synthetic_only"])
                self.assertFalse(result["actual_ui_evidence_verified"])
                self.assertFalse(result["publication_authorized"])
                self.assertEqual(
                    result["mock_allowlist"], sorted({"storyboard", "mock-image", "deck"} - expected.keys())
                )
                for key, reason in expected.items():
                    self.assertEqual(result["decisions"][key], reason)

    def test_duplicates_and_unknown_artifacts_stay_out(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        first = fixture["artifacts"][0]
        decisions = review(fixture["baseline"], [first, first, {**first, "key": "unknown"}])
        self.assertEqual(
            decisions,
            {
                "storyboard": "duplicate_artifact",
                "unknown": "unrecognized_artifact",
                "deck": "artifact_missing",
                "mock-image": "artifact_missing",
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=CASES)
    result = rehearse(parser.parse_args().scenario)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
