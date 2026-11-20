#!/usr/bin/env python3
"""H10 signed reaction through pinned Tether and Refinery to a replayable batch."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.feedback_hero import ROOT, require, rows, sha, verify_sources

SECRET = b"synthetic-composition-reactor-not-a-credential"
NOW = 1900000000
ACTOR = "UCOMPOSITION"
WORKSPACE = "TCOMPOSITION"
CHANNEL = "CCOMPOSITION"
APP = "ACOMPOSITION"
THREAD = "1900000000.000001"
MESSAGE = "1900000000.000003"
TASK = "Synthetic case: preserve the exact answer."
ANSWER = b"Synthetic answer: caf\xc3\xa9."
DATASET = "composition-h10"
FAMILY = "composition-h10-family"
SEED = "hero-dataset"
REF = "synthetic-dataset-grant"
PHASES = (
    "prepare",
    "crash",
    "materialize",
    "replay",
    "wrong_purpose",
    "denied_consent",
    "remove",
    "source_revoked",
    "withdraw",
    "withdrawn",
    "mutant",
)


def wire(event_id: str, event: dict[str, Any]) -> bytes:
    return json.dumps(
        dict(
            type="event_callback",
            api_app_id=APP,
            team_id=WORKSPACE,
            event_id=event_id,
            event=event,
            event_time=NOW,
            is_ext_shared_channel=False,
            authorizations=[
                dict(
                    team_id=WORKSPACE,
                    user_id="UBOT",
                    enterprise_id=None,
                    is_bot=True,
                    is_enterprise_install=False,
                )
            ],
        )
    ).encode()


def signature(raw: bytes) -> tuple[tuple[str, str], ...]:
    proof = hmac.digest(SECRET, f"v0:{NOW}:".encode() + raw, "sha256").hex()
    return (
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(raw))),
        ("X-Slack-Request-Timestamp", str(NOW)),
        ("X-Slack-Signature", "v0=" + proof),
    )


def reaction(removed: bool) -> bytes:
    return wire(
        "EvRemove" if removed else "EvAdd",
        dict(
            type="reaction_removed" if removed else "reaction_added",
            user=ACTOR,
            reaction="thumbsup",
            event_ts="1900000000.000005" if removed else "1900000000.000004",
            item=dict(type="message", channel=CHANNEL, ts=MESSAGE),
        ),
    )


def open_tether(
    root: Path, dep: Any, stack: ExitStack, payload: Any, output_sha: str, prepare: bool
) -> tuple[Any, dict[str, Any], Any]:
    a, j, f, t, ingress, slack = (
        dep.modules["tether." + name]
        for name in (
            "admission",
            "journal",
            "feedback",
            "testing",
            "slack_ingress",
            "slack_feedback",
        )
    )
    route = ingress.Route(APP, WORKSPACE, ACTOR, CHANNEL, THREAD)
    signed = ingress.SignedSlackIngress(
        str(root / "admission.sqlite"),
        SECRET,
        route,
        lambda: NOW,
        lambda identity, digest: a.Grant(
            identity,
            digest,
            "task",
            1,
            "operation",
            "policy",
            "host",
            1,
            "grant",
            "synthetic",
        ),
    )
    stack.callback(signed.close)
    if prepare:
        raw = wire(
            "EvTask",
            dict(
                type="message",
                channel=CHANNEL,
                user=ACTOR,
                text=TASK,
                ts="1900000000.000002",
                thread_ts=THREAD,
            ),
        )
        signed.ingest(raw, signature(raw))
    delivery = a.canonical(
        dict(
            version="runspindle.envelope.v1",
            message_type="delivery_request",
            message_id="delivery-event",
            binding=dict(
                task_id="task",
                revision=1,
                operation_id="operation",
                policy_revision="policy",
                host_id="host",
                workspace_id=WORKSPACE,
                lease_epoch=1,
            ),
            payload=dict(
                artifact_id="artifact",
                artifact_revision=1,
                sha256=output_sha,
                validator_revision="validator",
                account_id="account",
                destination_id="destination",
                delivery_operation_id="delivery",
            ),
        )
    )
    destination = t.Destination(WORKSPACE, CHANNEL, THREAD)
    journal = j.ProviderJournal(
        str(root / "journal.sqlite"),
        signed.admission,
        lambda raw, digest: raw == delivery and digest == payload.digest(),
        lambda *_: destination,
    )
    stack.callback(journal.close)
    provider = t.FakeSlack(destination, lambda: NOW, lambda: MESSAGE)
    if prepare:
        journal.send(delivery, payload, provider)
        journal.lookup(delivery, payload, provider)
    app = slack.SignedSlackFeedback(
        str(root / "feedback.sqlite"),
        SECRET,
        route,
        lambda: NOW,
        journal,
        slack.FeedbackTarget(delivery, payload, MESSAGE),
        authorize_retention=lambda i, e, x: f.FeedbackGrant(
            i, e, x, "retention", "grant"
        ),
        verify_target=lambda received, body, target: received == delivery
        and body == payload
        and target == journal.retained_target(delivery, payload, MESSAGE),
        authorize_invalidation=lambda _: True,
    )
    stack.callback(app.close)
    if prepare:
        raw = reaction(False)
        try:
            app.react(
                raw, (*signature(raw)[:-1], ("X-Slack-Signature", "v0=" + "0" * 64))
            )
        except a.Rejected:
            pass
        else:
            raise ValueError("mismatched signature accepted")
        app.react(raw, signature(raw))
    require(len(provider.requests) == (2 if prepare else 0))
    return app, journal.retained_target(delivery, payload, MESSAGE), a


def selection(app: Any, a: Any) -> Any:
    from refinery.feedback_collection import SelectedFeedback

    key = "reaction:" + sha(a.canonical([app.namespace, ACTOR, MESSAGE, "thumbs_up"]))
    event = app.store.evidence(app.namespace, key)["revisions"][0]
    return SelectedFeedback(app.namespace, key, 1, event["event_sha256"], "automatic")


def open_refinery(
    root: Path,
    tether: Path,
    refinery: Path,
    prepare: bool,
    stack: ExitStack,
) -> tuple[Any, Any, Any]:
    sys.path.insert(0, str(refinery))
    from refinery import storage
    from refinery.dataset_materialization import DatasetRegistry
    from refinery.feedback_collection import Material, collect
    from refinery.feedback_projection import RetainedSource
    from refinery.feedback_use import RetainedFeedbackUse
    from refinery.lineage import (
        THUMBS_UP_GOLD_RULE,
        Feedback,
        OutputRevision,
        SourceRevision,
    )
    from refinery.tether_dependency import TetherDependency

    dep = TetherDependency(tether)
    t = dep.modules["tether.testing"]
    payload = t.Payload(
        ANSWER.decode(), (t.Attachment("artifact", "answer.txt", ANSWER),)
    )
    app, target, a = open_tether(root, dep, stack, payload, sha(ANSWER), prepare)
    pick = selection(app, a)
    source = SourceRevision("source", "1", FAMILY, TASK.encode(), sha(TASK.encode()))
    output = OutputRevision(
        "artifact",
        "1",
        "summary",
        "source",
        "1",
        source.sha256,
        ANSWER,
        sha(ANSWER),
    )
    material = Material(source, output, "synthetic-exact-material")
    store_api: Any = storage
    store = store_api.Store(root / "refinery.sqlite")
    stack.callback(store.close)

    def exact_material(received: dict[str, Any], verified: Any) -> bool:
        return received == target and verified == material

    marker = root / "snapshot"
    feedback = Feedback(
        sha(store_api.pack((pick.namespace, pick.feedback_id, 1, pick.event_sha256))),
        ACTOR,
        "artifact",
        "1",
        output.sha256,
        THUMBS_UP_GOLD_RULE,
        "thumbs_up",
        None,
    )
    permitted_batch = sha(store_api.pack(((source,), (output,), (feedback,), (), SEED)))
    if prepare:
        snapshot = collect(
            store,
            dep,
            app.store,
            (pick,),
            (),
            seed=SEED,
            collection_ref="collection",
            training_ref="training",
            resolve_material=lambda received: material if received == target else None,
            verify_material=exact_material,
            approve_collection=lambda digest, ref: digest == permitted_batch
            and ref == "collection",
            approve_training=lambda digest, ref: digest == permitted_batch
            and ref == "training",
        )
        marker.write_text(snapshot, encoding="ascii")
    snapshot = marker.read_text(encoding="ascii")
    lineage = store.get("lineage", snapshot)
    require(lineage["batch_sha256"] == permitted_batch)
    collection_sha = lineage["collection_evidence"]
    use = RetainedFeedbackUse(
        dep,
        app.store,
        verify_material=exact_material,
        approve_use=lambda request: request.snapshot_sha256 == snapshot
        and request.batch_sha256 == permitted_batch
        and request.collection_receipt_sha256 == collection_sha
        and request.purpose
        in {
            "feedback_projection",
            "dataset_materialization",
            "optimization",
            "evaluation",
        },
    )
    source_ref = RetainedSource(
        store,
        snapshot,
        pick,
        use,
        lambda key, destination: dict(
            revision="local-only",
            collection_allowed=True,
            use_allowed=True,
            export_allowed=False,
            current_target=True,
        )
        if len(key) == 64 and destination == f"local-dataset:{DATASET}"
        else {},
    )
    registry = DatasetRegistry(root / "datasets.sqlite")
    stack.callback(registry.close)
    return app, source_ref, registry


def bindings(root: Path) -> tuple[dict[str, Any], str, bytes]:
    manifest = (root / "batch.json").read_bytes()
    body = json.loads(manifest)
    return body["items"][0]["item"], body["purpose"], manifest


def worker(root: Path, tether: Path, refinery: Path, phase: str) -> None:
    verify_sources(tether, refinery)
    root = root.resolve()
    with ExitStack() as stack:
        network = stack.enter_context(
            patch("socket.socket", side_effect=AssertionError("network forbidden"))
        )
        app, source, registry = open_refinery(
            root, tether, refinery, phase == "prepare", stack
        )

        from refinery import dataset_batch as batch

        permission_checks = 0

        def approve(descriptor: dict[str, Any], purpose: str, reference: str) -> bool:
            nonlocal permission_checks
            permission_checks += 1
            if phase == "crash" and purpose == "materialize" and permission_checks == 2:
                require(registry.db.in_transaction)
                require(
                    registry.db.execute("SELECT count(*) FROM items").fetchone() == (1,)
                )
                os._exit(70)
            return (
                phase != "denied_consent"
                and reference == REF
                and descriptor["output_sha256"] == sha(ANSWER)
                and descriptor["input_sha256"] == sha(canonical(TASK))
                and purpose in {"materialize", "evaluation", "optimization", "withdraw"}
            )

        by_split = {"train": "optimization", "heldout": "evaluation"}
        if phase in {"materialize", "crash"}:
            item = registry.materialize(
                source, DATASET, approve=approve, permission_ref=REF
            )
            purpose = by_split[item["split"]]
            manifest, contents = batch.capture(
                registry,
                (batch.Selection(item["item_id"], source),),
                purpose=purpose,
                approve=approve,
                permission_ref=REF,
            )
            (root / "batch.json").write_bytes(manifest)
            write_read_receipt(root, phase, contents)
        elif phase == "remove":
            raw = reaction(True)
            app.react(raw, signature(raw))
        elif phase == "withdraw":
            item, _, _ = bindings(root)
            registry.withdraw(item["item_id"], approve=approve, permission_ref=REF)
        elif phase != "prepare":
            item, purpose, manifest = bindings(root)
            if phase == "wrong_purpose":
                purpose = "evaluation" if purpose == "optimization" else "optimization"
            if phase == "mutant":
                stack.enter_context(
                    patch.object(registry, "available", return_value=None)
                )
            try:
                contents = batch.read(
                    manifest,
                    registry,
                    (batch.Selection(item["item_id"], source),),
                    purpose=purpose,
                    approve=approve,
                    permission_ref=REF,
                )
            except ValueError:
                contents = ()
            write_read_receipt(root, phase, contents)
        network.assert_not_called()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def write_read_receipt(
    root: Path, phase: str, contents: tuple[tuple[Any, bytes], ...]
) -> None:
    # Observe the bytes crossing the Registry read boundary, not its explanation.
    receipt = [[sha(canonical(text)), sha(answer)] for text, answer in contents]
    (root / (phase + ".json")).write_bytes(canonical(receipt))


def observe(root: Path) -> dict[str, Any]:
    """Recompute item and receipt attribution directly from persisted SQLite rows."""
    item, purpose, wire_manifest = bindings(root)
    dataset = rows(
        root / "datasets.sqlite",
        "SELECT item_id,descriptor,input,output,receipt FROM items",
    )
    require(len(dataset) == 1)
    item_id, descriptor, input_data, output, receipt = dataset[0]
    event = rows(
        root / "feedback.sqlite",
        "SELECT digest,body FROM feedback_revisions ORDER BY revision",
    )
    require(len(event) == 1 and sha(event[0][1]) == event[0][0])
    original = json.loads(event[0][1])
    identity = sha(
        canonical(
            dict(
                namespace=original["namespace"],
                feedback_id=original["feedback_id"],
                actor_id=ACTOR,
                target=original["target"],
            )
        )
    )
    evidence = json.loads(receipt)
    snapshot = (root / "snapshot").read_text(encoding="ascii")
    require(original["actor_id"] == ACTOR and original["judgment"] == "thumbs_up")
    target = original["target"]
    require(
        all(
            target[name] == value
            for name, value in {
                "artifact_id": "artifact",
                "artifact_revision": 1,
                "artifact_sha256": sha(ANSWER),
                "task_id": "task",
                "task_revision": 1,
                "message_id": MESSAGE,
                "delivery_operation_id": "delivery",
                "workspace_id": WORKSPACE,
                "channel_id": CHANNEL,
                "thread_id": THREAD,
            }.items()
        )
    )
    require(input_data == canonical(TASK) and output == ANSWER)
    require(
        item["input_sha256"] == sha(input_data) and item["output_sha256"] == sha(output)
    )
    require(item["source_identity_sha256"] == identity and item["dataset"] == DATASET)
    require(item["family_sha256"] == sha(canonical({"refinery_source_family": FAMILY})))
    split = "heldout" if int(sha(canonical([SEED, FAMILY])), 16) % 10 < 2 else "train"
    require(item["split"] == split)
    require(purpose == {"train": "optimization", "heldout": "evaluation"}[split])
    require(
        item_id
        == item["item_id"]
        == sha(canonical({key: val for key, val in item.items() if key != "item_id"}))
    )
    require(descriptor == canonical(item))
    require(evidence["item_id"] == item_id and evidence["snapshot_sha256"] == snapshot)
    require(evidence["selected_event_sha256"] == event[0][0])
    objects = {
        kind: (key, digest, payload)
        for kind, key, digest, payload in rows(
            root / "refinery.sqlite",
            "SELECT kind,identity,digest,payload FROM objects WHERE kind IN ('lineage','feedback_collection')",
        )
    }
    require(
        len(objects) == 2
        and all(
            key == digest == sha(payload) for key, digest, payload in objects.values()
        )
    )
    require(objects["lineage"][0] == snapshot)
    require(objects["feedback_collection"][0] == evidence["collection_receipt_sha256"])
    require(evidence["permission_reference_sha256"] == sha(REF.encode()))
    require(
        wire_manifest
        == canonical(
            dict(
                version="refinery.dataset-batch.v1",
                purpose=purpose,
                items=[
                    dict(
                        item=item, snapshot_sha256=snapshot, receipt_sha256=sha(receipt)
                    )
                ],
            )
        )
    )
    for table in ("budgets", "experiments", "attempts", "activations"):
        require(
            rows(root / "refinery.sqlite", "SELECT count(*) FROM " + table) == [(0,)]
        )
    return {
        "item_sha256": item_id,
        "manifest_sha256": sha(wire_manifest),
        "receipt_sha256": sha(receipt),
        "split": item["split"],
    }


def run(tether: Path, refinery: Path) -> dict[str, Any]:
    tether, refinery = tether.absolute(), refinery.absolute()
    sources = verify_sources(tether, refinery)["sources"]
    receipt = canonical([[sha(canonical(TASK)), sha(ANSWER)]])
    results = []
    with tempfile.TemporaryDirectory(prefix="feedback-dataset-hero-") as directory:
        root = Path(directory).resolve()

        def invoke(case: Path, phase: str) -> None:
            case.mkdir(mode=0o700, exist_ok=True)
            command = [
                sys.executable,
                "-I",
                *(["-O"] if sys.flags.optimize else []),
                "-B",
                "-X",
                "pycache_prefix=" + str(root / "empty-cache"),
                str(Path(__file__).resolve()),
                "--worker",
                phase,
                "--directory",
                str(case),
                "--tether",
                str(tether),
                "--refinery",
                str(refinery),
            ]
            completed = subprocess.run(
                command,
                capture_output=True,
                timeout=20,
            )
            require(completed.returncode == (70 if phase == "crash" else 0))

        for repeat in range(2):
            case = root / str(repeat)
            invoke(case, "prepare")
            effects = rows(case / "journal.sqlite", "SELECT * FROM provider_attempts")
            require(len(effects) == 1)
            if repeat == 0:
                invoke(case, "crash")
                require(
                    rows(case / "datasets.sqlite", "SELECT count(*) FROM items")
                    == [(0,)]
                )
                require(not (case / "batch.json").exists())
            invoke(case, "materialize")
            first = observe(case)
            invoke(case, "materialize")
            invoke(case, "replay")
            require(observe(case) == first)
            for phase in ("materialize", "replay"):
                require((case / (phase + ".json")).read_bytes() == receipt)
            for phase in ("wrong_purpose", "denied_consent"):
                invoke(case, phase)
                require((case / (phase + ".json")).read_bytes() == b"[]")
            if repeat == 0:
                invoke(case, "remove")
                invoke(case, "source_revoked")
                require((case / "source_revoked.json").read_bytes() == b"[]")
                require(
                    rows(
                        case / "feedback.sqlite",
                        "SELECT count(*) FROM feedback_invalidations",
                    )
                    == [(1,)]
                )
            else:
                invoke(case, "withdraw")
                invoke(case, "withdrawn")
                require((case / "withdrawn.json").read_bytes() == b"[]")
                invoke(case, "mutant")
                require((case / "mutant.json").read_bytes() == receipt)
                require(
                    rows(case / "datasets.sqlite", "SELECT count(*) FROM withdrawals")
                    == [(1,)]
                )
            require(
                rows(case / "datasets.sqlite", "SELECT count(*) FROM items") == [(1,)]
            )
            require(
                rows(case / "journal.sqlite", "SELECT * FROM provider_attempts")
                == effects
            )
            results.append(first)
        require(results[0] == results[1])
    return dict(
        lane="H10.materialized_feedback_batch",
        status="passed",
        repeat_runs=2,
        invalid_signature="denied",
        wrong_purpose="denied",
        missing_dataset_consent="denied",
        source_revocation="denied",
        local_withdrawal="denied",
        mutation_detected=True,
        crash_before_commit="rolled_back",
        replay=results[0],
        sources={name: source["commit"] for name, source in sources.items()},
        system_acceptance="blocked",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tether", type=Path, default=ROOT / "components/tether")
    parser.add_argument("--refinery", type=Path, default=ROOT / "components/refinery")
    parser.add_argument("--worker", choices=PHASES)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    try:
        if args.worker:
            require(args.directory is not None)
            worker(args.directory, args.tether, args.refinery, args.worker)
        else:
            print(json.dumps(run(args.tether, args.refinery), sort_keys=True))
        return 0
    except Exception:
        print(
            json.dumps(
                {
                    "lane": "H10.materialized_feedback_batch",
                    "status": "failed",
                    "reason": "bounded_validation_error",
                }
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
