# Native-turn request v1

This closed, independent contract is `runspindle.native-turn.v1`. It is a bounded
composition #43 extension, not an extra `runspindle.envelope.v1` event, a new
Admission payload, an input store, or runtime activation. Existing fixture,
Runtime v1, integration v1, Admission `normalized_digest` and grant semantics
remain unchanged. Structural conformance does not authorize task execution.

## Exact request and input

The request contains exactly `version`, `binding`, `thread_id`, `input` and
`profile`. All fields are required; none is nullable. Unknown versions, unknown
profile kinds, unknown or missing fields, duplicate JSON keys at any depth,
non-objects, invalid scalars and noncanonical encodings are rejected before an
adapter is invoked. No negotiation, fallback or upstream passthrough is allowed.

- `binding` contains exactly `task_id`, `revision`, `operation_id`,
  `policy_revision`, `host_id`, `workspace_id` and `lease_epoch`, with their existing
  meanings. Both counters are JSON integer tokens in 1..2^64-1. Booleans, floats,
  exponents and negative tokens (including `-0`) are rejected.
- `thread_id` identifies the exact existing native thread, not an operation or
  task ID. Identifier fields, including `profile.model`, match the ASCII pattern
  `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`. Paths, URLs and arbitrary model options are
  not identifiers.
- `input` contains exactly `sha256` (64 lowercase hexadecimal characters) and
  `byte_length` (an integer in 1..2048). The digest is the content address itself,
  not a filesystem path, URL or remote storage reference. It binds exact nonempty
  UTF-8 bytes. No trimming, newline insertion, Unicode normalization, lossy
  decoding or BOM removal occurs. Valid whitespace/control characters remain
  exact text; malformed UTF-8 and surrogate encodings are rejected. The consumer
  must independently check both length and SHA-256 on the resolved bytes.
- `profile` contains exactly `kind: "read_only_text_v1"` and `model`. It does not
  accept credentials, environment, tool settings, arbitrary upstream JSON or
  sandbox/approval overrides from the caller.

The wire request is UTF-8 JSON, lexicographically sorted object keys, compact
commas/colons, decimal integers and no unnecessary string escapes. Every request
string is ASCII. There is no trailing newline. Input bytes are referenced, not
embedded. The encoded request is at most 4096 bytes. `encode` produces these exact
bytes; `decode` rejects any other representation, including whitespace, escaped
ASCII and a UTF-8 BOM. If a later authority mechanism identifies a request by
SHA-256, it must bind these full canonical bytes, not just `input.sha256` or the
unrelated Admission digest. This contract supplies no such mechanism or grant.

## Explicit pinned upstream mapping

Reviewed source: [openai/codex TurnStartParams at
`d32063f96c2dff1dc96af839b3952abb6acfeda4`](https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/app-server-protocol/schema/json/v2/TurnStartParams.json),
Git blob `488c18cf2d9cf52a78ee1954e167f1ce2070e0ef`. No upstream executable or schema
source is imported here. Host's installed-binary/source correspondence is a
separate qualification, not established by this schema reference.

The only emitted method is `turn/start`, with exactly these parameters:

- `threadId` copies `thread_id` unchanged.
- `input` is a single-element array: `type: "text"`, `text` is the independently
  checked UTF-8 input, and `text_elements` is an empty array.
- `model` copies `profile.model` unchanged.
- `approvalPolicy` is the fixed string `"never"`.
- `sandboxPolicy` is exactly `type: "readOnly"`, `networkAccess: false`.

None of the binding, digest, byte length or profile kind is silently mapped to
an upstream field. RPC correlation IDs belong to the transport and are not task
identity, idempotency keys or authority. The Host transport separately limits the
entire encoded RPC request, including ID, JSON escaping and final newline, to
4096 bytes. A valid 2048-byte input can exceed that bound after escaping. Reject
before writing rather than truncate or change the input; any durable reservation
already created remains uncertain until the Host's reconciliation policy resolves
it. The Python size oracle uses positive u64 correlation IDs; this is its bounded
test interface, not an extension of the upstream schema.

The upstream schema explicitly describes `model`, `approvalPolicy` and
`sandboxPolicy` as overrides for this **and subsequent turns**. The closed profile
means text-only input and those requested policies. It does not prove absence of
inherited tools/plugins, hooks, history or instructions. Omitted
`disabledPluginIds` preserves the thread's list. `turn/start` can add input to an
already-active turn. A returned turn ID is an acknowledged identity, not proof
that a new turn was created, work completed, or no other effect occurred.

## Authority, lifecycle and evidence limits

The trusted consumer must compare the entire binding and native thread to its
expected target, then obtain independent approval of the entire exact request,
including the content address, length, profile and model. Default is deny. An
Admission grant, existing native session, successful resume, input hash or prior
request approval is not task-input authority. Authority must be checked again
inside the Host's current owner/lease transaction immediately before dispatch;
input resolution must also remain within current authority. No HTTP endpoint,
store, signer, credentials or approved runtime configuration is installed here.

Host owns the durable at-most-one-attempt reservation, fencing across processes,
input-reader limits, persisted acknowledged turn ID and unknown outcomes.
Neither retry nor terminal success may be inferred from a missing response.
Task-terminal and cancel-result mapping remain unsupported pending explicit
qualified mappings. Unknown events or responses may not become success or a
new grant. No composition pin is advanced by this contract tranche.

`conformance/native-turn-v1/native_turn.py` is an independent stdlib producer/consumer
and mapping oracle for synthetic inputs. `produce` hashes supplied bytes;
`consume` compares expected identity, uses a default-deny injected verifier,
checks the input, constructs bounded RPC bytes, rechecks authority and invokes
an injected observation callback. The callback is a test seam, not a native
transport. This consumer is stateless: it provides no replay/durability guarantee
and must not be substituted for Host dispatch. Verifier callbacks are trusted
code, not a signature implementation. Production use remains blocked on
reviewed authority/input custody, thread/tool isolation, real native wire and
lifecycle qualification. See [bounded evidence](../docs/NATIVE_TURN_CONFORMANCE.md).
