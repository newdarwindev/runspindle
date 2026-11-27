"""Check invented approval envelopes without contacting an external provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import unittest


SCRIPT = Path(__file__).resolve()
FIXTURE = SCRIPT.with_name("fixtures") / "synthetic-provider-envelope.json"
IDENTITIES = ("provider", "project", "model", "payload", "target")
CAPS = ("cost_cents", "calls", "tokens", "runtime_ticks")
CASES = {
    "exact": "verified_fixture",
    "wrong-model": "wrong_model",
    "expired": "expired_scope",
    "missing-cap": "missing_cap_calls",
    **{f"over-{cap}": f"over_cap_{cap}" for cap in CAPS},
}


def _strict_nonnegative(value: object) -> bool:
    return type(value) is int and value >= 0


def classify(approval: dict[str, Any], request: dict[str, Any], now: int) -> str:
    expires = approval.get("expires")
    if type(expires) is not int or expires <= now:
        return "expired_scope"
    for key in IDENTITIES:
        value = approval.get(key)
        if not isinstance(value, str) or not value or value != request.get(key):
            return f"wrong_{key}"
    if approval.get("disposable") is not True or request.get("disposable") is not True:
        return "target_not_disposable"
    caps, usage = approval.get("caps"), request.get("usage")
    if not isinstance(caps, dict) or not isinstance(usage, dict):
        return "missing_numeric_bounds"
    for key in CAPS:
        if key not in caps:
            return f"missing_cap_{key}"
        cap, amount = caps[key], usage.get(key)
        if not _strict_nonnegative(cap) or not _strict_nonnegative(amount):
            return f"invalid_bound_{key}"
        if amount > cap:
            return f"over_cap_{key}"
    if usage["calls"] != 1:
        return "wrong_stub_call_count"
    return "verified_fixture"


class LocalStub:
    """Count the completely local fixture action; no client or transport."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self) -> None:
        self.calls += 1


def rehearse(scenario: str) -> dict[str, Any]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    approval, request, now = data["approval"], data["request"], data["now"]
    if scenario == "wrong-model":
        request["model"] = "fixture-other-model"
    elif scenario == "expired":
        approval["expires"] = now
    elif scenario == "missing-cap":
        del approval["caps"]["calls"]
    elif scenario.startswith("over-"):
        metric = scenario.removeprefix("over-")
        request["usage"][metric] = approval["caps"][metric] + 1
    stub = LocalStub()
    outcome = classify(approval, request, now)
    if outcome == "verified_fixture":
        stub.invoke()
    return {
        "synthetic_only": True,
        "real_provider_run_authorized": False,
        "actual_spend_cents": 0,
        "scenario": scenario,
        "outcome": outcome,
        "stub_calls": stub.calls,
        "passed": outcome == CASES[scenario] and stub.calls == int(scenario == "exact"),
    }


class SyntheticProviderEnvelopeTests(unittest.TestCase):
    def test_cli_repeats_exact_approval_and_all_cap_denials(self) -> None:
        for scenario, expected in CASES.items():
            with self.subTest(scenario=scenario):
                cmd = [sys.executable, str(SCRIPT), scenario]
                output = subprocess.check_output(cmd, text=True)
                self.assertEqual(output, subprocess.check_output(cmd, text=True))
                result = json.loads(output)
                self.assertTrue(result["passed"])
                self.assertTrue(result["synthetic_only"])
                self.assertFalse(result["real_provider_run_authorized"])
                self.assertEqual(result["actual_spend_cents"], 0)
                self.assertEqual(result["stub_calls"], int(scenario == "exact"))
                self.assertEqual(result["outcome"], expected)

    def test_every_identity_and_disposable_flag_must_match(self) -> None:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        approval, request, now = data["approval"], data["request"], data["now"]
        for key in IDENTITIES:
            with self.subTest(key=key):
                self.assertEqual(classify(approval, {**request, key: "other"}, now), f"wrong_{key}")
        self.assertEqual(classify(approval, {**request, "disposable": False}, now), "target_not_disposable")

    def test_every_cap_must_exist_and_boolean_or_negative_values_fail(self) -> None:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        approval, request, now = data["approval"], data["request"], data["now"]
        for key in CAPS:
            with self.subTest(key=key):
                caps = {name: val for name, val in approval["caps"].items() if name != key}
                self.assertEqual(classify({**approval, "caps": caps}, request, now), f"missing_cap_{key}")
                for value in (True, -1):
                    usage = {**request["usage"], key: value}
                    self.assertEqual(classify(approval, {**request, "usage": usage}, now), f"invalid_bound_{key}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=CASES)
    receipt = rehearse(parser.parse_args().scenario)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
