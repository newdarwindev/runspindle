"""Rehearse exact fixture pins and restart reconciliation with no live adapters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest


SCRIPT = Path(__file__).resolve()
FIXTURE = SCRIPT.with_name("fixtures") / "composition-resume-rehearsal.json"
CASES = {
    "verified": "verified_fixture",
    "incompatible-pin": "incompatible_pin",
    "missing-adapter": "missing_adapter",
    "missing-effect": "effect_unknown",
    "mismatched-effect": "effect_mismatch",
}


def _adapter(value: str) -> dict[str, str]:
    return {"id": "fixture-operation", "value": value.upper()}


def boundary(phase: str, payload: dict[str, Any]) -> dict[str, Any]:
    """One disposable process either applies a fixture effect or reads its evidence."""
    if phase == "apply":
        return {"effect": _adapter(payload["value"]), "adapter_calls": 1, "acknowledged": False}
    expected = payload["expected"]
    receipt = payload["receipt"]
    if receipt is None:
        return {"outcome": "effect_unknown", "adapter_calls": 0}
    return {
        "outcome": "verified_fixture" if receipt == expected else "effect_mismatch",
        "adapter_calls": 0,
    }


def _new_process(phase: str, payload: dict[str, Any]) -> dict[str, Any]:
    stdout = subprocess.check_output(
        [sys.executable, str(SCRIPT), "--boundary", phase],
        input=json.dumps(payload),
        text=True,
    )
    response: dict[str, Any] = json.loads(stdout)
    return response


def _once(fixture: dict[str, Any], case: str, directory: Path) -> dict[str, Any]:
    pins = fixture["pins"]
    installed = dict(fixture["installed"])
    if case == "missing-adapter":
        del installed["effect"]
    elif case == "incompatible-pin":
        installed["effect"] = "wrong-fixture-pin"

    if set(installed) != set(pins):
        return {"component": "missing_adapter", "integration": "not_run", "calls": 0}
    if installed != pins:
        return {"component": "incompatible_pin", "integration": "not_run", "calls": 0}

    expected = fixture["expected_effect"]
    # An isolated adapter check has no effect on the integration ledger.
    component = "passed" if _adapter(fixture["input"]) == expected else "failed"
    if component == "failed":
        return {"component": component, "integration": "not_run", "calls": 0}

    # The first process exits after the effect but before acknowledgment.
    attempt = _new_process("apply", {"value": fixture["input"]})
    ledger = directory / "effect.json"
    ledger.write_text(json.dumps(attempt["effect"]), encoding="utf-8")
    if attempt["acknowledged"]:
        return {"component": component, "integration": "bad_fixture", "calls": attempt["adapter_calls"]}
    # Read the effect ledger independently. The frozen observer fixture simulates
    # a separate readback channel that can lose or corrupt its receipt.
    written = json.loads(ledger.read_text(encoding="utf-8"))
    receipt = fixture["observer"] if written == fixture["observer"] else None
    if case == "missing-effect":
        receipt = None
    elif case == "mismatched-effect":
        receipt = {**fixture["observer"], "id": "other-fixture-operation"}
    resumed = _new_process("readback", {"expected": expected, "receipt": receipt})
    return {
        "component": component,
        "integration": resumed["outcome"],
        "calls": attempt["adapter_calls"] + resumed["adapter_calls"],
        "resume_calls": resumed["adapter_calls"],
    }


def rehearse(case: str) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="composition-fixture-") as temporary:
        root = Path(temporary)
        results = []
        for label in ("first", "second"):
            directory = root / label
            directory.mkdir()
            results.append(_once(fixture, case, directory))
    teardown = not root.exists()
    stable = results[0] == results[1]
    first = results[0]
    aggregate = stable and teardown and first == {
        "component": "passed", "integration": "verified_fixture", "calls": 1, "resume_calls": 0
    }
    actual = first["integration"] if first["component"] == "passed" else first["component"]
    exact_calls = (
        first["calls"] == first.get("resume_calls", 0) == 0
        if case in {"incompatible-pin", "missing-adapter"}
        else first["calls"] == 1 and first.get("resume_calls") == 0
    )
    return {
        "synthetic_only": True,
        "live_adapters_verified": False,
        "scenario": case,
        "component": first["component"],
        "integration": first["integration"],
        "aggregate_fixture_verified": aggregate,
        "repeat_equal": stable,
        "effect_calls_per_replay": first["calls"],
        "resume_calls_per_replay": first.get("resume_calls", 0),
        "teardown_cleared": teardown,
        "passed": teardown and stable and exact_calls and actual == CASES[case] and aggregate == (case == "verified"),
    }


class CompositionResumeRehearsalTests(unittest.TestCase):
    def test_cli_cases_keep_component_integration_and_aggregate_separate(self) -> None:
        for case in CASES:
            with self.subTest(case=case):
                cmd = [sys.executable, str(SCRIPT), case]
                output = subprocess.check_output(cmd, text=True)
                self.assertEqual(output, subprocess.check_output(cmd, text=True))
                result = json.loads(output)
                self.assertTrue(result["passed"])
                self.assertTrue(result["synthetic_only"])
                self.assertFalse(result["live_adapters_verified"])
                self.assertTrue(result["teardown_cleared"])
                self.assertEqual(result["resume_calls_per_replay"], 0)
                self.assertEqual(result["aggregate_fixture_verified"], case == "verified")
                if case in {"incompatible-pin", "missing-adapter"}:
                    self.assertEqual(result["component"], CASES[case])
                    self.assertEqual(result["effect_calls_per_replay"], 0)
                else:
                    self.assertEqual(result["component"], "passed")
                    self.assertEqual(result["integration"], CASES[case])
                    self.assertEqual(result["effect_calls_per_replay"], 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", nargs="?", choices=CASES)
    parser.add_argument("--boundary", choices=("apply", "readback"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.boundary and args.scenario is None:
        print(json.dumps(boundary(args.boundary, json.load(sys.stdin)), sort_keys=True))
        return 0
    if args.scenario is None or args.boundary:
        parser.error("provide one rehearsal scenario")
    receipt = rehearse(args.scenario)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
