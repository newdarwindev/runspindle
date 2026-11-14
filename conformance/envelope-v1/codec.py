"""Independent stdlib producer/consumer; never imports Rust/component serializers.

Validation uses explicit exceptions so optimized Python cannot skip rejection.
"""

import json
import re
from typing import Any, Callable, Iterable, TypeVar, cast

T = TypeVar("T")

VERSION = "runspindle.envelope.v1"
BINDING = "task_id revision operation_id policy_revision host_id workspace_id lease_epoch".split()
ADMISSION = "delivery_namespace delivery_id predecessor_revision normalized_digest grant_ref".split()
OBSERVATION = "native_session_id sequence observed_at_ms state".split()
DELIVERY = "artifact_id artifact_revision sha256 validator_revision account_id destination_id delivery_operation_id".split()


def fields(value: Any, names: Iterable[str]) -> None:
    if not (type(value) is dict and set(value) == set(names)):
        raise AssertionError("fields")


def identifier(value: Any) -> None:
    if not (
        type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value)
    ):
        raise AssertionError("identifier")


def counter(value: Any, positive: bool = False) -> None:
    if not (type(value) is int and int(positive) <= value <= 2**64 - 1):
        raise AssertionError("counter")


def digest(value: Any) -> None:
    if not (type(value) is str and re.fullmatch("[0-9a-f]{64}", value)):
        raise AssertionError("digest")


def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in rows:
        if key in result:
            raise AssertionError("duplicate key")
        result[key] = value
    return result


def unsigned_token(token: str) -> int:
    if token.startswith("-"):
        raise AssertionError("negative integer token")
    return int(token)


def decode(data: bytes | str) -> dict[str, Any]:
    if len(data) > 1048576:
        raise AssertionError("size")
    value = json.loads(
        data.decode("utf-8") if isinstance(data, bytes) else data,
        parse_int=unsigned_token,
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(AssertionError("constant")),
    )
    validate(value)
    return cast(dict[str, Any], value)


def encode(value: dict[str, Any]) -> bytes:
    validate(value)
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def validate(e: dict[str, Any]) -> None:
    fields(e, ["version", "message_type", "message_id", "binding", "payload"])
    if e["version"] != VERSION:
        raise AssertionError("version")
    identifier(e["message_id"])
    b = e["binding"]
    fields(b, BINDING)
    for key in BINDING:
        (
            counter(b[key], True)
            if key in ["revision", "lease_epoch"]
            else identifier(b[key])
        )
    p = e["payload"]
    kind = e["message_type"]
    if kind == "admission_request":
        fields(p, ADMISSION)
        for key in ["delivery_namespace", "delivery_id", "grant_ref"]:
            identifier(p[key])
        digest(p["normalized_digest"])
        predecessor = p["predecessor_revision"]
        if b["revision"] == 1:
            if predecessor is not None:
                raise AssertionError("predecessor")
        else:
            counter(predecessor, True)
            if predecessor != b["revision"] - 1:
                raise AssertionError("predecessor")
    elif kind == "host_observation":
        fields(p, OBSERVATION)
        identifier(p["native_session_id"])
        counter(p["sequence"], True)
        counter(p["observed_at_ms"])
        if p["state"] not in ["running", "completed", "failed", "cancelled"]:
            raise AssertionError("state")
    elif kind in ["delivery_request", "delivery_receipt"]:
        if kind == "delivery_receipt":
            fields(p, ["request", "receipt_id"])
            identifier(p["receipt_id"])
            p = p["request"]
        fields(p, DELIVERY)
        for key in [
            "artifact_id",
            "validator_revision",
            "account_id",
            "destination_id",
            "delivery_operation_id",
        ]:
            identifier(p[key])
        counter(p["artifact_revision"], True)
        digest(p["sha256"])
        if p["delivery_operation_id"] == b["operation_id"]:
            raise AssertionError("operation")
    else:
        raise AssertionError("message_type")


def component(e: dict[str, Any]) -> dict[str, Any]:
    validate(e)
    p, b = e["payload"], e["binding"]
    if e["message_type"] == "admission_request":
        return dict(version="runspindle.runtime.v1", **b, **p)
    if e["message_type"] == "host_observation":
        return dict(
            binding=b,
            native_session_id=p["native_session_id"],
            sequence=p["sequence"],
            observed_at_ms=p["observed_at_ms"],
            terminal=None if p["state"] == "running" else p["state"].capitalize(),
        )

    def delivery(p: dict[str, Any]) -> dict[str, Any]:
        artifact = {k: p[k] for k in ["artifact_id", "artifact_revision", "sha256"]}
        artifact["binding"] = b
        return dict(
            version="runspindle.integration.v1",
            accepted=dict(
                validation=dict(
                    artifact=artifact,
                    validator_revision=p["validator_revision"],
                    policy_revision=b["policy_revision"],
                    passed=True,
                )
            ),
            **{
                k: p[k]
                for k in ["account_id", "destination_id", "delivery_operation_id"]
            },
        )

    if e["message_type"] == "delivery_request":
        return delivery(p)
    return dict(request=delivery(p["request"]), receipt_id=p["receipt_id"])


def consume(
    data: bytes | str,
    expected_binding: dict[str, Any],
    adapter: Callable[[dict[str, Any]], T],
    session: str | None = None,
    last_sequence: int = 0,
    destination: tuple[str, str] | None = None,
) -> T:
    e = decode(data)
    if e["binding"] != expected_binding:
        raise AssertionError("binding mismatch")
    p = e["payload"]
    if e["message_type"] == "host_observation":
        if not (p["native_session_id"] == session and p["sequence"] > last_sequence):
            raise AssertionError("stale session/sequence")
    if e["message_type"] in ["delivery_request", "delivery_receipt"]:
        if e["message_type"] == "delivery_receipt":
            p = p["request"]
        if (p["account_id"], p["destination_id"]) != destination:
            raise AssertionError("destination mismatch")
    return adapter(component(e))
