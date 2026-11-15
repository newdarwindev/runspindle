"""Independent, stateless native-turn conformance codec; no runtime or input store.

The default-deny consumer uses injected synthetic callbacks only. It does not
implement the Host's durable reservation/owner fence or authorize a native call.
"""

import copy
import hashlib
import json
import re
from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")
VERSION = "runspindle.native-turn.v1"
MAX_ENVELOPE_BYTES = 4096
MAX_INPUT_BYTES = 2048
MAX_RPC_BYTES = 4096
BINDING = (
    "task_id",
    "revision",
    "operation_id",
    "policy_revision",
    "host_id",
    "workspace_id",
    "lease_epoch",
)


class Rejected(ValueError):
    """A closed-contract check failed; messages never include input text."""


def fields(value: Any, names: tuple[str, ...]) -> None:
    if type(value) is not dict or set(value) != set(names):
        raise Rejected("fields")


def identifier(value: Any) -> None:
    if type(value) is not str or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value
    ):
        raise Rejected("identifier")


def positive(value: Any, maximum: int = 2**64 - 1) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise Rejected("positive integer")


def binding(value: Any) -> None:
    fields(value, BINDING)
    for key in BINDING:
        if key in ("revision", "lease_epoch"):
            positive(value[key])
        else:
            identifier(value[key])


def validate(value: Any) -> None:
    fields(value, ("version", "binding", "thread_id", "input", "profile"))
    if value["version"] != VERSION:
        raise Rejected("version")
    binding(value["binding"])
    identifier(value["thread_id"])
    fields(value["input"], ("sha256", "byte_length"))
    digest = value["input"]["sha256"]
    if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise Rejected("digest")
    positive(value["input"]["byte_length"], MAX_INPUT_BYTES)
    fields(value["profile"], ("kind", "model"))
    if value["profile"]["kind"] != "read_only_text_v1":
        raise Rejected("profile")
    identifier(value["profile"]["model"])


def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in rows:
        if key in result:
            raise Rejected("duplicate key")
        result[key] = value
    return result


def integer(token: str) -> int:
    if token.startswith("-"):
        raise Rejected("negative token")
    return int(token)


def invalid_constant(_: str) -> None:
    raise Rejected("non-JSON constant")


def decode(data: bytes) -> dict[str, Any]:
    if type(data) is not bytes or len(data) > MAX_ENVELOPE_BYTES:
        raise Rejected("envelope bytes")
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_constant=invalid_constant,
        )
    except (ValueError, UnicodeError, RecursionError):
        raise Rejected("JSON") from None
    validate(value)
    if canonical(value) != data:
        raise Rejected("noncanonical JSON")
    return cast(dict[str, Any], value)


def canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def encode(value: dict[str, Any]) -> bytes:
    validate(value)
    raw = canonical(value)
    if len(raw) > MAX_ENVELOPE_BYTES:
        raise Rejected("envelope bytes")
    return raw


def text_bytes(data: bytes) -> str:
    if type(data) is not bytes or not 1 <= len(data) <= MAX_INPUT_BYTES:
        raise Rejected("input bytes")
    try:
        return data.decode("utf-8")
    except UnicodeError:
        raise Rejected("UTF-8") from None


def produce(
    expected_binding: dict[str, Any], thread_id: str, data: bytes, model: str
) -> bytes:
    """Hash exact supplied UTF-8 bytes; do not trim, normalize or store them."""
    text_bytes(data)
    return encode(
        {
            "version": VERSION,
            "binding": copy.deepcopy(expected_binding),
            "thread_id": thread_id,
            "input": {
                "sha256": hashlib.sha256(data).hexdigest(),
                "byte_length": len(data),
            },
            "profile": {"kind": "read_only_text_v1", "model": model},
        }
    )


def native_params(request: dict[str, Any], data: bytes) -> dict[str, Any]:
    """Map only the closed pinned turn/start subset; this never sends a request."""
    validate(request)
    text = text_bytes(data)
    if (
        len(data) != request["input"]["byte_length"]
        or hashlib.sha256(data).hexdigest() != request["input"]["sha256"]
    ):
        raise Rejected("input mismatch")
    return {
        "threadId": request["thread_id"],
        "input": [{"type": "text", "text": text, "text_elements": []}],
        "model": request["profile"]["model"],
        "approvalPolicy": "never",
        "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
    }


def rpc_bytes(request: dict[str, Any], data: bytes, request_id: int) -> bytes:
    """Offline size oracle including JSON escaping, RPC id and final newline."""
    positive(request_id)
    raw = (
        canonical(
            {
                "id": request_id,
                "method": "turn/start",
                "params": native_params(request, data),
            }
        )
        + b"\n"
    )
    if len(raw) > MAX_RPC_BYTES:
        raise Rejected("RPC bytes")
    return raw


def deny(_: dict[str, Any]) -> bool:
    return False


def consume(
    raw: bytes,
    expected_binding: dict[str, Any],
    expected_thread_id: str,
    data: bytes,
    adapter: Callable[[bytes], T],
    *,
    verifier: Callable[[dict[str, Any]], bool] = deny,
    request_id: int = 1,
) -> T:
    """Synthetic seam observation, not durable dispatch or a grant verifier.

    Each call is independent. Production replay, owner/lease fencing, local input
    resolution and unknown-outcome reconciliation belong to the Host, not here.
    The verifier sees a copy and must approve the entire exact request.
    """
    request = decode(raw)
    binding(expected_binding)
    identifier(expected_thread_id)
    if (
        request["binding"] != expected_binding
        or request["thread_id"] != expected_thread_id
    ):
        raise Rejected("binding mismatch")
    if verifier(copy.deepcopy(request)) is not True:
        raise Rejected("authority")
    outgoing = rpc_bytes(request, data, request_id)
    if verifier(copy.deepcopy(request)) is not True:
        raise Rejected("authority changed")
    return adapter(outgoing)
