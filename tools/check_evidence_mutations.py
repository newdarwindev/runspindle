#!/usr/bin/env python3
"""Prove changed-byte tests detect a disabled evidence integrity invariant."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_evidence_reconciliation.py",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def main() -> int:
    env = dict(os.environ)
    env.pop("RUNSPINDLE_RECONCILER", None)
    baseline = run(env)
    if baseline.returncode:
        print(baseline.stderr)
        return 1
    source = (ROOT / "tools/reconcile_evidence.py").read_text()
    invariant = 'hashlib.sha256(data).hexdigest() == record["sha256"]'
    if source.count(invariant) != 1:
        return 1
    with tempfile.TemporaryDirectory(prefix="runspindle-evidence-mutation-") as folder:
        mutated = Path(folder) / "mutated.py"
        mutated.write_text(source.replace(invariant, "True"))
        env["RUNSPINDLE_RECONCILER"] = str(mutated)
        result = run(env)
    detected = result.returncode != 0 and "FAIL: test_changed_artifact" in result.stderr
    print(
        json.dumps(
            {
                "status": "passed" if detected else "failed",
                "mutation": "disabled_artifact_digest_check",
                "detected": detected,
                "evidence_class": "synthetic",
                "live_acceptance": "not_run",
            }
        )
    )
    return 0 if detected else 1


if __name__ == "__main__":
    raise SystemExit(main())
