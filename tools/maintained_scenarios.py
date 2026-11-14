#!/usr/bin/env python3
"""Candidate offline H10/H11/H12 with independent SQL and installed-byte reads.

Candidate heads never advance reviewed composition pins. Required external and
review gates keep the aggregate non-success even when bounded lanes pass.
"""
import argparse
import base64
from contextlib import closing
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
VERSION = "runspindle.maintained-scenarios.v1"
PYTHON_IMAGE = (
    "python@sha256:0e58fc4a4575979bfce26735236422a48b38dae99d72b9d72a15e8e3fe0f7f93"
)
GATES = {
    "independent_final_head_review": "user_waived_no_review_performed",
    "composition_pin_upgrade": "qualified_merged_revisions_required",
    "Langfuse": "blocked",
    "native_wire": "blocked",
    "Tether": "blocked",
    "browser": "deferred",
    "console": "deferred",
    "provider_live": "deferred",
    "paid_evaluation": "deferred",
    "full_product_release": "blocked",
    "live_acceptance": "not_run",
}


class Blocked(RuntimeError):
    pass


def check(value, message):
    if not value:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(path, *args):
    return subprocess.check_output(
        ["git", *args], cwd=path, text=True, timeout=30
    ).strip()


def inventory(manifest, overrides):
    if (
        set(manifest) != {"version", "reviewed_composition_base", "sources"}
        or manifest["version"] != VERSION
    ):
        raise Blocked("unsupported candidate scenario manifest")
    lock = json.loads((ROOT / "composition.lock.json").read_bytes())
    expected = {item["component"]: item for item in lock["components"]}
    if set(manifest["sources"]) != set(expected) or not set(overrides) <= set(expected):
        raise Blocked("missing/unknown component source")
    if subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            manifest["reviewed_composition_base"],
            "HEAD",
        ],
        cwd=ROOT,
    ).returncode:
        raise Blocked("composition base is not an ancestor")
    result = {}
    for name, item in expected.items():
        source = manifest["sources"][name]
        if set(source) != {"base", "commit"} or source["base"] != item["commit"]:
            raise Blocked("candidate base does not match reviewed pin: " + name)
        staged = git(ROOT, "ls-files", "--stage", "--", item["path"])
        if not staged.startswith("160000 " + source["base"] + " 0\t"):
            raise Blocked("reviewed gitlink/lock mismatch: " + name)
        path = Path(overrides.get(name, ROOT / item["path"])).resolve()
        if git(path, "rev-parse", "HEAD") != source["commit"] or git(
            path, "status", "--porcelain"
        ):
            raise Blocked(
                "candidate source differs from declared clean revision: " + name
            )
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", source["base"], source["commit"]],
            cwd=path,
        ).returncode:
            raise Blocked("candidate does not extend reviewed source: " + name)
        # Ignored executable files must not shadow tracked imports.
        unknown = git(
            path, "ls-files", "--others", "--", "refinery", "tools", "src"
        ).splitlines()
        if any(p.endswith((".py", ".rs")) for p in unknown):
            raise Blocked("untracked candidate executable source: " + name)
        result[name] = {**source, "path": path}
    return result


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def rows(path, query, params=()):
    check(path.is_file(), "missing independent component store")
    with closing(sqlite3.connect("file:" + str(path) + "?mode=rw", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        return db.execute(query, params).fetchall()


def decode(value):
    """Independent evidence-only decoder; does not import component serializers."""
    if not isinstance(value, dict):
        return value
    if set(value) == {"bytes"}:
        return base64.b64decode(value["bytes"], validate=True)
    if set(value) == {"tuple"}:
        return tuple(decode(v) for v in value["tuple"])
    if set(value) == {"dict"}:
        return {k: decode(v) for k, v in value["dict"].items()}
    if set(value) == {"type", "fields"}:
        return {
            "type": value["type"],
            **{k: decode(v) for k, v in value["fields"].items()},
        }
    raise AssertionError("unsupported component evidence record")


def observe_lineage(directory):
    stored = rows(
        directory / "refinery.sqlite", "SELECT kind,digest,payload FROM objects"
    )
    check(
        all(sha(payload) == digest for _, digest, payload in stored),
        "changed immutable stored bytes",
    )
    objects = [(kind, decode(json.loads(payload))) for kind, _, payload in stored]
    outputs = [value for kind, value in objects if kind == "output"]
    check(
        len(outputs) == 13 and all(sha(o["content"]) == o["sha256"] for o in outputs),
        "missing/changed exact outputs",
    )
    snapshot = next(value for kind, value in objects if kind == "lineage")
    data, split = snapshot["dataset"], snapshot["split"]
    examples = data["examples"]
    check(len(examples) == 11, "conflicting example not excluded")
    check(
        all(e["output"]["revision"] == "1" for e in examples),
        "old feedback rebound to newer output",
    )
    check(
        all(
            e["output"]["sha256"] == e["feedback"][0]["output_sha256"] for e in examples
        ),
        "feedback digest rebinding",
    )
    reasons = sorted(q["reason"] for q in data["quarantine"])
    check(
        reasons
        == [
            "conflicting_feedback",
            "conflicting_feedback",
            "missing_or_changed_output",
        ],
        "quarantine observations changed",
    )
    assignments = dict(split["assignments"])
    check(
        set(assignments.values()) == {"train", "heldout"}
        and len(assignments) == len({e["source"]["family_id"] for e in examples}),
        "family split missing or leaked",
    )
    return {
        "output_revisions": 13,
        "examples": len(examples),
        "quarantine": reasons,
        "dataset_sha256": split["dataset_sha256"],
        "split_sha256": split["sha256"],
    }


def observe_serving(directory, result):
    db = directory / "refinery.sqlite"
    attempts = rows(
        db, "SELECT request,outcome,receipt FROM attempts ORDER BY experiment,ticket"
    )
    check(
        attempts
        and all(
            state == "settled" and receipt is not None for _, state, receipt in attempts
        ),
        "unresolved experiment passed",
    )
    requests = [decode(json.loads(r)) for r, _, _ in attempts]
    for stage in ("baseline", "candidate"):
        selected = [
            (r["output_id"], r["output_revision"])
            for r in requests
            if r["stage"] == stage
        ]
        other = [
            (r["output_id"], r["output_revision"])
            for r in requests
            if r["stage"] == ("candidate" if stage == "baseline" else "baseline")
        ]
        check(selected == other, "baseline/candidate heldout mismatch")
    serving = directory / "serving.sqlite"
    calls = rows(
        serving, "SELECT activation,digest FROM calls WHERE action='load' ORDER BY id"
    )
    check(
        [r[0] for r in calls] == ["candidate-0", "candidate-1", "rollback"],
        "duplicate serving load after lost acknowledgement",
    )
    active = rows(
        serving,
        "SELECT activation,generation,digest,content FROM active WHERE environment='local'",
    )[0]
    program = json.loads(active[3])
    check(
        active[0] == "rollback"
        and active[1] == 3
        and active[2] == sha(active[3]) == calls[0][1],
        "incorrect actual serving version",
    )
    check(
        result["rolled_output"]
        == {"output": program["responses"]["hello"], "candidate_sha256": active[2]},
        "output serving attribution fabricated",
    )
    check(
        result["second_output"]["candidate_sha256"] == calls[1][1]
        and result["second_output"]["output"] == "second",
        "historical output attribution lost",
    )
    check(
        rows(db, "SELECT state FROM activations ORDER BY generation")
        == [("active",)] * 3,
        "registry activation readback missing",
    )
    return {
        "attempts": len(attempts),
        "load_order": [r[0] for r in calls],
        "active_sha256": active[2],
        "recovery": "fresh_process_after_actual_load_before_registry_ack",
        "dspy": "real_local_synthetic_LM",
        "monetary_cost": "not_measured",
    }


def container_worker(lane, directory, sources, *, recover=False):
    refinery, platform = sources["refinery"]["path"], sources["platform"]["path"]
    if lane == "H11":
        helper = load(refinery / "tools/offline_dspy.py", "candidate_dspy_preparation")
        if helper.inventory(refinery / "local/python-deps") != json.loads(
            (refinery / "offline/dependencies.json").read_bytes()
        ):
            raise Blocked("DSPy preparation byte mismatch")
    name = "runspindle-composition-" + uuid.uuid4().hex
    arguments = [
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
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "5g" if lane == "H12" else "1536m",
        "--cpus",
        "2",
        "--pids-limit",
        "256",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=4g" if lane == "H12" else "/tmp:rw,nosuid,size=256m",
        "-v",
        str(ROOT) + ":/composition:ro",
        "-v",
        str(platform) + ":/platform:ro",
        "-v",
        str(directory) + ":/evidence",
        "-w",
        "/platform",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-e",
        "HOME=/tmp",
        "-e",
        "DSPY_CACHEDIR=/tmp/dspy",
        "-e",
        "LITELLM_LOCAL_MODEL_COST_MAP=True",
        "-e",
        "HF_HUB_OFFLINE=1",
    ]
    if lane == "H12":
        arguments += ["--add-host", "temporal:127.0.0.1"]
    if lane != "H12":
        arguments += ["-v", str(refinery) + ":/refinery:ro"]
    if lane == "H11":
        arguments += ["-v", str(refinery / "local/python-deps") + ":/deps:ro"]
    arguments += [
        "-e",
        (
            "PYTHONPATH=/platform"
            if lane == "H12"
            else "PYTHONPATH=/refinery:/platform:/deps"
        ),
        PYTHON_IMAGE,
        "python",
        "/composition/tools/maintained_lane_worker.py",
        lane,
        "/evidence",
    ]
    if recover:
        arguments.append("--recover")
    try:
        completed = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            timeout=600 if lane == "H12" else 90,
        )
        expected = 93 if lane == "H11" and not recover else 0
        check(
            completed.returncode == expected,
            "composition worker failed: " + completed.stderr[-3000:],
        )
        return completed
    finally:
        subprocess.run(
            ["docker", "rm", "--force", name], capture_output=True, timeout=30
        )
        check(
            subprocess.run(
                ["docker", "inspect", name], capture_output=True, timeout=30
            ).returncode
            != 0,
            "composition worker leaked",
        )


def development_bundle(sources):
    module = load(
        sources["platform"]["path"] / "tools/development_bundle.py",
        "candidate_development_bundle",
    )
    pins = {name: item["commit"] for name, item in sources.items()}
    files = {}
    licenses = {}
    for name, item in sources.items():
        for relative in ("component.json", "LEGAL.md"):
            content = (item["path"] / relative).read_bytes()
            key = name + "/" + relative
            files[key] = content
            if relative == "LEGAL.md":
                licenses[key] = sha(content)
    files["contracts/maintained-evidence-v1.json"] = (
        ROOT / "contracts/maintained-evidence-v1.json"
    ).read_bytes()
    files["development/README.txt"] = (
        b"Development evidence metadata bundle only. No product adapters, services or production installation. Component heads are candidates awaiting independent review."
    )
    dependencies = {
        name
        + "/inventory": "sha256:"
        + sha((sources[name]["path"] / relative).read_bytes())
        for name, relative in (
            ("core", "docs/runtime-dependencies.json"),
            ("refinery", "offline/dependencies.json"),
            ("platform", "telemetry/dependencies.json"),
        )
    }
    bundle = module.build(
        "runspindle.maintained-evidence.v1",
        git(ROOT, "rev-parse", "HEAD"),
        pins,
        files,
        dependencies=dependencies,
        toolchains={"python_image": PYTHON_IMAGE.split("@", 1)[1]},
        licenses=licenses,
    )
    return bundle, pins


def run_lane(
    lane, sources, artifact_directory, core_prepared=None, platform_prepared=None
):
    with tempfile.TemporaryDirectory(prefix="maintained-" + lane + "-") as temporary:
        directory = Path(temporary)
        if lane == "H12":
            from build_offline_bundle import build as build_stream

            check(core_prepared is not None, "qualified core preparation required")
            pins = {name: item["commit"] for name, item in sources.items()}
            manifests = {}
            for variant in ("baseline", "upgrade"):
                manifest, digest = build_stream(
                    directory / (variant + ".stream"),
                    sources,
                    core_prepared,
                    platform_prepared,
                    variant=variant,
                )
                manifests[variant] = {"manifest": manifest, "sha256": digest}
            (directory / "bundle-input.json").write_text(
                json.dumps({"component_commits": pins, "bundles": manifests})
            )
            container_worker(lane, directory, sources)
            result = json.loads((directory / "H12-worker.json").read_bytes())
            artifact_directory.mkdir(parents=True, exist_ok=True)
            for variant in ("baseline", "upgrade"):
                import shutil

                shutil.copyfile(
                    directory / (variant + ".stream"),
                    artifact_directory / (variant + ".stream"),
                )
            (artifact_directory / "bundle-input.json").write_bytes(
                (directory / "bundle-input.json").read_bytes()
            )
            for relative, source in {
                "composition/tools/maintained_lane_worker.py": ROOT
                / "tools/maintained_lane_worker.py",
                "platform/tools/development_bundle.py": sources["platform"]["path"]
                / "tools/development_bundle.py",
                "platform/tools/streaming_bundle.py": sources["platform"]["path"]
                / "tools/streaming_bundle.py",
            }.items():
                destination = artifact_directory / "bootstrap" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            shutil.copyfile(
                ROOT / "tools/run_saved_offline_bundle.py",
                artifact_directory / "run.py",
            )
            (artifact_directory / "README.txt").write_text(
                "Offline development bundle only. Preload the exact Python image from the manifest. "
                "Run: python3 run.py --artifacts .\n"
                "Uses disposable Linux arm64 Docker targets with denied network and bounded resources. "
                "Native, Tether, browser, console, providers and production services are unsupported.\n"
            )
            return result
        container_worker(lane, directory, sources)
        lineage = observe_lineage(directory)
        if lane == "H11":
            # Inspect the independently active candidate while registry acknowledgement is absent.
            check(
                rows(directory / "refinery.sqlite", "SELECT pending FROM environments")[
                    0
                ][0]
                == "candidate-1",
                "missing interrupted activation intent",
            )
            check(
                rows(directory / "serving.sqlite", "SELECT activation FROM active")[0][
                    0
                ]
                == "candidate-1",
                "load did not actually precede interruption",
            )
            container_worker(lane, directory, sources, recover=True)
            result = json.loads((directory / "H11-worker.json").read_bytes())
            return {"lineage": lineage, "serving": observe_serving(directory, result)}
        return lineage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument(
        "--component",
        action="append",
        default=[],
        help="component=/exact/clean/worktree",
    )
    parser.add_argument("--report", required=True)
    parser.add_argument("--core-prepared", required=True)
    parser.add_argument("--platform-prepared", required=True)
    parser.add_argument("--artifacts", default=str(ROOT / "local/maintained-artifacts"))
    args = parser.parse_args()
    overrides = dict(value.split("=", 1) for value in args.component)
    manifest = json.loads(Path(args.manifest).read_bytes())
    try:
        sources = inventory(manifest, overrides)
        lanes = {}
        for lane in ("H10", "H11", "H12"):
            first, second = [
                run_lane(
                    lane,
                    sources,
                    Path(args.artifacts),
                    args.core_prepared,
                    args.platform_prepared,
                )
                for _ in range(2)
            ]
            check(first == second, "normalized seeded outcomes differ: " + lane)
            lanes[lane] = {
                "status": "passed",
                "evidence_class": "candidate_component_composition",
                "repeat_runs": 2,
                "outcome": first,
                "outcome_sha256": sha(
                    json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
                ),
            }
        result = {
            "version": VERSION,
            "status": "blocked",
            "seed": 17,
            "composition_head": git(ROOT, "rev-parse", "HEAD"),
            "sources": {
                name: {k: v for k, v in item.items() if k != "path"}
                for name, item in sources.items()
            },
            "contract_sha256": sha(
                (ROOT / "contracts/maintained-evidence-v1.json").read_bytes()
            ),
            "lanes": lanes,
            "required_gates": {
                **GATES,
                "composition_pin_upgrade": (
                    "passed_exact_component_pins"
                    if all(item["base"] == item["commit"] for item in sources.values())
                    else "candidate_only"
                ),
            },
            "boundaries": {
                "H10": {
                    "real": ["refinery_SQLite"],
                    "scripted": ["Tether_observations", "consent_and_actor_authority"],
                },
                "H11": {
                    "real": [
                        "refinery_SQLite",
                        "pinned_DSPy_Predict",
                        "local_serving_load_readback_rollback",
                    ],
                    "scripted": ["LM_completions", "approval_authority"],
                },
                "H12": {
                    "real": [
                        "streaming_development_executable_and_dependencies",
                        "installed_core_storage_and_default_denial",
                        "installed_Temporal_registry_and_scripted_peer_history_replay",
                        "installed_refinery_DSPy_budget_serving_recovery_rollback",
                        "interrupted_upgrade_and_rollback_fresh_process",
                        "Linux_arm64_disposable_filesystem",
                    ],
                    "unsupported": ["product_adapters", "services"],
                },
            },
        }
    except Blocked as error:
        result = {
            "version": VERSION,
            "status": "blocked",
            "reason": str(error),
            "required_gates": GATES,
        }
    Path(args.report).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 78


if __name__ == "__main__":

    def interrupted(*_):
        raise KeyboardInterrupt("composition lane cancelled")

    signal.signal(signal.SIGTERM, interrupted)
    raise SystemExit(main())
