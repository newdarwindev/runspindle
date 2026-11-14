#!/usr/bin/env python3
"""H10 retained-feedback seam: real pinned stores, synthetic external adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import ExitStack, closing
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MANIFEST = ROOT / "scenarios/feedback-collection-v1.json"


def require(value: object) -> None:
    if not value:
        raise ValueError("feedback hero invariant failed")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, timeout=30
    ).strip()


def verify_sources(tether: Path, refinery: Path) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_bytes())
    require(manifest["version"] == "runspindle.feedback-hero.v1")
    require(set(manifest["sources"]) == {"tether", "refinery"})
    require(
        subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "merge-base",
                "--is-ancestor",
                manifest["composition_base"],
                "HEAD",
            ],
            check=False,
        ).returncode
        == 0
    )
    lock = {
        x["component"]: x
        for x in json.loads((ROOT / "composition.lock.json").read_bytes())["components"]
    }
    for name, source in (("tether", tether), ("refinery", refinery)):
        item = manifest["sources"][name]
        require(source.is_dir() and not source.is_symlink())
        require(git(source, "rev-parse", "HEAD") == item["commit"])
        require(item["base"] == lock[name]["commit"])
        require(
            git(ROOT, "ls-files", "--stage", "--", "components/" + name).startswith(
                "160000 " + item["base"] + " 0\t"
            )
        )
        require(not git(source, "status", "--porcelain"))
        # The entire root is on sys.path, so ignored top-level files can also
        # shadow stdlib imports. Reject ALL untracked root bytes, not merely
        # package files or a suffix allowlist. Sources must be pristine/cache-free.
        require(not git(source, "ls-files", "--others"))
        require(
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(source),
                    "merge-base",
                    "--is-ancestor",
                    item["base"],
                    item["commit"],
                ],
                check=False,
            ).returncode
            == 0
        )
        for path, digest in item["files"].items():
            file = source / path
            require(
                file.is_file()
                and not file.is_symlink()
                and sha(file.read_bytes()) == digest
            )
        require(
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(source),
                    "merge-base",
                    "--is-ancestor",
                    item["commit"],
                    item["merged_ancestry"],
                ],
                check=False,
            ).returncode
            == 0
        )
    pin = json.loads((refinery / "dependencies/tether-feedback.json").read_bytes())
    require(pin["commit"] == manifest["sources"]["tether"]["commit"])
    return cast(dict[str, Any], manifest)


def rows(path: Path, query: str) -> list[Any]:
    require(path.is_file())
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        return db.execute(query).fetchall()


def fixture(
    root: Path, tether: Path, refinery: Path, stack: ExitStack
) -> dict[str, Any]:
    # Each worker starts with an empty temporary pycache prefix and -B. No test
    # modules or fake collection implementations are imported.
    sys.path.insert(0, str(refinery))
    from refinery.feedback_collection import Material, SelectedFeedback
    from refinery.lineage import (
        Feedback,
        GoldRule,
        OutputRevision,
        SourceRevision,
        digest,
    )
    from refinery import storage

    legacy: Any = storage
    pack = legacy.pack
    from refinery.tether_dependency import TetherDependency

    dep = TetherDependency(tether)
    a, j, f, t = (
        dep.modules["tether." + n]
        for n in ("admission", "journal", "feedback", "testing")
    )
    identity = a.Identity("actor", "workspace", "channel", "thread")
    raw = a.canonical(
        dict(
            version="runspindle.tether.ingress.v1",
            event_id="event",
            message_id="input",
            actor_id="actor",
            workspace_id="workspace",
            channel_id="channel",
            thread_id="thread",
            revision=1,
            kind="create",
            text="Synthetic task",
            mirrored=False,
        )
    )
    grant = a.Grant(
        identity,
        digest(raw),
        "task",
        1,
        "operation",
        "policy",
        "host",
        1,
        "grant",
        "synthetic",
    )
    admission = a.Admission(
        str(root / "admission.sqlite"),
        lambda r, p: identity if p == digest(r) else None,
        lambda i, d: grant if i == identity and d == grant.event_digest else None,
    )
    stack.callback(admission.close)
    admission.ingest(raw, digest(raw))
    source = SourceRevision(
        "source", "1", "family", b"Synthetic task", digest(b"Synthetic task")
    )
    output = OutputRevision(
        "artifact",
        "1",
        "summary",
        "source",
        "1",
        source.sha256,
        b"Synthetic answer",
        digest(b"Synthetic answer"),
    )
    material = Material(source, output, "verified-material")
    payload = t.Payload(
        "Synthetic answer", (t.Attachment("artifact", "output.txt", output.content),)
    )
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
                workspace_id="workspace",
                lease_epoch=1,
            ),
            payload=dict(
                artifact_id="artifact",
                artifact_revision=1,
                sha256=output.sha256,
                validator_revision="validator",
                account_id="account",
                destination_id="destination",
                delivery_operation_id="delivery",
            ),
        )
    )
    destination = t.Destination("workspace", "channel", "thread")
    journal = j.ProviderJournal(
        str(root / "journal.sqlite"),
        admission,
        lambda r, d: r == delivery and d == payload.digest(),
        lambda a, d: destination,
    )
    stack.callback(journal.close)
    provider = t.FakeSlack(destination, lambda: 100, lambda: "output-message")
    # Initial fixture preparation is the only simulated provider-send phase.
    if not (root / "prepared.json").exists():
        journal.send(delivery, payload, provider)
        journal.lookup(delivery, payload, provider)
    target = journal.retained_target(delivery, payload, "output-message")
    feedback = f.FeedbackStore(
        str(root / "feedback.sqlite"),
        journal,
        lambda r, p: identity if p == digest(r) else None,
        lambda i, e, t: f.FeedbackGrant(i, e, t, "retention-policy", "retention-grant"),
        lambda r, p, x: r == delivery and p == payload and x == target,
    )
    stack.callback(feedback.close)
    event = dict(
        version="runspindle.tether.feedback.v1",
        namespace="synthetic",
        event_id="feedback-event-1",
        feedback_id="feedback",
        revision=1,
        predecessor=None,
        actor_id="actor",
        workspace_id="workspace",
        channel_id="channel",
        thread_id="thread",
        kind="create",
        judgment="positive",
        correction=None,
        target=target,
    )
    raw_feedback = a.canonical(event)
    if not (root / "prepared.json").exists():
        feedback.ingest(raw_feedback, digest(raw_feedback), delivery, payload)
    selected = SelectedFeedback(
        "synthetic", "feedback", 1, digest(raw_feedback), "gold"
    )
    rules = (GoldRule("summary", "gold", ("positive", "correction")),)
    # Explicit synthetic grants are prepared from the selected immutable batch,
    # not accepted from whatever digest the collection callback proposes.
    judgment = Feedback(
        digest(pack(("synthetic", "feedback", 1, digest(raw_feedback)))),
        "actor",
        "artifact",
        "1",
        output.sha256,
        "gold",
        "positive",
        None,
    )
    batch = digest(pack(((source,), (output,), (judgment,), rules, "seed")))
    store = legacy.Store(root / "refinery.sqlite")
    stack.callback(store.close)
    return locals()


def worker(root: Path, tether: Path, refinery: Path, mode: str) -> None:
    verify_sources(tether, refinery)
    with ExitStack() as stack:
        network = stack.enter_context(
            patch("socket.socket", side_effect=AssertionError("network forbidden"))
        )
        x = fixture(root, tether, refinery, stack)
        if mode == "prepare":
            (root / "prepared.json").write_text(
                json.dumps(
                    {
                        "batch": x["batch"],
                        "event": sha(x["raw_feedback"]),
                        "artifact": x["output"].sha256,
                    }
                )
            )
            require(len(x["provider"].requests) == 2)
        else:
            from refinery.feedback_collection import collect

            prepared = json.loads((root / "prepared.json").read_bytes())
            require(prepared["batch"] == x["batch"])
            calls: list[list[str]] = []

            def consent(digest: str, ref: str) -> bool:
                calls.append([digest, ref])
                return digest == prepared["batch"] and ref in (
                    "collection-grant",
                    "training-grant",
                )

            training_calls = 0

            def training(digest: str, ref: str) -> bool:
                nonlocal training_calls
                training_calls += 1
                if mode == "crash" and training_calls == 3:
                    os._exit(
                        70
                    )  # Deliberate pre-commit interruption; parent checks rollback.
                return (
                    consent(digest, ref)
                    and ref == "training-grant"
                    and (mode != "revoked" or training_calls < 3)
                )

            if mode == "stale":
                event = dict(
                    x["event"],
                    revision=2,
                    predecessor=1,
                    event_id="feedback-event-2",
                    kind="edit",
                    judgment="negative",
                )
                raw = x["a"].canonical(event)
                x["feedback"].ingest(raw, sha(raw), x["delivery"], x["payload"])
            selections = (x["selected"],) * (2 if mode == "duplicate" else 1)
            if mode == "mutant":
                import types

                text = (refinery / "refinery/feedback_collection.py").read_text()
                anchor = "            recheck()\n"
                require(text.count(anchor) == 1)
                module: Any = types.ModuleType("refinery.hero_mutant")
                module.__package__ = "refinery"
                sys.modules[module.__name__] = module
                stack.callback(sys.modules.pop, module.__name__, None)
                exec(
                    compile(
                        text.replace(anchor, "            pass\n"),
                        "<deliberate-mutant>",
                        "exec",
                    ),
                    module.__dict__,
                )
                module.SelectedFeedback = type(x["selected"])
                module.Material = type(x["material"])
                collect = module.collect
                mode = "revoked"
            denied = False
            try:
                snapshot = collect(
                    x["store"],
                    x["dep"],
                    x["feedback"],
                    selections,
                    x["rules"],
                    seed="seed",
                    collection_ref="collection-grant",
                    training_ref="training-grant",
                    resolve_material=lambda target: x["material"],
                    verify_material=lambda target, material: target == x["target"]
                    and material == x["material"],
                    approve_collection=lambda d, r: consent(d, r)
                    and r == "collection-grant",
                    approve_training=training,
                )
            except ValueError:
                denied = True
                snapshot = None
            require(not x["provider"].requests)
            (root / "result.json").write_text(
                json.dumps(
                    {
                        "snapshot": snapshot,
                        "denied": denied,
                        "approval_calls": calls,
                        "provider_calls": 0,
                    }
                )
            )
        network.assert_not_called()


def observe(root: Path) -> dict[str, Any]:
    # Reuse the composition's independent codec, not Refinery's serializer.
    from tools.maintained_scenarios import decode as component_decode

    decode: Any = component_decode

    for table in ("budgets", "experiments", "attempts", "environments", "activations"):
        require(
            rows(root / "refinery.sqlite", "SELECT count(*) FROM " + table)[0][0] == 0
        )
    objects = rows(
        root / "refinery.sqlite",
        "SELECT kind,identity,digest,payload FROM objects ORDER BY kind,identity",
    )
    require(all(sha(payload) == digest for _, _, digest, payload in objects))
    values = {kind: decode(json.loads(payload)) for kind, _, _, payload in objects}
    result = json.loads((root / "result.json").read_bytes())
    retained = rows(
        root / "feedback.sqlite",
        "SELECT revision,digest,body FROM feedback_revisions ORDER BY revision",
    )
    require(all(sha(body) == digest for _, digest, body in retained))
    require(result["provider_calls"] == 0)
    if objects:
        require(len(objects) == 6 and len(values) == 6)
        require(
            result["snapshot"]
            == next(identity for kind, identity, _, _ in objects if kind == "lineage")
        )
        selection = values["feedback_collection"]["selected"][0]
        require(selection["selection"]["event_sha256"] == retained[0][1])
        example = values["lineage"]["dataset"]["examples"][0]
        require(
            sha(example["output"]["content"])
            == example["output"]["sha256"]
            == selection["target"]["artifact_sha256"]
        )
        require(example["feedback"][0]["actor_id"] == "actor")
        require(
            values["lineage"]["batch_sha256"]
            == values["feedback_collection"]["batch_sha256"]
        )
        require(
            values["lineage"]["collection_evidence"]
            == next(
                identity
                for kind, identity, _, _ in objects
                if kind == "feedback_collection"
            )
        )

    return {
        "objects": len(objects),
        "lineage": values.get("lineage"),
        "receipt": values.get("feedback_collection"),
        "retained_revisions": len(retained),
        "result": result,
        "object_digest": sha(b"".join(p for _, _, _, p in objects)),
    }


def run(tether: Path, refinery: Path) -> dict[str, Any]:
    tether, refinery = tether.absolute(), refinery.absolute()
    manifest = verify_sources(tether, refinery)
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="feedback-hero-") as directory:
        root = Path(directory)

        def invoke(case: Path, mode: str) -> None:
            case.mkdir(exist_ok=True)
            cache = root / "empty-cache"
            environment = dict(
                os.environ, PYTHONPYCACHEPREFIX=str(cache), PYTHONDONTWRITEBYTECODE="1"
            )
            command = [
                sys.executable,
                *(["-O"] if sys.flags.optimize else []),
                "-B",
                str(Path(__file__).resolve()),
                "--worker",
                mode,
                "--directory",
                str(case),
                "--tether",
                str(tether),
                "--refinery",
                str(refinery),
            ]
            completed = subprocess.run(
                command, env=environment, capture_output=True, timeout=40
            )
            require(completed.returncode == (70 if mode == "crash" else 0))

        for repeat in range(2):
            case = root / f"positive-{repeat}"
            invoke(case, "prepare")
            require(
                rows(case / "refinery.sqlite", "SELECT count(*) FROM objects")[0][0]
                == 0
            )
            invoke(case, "collect")
            first = observe(case)
            require(
                not first["result"]["denied"]
                and len(first["lineage"]["dataset"]["examples"]) == 1
            )
            require(
                first["receipt"]["batch_sha256"]
                == json.loads((case / "prepared.json").read_bytes())["batch"]
            )
            require(
                first["receipt"]["dependency_commit"]
                == manifest["sources"]["tether"]["commit"]
            )
            require(first["retained_revisions"] == 1)
            invoke(case, "collect")
            require(first == observe(case))
            outcomes.append(first["object_digest"])
        require(outcomes[0] == outcomes[1])
        crash = root / "crash"
        invoke(crash, "prepare")
        invoke(crash, "crash")
        require(
            rows(crash / "refinery.sqlite", "SELECT count(*) FROM objects")[0][0] == 0
        )
        invoke(crash, "collect")
        require(observe(crash)["object_digest"] == outcomes[0])
        for mode in ("duplicate", "revoked", "stale", "mutant"):
            case = root / mode
            invoke(case, "prepare")
            invoke(case, mode)
            found = observe(case)
            if mode == "mutant":
                # Independent SQL catches an actual unauthorized commit when the
                # exact final guard is deliberately removed in a throwaway module.
                require(found["objects"] > 0 and not found["result"]["denied"])
            else:
                require(found["objects"] == 0 and found["result"]["denied"])
    return {
        "lane": "H10.retained_feedback_collection",
        "status": "passed",
        "repeat_runs": 2,
        "fresh_process_replay": "passed",
        "precommit_process_crash_recovery": "passed",
        "negative_cases": 3,
        "deliberate_mutation_detected": True,
        "independent_object_digest": outcomes[0],
        "sources": {n: i["commit"] for n, i in manifest["sources"].items()},
        "system_acceptance": "blocked",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tether", type=Path, default=ROOT / "components/tether")
    parser.add_argument("--refinery", type=Path, default=ROOT / "components/refinery")
    parser.add_argument(
        "--worker",
        choices=(
            "prepare",
            "collect",
            "duplicate",
            "revoked",
            "stale",
            "mutant",
            "crash",
        ),
    )
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
                    "lane": "H10.retained_feedback_collection",
                    "status": "failed",
                    "reason": "bounded_validation_error",
                }
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
