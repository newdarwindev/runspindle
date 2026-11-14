#!/usr/bin/env python3
"""Fail closed unless CI uses the pinned document environment and matching receipt."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from pathlib import Path
from typing import Mapping

INTERPRETER = "/opt/runspindle-documents/bin/python"
PYTHON = "3.12.3"
CLOSURE_SHA256 = "7cfe6b9eb076efb723cb7e986c9429ace15eebc7ab6e3536d3fbce8c3aa72b7d"
PACKAGES = {"reportlab": "4.4.9", "pillow": "13.0.0", "charset-normalizer": "3.5.2"}


def check(
    *,
    executable: str,
    prefix: str,
    version: str,
    implementation: str,
    machine: str,
    system: str,
    packages: Mapping[str, str],
    receipt: Mapping[str, object],
    image: Mapping[str, object],
) -> None:
    if (
        executable != INTERPRETER
        or prefix != str(Path(INTERPRETER).parent.parent)
        or version != PYTHON
        or implementation != "CPython"
        or machine != "x86_64"
        or system != "Linux"
        or dict(packages) != PACKAGES
    ):
        raise ValueError("document renderer interpreter or dependency version mismatch")
    if (
        receipt.get("status") != "verified"
        or receipt.get("closure_sha256") != CLOSURE_SHA256
        or receipt.get("python") != PYTHON
        or receipt.get("interpreter") != INTERPRETER
        or receipt.get("packages") != PACKAGES
        or receipt.get("wheel_count") != 3
        or image.get("documents") != dict(receipt)
    ):
        raise ValueError("document renderer image receipt missing or mismatched")


def main() -> None:
    try:
        receipt = json.loads(
            Path("/opt/runspindle-documents/verified.json").read_text()
        )
        image = json.loads(Path("/etc/runspindle-image.json").read_text())
        check(
            executable=sys.executable,
            prefix=sys.prefix,
            version=platform.python_version(),
            implementation=platform.python_implementation(),
            machine=platform.machine(),
            system=platform.system(),
            packages={name: importlib.metadata.version(name) for name in PACKAGES},
            receipt=receipt,
            image=image,
        )
    except (OSError, ValueError, importlib.metadata.PackageNotFoundError) as error:
        raise SystemExit(f"Pinned document renderer unavailable: {error}") from error
    print(json.dumps({"status": "verified", "document_closure_sha256": CLOSURE_SHA256}))


if __name__ == "__main__":
    main()
