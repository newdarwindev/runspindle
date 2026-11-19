#!/usr/bin/env python3
"""Compare allowlisted Actions step timings, without reading logs or contacting GitHub."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

CHECKOUT = "Run actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
PHASES = {
    CHECKOUT: "checkout",
    "Checkout pinned v1 compatibility source": "checkout_compat",
    "Prepare exact Tether feedback candidate": "checkout_tether",
    "Prepare exact Refinery feedback candidate": "checkout_refinery",
    "Run component partition": "component",
    "Run quality partition": "quality",
    "Run rust partition": "rust",
}
MAX_RECEIPT_BYTES = 1_000_000
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"[0-9a-f]{64}")
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
REPO = re.compile(r"newdarwindev/runspindle(?:-(?:core|tether|refinery|platform|host|browser|console))?")
JOB = re.compile(r"validation / (?:component|quality|rust)")


def _seconds(item):
    stamps = [item.get(k) for k in ("started_at", "completed_at")]
    if not all(isinstance(s, str) and TIMESTAMP.fullmatch(s) for s in stamps):
        raise ValueError("missing or invalid UTC timestamps")
    start, end = [datetime.fromisoformat(s.replace("Z", "+00:00")) for s in stamps]
    if start > end:
        raise ValueError("negative duration")
    return start, end


def _matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _sample(receipt, expected_state):
    if not isinstance(receipt, dict) or receipt.get("cache_state") != expected_state:
        raise ValueError("invalid declared cache state")
    repo = receipt.get("repository")
    recipe = receipt.get("runner_recipe_sha256")
    job = receipt.get("job")
    if not _matches(REPO, repo) or not _matches(DIGEST, recipe) or not isinstance(job, dict):
        raise ValueError("invalid receipt identity")
    sha, name = job.get("head_sha"), job.get("name")
    if not _matches(SHA, sha) or not _matches(JOB, name):
        raise ValueError("invalid job identity")
    if (job.get("status"), job.get("conclusion")) != ("completed", "success"):
        raise ValueError("job did not succeed")
    run_id, job_id = job.get("run_id"), job.get("id")
    if not all(type(i) is int and i > 0 for i in (run_id, job_id)):
        raise ValueError("invalid run or job id")
    start, end = _seconds(job)
    steps = job.get("steps")
    if not isinstance(steps, list):
        raise ValueError("missing steps")
    phases = {}
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("name"), str):
            raise ValueError("invalid step")
        phase = PHASES.get(step["name"])
        if phase is None:
            continue
        if phase in phases or (step.get("status"), step.get("conclusion")) != (
            "completed", "success"
        ):
            raise ValueError("duplicate or unsuccessful allowlisted step")
        first, last = _seconds(step)
        if not start <= first <= last <= end:
            raise ValueError("step is outside job interval")
        phases[phase] = int((last - first).total_seconds())
    if "checkout" not in phases or name.removeprefix("validation / ") not in phases:
        raise ValueError("missing comparable checkout and work steps")
    return (repo, sha, name, recipe), (run_id, job_id), int((end - start).total_seconds()), phases


def compare(cold, warm):
    """Report observed elapsed deltas, not causal cache savings or gate evidence."""
    a, b = [_sample(receipt, state) for receipt, state in ((cold, "cold"), (warm, "warm"))]
    if a[0] != b[0]:
        raise ValueError("repository, SHA, job or recipe changed")
    if a[1][0] == b[1][0] or a[1][1] == b[1][1]:
        raise ValueError("need independent runs and jobs")
    if a[3].keys() != b[3].keys():
        raise ValueError("allowlisted phase set changed")

    def metric(x, y):
        return {"cold_seconds": x, "warm_seconds": y, "observed_delta_seconds": x - y}

    return {
        "schema": "runspindle.ci-timing-comparison.v1",
        "scope": "observational_only",
        "repository": a[0][0],
        "head_sha": a[0][1],
        "job_name": a[0][2],
        "runner_recipe_sha256": a[0][3],
        "cold_run_id": a[1][0],
        "warm_run_id": b[1][0],
        "job": metric(a[2], b[2]),
        "phases": {p: metric(a[3][p], b[3][p]) for p in sorted(a[3])},
    }


def _read(path):
    with path.open("rb") as inp:
        data = inp.read(MAX_RECEIPT_BYTES + 1)
    if len(data) > MAX_RECEIPT_BYTES:
        raise ValueError("receipt exceeds size limit")
    return json.loads(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cold", type=Path)
    parser.add_argument("warm", type=Path)
    args = parser.parse_args()
    try:
        result = compare(_read(args.cold), _read(args.warm))
    except (OSError, ValueError, RecursionError):
        parser.exit(2, "Invalid or incomparable timing receipts; no evidence emitted.\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
