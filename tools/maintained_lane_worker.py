#!/usr/bin/env python3
"""Synthetic composition stimuli against real component code in isolated processes.

The parent independently reads component SQL/serving/filesystem results. This
worker's status alone never establishes integration or approval authority.
"""
import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import socket


def deny_network(*_args, **_kwargs):
    raise AssertionError("outbound network forbidden")


def refinery_fixture(store):
    from refinery.lineage import (
        SourceRevision,
        OutputRevision,
        Feedback,
        GoldRule,
        digest,
    )
    from refinery.storage import VERSION, pack

    sources, outputs, feedback = [], [], []
    for i in range(12):
        source = SourceRevision(
            "source-" + str(i),
            "1",
            "family-" + str(i),
            b"synthetic input",
            digest(b"synthetic input"),
        )
        output = OutputRevision(
            "output-" + str(i),
            "1",
            "summary",
            source.source_id,
            source.revision,
            source.sha256,
            b"gold",
            digest(b"gold"),
        )
        event = Feedback(
            "feedback-" + str(i),
            "observed-reviewer",
            output.output_id,
            output.revision,
            output.sha256,
            "summary-v1",
            "positive",
        )
        sources.append(source)
        outputs.append(output)
        feedback.append(event)
    old = outputs[0]
    outputs.append(
        replace(
            old,
            revision="2",
            content=b"new unlabelled output",
            sha256=digest(b"new unlabelled output"),
        )
    )
    feedback.append(
        replace(
            feedback[1],
            feedback_id="conflict",
            kind="correction",
            correction=b"conflicting correction",
        )
    )
    feedback.append(
        replace(feedback[2], feedback_id="missing", output_revision="absent")
    )
    observations = {digest(pack(event)): event.actor_id for event in feedback}
    batch = (
        tuple(sources),
        tuple(outputs),
        tuple(feedback),
        (GoldRule("summary", "summary-v1", ("positive", "correction")),),
        "seed-2",
    )
    expected_consent = digest(pack(batch))
    snapshot = store.commit_lineage(
        VERSION,
        *batch[:4],
        seed=batch[4],
        collection_evidence="synthetic-collection-proof",
        verify_collection=lambda sha, evidence: sha == expected_consent
        and evidence == "synthetic-collection-proof",
        verify_actor=lambda event: observations.get(digest(pack(event))),
    )
    return snapshot


def run_refinery(directory, dspy=False):
    from refinery.storage import Store, VERSION, pack
    from refinery.lineage import digest
    from refinery.evaluation import (
        Completion,
        Configuration,
        Experiment,
        Limits,
        Reservation,
        VirtualClock,
    )
    from refinery.durable_evaluation import run
    from refinery.serving import Registry, Policy, Approval, LocalServing

    with Store(directory / "refinery.sqlite") as store:
        snapshot = refinery_fixture(store)
        dataset, split = store.lineage(snapshot)
        if not dspy:
            return {
                "snapshot_sha256": snapshot,
                "dataset_sha256": split.dataset_sha256,
                "split_sha256": split.sha256,
                "examples": len(dataset.examples),
                "excluded_counts": dataset.excluded_counts,
                "assignments": split.assignments,
            }
        heldout = [
            e
            for e in dataset.examples
            if split.partition(e.source.family_id) == "heldout"
        ]
        script = tuple(
            Completion(e.gold, 1, 1, True, 1) for _ in range(2) for e in heldout
        )
        from refinery.dspy_local import LocalDSPyProvider

        inventory = Path("/refinery/offline/dependencies.json")
        provider = LocalDSPyProvider(
            script,
            clock=VirtualClock(),
            dependency_sha256=digest(inventory.read_bytes()),
        )
        config = Configuration(
            Limits(100, 1000, 1000, 1000),
            Reservation(10, 10),
            provider.sha256,
            1_000_000,
            0,
            1,
            (),
            provider="dspy.local.v1",
            optimizer="dspy.predict.v1",
        )

        def evaluate(name, answer):
            content = json.dumps(
                {"format": "synthetic.map.v1", "responses": {"hello": answer}},
                sort_keys=True,
            ).encode()
            experiment = Experiment(
                split.dataset_sha256,
                split.sha256,
                b"baseline",
                digest(b"baseline"),
                content,
                digest(content),
                config,
                config.sha256,
            )
            local = LocalDSPyProvider(
                script,
                clock=VirtualClock(),
                dependency_sha256=provider.dependency_sha256,
            )
            report = run(
                store,
                VERSION,
                name,
                snapshot,
                experiment,
                provider=local,
                budget_id=name,
            )
            assert report.status == "passed" and len(local.calls) == len(local.lm_calls)
            return report

        registry = Registry(
            store,
            verify_approval=lambda approval: (
                "synthetic-reviewer"
                if approval.evidence == "independent-synthetic-proof"
                else None
            ),
        )
        adapter = LocalServing(directory / "serving.sqlite")
        try:
            reports = []
            for number, answer in enumerate(("first", "second")):
                name = "candidate-" + str(number)
                report = evaluate(name, answer)
                reports.append(report)
                key = registry.qualify(
                    VERSION, name, Policy("local", 1_000_000, 0, 1000, 1000)
                )
                candidate = store.get("candidate", key)
                approval = Approval(
                    candidate["candidate_sha256"],
                    candidate["evaluation_sha256"],
                    candidate["policy_sha256"],
                    "local",
                    "synthetic-reviewer",
                    "independent-synthetic-proof",
                )
                registry.begin(VERSION, name, key, approval, expected_generation=number)
                if number == 1:
                    # Exit the actual worker process after load, before registry acknowledgement.
                    def lost_reply(point):
                        if point == "after_candidate_load":
                            os._exit(93)

                    registry.load(VERSION, name, adapter, checkpoint=lost_reply)
                else:
                    assert registry.load(VERSION, name, adapter) == "active"
            second_output = adapter.predict("local", "hello")
            registry.rollback(VERSION, "rollback", "local", expected_generation=2)
            assert registry.load(VERSION, "rollback", adapter) == "active"
            return {
                "snapshot_sha256": snapshot,
                "reports": [digest(pack(r)) for r in reports],
                "dspy_calls": sum(len(r.attempts) for r in reports),
                "second_output": second_output,
                "rolled_output": adapter.predict("local", "hello"),
                "readback": adapter.readback("local"),
            }
        finally:
            adapter.close()


def recover_refinery(directory):
    from refinery.storage import Store, VERSION
    from refinery.serving import Registry, LocalServing

    with Store(directory / "refinery.sqlite") as store:
        registry = Registry(
            store,
            verify_approval=lambda a: (
                "synthetic-reviewer"
                if a.evidence == "independent-synthetic-proof"
                else None
            ),
        )
        adapter = LocalServing(directory / "serving.sqlite")
        try:
            second = adapter.predict("local", "hello")
            assert (
                second["output"] == "second"
                and registry.state("local")["pending"] == "candidate-1"
            )
            assert registry.load(VERSION, "candidate-1", adapter) == "active"
            registry.rollback(VERSION, "rollback", "local", expected_generation=2)
            assert registry.load(VERSION, "rollback", adapter) == "active"
            reports = [
                row[0]
                for row in store.db.execute(
                    "SELECT report FROM experiments ORDER BY identity"
                )
            ]
            return {
                "reports": reports,
                "dspy_calls": store.db.execute(
                    "SELECT count(*) FROM attempts"
                ).fetchone()[0],
                "second_output": second,
                "rolled_output": adapter.predict("local", "hello"),
                "readback": adapter.readback("local"),
            }
        finally:
            adapter.close()


def run_bundle(directory):
    import subprocess
    import sys
    from tools.streaming_bundle import VERSION, StreamingTarget, file_sha

    metadata = json.loads((directory / "bundle-input.json").read_bytes())
    pins = metadata["component_commits"]
    target = StreamingTarget.create()

    def independent(variant):
        expected = metadata["bundles"][variant]
        digest = json.loads((target.root / "active.json").read_bytes())[
            "manifest_sha256"
        ]
        assert digest == expected["sha256"]
        folder = target.root / "versions" / digest
        # Hash actual files independently, without using installer's verification.
        observed = {
            str(p.relative_to(folder)): {
                "sha256": file_sha(p),
                "size": p.stat().st_size,
                "mode": p.stat().st_mode & 0o7777,
            }
            for p in folder.rglob("*")
            if p.is_file()
        }
        assert observed == expected["manifest"]["files"]
        return (
            folder,
            hashlib.sha256(
                json.dumps(observed, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        )

    def action(code, *args, expected=0):
        script = (
            "import sys,os,json; from tools.streaming_bundle import StreamingTarget,VERSION; t=StreamingTarget(sys.argv[1]); pins=json.loads(sys.argv[2]); "
            + code
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(target.root),
                json.dumps(pins),
                *map(str, args),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert completed.returncode == expected, completed.stderr[-3000:]

    def smoke(folder):
        env = {
            **os.environ,
            "PYTHONPATH": str(folder / "refinery")
            + ":"
            + str(folder / "dependencies")
            + ":"
            + str(folder / "platform"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "DSPY_CACHEDIR": "/tmp/dspy-installed",
            "HOME": "/tmp",
            "LITELLM_LOCAL_MODEL_COST_MAP": "True",
            "HF_HUB_OFFLINE": "1",
        }
        core = subprocess.run(
            [str(folder / "bin/temporal-runtime"), "offline-smoke"],
            capture_output=True,
            text=True,
            cwd="/tmp",
            env=env,
            timeout=30,
        )
        assert core.returncode == 0, core.stderr
        core_result = json.loads(core.stdout)
        assert (
            core_result["status"] == "passed"
            and core_result["unverified_acceptance"] == "denied"
        )
        evidence = target.root / ("smoke-" + folder.name)
        evidence.mkdir()
        worker = folder / "composition/tools/maintained_lane_worker.py"
        first = subprocess.run(
            [sys.executable, str(worker), "H11", str(evidence)],
            capture_output=True,
            text=True,
            cwd="/tmp",
            env=env,
            timeout=90,
        )
        assert first.returncode == 93, first.stderr[-3000:]
        recovered = subprocess.run(
            [sys.executable, str(worker), "H11", str(evidence), "--recover"],
            capture_output=True,
            text=True,
            cwd="/tmp",
            env=env,
            timeout=90,
        )
        assert recovered.returncode == 0, recovered.stderr[-3000:]
        serving = json.loads((evidence / "H11-worker.json").read_bytes())
        # Query real SQLite bytes/call order separately from the serving adapter.
        import sqlite3
        from contextlib import closing

        with closing(
            sqlite3.connect(
                "file:" + str(evidence / "serving.sqlite") + "?mode=rw", uri=True
            )
        ) as db:
            db.execute("PRAGMA query_only=ON")
            calls = db.execute(
                "SELECT activation,digest FROM calls WHERE action='load' ORDER BY id"
            ).fetchall()
            active = db.execute(
                "SELECT activation,digest,content FROM active WHERE environment='local'"
            ).fetchone()
        assert [r[0] for r in calls] == ["candidate-0", "candidate-1", "rollback"]
        assert (
            active[0] == "rollback"
            and active[1] == hashlib.sha256(active[2]).hexdigest() == calls[0][1]
        )
        assert serving["rolled_output"]["candidate_sha256"] == active[1]
        return {
            "core": core_result,
            "serving_sha256": active[1],
            "load_order": [r[0] for r in calls],
            "dspy_calls": serving["dspy_calls"],
        }

    try:
        target.install(
            VERSION,
            directory / "baseline.stream",
            component_commits=pins,
            expected_generation=0,
        )
        folder, baseline_tree = independent("baseline")
        baseline_smoke = smoke(folder)
        action(
            "t.install(VERSION,sys.argv[3],component_commits=pins,expected_generation=1,checkpoint=lambda p:os._exit(101) if p=='after_staged_payload' else None)",
            directory / "upgrade.stream",
            expected=101,
        )
        assert target.state()["pending"] == metadata["bundles"]["upgrade"]["sha256"]
        independent("baseline")
        action("t.recover(VERSION,component_commits=pins);t.close()")
        folder, upgrade_tree = independent("upgrade")
        assert smoke(folder) == baseline_smoke
        action(
            "t.rollback(VERSION,component_commits=pins,expected_generation=2,checkpoint=lambda p:os._exit(102) if p=='after_rollback_intent' else None)",
            expected=102,
        )
        independent("upgrade")
        action("t.recover(VERSION,component_commits=pins);t.close()")
        folder, rolled_tree = independent("baseline")
        assert (
            rolled_tree == baseline_tree
            and target.state()["generation"] == 3
            and target.state()["pending"] is None
        )
        return {
            "bundle_version": VERSION,
            "baseline_manifest_sha256": metadata["bundles"]["baseline"]["sha256"],
            "upgrade_manifest_sha256": metadata["bundles"]["upgrade"]["sha256"],
            "installed_files": len(
                metadata["bundles"]["baseline"]["manifest"]["files"]
            ),
            "baseline_tree_sha256": baseline_tree,
            "upgrade_tree_sha256": upgrade_tree,
            "installed_smoke": baseline_smoke,
            "fresh_process_recovery": ["staged_upgrade", "rollback_intent"],
            "target": "linux/arm64",
            "unsupported": metadata["bundles"]["baseline"]["manifest"]["unsupported"],
        }
    finally:
        target.cleanup()
        assert not target.root.exists()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("lane", choices=["H10", "H11", "H12"])
    parser.add_argument("directory")
    parser.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    socket.create_connection = deny_network
    socket.socket.connect = deny_network
    directory = Path(args.directory)
    result = (
        run_bundle(directory)
        if args.lane == "H12"
        else (
            recover_refinery(directory)
            if args.recover
            else run_refinery(directory, args.lane == "H11")
        )
    )
    (directory / (args.lane + "-worker.json")).write_text(
        json.dumps(result, sort_keys=True)
    )
    print(json.dumps(result, sort_keys=True))
