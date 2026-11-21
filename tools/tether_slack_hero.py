#!/usr/bin/env python3
"""H01 real pinned Tether, with synthetic Core, native events and Slack."""

from __future__ import annotations

import base64
import hmac
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(ROOT))
from tools.browser_effect_hero import (  # noqa: E402
    deny_external,
    git,
    require,
    rows,
    sha,
    stage_source,
)

MANIFEST = ROOT / "scenarios/tether-slack-v1.json"
CANARY = "SYNTHETIC_H01_REDACTION_CANARY"
SIGNING_KEY = b"synthetic-h01-fixture-key-not-a-credential"
OUTBOUND_TEXT = "Synthetic accepted result"
MUTATION_FAILURE = "provider call or effect count changed"
CRASH_EXIT = 17


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def task_id(source: dict[str, Any]) -> str:
    fields = (
        "app_id",
        "account_id",
        "workspace_id",
        "channel_id",
        "thread_id",
        "message_id",
    )
    return "tether-task:" + sha(canonical([source[key] for key in fields]))


def binding_for(spec: dict[str, Any], revision: int) -> dict[str, Any]:
    return {
        "task_id": task_id(spec["source"]),
        "revision": revision,
        "operation_id": f"h01-operation-{revision}",
        "policy_revision": "h01-policy",
        "host_id": spec["host"],
        "workspace_id": spec["source"]["workspace_id"],
        "lease_epoch": 1,
    }


def callbacks(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source = spec["source"]
    message = {
        "type": "message",
        "user": source["actor_id"],
        "text": "synthetic original request",
        "ts": source["message_id"],
        "thread_ts": source["thread_id"],
    }
    create = {
        "type": "event_callback",
        "api_app_id": source["app_id"],
        "team_id": source["workspace_id"],
        "event_id": "EvH01CREATE",
        "event_time": spec["clock"],
        "is_ext_shared_channel": False,
        "event": {**message, "channel": source["channel_id"]},
    }
    edit = {
        **create,
        "event_id": "EvH01EDIT",
        "event": {
            "type": "message",
            "subtype": "message_changed",
            "hidden": True,
            "channel": source["channel_id"],
            "ts": spec["edit_ts"],
            "message": {
                **message,
                "text": "synthetic corrected request",
                "edited": {"user": source["actor_id"], "ts": spec["edit_ts"]},
            },
            "previous_message": message,
        },
    }
    return create, edit


def expected_grants(spec: dict[str, Any], types: Any, identity: Any) -> dict[str, Any]:
    source = spec["source"]
    grants = {}
    for revision, event in enumerate(callbacks(spec), 1):
        body = event["event"].get("message", event["event"])
        digest = sha(
            canonical(
                {
                    "version": "runspindle.tether.ingress.v1",
                    "event_id": event["event_id"],
                    "message_id": source["message_id"],
                    "actor_id": source["actor_id"],
                    "workspace_id": source["workspace_id"],
                    "channel_id": source["channel_id"],
                    "thread_id": source["thread_id"],
                    "revision": revision,
                    "kind": "create" if revision == 1 else "edit",
                    "text": body["text"],
                    "mirrored": False,
                }
            )
        )
        grants[digest] = types.Grant(
            identity,
            digest,
            task_id(source),
            revision,
            f"h01-operation-{revision}",
            "h01-policy",
            spec["host"],
            1,
            f"h01-grant-{revision}",
            "h01-install",
        )
    return grants


def reject(call: Callable[[], object], rejection: type[Exception]) -> None:
    try:
        call()
    except rejection:
        return
    raise AssertionError("forbidden operation admitted")


def ingress(app: Any, rejection: type[Exception], spec: dict[str, Any]) -> list[str]:
    create, edit = callbacks(spec)

    def submit(
        value: dict[str, Any], *, stale: bool = False, signing_key: bytes = SIGNING_KEY
    ) -> str:
        raw = json.dumps(value, indent=2).encode()
        timestamp = spec["clock"] - (600 if stale else 0)
        signature = hmac.digest(
            signing_key, f"v0:{timestamp}:".encode() + raw, "sha256"
        )
        return str(
            app.ingest(
                raw,
                (
                    ("Content-Type", "application/json"),
                    ("X-Slack-Request-Timestamp", str(timestamp)),
                    ("X-Slack-Signature", "v0=" + signature.hex()),
                ),
            )
        )

    reject(lambda: submit(edit), rejection)
    reject(lambda: submit(create, stale=True), rejection)
    reject(lambda: submit(create, signing_key=b"wrong-synthetic-key"), rejection)
    wrong = {**create, "event": {**create["event"], "channel": "COTHER"}}
    reject(lambda: submit(wrong), rejection)
    return [submit(create), submit(create), submit(edit), submit(create)]


def progress(app: Any, spec: dict[str, Any], destination: Any) -> list[str]:
    native = import_module("tether.native_testing")
    testing = import_module("tether.testing")
    key = task_id(spec["source"])
    binding = native.Binding(key, spec["host"], spec["session"], destination)
    reader = native.NativeSource(binding, native.Mode.EVENTS, lambda: spec["clock"])
    event = native.Event(
        binding,
        "h01-progress",
        1,
        spec["clock"],
        "public_summary",
        testing.Payload("Synthetic progress " + CANARY),
    )
    writes: list[tuple[str, str]] = []

    def sink(item: Any) -> None:
        writes.append((item.binding.session_id, item.event_id))
        app.admission.persist_projection(
            key,
            2,
            {
                "version": "runspindle.projection.v1",
                "kind": item.kind,
                "message": item.payload.text,
            },
        )

    outcomes = [
        reader.emit(item, sink).outcome
        for item in (
            replace(event, sequence=2),
            replace(event, observed_at=spec["clock"] - 120),
            replace(event, kind="hidden_reasoning"),
            replace(event, binding=replace(binding, session_id="other-session")),
            event,
            event,
        )
    ]
    require(writes == [(spec["session"], "h01-progress")], "forbidden mirror call")
    require(CANARY not in app.admission.render_projection(key, 2), "rendered canary")
    return outcomes


class SyntheticSlack:
    """A separately observed non-idempotent effect store. No Slack networking."""

    def __init__(self, db: sqlite3.Connection, testing: Any, mode: str) -> None:
        self.db, self.testing, self.mode = db, testing, mode
        db.executescript("""
            CREATE TABLE IF NOT EXISTS effects (
                id INTEGER PRIMARY KEY, route BLOB, operation TEXT, message TEXT,
                artifact TEXT, filename TEXT, content BLOB
            );
            CREATE TABLE IF NOT EXISTS calls (action TEXT);
        """)

    @staticmethod
    def route(destination: Any) -> bytes:
        return canonical(
            [destination.workspace_id, destination.channel_id, destination.thread_id]
        )

    def send(self, destination: Any, operation: str, payload: Any) -> None:
        item = payload.attachments[0]
        with self.db:
            self.db.execute("INSERT INTO calls VALUES ('send')")
            self.db.execute(
                "INSERT INTO effects(route,operation,message,artifact,filename,content) VALUES (?,?,?,?,?,?)",
                (
                    self.route(destination),
                    operation,
                    payload.text,
                    item.attachment_id,
                    item.filename,
                    item.content,
                ),
            )
        if self.mode == "crash_after":
            os._exit(CRASH_EXIT)
        raise TimeoutError("synthetic lost acknowledgment")

    def readback(self, destination: Any, operation: str) -> object:
        with self.db:
            self.db.execute("INSERT INTO calls VALUES ('readback')")
        if self.mode == "outage":
            raise TimeoutError("synthetic readback outage")
        records = self.db.execute(
            "SELECT id,route,message,artifact,filename,content FROM effects WHERE operation=? ORDER BY id",
            (operation,),
        ).fetchall()
        return tuple(
            self.testing.Record(
                (
                    self.testing.Destination(*json.loads(route))
                    if self.mode != "wrong_thread"
                    else replace(destination, thread_id="1900000000.000003")
                ),
                operation,
                f"h01-message-{identity}",
                self.testing.Payload(
                    text, (self.testing.Attachment(artifact_id, filename, content),)
                ),
                False,
            )
            for identity, route, text, artifact_id, filename, content in records
        )


def artifact(testing: Any, content: bytes) -> Any:
    return testing.Payload(
        OUTBOUND_TEXT,
        (testing.Attachment("h01-artifact", "result.txt", content),),
    )


def delivery(app: Any, data: Path, mode: str, spec: dict[str, Any]) -> dict[str, Any]:
    testing = import_module("tether.testing")
    journal_type = import_module("tether.journal").ProviderJournal
    rejection = import_module("tether.admission").Rejected
    source = spec["source"]
    destination = testing.Destination(
        source["workspace_id"], source["channel_id"], source["thread_id"]
    )
    content = spec["accepted_bytes"].encode()
    payload = artifact(testing, content)
    envelope = {
        "version": "runspindle.envelope.v1",
        "message_type": "delivery_request",
        "message_id": "h01-delivery-request",
        "payload": {
            "artifact_id": "h01-artifact",
            "artifact_revision": 1,
            "sha256": sha(content),
            "validator_revision": "h01-validator",
            "account_id": source["account_id"],
            "destination_id": "h01-route",
            "delivery_operation_id": "h01-delivery",
        },
    }
    older, current = [
        canonical({**envelope, "binding": binding_for(spec, revision)})
        for revision in (1, 2)
    ]

    def authorize(raw: bytes, digest: str) -> bool:
        return raw in (older, current) and bool(digest == payload.digest())

    def resolve(account: str, route: str) -> Any:
        return (
            destination
            if (account, route) == (source["account_id"], "h01-route")
            else None
        )

    with (
        closing(sqlite3.connect(data / "provider.sqlite")) as db,
        closing(
            journal_type(
                str(data / "journal.sqlite"),
                app.admission,
                authorize=authorize,
                resolve=resolve,
            )
        ) as journal,
    ):
        provider = SyntheticSlack(db, testing, mode)
        projections = None
        if mode in spec["initial_faults"]:
            projections = progress(app, spec, destination)
            require(
                projections == spec["expected"]["progress"],
                "unexpected progress outcomes",
            )
            reject(lambda: journal.send(older, payload, provider), rejection)
        observation = journal.send(current, payload, provider)
        return {
            "outcome": observation.state,
            "message": observation.message_id,
            "progress": projections,
        }


def worker(source: Path, data: Path, mode: str) -> object:
    deny_external(data)
    sys.path.insert(0, str(source))
    admission = import_module("tether.admission")
    revision = import_module("tether.slack_revisions")
    semantic = import_module("tether.semantic_journal")
    route_type = import_module("tether.slack_ingress").Route
    sanitize = import_module("tether.sanitization").Sanitizer
    spec = json.loads(MANIFEST.read_bytes())
    scope = spec["source"]
    route = route_type(
        scope["app_id"],
        scope["workspace_id"],
        scope["actor_id"],
        scope["channel_id"],
        scope["thread_id"],
    )
    grants = expected_grants(spec, admission, route.identity)
    with closing(
        revision.SignedRevisionIngress(
            str(data / "admission.sqlite"),
            SIGNING_KEY,
            route,
            lambda: spec["clock"],
            account_id=scope["account_id"],
            authorize=lambda identity, digest: grants.get(digest)
            if identity == route.identity
            else None,
            references=lambda env: semantic.IntentReferences(
                f"h01-v3-{env['binding']['revision']}",
                f"h01-inbound-{env['binding']['revision']}",
            ),
            sanitizer=sanitize((CANARY,)),
        )
    ) as app:
        if mode == "ingress":
            return ingress(app, admission.Rejected, spec)
        return delivery(app, data, mode, spec)


def invoke(source: Path, data: Path, mode: str) -> Any:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            *("-O" for _ in range(sys.flags.optimize)),
            str(SCRIPT),
            "--worker",
            str(source),
            str(data),
            mode,
        ],
        cwd=data,
        capture_output=True,
        check=False,
        timeout=15,
    )
    require(not (data / "forbidden").exists(), "worker attempted external effect")
    if mode == "crash_after":
        require(
            result.returncode == CRASH_EXIT and not result.stdout and not result.stderr,
            "expected abrupt worker interruption",
        )
        return {"outcome": "interrupted", "message": None, "progress": None}
    require(result.returncode == 0 and not result.stderr, f"worker failed: {mode}")
    require(
        CANARY.encode() not in result.stdout and SIGNING_KEY not in result.stdout,
        "worker output contained a fixture secret",
    )
    return json.loads(result.stdout)


def scenario(
    source: Path, data: Path, spec: dict[str, Any], fault: str
) -> dict[str, Any]:
    data.mkdir()
    expected = spec["expected"]
    key = task_id(spec["source"])
    inbound = invoke(source, data, "ingress")
    require(inbound == expected["ingress"], "unexpected ingress outcomes")
    admission = data / "admission.sqlite"
    require(
        [
            (task, revision, kind, json.loads(event)["binding"])
            for task, revision, kind, event in rows(
                admission,
                "SELECT task,revision,kind,envelope FROM revisions ORDER BY rowid",
            )
        ]
        == [
            (key, "1", "create", binding_for(spec, 1)),
            (key, "2", "edit", binding_for(spec, 2)),
        ],
        "incorrect retained revisions",
    )
    require(
        rows(admission, "SELECT task,revision,deleted FROM heads") == [(key, "2", 0)],
        "incorrect current identity",
    )
    first = invoke(source, data, fault)
    initial_reservation = "attempted" if fault == "crash_after" else "unknown"
    journal = data / "journal.sqlite"
    require(
        rows(journal, "SELECT state,acknowledgement,observed FROM provider_attempts")
        == [(initial_reservation, None, None)],
        "dispatch intent did not survive",
    )
    phases = [first, *(invoke(source, data, mode) for mode in spec["readback_phases"])]
    provider = data / "provider.sqlite"
    calls = [
        value for (value,) in rows(provider, "SELECT action FROM calls ORDER BY rowid")
    ]
    scope = spec["source"]
    route = canonical([scope["workspace_id"], scope["channel_id"], scope["thread_id"]])
    content = spec["accepted_bytes"].encode()
    require(
        calls == expected["provider_calls"]
        and rows(
            provider,
            "SELECT route,operation,message,artifact,filename,content FROM effects",
        )
        == [
            (
                route,
                "h01-delivery",
                OUTBOUND_TEXT,
                "h01-artifact",
                "result.txt",
                content,
            )
        ],
        MUTATION_FAILURE,
    )
    require(
        [phase["outcome"] for phase in phases] == expected[f"{fault}_outcomes"]
        and [phase["message"] for phase in phases]
        == [None, None, None, "h01-message-1"],
        "unexpected delivery observations",
    )
    require(
        rows(
            journal,
            "SELECT operation,acknowledgement,observed,conflict FROM provider_attempts",
        )
        == [("h01-delivery", None, "h01-message-1", 0)],
        "wrong durable receipt",
    )
    projections = rows(
        admission, "SELECT task,revision,body FROM sanitized_projections"
    )
    require(
        len(projections) == 1 and projections[0][:2] == (key, "2"),
        "unexpected retained projection",
    )
    projection = json.loads(projections[0][2])
    require(
        projection["kind"] == "public_summary"
        and projection["message"].startswith("Synthetic progress "),
        "lost public progress",
    )
    encodings = (
        CANARY.encode(),
        SIGNING_KEY,
        base64.b64encode(CANARY.encode()),
        base64.b64encode(SIGNING_KEY),
    )
    require(
        not any(
            needle in p.read_bytes()
            for p in data.iterdir()
            if p.is_file()
            for needle in encodings
        ),
        "retained canary",
    )
    return {
        "task": key,
        "initial_reservation": initial_reservation,
        "host": spec["host"],
        "thread": scope["thread_id"],
        "session": spec["session"],
        "revisions": [1, 2],
        "ingress": inbound,
        "progress": phases[0]["progress"],
        "calls": calls,
        "delivery": [phase["outcome"] for phase in phases],
        "artifact_sha256": sha(content),
    }


def run() -> dict[str, Any]:
    raw = MANIFEST.read_bytes()
    spec = json.loads(raw)
    require(
        spec["version"] == "runspindle.tether-slack-hero.v1"
        and spec["initial_faults"] == ["dispatch", "crash_after"]
        and spec["readback_phases"] == ["outage", "wrong_thread", "resume"],
        "invalid scenario",
    )
    with TemporaryDirectory(prefix="runspindle-h01-") as temporary:
        root = Path(temporary).resolve()
        source = root / "source"
        pins = stage_source(source, spec, component="tether")
        observed = {
            fault: scenario(source, root / (fault + "-first"), spec, fault)
            for fault in spec["initial_faults"]
        }
        require(
            observed
            == {
                fault: scenario(source, root / (fault + "-repeat"), spec, fault)
                for fault in spec["initial_faults"]
            },
            "normalized replay changed",
        )
        mutant = root / "mutant"
        shutil.copytree(source, mutant)
        path = mutant / "tether/journal.py"
        original = path.read_text()
        needle = "return self.lookup(raw, payload, provider)"
        require(original.count(needle) == 1, "mutation anchor changed")
        path.write_text(
            original.replace(
                needle,
                "try:\n"
                "                    provider.send(destination, operation, payload)\n"
                "                except TimeoutError:\n"
                "                    pass\n"
                "                " + needle,
            )
        )
        try:
            scenario(mutant, root / "mutated", spec, "dispatch")
        except AssertionError as error:
            require(
                str(error) == MUTATION_FAILURE,
                "mutation failed outside provider oracle",
            )
            mutant_sends = rows(
                root / "mutated/provider.sqlite",
                "SELECT action FROM calls ORDER BY rowid",
            ).count(("send",))
            require(mutant_sends > 1, "mutation lacks duplicate evidence")
        else:
            raise AssertionError("blind-resend mutation escaped")
    return {
        "hero": "H01",
        "status": "passed",
        "repeat_runs": 2,
        "evidence_class": "isolated_pinned_tether_with_synthetic_peers",
        "composition": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "components": pins,
        "fixture_sha256": sha(raw),
        "harness_sha256": sha(SCRIPT.read_bytes()),
        "composition_lock_sha256": sha((ROOT / "composition.lock.json").read_bytes()),
        "toolchain": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "observed": observed,
        "mutations": ["blind_resend"],
        "mutant_provider_sends": mutant_sends,
        "core_only": "not_run",
        "host_only": "not_run",
        "system_aggregate": "blocked",
        "live": "not_run",
    }


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])))
    else:
        require(len(sys.argv) == 1, "usage: python3 -B tools/tether_slack_hero.py")
        print(json.dumps(run(), indent=2, sort_keys=True))
