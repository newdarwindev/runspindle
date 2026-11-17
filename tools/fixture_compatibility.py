"""Deterministic byte/schema diff for reviewed synthetic fixture pin upgrades."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def compare(previous: Path, current: Path) -> dict[str, Any]:
    """Inspect data only: never execute either candidate validator."""

    def snapshot(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
        if (root / "manifest.json").is_symlink() or not (
            root / "manifest.json"
        ).is_file():
            raise ValueError("invalid fixture manifest")
        manifest = json.loads((root / "manifest.json").read_text())
        expected_names = set(manifest["files"]) | {"manifest.json"}
        actual_names = {p.name for p in root.iterdir() if p.name != "__pycache__"}
        if actual_names != expected_names:
            raise ValueError("fixture inventory mismatch")
        hashes = {}
        for name, expected in manifest["files"].items():
            path = root / name
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("fixture path escaped")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError("fixture digest mismatch")
            hashes[name] = actual
        return manifest, hashes

    old, old_hashes = snapshot(previous)
    new, new_hashes = snapshot(current)
    names = sorted(set(old_hashes) | set(new_hashes))
    changes = [
        {"file": name, "before": old_hashes.get(name), "after": new_hashes.get(name)}
        for name in names
        if old_hashes.get(name) != new_hashes.get(name)
    ]
    metadata_changes = [
        {
            "field": name,
            "before_present": name in old,
            "after_present": name in new,
            "before": old.get(name),
            "after": new.get(name),
        }
        for name in sorted((set(old) | set(new)) - {"files"})
        if (name in old) != (name in new)
        or json.dumps(old.get(name), sort_keys=True)
        != json.dumps(new.get(name), sort_keys=True)
    ]
    contract_changed = old_hashes.get("contract.json") != new_hashes.get(
        "contract.json"
    )
    return {
        "evidence_class": "synthetic_fixture_compatibility_diff",
        "previous_schema": old["schema"],
        "current_schema": new["schema"],
        "contract_changed": contract_changed,
        "changes": changes,
        "metadata_changes": metadata_changes,
        "review_required": bool(changes or metadata_changes),
        "runtime_compatibility": "not_run",
        "automatic_pin_upgrade": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("previous", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.previous, args.current), sort_keys=True, indent=2))
