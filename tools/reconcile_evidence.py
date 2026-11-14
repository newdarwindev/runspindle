#!/usr/bin/env python3
"""Reconcile offline exact-source evidence. Never executes receipt commands."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

VERSION = "runspindle.evidence-reconciliation.v1"
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"[0-9a-f]{64}")
STATES = {"passed", "failed", "blocked", "not_run", "unknown"}
CLASSES = {"structural", "synthetic", "component", "isolated_integration", "live_acceptance"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def git(root, *args):
    # Fixed read-only arguments only; never shell/receipt/manifest commands.
    return subprocess.check_output(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                   text=True, stderr=subprocess.DEVNULL).strip()


def contained(root, name):
    require(isinstance(name, str) and name, "invalid_path")
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), "path_outside_root")
    return path


def digest_file(root, record):
    require(DIGEST.fullmatch(record["sha256"]) is not None, "invalid_artifact_digest")
    path = contained(root, record["path"])
    require(path.is_file(), "missing_artifact")
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == record["sha256"], "artifact_digest_mismatch")
    return data


def decode_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def load_json(path):
    return decode_json(path.read_bytes())


def reconcile(manifest, base):
    require(manifest["version"] == VERSION, "unsupported_version")
    require(manifest["criteria"], "empty_criteria")
    artifact_root = (base / manifest["artifact_root"]).resolve()
    composition = (base / manifest["composition_root"]).resolve()
    lock = load_json(composition / "composition.lock.json")
    require(lock["schema_version"] == 1, "unsupported_lock")
    pins = {row["component"]: row for row in lock["components"]}
    require(len(pins) == len(lock["components"]) == 7 and
            set(pins) == {"core", "host", "browser", "tether", "refinery", "console", "platform"},
            "invalid_pin_set")
    composition_sha = git(composition, "rev-parse", "HEAD")
    lock_digest = hashlib.sha256((composition / "composition.lock.json").read_bytes()).hexdigest()
    for name, pin in pins.items():
        require(pin["path"] == "components/" + name and SHA.fullmatch(pin["commit"]) is not None,
                "invalid_pin_identity")
        entry = git(composition, "ls-files", "--stage", "--", pin["path"])
        require(entry == "160000 " + pin["commit"] + " 0\t" + pin["path"], "gitlink_lock_mismatch")
    require("composition" in manifest["sources"], "missing_composition_snapshot")
    require((base / manifest["sources"]["composition"]["root"]).resolve() == composition,
            "composition_root_mismatch")
    sources = {}
    for name, record in manifest["sources"].items():
        root = (base / record["root"]).resolve()
        require(Path(git(root, "rev-parse", "--show-toplevel")).resolve() == root, "source_root_mismatch")
        sha = git(root, "rev-parse", "HEAD")
        require(SHA.fullmatch(record["main_sha"]) is not None, "invalid_main_sha")
        kind = record["kind"]
        require(kind in {"current_main", "draft", "historical"}, "invalid_source_kind")
        expected = git(composition, "rev-parse", "HEAD") if name == "composition" else pins[name]["commit"]
        sources[name] = {"sha": sha, "main_sha": record["main_sha"], "kind": kind,
                         "dirty": bool(git(root, "status", "--porcelain", "--untracked-files=all")),
                         "pinned": sha == expected, "root": root}
    # Composition dirtiness also invalidates all component claims from that composition.
    composition_dirty = bool(git(composition, "status", "--porcelain", "--untracked-files=all"))
    composition_current = (sources["composition"]["kind"] == "current_main" and
                           sources["composition"]["main_sha"] == composition_sha)
    capabilities = manifest["capabilities"]
    require(len({row["id"] for row in manifest["criteria"]}) == len(manifest["criteria"]), "duplicate_criterion")
    results = []
    for criterion in manifest["criteria"]:
        reasons = []
        observed_status = "unknown"
        source = sources[criterion["source"]]
        cap = capabilities[criterion["capability"]]
        required_class = criterion["evidence_class"]
        require(required_class in CLASSES, "invalid_evidence_class")
        if not composition_current:
            reasons.append("composition_not_current_main")
        if source["kind"] != "current_main":
            reasons.append(source["kind"] + "_source")
        if source["sha"] != source["main_sha"]:
            reasons.append("not_current_main")
        if not source["pinned"]:
            reasons.append("not_composition_pin")
        if source["dirty"] or composition_dirty:
            reasons.append("dirty_source")
        try:
            require(cap["source"] == criterion["source"], "capability_source_mismatch")
            require(cap["criterion"] == criterion["id"], "capability_criterion_mismatch")
            require(cap["status"] in STATES, "invalid_capability_status")
            receipt = decode_json(digest_file(artifact_root, cap["receipt"]))
            observed_status = receipt["status"]
            require(observed_status in STATES, "invalid_receipt_status")
            require(receipt["source_sha"] == source["sha"], "stale_receipt_sha")
            require(receipt["source_clean"] is True, "dirty_receipt")
            require(receipt["criterion"] == criterion["id"], "receipt_criterion_mismatch")
            require(receipt["evidence_class"] == required_class, "evidence_class_mismatch")
            require(receipt["status"] == cap["status"], "capability_status_mismatch")
            require(isinstance(receipt["command"], list) and receipt["command"] and
                    all(isinstance(arg, str) for arg in receipt["command"]), "missing_command_identity")
            # Digests identify inputs; they do not authorize retrieval or execution.
            for key in ("toolchain", "config", "fixtures", "dependencies"):
                digest_file(artifact_root, receipt["inputs"][key])
            require(receipt["artifacts"], "missing_artifact")
            for artifact in receipt["artifacts"]:
                digest_file(artifact_root, artifact)
            observation = decode_json(digest_file(artifact_root, receipt["observation"]))
            require(observation["source_sha"] == source["sha"], "stale_observation_sha")
            require(observation["criterion"] == criterion["id"], "observation_criterion_mismatch")
            require(isinstance(observation["observer"], str) and observation["observer"] and
                    observation["observer"] != receipt["producer"], "not_independent_observer")
            require(type(observation["forbidden_calls"]) is int and observation["forbidden_calls"] == 0,
                    "forbidden_calls_observed")
            require(type(observation["forbidden_effects"]) is int and observation["forbidden_effects"] == 0,
                    "forbidden_effects_observed")
            require(observation["expected"] == observation["observed"], "effect_observation_mismatch")
        except (KeyError, TypeError, ValueError, OSError) as error:
            reasons.append(str(error) if isinstance(error, ValueError) else "missing_or_malformed_evidence")
        if observed_status != "passed":
            reasons.append("receipt_" + observed_status)
        status = "passed" if not reasons else (observed_status if observed_status in {"failed", "blocked", "not_run"} else "unknown")
        results.append({"id": criterion["id"], "issue": criterion["issue"], "status": status,
                        "evidence_class": required_class, "reasons": sorted(set(reasons))})
    # Detect source/index changes during evidence reads. This is an optimistic
    # before/after check, not a filesystem snapshot or concurrent-write lock.
    def source_changed():
        changed = (git(composition, "rev-parse", "HEAD") != composition_sha or
                   hashlib.sha256((composition / "composition.lock.json").read_bytes()).hexdigest() != lock_digest)
        for pin in pins.values():
            changed = changed or git(composition, "ls-files", "--stage", "--", pin["path"]) != (
                "160000 " + pin["commit"] + " 0\t" + pin["path"])
        changed = changed or bool(git(composition, "status", "--porcelain", "--untracked-files=all"))
        for source in sources.values():
            changed = changed or git(source["root"], "rev-parse", "HEAD") != source["sha"]
            changed = changed or bool(git(source["root"], "status", "--porcelain", "--untracked-files=all"))
        return changed
    changed = source_changed()
    if changed:
        for row in results:
            row["reasons"] = sorted(set(row["reasons"] + ["source_changed_or_dirty_during_check"]))
            if row["status"] == "passed":
                row["status"] = "unknown"
    by_id = {row["id"]: row for row in results}
    claim_results = []
    for claim in manifest["claims"]:
        try:
            # Hash pins the full README/STATUS bytes, so obsolete prose cannot be silently reused.
            data = digest_file(composition, claim["file"])
            expected = by_id[claim["criterion"]]["status"]
            if Path(claim["file"]["path"]).suffix == ".json":
                value = decode_json(data)
                for key in claim["selector"]:
                    value = value[key]
                require(value == expected, "stale_status_claim")
            else:
                require(claim["marker"] in data.decode("utf-8"), "missing_readme_claim")
                require(claim["status"] == expected, "stale_readme_claim")
            claim_results.append({"criterion": claim["criterion"], "status": "passed"})
        except (KeyError, TypeError, ValueError, OSError) as error:
            claim_results.append({"criterion": claim["criterion"], "status": "failed",
                                  "reason": str(error) if isinstance(error, ValueError) else "malformed_claim"})
    require(manifest["claims"], "missing_claim_checks")
    if source_changed():
        for row in results:
            row["reasons"] = sorted(set(row["reasons"] + ["source_changed_or_dirty_during_check"]))
            if row["status"] == "passed":
                row["status"] = "unknown"
        for row in claim_results:
            row["status"] = "failed"
            row["reason"] = "source_changed_or_dirty_during_check"
    passed = all(row["status"] == "passed" for row in results + claim_results)
    return {"version": VERSION, "status": "passed" if passed else "non_success",
            "evidence_class": "offline_evidence_reconciliation", "criteria": results,
            "claims": claim_results, "system_acceptance": "not_inferred",
            "source_inventory": {name: {k: v for k, v in record.items() if k != "root"}
                                 for name, record in sources.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = reconcile(load_json(args.manifest), args.manifest.resolve().parent)
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError):
        result = {"version": VERSION, "status": "failed", "reason": "invalid_or_unavailable_input",
                  "system_acceptance": "not_inferred"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
