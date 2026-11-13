#!/usr/bin/env python3
"""Pinned H02/H07 with composition-owned direct ledger observations; system stays blocked."""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/runtime-integration-scenarios-v1.json"
GATES = {
    "native_wire": "blocked",
    "Tether_source_and_transport": "blocked",
    "browser_fencing": "not_run",
    "provider_live": "not_run",
    "console_projection": "not_run",
    "full_workflow_acceptance": "blocked",
    "live_acceptance": "not_run",
}
LANES = {
    "H02": {"real": ["core", "host_library", "Temporal"], "scripted": ["native_peer"]},
    "H07": {
        "real": ["core_acceptance_store", "core_outbox", "Temporal"],
        "scripted": ["destination_transport"],
    },
}


class Blocked(RuntimeError):
    pass


def check(value, message):
    if not value:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_manifest(value):
    expected = {
        "version": "runspindle.integration-scenarios.v1",
        "contract": "runspindle.integration.v1",
        "seed": 17,
        "repeat_runs": 2,
        "lanes": LANES,
        "required_system_gates": GATES,
    }
    if (
        value != expected
        or type(value.get("seed")) is not int
        or type(value.get("repeat_runs")) is not int
    ):
        raise Blocked("unsupported or changed scenario contract/boundaries")
    return value


def aggregate(lane):
    return "failed" if lane == "failed" else "blocked"


def git(directory, *args):
    return subprocess.check_output(
        ["git", *args], cwd=directory, text=True, timeout=30
    ).strip()


def inventory(root=ROOT):
    lock = json.loads((root / "composition.lock.json").read_text())
    components = {}
    for item in lock["components"]:
        path = root / item["path"]
        name = item["component"]
        if not (path / "component.json").is_file():
            raise Blocked("missing component: " + name)
        head = git(path, "rev-parse", "HEAD")
        if head != item["commit"] or git(
            path, "status", "--porcelain", "--untracked-files=normal"
        ):
            raise Blocked("component source differs from composition pin: " + name)
        if not git(root, "ls-files", "--stage", "--", item["path"]).startswith(
            "160000 " + head + " 0\t"
        ):
            raise Blocked("gitlink/lock mismatch: " + name)
        extras = git(
            path, "ls-files", "--others", "--", "src", "tools", "build.rs", ".cargo"
        ).splitlines()
        if any(p.endswith((".rs", ".py")) or p.startswith(".cargo/") for p in extras):
            raise Blocked("untracked executable source in component: " + name)
        components[name] = {"commit": head, "path": item["path"]}
    core = root / components["core"]["path"]
    host = components["host"]["commit"]
    cargo = (core / "Cargo.toml").read_text()
    lock_bytes = (core / "Cargo.lock").read_text()
    if not re.search(r'runspindle-host\s*=\s*\{[^\n]*rev\s*=\s*"' + host + '"', cargo):
        raise Blocked("core host dependency does not match composition host pin")
    if "?rev=" + host + "#" + host not in lock_bytes:
        raise Blocked("Cargo.lock host dependency differs from composition pin")
    return {
        "components": components,
        "composition_head": git(root, "rev-parse", "HEAD"),
        "contract": "runspindle.integration.v1",
    }


def load_exact(path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def load_component(core, relative, name):
    expected = subprocess.check_output(
        ["git", "show", "HEAD:" + relative], cwd=core, timeout=30
    )
    if (core / relative).read_bytes() != expected:
        raise Blocked("component helper source changed: " + relative)
    return load_exact(core / relative, name)


def records(directory, database, sql):
    with sqlite3.connect(
        "file:" + str(directory / database) + "?mode=ro", uri=True
    ) as db:
        return db.execute(sql).fetchall()


def observe_host(directory, context):
    request = context["request"]
    binding = request["admission"]
    keys = (
        "task_id",
        "revision",
        "operation_id",
        "policy_revision",
        "host_id",
        "workspace_id",
        "lease_epoch",
    )
    binding = {k: binding[k] for k in keys}
    state = json.loads(
        records(directory, "host.sqlite", "SELECT state FROM host_state WHERE id=1")[0][
            0
        ]
    )
    snapshot = state["entries"][binding["operation_id"]]
    check(snapshot["binding"] == binding, "host operation rebound")
    calls = [
        (action, json.loads(b))
        for action, b in records(
            directory,
            "native-peer.sqlite",
            "SELECT action,binding FROM calls ORDER BY id",
        )
    ]
    selected = [action for action, b in calls if b == binding]
    check(selected.count("launch") == 1, "duplicate/missing host dispatch")
    sessions = [
        json.loads(row[0])
        for row in records(
            directory, "native-peer.sqlite", "SELECT observation FROM sessions"
        )
    ]
    receipts = [o for o in sessions if o["binding"] == binding]
    if context["before"]:
        check(
            all(b == binding for _, b in calls) and not sessions,
            "unexpected effect at before-dispatch boundary",
        )
        check(
            not receipts
            and snapshot["execution"] == "Unknown"
            and snapshot["native_session_id"] is None,
            "before-effect uncertainty fabricated native success",
        )
        check(
            selected.count("cancel") == 0 and "discover" in selected,
            "before-effect intent retried or not reconciled",
        )
        return {
            "boundary": "before_peer_effect",
            "launch_calls": 1,
            "native_receipts": 0,
            "state": "unknown",
        }
    check(len(receipts) == 1, "ambiguous native receipts")
    receipt = receipts[0]
    check(
        receipt.get("terminal") == "Completed"
        and receipt.get("observed_at_ms") == snapshot.get("observed_at_ms"),
        "native outcome/time not observed from peer",
    )
    check(
        snapshot["native_session_id"] == receipt["native_session_id"]
        and snapshot["last_sequence"] == receipt["sequence"]
        and snapshot["last_sequence"] >= 2,
        "native identity/sequence mismatch",
    )
    check(
        snapshot["execution"] == {"Terminal": "Completed"}
        and snapshot["cancellation"] == "ObservedTerminal",
        "native completion/cancel state mismatch",
    )
    check(
        selected.count("cancel") == 1
        and selected.index("launch")
        < selected.index("discover")
        < selected.index("cancel"),
        "host effect count/order mismatch",
    )
    race = context["terminal_race"]
    race_binding = {k: race["request"]["admission"][k] for k in keys}
    native = state["entries"][race_binding["operation_id"]]
    check(
        all(b in (binding, race_binding) for _, b in calls),
        "unexpected host target/effect",
    )
    race_receipts = [o for o in sessions if o["binding"] == race_binding]
    check(
        len(sessions) == 2
        and len(race_receipts) == 1
        and race_receipts[0].get("terminal") == "Completed"
        and race_receipts[0]["native_session_id"] == native["native_session_id"],
        "race outcome/session lacks independent receipt",
    )
    race_calls = [action for action, b in calls if b == race_binding]
    check(
        race_calls.count("launch") == 1 and "discover" in race_calls,
        "race operation did not reconcile exactly one dispatch",
    )
    held = json.loads(
        (
            directory / ("reconcile-ready-" + race_binding["operation_id"] + ".json")
        ).read_text()
    )
    returned = json.loads(
        (
            directory / ("reconcile-returned-" + race_binding["operation_id"] + ".json")
        ).read_text()
    )
    check(
        held == returned
        and native["binding"] == race_binding
        and held["execution"] == {"Terminal": "Completed"}
        and held["cancellation"] == "None",
        "terminal barrier fabricated host observation",
    )
    check(
        race["core"]["native_session_id"] == native["native_session_id"]
        and race["core"]["cancellation"] == "ObservedTerminal"
        and race["core"]["execution"] == native["execution"],
        "core lost accepted cancellation or changed native outcome",
    )
    check(
        max(race["completed_events"]) > max(race["accepted_events"]),
        "terminal reply was not after cancel acceptance",
    )
    check(
        not any(action == "cancel" and b == race_binding for action, b in calls),
        "late cancellation effect after observed completion",
    )
    return {
        "boundary": "after_peer_effect",
        "launch_calls": 1,
        "cancel_calls": 1,
        "native_receipts": 1,
        "identity_preserved": True,
        "cancel_completion_race": "preserved",
    }


def observe_delivery(directory, context):
    request = context["request"]
    accepted = request["accepted"]
    validation = accepted["validation"]
    reference = validation["artifact"]
    artifacts = records(
        directory, "core.sqlite", "SELECT reference,bytes FROM artifacts"
    )
    validations = records(directory, "core.sqlite", "SELECT record FROM validations")
    acceptances = records(directory, "core.sqlite", "SELECT record FROM acceptances")
    check(
        len(artifacts) == len(validations) == len(acceptances) == 1,
        "missing/extra durable artifact evidence",
    )
    stored_ref, data = artifacts[0]
    check(
        json.loads(stored_ref) == reference
        and len(data) <= 1048576
        and sha(data) == reference["sha256"],
        "changed accepted bytes",
    )
    check(
        json.loads(validations[0][0]) == validation
        and validation["passed"] is True
        and validation["policy_revision"] == reference["binding"]["policy_revision"],
        "validation skipped or rebound",
    )
    check(
        json.loads(acceptances[0][0]) == accepted
        and not (directory / "artifact.bin").exists(),
        "acceptance changed or generation input retained",
    )
    rows = records(
        directory, "core.sqlite", "SELECT request,state,receipt,conflict FROM outbox"
    )
    check(
        len(rows) == 1 and json.loads(rows[0][0]) == request,
        "delivery reservation rebound",
    )
    calls = [
        (action, json.loads(r))
        for action, r in records(
            directory,
            "destination.sqlite",
            "SELECT action,request FROM calls ORDER BY id",
        )
    ]
    check(
        all(r == request for _, r in calls), "destination transport authority changed"
    )
    receipts = records(
        directory, "destination.sqlite", "SELECT receipt,bytes FROM receipts"
    )
    sends = sum(action == "send" for action, _ in calls)
    if context["before"]:
        check(
            sends == 0
            and not receipts
            and rows[0][1] == "unknown"
            and rows[0][2] is None
            and rows[0][3] == 0,
            "uncertain reservation resent or receipt fabricated",
        )
        return {
            "boundary": "reservation_before_send",
            "send_calls": 0,
            "receipt_count": 0,
            "state": "unknown",
            "accepted_sha256": sha(data),
        }
    check(
        sends == 1
        and len(receipts) == 1
        and calls[0][0] == "send"
        and any(action == "lookup" for action, _ in calls[1:]),
        "delivery count/order mismatch",
    )
    receipt, delivered = receipts[0]
    receipt = json.loads(receipt)
    check(
        receipt["request"] == request
        and delivered == data
        and sha(delivered) == reference["sha256"],
        "destination bytes/receipt differ from acceptance",
    )
    check(
        rows[0][1] == "delivered"
        and json.loads(rows[0][2]) == receipt
        and rows[0][3] == 1,
        "confirmed receipt changed or later contradiction was forgotten",
    )
    return {
        "boundary": "lost_ack_after_send",
        "send_calls": 1,
        "receipt_count": 1,
        "accepted_sha256": sha(data),
        "conflicting_receipt": "durably_fenced",
    }


def run(lane, platform_prepared, core_prepared, root=ROOT):
    config = validate_manifest(
        json.loads((root / "specs/runtime-integration-scenarios-v1.json").read_text())
    )
    sources = inventory(root)
    if lane not in LANES:
        raise Blocked("unsupported lane")
    core = root / "components/core"
    platform = root / "components/platform"
    artifact = load_component(core, "tools/runtime_artifact.py", "runtime_artifact")
    try:
        prepared = artifact.validate(core, core_prepared)
        declared = json.loads((core / "docs/runtime-build.json").read_text())
        if prepared.get("features") != declared.get("features"):
            raise ValueError("prepared feature binding mismatch")
        allowed = (
            ("delivery-runtime",)
            if lane == "H07"
            else ("host-runtime", "host-runtime,artifact-store", "delivery-runtime")
        )
        if prepared.get("features") not in allowed:
            raise ValueError("required runtime feature absent")
        platform_module = load_component(
            platform, "tools/temporal_lane.py", "integration_platform_preflight"
        )
        platform_module.Lane(platform_prepared)
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        raise Blocked(
            "prepared integration prerequisites unavailable: " + type(error).__name__
        ) from error
    host = load_component(core, "tools/test_host_runtime.py", "test_host_runtime")
    controller = (
        host
        if lane == "H02"
        else load_component(
            core, "tools/test_delivery_runtime.py", "test_delivery_runtime"
        )
    )
    import inspect

    if "observer" not in inspect.signature(controller.run).parameters:
        raise Blocked("pinned component lacks integration observer interface")
    independent = []
    component = []
    for repeat in range(config["repeat_runs"]):
        observed = []
        outcomes = []
        for before in (False, True):
            observer = observe_host if lane == "H02" else observe_delivery

            def capture(directory, context):
                observed.append(observer(directory, context))

            if lane == "H02":
                outcome = controller.run(
                    platform,
                    platform_prepared,
                    core_prepared,
                    config["seed"],
                    before,
                    observer=capture,
                )
            else:
                outcome = controller.run(
                    platform,
                    platform_prepared,
                    core_prepared,
                    config["seed"],
                    before,
                    observer=capture,
                )
            outcomes.append(outcome)
        check(len(observed) == 2, "missing independent seam observations")
        independent.append(observed)
        component.append(outcomes)
    check(
        all(o == independent[0] for o in independent),
        "independent seeded outcomes differ",
    )
    check(all(o == component[0] for o in component), "component seeded outcomes differ")
    return {
        "schema_version": "runspindle.integration-scenario-report.v1",
        "lane": lane,
        "lane_status": "passed",
        "aggregate": aggregate("passed"),
        "evidence_class": "isolated_integration",
        "sources": sources,
        "repeat_runs": config["repeat_runs"],
        "seed": config["seed"],
        "boundary_matrix": LANES[lane],
        "independent_observations": independent[0],
        "component_outcomes": component[0],
        "normalized_outcome_sha256": sha(
            json.dumps(independent[0], sort_keys=True).encode()
        ),
        "system_gates": GATES,
        "live_acceptance": "not_run",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lane", choices=list(LANES), required=True)
    p.add_argument("--platform-prepared", required=True)
    p.add_argument("--core-prepared", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    try:
        report = run(a.lane, a.platform_prepared, a.core_prepared)
    except (
        Blocked,
        OSError,
        RuntimeError,
        AssertionError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        sqlite3.Error,
    ) as error:
        status = (
            "blocked"
            if isinstance(error, (Blocked, OSError))
            or type(error).__name__ == "Blocked"
            else "failed"
        )
        report = {
            "lane": a.lane,
            "lane_status": status,
            "aggregate": aggregate(status),
            "reason": str(error),
            "live_acceptance": "not_run",
        }
    report["observed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pathlib.Path(a.report).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({k: report[k] for k in ("lane", "lane_status", "aggregate")}))
    raise SystemExit(1 if report["aggregate"] == "failed" else 78)


if __name__ == "__main__":
    main()
