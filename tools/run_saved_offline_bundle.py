#!/usr/bin/env python3
"""Execute saved development bundles on a disposable, offline Linux arm64 target.

Needs only Python on the launcher host, Docker, and the already-loaded exact
Python runtime image. It does not need component checkouts or dependency caches.
"""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path
from typing import Any, cast

IMAGE = "python@sha256:0e58fc4a4575979bfce26735236422a48b38dae99d72b9d72a15e8e3fe0f7f93"


def run(artifacts: str | Path, *, input_sha256: str) -> dict[str, Any]:
    directory = Path(artifacts).resolve()
    if re.fullmatch(r"[0-9a-f]{64}", input_sha256) is None:
        raise ValueError("expected a lowercase SHA-256 for the qualified bundle input")
    bundle_input = directory / "bundle-input.json"
    if bundle_input.is_symlink():
        raise ValueError("saved bundle input must be a local file")
    input_bytes = bundle_input.read_bytes()
    if hashlib.sha256(input_bytes).hexdigest() != input_sha256:
        raise ValueError("saved bundle input differs from qualification report")
    metadata = json.loads(input_bytes)
    bootstrap = directory / "bootstrap"
    manifest = metadata["bundles"]["baseline"]["manifest"]
    for name, relative in (
        (
            "composition/tools/maintained_lane_worker.py",
            "composition/tools/maintained_lane_worker.py",
        ),
        (
            "platform/tools/development_bundle.py",
            "platform/tools/development_bundle.py",
        ),
        ("platform/tools/streaming_bundle.py", "platform/tools/streaming_bundle.py"),
    ):
        path = bootstrap / relative
        if (
            path.is_symlink()
            or hashlib.sha256(path.read_bytes()).hexdigest()
            != manifest["files"][name]["sha256"]
        ):
            raise ValueError("saved bootstrap differs from bundle manifest")
    if (
        hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        != manifest["files"]["composition/tools/run_saved_offline_bundle.py"]["sha256"]
    ):
        raise ValueError("launcher differs from bundle manifest")
    name = "runspindle-saved-offline-" + uuid.uuid4().hex
    args = [
        "docker",
        "run",
        "--name",
        name,
        "--pull",
        "never",
        "--platform",
        "linux/arm64",
        "--network",
        "none",
        "--add-host",
        "temporal:127.0.0.1",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "5g",
        "--cpus",
        "2",
        "--pids-limit",
        "256",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=4g",
        "-v",
        str(directory) + ":/evidence",
        "-v",
        str(bootstrap / "composition") + ":/composition:ro",
        "-v",
        str(bootstrap / "platform") + ":/platform:ro",
        "-e",
        "PYTHONPATH=/platform",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        IMAGE,
        "python",
        "/composition/tools/maintained_lane_worker.py",
        "H12",
        "/evidence",
    ]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise RuntimeError("saved offline bundle failed: " + result.stderr[-3000:])
        receipt = cast(
            dict[str, Any], json.loads((directory / "H12-worker.json").read_bytes())
        )
        return {**receipt, "bundle_input_sha256": input_sha256}
    finally:
        subprocess.run(
            ["docker", "rm", "--force", name],
            capture_output=True,
            check=True,
            timeout=30,
        )
        if (
            subprocess.run(
                ["docker", "inspect", name], capture_output=True, timeout=30
            ).returncode
            == 0
        ):
            raise RuntimeError("saved offline target cleanup incomplete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default=str(Path(__file__).resolve().parent))
    parser.add_argument(
        "--input-sha256",
        required=True,
        help="Bundle input digest from the trusted H12 qualification report",
    )
    args = parser.parse_args()
    print(
        json.dumps(run(args.artifacts, input_sha256=args.input_sha256), sort_keys=True)
    )
