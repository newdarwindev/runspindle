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
    from tools.development_bundle import VERSION, DisposableTarget, verify

    metadata = json.loads((directory / "bundle-input.json").read_bytes())
    pins = metadata["component_commits"]
    target = DisposableTarget.create()
    try:
        content = (directory / "development.bundle").read_bytes()
        installed = target.install(
            VERSION, content, component_commits=pins, expected_generation=0
        )
        manifest, files, digest = verify(content, component_commits=pins)
        # Independent filesystem reads outside the install adapter.
        observed = {
            str(p.relative_to(target.root / "versions" / digest)): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in (target.root / "versions" / digest).rglob("*")
            if p.is_file()
        }
        assert observed == manifest["files"] and installed["manifest_sha256"] == digest
        # The actual Linux component suite separately exercises process interruption.
        return {
            "manifest_sha256": digest,
            "installed_files": observed,
            "target": "linux/arm64",
            "unsupported": installed["unsupported"],
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
