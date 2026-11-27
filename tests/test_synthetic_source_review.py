"""Compare invented import/attribution records; never copy or inspect real sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import unittest


SCRIPT = Path(__file__).resolve()
FIXTURE = SCRIPT.with_name("fixtures") / "synthetic-source-review.json"
SCOPE = ("source", "destination", "use")
CASES = {
    "allowed": {},
    "conflicting-grant": {"fixture/beta": "conflicting_grant"},
    "missing-notice": {"fixture/gamma": "notice_missing"},
    "wrong-destination": {"fixture/alpha": "grant_missing"},
    "wrong-use": {"fixture/alpha": "grant_missing"},
}


def review(request: dict[str, Any], grants: list[dict[str, Any]]) -> str:
    if any(not isinstance(request.get(field), str) or not request[field] for field in SCOPE):
        return "request_scope_missing"
    matching = [
        grant for grant in grants
        if all(grant.get(field) == request[field] for field in SCOPE)
    ]
    decisions = {grant.get("decision") for grant in matching}
    if "deny" in decisions:
        return "conflicting_grant" if "allow" in decisions else "grant_denied"
    if decisions != {"allow"}:
        return "grant_missing"
    notices = {grant.get("notice") for grant in matching}
    if len(notices) != 1 or not all(isinstance(notice, str) and notice for notice in notices):
        return "grant_notice_conflict"
    if not request.get("notice"):
        return "notice_missing"
    if request["notice"] not in notices:
        return "notice_mismatch"
    return "mock_allowed"


def rehearse(case: str) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    imports = fixture["imports"]
    grants = fixture["grants"]
    if case == "conflicting-grant":
        grants.append({**grants[1], "decision": "deny"})
    elif case == "missing-notice":
        del imports[2]["notice"]
    elif case == "wrong-destination":
        imports[0]["destination"] = "fixture/unapproved/alpha"
    elif case == "wrong-use":
        imports[0]["use"] = "fixture-unreviewed-use"

    outcomes = [
        {"source": request["source"], "destination": request["destination"], "outcome": review(request, grants)}
        for request in imports
    ]
    denied = {row["source"]: row["outcome"] for row in outcomes if row["outcome"] != "mock_allowed"}
    return {
        "synthetic_only": True,
        "actual_rights_verified": False,
        "source_copied": False,
        "scenario": case,
        "decisions": outcomes,
        "mock_allowlist": [row for row in outcomes if row["outcome"] == "mock_allowed"],
        "passed": denied == CASES[case] and len(outcomes) == 3,
    }


class SyntheticSourceReviewTests(unittest.TestCase):
    def test_cli_cases_are_repeatable_and_scope_specific(self) -> None:
        for case, denied in CASES.items():
            with self.subTest(case=case):
                cmd = [sys.executable, str(SCRIPT), case]
                output = subprocess.check_output(cmd, text=True)
                self.assertEqual(output, subprocess.check_output(cmd, text=True))
                receipt = json.loads(output)
                self.assertTrue(receipt["passed"])
                self.assertTrue(receipt["synthetic_only"])
                self.assertFalse(receipt["actual_rights_verified"])
                self.assertFalse(receipt["source_copied"])
                self.assertEqual(
                    {row["source"] for row in receipt["mock_allowlist"]},
                    {"fixture/alpha", "fixture/beta", "fixture/gamma"} - denied.keys(),
                )
                self.assertEqual(
                    {r["source"]: r["outcome"] for r in receipt["decisions"] if r["outcome"] != "mock_allowed"},
                    denied,
                )

    def test_matching_grants_with_conflicting_notices_do_not_pass(self) -> None:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        original = data["grants"][0]
        grants = [original, {**original, "notice": "fixture-unrelated"}]
        self.assertEqual(review(data["imports"][0], grants), "grant_notice_conflict")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=CASES)
    receipt = rehearse(parser.parse_args().scenario)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
